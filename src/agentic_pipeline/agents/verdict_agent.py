from crewai import Agent, Task, Crew, LLM
from crewai.project import CrewBase, agent, task, crew

from dotenv import load_dotenv

import os
import json


load_dotenv()


@CrewBase
class VerdictCrew:

    agents_config = "config/verdict_agents.yaml"
    tasks_config = "config/verdict_tasks.yaml"

    def __init__(self):
        """Initialize LLM client, with a safe local fallback."""

        api_key = os.getenv("OPENAI_API_KEY")

        try:

            if api_key:

                self.llm = LLM(

                    model="gpt-4o-mini",

                    api_key=api_key
                )

            else:

                raise RuntimeError(
                    "No OPENAI_API_KEY; using fallback LLM"
                )

        except Exception:

            class _FallbackLLM:

                def call(self, prompt: str) -> str:

                    sample = {

                        "investment_verdict": "HOLD",

                        "verdict_score": 55,

                        "confidence_level": "Moderate",

                        "holding_period": "Medium-Term",

                        "key_drivers": [

                            "Stable profitability",

                            "Balanced risk profile",

                            "Fair valuation"
                        ],

                        "primary_reasons": [

                            "Stable revenue",

                            "Diversified operations"
                        ],

                        "major_concerns": [

                            "Elevated valuation",

                            "Macro uncertainty"
                        ],

                        "final_summary":
                            "Balanced outlook with moderate upside potential."
                    }

                    return json.dumps(sample)

            self.llm = _FallbackLLM()

    @agent
    def verdict_agent(self) -> Agent:

        return Agent(

            config=self.agents_config["verdict_agent"],

            llm=self.llm
        )

    @task
    def verdict_task(self) -> Task:

        return Task(

            config=self.tasks_config["verdict_task"],
            agent=self.verdict_agent(),
        )

    @crew
    def crew(self) -> Crew:

        return Crew(agents=[self.verdict_agent()],tasks=[self.verdict_task()],verbose=True)

    def run_verdict(
        self,
        business_analysis,
        financial_analysis,
        risk_analysis,
        valuation_analysis,
    ):

        combined_context = {

            "business_analysis":
                business_analysis,

            "financial_analysis":
                financial_analysis,

            "risk_analysis":
                risk_analysis,

            "valuation_analysis":
                valuation_analysis,
        }

        expected_schema = {

            "investment_verdict": "",

            "verdict_score": 0,

            "confidence_level": "",

            "holding_period": "",

            "key_drivers": [],

            "primary_reasons": [],

            "major_concerns": [],

            "final_summary": ""
        }

        prompt = f"""
        Analyze the following investment analyses:

        {json.dumps(combined_context, indent=2, default=str)}

        Return ONLY valid JSON.

        Use this exact structure:

        {json.dumps(expected_schema, indent=2)}

        Rules:

        - investment_verdict must be one of:
          BUY, HOLD, SELL

        - confidence_level must be one of:
          Low, Moderate, High

        - holding_period must be one of:
          Short-Term, Medium-Term, Long-Term

        - Consider:
          * business outlook
          * industry outlook
          * industry growth potential
          * financial outlook
          * risk outlook
          * valuation outlook

        - verdict_score must be between 0 and 100.

        - Score interpretation:
          0-39 -> SELL
          40-59 -> HOLD
          60-100 -> BUY

        - investment_verdict must be consistent with verdict_score.

        - key_drivers should contain the top 3 factors driving the verdict.

        - Keep responses concise.

        - No markdown.

        - No paragraphs.

        - No explanations outside JSON.

        - Keep final_summary under 25 words.
        """

        result = self.llm.call(
            prompt
        )

        parsed_result = json.loads(
            result
        )

        return parsed_result

    