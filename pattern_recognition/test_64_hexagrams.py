"""
64卦匹配测试 - 多场景验证
"""
from hexagram_patterns_extended import extend_hexagram_patterns
from hexagram_patterns import HexagramMatcher

# 扩展到64卦
extend_hexagram_patterns()

# 创建匹配器
matcher = HexagramMatcher()

# 测试场景
test_scenarios = [
    {
        "name": "顺利期",
        "metrics": {
            "success_rate": 0.9,
            "growth_rate": 0.3,
            "stability": 0.8,
            "resource_usage": 0.4,
        }
    },
    {
        "name": "危机期",
        "metrics": {
            "success_rate": 0.2,
            "growth_rate": -0.3,
            "stability": 0.3,
            "resource_usage": 0.8,
        }
    },
    {
        "name": "困难期",
        "metrics": {
            "success_rate": 0.5,
            "growth_rate": 0.0,
            "stability": 0.3,
            "resource_usage": 0.7,
        }
    },
    {
        "name": "稳定期",
        "metrics": {
            "success_rate": 0.8,
            "growth_rate": 0.0,
            "stability": 0.9,
            "resource_usage": 0.4,
        }
    },
    {
        "name": "成长期",
        "metrics": {
            "success_rate": 0.75,
            "growth_rate": 0.25,
            "stability": 0.7,
            "resource_usage": 0.5,
        }
    },
]

print("=== 64卦匹配测试 ===\n")

for scenario in test_scenarios:
    print(f"【{scenario['name']}】")
    metrics = scenario['metrics']
    print(f"  成功率: {metrics['success_rate']*100:.0f}%")
    print(f"  增长率: {metrics['growth_rate']*100:+.0f}%")
    print(f"  稳定性: {metrics['stability']*100:.0f}%")
    print(f"  资源使用: {metrics['resource_usage']*100:.0f}%")
    
    # 获取最佳匹配
    pattern, confidence = matcher.match(metrics)
    print(f"\n  最佳匹配: {pattern.name} (第{pattern.number}卦)")
    print(f"  置信度: {confidence:.1%}")
    print(f"  风险等级: {pattern.risk_level}")
    print(f"  推荐策略: {pattern.strategy['priority']}")
    print(f"  模型偏好: {pattern.strategy['model_preference']}")
    
    # 获取前3个匹配
    top_matches = matcher.get_top_matches(metrics, top_n=3)
    print(f"\n  备选卦象:")
    for i, (p, c) in enumerate(top_matches[1:3], 2):
        print(f"    {i}. {p.name} (第{p.number}卦) - {c:.1%}")
    
    print()

print("=== 测试完成 ===")
