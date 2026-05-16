from tools.financial_tool import fetch_company_data
from tools.news_tool import fetch_company_news
from schema.unified_schema import build_schema
import json


def main():

    ticker = input("Enter company ticker: ")
    exchange = input("Enter exchange (NSE/BSE): ")

    raw_data = fetch_company_data(ticker,exchange)

    if raw_data is None:
        print("Failed to fetch company data.")
        return


    company_name = raw_data["info"].get("longName")

    news_data = fetch_company_news(company_name)

    final_schema = build_schema(raw_data, news_data)

    final_schema["news_data"] = news_data

    print(json.dumps(final_schema, indent=4))


if __name__ == "__main__":
    main()