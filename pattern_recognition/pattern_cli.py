"""
Pattern Recognition CLI - 命令行工具
快速查看系统状态和推荐策略
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pattern_recognizer import PatternRecognizerAgent
from hexagram_patterns import HexagramMatcher


def cmd_analyze():
    """分析当前系统状态"""
    agent = PatternRecognizerAgent()
    print(agent.generate_summary_report())


def cmd_history(hours=24):
    """查看历史模式"""
    agent = PatternRecognizerAgent()
    patterns = agent.get_recent_patterns(hours=hours)
    
    if not patterns:
        print(f"没有找到最近{hours}小时的模式记录")
        return
    
    print(f"=== 最近{hours}小时的模式历史 ===\n")
    for i, pattern in enumerate(patterns, 1):
        timestamp = pattern.get("timestamp", "")
        primary = pattern.get("primary_pattern", {})
        print(f"[{i}] {timestamp}")
        print(f"    卦象: {primary.get('name')} (置信度: {primary.get('confidence', 0) * 100:.1f}%)")
        print(f"    风险: {primary.get('risk_level')}")
        print()


def cmd_shift():
    """检测模式转变"""
    agent = PatternRecognizerAgent()
    shift = agent.detect_pattern_shift()
    
    if shift:
        print("=== 检测到模式转变 ===\n")
        print(f"时间: {shift['timestamp']}")
        print(f"转变: {shift['from_pattern']} → {shift['to_pattern']}")
        print(f"风险: {shift['from_risk']} → {shift['to_risk']}")
        print(f"\n{shift['message']}")
    else:
        print("未检测到模式转变")


def cmd_simulate(success_rate, growth_rate, stability, resource_usage):
    """模拟系统状态并匹配卦象"""
    metrics = {
        "success_rate": float(success_rate),
        "growth_rate": float(growth_rate),
        "stability": float(stability),
        "resource_usage": float(resource_usage),
    }
    
    matcher = HexagramMatcher()
    pattern, confidence = matcher.match(metrics)
    
    print("=== 模拟系统状态 ===\n")
    print(f"成功率: {metrics['success_rate'] * 100:.1f}%")
    print(f"增长率: {metrics['growth_rate'] * 100:+.1f}%")
    print(f"稳定性: {metrics['stability'] * 100:.1f}%")
    print(f"资源使用: {metrics['resource_usage'] * 100:.1f}%")
    print(f"\n匹配卦象: {pattern.name} (第{pattern.number}卦)")
    print(f"置信度: {confidence * 100:.1f}%")
    print(f"风险等级: {pattern.risk_level}")
    print(f"\n推荐策略:")
    print(f"  优先级: {pattern.strategy['priority']}")
    print(f"  模型偏好: {pattern.strategy['model_preference']}")
    print(f"  风险容忍度: {pattern.strategy['risk_tolerance']}")
    print(f"  建议行动:")
    for action in pattern.strategy['actions']:
        print(f"    - {action}")


def cmd_help():
    """显示帮助信息"""
    print("""
Pattern Recognition CLI - 使用指南

命令:
  analyze              分析当前系统状态
  history [hours]      查看历史模式（默认24小时）
  shift                检测模式转变
  simulate <sr> <gr> <st> <ru>  模拟系统状态
  help                 显示此帮助信息

示例:
  python pattern_cli.py analyze
  python pattern_cli.py history 48
  python pattern_cli.py shift
  python pattern_cli.py simulate 0.9 0.3 0.8 0.4

参数说明（simulate）:
  sr  - success_rate (成功率, 0-1)
  gr  - growth_rate (增长率, -1 ~ 1)
  st  - stability (稳定性, 0-1)
  ru  - resource_usage (资源使用, 0-1)
""")


def main():
    if len(sys.argv) < 2:
        cmd_help()
        return
    
    command = sys.argv[1]
    
    try:
        if command == "analyze":
            cmd_analyze()
        elif command == "history":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            cmd_history(hours)
        elif command == "shift":
            cmd_shift()
        elif command == "simulate":
            if len(sys.argv) < 6:
                print("错误: simulate 需要4个参数 (success_rate growth_rate stability resource_usage)")
                return
            cmd_simulate(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif command == "help":
            cmd_help()
        else:
            print(f"未知命令: {command}")
            cmd_help()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
