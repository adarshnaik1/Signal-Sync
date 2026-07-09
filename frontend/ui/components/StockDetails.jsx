"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

const BGV_API_BASE = process.env.NEXT_PUBLIC_BGV_API_BASE_URL || "";
const TA_API_BASE = process.env.NEXT_PUBLIC_TA_API_BASE_URL || BGV_API_BASE;

export default function StockDetails({ data }) {
  const {
    companyName,
    symbol,
    price,
    currency,
    peRatio,
    marketCap,
    pb,
    dividendYield,
    roe,
    description,
    sector,
    industry,
    website,
    previousClose,
    fiftyTwoWeekHigh,
    fiftyTwoWeekLow,
  } = data;

  const formatNumber = (value) => {
    if (value == null) return "—";
    if (typeof value === "number") {
      if (Math.abs(value) >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
      if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
      if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
      return value.toLocaleString();
    }
    return String(value);
  };

  const formatPercent = (value) => {
    if (value == null || Number.isNaN(Number(value))) return "—";
    return `${(Number(value) * 100).toFixed(2)}%`;
  };

  const stats = [
    { label: "Price", value: price == null ? "—" : `${price} ${currency || ""}`.trim() },
    { label: "P/E Ratio", value: peRatio ?? "—" },
    { label: "Dividend Yield", value: formatPercent(dividendYield) },
    { label: "ROE", value: formatPercent(roe) },
    { label: "P/B", value: pb ?? "—" },
    { label: "Market Cap", value: formatNumber(marketCap) },
    { label: "Prev Close", value: formatNumber(previousClose) },
    { label: "52W High", value: formatNumber(fiftyTwoWeekHigh) },
    { label: "52W Low", value: formatNumber(fiftyTwoWeekLow) },
  ];

  const router = useRouter();
  const [loadingAction, setLoadingAction] = useState(null);
  const [error, setError] = useState(null);

  const startAnalysis = async ({ label, apiBase, routePrefix, formFields }) => {
    if (!symbol) return;

    try {
      setError(null);
      setLoadingAction(label);
      const form = new FormData();
      Object.entries(formFields).forEach(([key, value]) => {
        form.append(key, value ?? "");
      });

      const res = await fetch(`${apiBase}/api/${routePrefix}/start`, { method: "POST", body: form });
      const text = await res.text();
      if (!res.ok) {
        throw new Error(text || `Failed to start ${label}`);
      }

      let json;
      try {
        json = JSON.parse(text);
      } catch {
        throw new Error(`Invalid API response: ${text.slice(0, 120)}`);
      }

      if (!json?.job_id) {
        throw new Error(`Missing job id in ${label} response`);
      }

      router.push(`/${routePrefix}/${json.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl rounded-3xl border border-slate-200 bg-zinc-100 p-6 shadow-lg shadow-slate-200/60 sm:p-8">
      <div className="flex flex-col gap-6 border-b border-slate-200 pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
              {companyName || symbol}
            </h2>
            {symbol ? (
              <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-600">
                {symbol}
              </span>
            ) : null}
          </div>

          <div className="mt-3">
            <div className="mt-3 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() =>
                  startAnalysis({
                    label: "BGV analysis",
                    apiBase: BGV_API_BASE,
                    routePrefix: "bgv",
                    formFields: {
                      company_name: companyName || symbol,
                      ticker: symbol,
                      sector: sector || "",
                    },
                  })
                }
                className="inline-flex items-center rounded-md bg-amber-400 px-3 py-1.5 text-sm font-semibold text-slate-900 shadow-sm hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loadingAction !== null}
              >
                {loadingAction === "BGV analysis" ? "Starting..." : "Run BGV Analysis"}
              </button>

              <button
                type="button"
                onClick={() =>
                  startAnalysis({
                    label: "TA analysis",
                    apiBase: TA_API_BASE,
                    routePrefix: "ta",
                    formFields: {
                      company_name: companyName || symbol,
                      ticker: symbol,
                      sector: sector || "",
                      horizon: "medium-term",
                    },
                  })
                }
                className="inline-flex items-center rounded-md bg-slate-950 px-3 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loadingAction !== null}
              >
                {loadingAction === "TA analysis" ? "Starting..." : "Run TA Analysis"}
              </button>
            </div>
          </div>

          {error ? (
            <div className="mt-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <div className="border-white border mt-2 text-sm text-black lg:w-80 rounded-2xl p-2  bg-amber-200/40 shadow-amber-300 shadow">
                {sector ? <span>{sector}</span> : null}
            {industry ? <span>{industry}</span> : null}
          </div>



          
        </div>

        <div className="rounded-2xl bg-slate-950 px-5 py-4 text-white">
          <div className="text-3xl font-bold tracking-tight">
            {price == null ? "—" : `${price} ${currency || ""}`.trim()}
          </div>
          <div className="mt-1 text-sm text-slate-300">Current price</div>
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
              {stat.label}
            </div>
            <div className="mt-2 text-lg font-semibold text-slate-950">{stat.value}</div>
          </div>
        ))}
      </div>

      {website ? (
        <div className="mt-6 text-sm text-slate-600">
          Website: {" "}
          <a className="font-medium text-slate-950 underline underline-offset-4" href={website} target="_blank" rel="noreferrer">
            {website}
          </a>
        </div>
      ) : null}

      {description ? (
        <div className="mt-6 rounded-2xl bg-slate-50 p-5 text-sm leading-7 text-slate-700">
          {description}
        </div>
      ) : null}
    </div>
  );
}
