from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool, PDFSearchTool
from typing import List
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from signal_sync.tools.stock_tool import StockDataTool
from signal_sync.schemas.bgv_schemas import (
    BGVOutput,
    CompanyOverviewOutput,
    ManagementResearchOutput,
    FinancialIrregularitiesOutput,
    ScamDetectionOutput
)

# Output directory setup
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@CrewBase
class BGVCrew():
    """
    BGV (Background Verification) Crew for Retail Investment Advisor.
    
    This crew performs comprehensive background verification on companies including:
    - Company overview and profile analysis
    - Management team background research
    - Financial irregularities detection
    - Market manipulation/scam signal detection
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    
    # Initialize tools
    serper_tool = SerperDevTool()
    stock_tool = StockDataTool()
    
    def __init__(self, company_name: str = "", ticker: str = "", sector: str = "", 
                 annual_report_path: str = ""):
        """
        Initialize BGV Crew with company details.
        
        Args:
            company_name: Name of the company to verify
            ticker: Stock ticker symbol
            sector: Business sector
            annual_report_path: Path to the annual report PDF
        """
        self.company_name = company_name
        self.ticker = ticker
        self.sector = sector
        self.annual_report_path = annual_report_path
        self.output_path = os.path.join(OUTPUT_DIR, "bgv_output.json")
        
        # Initialize PDF tool if annual report is provided
        if annual_report_path and os.path.exists(annual_report_path):
            self.pdf_tool = PDFSearchTool(pdf=annual_report_path)
        else:
            self.pdf_tool = None

    @agent
    def company_overview_agent(self) -> Agent:
        """Agent responsible for generating company overview."""
        return Agent(
            config=self.agents_config['company_overview_agent'],
            tools=[self.serper_tool],
            verbose=True
        )

    @agent
    def management_research_agent(self) -> Agent:
        """Agent responsible for researching management team backgrounds."""
        return Agent(
            config=self.agents_config['management_research_agent'],
            tools=[self.serper_tool],
            verbose=True
        )

    @agent
    def financial_irregularities_agent(self) -> Agent:
        """Agent responsible for detecting financial irregularities."""
        tools = [self.serper_tool]
        if self.pdf_tool:
            tools.append(self.pdf_tool)
        return Agent(
            config=self.agents_config['financial_irregularities_agent'],
            tools=tools,
            verbose=True
        )

    @agent
    def scam_detection_agent(self) -> Agent:
        """Agent responsible for detecting scam and manipulation signals."""
        return Agent(
            config=self.agents_config['scam_detection_agent'],
            tools=[self.stock_tool, self.serper_tool],
            verbose=True
        )

    @agent
    def bgv_report_compiler(self) -> Agent:
        """Agent responsible for compiling the final BGV report."""
        return Agent(
            config=self.agents_config['bgv_report_compiler'],
            verbose=True
        )

    @task
    def company_overview_task(self) -> Task:
        """Task for generating company overview."""
        return Task(
            config=self.tasks_config['company_overview_task'],
            output_json=CompanyOverviewOutput,
        )

    @task
    def management_research_task(self) -> Task:
        """Task for researching management team."""
        return Task(
            config=self.tasks_config['management_research_task'],
            output_json=ManagementResearchOutput,
        )

    @task
    def financial_irregularities_task(self) -> Task:
        """Task for detecting financial irregularities."""
        return Task(
            config=self.tasks_config['financial_irregularities_task'],
            output_json=FinancialIrregularitiesOutput,
        )

    @task
    def scam_detection_task(self) -> Task:
        """Task for detecting scam signals."""
        return Task(
            config=self.tasks_config['scam_detection_task'],
            output_json=ScamDetectionOutput,
        )

    @task
    def compile_bgv_report_task(self) -> Task:
        """Task for compiling the final BGV report."""
        return Task(
            config=self.tasks_config['compile_bgv_report_task'],
            output_json=BGVOutput,
            context=[
                self.company_overview_task(),
                self.management_research_task(),
                self.financial_irregularities_task(),
                self.scam_detection_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the BGV Crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
    
    def run(self) -> str:
        """
        Execute the BGV verification pipeline.
        
        Returns:
            Path to the output JSON file
        """
        inputs = {
            'company_name': self.company_name,
            'ticker': self.ticker,
            'sector': self.sector,
            'annual_report_path': self.annual_report_path,
            'output_path': self.output_path
        }
        
        result = self.crew().kickoff(inputs=inputs)
        
        # Validate and save structured output
        self._save_structured_output(result)
        
        return self.output_path
    
    def _save_structured_output(self, crew_result) -> None:
        """
        Process and validate the crew result, saving structured JSON output.
        """
        try:
            # Try to get the result data
            if hasattr(crew_result, 'json_dict') and crew_result.json_dict:
                # CrewAI structured output - already a dict
                output_data = crew_result.json_dict
            elif hasattr(crew_result, 'pydantic') and crew_result.pydantic:
                # Pydantic model output
                output_data = crew_result.pydantic.model_dump()
            elif hasattr(crew_result, 'raw'):
                raw_output = crew_result.raw
                output_data = self._extract_json_from_text(raw_output)
            else:
                raw_output = str(crew_result)
                output_data = self._extract_json_from_text(raw_output)
            
            # If we still don't have valid data, use fallback
            if not output_data or not isinstance(output_data, dict):
                output_data = self._create_fallback_output(str(crew_result))
            
            # Validate against schema and fill missing fields
            try:
                validated_output = BGVOutput(**output_data)
                final_output = validated_output.model_dump()
            except Exception as validation_error:
                print(f"Validation warning: {validation_error}")
                # Try to salvage what we can from the output
                final_output = self._merge_with_defaults(output_data)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # Save to file
            with open(self.output_path, 'w') as f:
                json.dump(final_output, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Warning: Could not save structured output: {e}")
            # Save raw result as fallback
            with open(self.output_path, 'w') as f:
                fallback = self._create_fallback_output(str(crew_result))
                json.dump(fallback, f, indent=2, default=str)
    
    def _extract_json_from_text(self, text: str) -> dict:
        """
        Extract JSON from text that may contain markdown code blocks or other formatting.
        """
        if not text:
            return {}
        
        # Try direct JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
            r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
            r'\{[\s\S]*\}',                   # Raw JSON object
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    # Clean up the match
                    cleaned = match.strip()
                    if cleaned.startswith('{'):
                        return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue
        
        return {}
    
    def _merge_with_defaults(self, partial_data: dict) -> dict:
        """
        Merge partial data with default structure to ensure completeness.
        """
        default = self._create_fallback_output("")
        
        # Deep merge
        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                elif value is not None and value != [] and value != "":
                    result[key] = value
            return result
        
        merged = deep_merge(default, partial_data)
        
        # Recalculate scores if we have the component scores
        merged = self._calculate_scores(merged)
        
        # Remove raw_analysis if it's empty
        if "raw_analysis" in merged and not merged["raw_analysis"]:
            del merged["raw_analysis"]
        
        return merged
    
    def _calculate_scores(self, data: dict) -> dict:
        """
        Calculate aggregate scores based on findings and evidence.
        
        Scoring Rubrics:
        - trustworthiness_score: Based on company profile completeness and positive findings
        - financial_integrity_score: Based on absence of financial irregularities
        - management_risk_score: Based on red flags found in management research
        - market_manipulation_risk_score: Based on scam signals detected
        """
        scores = data.get("scores", {})
        findings = data.get("findings", {})
        evidence = data.get("evidence", {})
        
        # Calculate financial_integrity_score (higher = better)
        # Start at 85, subtract 10 for each irregularity found
        fin_irregularities = findings.get("financial_irregularities", [])
        fin_score = max(20, 85 - (len(fin_irregularities) * 10))
        if scores.get("financial_integrity_score", 50) == 50:
            scores["financial_integrity_score"] = fin_score
        
        # Calculate management_risk_score (higher = more risky)
        # Start at 20, add 15 for each red flag
        mgmt_findings = findings.get("management_findings", [])
        people_profiles = evidence.get("people_profiles", [])
        total_red_flags = sum(len(p.get("red_flags", [])) for p in people_profiles)
        mgmt_risk = min(90, 20 + (len(mgmt_findings) * 10) + (total_red_flags * 15))
        if scores.get("management_risk_score", 50) == 50:
            scores["management_risk_score"] = mgmt_risk
        
        # Calculate market_manipulation_risk_score (higher = more risky)
        # Start at 15, add 20 for each scam signal
        scam_signals = findings.get("scam_signals", [])
        market_risk = min(95, 15 + (len(scam_signals) * 20))
        if scores.get("market_manipulation_risk_score", 50) == 50:
            scores["market_manipulation_risk_score"] = market_risk
        
        # Calculate trustworthiness_score (composite score)
        # Formula: (financial_integrity + (100 - management_risk) + (100 - market_manipulation_risk)) / 3
        fin_integrity = scores.get("financial_integrity_score", 50)
        mgmt_risk_score = scores.get("management_risk_score", 50)
        market_risk_score = scores.get("market_manipulation_risk_score", 50)
        
        trust_score = (fin_integrity + (100 - mgmt_risk_score) + (100 - market_risk_score)) / 3
        if scores.get("trustworthiness_score", 50) == 50:
            scores["trustworthiness_score"] = round(trust_score, 1)
        
        data["scores"] = scores
        
        # Update final verdict based on scores
        if data.get("final_verdict", "").startswith("Analysis completed"):
            data["final_verdict"] = self._generate_verdict(scores, findings)
        
        return data
    
    def _generate_verdict(self, scores: dict, findings: dict) -> str:
        """
        Generate a final verdict based on scores and findings.
        """
        trust = scores.get("trustworthiness_score", 50)
        fin = scores.get("financial_integrity_score", 50)
        mgmt_risk = scores.get("management_risk_score", 50)
        market_risk = scores.get("market_manipulation_risk_score", 50)
        
        # Count total issues
        total_issues = (
            len(findings.get("financial_irregularities", [])) +
            len(findings.get("management_findings", [])) +
            len(findings.get("scam_signals", []))
        )
        
        # Determine risk level
        if trust >= 75 and mgmt_risk <= 30 and market_risk <= 25:
            verdict = "LOW RISK: Company appears trustworthy with strong financial integrity and clean management track record. Safe for investment consideration."
        elif trust >= 60 and mgmt_risk <= 50 and market_risk <= 40:
            verdict = f"MODERATE RISK: Company shows acceptable trustworthiness but {total_issues} concern(s) identified. Proceed with caution and additional due diligence recommended."
        elif trust >= 40 or (mgmt_risk <= 70 and market_risk <= 60):
            verdict = f"HIGH RISK: Significant concerns identified ({total_issues} issues found). Detailed review required before any investment decision."
        else:
            verdict = f"CRITICAL RISK: Major red flags detected with {total_issues} serious concerns. Not recommended for investment without thorough investigation."
        
        return verdict
    
    def _create_fallback_output(self, raw_output: str) -> dict:
        """Create a fallback structured output when parsing fails."""
        # Try to extract any useful information from the raw output
        extracted_findings = self._extract_findings_from_text(raw_output)
        
        return {
            "meta": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "pipeline_version": "bgv_v1.0",
                "sources": [{"name": "SerperDev", "type": "web_search"}, {"name": "yfinance", "type": "time_series"}]
            },
            "company": {
                "name": self.company_name,
                "ticker": self.ticker,
                "sector": self.sector,
                "profile_summary": extracted_findings.get("profile_summary", "Analysis completed - see raw output for details")
            },
            "scores": {
                "trustworthiness_score": 50.0,
                "financial_integrity_score": 50.0,
                "management_risk_score": 50.0,
                "market_manipulation_risk_score": 50.0
            },
            "findings": {
                "overview_findings": extracted_findings.get("overview", []),
                "management_findings": extracted_findings.get("management", []),
                "financial_irregularities": extracted_findings.get("financial", []),
                "scam_signals": extracted_findings.get("scam", [])
            },
            "evidence": {
                "documents": [],
                "time_series": [],
                "people_profiles": []
            },
            "final_verdict": "Analysis completed. Please review raw output for detailed findings.",
            "raw_analysis": raw_output[:5000] if raw_output else ""  # Truncate to avoid huge files
        }
    
    def _extract_findings_from_text(self, text: str) -> dict:
        """
        Try to extract findings from unstructured text output.
        """
        findings = {
            "overview": [],
            "management": [],
            "financial": [],
            "scam": [],
            "profile_summary": ""
        }
        
        if not text:
            return findings
        
        # Look for bullet points or numbered items
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            lower_line = line.lower()
            if 'overview' in lower_line or 'company' in lower_line or 'profile' in lower_line:
                current_section = 'overview'
            elif 'management' in lower_line or 'executive' in lower_line or 'founder' in lower_line:
                current_section = 'management'
            elif 'financial' in lower_line or 'irregularit' in lower_line or 'accounting' in lower_line:
                current_section = 'financial'
            elif 'scam' in lower_line or 'manipulation' in lower_line or 'fraud' in lower_line:
                current_section = 'scam'
            
            # Extract bullet points
            if line.startswith(('-', '*', '•')) or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
                clean_line = line.lstrip('-*•0123456789.) ').strip()
                if clean_line and current_section and len(clean_line) > 10:
                    findings[current_section].append(clean_line)
        
        return findings


# Keep legacy class for backward compatibility
@CrewBase
class SignalSync():
    """SignalSync crew - Legacy class for backward compatibility"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['company_overview_agent'],
            verbose=True
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['bgv_report_compiler'],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['company_overview_task'],
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['compile_bgv_report_task'],
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SignalSync crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
