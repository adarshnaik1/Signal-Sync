"use client";

const FIELDS = [
  { key: "name", label: "Name" },
  { key: "age", label: "Age" },
  { key: "annual_income", label: "Annual Income" },
  { key: "email", label: "Email" },
  { key: "phone_number", label: "Phone Number" },
  { key: "number_of_dependents", label: "Number of Dependents" },
  { key: "investor_type", label: "Investor Type" },
];

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }

  return String(value);
}

export default function ProfileView({ authUser, customer, onEdit }) {
  const displayName = authUser?.user_metadata?.full_name || "Not provided";
  const authEmail = authUser?.email || "Not provided";
  const customerForDisplay = {
    ...customer,
    name: displayName,
    email: authEmail,
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Account</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Display Name</p>
            <p className="mt-1 text-base text-zinc-900 dark:text-zinc-100">{displayName}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Auth Email</p>
            <p className="mt-1 text-base text-zinc-900 dark:text-zinc-100">{authEmail}</p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Customer Profile</h2>
          <button
            type="button"
            onClick={onEdit}
            className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500"
          >
            Edit Profile
          </button>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {FIELDS.map((field) => (
            <div
              key={field.key}
              className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900"
            >
              <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{field.label}</p>
              <p className="mt-1 text-base text-zinc-900 dark:text-zinc-100">
                {formatValue(customerForDisplay?.[field.key])}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
