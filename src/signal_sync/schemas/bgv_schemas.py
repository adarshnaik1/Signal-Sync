# src/signal_sync/schemas/bgv_schemas.py
"""
Pydantic models for structured outputs in BGV verification.
These schemas are compatible with OpenAI's structured output capability.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SourceInfo(BaseModel):
    """Information about data sources used in the analysis."""
    name: str = Field(..., description="Name of the data source")
    type: str = Field(..., description="Type of source (web_search, time_series, document, etc.)")
    url: Optional[str] = Field(None, description="URL of the source if applicable")


class CompanyProfile(BaseModel):
    """Company profile information."""
    name: str = Field(..., description="Company name")
    ticker: str = Field(..., description="Stock ticker symbol")
    sector: str = Field(..., description="Business sector")
    profile_summary: Optional[str] = Field(None, description="Brief summary of the company")
    headquarters: Optional[str] = Field(None, description="Company headquarters location")
    founded_year: Optional[int] = Field(None, description="Year the company was founded")
    employees: Optional[int] = Field(None, description="Number of employees")
    products_services: Optional[List[str]] = Field(default_factory=list, description="Main products or services")
    subsidiaries: Optional[List[str]] = Field(default_factory=list, description="List of subsidiaries")
    market_presence: Optional[str] = Field(None, description="Geographic market presence")


class BGVScores(BaseModel):
    """Risk and trustworthiness scores."""
    trustworthiness_score: float = Field(..., ge=0, le=100, description="Overall trustworthiness score (0-100)")
    financial_integrity_score: float = Field(..., ge=0, le=100, description="Financial health and integrity score (0-100)")
    management_risk_score: float = Field(..., ge=0, le=100, description="Management risk level score (0-100, higher = more risky)")
    market_manipulation_risk_score: float = Field(..., ge=0, le=100, description="Market manipulation risk score (0-100)")


class BGVFindings(BaseModel):
    """Findings from all verification agents."""
    overview_findings: List[str] = Field(default_factory=list, description="Findings from company overview analysis")
    management_findings: List[str] = Field(default_factory=list, description="Findings from management research")
    financial_irregularities: List[str] = Field(default_factory=list, description="Detected financial irregularities")
    scam_signals: List[str] = Field(default_factory=list, description="Detected potential scam or manipulation signals")


class DocumentEvidence(BaseModel):
    """Evidence from analyzed documents."""
    type: str = Field(..., description="Type of document (annual_report, quarterly_filing, etc.)")
    location: str = Field(..., description="File path or URL of the document")
    summary: Optional[str] = Field(None, description="Summary of key findings from the document")


class TimeSeriesEvidence(BaseModel):
    """Evidence from time series analysis."""
    source: str = Field(..., description="Data source (e.g., yfinance)")
    from_date: str = Field(..., description="Start date of the time series")
    to_date: str = Field(..., description="End date of the time series")
    file: str = Field(..., description="Path to the cached data file")
    metrics: dict = Field(default_factory=dict, description="Key metrics extracted from analysis")


class PersonProfile(BaseModel):
    """Profile of a company executive or founder."""
    name: str = Field(..., description="Person's name")
    role: str = Field(..., description="Role in the company")
    red_flags: List[str] = Field(default_factory=list, description="Identified red flags or concerns")
    evidence_links: List[str] = Field(default_factory=list, description="Links to supporting evidence")


class BGVEvidence(BaseModel):
    """All evidence collected during verification."""
    documents: List[DocumentEvidence] = Field(default_factory=list, description="Document evidence")
    time_series: List[TimeSeriesEvidence] = Field(default_factory=list, description="Time series evidence")
    people_profiles: List[PersonProfile] = Field(default_factory=list, description="Executive/founder profiles")


class MetaInfo(BaseModel):
    """Metadata about the BGV report."""
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="Report generation timestamp")
    pipeline_version: str = Field(default="bgv_v1.0", description="Version of the BGV pipeline")
    sources: List[SourceInfo] = Field(default_factory=list, description="All data sources used")


class BGVOutput(BaseModel):
    """
    Complete BGV (Background Verification) output schema.
    This is the final structured output that will be saved to bgv_output.json.
    """
    meta: MetaInfo = Field(..., description="Report metadata")
    company: CompanyProfile = Field(..., description="Company profile information")
    scores: BGVScores = Field(..., description="Risk and trustworthiness scores")
    findings: BGVFindings = Field(..., description="All findings from verification")
    evidence: BGVEvidence = Field(..., description="Supporting evidence")
    final_verdict: str = Field(..., description="Final assessment and recommendation")


# Agent-specific output schemas for structured LLM outputs

class CompanyOverviewOutput(BaseModel):
    """Structured output for Company Overview Agent."""
    company: CompanyProfile = Field(..., description="Company profile information")
    findings: List[str] = Field(default_factory=list, description="Key findings about the company")
    trust_score: float = Field(default=70.0, ge=0, le=100, description="Initial trustworthiness assessment")
    sources: List[SourceInfo] = Field(default_factory=list, description="Sources used for research")


class ManagementResearchOutput(BaseModel):
    """Structured output for Management Research Agent."""
    people_profiles: List[PersonProfile] = Field(default_factory=list, description="Executive profiles with red flags")
    findings: List[str] = Field(default_factory=list, description="Key findings about management")
    management_risk_score: float = Field(default=30.0, ge=0, le=100, description="Management risk assessment (higher = more risky)")
    sources: List[SourceInfo] = Field(default_factory=list, description="Sources used for research")


class FinancialIrregularitiesOutput(BaseModel):
    """Structured output for Financial Irregularities Agent."""
    findings: List[str] = Field(default_factory=list, description="Detected financial irregularities")
    financial_integrity_score: float = Field(default=75.0, ge=0, le=100, description="Financial integrity assessment")
    report_summary: Optional[str] = Field(None, description="Summary of annual report analysis")
    anomalies_detected: List[dict] = Field(default_factory=list, description="Detailed anomaly records")


class ScamDetectionOutput(BaseModel):
    """Structured output for Scam Detection Agent."""
    findings: List[str] = Field(default_factory=list, description="Detected scam or manipulation signals")
    market_manipulation_risk_score: float = Field(default=20.0, ge=0, le=100, description="Market manipulation risk")
    metrics: dict = Field(default_factory=dict, description="Analysis metrics")
    volume_analysis: Optional[dict] = Field(None, description="Volume spike analysis results")
    price_analysis: Optional[dict] = Field(None, description="Price anomaly analysis results")
