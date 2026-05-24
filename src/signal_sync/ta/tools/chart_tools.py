import json
import os
from datetime import datetime
from typing import Type, Any, cast
from dotenv import load_dotenv
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

load_dotenv()

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CHART_DIR = os.path.join(ROOT, "src", "signal_sync", "ta", "charts")
os.makedirs(CHART_DIR, exist_ok=True)


class RenderChartInput(BaseModel):
    ohlcv_json: str = Field(..., description="JSON string containing OHLCV list or object with key 'ohlcv'.")
    ticker: str = Field(default="UNKNOWN", description="Ticker symbol for chart title and filename.")
    include_rsi: bool = Field(default=False, description="Render optional RSI panel.")


class RenderChartTool(BaseTool):
    name: str = "render_chart_tool"
    description: str = "Render internal TA chart PNG (price-volume + EMA overlays, optional RSI)."
    args_schema: Type[BaseModel] = RenderChartInput

    def _run(self, ohlcv_json: str, ticker: str = "UNKNOWN", include_rsi: bool = False) -> str:
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
        except ImportError:
            return json.dumps({"success": False, "error": "Missing matplotlib/pandas dependency."})

        try:
            raw = json.loads(ohlcv_json)
            rows = raw.get("ohlcv", raw) if isinstance(raw, dict) else raw
            df = pd.DataFrame(rows)

            rename_map = {
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
                "date": "Date",
                "datetime": "Datetime",
                "timestamp": "Date",
            }
            for src, dst in rename_map.items():
                if src in df.columns and dst not in df.columns:
                    df = df.rename(columns={src: dst})

            dt_col = "Date" if "Date" in df.columns else ("Datetime" if "Datetime" in df.columns else None)
            if dt_col is None:
                return json.dumps({"success": False, "error": "Expected Date/Datetime column."})

            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
            df = df.dropna(subset=[dt_col]).sort_values(dt_col)
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df["ema20"] = df["Close"].ewm(span=20, adjust=False).mean()
            df["ema50"] = df["Close"].ewm(span=50, adjust=False).mean()
            df["ema200"] = df["Close"].ewm(span=200, adjust=False).mean()

            if include_rsi:
                delta = df["Close"].diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / loss.replace(0, float("nan"))
                df["rsi14"] = 100 - (100 / (1 + rs))

            nrows = 3 if include_rsi else 2
            fig, axes = plt.subplots(nrows=nrows, ncols=1, figsize=(14, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1, 1] if include_rsi else [3, 1]})

            ax_price = axes[0]
            ax_price.plot(df[dt_col], df["Close"], label="Close", linewidth=1.5)
            ax_price.plot(df[dt_col], df["ema20"], label="EMA20", linewidth=1.0)
            ax_price.plot(df[dt_col], df["ema50"], label="EMA50", linewidth=1.0)
            ax_price.plot(df[dt_col], df["ema200"], label="EMA200", linewidth=1.0)
            ax_price.set_title(f"{ticker} Technical Chart")
            ax_price.legend(loc="upper left")
            ax_price.grid(alpha=0.2)

            ax_vol = axes[1]
            ax_vol.bar(df[dt_col], df["Volume"], width=1.0)
            ax_vol.set_title("Volume")
            ax_vol.grid(alpha=0.2)

            if include_rsi:
                ax_rsi = axes[2]
                ax_rsi.plot(df[dt_col], df["rsi14"], label="RSI14", linewidth=1.0)
                ax_rsi.axhline(70, linestyle="--", linewidth=0.8)
                ax_rsi.axhline(30, linestyle="--", linewidth=0.8)
                ax_rsi.set_ylim(0, 100)
                ax_rsi.set_title("RSI")
                ax_rsi.grid(alpha=0.2)

            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            out_path = os.path.join(CHART_DIR, f"{ticker}_{ts}.png")
            fig.tight_layout()
            fig.savefig(out_path, dpi=130)
            plt.close(fig)

            return json.dumps({"success": True, "chart_path": out_path})
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Chart render failed: {exc}"})


class VisionReviewInput(BaseModel):
    chart_path: str = Field(..., description="Absolute path to generated chart image file.")
    model: str = Field(default="gpt-4.1-mini", description="Vision-capable model name.")


class VisionReviewTool(BaseTool):
    name: str = "vision_review_tool"
    description: str = "Advisory visual review of generated chart. Deterministic tools remain source-of-truth."
    args_schema: Type[BaseModel] = VisionReviewInput

    def _run(self, chart_path: str, model: str = "gpt-4.1-mini") -> str:
        if not os.path.exists(chart_path):
            return json.dumps({"success": False, "error": f"Chart file not found: {chart_path}"})

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return json.dumps(
                {
                    "success": True,
                    "visual_summary": "Vision review skipped because OPENAI_API_KEY is not configured. Use deterministic pattern outputs as source-of-truth.",
                    "confidence": 0.0,
                    "advisory_only": True,
                }
            )

        try:
            import base64
            import io
            from PIL import Image
            from openai import OpenAI

            # Compress the chart image to keep payloads reasonable
            with Image.open(chart_path) as img:
                img.thumbnail((1200, 800), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            client = OpenAI(api_key=api_key)
            prompt = (
                "Review this technical chart image and provide a brief advisory summary of trend/consolidation/breakout cues. "
                "Do not provide investment guarantees. Return strict JSON with keys visual_summary and confidence (0 to 1)."
            )

            input_payload = [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"},
                    ],
                }
            ]

            resp = client.responses.create(
                model=model,
                input=cast(Any, input_payload),
                temperature=0.2,
            )

            text = getattr(resp, "output_text", "")
            if not text:
                text = str(resp)

            try:
                parsed = json.loads(text)
                summary = parsed.get("visual_summary", "No summary provided")
                confidence = float(parsed.get("confidence", 0.5))
            except Exception:
                summary = text
                confidence = 0.5

            return json.dumps(
                {
                    "success": True,
                    "visual_summary": summary,
                    "confidence": max(0.0, min(confidence, 1.0)),
                    "advisory_only": True,
                }
            )
        except Exception as exc:
            return json.dumps(
                {
                    "success": True,
                    "visual_summary": f"Vision review unavailable ({exc}). Continue with deterministic results.",
                    "confidence": 0.0,
                    "advisory_only": True,
                }
            )
