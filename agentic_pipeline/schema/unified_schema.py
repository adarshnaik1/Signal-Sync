from datetime import datetime
import pandas as pd

def extract_metric(dataframe, metric_name):

    if metric_name not in dataframe.index:
        return None

    series = dataframe.loc[metric_name]

    cleaned_data = {}

    for date, value in series.items():

        year = str(date.year)

        if pd.notna(value):
            cleaned_data[year] = float(value)

    return cleaned_data


def build_schema(raw_data,news_data):

    info = raw_data["info"]

    financials = raw_data["financials"]
    balance_sheet = raw_data["balance_sheet"]
    cashflow = raw_data["cashflow"]

    schema = {

        "timestamp": datetime.now().isoformat(),

        "company_identification": {
            "symbol": info.get("symbol"),
            "long_name": info.get("longName"),
            "exchange": info.get("exchange")
        },

        "company_metadata": {
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "business_summary": info.get("longBusinessSummary")
        },

        "market_data": {
            "market_cap": info.get("marketCap"),
            "current_price": info.get("currentPrice"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "volume": info.get("volume"),
            "average_volume": info.get("averageVolume")
        },

        "financial_ratios": {
            "pe_ratio": info.get("trailingPE"),
            "debt_to_equity": info.get("debtToEquity"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "profit_margin": info.get("profitMargins")
        },

        "financial_data": {

            "income_statement": {
                "total_revenue": extract_metric(financials, "Total Revenue"),
                "gross_profit": extract_metric(financials, "Gross Profit"),
                "operating_income": extract_metric(financials, "Operating Income"),
                "ebitda": extract_metric(financials, "EBITDA"),
                "net_income": extract_metric(financials, "Net Income"),
                "diluted_eps": extract_metric(financials, "Diluted EPS")
            },

            "balance_sheet": {
                "total_debt": extract_metric(balance_sheet, "Total Debt"),
                "cash_and_cash_equivalents": extract_metric(balance_sheet, "Cash And Cash Equivalents"),
                "total_assets": extract_metric(balance_sheet, "Total Assets"),
                "total_liabilities": extract_metric(balance_sheet, "Total Liabilities Net Minority Interest"),
                "shareholders_equity": extract_metric(balance_sheet, "Stockholders Equity")
            },

            "cash_flow": {
                "operating_cash_flow": extract_metric(cashflow, "Operating Cash Flow"),
                "free_cash_flow": extract_metric(cashflow, "Free Cash Flow"),
                "capital_expenditure": extract_metric(cashflow, "Capital Expenditure")
            }

        },

        "news_data": news_data

    }

    return schema