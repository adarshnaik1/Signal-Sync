"use client";

import { useMemo, useState } from "react";
import HoldingForm from "./HoldingForm";

function toDisplayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }
  return String(value);
}

function toNullableString(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const normalized = String(value).trim();
  return normalized === "" ? null : normalized;
}

function formatCurrency(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatDate(value) {
  if (!value) {
    return "Not provided";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return toDisplayValue(value);
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

export default function PortfolioCard({
  portfolio,
  holdings,
  onUpdatePortfolio,
  onDeletePortfolio,
  onAddHolding,
  onUpdateHolding,
  onDeleteHolding,
}) {
  const [isEditingPortfolio, setIsEditingPortfolio] = useState(false);
  const [portfolioName, setPortfolioName] = useState(portfolio?.portfolio_name ?? "");
  const [portfolioError, setPortfolioError] = useState("");
  const [showHoldingForm, setShowHoldingForm] = useState(false);
  const [holdingSubmitting, setHoldingSubmitting] = useState(false);
  const [editingHoldingId, setEditingHoldingId] = useState(null);
  const [editingHoldingData, setEditingHoldingData] = useState({ quantity: "", buy_price: "" });

  const totalPortfolioValue = useMemo(
    () =>
      holdings.reduce(
        (sum, item) => sum + Number(item.quantity || 0) * Number(item.buy_price || 0),
        0
      ),
    [holdings]
  );

  const submitPortfolioEdit = async () => {
    setPortfolioError("");
    const result = await onUpdatePortfolio(portfolio.portfolio_id, { portfolio_name: portfolioName });
    if (result?.error) {
      setPortfolioError(result.error);
      return;
    }
    setIsEditingPortfolio(false);
  };

  const submitHolding = async (payload) => {
    setHoldingSubmitting(true);
    const result = await onAddHolding(portfolio.portfolio_id, payload);
    setHoldingSubmitting(false);
    if (!result?.error) {
      setShowHoldingForm(false);
    }
    return result;
  };

  const saveHoldingEdit = async (holdingId) => {
    const result = await onUpdateHolding(holdingId, editingHoldingData);
    if (result?.error) {
      setPortfolioError(result.error);
      return;
    }
    setEditingHoldingId(null);
  };

  return (
    <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          {isEditingPortfolio ? (
            <div className="flex gap-2">
              <input
                value={portfolioName}
                onChange={(event) => setPortfolioName(event.target.value)}
                className="rounded-md border border-zinc-300 px-3 py-1.5 dark:border-zinc-600 dark:bg-zinc-800"
              />
              <button
                type="button"
                onClick={submitPortfolioEdit}
                className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm text-white"
              >
                Save
              </button>
              <button
                type="button"
                onClick={() => {
                  setPortfolioName(portfolio?.portfolio_name ?? "");
                  setIsEditingPortfolio(false);
                }}
                className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm dark:border-zinc-600"
              >
                Cancel
              </button>
            </div>
          ) : (
            <>
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                {toDisplayValue(portfolio?.portfolio_name)}
              </h3>
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
                Total Value: {formatCurrency(totalPortfolioValue)}
              </p>
            </>
          )}
        </div>

        <div className="flex gap-2">
          {!isEditingPortfolio ? (
            <button
              type="button"
              onClick={() => setIsEditingPortfolio(true)}
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm dark:border-zinc-600"
            >
              Edit Portfolio
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => onDeletePortfolio(portfolio.portfolio_id)}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm text-white"
          >
            Delete Portfolio
          </button>
          <button
            type="button"
            onClick={() => setShowHoldingForm((prev) => !prev)}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white"
          >
            {showHoldingForm ? "Close Holding Form" : "Add Holding"}
          </button>
        </div>
      </div>

      {portfolioError ? <p className="mt-3 text-sm text-red-500">{portfolioError}</p> : null}

      {showHoldingForm ? <HoldingForm onSubmit={submitHolding} submitting={holdingSubmitting} /> : null}

      <div className="mt-4">
        {holdings.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No holdings added</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-zinc-500 dark:text-zinc-400">
                <tr>
                  <th className="px-3 py-2">Ticker</th>
                  <th className="px-3 py-2">Quantity</th>
                  <th className="px-3 py-2">Buy Price</th>
                  <th className="px-3 py-2">Date Of Purchase</th>
                  <th className="px-3 py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding) => (
                  <tr key={holding.holding_id} className="border-t border-zinc-200 dark:border-zinc-700">
                    <td className="px-3 py-2">{toDisplayValue(holding.ticker)}</td>
                    <td className="px-3 py-2">
                      {editingHoldingId === holding.holding_id ? (
                        <input
                          type="number"
                          value={editingHoldingData.quantity}
                          onChange={(event) =>
                            setEditingHoldingData((prev) => ({ ...prev, quantity: event.target.value }))
                          }
                          className="w-24 rounded-md border border-zinc-300 px-2 py-1 dark:border-zinc-600 dark:bg-zinc-800"
                        />
                      ) : (
                        toDisplayValue(holding.quantity)
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {editingHoldingId === holding.holding_id ? (
                        <input
                          type="number"
                          step="0.01"
                          value={editingHoldingData.buy_price}
                          onChange={(event) =>
                            setEditingHoldingData((prev) => ({ ...prev, buy_price: event.target.value }))
                          }
                          className="w-28 rounded-md border border-zinc-300 px-2 py-1 dark:border-zinc-600 dark:bg-zinc-800"
                        />
                      ) : (
                        toDisplayValue(holding.buy_price)
                      )}
                    </td>
                    <td className="px-3 py-2">{formatDate(holding.date_of_purchase)}</td>
                    <td className="px-3 py-2">
                      <div className="flex gap-2">
                        {editingHoldingId === holding.holding_id ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveHoldingEdit(holding.holding_id)}
                              className="rounded-md bg-emerald-600 px-2 py-1 text-xs text-white"
                            >
                              Save
                            </button>
                            <button
                              type="button"
                              onClick={() => setEditingHoldingId(null)}
                              className="rounded-md border border-zinc-300 px-2 py-1 text-xs dark:border-zinc-600"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => {
                                setEditingHoldingId(holding.holding_id);
                                setEditingHoldingData({
                                  quantity: toNullableString(holding.quantity) ?? "",
                                  buy_price: toNullableString(holding.buy_price) ?? "",
                                });
                              }}
                              className="rounded-md border border-zinc-300 px-2 py-1 text-xs dark:border-zinc-600"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => onDeleteHolding(holding.holding_id, portfolio.portfolio_id)}
                              className="rounded-md bg-red-600 px-2 py-1 text-xs text-white"
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
