# streamlit_app/app.py
"""
BGV Verification Streamlit Frontend
Provides a user interface for triggering the BGV verification pipeline.
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add the src directory to the path for imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

# Load environment variables from .env file
load_dotenv(ROOT_DIR / ".env")

# Page configuration
st.set_page_config(
    page_title="BGV Verification - Signal Sync",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #60a5fa;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white !important;
        text-align: center;
        margin: 10px;
    }
    .score-card h1, .score-card h3, .score-card p {
        color: white !important;
    }
    .risk-high { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .risk-moderate { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .risk-low { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .finding-item {
        background-color: #1e293b;
        border-left: 4px solid #667eea;
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 0 5px 5px 0;
        color: #e2e8f0 !important;
    }
    .red-flag {
        border-left-color: #f5576c;
        background-color: #2d1f2f;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/search--v1.png", width=80)
    st.title("Signal Sync")
    st.markdown("### BGV Verification System")
    st.markdown("---")
    st.markdown("""
    **Background Verification Checks:**
    - 🏢 Company Overview
    - 👥 Management Research
    - 📊 Financial Irregularities
    - ⚠️ Scam Detection
    """)
    st.markdown("---")
    st.info("Ensure you have set your API keys in the environment variables.")

# Main content
st.markdown('<h1 class="main-header">🔍 BGV Verification Portal</h1>', unsafe_allow_html=True)

# Input form
st.markdown("### Enter Company Details")

col1, col2 = st.columns(2)

with col1:
    company_name = st.text_input(
        "Company Name *",
        placeholder="e.g., Infosys Limited",
        help="Enter the full legal name of the company"
    )
    
    sector = st.selectbox(
        "Sector *",
        options=[
            "Technology",
            "Finance & Banking",
            "Healthcare",
            "Consumer Goods",
            "Energy",
            "Manufacturing",
            "Real Estate",
            "Telecommunications",
            "Retail",
            "Other"
        ],
        help="Select the primary business sector"
    )

with col2:
    ticker = st.text_input(
        "Stock Ticker *",
        placeholder="e.g., INFY.NS, AAPL, RELIANCE.NS",
        help="Enter the stock ticker symbol (include exchange suffix if applicable)"
    )
    
    # Custom sector input if "Other" is selected
    if sector == "Other":
        sector = st.text_input(
            "Specify Sector",
            placeholder="Enter the sector"
        )

# File uploader for annual report
st.markdown("### Upload Annual Report")
annual_pdf = st.file_uploader(
    "Annual Report PDF (Optional but recommended)",
    type=["pdf"],
    help="Upload the company's annual report for financial analysis"
)

# Display uploaded file info
if annual_pdf:
    st.success(f"✅ Uploaded: {annual_pdf.name} ({annual_pdf.size / 1024:.1f} KB)")

st.markdown("---")

# Run BGV button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button(
        "🚀 Run BGV Verification",
        type="primary",
        use_container_width=True
    )

# Handle form submission
if run_button:
    # Validation
    if not company_name:
        st.error("⚠️ Please enter the company name.")
    elif not ticker:
        st.error("⚠️ Please enter the stock ticker.")
    elif not sector:
        st.error("⚠️ Please select or enter the sector.")
    else:
        # Create uploads directory
        uploads_dir = ROOT_DIR / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded PDF if provided
        pdf_path = ""
        if annual_pdf:
            pdf_path = str(uploads_dir / f"{ticker.replace('.', '_')}_annual_report.pdf")
            with open(pdf_path, "wb") as f:
                f.write(annual_pdf.read())
            st.info(f"📄 Annual report saved to: {pdf_path}")
        
        # Progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Initializing BGV verification pipeline...")
            progress_bar.progress(10)
            
            # Import and run the BGV pipeline
            from signal_sync.main import run_bgv
            
            status_text.text("🔍 Running company overview analysis...")
            progress_bar.progress(30)
            
            status_text.text("👥 Researching management team...")
            progress_bar.progress(50)
            
            status_text.text("📊 Analyzing financial data...")
            progress_bar.progress(70)
            
            status_text.text("⚠️ Running scam detection...")
            progress_bar.progress(85)
            
            # Run the actual pipeline
            output_path = run_bgv(
                company_name=company_name.strip(),
                ticker=ticker.strip().upper(),
                sector=sector.strip(),
                annual_report_path=pdf_path
            )
            
            progress_bar.progress(100)
            status_text.text("✅ BGV verification completed!")
            
            # Display results
            st.markdown("---")
            st.markdown("## 📋 BGV Verification Results")
            
            # Load and display results
            if os.path.exists(output_path):
                with open(output_path) as f:
                    result = json.load(f)
                
                # Display scores
                st.markdown("### Risk Scores")
                score_cols = st.columns(4)
                
                scores = result.get('scores', {})
                
                with score_cols[0]:
                    trust_score = scores.get('trustworthiness_score', 0)
                    score_class = 'risk-low' if trust_score >= 70 else ('risk-moderate' if trust_score >= 40 else 'risk-high')
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h3>Trustworthiness</h3>
                        <h1>{trust_score:.1f}</h1>
                        <p>/100</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with score_cols[1]:
                    fin_score = scores.get('financial_integrity_score', 0)
                    score_class = 'risk-low' if fin_score >= 70 else ('risk-moderate' if fin_score >= 40 else 'risk-high')
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h3>Financial Integrity</h3>
                        <h1>{fin_score:.1f}</h1>
                        <p>/100</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with score_cols[2]:
                    mgmt_risk = scores.get('management_risk_score', 0)
                    score_class = 'risk-low' if mgmt_risk <= 30 else ('risk-moderate' if mgmt_risk <= 60 else 'risk-high')
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h3>Management Risk</h3>
                        <h1>{mgmt_risk:.1f}</h1>
                        <p>/100</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with score_cols[3]:
                    market_risk = scores.get('market_manipulation_risk_score', 0)
                    score_class = 'risk-low' if market_risk <= 30 else ('risk-moderate' if market_risk <= 60 else 'risk-high')
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h3>Market Manipulation</h3>
                        <h1>{market_risk:.1f}</h1>
                        <p>/100</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Final Verdict
                st.markdown("### Final Verdict")
                verdict = result.get('final_verdict', 'No verdict available')
                if 'CRITICAL' in verdict.upper() or 'HIGH' in verdict.upper():
                    st.error(f"🚨 {verdict}")
                elif 'MODERATE' in verdict.upper():
                    st.warning(f"⚠️ {verdict}")
                else:
                    st.success(f"✅ {verdict}")
                
                # Findings tabs
                st.markdown("### Detailed Findings")
                findings_tabs = st.tabs([
                    "🏢 Company Overview",
                    "👥 Management",
                    "📊 Financial",
                    "⚠️ Scam Signals"
                ])
                
                findings = result.get('findings', {})
                
                with findings_tabs[0]:
                    overview_findings = findings.get('overview_findings', [])
                    if overview_findings:
                        for finding in overview_findings:
                            st.markdown(f'<div class="finding-item">{finding}</div>', unsafe_allow_html=True)
                    else:
                        st.info("No specific findings to report.")
                
                with findings_tabs[1]:
                    mgmt_findings = findings.get('management_findings', [])
                    if mgmt_findings:
                        for finding in mgmt_findings:
                            css_class = "finding-item red-flag" if any(kw in finding.lower() for kw in ['fraud', 'scandal', 'fine', 'violation']) else "finding-item"
                            st.markdown(f'<div class="{css_class}">{finding}</div>', unsafe_allow_html=True)
                    else:
                        st.info("No specific findings to report.")
                    
                    # People profiles
                    people = result.get('evidence', {}).get('people_profiles', [])
                    if people:
                        st.markdown("#### Executive Profiles")
                        for person in people:
                            with st.expander(f"👤 {person.get('name', 'Unknown')} - {person.get('role', 'Unknown')}"):
                                red_flags = person.get('red_flags', [])
                                if red_flags:
                                    st.markdown("**Red Flags:**")
                                    for flag in red_flags:
                                        st.markdown(f"- 🚩 {flag}")
                                else:
                                    st.success("No red flags identified.")
                
                with findings_tabs[2]:
                    fin_findings = findings.get('financial_irregularities', [])
                    if fin_findings:
                        for finding in fin_findings:
                            css_class = "finding-item red-flag" if any(kw in finding.lower() for kw in ['spike', 'anomaly', 'irregularity', 'concern']) else "finding-item"
                            st.markdown(f'<div class="{css_class}">{finding}</div>', unsafe_allow_html=True)
                    else:
                        st.success("No financial irregularities detected.")
                
                with findings_tabs[3]:
                    scam_findings = findings.get('scam_signals', [])
                    if scam_findings:
                        for finding in scam_findings:
                            st.markdown(f'<div class="finding-item red-flag">{finding}</div>', unsafe_allow_html=True)
                    else:
                        st.success("No scam signals detected.")
                
                # Company Profile
                st.markdown("### Company Profile")
                company = result.get('company', {})
                profile_cols = st.columns(2)
                
                with profile_cols[0]:
                    st.markdown(f"**Name:** {company.get('name', 'N/A')}")
                    st.markdown(f"**Ticker:** {company.get('ticker', 'N/A')}")
                    st.markdown(f"**Sector:** {company.get('sector', 'N/A')}")
                    st.markdown(f"**Headquarters:** {company.get('headquarters', 'N/A')}")
                
                with profile_cols[1]:
                    st.markdown(f"**Founded:** {company.get('founded_year', 'N/A')}")
                    st.markdown(f"**Employees:** {company.get('employees', 'N/A')}")
                    if company.get('profile_summary'):
                        st.markdown(f"**Summary:** {company.get('profile_summary')}")
                
                # Download button
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="📥 Download Full BGV Report (JSON)",
                        data=json.dumps(result, indent=2),
                        file_name=f"bgv_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            else:
                st.error("❌ Output file not found. Please check the logs.")
                
        except ImportError as e:
            st.error(f"❌ Import error: {e}")
            st.info("Make sure all dependencies are installed. Run: `pip install -e .` in the project root.")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
            st.exception(e)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Signal Sync BGV Verification System | Built with CrewAI & Streamlit</p>
        <p>⚠️ This tool is for informational purposes only. Always conduct your own due diligence.</p>
    </div>
    """,
    unsafe_allow_html=True
)
