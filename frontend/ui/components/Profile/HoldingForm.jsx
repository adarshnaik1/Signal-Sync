"use client";

import { useState } from "react";

const INITIAL_FORM = {
  ticker: "",
  quantity: "",
  buy_price: "",
  date_of_purchase: "",
};

export default function HoldingForm({ onSubmit, submitting }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [error, setError] = useState("");

  const handleChange = (key) => (event) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    const result = await onSubmit(form);
    if (result?.error) {
      setError(result.error);
      return;
    }
    setForm(INITIAL_FORM);
  };

  return (
    <form onSubmit={handleSubmit} className="mt-3 grid gap-3 rounded-lg border border-zinc-200 p-3 dark:border-zinc-700">
      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      <div className="grid gap-3 sm:grid-cols-2">
        <input
          type="text"
          placeholder="Ticker (e.g. AAPL)"
          value={form.ticker}
          onChange={handleChange("ticker")}
          className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
        />
        <input
          type="number"
          placeholder="Quantity"
          value={form.quantity}
          onChange={handleChange("quantity")}
          className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
        />
        <input
          type="number"
          step="0.01"
          placeholder="Buy Price"
          value={form.buy_price}
          onChange={handleChange("buy_price")}
          className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
        />
        <input
          type="date"
          value={form.date_of_purchase}
          onChange={handleChange("date_of_purchase")}
          className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
        />
      </div>
      <div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-70"
        >
          {submitting ? "Adding..." : "Add Holding"}
        </button>
      </div>
    </form>
  );
}
