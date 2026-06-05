from crewai import Agent, Task, Crew, LLM
from crewai.project import CrewBase, agent, task, crew

from dotenv import load_dotenv

import os
import json
import sys

# Ensure sibling packages like `tools` can be imported when running from
# the package root or this module directly.
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agentic_pipeline.tools.risk_analysis_tool import analyze_risk


load_dotenv()


@CrewBase
class RiskAnalysisCrew:

    agents_config = "config/risk_agents.yaml"
    tasks_config = "config/risk_tasks.yaml"

    llm = LLM(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    @agent
    def risk_analysis_agent(self) -> Agent:

        return Agent(

            config=self.agents_config["risk_analysis_agent"],

            llm=self.llm,
        )

    @task
    def risk_analysis_task(self) -> Task:

        return Task(

            config=self.tasks_config["risk_analysis_task"],

            agent=self.risk_analysis_agent(),
        )

    @crew
    def crew(self) -> Crew:

        return Crew(agents=[self.risk_analysis_agent()],tasks=[self.risk_analysis_task()],verbose=True)

    def run_risk_analysis(self, unified_schema):
        computed_risks = analyze_risk(
            unified_schema
        )

        combined_context = {

            "company_data":
                unified_schema,

            "computed_risk_metrics":
                computed_risks
        }

        prompt = f"""

        Analyze the following company risk data:

        {json.dumps(combined_context, indent=2, default=str)}

        Return ONLY valid JSON.

        Use this exact structure:

        {{
            "overall_risk_level": "",
            "market_risk": "",
            "industry_risks": [],
            "debt_risk": "",
            "liquidity_risk": "",
            "profitability_risk": "",
            "operational_risk": "",
            "financial_stability_risk": "",
            "key_warning_signals": [],
            "risk_summary": ""
        }}

        Rules:
        - Keep responses concise.
        - No paragraphs.
        - No markdown.
        - No explanations outside JSON.
        - Keep summaries under 30 words.
        """

        result = self.risk_analysis_agent().llm.call(
            prompt
        )

        parsed_result = json.loads(result)

        return {

            "risk_analysis": parsed_result
        }

    