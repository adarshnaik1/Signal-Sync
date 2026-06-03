import json

from agents.data_acquisition_agent import (
    DataAcquisitionCrew
)

from agents.valuation_agent import (
    ValuationCrew
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


# Step 3 → Run Valuation Agent
valuation_crew = ValuationCrew()

result = valuation_crew.run_valuation(unified_schema)


# Step 4 → Print Result
print(

    json.dumps(

        result,

        indent=2,

        default=str
    )
)