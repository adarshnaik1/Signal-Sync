"use client";

import Image from "next/image";
import React from "react";

const RAW_API_BASE_URL = process.env.NEXT_PUBLIC_BGV_API_BASE_URL || "";
const API_BASE_URL = RAW_API_BASE_URL.replace(/\/+$/, "");

function resolveChartUrl(url) {
  if (!url) return null;
  if (/^https?:\/\//i.test(url) || url.startsWith("data:")) {
    return url;
  }
  if (API_BASE_URL) {
    const trimmedApiBase = API_BASE_URL.replace(/\/$/, "");
    const trimmedUrl = url.replace(/^\//, "");
    return `${trimmedApiBase}/${trimmedUrl}`;
  }
  return url;
}

function Section({ title, children, subtitle }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
        {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function KeyValue({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</div>
      <div className="mt-2 text-sm font-medium text-slate-950">{value ?? "—"}</div>
    </div>
  );
}

function PillList({ items, emptyLabel = "No items reported." }) {
  if (!Array.isArray(items) || items.length === 0) {
    return <p className="text-sm text-slate-500">{emptyLabel}</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, index) => (
        <span
          key={`pill-${index}-${String(item)}`}
          className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700"
        >
          {String(item)}
        </span>
      ))}
    </div>
  );
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function pickText(...values) {
  for (const value of values) {
    if (value == null) continue;
    if (typeof value === "string" && value.trim()) return value;
    if (typeof value === "number" && Number.isFinite(value)) return String(value);
  }
  return "—";
}

function normalizeList(value) {
  if (Array.isArray(value)) return value;
  if (typeof value === "string" && value.trim()) return [value];
  if (value && typeof value === "object") {
    return Object.values(value)
      .filter((item) => typeof item === "string" || typeof item === "number")
      .map(String);
  }
  return [];
}

function formatScalar(value) {
  if (value == null || value === "") return "—";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function formatObjectValue(value) {
  if (Array.isArray(value)) {
    const items = value.map((item) => formatScalar(item)).filter((item) => item !== "—");
    return items.length ? items.join(", ") : "—";
  }
  if (isPlainObject(value)) {
    const entries = Object.entries(value).filter(([, item]) => item != null && item !== "");
    if (!entries.length) return "—";
    return entries
      .slice(0, 4)
      .map(([key, item]) => `${key}: ${formatScalar(item)}`)
      .join(" · ");
  }
  return formatScalar(value);
}

function renderObjectGrid(value) {
  if (!isPlainObject(value)) return null;
  const entries = Object.entries(value).filter(([, item]) => item != null && item !== "");
  if (!entries.length) return <p className="text-sm text-slate-500">No data reported.</p>;

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {entries.map(([key, item]) => (
        <div key={key} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{key.replace(/_/g, " ")}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{formatObjectValue(item)}</div>
        </div>
      ))}
    </div>
  );
}

function renderListPills(items, emptyLabel = "No items reported.") {
  if (!Array.isArray(items) || items.length === 0) {
    return <p className="text-sm text-slate-500">{emptyLabel}</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, index) => (
        <span
          key={`pill-${index}-${String(item)}`}
          className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700"
        >
          {String(item)}
        </span>
      ))}
    </div>
  );
}

function renderSectionValue(value, emptyLabel = "No data reported.") {
  if (value == null || value === "") {
    return <p className="text-sm text-slate-500">{emptyLabel}</p>;
  }

  if (Array.isArray(value)) {
    return renderListPills(value, emptyLabel);
  }

  if (isPlainObject(value)) {
    return renderObjectGrid(value);
  }

  return <p className="text-sm leading-7 text-slate-700">{formatScalar(value)}</p>;
}

function SectionCard({ title, value, subtitle, emptyLabel }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{title}</div>
      {subtitle ? <div className="mt-1 text-xs text-slate-400">{subtitle}</div> : null}
      <div className="mt-3">{renderSectionValue(value, emptyLabel)}</div>
    </div>
  );
}

export default function TAReportView({ result }) {
  let legacyParsed = null;
  try {
    if (result?.raw && typeof result.raw === "string") {
      let s = result.raw.trim();
      if (s.startsWith("```")) {
        const end = s.lastIndexOf("```");
        if (end > 0) {
          let inner = s.slice(3, end);
          const nl = inner.indexOf("\n");
          if (nl !== -1) {
            const first = inner.slice(0, nl).trim();
            const rest = inner.slice(nl + 1);
            if (/^[a-zA-Z]+$/.test(first) || first.toLowerCase().startsWith("json")) {
              inner = rest;
            }
          }
          s = inner.trim();
        }
      }
      legacyParsed = JSON.parse(s);
    }
  } catch (e) {
    legacyParsed = null;
  }

  const chartUrlRaw =
    result?.chart_url ||
    result?.visual_review?.chart_url ||
    (result?._artifact_urls && result._artifact_urls[0]) ||
    (legacyParsed && (legacyParsed.chart_url || (legacyParsed._artifact_urls && legacyParsed._artifact_urls[0])));
  const chartUrl = resolveChartUrl(chartUrlRaw);
  const summary = result?.summary || {};
  const stance = pickText(summary.stance, result?.stance);
  const confidence = pickText(summary.confidence, result?.confidence);
  const thesis = pickText(summary.thesis, result?.thesis);
  const topIndicators = {
    trend: result?.trend,
    momentum: result?.momentum,
    volatility: result?.volatility,
    volume: result?.volume,
  };
  const patterns = result?.pattern_explanation || result?.patterns || result?.pattern_explanations || {};
  const sr = result?.sr_explanation || result?.sr || {};
  const uncertainty = result?.uncertainty_notes || result?.uncertainty || {};
  const monitoring = normalizeList(result?.monitoring_checklist || result?.monitoring || []);
  const explanations = result?.explanations || {};
  const takeaways = normalizeList(result?.takeaways || []);
  const visualReview = result?.visual_review || legacyParsed?.visual_review || null;

  return (
    <div className="space-y-6">
      {chartUrl ? (
        <Section title="Chart" subtitle="Rendered technical chart">
          <div className="flex justify-center">
            <Image src={chartUrl} alt="TA chart" width={1024} height={576} unoptimized className="h-auto max-w-full rounded-lg shadow" />
          </div>
        </Section>
      ) : null}
      {visualReview ? (
        <Section title="Image Analysis" subtitle="Advisory visual review of the rendered chart image.">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <KeyValue label="Status" value={visualReview?.image_analysis_status || (visualReview?.success ? "completed" : "unavailable")} />
            <KeyValue label="Confidence" value={visualReview?.confidence} />
            <KeyValue label="Model" value={visualReview?.model} />
            <KeyValue label="Rows rendered" value={result?.rows_rendered || visualReview?.rows_rendered} />
          </div>
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Visual summary</div>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              {formatScalar(visualReview?.visual_summary || visualReview?.error)}
            </p>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <SectionCard
              title="Chart source"
              value={{ source_key: result?.source_key, chart_url: chartUrl }}
              emptyLabel="No chart source metadata reported."
            />
            <SectionCard title="Image metadata" value={{ image_size: visualReview?.image_size, reviewed_image_size: visualReview?.reviewed_image_size }} emptyLabel="No image metadata reported." />
          </div>
        </Section>
      ) : null}
      <section className="rounded-3xl border border-slate-200 bg-linear-to-br from-slate-950 to-slate-800 p-6 text-white shadow-lg">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-amber-300">Technical Thesis</p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight capitalize">{stance}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">{thesis}</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/8 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Confidence</div>
              <div className="mt-2 text-2xl font-bold text-white">{confidence}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/8 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Model stance</div>
              <div className="mt-2 text-2xl font-bold text-white capitalize">{stance}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/8 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Result shape</div>
              <div className="mt-2 text-lg font-semibold text-white">Structured TA output</div>
            </div>
          </div>
        </div>
      </section>

      <Section title="Signal Snapshot" subtitle="Direct rendering of the backend JSON values.">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <KeyValue label="Stance" value={stance} />
          <KeyValue label="Confidence" value={confidence} />
          <KeyValue label="Thesis" value={thesis} />
          <KeyValue label="Result shape" value="Structured TA output" />
        </div>
      </Section>

      <div className="grid gap-6 xl:grid-cols-2">
        <Section title="Indicators" subtitle="Rendered directly from the computed JSON sections.">
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(topIndicators).map(([key, value]) => (
              <SectionCard key={key} title={key} value={value} emptyLabel="No indicator data reported." />
            ))}
          </div>
        </Section>

        <Section title="Patterns" subtitle="Candlestick and chart structure output from the backend JSON.">
          <div className="space-y-4">
            <SectionCard
              title="Candlestick patterns"
              value={result?.candlestick_patterns || patterns?.candlestick_patterns}
              emptyLabel="No significant candlestick patterns reported."
            />
            <SectionCard
              title="Chart patterns"
              value={result?.chart_patterns || patterns?.chart_patterns}
              emptyLabel="No significant chart patterns reported."
            />
          </div>
        </Section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Section title="Support / Resistance" subtitle="Rendered from the saved support and resistance JSON." >
          <div className="space-y-3">
            <SectionCard
              title="Support zones"
              value={sr?.support_zones || sr?.support_levels || result?.support_zones}
              emptyLabel="No support zones reported."
            />
            <SectionCard
              title="Resistance zones"
              value={sr?.resistance_zones || sr?.resistance_levels || result?.resistance_zones}
              emptyLabel="No resistance zones reported."
            />
          </div>
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Explanation</div>
            <div className="mt-3 text-sm leading-7 text-slate-700">{renderSectionValue(sr, "No support/resistance explanation reported.")}</div>
          </div>
        </Section>

        <Section title="Uncertainty and Monitoring" subtitle="What to watch next and where the thesis can break.">
          <div className="space-y-5">
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Uncertainty notes</h4>
              <div className="mt-2">{renderSectionValue(uncertainty, "No uncertainty notes available.")}</div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Plain-language takeaways</h4>
              <div className="mt-2">
                {renderListPills(takeaways, "No plain-language takeaways available.")}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Monitoring checklist</h4>
              <div className="mt-2">
                {renderListPills(monitoring, "No monitoring checklist available.")}
              </div>
            </div>
          </div>
        </Section>
      </div>

      {(Object.keys(explanations).length > 0) ? (
        <Section title="Explanation Details" subtitle="Flattened supporting context from the backend JSON.">
          <div className="grid gap-4 md:grid-cols-2">
            {Object.entries(explanations).map(([key, value]) => (
              <SectionCard key={key} title={key} value={value} emptyLabel="No explanation data reported." />
            ))}
          </div>
        </Section>
      ) : null}
    </div>
  );
}
