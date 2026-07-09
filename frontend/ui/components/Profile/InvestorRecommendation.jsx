"use client";

const ASSET_LABELS = {
  equity: "Equity",
  debt: "Debt",
  gold: "Gold",
  cash: "Cash",
};

function formatCurrency(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

export default function InvestorRecommendation({
  recommendation,
  latestRecommendation,
  missingFields,
  totals,
  loading,
  error,
  onGenerate,
}) {
  const visibleRecommendation = recommendation || latestRecommendation;
  const allocation = visibleRecommendation?.allocation || {
    equity: visibleRecommendation?.equity_pct,
    debt: visibleRecommendation?.debt_pct,
    gold: visibleRecommendation?.gold_pct,
    cash: visibleRecommendation?.cash_pct,
  };

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Investor Recommendation</h2>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
            Model-based investor type and suggested asset allocation.
          </p>
        </div>
        <button
          type="button"
          onClick={onGenerate}
          disabled={loading || missingFields.length > 0}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Generating..." : "Generate"}
        </button>
      </div>

      {error ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      ) : null}

      {missingFields.length > 0 ? (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          <p className="font-medium">Complete these fields before generating:</p>
          <p className="mt-2">{missingFields.join(", ")}</p>
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 sm:grid-cols-4">
        <Metric label="Total Assets" value={formatCurrency(totals.totalAssets)} />
        <Metric label="Liquid Assets" value={formatCurrency(totals.totalLiquidAssets)} />
        <Metric label="Stocks" value={formatCurrency(totals.totalStockAssets)} />
        <Metric label="Debt" value={formatCurrency(totals.totalLiabilities)} />
      </div>

      {visibleRecommendation ? (
        <div className="mt-6">
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Recommended Profile</p>
            <p className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
              {visibleRecommendation.investor_label || visibleRecommendation.investor_type_label}
            </p>
            {visibleRecommendation.investor_description ? (
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
                {visibleRecommendation.investor_description}
              </p>
            ) : null}
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-4">
            {Object.entries(allocation || {}).map(([asset, value]) => (
              <div key={asset} className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900">
                <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{ASSET_LABELS[asset] || asset}</p>
                <p className="mt-1 text-xl font-semibold">{Number(value || 0).toFixed(2)}%</p>
                <div className="mt-3 h-2 rounded-full bg-zinc-200 dark:bg-zinc-700">
                  <div
                    className="h-2 rounded-full bg-blue-600"
                    style={{ width: `${Math.min(Math.max(Number(value || 0), 0), 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="mt-5 text-sm text-zinc-500 dark:text-zinc-400">No recommendation generated yet.</p>
      )}
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900">
      <p className="text-sm text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="mt-1 text-lg font-semibold text-zinc-900 dark:text-zinc-100">{value}</p>
    </div>
  );
}
