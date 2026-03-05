"""
AIOS Trigram Detector - 八卦状态检测
职责: 从系统指标推导八卦状态（状态空间压缩）
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TrigramResult:
    """八卦检测结果"""
    name: str              # 卦名（乾/坤/震/巽/坎/离/艮/兑）
    symbol: str            # 卦象符号（☰/☷/☳/☴/☵/☲/☶/☱）
    phase: str             # 系统阶段描述
    confidence: float      # 置信度
    reasoning: str         # 检测理由


# 八卦策略映射表
TRIGRAM_STRATEGY = {
    "乾": {
        "router_threshold": 0.90,
        "debate_rate": 0.05,
        "retry_limit": 1,
        "reasoning": "高性能运行，允许更激进策略"
    },
    "坤": {
        "router_threshold": 0.85,
        "debate_rate": 0.10,
        "retry_limit": 2,
        "reasoning": "系统稳定，维持当前策略"
    },
    "震": {
        "router_threshold": 0.80,
        "debate_rate": 0.15,
        "retry_limit": 2,
        "reasoning": "任务突增，提高路由容量"
    },
    "巽": {
        "router_threshold": 0.82,
        "debate_rate": 0.18,
        "retry_limit": 2,
        "reasoning": "策略调整，微调参数"
    },
    "坎": {
        "router_threshold": 0.70,
        "debate_rate": 0.35,
        "retry_limit": 4,
        "reasoning": "风险期，增加辩论和重试"
    },
    "离": {
        "router_threshold": 0.75,
        "debate_rate": 0.25,
        "retry_limit": 3,
        "reasoning": "高负载，降低复杂任务"
    },
    "艮": {
        "router_threshold": 0.65,
        "debate_rate": 0.20,
        "retry_limit": 2,
        "reasoning": "资源瓶颈，限制任务并发"
    },
    "兑": {
        "router_threshold": 0.80,
        "debate_rate": 0.25,
        "retry_limit": 2,
        "reasoning": "多Agent协同，保持辩论"
    }
}


def detect_trigram(
    success_rate: float,
    latency: float,
    debate_rate: float,
    resource_usage: float = 0.0,
    task_rate_spike: bool = False
) -> TrigramResult:
    """
    从系统指标推导八卦状态
    
    Args:
        success_rate: 任务成功率 (0.0 ~ 1.0)
        latency: 平均延迟（秒）
        debate_rate: 辩论触发率 (0.0 ~ 1.0)
        resource_usage: 资源使用率 (0.0 ~ 1.0)
        task_rate_spike: 任务突增标志
    
    Returns:
        TrigramResult: 八卦检测结果
    """
    
    # 优先级检测（从高到低）
    
    # 1. 乾卦 ☰ - 高性能运行
    if success_rate >= 0.96 and latency <= 7:
        return TrigramResult(
            name="乾",
            symbol="☰",
            phase="High Performance",
            confidence=0.95,
            reasoning=f"成功率 {success_rate:.1%}，延迟 {latency:.1f}s，系统高效运行"
        )
    
    # 2. 坤卦 ☷ - 稳定期
    if 0.94 <= success_rate < 0.96 and latency <= 9:
        return TrigramResult(
            name="坤",
            symbol="☷",
            phase="Stable",
            confidence=0.92,
            reasoning=f"成功率 {success_rate:.1%}，延迟 {latency:.1f}s，系统平稳运行"
        )
    
    # 3. 震卦 ☳ - 任务突增
    if task_rate_spike:
        return TrigramResult(
            name="震",
            symbol="☳",
            phase="Task Surge",
            confidence=0.88,
            reasoning="任务突然增加，需要提高路由容量"
        )
    
    # 4. 坎卦 ☵ - 风险期（高优先级）
    if success_rate < 0.90:
        return TrigramResult(
            name="坎",
            symbol="☵",
            phase="Risk",
            confidence=0.85,
            reasoning=f"成功率 {success_rate:.1%}，系统出现错误，需要增加辩论和重试"
        )
    
    # 5. 离卦 ☲ - 高计算负载
    if latency > 12:
        return TrigramResult(
            name="离",
            symbol="☲",
            phase="High Load",
            confidence=0.82,
            reasoning=f"延迟 {latency:.1f}s，系统负载高，需要降低复杂任务"
        )
    
    # 6. 艮卦 ☶ - 资源瓶颈
    if resource_usage > 0.80:
        return TrigramResult(
            name="艮",
            symbol="☶",
            phase="Resource Bottleneck",
            confidence=0.80,
            reasoning=f"资源使用率 {resource_usage:.1%}，系统资源受限，需要限制任务并发"
        )
    
    # 7. 兑卦 ☱ - 多Agent协同
    if debate_rate > 0.20:
        return TrigramResult(
            name="兑",
            symbol="☱",
            phase="Collaboration",
            confidence=0.88,
            reasoning=f"辩论率 {debate_rate:.1%}，系统协作增强，保持辩论"
        )
    
    # 8. 巽卦 ☴ - 策略调整（默认）
    return TrigramResult(
        name="巽",
        symbol="☴",
        phase="Adjustment",
        confidence=0.85,
        reasoning="系统逐渐变化，需要微调策略"
    )


def get_trigram_strategy(trigram_name: str) -> dict:
    """
    获取八卦对应的策略
    
    Args:
        trigram_name: 卦名（乾/坤/震/巽/坎/离/艮/兑）
    
    Returns:
        dict: 策略参数
    """
    return TRIGRAM_STRATEGY.get(trigram_name, TRIGRAM_STRATEGY["巽"])


if __name__ == "__main__":
    # 测试八卦检测
    test_cases = [
        {
            "name": "高性能运行",
            "success_rate": 0.97,
            "latency": 6.5,
            "debate_rate": 0.08,
            "resource_usage": 0.45,
            "task_rate_spike": False
        },
        {
            "name": "稳定期",
            "success_rate": 0.95,
            "latency": 8.1,
            "debate_rate": 0.12,
            "resource_usage": 0.50,
            "task_rate_spike": False
        },
        {
            "name": "任务突增",
            "success_rate": 0.93,
            "latency": 10.2,
            "debate_rate": 0.15,
            "resource_usage": 0.60,
            "task_rate_spike": True
        },
        {
            "name": "风险期",
            "success_rate": 0.88,
            "latency": 11.5,
            "debate_rate": 0.28,
            "resource_usage": 0.55,
            "task_rate_spike": False
        },
        {
            "name": "高负载",
            "success_rate": 0.92,
            "latency": 14.3,
            "debate_rate": 0.18,
            "resource_usage": 0.65,
            "task_rate_spike": False
        },
        {
            "name": "资源瓶颈",
            "success_rate": 0.91,
            "latency": 10.8,
            "debate_rate": 0.16,
            "resource_usage": 0.85,
            "task_rate_spike": False
        },
        {
            "name": "多Agent协同",
            "success_rate": 0.94,
            "latency": 9.2,
            "debate_rate": 0.25,
            "resource_usage": 0.58,
            "task_rate_spike": False
        },
        {
            "name": "策略调整",
            "success_rate": 0.93,
            "latency": 9.8,
            "debate_rate": 0.14,
            "resource_usage": 0.52,
            "task_rate_spike": False
        }
    ]
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  AIOS Trigram Detector - Test Suite  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    for i, case in enumerate(test_cases, 1):
        result = detect_trigram(
            success_rate=case["success_rate"],
            latency=case["latency"],
            debate_rate=case["debate_rate"],
            resource_usage=case["resource_usage"],
            task_rate_spike=case["task_rate_spike"]
        )
        
        strategy = get_trigram_strategy(result.name)
        
        print(f"[Test {i}] {case['name']}")
        print(f"  Trigram: {result.name} {result.symbol}")
        print(f"  Phase: {result.phase}")
        print(f"  Confidence: {result.confidence:.1%}")
        print(f"  Reasoning: {result.reasoning}")
        print(f"  Strategy:")
        print(f"    router_threshold: {strategy['router_threshold']:.2f}")
        print(f"    debate_rate: {strategy['debate_rate']:.2f}")
        print(f"    retry_limit: {strategy['retry_limit']}")
        print()
    
    print("[OK] Trigram Detector test completed")
