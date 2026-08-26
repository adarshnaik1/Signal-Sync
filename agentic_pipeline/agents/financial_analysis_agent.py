from crewai import Agent, Task, Crew, LLM
from crewai.project import CrewBase, agent, task, crew

from dotenv import load_dotenv

import os
import json

from tools.financial_analysis_tool import (
    analyze_financials
)

load_dotenv()


@CrewBase
class FinancialAnalysisCrew:

    agents_config = "config/financial_agents.yaml"
    tasks_config = "config/financial_tasks.yaml"

    llm = LLM(

        model="gemini/gemini-3.5-flash",

        api_key=os.getenv("GEMINI_API_KEY")
    )

    @agent
    def financial_analysis_agent(self) -> Agent:

        return Agent(

            config=self.agents_config["financial_analysis_agent"],
            llm=self.llm
        )

    @task
    def financial_analysis_task(self) -> Task:

        return Task(

            config=self.tasks_config["financial_analysis_task"],
            agent=self.financial_analysis_agent(),
        )

    @crew
    def crew(self) -> Crew:

        return Crew(agents=[self.financial_analysis_agent()], tasks=[self.financial_analysis_task()], verbose=True)

    def run_financial_analysis(self, unified_schema):

        computed_metrics = analyze_financials(
            unified_schema
        )

        combined_context = {

            "company_data":
                unified_schema,

            "computed_financial_metrics":
                computed_metrics
        }

        expected_schema = {

            "revenue_growth": {

                "status": "",

                "value_percent": 0,

                "summary": ""
            },

            "profitability": {

                "status": "",

                "summary": ""
            },

            "debt_health": {

                "status": "",

                "summary": ""
            },

            "cash_flow_strength": {

                "status": "",

                "summary": ""
            },

            "operational_efficiency": {

                "status": "",

                "summary": ""
            },

            "financial_stability": {

                "status": "",

                "summary": ""
            },

            "key_financial_risks": [],

            "financial_outlook": "",

            "financial_summary": ""
        }

        prompt = f"""

        Analyze the following company financial data:

        {json.dumps(combined_context, indent=2, default=str)}

        Return ONLY valid JSON.

        Use this exact structure:

        {json.dumps(expected_schema, indent=2)}

        Rules:

        - Keep responses concise.
        - No markdown.
        - No paragraphs.
        - No explanations outside JSON.
        - Keep summaries under 30 words.
        - status fields should be one of:
          Positive, Neutral, Negative.
        """

        result = self.financial_analysis_agent().llm.call(
            prompt
        )

        parsed_result = json.loads(
            result
        )

        return {

            "financial_analysis":
                parsed_result
        }

    def run(self, unified_schema):

        return self.run_financial_analysis(
            unified_schema
        )