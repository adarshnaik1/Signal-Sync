"use client";

import { useState } from "react";

const EDUCATION_OPTIONS = [
  { value: "1", label: "School or below" },
  { value: "2", label: "Graduate" },
  { value: "3", label: "Postgraduate or above" },
  { value: "-1", label: "Other or unknown" },
];

const YES_NO_OPTIONS = [
  { value: "true", label: "Yes" },
  { value: "false", label: "No" },
];

const INITIAL_FORM = {
  name: "",
  age: "",
  annual_income: "",
  email: "",
  phone_number: "",
  number_of_dependents: "",
  education_level_code: "",
  is_married: "",
  saves_regularly: "",
  has_emergency_fund: "",
};

function toInputValue(value) {
  return value === null || value === undefined ? "" : String(value);
}

function toBooleanInputValue(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return value ? "true" : "false";
}

function toDisplayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }
  return String(value);
}

function getEducationLabel(value) {
  const option = EDUCATION_OPTIONS.find((item) => item.value === String(value));
  return option?.label ?? toDisplayValue(value);
}

function getBooleanLabel(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }
  return value ? "Yes" : "No";
}

export default function BasicInfo({ customer, authUser, onSave, saving }) {
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(() => buildForm(customer, authUser));

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
            onClick={() => {
              setForm(buildForm(customer, authUser));
              setIsEditing(true);
            }}
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
            ["Education", getEducationLabel(customer?.education_level_code)],
            ["Married", getBooleanLabel(customer?.is_married)],
            ["Saves Regularly", getBooleanLabel(customer?.saves_regularly)],
            ["Emergency Fund", getBooleanLabel(customer?.has_emergency_fund)],
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
          <TextInput label="Name" value={form.name} disabled />
          <TextInput label="Email" type="email" value={form.email} disabled />
          <TextInput label="Age" type="number" value={form.age} onChange={handleChange("age")} />
          <TextInput
            label="Annual Income"
            type="number"
            step="0.01"
            value={form.annual_income}
            onChange={handleChange("annual_income")}
          />
          <TextInput label="Phone Number" value={form.phone_number} onChange={handleChange("phone_number")} />
          <TextInput
            label="Number Of Dependents"
            type="number"
            value={form.number_of_dependents}
            onChange={handleChange("number_of_dependents")}
          />
          <SelectInput
            label="Education"
            value={form.education_level_code}
            onChange={handleChange("education_level_code")}
            placeholder="Select education"
            options={EDUCATION_OPTIONS}
          />
          <SelectInput
            label="Married"
            value={form.is_married}
            onChange={handleChange("is_married")}
            placeholder="Select status"
            options={YES_NO_OPTIONS}
          />
          <SelectInput
            label="Saves Regularly"
            value={form.saves_regularly}
            onChange={handleChange("saves_regularly")}
            placeholder="Select savings habit"
            options={YES_NO_OPTIONS}
          />
          <SelectInput
            label="Emergency Fund"
            value={form.has_emergency_fund}
            onChange={handleChange("has_emergency_fund")}
            placeholder="Select emergency fund status"
            options={YES_NO_OPTIONS}
          />
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

function buildForm(customer, authUser) {
  return {
    ...INITIAL_FORM,
    name: toInputValue(authUser?.user_metadata?.full_name),
    age: toInputValue(customer?.age),
    annual_income: toInputValue(customer?.annual_income),
    email: toInputValue(authUser?.email),
    phone_number: toInputValue(customer?.phone_number),
    number_of_dependents: toInputValue(customer?.number_of_dependents),
    education_level_code: toInputValue(customer?.education_level_code),
    is_married: toBooleanInputValue(customer?.is_married),
    saves_regularly: toBooleanInputValue(customer?.saves_regularly),
    has_emergency_fund: toBooleanInputValue(customer?.has_emergency_fund),
  };
}

function TextInput({ label, disabled = false, type = "text", step, value, onChange }) {
  return (
    <label className="flex flex-col gap-2">
      <span className="text-sm text-zinc-600 dark:text-zinc-300">{label}</span>
      <input
        type={type}
        step={step}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className="rounded-md border border-zinc-300 px-3 py-2 disabled:bg-zinc-100 disabled:text-zinc-600 dark:border-zinc-600 dark:bg-zinc-900 dark:disabled:bg-zinc-900 dark:disabled:text-zinc-300"
      />
    </label>
  );
}

function SelectInput({ label, value, onChange, placeholder, options }) {
  return (
    <label className="flex flex-col gap-2">
      <span className="text-sm text-zinc-600 dark:text-zinc-300">{label}</span>
      <select
        value={value}
        onChange={onChange}
        className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-600 dark:bg-zinc-900"
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
