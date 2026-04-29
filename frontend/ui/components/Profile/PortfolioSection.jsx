"use client";

import { useState } from "react";
import PortfolioCard from "./PortfolioCard";

export default function PortfolioSection({
  portfolios,
  holdingsByPortfolio,
  onCreatePortfolio,
  onUpdatePortfolio,
  onDeletePortfolio,
  onAddHolding,
  onUpdateHolding,
  onDeleteHolding,
}) {
  const [portfolioName, setPortfolioName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const handleCreate = async (event) => {
    event.preventDefault();
    setError("");
    setCreating(true);
    const result = await onCreatePortfolio({ portfolio_name: portfolioName });
    setCreating(false);
    if (result?.error) {
      setError(result.error);
      return;
    }
    setPortfolioName("");
  };

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
      <h2 className="mb-5 text-xl font-semibold text-zinc-900 dark:text-zinc-100">Portfolios</h2>

      <form onSubmit={handleCreate} className="mb-5 grid gap-3 sm:grid-cols-3">
        <input
          type="text"
          placeholder="Portfolio name"
          value={portfolioName}
          onChange={(event) => setPortfolioName(event.target.value)}
          className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900 sm:col-span-2"
        />
        <button
          type="submit"
          disabled={creating}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-70"
        >
          {creating ? "Creating..." : "Create Portfolio"}
        </button>
      </form>

      {error ? <p className="mb-3 text-sm text-red-500">{error}</p> : null}

      {portfolios.length === 0 ? (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">No portfolios created</p>
      ) : (
        <div className="space-y-4">
          {portfolios.map((portfolio) => (
            <PortfolioCard
              key={portfolio.portfolio_id}
              portfolio={portfolio}
              holdings={holdingsByPortfolio[portfolio.portfolio_id] ?? []}
              onUpdatePortfolio={onUpdatePortfolio}
              onDeletePortfolio={onDeletePortfolio}
              onAddHolding={onAddHolding}
              onUpdateHolding={onUpdateHolding}
              onDeleteHolding={onDeleteHolding}
            />
          ))}
        </div>
      )}
    </section>
  );
}
