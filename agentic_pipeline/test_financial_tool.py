#this file is only for purpose of testing financial_tool independently. It is not part of the main pipeline and can be ignored for the overall project structure.

from tools.financial_tool import fetch_company_data


data = fetch_company_data("INFY.NS")



print(data["info"].keys())

print(data["financials"])

print(data["balance_sheet"])

print(data["cashflow"])