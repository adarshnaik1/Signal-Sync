import json

from agents.data_acquisition_agent import (
    DataAcquisitionCrew
)

from agents.business_analysis_agent import (
    BusinessAnalysisCrew
)

from agents.financial_analysis_agent import (
    FinancialAnalysisCrew
)

from agents.risk_analysis_agent import (
    RiskAnalysisCrew
)

from agents.valuation_agent import (
    ValuationCrew
)

from agents.verdict_agent import (
    VerdictCrew
)

from explainers.explanation_generator import (
    ExplanationGenerator
)


ticker = input(
    "Enter company ticker: "
).strip()

exchange = input(
    "Enter exchange (NSE/BSE): "
).strip()


# Step 1 → Data Acquisition

data_crew = DataAcquisitionCrew()

unified_schema = data_crew.run(
    ticker,
    exchange
)


# Step 2 → Business Analysis

business_analysis = (
    BusinessAnalysisCrew()
    .run_business_analysis(unified_schema)
)


# Step 3 → Financial Analysis

financial_analysis = (
    FinancialAnalysisCrew()
    .run_financial_analysis(unified_schema)
)


# Step 4 → Risk Analysis

risk_analysis = (
    RiskAnalysisCrew()
    .run_risk_analysis(unified_schema)
)


# Step 5 → Valuation Analysis

valuation_analysis = (
    ValuationCrew()
    .run_valuation(unified_schema)
)


# Step 6 → Verdict

verdict = VerdictCrew().run_verdict(
    business_analysis,
    financial_analysis,
    risk_analysis,
    valuation_analysis
)


# Step 7 → Explanation

explanation = ExplanationGenerator().generate(
    business_analysis,
    financial_analysis,
    risk_analysis,
    valuation_analysis,
    verdict
)


print(
    json.dumps(
        explanation,
        indent=2
    )
)