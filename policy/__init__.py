"""
AIOS Policy Engine - I Ching Interface
Shadow Mode: metrics → hexagram → strategy → log (no runtime control)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemMetrics:
    success_rate: float       # 0.0 ~ 1.0
    debate_rate: float        # 辩论触发率
    avg_latency: float        # 平均延迟（秒）
    healing_rate: float       # 自愈成功率
    failure_count: int        # 失败次数
    evolution_score: float    # Evolution Score


@dataclass
class HexagramResult:
    number: int               # 卦象编号 1-64
    name: str                 # 卦象名称（中文）
    phase: str                # 系统阶段描述
    confidence: float         # 置信度


@dataclass
class PolicySuggestion:
    hexagram: HexagramResult
    router_threshold: float   # 路由阈值建议
    debate_rate: float        # 辩论触发率建议
    retry_limit: int          # 重试次数建议
    reasoning: str            # 建议理由
    shadow_mode: bool = True  # 始终为 True（Shadow Mode）


def get_hexagram(metrics: SystemMetrics) -> HexagramResult:
    """
    从系统指标推导当前卦象
    Shadow Mode: 只读取指标，不影响 Runtime
    """
    from policy.iching_engine import IChingEngine
    engine = IChingEngine()
    return engine.detect(metrics)


def get_strategy(hexagram: HexagramResult) -> PolicySuggestion:
    """
    从卦象映射策略建议
    Shadow Mode: 只生成建议，不执行
    """
    from policy.iching_engine import IChingEngine
    engine = IChingEngine()
    return engine.suggest(hexagram)


def get_policy(metrics: SystemMetrics) -> PolicySuggestion:
    """
    完整流程: metrics → hexagram → strategy
    Shadow Mode: 只建议，不控制
    """
    hexagram = get_hexagram(metrics)
    return get_strategy(hexagram)
