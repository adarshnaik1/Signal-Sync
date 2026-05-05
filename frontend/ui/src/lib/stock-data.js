import YahooFinance from "yahoo-finance2";


const yf = new YahooFinance()

function rawValue(value) {
  if (value && typeof value === "object" && "raw" in value) {
    return value.raw;
  }

  return value ?? null;
}

function buildCandidates(symbol) {
  const trimmed = symbol.trim().toUpperCase();
  if (trimmed.includes(".")) {
    return [trimmed];
  }

  return [`${trimmed}.NS`];
}

function isLikelyEquity(payload) {
  const quoteType = String(payload?.quoteType || "").toUpperCase();
  const exchange = String(payload?.exchange || payload?.exchangeName || "").toUpperCase();

  if (quoteType && quoteType !== "EQUITY") {
    return false;
  }

  if (!exchange) {
    return true;
  }

  return !["MUTUALFUND", "ETF", "FUTURE", "OPTION", "CURRENCY"].includes(quoteType);
}

export async function getStockData(symbol) {
  const modules = [
    "price",
    "summaryDetail",
    "defaultKeyStatistics",
    "financialData",
    "assetProfile",
  ];

  for (const candidate of buildCandidates(symbol)) {
    try {
      const [summaryResult, quoteResult] = await Promise.allSettled([
        yf.quoteSummary(candidate, { modules }),
        yf.quote(candidate),
      ]);

      

      const summary = summaryResult.status === "fulfilled" ? summaryResult.value : null;
      const quote = quoteResult.status === "fulfilled" ? quoteResult.value : null;

      const quoteTypeSource = summary?.price ?? quote ?? {};

      if (summary || quote) {
        if (!isLikelyEquity(quoteTypeSource)) {
          continue;
        }

        const priceNode = summary?.price ?? quote ?? {};
        const detailNode = summary?.summaryDetail ?? {};
        const statisticsNode = summary?.defaultKeyStatistics ?? {};
        const financialNode = summary?.financialData ?? {};
        const profileNode = summary?.assetProfile ?? summary?.summaryProfile ?? {};

        return {
          symbol: candidate,
          companyName:
            rawValue(priceNode.longName) ??
            rawValue(priceNode.shortName) ??
            rawValue(quote?.longName) ??
            rawValue(quote?.shortName) ??
            candidate,
          price:
            rawValue(priceNode.regularMarketPrice) ??
            rawValue(quote?.regularMarketPrice) ??
            null,
          currency: rawValue(priceNode.currency) ?? rawValue(quote?.currency) ?? null,
          peRatio:
            rawValue(detailNode.trailingPE) ?? rawValue(statisticsNode.trailingPE) ?? null,
          marketCap:
            rawValue(priceNode.marketCap) ?? rawValue(statisticsNode.marketCap) ?? null,
          pb:
            rawValue(detailNode.priceToBook) ?? rawValue(statisticsNode.priceToBook) ?? null,
          dividendYield:
            rawValue(detailNode.dividendYield) ??
            rawValue(detailNode.trailingAnnualDividendYield) ??
            null,
          roe: rawValue(financialNode.returnOnEquity) ?? null,
          roce: rawValue(financialNode.returnOnCapitalEmployed) ?? null,
          faceValue:
            rawValue(detailNode.faceValue) ??
            rawValue(priceNode.faceValue) ??
            rawValue(statisticsNode.faceValue) ??
            null,
          description:
            rawValue(profileNode.longBusinessSummary) ??
            rawValue(profileNode.shortBusinessSummary) ??
            null,
          sector: rawValue(profileNode.sector) ?? null,
          industry: rawValue(profileNode.industry) ?? null,
          website: rawValue(profileNode.website) ?? null,
          dayHigh: rawValue(detailNode.dayHigh) ?? null,
          dayLow: rawValue(detailNode.dayLow) ?? null,
          previousClose: rawValue(detailNode.previousClose) ?? null,
          fiftyTwoWeekHigh: rawValue(detailNode.fiftyTwoWeekHigh) ?? null,
          fiftyTwoWeekLow: rawValue(detailNode.fiftyTwoWeekLow) ?? null,
        };
      }
    } catch (error) {
      console.error(`Yahoo lookup failed for ${candidate}:`, error);
    }
  }

  return null;
}