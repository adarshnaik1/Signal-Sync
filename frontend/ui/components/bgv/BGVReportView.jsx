"use client";

import React from "react";

const SCORE_LABELS = {
  trustworthiness_score: { label: "Trustworthiness", max: 100, tone: "emerald" },
  financial_integrity_score: { label: "Financial Integrity", max: 100, tone: "blue" },
  management_risk_score: { label: "Management Risk", max: 100, tone: "amber" },
  market_manipulation_risk_score: { label: "Market Manipulation Risk", max: 100, tone: "rose" },
};

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function scoreTone(scoreKey) {
  return SCORE_LABELS[scoreKey]?.tone || "slate";
}

function formatScoreValue(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return Number(value).toFixed(Number.isInteger(Number(value)) ? 0 : 1);
}

function ProgressBar({ value, max = 100, tone = "emerald" }) {
  const percentage = Math.max(0, Math.min(100, (Number(value) / Number(max)) * 100 || 0));
  const toneMap = {
    emerald: "from-emerald-500 to-emerald-400",
    blue: "from-blue-500 to-cyan-400",
    amber: "from-amber-500 to-orange-400",
    rose: "from-rose-500 to-pink-400",
    slate: "from-slate-500 to-slate-400",
  };

  return (
    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
      <div className={`h-full rounded-full bg-linear-to-r ${toneMap[tone] || toneMap.slate}`} style={{ width: `${percentage}%` }} />
    </div>
  );
}

function Section({ title, children, subtitle }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
          {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
        </div>
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

function BulletList({ items, emptyLabel = "No items reported." }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">{emptyLabel}</p>;
  }
  return (
    <ul className="space-y-2 text-sm text-slate-700">
      {items.map((item, index) => (
        <li key={index} className="flex gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <span className="mt-1 h-2.5 w-2.5 rounded-full bg-amber-500" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function BGVReportView({ result }) {
  const scores = result?.scores || {};
  const company = result?.company || {};
  const findings = result?.findings || {};
  const evidence = result?.evidence || {};
  const meta = result?.meta || {};
  const scoreEntries = Object.entries(SCORE_LABELS);

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-linear-to-br from-slate-950 to-slate-800 p-6 text-white shadow-lg">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-amber-300">Final Verdict</p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight">{result?.final_verdict || "Analysis complete"}</h2>
            <p className="mt-2 max-w-3xl text-sm text-slate-300">
              {company.name ? `${company.name} (${company.ticker || ""})` : "Structured BGV report"}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {scoreEntries.map(([key, config]) => {
              const value = scores[key];
              return (
                <div key={key} className="rounded-2xl border border-white/10 bg-white/8 p-4">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">{config.label}</div>
                  <div className="mt-2 text-2xl font-bold text-white">
                    {formatScoreValue(value)} <span className="text-sm font-medium text-slate-300">/ {config.max}</span>
                  </div>
                  <ProgressBar value={value} max={config.max} tone={scoreTone(key)} />
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <Section title="Company Profile" subtitle="Overview of the company being verified.">
          <div className="grid gap-3 sm:grid-cols-2">
            <KeyValue label="Name" value={company.name} />
            <KeyValue label="Ticker" value={company.ticker} />
            <KeyValue label="Sector" value={company.sector} />
            <KeyValue label="Headquarters" value={company.headquarters} />
            <KeyValue label="Founded" value={company.founded_year} />
            <KeyValue label="Employees" value={company.employees} />
          </div>
          {company.profile_summary ? <p className="mt-4 text-sm leading-7 text-slate-700">{company.profile_summary}</p> : null}
          {asArray(company.products_services).length ? (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-slate-950">Products and services</h4>
              <div className="mt-2 flex flex-wrap gap-2">
                {company.products_services.map((item) => (
                  <span key={item} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">{item}</span>
                ))}
              </div>
            </div>
          ) : null}
        </Section>

        <Section title="Report Metadata" subtitle="Generation and provenance details.">
          <div className="grid gap-3 sm:grid-cols-2">
            <KeyValue label="Generated at" value={meta.generated_at} />
            <KeyValue label="Pipeline version" value={meta.pipeline_version} />
            <KeyValue label="Sources" value={asArray(meta.sources).length} />
            <KeyValue label="Evidence items" value={asArray(evidence.documents).length + asArray(evidence.time_series).length + asArray(evidence.people_profiles).length} />
          </div>
          {asArray(meta.sources).length ? (
            <div className="mt-4 space-y-2">
              {meta.sources.map((source, index) => (
                <div key={`${source.name}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="font-medium text-slate-950">{source.name}</div>
                  <div className="text-sm text-slate-500">{source.type}{source.url ? ` · ${source.url}` : ""}</div>
                </div>
              ))}
            </div>
          ) : null}
        </Section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Section title="Findings" subtitle="Grouped observations from each verification stage.">
          <div className="space-y-5">
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Overview findings</h4>
              <div className="mt-2">
                <BulletList items={asArray(findings.overview_findings)} />
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Management findings</h4>
              <div className="mt-2">
                <BulletList items={asArray(findings.management_findings)} />
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Financial irregularities</h4>
              <div className="mt-2">
                <BulletList items={asArray(findings.financial_irregularities)} />
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Scam signals</h4>
              <div className="mt-2">
                <BulletList items={asArray(findings.scam_signals)} />
              </div>
            </div>
          </div>
        </Section>

        <Section title="Evidence" subtitle="Supporting documents, people profiles and market data.">
          <div className="space-y-4">
            <EvidenceGroup title="Documents" items={asArray(evidence.documents)} renderItem={(item) => (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="font-medium text-slate-950">{item.type}</div>
                <div className="text-sm text-slate-500">{item.location}</div>
                {item.summary ? <p className="mt-2 text-sm text-slate-700">{item.summary}</p> : null}
              </div>
            )} />
            <EvidenceGroup title="People profiles" items={asArray(evidence.people_profiles)} renderItem={(item) => (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="font-medium text-slate-950">{item.name}</div>
                <div className="text-sm text-slate-500">{item.role}</div>
                {asArray(item.red_flags).length ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {item.red_flags.map((flag) => (
                      <span key={flag} className="rounded-full bg-rose-100 px-2.5 py-1 text-xs font-medium text-rose-700">{flag}</span>
                    ))}
                  </div>
                ) : null}
              </div>
            )} />
            <EvidenceGroup title="Time series" items={asArray(evidence.time_series)} renderItem={(item) => (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="font-medium text-slate-950">{item.source}</div>
                <div className="text-sm text-slate-500">{item.from_date} → {item.to_date}</div>
                <div className="text-sm text-slate-700">{item.file}</div>
              </div>
            )} />
          </div>
        </Section>
      </div>
    </div>
  );
}

function EvidenceGroup({ title, items, renderItem }) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      <div className="mt-2 space-y-3">
        {items.length ? items.map((item, index) => <React.Fragment key={index}>{renderItem(item)}</React.Fragment>) : <p className="text-sm text-slate-500">No {title.toLowerCase()} available.</p>}
      </div>
    </div>
  );
}
