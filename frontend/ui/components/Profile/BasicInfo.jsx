"use client";

import { useEffect, useState } from "react";

const INVESTOR_TYPES = ["Moderate", "Aggresive", "Conservative"];

const INITIAL_FORM = {
  name: "",
  age: "",
  annual_income: "",
  email: "",
  phone_number: "",
  number_of_dependents: "",
  investor_type: "",
};

function toInputValue(value) {
  return value === null || value === undefined ? "" : String(value);
}

function toDisplayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }
  return String(value);
}

export default function BasicInfo({ customer, authUser, onSave, saving }) {
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(INITIAL_FORM);

  useEffect(() => {
    setForm({
      name: toInputValue(authUser?.user_metadata?.full_name),
      age: toInputValue(customer?.age),
      annual_income: toInputValue(customer?.annual_income),
      email: toInputValue(authUser?.email),
      phone_number: toInputValue(customer?.phone_number),
      number_of_dependents: toInputValue(customer?.number_of_dependents),
      investor_type: toInputValue(customer?.investor_type),
    });
  }, [customer, authUser]);

  const handleChange = (key) => (event) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    const result = await onSave(form);
    if (result?.error) {
      setError(result.error);
      return;
    }
    setIsEditing(false);
  };

  if (!isEditing) {
    return (
      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Basic Information</h2>
          <button
            type="button"
            onClick={() => setIsEditing(true)}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
          >
            Edit
          </button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            ["Name", authUser?.user_metadata?.full_name],
            ["Age", customer?.age],
            ["Annual Income", customer?.annual_income],
            ["Email", authUser?.email],
            ["Phone Number", customer?.phone_number],
            ["Number Of Dependents", customer?.number_of_dependents],
            ["Investor Type", customer?.investor_type],
          ].map(([label, value]) => (
            <div
              key={label}
              className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900"
            >
              <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{label}</p>
              <p className="mt-1 text-zinc-900 dark:text-zinc-100">{toDisplayValue(value)}</p>
            </div>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Basic Information</h2>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error ? <p className="text-sm text-red-500">{error}</p> : null}
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-2">
            <span className="text-sm text-zinc-600 dark:text-zinc-300">Name</span>
            <input
              type="text"
              value={form.name}
              disabled
              className="rounded-md border border-zinc-300 bg-zinc-100 px-3 py-2 text-zinc-600 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-300"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-sm text-zinc-600 dark:text-zinc-300">Email</span>
            <input
              type="email"
              value={form.email}
              disabled
              className="rounded-md border border-zinc-300 bg-zinc-100 px-3 py-2 text-zinc-600 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-300"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-sm text-zinc-600 dark:text-zinc-300">Age</span>
            <input
              type="number"
              value={form.age}
              onChange={handleChange("age")}
              className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-sm text-zinc-600 dark:text-zinc-300">Annual Income</span>
            <input
              type="number"
              step="0.01"
              value={form.annual_income}
              onChange={handleChange("annual_income")}
              className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-sm text-zinc-600 dark:text-zinc-300">Phone Number</span>
            <input
              type="text"
              value={form.phone_number}
              onChange={handleChange("phone_number")}
              className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-sm text-zinc-600 dark:text-zinc-300">Number Of Dependents</span>
            <input
              type="number"
              value={form.number_of_dependents}
              onChange={handleChange("number_of_dependents")}
              className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
            />
          </label>
          <label className="flex flex-col gap-2 sm:col-span-2">
            <span className="text-sm text-zinc-600 dark:text-zinc-300">Investor Type</span>
            <select
              value={form.investor_type}
              onChange={handleChange("investor_type")}
              className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
            >
              <option value="">Select investor type</option>
              {INVESTOR_TYPES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => {
              setError("");
              setIsEditing(false);
            }}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm dark:border-zinc-600"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-70"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </section>
  );
}
