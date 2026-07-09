"use client";

import React from "react";

/* ─── helpers ──────────────────────────────────────────────────────── */

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function pickText(...values) {
  for (const v of values) {
    if (v == null) continue;
    if (typeof v === "string" && v.trim()) return v;
    if (typeof v === "number" && Number.isFinite(v)) return String(v);
  }
  return "—";
}

function formatScalar(value) {
  if (value == null || value === "") return "—";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

/* ─── reusable UI primitives ──────────────────────────────────────── */

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

function StatusBadge({ status }) {
  const colorMap = {
    positive: "bg-emerald-100 text-emerald-700 border-emerald-200",
    high: "bg-emerald-100 text-emerald-700 border-emerald-200",
    neutral: "bg-amber-100 text-amber-700 border-amber-200",
    moderate: "bg-amber-100 text-amber-700 border-amber-200",
    negative: "bg-rose-100 text-rose-700 border-rose-200",
    low: "bg-slate-100 text-slate-600 border-slate-200",
  };
  const key = (status || "").toLowerCase();
  const classes = colorMap[key] || "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold capitalize ${classes}`}>
      {status || "—"}
    </span>
  );
}

function StatusCard({ title, status, summary }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{title}</div>
        <StatusBadge status={status} />
      </div>
      {summary ? <p className="mt-3 text-sm leading-6 text-slate-700">{summary}</p> : null}
    </div>
  );
}

function BulletList({ items, emptyLabel = "No items reported." }) {
  const list = asArray(items);
  if (!list.length) return <p className="text-sm text-slate-500">{emptyLabel}</p>;
  return (
    <ul className="space-y-2 text-sm text-slate-700">
      {list.map((item, i) => (
        <li key={i} className="flex gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-amber-500" />
          <span>{typeof item === "string" ? item : JSON.stringify(item)}</span>
        </li>
      ))}
    </ul>
  );
}

function PillList({ items, emptyLabel = "No items reported." }) {
  const list = asArray(items);
  if (!list.length) return <p className="text-sm text-slate-500">{emptyLabel}</p>;
  return (
    <div className="flex flex-wrap gap-2">
      {list.map((item, i) => (
        <span key={i} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
          {String(item)}
        </span>
      ))}
    </div>
  );
}

function ProgressBar({ value, max = 100, tone = "emerald" }) {
  const pct = Math.max(0, Math.min(100, (Number(value) / Number(max)) * 100 || 0));
  const toneMap = {
    emerald: "from-emerald-500 to-emerald-400",
    blue: "from-blue-500 to-cyan-400",
    amber: "from-amber-500 to-orange-400",
    rose: "from-rose-500 to-pink-400",
    slate: "from-slate-500 to-slate-400",
  };
  return (
    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
      <div className={`h-full rounded-full bg-linear-to-r ${toneMap[tone] || toneMap.slate}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

/* ─── verdict colour mapping ──────────────────────────────────────── */

function verdictColor(verdict) {
  const v = (verdict || "").toUpperCase();
  if (v === "BUY") return { bg: "from-emerald-900 to-emerald-700", text: "text-emerald-300", badge: "bg-emerald-500" };
  if (v === "SELL") return { bg: "from-rose-900 to-rose-700", text: "text-rose-300", badge: "bg-rose-500" };
  return { bg: "from-slate-950 to-slate-800", text: "text-amber-300", badge: "bg-amber-500" };
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  Main component                                                     */
/* ═══════════════════════════════════════════════════════════════════ */

export default function FAReportView({ result }) {
  if (!result) return null;

  const company = result.company_identification || {};
  const meta = result.company_metadata || {};
  const market = result.market_data || {};
  const ratios = result.financial_ratios || {};
  const business = result.business_analysis || {};
  const financial = result.financial_analysis || {};
  const risk = result.risk_analysis || {};
  const valuation = result.valuation_analysis || {};
  const verdict = result.investment_verdict || {};
  const explanation = result.explanation || {};

  const vc = verdictColor(verdict.investment_verdict);

  return (
    <div className="space-y-6">
      {/* ─── 1  INVESTMENT VERDICT HERO ──────────────────────────── */}
      <section className={`rounded-3xl border border-slate-200 bg-linear-to-br ${vc.bg} p-6 text-white shadow-lg`}>
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className={`text-xs font-semibold uppercase tracking-[0.3em] ${vc.text}`}>Investment Verdict</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight">
              {verdict.investment_verdict || "Analysis Complete"}
            </h2>
            {verdict.final_summary ? (
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">{verdict.final_summary}</p>
            ) : null}
            {company.long_name ? (
              <p className="mt-2 text-sm text-slate-400">
                {company.long_name} ({company.symbol || ""}) · {company.exchange || ""}
              </p>
            ) : null}
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-white/10 bg-white/8 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Verdict Score</div>
              <div className="mt-2 text-2xl font-bold text-white">
                {verdict.verdict_score ?? "—"} <span className="text-sm font-medium text-slate-300">/ 100</span>
              </div>
              <ProgressBar
                value={verdict.verdict_score}
                max={100}
                tone={verdict.investment_verdict === "BUY" ? "emerald" : verdict.investment_verdict === "SELL" ? "rose" : "amber"}
              />
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/8 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Confidence</div>
              <div className="mt-2 text-2xl font-bold text-white capitalize">{pickText(verdict.confidence_level)}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/8 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Holding Period</div>
              <div className="mt-2 text-2xl font-bold text-white capitalize">{pickText(verdict.holding_period)}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/8 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Result Shape</div>
              <div className="mt-2 text-lg font-semibold text-white">Structured FA</div>
            </div>
          </div>
        </div>

        {/* key drivers */}
        {asArray(verdict.key_drivers).length > 0 ? (
          <div className="mt-6 flex flex-wrap gap-2">
            {verdict.key_drivers.map((d, i) => (
              <span key={i} className={`rounded-full ${vc.badge} px-3 py-1 text-xs font-semibold text-white`}>{d}</span>
            ))}
          </div>
        ) : null}
      </section>

      {/* ─── 2  VERDICT DETAILS ──────────────────────────────────── */}
      <div className="grid gap-6 xl:grid-cols-2">
        <Section title="Primary Reasons" subtitle="Top factors supporting the investment verdict.">
          <BulletList items={verdict.primary_reasons} emptyLabel="No primary reasons reported." />
        </Section>
        <Section title="Major Concerns" subtitle="Key risks and watchpoints identified by the analysis.">
          <BulletList items={verdict.major_concerns} emptyLabel="No major concerns reported." />
        </Section>
      </div>

      {/* ─── 3  BUSINESS ANALYSIS ────────────────────────────────── */}
      <Section title="Business Analysis" subtitle="Industry positioning, revenue drivers, and competitive landscape.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <KeyValue label="Business Model" value={business.business_model} />
          <KeyValue label="Business Outlook" value={business.business_outlook} />
          <KeyValue label="Industry Position" value={business.industry_position} />
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <StatusCard
            title="Industry Outlook"
            status={business.industry_outlook?.status}
            summary={business.industry_outlook?.summary}
          />
          <StatusCard
            title="Industry Growth Potential"
            status={business.industry_growth_potential?.status}
            summary={business.industry_growth_potential?.summary}
          />
        </div>

        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-semibold text-slate-950">Core Revenue Drivers</h4>
            <div className="mt-2"><PillList items={business.core_revenue_drivers} /></div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-950">Competitive Advantages</h4>
            <div className="mt-2"><PillList items={business.competitive_advantages} /></div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-950">Growth Opportunities</h4>
            <div className="mt-2"><PillList items={business.growth_opportunities} /></div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-950">Business Risks</h4>
            <div className="mt-2"><PillList items={business.business_risks} /></div>
          </div>
        </div>

        {business.business_summary ? (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Business Summary</div>
            <p className="mt-3 text-sm leading-7 text-slate-700">{business.business_summary}</p>
          </div>
        ) : null}

        {asArray(business.recent_business_developments).length > 0 ? (
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-slate-950">Recent Developments</h4>
            <div className="mt-2"><BulletList items={business.recent_business_developments} /></div>
          </div>
        ) : null}
      </Section>

      {/* ─── 4  FINANCIAL ANALYSIS ───────────────────────────────── */}
      <Section title="Financial Analysis" subtitle="Profitability, debt health, cash flows, and operational efficiency.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <StatusCard
            title="Revenue Growth"
            status={financial.revenue_growth?.status}
            summary={
              financial.revenue_growth?.value_percent != null
                ? `${financial.revenue_growth.value_percent}% — ${financial.revenue_growth.summary || ""}`
                : financial.revenue_growth?.summary
            }
          />
          <StatusCard title="Profitability" status={financial.profitability?.status} summary={financial.profitability?.summary} />
          <StatusCard title="Debt Health" status={financial.debt_health?.status} summary={financial.debt_health?.summary} />
          <StatusCard title="Cash Flow Strength" status={financial.cash_flow_strength?.status} summary={financial.cash_flow_strength?.summary} />
          <StatusCard title="Operational Efficiency" status={financial.operational_efficiency?.status} summary={financial.operational_efficiency?.summary} />
          <StatusCard title="Financial Stability" status={financial.financial_stability?.status} summary={financial.financial_stability?.summary} />
        </div>

        {asArray(financial.key_financial_risks).length > 0 ? (
          <div className="mt-5">
            <h4 className="text-sm font-semibold text-slate-950">Key Financial Risks</h4>
            <div className="mt-2"><BulletList items={financial.key_financial_risks} /></div>
          </div>
        ) : null}

        {financial.financial_summary ? (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Financial Summary</div>
            <p className="mt-3 text-sm leading-7 text-slate-700">{financial.financial_summary}</p>
          </div>
        ) : null}
      </Section>

      {/* ─── 5  RISK ANALYSIS ────────────────────────────────────── */}
      <Section title="Risk Analysis" subtitle="Market, industry, and operational risk assessment.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <KeyValue label="Overall Risk Level" value={risk.overall_risk_level} />
          <KeyValue label="Market Risk" value={risk.market_risk} />
          <KeyValue label="Debt Risk" value={risk.debt_risk} />
          <KeyValue label="Liquidity Risk" value={risk.liquidity_risk} />
          <KeyValue label="Profitability Risk" value={risk.profitability_risk} />
          <KeyValue label="Operational Risk" value={risk.operational_risk} />
          <KeyValue label="Financial Stability Risk" value={risk.financial_stability_risk} />
        </div>

        {asArray(risk.industry_risks).length > 0 ? (
          <div className="mt-5">
            <h4 className="text-sm font-semibold text-slate-950">Industry Risks</h4>
            <div className="mt-2"><PillList items={risk.industry_risks} /></div>
          </div>
        ) : null}

        {asArray(risk.key_warning_signals).length > 0 ? (
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-slate-950">Warning Signals</h4>
            <div className="mt-2"><BulletList items={risk.key_warning_signals} /></div>
          </div>
        ) : null}

        {risk.risk_summary ? (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Risk Summary</div>
            <p className="mt-3 text-sm leading-7 text-slate-700">{risk.risk_summary}</p>
          </div>
        ) : null}
      </Section>

      {/* ─── 6  VALUATION ANALYSIS ───────────────────────────────── */}
      <Section title="Valuation Analysis" subtitle="Price-to-earnings, growth outlook, and intrinsic value assessment.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <KeyValue label="Valuation Status" value={valuation.valuation_status} />
          <KeyValue label="Valuation Confidence" value={valuation.valuation_confidence} />
          <KeyValue label="P/E Analysis" value={valuation.pe_analysis} />
          <KeyValue label="Growth vs Valuation" value={valuation.growth_vs_valuation} />
          <KeyValue label="Intrinsic Value Outlook" value={valuation.intrinsic_value_outlook} />
        </div>
        {valuation.valuation_summary ? (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Valuation Summary</div>
            <p className="mt-3 text-sm leading-7 text-slate-700">{valuation.valuation_summary}</p>
          </div>
        ) : null}
      </Section>

      {/* ─── 7  MARKET SNAPSHOT ──────────────────────────────────── */}
      <Section title="Market Snapshot" subtitle="Current market data and key financial ratios.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KeyValue label="Current Price" value={market.current_price ? `₹${Number(market.current_price).toLocaleString()}` : null} />
          <KeyValue label="Market Cap" value={market.market_cap ? `₹${(market.market_cap / 1e7).toFixed(2)} Cr` : null} />
          <KeyValue label="52W High" value={market.fifty_two_week_high} />
          <KeyValue label="52W Low" value={market.fifty_two_week_low} />
          <KeyValue label="P/E Ratio" value={ratios.pe_ratio != null ? Number(ratios.pe_ratio).toFixed(2) : null} />
          <KeyValue label="ROE" value={ratios.roe != null ? `${(ratios.roe * 100).toFixed(2)}%` : null} />
          <KeyValue label="Debt to Equity" value={ratios.debt_to_equity} />
          <KeyValue label="Profit Margin" value={ratios.profit_margin != null ? `${(ratios.profit_margin * 100).toFixed(2)}%` : null} />
        </div>
      </Section>

      {/* ─── 8  EXPLANATION (optional) ───────────────────────────── */}
      {Object.keys(explanation).length > 0 ? (
        <Section title="AI Explanation" subtitle="Plain-language interpretation of the investment recommendation.">
          {explanation.executive_summary ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Executive Summary</div>
              <p className="mt-3 text-sm font-medium leading-7 text-slate-950">{explanation.executive_summary}</p>
            </div>
          ) : null}

          {explanation.why_buy_hold_sell ? (
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Investment Rationale</div>
              <p className="mt-3 text-sm leading-7 text-slate-700">{explanation.why_buy_hold_sell}</p>
            </div>
          ) : null}

          <div className="mt-5 grid gap-5 md:grid-cols-3">
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Key Strengths</h4>
              <div className="mt-2"><BulletList items={explanation.key_strengths} emptyLabel="—" /></div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-950">Key Risks</h4>
              <div className="mt-2"><BulletList items={explanation.key_risks} emptyLabel="—" /></div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-950">What to Monitor</h4>
              <div className="mt-2"><BulletList items={explanation.what_to_monitor} emptyLabel="—" /></div>
            </div>
          </div>
        </Section>
      ) : null}
    </div>
  );
}
