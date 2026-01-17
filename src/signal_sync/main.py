#!/usr/bin/env python
"""
Signal Sync - BGV Verification Pipeline
Main entry point for running the BGV crew via CLI or programmatically.
"""
import sys
import warnings
import os
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from signal_sync.crew import BGVCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Output directory setup
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_bgv(
    company_name: str,
    ticker: str,
    sector: str,
    annual_report_path: Optional[str] = None
) -> str:
    """
    Run the BGV verification pipeline.
    
    Args:
        company_name: Name of the company to verify
        ticker: Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS')
        sector: Business sector (e.g., 'Technology', 'Finance')
        annual_report_path: Optional path to the annual report PDF
    
    Returns:
        Path to the generated bgv_output.json file
    """
    print(f"\n{'='*60}")
    print(f"Starting BGV Verification for {company_name} ({ticker})")
    print(f"Sector: {sector}")
    print(f"{'='*60}\n")
    
    # Validate annual report path
    if annual_report_path and not os.path.exists(annual_report_path):
        print(f"Warning: Annual report not found at {annual_report_path}")
        annual_report_path = None
    
    try:
        # Initialize and run the BGV crew
        bgv_crew = BGVCrew(
            company_name=company_name,
            ticker=ticker,
            sector=sector,
            annual_report_path=annual_report_path or ""
        )
        
        output_path = bgv_crew.run()
        
        print(f"\n{'='*60}")
        print(f"BGV Verification Complete!")
        print(f"Output saved to: {output_path}")
        print(f"{'='*60}\n")
        
        return output_path
        
    except Exception as e:
        raise Exception(f"An error occurred while running the BGV crew: {e}")


def generate_dummy_output(company_name: str, ticker: str, sector: str) -> str:
    """
    Generate dummy/mock BGV output for testing without calling AI agents.
    """
    dummy_output = {
        "meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "pipeline_version": "bgv_v1.0_dummy",
            "sources": [
                {"name": "Yahoo Finance", "type": "time_series", "url": f"https://finance.yahoo.com/quote/{ticker}"},
                {"name": "Web Search", "type": "web_search", "url": None}
            ]
        },
        "company": {
            "name": company_name,
            "ticker": ticker,
            "sector": sector,
            "profile_summary": f"{company_name} is a leading company in the {sector} sector, known for innovation and market leadership.",
            "headquarters": "United States",
            "founded_year": 2003,
            "employees": 100000,
            "products_services": ["Electric Vehicles", "Energy Storage", "Solar Panels", "Autopilot Software"],
            "subsidiaries": ["Tesla Energy", "Tesla Insurance"],
            "market_presence": "Global - North America, Europe, Asia Pacific"
        },
        "scores": {
            "trustworthiness_score": 72.5,
            "financial_integrity_score": 68.0,
            "management_risk_score": 45.0,
            "market_manipulation_risk_score": 35.0
        },
        "findings": {
            "overview_findings": [
                f"{company_name} has shown consistent growth in the {sector} sector",
                "Strong brand recognition and market positioning",
                "Diversified product portfolio reducing risk"
            ],
            "management_findings": [
                "CEO has a strong track record but occasional controversial statements",
                "Management team has relevant industry experience",
                "No major fraud allegations found"
            ],
            "financial_irregularities": [
                "Revenue recognition practices appear standard",
                "Debt levels are manageable but increasing",
                "No major audit concerns identified"
            ],
            "scam_signals": [
                "Some volume spikes detected around earnings announcements (normal)",
                "No clear pump-and-dump patterns identified",
                "Social media activity correlates with legitimate news events"
            ]
        },
        "evidence": {
            "documents": [],
            "time_series": [
                {
                    "source": "yfinance",
                    "from_date": "2025-12-17",
                    "to_date": "2026-01-17",
                    "file": "DUMMY_cache.json",
                    "metrics": {
                        "avg_volume": 50000000,
                        "price_volatility": 3.2,
                        "volume_spike_ratio": 1.8
                    }
                }
            ],
            "people_profiles": [
                {
                    "name": "CEO",
                    "role": "Chief Executive Officer",
                    "red_flags": [],
                    "evidence_links": []
                }
            ]
        },
        "final_verdict": f"MODERATE RISK - {company_name} ({ticker}) appears to be a legitimate company with standard business practices. Some volatility and management-related concerns exist but no major red flags were identified. Suitable for investors with moderate risk tolerance."
    }
    
    output_path = os.path.join(OUTPUT_DIR, "bgv_output.json")
    with open(output_path, "w") as f:
        json.dump(dummy_output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"[DUMMY MODE] Generated mock BGV output for {company_name} ({ticker})")
    print(f"Output saved to: {output_path}")
    print(f"{'='*60}\n")
    
    return output_path


def run():
    """
    Run the BGV crew with default/example inputs.
    This is the entry point for the CLI command.
    """
    # Check for --dummy flag
    dummy_mode = '--dummy' in sys.argv
    if dummy_mode:
        sys.argv.remove('--dummy')
    
    # Default example inputs for testing
    inputs = {
        'company_name': 'Example Corp',
        'ticker': 'EXMPL',
        'sector': 'Technology',
        'annual_report_path': ''
    }
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        inputs['company_name'] = sys.argv[1]
    if len(sys.argv) > 2:
        inputs['ticker'] = sys.argv[2]
    if len(sys.argv) > 3:
        inputs['sector'] = sys.argv[3]
    if len(sys.argv) > 4:
        inputs['annual_report_path'] = sys.argv[4]
    
    try:
        if dummy_mode:
            # Generate dummy output without calling AI agents
            output_path = generate_dummy_output(
                inputs['company_name'],
                inputs.get('ticker', inputs['company_name'].upper()[:4]),
                inputs.get('sector', 'Technology')
            )
        else:
            output_path = run_bgv(**inputs)
        
        # Display summary
        if os.path.exists(output_path):
            with open(output_path) as f:
                result = json.load(f)
                print("\n--- BGV Summary ---")
                if 'final_verdict' in result:
                    print(f"Final Verdict: {result['final_verdict']}")
                if 'scores' in result:
                    print(f"Scores: {json.dumps(result['scores'], indent=2)}")
                    
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'company_name': 'Training Corp',
        'ticker': 'TRAIN',
        'sector': 'Technology',
        'annual_report_path': '',
        'output_path': os.path.join(OUTPUT_DIR, "bgv_output.json")
    }
    
    try:
        BGVCrew(
            company_name=inputs['company_name'],
            ticker=inputs['ticker'],
            sector=inputs['sector']
        ).crew().train(
            n_iterations=int(sys.argv[1]), 
            filename=sys.argv[2], 
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        BGVCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'company_name': 'Test Corp',
        'ticker': 'TEST',
        'sector': 'Technology',
        'annual_report_path': '',
        'output_path': os.path.join(OUTPUT_DIR, "bgv_output.json")
    }
    
    try:
        BGVCrew(
            company_name=inputs['company_name'],
            ticker=inputs['ticker'],
            sector=inputs['sector']
        ).crew().test(
            n_iterations=int(sys.argv[1]), 
            eval_llm=sys.argv[2], 
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    run()
