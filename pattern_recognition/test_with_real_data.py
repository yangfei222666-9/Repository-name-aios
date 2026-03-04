"""
测试模式识别 - 使用真实数据
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from change_detector import SystemChangeMonitor
from hexagram_patterns import HexagramMatcher
from hexagram_patterns_extended import extend_hexagram_patterns

# 扩展到64卦
extend_hexagram_patterns()

# 创建监控器
data_dir = Path(__file__).parent.parent / "agent_system" / "data"
monitor = SystemChangeMonitor(data_dir)

# 加载任务
tasks = monitor.load_recent_tasks(hours=24)
print(f"=== 加载数据 ===")
print(f"加载了 {len(tasks)} 个任务\n")

if len(tasks) == 0:
    print("没有任务数据")
    exit(0)

# 更新检测器
monitor.update_from_tasks(tasks)

# 获取趋势
trends = monitor.get_all_trends()
print("=== 趋势分析 ===")
for metric, data in trends.items():
    print(f"{metric}:")
    print(f"  趋势: {data['trend']}")
    print(f"  置信度: {data['confidence']:.1%}")
    print(f"  当前值: {data['current_value']:.3f}")
    print()

# 计算系统指标
success_rate = trends["success_rate"]["current_value"] or 0.5
error_rate = trends["error_rate"]["current_value"] or 0.5

# 简单计算增长率和稳定性
success_trend = trends["success_rate"]["trend"]
if success_trend == "rising":
    growth_rate = 0.2
elif success_trend == "falling":
    growth_rate = -0.2
else:
    growth_rate = 0.0

success_std = trends["success_rate"]["std_dev"] or 0.1
stability = max(0, 1.0 - success_std * 2)

avg_duration = trends["avg_duration"]["current_value"] or 30
resource_usage = min(avg_duration / 30, 2.0) / 2

system_metrics = {
    "success_rate": success_rate,
    "growth_rate": growth_rate,
    "stability": stability,
    "resource_usage": resource_usage,
}

print("=== 系统指标 ===")
for key, value in system_metrics.items():
    print(f"{key}: {value:.3f}")
print()

# 匹配卦象
matcher = HexagramMatcher()
pattern, confidence = matcher.match(system_metrics)

print("=== 卦象匹配 ===")
print(f"最佳匹配: {pattern.name} (第{pattern.number}卦)")
print(f"置信度: {confidence:.1%}")
print(f"风险等级: {pattern.risk_level}")
print()

print("=== 推荐策略 ===")
strategy = pattern.strategy
print(f"优先级: {strategy['priority']}")
print(f"模型偏好: {strategy['model_preference']}")
print(f"风险容忍度: {strategy['risk_tolerance']}")
print(f"建议行动:")
for action in strategy['actions']:
    print(f"  - {action}")
