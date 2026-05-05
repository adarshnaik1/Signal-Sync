import { getStockData } from "../../../lib/stock-data";

export async function GET(req) {
  try {
    const { searchParams } = new URL(req.url);
    const symbol = (searchParams.get("symbol") || "").trim();

    if (!symbol) {
      return Response.json({ error: "Missing symbol" }, { status: 400 });
    }

    const data = await getStockData(symbol);

    if (!data) {
      return Response.json(
        { error: `No market data found for ${symbol}` },
        { status: 404 }
      );
    }

    return Response.json(data);
  } catch (error) {
    console.error("Error in /api/stock:", error);
    return Response.json({ error: "Failed to fetch data" }, { status: 500 });
  }
}