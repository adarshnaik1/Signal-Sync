# src/signal_sync/__init__.py
"""
Signal Sync - Agentic AI Retail Investment Advisor
BGV (Background Verification) Module
"""

from signal_sync.crew import BGVCrew
from signal_sync.main import run_bgv

__version__ = "0.1.0"
__all__ = ["BGVCrew", "run_bgv"]
