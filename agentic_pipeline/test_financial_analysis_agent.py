import json

from agents.data_acquisition_agent import (
    DataAcquisitionCrew
)

from agents.financial_analysis_agent import (
    FinancialAnalysisCrew
)


# Step 1 → Take user input
ticker = input(
    "Enter company ticker: "
).strip()

exchange = input(
    "Enter exchange (NSE/BSE): "
).strip()


# Step 2 → Run Data Acquisition Agent
acquisition_crew = DataAcquisitionCrew()

unified_schema = acquisition_crew.run(
    ticker,
    exchange
)


# Step 3 → Run Financial Analysis Agent
financial_crew = FinancialAnalysisCrew()

result = financial_crew.run_financial_analysis(unified_schema)


# Step 4 → Print Result
print(

    json.dumps(

        result,

        indent=2,

        default=str
    )
)