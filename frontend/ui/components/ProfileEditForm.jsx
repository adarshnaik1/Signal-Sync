"use client";

import { useEffect, useState } from "react";

const FORM_FIELDS = [
  { key: "name", label: "Name", type: "text", disabled: true },
  { key: "age", label: "Age", type: "number" },
  { key: "annual_income", label: "Annual Income", type: "number", step: "0.01" },
  { key: "email", label: "Email", type: "email", disabled: true },
  { key: "phone_number", label: "Phone Number", type: "text" },
  { key: "number_of_dependents", label: "Number of Dependents", type: "number" },
  {
    key: "investor_type",
    label: "Investor Type",
    type: "select",
    options: ["Moderate", "Aggresive", "Conservative"],
  },
];

function toInputValue(value) {
  return value === null || value === undefined ? "" : String(value);
}

export default function ProfileEditForm({ customer, authUser, onSave, onCancel, saving, error }) {
  const [formData, setFormData] = useState({
    name: "",
    age: "",
    annual_income: "",
    email: "",
    phone_number: "",
    number_of_dependents: "",
    investor_type: "",
  });

  useEffect(() => {
    const displayName = toInputValue(authUser?.user_metadata?.full_name);
    const authEmail = toInputValue(authUser?.email);

    setFormData({
      name: displayName,
      age: toInputValue(customer?.age),
      annual_income: toInputValue(customer?.annual_income),
      email: authEmail,
      phone_number: toInputValue(customer?.phone_number),
      number_of_dependents: toInputValue(customer?.number_of_dependents),
      investor_type: toInputValue(customer?.investor_type),
    });
  }, [customer, authUser]);

  const handleChange = (key) => (event) => {
    setFormData((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await onSave(formData);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Edit Profile</h2>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-600 dark:text-zinc-200 dark:hover:bg-zinc-700"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-red-500">{error}</p> : null}

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {FORM_FIELDS.map((field) => (
          <label key={field.key} className="flex flex-col gap-2">
            <span className="text-sm font-medium text-zinc-600 dark:text-zinc-300">{field.label}</span>
            {field.type === "select" ? (
              <select
                value={formData[field.key]}
                onChange={handleChange(field.key)}
                className="w-full rounded-md border border-zinc-300 px-3 py-2 text-zinc-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100"
              >
                <option value="">Select investor type</option>
                {field.options.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={field.type}
                value={formData[field.key]}
                onChange={handleChange(field.key)}
                step={field.step}
                disabled={field.disabled}
                className="w-full rounded-md border border-zinc-300 px-3 py-2 text-zinc-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:cursor-not-allowed disabled:bg-zinc-100 disabled:text-zinc-500 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-400"
              />
            )}
          </label>
        ))}
      </div>
    </form>
  );
}
