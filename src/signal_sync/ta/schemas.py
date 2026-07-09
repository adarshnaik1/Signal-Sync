from pydantic import BaseModel, Field
from typing import Optional, List, Dict

# 1. Market Data Schema
class ValidationResult(BaseModel):
    success: bool = Field(..., description="Whether validation succeeded.")
    rows: int = Field(..., description="Number of validated rows.")
    dropped_rows: int = Field(..., description="Number of rows dropped during validation.")

class MarketDataTaskOutput(BaseModel):
    success: bool = Field(..., description="Whether the market data step succeeded.")
    ticker: str = Field(..., description="Ticker symbol analyzed.")
    bundle_file: str = Field(..., description="Path to the market data bundle file.")
    daily_rows: int = Field(..., description="Number of rows in daily data.")
    weekly_rows: Optional[int] = Field(None, description="Number of rows in weekly data.")
    actions_count: int = Field(..., description="Number of corporate actions fetched.")
    validation: ValidationResult = Field(..., description="Validation summary details.")

# 2. Indicators Schema
class TrendIndicators(BaseModel):
    sma: Dict[str, Optional[float]] = Field(..., description="SMA indicator values, e.g. sma20, sma50, sma100, sma200.")
    ema: Dict[str, Optional[float]] = Field(..., description="EMA indicator values, e.g. ema20, ema50, ema100, ema200.")

class MomentumIndicators(BaseModel):
    rsi14: Optional[float] = Field(..., description="RSI (14) indicator value.")
    macd: Optional[float] = Field(..., description="MACD line value.")
    macd_signal: Optional[float] = Field(..., description="MACD signal line value.")
    macd_histogram: Optional[float] = Field(..., description="MACD histogram value.")

class VolatilityIndicators(BaseModel):
    atr14: Optional[float] = Field(..., description="ATR (14) indicator value.")
    bb_basis20: Optional[float] = Field(..., description="Bollinger Bands 20-period basis (middle line).")
    bb_upper20: Optional[float] = Field(..., description="Bollinger Bands 20-period upper band.")
    bb_lower20: Optional[float] = Field(..., description="Bollinger Bands 20-period lower band.")

class VolumeIndicators(BaseModel):
    obv: Optional[float] = Field(None, description="OBV (On-Balance Volume) value.")

class IndicatorTaskOutput(BaseModel):
    trend: TrendIndicators
    momentum: MomentumIndicators
    volatility: VolatilityIndicators
    volume: VolumeIndicators

# 3. Pattern Detection Schema
class VisualReview(BaseModel):
    success: bool = Field(..., description="Whether the visual review was successful.")
    visual_summary: str = Field(..., description="Advisory summary of the chart image. Must be concise (maximum 1-2 sentences) and grounded in visual evidence.")
    confidence: float = Field(0.0, description="Confidence score for the visual review (from 0.0 to 1.0).")
    image_analysis_status: str = Field("reported", description="Status of the image analysis (e.g. 'reported', 'unavailable', 'missing').")
    model: Optional[str] = Field(None, description="The vision model used.")
    image_size: Optional[str] = Field(None, description="Input image dimensions.")
    reviewed_image_size: Optional[str] = Field(None, description="Reviewed image dimensions.")
    error: Optional[str] = Field(None, description="Error message if visual review failed.")

class PatternDetectionTaskOutput(BaseModel):
    candlestick_patterns: List[str] = Field(default_factory=list, description="List of detected candlestick patterns (e.g., 'doji', 'hammer', 'bullish_engulfing', 'bearish_engulfing', 'shooting_star'). Must be a clean JSON list of strings.")
    chart_patterns: List[str] = Field(default_factory=list, description="List of detected chart patterns (e.g., 'double_top', 'double_bottom', 'channel'). Must be a clean JSON list of strings.")
    chart_path: str = Field(..., description="File path to the rendered chart image.")
    visual_review: VisualReview = Field(..., description="Vision review analysis of the rendered chart.")

# 4. Support and Resistance Schema
class SupportResistanceTaskOutput(BaseModel):
    support_zones: List[float] = Field(default_factory=list, description="List of support levels/zones identified (as numbers).")
    resistance_zones: List[float] = Field(default_factory=list, description="List of resistance levels/zones identified (as numbers).")
    evidence_by_layer: Dict[str, List[float]] = Field(default_factory=dict, description="Evidence supporting each level grouped by source layer (e.g. 'swings', 'volume_zones', 'ema_levels').")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores associated with the levels or layers.")

# 5. Strategy/Signal Schema
class StrategySignalTaskOutput(BaseModel):
    stance: str = Field(..., description="Overall stance: must be one of 'bullish', 'bearish', or 'neutral'.")
    confidence: str = Field(..., description="Confidence level: e.g., 'high', 'medium', or 'low'.")
    thesis: str = Field(..., description="Concise analysis thesis/rationale. Must be professional and strictly between 2 to 4 sentences.")
    key_supporting_evidence: List[str] = Field(default_factory=list, description="Key points of supporting evidence for the stance.")

# 6. Explanation Schema
class ExplanationSummary(BaseModel):
    stance: str = Field(..., description="Stance: 'bullish', 'bearish', or 'neutral'.")
    confidence: str = Field(..., description="Confidence level, e.g. 'high', 'medium', or 'low'.")
    thesis: str = Field(..., description="Concise explanation summary thesis. Maximum 2-4 sentences.")

class ExplanationTaskOutput(BaseModel):
    summary: ExplanationSummary = Field(..., description="Overall stance, confidence, and concise thesis summary.")
    indicator_explanation: str = Field(..., description="Concise explanation of the technical indicator readings. Maximum 3-4 sentences.")
    pattern_explanation: str = Field(..., description="Concise explanation of the detected candlestick and chart patterns. Maximum 3-4 sentences.")
    sr_explanation: str = Field(..., description="Concise explanation of the support and resistance structures. Maximum 3-4 sentences.")
    uncertainty_notes: List[str] = Field(default_factory=list, description="Concise, company-specific uncertainty notes. Prefer 2-4 distinct notes that cite different evidence sources. Each note must be a short string.")
    monitoring_checklist: List[str] = Field(default_factory=list, description="Specific metrics, levels, or triggers to monitor next. Must be a clean JSON list of strings.")
