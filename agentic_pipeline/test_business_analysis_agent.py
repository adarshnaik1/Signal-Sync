import json

from agents.data_acquisition_agent import DataAcquisitionCrew
from agents.business_analysis_agent import BusinessAnalysisCrew


ticker = input("Enter company ticker: ").strip()

exchange = input(
    "Enter exchange (NSE/BSE): "
).strip()


# Step 1 → Run Data Acquisition Agent
acquisition_crew = DataAcquisitionCrew()

unified_schema = acquisition_crew.run(
    ticker,
    exchange
)


# Step 2 → Run Business Analysis Agent
business_crew = BusinessAnalysisCrew()

result = business_crew.run_business_analysis(unified_schema)


# Step 3 → Print Result
print(json.dumps(result, indent=2, default=str))