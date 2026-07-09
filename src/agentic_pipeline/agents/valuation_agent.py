from crewai import Agent, Task, Crew, LLM
from crewai.project import CrewBase, agent, task, crew

from dotenv import load_dotenv

import os
import json


from agentic_pipeline.tools.valuation_tool import analyze_valuation


load_dotenv()


@CrewBase
class ValuationCrew:

    agents_config = "config/valuation_agents.yaml"
    tasks_config = "config/valuation_tasks.yaml"

    llm = LLM(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    @agent
    def valuation_agent(self) -> Agent:

        return Agent(

            config=self.agents_config["valuation_agent"],
            llm=self.llm
        )

    @task
    def valuation_task(self) -> Task:

        return Task(

            config=self.tasks_config["valuation_task"],

            agent=self.valuation_agent(),
        )

    @crew
    def crew(self) -> Crew:

        return Crew(agents=[self.valuation_agent()],tasks=[self.valuation_task()],verbose=True)

    def run_valuation(self, unified_schema):

        computed_valuation = analyze_valuation(
            unified_schema
        )

        combined_context = {

            "company_data":
                unified_schema,

            "computed_valuation_metrics":
                computed_valuation
        }

        prompt = f"""

        Analyze the following company valuation data:

        {json.dumps(combined_context, indent=2, default=str)}

        Return ONLY valid JSON.

        Use this exact structure:

        {{
            "valuation_status": "",
            "valuation_confidence": "",
            "pe_analysis": "",
            "growth_vs_valuation": "",
            "intrinsic_value_outlook": "",
            "valuation_summary": ""
        }}

        Rules:
        - Keep responses concise.
        - No markdown.
        - No paragraphs.
        - No explanations outside JSON.
        - Keep summaries under 30 words.
        """

        try:
            result = self.llm.call(
                prompt
            )

            parsed_result = json.loads(
                result
            )
        except Exception as e:
            # LLM unavailable or errored — return a safe fallback using computed metrics
            import logging

            logging.warning(f"LLM call failed, returning fallback valuation: {e}")

            parsed_result = {
                "valuation_status": "unknown",
                "valuation_confidence": "low",
                "pe_analysis": str(computed_valuation.get("pe", "")),
                "growth_vs_valuation": str(computed_valuation.get("revenue_growth", "")),
                "intrinsic_value_outlook": "unavailable",
                "valuation_summary": "LLM unavailable — returning computed metrics."
            }

        return {

            "valuation_analysis":
                parsed_result
        }

    