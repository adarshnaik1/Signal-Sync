"""
Package initializer for agent modules.

This file imports agent modules so they are evaluated and any
`@CrewBase` decorated classes register their agents/tasks with
the CrewAI project loader.
"""
from . import data_acquisition_agent  # noqa: F401
from . import business_analysis_agent  # noqa: F401
from . import financial_analysis_agent  # noqa: F401
from . import risk_analysis_agent  # noqa: F401
from . import valuation_agent  # noqa: F401
from . import verdict_agent  # noqa: F401
