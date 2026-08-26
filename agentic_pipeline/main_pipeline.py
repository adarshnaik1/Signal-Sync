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


class SignalSyncPipeline:

    def __init__(self):

        self.data_agent = DataAcquisitionCrew()

        self.business_agent = BusinessAnalysisCrew()

        self.financial_agent = FinancialAnalysisCrew()

        self.risk_agent = RiskAnalysisCrew()

        self.valuation_agent = ValuationCrew()

        self.verdict_agent = VerdictCrew()

    def run(self, ticker, exchange="NSE"):

        # Step 1
        unified_schema = self.data_agent.run(
            ticker,
            exchange
        )

        # Step 2
        business_analysis = self.business_agent.run_business_analysis(
            unified_schema
        )

        # Step 3
        financial_analysis = self.financial_agent.run_financial_analysis(
            unified_schema
        )

        # Step 4
        risk_analysis = self.risk_agent.run_risk_analysis(
            unified_schema
        )

        # Step 5
        valuation_analysis = self.valuation_agent.run_valuation(
            unified_schema
        )

        # Step 6
        verdict = self.verdict_agent.run_verdict(

            business_analysis,

            financial_analysis,

            risk_analysis,

            valuation_analysis
        )

        return {

            "company_identification":
                unified_schema.get(
                    "company_identification",
                    {}
                ),

            "business_analysis":
                business_analysis.get(
                    "business_analysis",
                    {}
                ),

            "financial_analysis":
                financial_analysis.get(
                    "financial_analysis",
                    {}
                ),

            "risk_analysis":
                risk_analysis.get(
                    "risk_analysis",
                    {}
                ),

            "valuation_analysis":
                valuation_analysis.get(
                    "valuation_analysis",
                    {}
                ),

            "investment_verdict":
                verdict.get(
                    "investment_verdict",
                    {}
                )
        }


if __name__ == "__main__":

    ticker = input(
        "Enter company ticker: "
    ).strip()

    exchange = input(
        "Enter exchange (NSE/BSE): "
    ).strip() or "NSE"

    pipeline = SignalSyncPipeline()

    result = pipeline.run(
        ticker,
        exchange
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )