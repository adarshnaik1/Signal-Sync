export default function Loading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center bg-linear-to-b from-blue-50 to-white px-6">
      <div className="flex flex-col items-center gap-4 rounded-3xl border border-blue-200 bg-white px-8 py-10 shadow-lg shadow-blue-100/60">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-700" />
        <p className="text-sm text-slate-500">Loading news sentiment analysis...</p>
      </div>
    </div>
  );
}
