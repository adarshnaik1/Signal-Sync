"use client";

import React, { useState } from "react";

function getOutlookStyles(outlook) {
  const o = (outlook || "").toUpperCase();
  if (o === "BULLISH") {
    return {
      bg: "from-emerald-900 to-emerald-700 border-emerald-800",
      text: "text-emerald-300",
      badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
      pill: "bg-emerald-500",
      desc: "The general market sentiment is positive. News headlines suggest upward growth and strong performance drivers.",
    };
  }
  if (o === "BEARISH") {
    return {
      bg: "from-rose-900 to-rose-700 border-rose-800",
      text: "text-rose-300",
      badge: "bg-rose-500/20 text-rose-300 border-rose-500/30",
      pill: "bg-rose-500",
      desc: "The general market sentiment is negative. Regulatory warnings, downturn indicators, or weak earnings are dominating the headlines.",
    };
  }
  return {
    bg: "from-slate-950 to-slate-800 border-slate-800",
    text: "text-amber-300",
    badge: "bg-amber-500/20 text-amber-300 border-amber-500/30",
    pill: "bg-amber-500",
    desc: "Market sentiment is neutral or balanced. There is a mix of positive growth news and counterbalancing caution in the press.",
  };
}

export default function NewsReportView({ result }) {
  const [filter, setFilter] = useState("all");

  if (!result || result.status === "error") {
    return (
      <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-rose-900">
        <h3 className="text-lg font-bold">Error in Analysis</h3>
        <p className="mt-2 text-sm">{result?.message || "Could not retrieve news sentiment analysis results."}</p>
      </div>
    );
  }

  const outlook = result.overall_status || "Neutral";
  const styles = getOutlookStyles(outlook);
  const dist = result.distribution || {};
  const newsList = result.news || [];

  const filteredNews = newsList.filter((item) => {
    if (filter === "all") return true;
    return (item.sentiment_label || "").toLowerCase() === filter;
  });

  return (
    <div className="space-y-6">
      {/* ─── HERO OUTLOOK CARD ──────────────────────────────────────────────── */}
      <section className={`rounded-3xl border bg-linear-to-br ${styles.bg} p-6 text-white shadow-lg`}>
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex-1">
            <p className={`text-xs font-semibold uppercase tracking-[0.3em] ${styles.text}`}>News Sentiment Outlook</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight">{outlook}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">{styles.desc}</p>
          </div>

          <div className="grid gap-3 grid-cols-2 md:grid-cols-3 xl:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Avg Sentiment Score</div>
              <div className="mt-2 text-2xl font-bold text-white">
                {result.average_score != null ? result.average_score.toFixed(2) : "—"}
              </div>
              <div className="mt-1 text-[10px] text-slate-300">Scale: -1.0 to +1.0</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Articles Analyzed</div>
              <div className="mt-2 text-2xl font-bold text-white">{result.total_articles ?? 0}</div>
              <div className="mt-1 text-[10px] text-slate-300">Last 45 days</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 col-span-2 md:col-span-1">
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Data Source</div>
              <div className="mt-2 text-md font-semibold text-white">SerperDev API</div>
              <div className="mt-1 text-[10px] text-slate-300">Google News (India)</div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── DISTRIBUTION VISUALIZER ────────────────────────────────────────── */}
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-950">Sentiment Distribution</h3>
        <p className="mt-1 text-sm text-slate-500">Proportional breakdown of positive, neutral, and negative news headlines.</p>

        {/* Stacked Percentage Bar */}
        <div className="mt-6 flex h-4 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full bg-emerald-500 transition-all duration-500"
            style={{ width: `${dist.positive_pct ?? 0}%` }}
            title={`Positive: ${dist.positive_pct?.toFixed(1)}%`}
          />
          <div
            className="h-full bg-slate-400 transition-all duration-500"
            style={{ width: `${dist.neutral_pct ?? 0}%` }}
            title={`Neutral: ${dist.neutral_pct?.toFixed(1)}%`}
          />
          <div
            className="h-full bg-rose-500 transition-all duration-500"
            style={{ width: `${dist.negative_pct ?? 0}%` }}
            title={`Negative: ${dist.negative_pct?.toFixed(1)}%`}
          />
        </div>

        {/* Breakdown details */}
        <div className="mt-6 grid gap-4 grid-cols-1 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Positive Headlines</div>
              <div className="mt-1 text-lg font-bold text-slate-900">{dist.positive ?? 0} articles</div>
            </div>
            <span className="text-2xl font-extrabold text-emerald-600">{dist.positive_pct != null ? `${dist.positive_pct.toFixed(0)}%` : "0%"}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Neutral Headlines</div>
              <div className="mt-1 text-lg font-bold text-slate-900">{dist.neutral ?? 0} articles</div>
            </div>
            <span className="text-2xl font-extrabold text-slate-600">{dist.neutral_pct != null ? `${dist.neutral_pct.toFixed(0)}%` : "0%"}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Negative Headlines</div>
              <div className="mt-1 text-lg font-bold text-slate-900">{dist.negative ?? 0} articles</div>
            </div>
            <span className="text-2xl font-extrabold text-rose-600">{dist.negative_pct != null ? `${dist.negative_pct.toFixed(0)}%` : "0%"}</span>
          </div>
        </div>
      </section>

      {/* ─── NEWS FEED LIST ─────────────────────────────────────────────────── */}
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-950">Analyzed News Feed</h3>
            <p className="mt-1 text-sm text-slate-500">Deduplicated headlines collected and categorized by sentiment.</p>
          </div>

          {/* Filters */}
          <div className="flex gap-2 rounded-2xl bg-slate-100 p-1">
            {["all", "positive", "neutral", "negative"].map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setFilter(type)}
                className={`rounded-xl px-3 py-1.5 text-xs font-semibold capitalize transition-all ${
                  filter === type
                    ? "bg-white text-slate-950 shadow-xs"
                    : "text-slate-500 hover:text-slate-950"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Feed Cards */}
        <div className="mt-6 space-y-4">
          {filteredNews.length === 0 ? (
            <p className="text-center text-sm text-slate-500 py-6">No headlines matching the filter.</p>
          ) : (
            filteredNews.map((item, i) => {
              const label = (item.sentiment_label || "").toLowerCase();
              let badgeStyles = "bg-slate-100 text-slate-700 border-slate-200";
              if (label === "positive") {
                badgeStyles = "bg-emerald-50 text-emerald-700 border-emerald-200";
              } else if (label === "negative") {
                badgeStyles = "bg-rose-50 text-rose-700 border-rose-200";
              }

              return (
                <div key={i} className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 transition-all hover:bg-slate-100/50">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-700">{item.source || "Unknown Source"}</span>
                      <span>•</span>
                      <span>{item.date || "Recently"}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.deep_analyzed ? (
                        <span className="rounded-full border border-purple-200 bg-purple-50 px-2.5 py-0.5 text-[10px] font-bold text-purple-700 uppercase tracking-wider">
                          🔍 Deep Scraped & Re-classified
                        </span>
                      ) : null}
                      <span className={`rounded-full border px-2.5 py-0.5 font-bold uppercase tracking-wider text-[10px] ${badgeStyles}`}>
                        {item.sentiment_label || "Neutral"}
                      </span>
                    </div>
                  </div>

                  <h4 className="text-sm font-semibold leading-6 text-slate-900">
                    {item.link ? (
                      <a href={item.link} target="_blank" rel="noopener noreferrer" className="hover:underline">
                        {item.title}
                      </a>
                    ) : (
                      item.title
                    )}
                  </h4>

                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>
                      Confidence:{" "}
                      <span className="font-semibold text-slate-700">
                        {item.sentiment_confidence != null ? `${(item.sentiment_confidence * 100).toFixed(1)}%` : "N/A"}
                      </span>
                    </span>
                    {item.link ? (
                      <a href={item.link} target="_blank" rel="noopener noreferrer" className="font-semibold text-blue-600 hover:underline">
                        View Article →
                      </a>
                    ) : null}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
}
