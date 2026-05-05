import { getStockData } from "../../../lib/stock-data";
import StockDetails from "../../../../components/StockDetails";

export default async function StockPage({ params }) {
  const { symbol: rawSymbol = "" } = (await params) ?? {};
  const symbol = String(rawSymbol).toUpperCase();

  if (!symbol) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-3xl items-center justify-center px-6">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 shadow-sm">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-red-500">
            Dashboard error
          </p>
          <h1 className="mt-2 text-2xl font-bold">Stock</h1>
          <p className="mt-3 text-sm">Missing symbol</p>
        </div>
      </div>
    );
  }

  const data = await getStockData(symbol);

  if (!data) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-3xl items-center justify-center px-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-slate-900">{symbol || "Stock"}</h1>
          <p className="mt-3 text-sm text-slate-500">No company data available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] bg-linear-to-b bg-zinc-900 px-4 py-8 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-white">
            Company Dashboard
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {data.companyName || symbol}
          </h1>
          <p className="mt-2 text-sm text-white">
            {data.symbol || symbol}
            
          </p>
          
         
                <div className="border-green-700 border mt-2 text-sm text-white lg:w-80 rounded-2xl p-2  bg-green-400/15 shadow-green-300 shadow">
                {data.sector ? `  ${data.sector}` : ""}
                {data.industry ? ` · ${data.industry}` : ""}
                </div>
           
          
        </div>
        <StockDetails data={data} />
      </div>
    </div>
  );
}