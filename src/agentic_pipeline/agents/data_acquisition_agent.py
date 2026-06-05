from crewai import Agent, Task, Crew
from crewai.project import CrewBase, agent, task, crew

# When running this module directly (python data_acquisition_agent.py)
# ensure the package root (agentic_pipeline) is on sys.path so
# sibling packages like `tools` and `schema` can be imported.
import os
import sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.financial_tool import fetch_company_data
from tools.news_tool import fetch_company_news
from ..schema.unified_schema import build_schema


@CrewBase
class DataAcquisitionCrew:
    """CrewAI-style wrapper for the data acquisition step.

    Provides an `agent` and a `task` and a simple `run` helper
    to execute the pipeline programmatically.
    """

    @agent
    def data_acquisition_agent(self) -> Agent:
        return Agent(
            role="Data Acquisition Specialist",
            goal=(
                "Fetch accurate company financial data, market data, "
                "and company-specific news for downstream analyses."
            ),
            backstory=(
                "Expert data engineer specialized in financial data "
                "pipelines, market intelligence, and structured data normalization."
            ),
            verbose=True,
            allow_delegation=False,
        )

    @task
    def data_acquisition_task(self) -> Task:
        return Task(
            description=(
                "Fetch company financials, market history, balance sheet, "
                "cashflow and recent news; normalize to unified schema."
            ),
            expected_output=(
                "A structured JSON schema with company metadata, financials, "
                "market data and news."
            ),
            agent=self.data_acquisition_agent(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(agents=[self.data_acquisition_agent()], tasks=[self.data_acquisition_task()], verbose=True)

    def run_data_acquisition(self, ticker: str, exchange: str):
        # Step 1 → Fetch financial/company data
        raw_data = fetch_company_data(ticker, exchange)

        if raw_data is None:
            return {"error": "Failed to fetch company financial data."}

        # Step 2 → Extract company name
        company_name = raw_data.get("info", {}).get("longName") or ticker

        # Step 3 → Fetch news
        news_data = fetch_company_news(company_name)

        # Step 4 → Build unified schema with both raw_data and news_data
        final_schema = build_schema(raw_data, news_data)

        return final_schema

    def run(self, ticker: str, exchange: str):
        """Convenience runner that executes the task and returns schema."""
        return self.run_data_acquisition(ticker, exchange)


if __name__ == "__main__":
    import json

    # Prompt for input interactively (like main.py)
    ticker = input("Enter company ticker: ").strip()
    exchange = input("Enter exchange (NSE/BSE): ").strip() or "NSE"

    if not ticker:
        print("Error: ticker cannot be empty.")
        raise SystemExit(1)

    try:
        crew = DataAcquisitionCrew()
        result = crew.run(ticker, exchange)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"Error running data acquisition: {e}")