import json
from typing import Any, Dict, List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from signal_sync.ta.tools import (
    FetchOHLCVTool,
    FetchActionsTool,
    ValidateDataTool,
    FetchMarketDataBundleTool,
    ComputeSMATool,
    ComputeEMATool,
    ComputeRSITool,
    ComputeMACDTool,
    ComputeATRTool,
    ComputeBollingerTool,
    ComputeOBVTool,
    IndicatorRuleEngineTool,
    DetectCandlestickPatternsTool,
    DetectChartPatternsTool,
    FindSwingsTool,
    ClusterLevelsTool,
    VolumeZoneTool,
    DynamicSRTool,
    RenderChartTool,
    VisionReviewTool,
)
from signal_sync.ta.schemas import (
    MarketDataTaskOutput,
    IndicatorTaskOutput,
    PatternDetectionTaskOutput,
    SupportResistanceTaskOutput,
    StrategySignalTaskOutput,
    ExplanationTaskOutput,
)


@CrewBase
class TAAnalysisCrew:
    """
    Technical Analysis crew aligned to ta_implementation_spec.md.

    Deterministic tools are primary source-of-truth.
    LLM reasoning and vision output are secondary/advisory.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    agents: List[BaseAgent]
    tasks: List[Task]

    def _agent_config(self, key: str) -> Dict[str, Any]:
        cfg = getattr(self, "agents_config", None)
        if not isinstance(cfg, dict):
            raise ValueError("Agent config is not loaded. Ensure agents_config path is correct.")
        if key not in cfg:
            raise KeyError(f"Agent config key not found: {key}")
        value = cfg[key]
        if not isinstance(value, dict):
            raise ValueError(f"Agent config for '{key}' is not a mapping.")
        return value

    def _task_config(self, key: str) -> Dict[str, Any]:
        cfg = getattr(self, "tasks_config", None)
        if not isinstance(cfg, dict):
            raise ValueError("Task config is not loaded. Ensure tasks_config path is correct.")
        if key not in cfg:
            raise KeyError(f"Task config key not found: {key}")
        value = cfg[key]
        if not isinstance(value, dict):
            raise ValueError(f"Task config for '{key}' is not a mapping.")
        return value

    def __init__(self, ticker: str, horizon: str = "medium-term"):
        self.ticker = ticker
        self.horizon = horizon

        self.fetch_ohlcv_tool = FetchOHLCVTool()
        self.fetch_actions_tool = FetchActionsTool()
        self.validate_data_tool = ValidateDataTool()
        self.fetch_market_data_bundle_tool = FetchMarketDataBundleTool()

        self.compute_sma_tool = ComputeSMATool()
        self.compute_ema_tool = ComputeEMATool()
        self.compute_rsi_tool = ComputeRSITool()
        self.compute_macd_tool = ComputeMACDTool()
        self.compute_atr_tool = ComputeATRTool()
        self.compute_bollinger_tool = ComputeBollingerTool()
        self.compute_obv_tool = ComputeOBVTool()
        self.indicator_rule_engine_tool = IndicatorRuleEngineTool()

        self.detect_candlestick_patterns_tool = DetectCandlestickPatternsTool()
        self.detect_chart_patterns_tool = DetectChartPatternsTool()

        self.find_swings_tool = FindSwingsTool()
        self.cluster_levels_tool = ClusterLevelsTool()
        self.volume_zone_tool = VolumeZoneTool()
        self.dynamic_sr_tool = DynamicSRTool()

        self.render_chart_tool = RenderChartTool()
        self.vision_review_tool = VisionReviewTool()

    @agent
    # Manager agent removed: crew operates with specialist agents only.

    @agent
    def market_data_agent(self) -> Agent:
        cfg = self._agent_config("market_data_agent").copy()
        cfg["tools"] = [self.fetch_market_data_bundle_tool]
        cfg.setdefault("verbose", True)
        return Agent(**cfg)

    @agent
    def indicator_agent(self) -> Agent:
        cfg = self._agent_config("indicator_agent").copy()
        cfg["tools"] = [self.indicator_rule_engine_tool]
        cfg.setdefault("verbose", True)
        return Agent(**cfg)

    @agent
    def pattern_detection_agent(self) -> Agent:
        cfg = self._agent_config("pattern_detection_agent").copy()
        cfg["tools"] = [
            self.detect_candlestick_patterns_tool,
            self.detect_chart_patterns_tool,
            self.render_chart_tool,
            self.vision_review_tool,
        ]
        cfg.setdefault("verbose", True)
        return Agent(**cfg)

    @agent
    def support_resistance_agent(self) -> Agent:
        cfg = self._agent_config("support_resistance_agent").copy()
        cfg["tools"] = [
            self.find_swings_tool,
            self.cluster_levels_tool,
            self.volume_zone_tool,
            self.dynamic_sr_tool,
        ]
        cfg.setdefault("verbose", True)
        return Agent(**cfg)

    @agent
    def strategy_signal_agent(self) -> Agent:
        cfg = self._agent_config("strategy_signal_agent").copy()
        cfg.setdefault("verbose", True)
        return Agent(**cfg)

    @agent
    def explanation_agent(self) -> Agent:
        cfg = self._agent_config("explanation_agent").copy()
        cfg.setdefault("verbose", True)
        return Agent(**cfg)

    @task
    # Manager task removed: tasks run directly without a manager brief.

    @task
    def market_data_task(self) -> Task:
        cfg = self._task_config("market_data_task").copy()
        # No manager task; market data runs standalone
        cfg["output_pydantic"] = MarketDataTaskOutput
        return Task(**cfg)

    @task
    def indicator_task(self) -> Task:
        cfg = self._task_config("indicator_task").copy()
        cfg["context"] = [self.market_data_task()]
        cfg["output_pydantic"] = IndicatorTaskOutput
        return Task(**cfg)

    @task
    def pattern_detection_task(self) -> Task:
        cfg = self._task_config("pattern_detection_task").copy()
        cfg["context"] = [self.market_data_task()]
        cfg["output_pydantic"] = PatternDetectionTaskOutput
        return Task(**cfg)

    @task
    def support_resistance_task(self) -> Task:
        cfg = self._task_config("support_resistance_task").copy()
        cfg["context"] = [self.market_data_task()]
        cfg["output_pydantic"] = SupportResistanceTaskOutput
        return Task(**cfg)

    @task
    def strategy_signal_task(self) -> Task:
        cfg = self._task_config("strategy_signal_task").copy()
        cfg["context"] = [self.indicator_task(), self.pattern_detection_task(), self.support_resistance_task()]
        cfg["output_pydantic"] = StrategySignalTaskOutput
        return Task(**cfg)

    @task
    def explanation_task(self) -> Task:
        cfg = self._task_config("explanation_task").copy()
        cfg["context"] = [self.strategy_signal_task()]
        cfg["output_pydantic"] = ExplanationTaskOutput
        return Task(**cfg)

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)

    def run(self) -> str:
        inputs = {
            "ticker": self.ticker,
            "horizon": self.horizon,
        }
        result = self.crew().kickoff(inputs=inputs)

        if hasattr(result, "json_dict") and result.json_dict:
            output = json.dumps(result.json_dict, indent=2)
            print(output)
            return output
        if hasattr(result, "raw"):
            output = str(result.raw)
            print(output)
            return output
        output = str(result)
        print(output)
        return output
