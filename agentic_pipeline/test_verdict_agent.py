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


if __name__ == "__main__":

    ticker = input(
        "Enter company ticker: "
    ).strip()

    exchange = input(
        "Enter exchange (NSE/BSE): "
    ).strip() or "NSE"

    # Step 1: Data Acquisition
    data_crew = DataAcquisitionCrew()

    unified_schema = data_crew.run(
        ticker,
        exchange
    )

    # Step 2: Business Analysis
    business_crew = BusinessAnalysisCrew()

    business_result = business_crew.run_business_analysis(
        unified_schema
    )

    # Step 3: Financial Analysis
    financial_crew = FinancialAnalysisCrew()

    financial_result = financial_crew.run_financial_analysis(
        unified_schema
    )

    # Step 4: Risk Analysis
    risk_crew = RiskAnalysisCrew()

    risk_result = risk_crew.run_risk_analysis(
        unified_schema
    )

    # Step 5: Valuation Analysis
    valuation_crew = ValuationCrew()

    valuation_result = valuation_crew.run_valuation(
        unified_schema
    )

    # Step 6: Verdict
    verdict_crew = VerdictCrew()

    verdict_result = verdict_crew.run_verdict(

        business_result,

        financial_result,

        risk_result,

        valuation_result
    )

    print(
        json.dumps(
            verdict_result,
            indent=2
        )
    )