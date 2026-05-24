# TA CrewAI Plan (Merged)

This file has been merged into the canonical specification:

- spec/ta_implementation_spec.md

Reason:
- avoid divergence between planning and implementation specs
- keep one source of truth for architecture, tool contracts, runtime behavior, and pending deep-testing work

Current status summary:
- specialist-agent sequential flow is active
- manager stage removed for reliability/performance
- market data uses bundle_file handoff
- indicator/pattern/support-resistance loaders support both JSON and file-path inputs
- deep testing is pending and tracked in the canonical spec

Action for contributors:
- update only spec/ta_implementation_spec.md for future TA spec changes