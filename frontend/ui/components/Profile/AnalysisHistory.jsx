"use client";

function toDisplayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }
  return String(value);
}

function formatDate(value) {
  if (!value) {
    return "Not provided";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not provided";
  }

  return date.toLocaleString();
}

export default function AnalysisHistory({ analysisHistory }) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
      <h2 className="mb-5 text-xl font-semibold text-zinc-900 dark:text-zinc-100">Analysis History</h2>

      {analysisHistory.length === 0 ? (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">No data available</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-zinc-500 dark:text-zinc-400">
              <tr>
                <th className="px-3 py-2">Analysis Type</th>
                <th className="px-3 py-2">Date Of Analysis</th>
              </tr>
            </thead>
            <tbody>
              {analysisHistory.map((item) => (
                <tr key={item.analysis_id} className="border-t border-zinc-200 dark:border-zinc-700">
                  <td className="px-3 py-2">{toDisplayValue(item.analysis_type)}</td>
                  <td className="px-3 py-2">{formatDate(item.date_of_analysis)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
