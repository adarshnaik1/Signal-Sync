from crewai import LLM

from dotenv import load_dotenv

import os
import json

load_dotenv()


class ExplanationGenerator:

    def __init__(self):

        self.llm = LLM(
            model="gemini/gemini-3.5-flash",
            api_key=os.getenv("GEMINI_API_KEY")
        )

    def generate(
        self,
        business_analysis,
        financial_analysis,
        risk_analysis,
        valuation_analysis,
        verdict
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

            "verdict":
                verdict
        }

        prompt = f"""
        Explain the following investment recommendation.

        {json.dumps(combined_context, indent=2, default=str)}

        Return ONLY valid JSON.

        Use this exact structure:

        {{
            "executive_summary": "",
            "why_buy_hold_sell": "",
            "key_strengths": [],
            "key_risks": [],
            "what_to_monitor": []
        }}

        Rules:
        - executive_summary <= 25 words.
        - investment_rationale <= 35 words.
        - Focus on explaining the verdict.
        - Do not repeat all metrics.
        - Mention only the most important supporting factors.
        """

        result = self.llm.call(prompt)

        parsed_result = json.loads(
            result
        )

        return parsed_result