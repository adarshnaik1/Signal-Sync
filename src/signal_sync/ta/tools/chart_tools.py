import json
import os
from datetime import datetime
from typing import Type, Any, cast
from dotenv import load_dotenv
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from .tool_utils import catch_and_normalize, extract_ohlcv_rows, load_json_or_path, make_response, ensure_abs_path

load_dotenv()

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CHART_DIR = os.path.join(ROOT, "src", "signal_sync", "ta", "charts")
DEFAULT_VISION_MODEL = "gpt-4.1-mini"
ALLOWED_VISION_MODELS = {
    DEFAULT_VISION_MODEL.lower(): DEFAULT_VISION_MODEL,
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4o": "gpt-4o",
}
VISION_MODEL_ALIASES = {
    "default",
    "standard",
    "advisory_review_model",
    "vision",
    "vision_model",
    "image_analysis",
    "none",
    "null",
}
os.makedirs(CHART_DIR, exist_ok=True)


class RenderChartInput(BaseModel):
    ohlcv_json: str = Field(..., description="JSON string or file path containing OHLCV list/object. Supports bundle keys: ohlcv, daily_ohlcv, weekly_ohlcv.")
    ticker: str = Field(default="UNKNOWN", description="Ticker symbol for chart title and filename.")
    include_rsi: bool = Field(default=False, description="Render optional RSI panel.")


class RenderChartTool(BaseTool):
    name: str = "render_chart_tool"
    description: str = "Render internal TA chart PNG (price-volume + EMA overlays, optional RSI)."
    args_schema: Type[BaseModel] = RenderChartInput

    @catch_and_normalize
    def _run(self, ohlcv_json: str, ticker: str = "UNKNOWN", include_rsi: bool = False) -> dict:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import pandas as pd
        except ImportError:
            return json.dumps({"success": False, "error": "Missing matplotlib/pandas dependency."})

        try:
            raw = load_json_or_path(ohlcv_json)
        except Exception as exc:
            return make_response(False, error="Invalid JSON provided to render_chart_tool.")

        try:
            rows, source_key = extract_ohlcv_rows(raw, min_rows=2)
        except Exception as exc:
            return make_response(False, error=str(exc))

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
            return make_response(False, error="Expected Date/Datetime column.")

        df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
        df = df.dropna(subset=[dt_col]).sort_values(dt_col)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        required_cols = ["Open", "High", "Low", "Close"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return make_response(False, error=f"Missing OHLC columns for chart: {', '.join(missing)}.")
        df = df.dropna(subset=required_cols)
        if len(df) < 2:
            return make_response(False, error="Need at least 2 OHLC rows to render a meaningful chart.", rows=int(len(df)), source_key=source_key)
        if "Volume" not in df.columns:
            df["Volume"] = 0
        df["Volume"] = df["Volume"].fillna(0)

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
        x_values = mdates.date2num(df[dt_col].dt.to_pydatetime())
        candle_width = max((x_values[-1] - x_values[0]) / max(len(x_values), 1) * 0.65, 0.4)
        up_color = "#16803c"
        down_color = "#c23b22"
        for x, open_p, high_p, low_p, close_p in zip(x_values, df["Open"], df["High"], df["Low"], df["Close"]):
            color = up_color if close_p >= open_p else down_color
            ax_price.vlines(x, low_p, high_p, color=color, linewidth=1.0, alpha=0.9)
            body_low = min(open_p, close_p)
            body_height = max(abs(close_p - open_p), (high_p - low_p) * 0.01, 0.01)
            ax_price.add_patch(
                plt.Rectangle(
                    (x - candle_width / 2, body_low),
                    candle_width,
                    body_height,
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.75,
                )
            )
        ax_price.plot(df[dt_col], df["Close"], label="Close", linewidth=1.0, color="#1f2937", alpha=0.85)
        ax_price.plot(df[dt_col], df["ema20"], label="EMA20", linewidth=1.0)
        ax_price.plot(df[dt_col], df["ema50"], label="EMA50", linewidth=1.0)
        ax_price.plot(df[dt_col], df["ema200"], label="EMA200", linewidth=1.0)
        ax_price.set_title(f"{ticker} Technical Chart ({source_key}, {len(df)} rows)")
        ax_price.legend(loc="upper left")
        ax_price.grid(alpha=0.2)
        ax_price.xaxis_date()

        ax_vol = axes[1]
        vol_colors = [up_color if close_p >= open_p else down_color for open_p, close_p in zip(df["Open"], df["Close"])]
        ax_vol.bar(df[dt_col], df["Volume"], width=candle_width, color=vol_colors, alpha=0.65)
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
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(out_path, dpi=130)
        plt.close(fig)

        return make_response(True, chart_path=ensure_abs_path(out_path), rows_rendered=int(len(df)), source_key=source_key)


def _normalize_vision_model(model: str) -> str:
    value = str(model or "").strip()
    normalized = value.lower()
    if not normalized or normalized in VISION_MODEL_ALIASES:
        return DEFAULT_VISION_MODEL
    return ALLOWED_VISION_MODELS.get(normalized, DEFAULT_VISION_MODEL)


def _parse_jsonish_text(text: str) -> dict | None:
    value = str(text or "").strip()
    if value.startswith("```"):
        end = value.rfind("```")
        if end > 0:
            inner = value[3:end].strip()
            if "\n" in inner:
                first, rest = inner.split("\n", 1)
                if first.strip().isalpha() or first.strip().lower().startswith("json"):
                    inner = rest.strip()
            value = inner
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


class VisionReviewInput(BaseModel):
    chart_path: str = Field(..., description="Absolute path to generated chart image file.")
    model: str = Field(default=DEFAULT_VISION_MODEL, description="Vision-capable model name.")


class VisionReviewTool(BaseTool):
    name: str = "vision_review_tool"
    description: str = "Advisory visual review of generated chart. Deterministic tools remain source-of-truth."
    args_schema: Type[BaseModel] = VisionReviewInput

    @catch_and_normalize
    def _run(self, chart_path: str, model: str = DEFAULT_VISION_MODEL) -> dict:
        if not os.path.exists(chart_path):
            return make_response(False, error=f"Chart file not found: {chart_path}")

        selected_model = _normalize_vision_model(model)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return make_response(
                True,
                visual_summary="Vision review skipped because OPENAI_API_KEY is not configured. Use deterministic pattern outputs as source-of-truth.",
                confidence=0.0,
                advisory_only=True,
                image_analysis_status="skipped_no_api_key",
                chart_path=ensure_abs_path(chart_path),
                model=selected_model,
            )

        try:
            import base64
            import io
            from PIL import Image
            from openai import OpenAI

            # Compress the chart image to keep payloads reasonable
            with Image.open(chart_path) as img:
                original_size = {"width": int(img.width), "height": int(img.height)}
                img.thumbnail((1200, 800), Image.LANCZOS)
                reviewed_size = {"width": int(img.width), "height": int(img.height)}
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
                model=selected_model,
                input=cast(Any, input_payload),
                temperature=0.2,
            )

            text = getattr(resp, "output_text", "")
            if not text:
                text = str(resp)

            parsed = _parse_jsonish_text(text)
            if parsed is not None:
                try:
                    confidence = float(parsed.get("confidence", 0.5))
                except Exception:
                    confidence = 0.5
                summary = parsed.get("visual_summary", "No summary provided")
            else:
                summary = text
                confidence = 0.5

            return make_response(
                True,
                visual_summary=summary,
                confidence=max(0.0, min(confidence, 1.0)),
                advisory_only=True,
                image_analysis_status="completed",
                chart_path=ensure_abs_path(chart_path),
                model=selected_model,
                image_size=original_size,
                reviewed_image_size=reviewed_size,
            )
        except Exception as exc:
            return make_response(
                True,
                visual_summary=f"Vision review unavailable ({exc}). Continue with deterministic results.",
                confidence=0.0,
                advisory_only=True,
                image_analysis_status="unavailable",
                chart_path=ensure_abs_path(chart_path),
                model=selected_model,
                error=str(exc),
            )
