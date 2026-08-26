import json

from agents.data_acquisition_agent import (
    DataAcquisitionCrew
)

from agents.risk_analysis_agent import (
    RiskAnalysisCrew
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


# Step 3 → Run Risk Analysis Agent
risk_crew = RiskAnalysisCrew()

result = risk_crew.run_risk_analysis(unified_schema)


# Step 4 → Print Result
print(

    json.dumps(

        result,

        indent=2,

        default=str
    )
)