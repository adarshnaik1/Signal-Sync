"use client";

import { useState } from "react";

function toDisplayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }
  return String(value);
}

export default function AssetsSection({ assets, totalAssets, onAdd, onUpdate, onDelete }) {
  const [newAsset, setNewAsset] = useState({ asset_value: "", current_value: "" });
  const [editingId, setEditingId] = useState(null);
  const [editingRow, setEditingRow] = useState({ asset_value: "", current_value: "" });
  const [error, setError] = useState("");

  const addAsset = async (event) => {
    event.preventDefault();
    setError("");
    const result = await onAdd(newAsset);
    if (result?.error) {
      setError(result.error);
      return;
    }
    setNewAsset({ asset_value: "", current_value: "" });
  };

  const startEdit = (row) => {
    setEditingId(row.asset_id);
    setEditingRow({
      asset_value: toDisplayValue(row.asset_value) === "Not provided" ? "" : String(row.asset_value),
      current_value: toDisplayValue(row.current_value) === "Not provided" ? "" : String(row.current_value),
    });
  };

  const saveEdit = async (assetId) => {
    setError("");
    const result = await onUpdate(assetId, editingRow);
    if (result?.error) {
      setError(result.error);
      return;
    }
    setEditingId(null);
  };

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Assets</h2>
        <span className="text-sm font-medium text-zinc-600 dark:text-zinc-300">Total: {totalAssets}</span>
      </div>

      {error ? <p className="mb-3 text-sm text-red-500">{error}</p> : null}

      <form onSubmit={addAsset} className="mb-5 grid gap-3 sm:grid-cols-3">
        <input
          placeholder="Asset Value"
          type="number"
          value={newAsset.asset_value}
          onChange={(e) => setNewAsset((prev) => ({ ...prev, asset_value: e.target.value }))}
          className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
        />
        <input
          placeholder="Current Value"
          type="number"
          step="0.01"
          value={newAsset.current_value}
          onChange={(e) => setNewAsset((prev) => ({ ...prev, current_value: e.target.value }))}
          className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
        />
        <button type="submit" className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500">
          Add Asset
        </button>
      </form>

      {assets.length === 0 ? (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">No data available</p>
      ) : (
        <div className="space-y-3">
          {assets.map((asset) => (
            <div
              key={asset.asset_id}
              className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900"
            >
              {editingId === asset.asset_id ? (
                <div className="grid gap-3 sm:grid-cols-4">
                  <input
                    type="number"
                    value={editingRow.asset_value}
                    onChange={(e) => setEditingRow((prev) => ({ ...prev, asset_value: e.target.value }))}
                    className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-800"
                  />
                  <input
                    type="number"
                    step="0.01"
                    value={editingRow.current_value}
                    onChange={(e) => setEditingRow((prev) => ({ ...prev, current_value: e.target.value }))}
                    className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-800"
                  />
                  <button
                    type="button"
                    onClick={() => saveEdit(asset.asset_id)}
                    className="rounded-md bg-emerald-600 px-3 py-2 text-sm text-white"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingId(null)}
                    className="rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-600"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="text-sm text-zinc-700 dark:text-zinc-200">
                    <p>Asset Value: {toDisplayValue(asset.asset_value)}</p>
                    <p>Current Value: {toDisplayValue(asset.current_value)}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => startEdit(asset)}
                      className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm dark:border-zinc-600"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(asset.asset_id)}
                      className="rounded-md bg-red-600 px-3 py-1.5 text-sm text-white"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
