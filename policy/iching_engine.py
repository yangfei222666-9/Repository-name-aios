"""
AIOS I Ching Engine - Shadow Mode
职责: metrics → trigram → hexagram → strategy → log (只建议，不控制)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 添加父目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from policy import SystemMetrics, HexagramResult, PolicySuggestion
from policy.trigram_detector import detect_trigram, get_trigram_strategy
from policy.hexagram_detector import get_hexagram as get_hexagram_from_trigrams


class IChingEngine:
    """易经策略引擎（Shadow Mode）"""
    
    def __init__(self):
        self.workspace = Path(__file__).parent.parent
        self.timeline_file = self.workspace / "policy" / "hexagram_timeline.jsonl"
        self.timeline_file.parent.mkdir(exist_ok=True)
    
    def detect(self, metrics: SystemMetrics) -> HexagramResult:
        """
        从系统指标推导卦象
        Shadow Mode: 只读取指标，不影响 Runtime
        
        新流程: metrics → trigram → hexagram
        """
        # 1. 检测八卦（上卦 = 下卦 = 当前状态）
        trigram = detect_trigram(
            success_rate=metrics.success_rate,
            latency=metrics.avg_latency,
            debate_rate=metrics.debate_rate,
            resource_usage=0.0,  # 未来可扩展
            task_rate_spike=False  # 未来可扩展
        )
        
        # 2. 从八卦推导六十四卦（上卦 = 下卦 = 同一状态）
        hexagram = get_hexagram_from_trigrams(trigram.name, trigram.name)
        
        # 3. 返回 HexagramResult（兼容旧接口）
        return HexagramResult(
            number=hexagram.number,
            name=hexagram.name,
            phase=hexagram.phase,
            confidence=trigram.confidence
        )
    
    def suggest(self, hexagram: HexagramResult) -> PolicySuggestion:
        """
        从卦象映射策略建议
        Shadow Mode: 只生成建议，不执行
        
        新流程: 从八卦策略表获取建议
        """
        # 从八卦策略表获取策略
        strategy = get_trigram_strategy(hexagram.name)
        
        return PolicySuggestion(
            hexagram=hexagram,
            router_threshold=strategy["router_threshold"],
            debate_rate=strategy["debate_rate"],
            retry_limit=strategy["retry_limit"],
            reasoning=strategy["reasoning"],
            shadow_mode=True
        )
    
    def log_timeline(self, metrics: SystemMetrics, suggestion: PolicySuggestion):
        """
        记录卦象演化轨迹
        Shadow Mode: 只记录，不控制
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "hexagram": {
                "number": suggestion.hexagram.number,
                "name": suggestion.hexagram.name,
                "phase": suggestion.hexagram.phase,
                "confidence": suggestion.hexagram.confidence
            },
            "metrics": {
                "success_rate": metrics.success_rate,
                "debate_rate": metrics.debate_rate,
                "avg_latency": metrics.avg_latency,
                "healing_rate": metrics.healing_rate,
                "evolution_score": metrics.evolution_score
            },
            "suggestion": {
                "router_threshold": suggestion.router_threshold,
                "debate_rate": suggestion.debate_rate,
                "retry_limit": suggestion.retry_limit,
                "reasoning": suggestion.reasoning
            },
            "shadow_mode": True
        }
        
        with open(self.timeline_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_timeline(self, days: int = 7) -> list:
        """
        读取最近N天的卦象演化轨迹
        """
        if not self.timeline_file.exists():
            return []
        
        timeline = []
        with open(self.timeline_file, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                timeline.append(entry)
        
        # 返回最近N天
        return timeline[-days*24:]  # 假设每小时记录一次


def run_shadow_mode(metrics: SystemMetrics) -> PolicySuggestion:
    """
    完整 Shadow Mode 流程
    metrics → hexagram → strategy → log
    """
    engine = IChingEngine()
    
    # 1. 检测卦象
    hexagram = engine.detect(metrics)
    
    # 2. 生成策略建议
    suggestion = engine.suggest(hexagram)
    
    # 3. 记录轨迹
    engine.log_timeline(metrics, suggestion)
    
    return suggestion


if __name__ == "__main__":
    # 测试 Shadow Mode
    test_metrics = SystemMetrics(
        success_rate=0.95,
        debate_rate=0.12,
        avg_latency=8.1,
        healing_rate=0.85,
        failure_count=2,
        evolution_score=0.975
    )
    
    suggestion = run_shadow_mode(test_metrics)
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  AIOS Policy Engine - Shadow Mode Test  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"Current Hexagram: {suggestion.hexagram.name} (No.{suggestion.hexagram.number})")
    print(f"System Phase: {suggestion.hexagram.phase}")
    print(f"Confidence: {suggestion.hexagram.confidence:.1%}")
    print()
    print("Metrics:")
    print(f"  success_rate: {test_metrics.success_rate:.1%}")
    print(f"  debate_rate: {test_metrics.debate_rate:.1%}")
    print(f"  avg_latency: {test_metrics.avg_latency:.1f}s")
    print(f"  healing_rate: {test_metrics.healing_rate:.1%}")
    print(f"  evolution_score: {test_metrics.evolution_score:.1%}")
    print()
    print("Suggested Strategy (Shadow):")
    print(f"  router_threshold: {suggestion.router_threshold:.2f}")
    print(f"  debate_rate: {suggestion.debate_rate:.2f}")
    print(f"  retry_limit: {suggestion.retry_limit}")
    print(f"  reasoning: {suggestion.reasoning}")
    print()
    print("[OK] Shadow Mode test completed")
