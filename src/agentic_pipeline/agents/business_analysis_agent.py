from crewai import Agent, Task, Crew, LLM
from crewai.project import CrewBase, agent, task, crew

from dotenv import load_dotenv
import os
import json


load_dotenv()


@CrewBase
class BusinessAnalysisCrew:
    agents_config = "config/business_agents.yaml"
    tasks_config = "config/business_tasks.yaml"

    # Configure LLM
    llm = LLM(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    @agent
    def business_analysis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["business_analysis_agent"],
            llm=self.llm,
        )

    @task
    def business_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["business_analysis_task"],
            agent=self.business_analysis_agent(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(agents=[self.business_analysis_agent()], tasks=[self.business_analysis_task()], verbose=True)

    def run_business_analysis(self, unified_schema):
        company_context = json.dumps(unified_schema, indent=2, default=str)

        expected_schema = {
            "business_model": "",
            "core_revenue_drivers": [],
            "industry_position": "",
            "industry_outlook": {"status": "", "summary": ""},
            "industry_growth_potential": {"status": "", "summary": ""},
            "industry_risks": [],
            "competitive_advantages": [],
            "growth_opportunities": [],
            "business_risks": [],
            "recent_business_developments": [],
            "business_outlook": "",
            "business_summary": "",
        }

        prompt = f"""
        Analyze the following company data:

        {company_context}

        Pay special attention to:
        - Sector
        - Industry
        - Business summary
        - Recent company news
        - Competitive positioning
        - Growth opportunities

        Return ONLY valid JSON.

        Use this exact structure:

        {json.dumps(expected_schema, indent=2)}

        Rules:
        - industry_outlook.status must be one of: Positive, Neutral, Negative
        - industry_growth_potential.status must be one of: High, Moderate, Low
        - Keep responses concise.
        - No markdown.
        - No paragraphs.
        - No explanations outside JSON.
        - Keep summaries under 25 words.
        """

        result = self.business_analysis_agent().llm.call(prompt)
        parsed_result = json.loads(result)

        return {"business_analysis": parsed_result}
