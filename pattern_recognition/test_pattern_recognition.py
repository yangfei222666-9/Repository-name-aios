"""
测试 Pattern Recognition 系统
"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from change_detector import ChangeDetector, SystemChangeMonitor
from hexagram_patterns import HexagramMatcher, get_strategy_for_state
from pattern_recognizer import PatternRecognizerAgent


def test_change_detector():
    """测试变化检测器"""
    print("=" * 60)
    print("测试1: ChangeDetector - 变化趋势检测")
    print("=" * 60)
    
    # 测试上升趋势
    print("\n【上升趋势】（泰卦）")
    detector = ChangeDetector(window_size=10, threshold=0.1)
    for i in range(10):
        detector.add_data_point(0.5 + i * 0.05)
    
    summary = detector.get_summary()
    print(f"  趋势: {summary['trend']}")
    print(f"  置信度: {summary['confidence']:.2%}")
    print(f"  当前值: {summary['current_value']:.3f}")
    
    # 测试下降趋势
    print("\n【下降趋势】（否卦）")
    detector = ChangeDetector(window_size=10, threshold=0.1)
    for i in range(10):
        detector.add_data_point(0.9 - i * 0.05)
    
    summary = detector.get_summary()
    print(f"  趋势: {summary['trend']}")
    print(f"  置信度: {summary['confidence']:.2%}")
    print(f"  当前值: {summary['current_value']:.3f}")
    
    # 测试波动趋势
    print("\n【波动趋势】（屯卦）")
    detector = ChangeDetector(window_size=10, threshold=0.1)
    import random
    random.seed(42)
    for i in range(10):
        detector.add_data_point(0.7 + random.uniform(-0.2, 0.2))
    
    summary = detector.get_summary()
    print(f"  趋势: {summary['trend']}")
    print(f"  置信度: {summary['confidence']:.2%}")
    print(f"  当前值: {summary['current_value']:.3f}")
    
    # 测试稳定趋势
    print("\n【稳定趋势】（恒卦）")
    detector = ChangeDetector(window_size=10, threshold=0.1)
    for i in range(10):
        detector.add_data_point(0.85 + random.uniform(-0.02, 0.02))
    
    summary = detector.get_summary()
    print(f"  趋势: {summary['trend']}")
    print(f"  置信度: {summary['confidence']:.2%}")
    print(f"  当前值: {summary['current_value']:.3f}")


def test_hexagram_matcher():
    """测试卦象匹配器"""
    print("\n" + "=" * 60)
    print("测试2: HexagramMatcher - 卦象匹配")
    print("=" * 60)
    
    matcher = HexagramMatcher()
    
    # 测试场景1：高成功率、快速增长（泰卦）
    print("\n【场景1：顺利期】")
    metrics = {
        "success_rate": 0.9,
        "growth_rate": 0.3,
        "stability": 0.8,
        "resource_usage": 0.4,
    }
    pattern, confidence = matcher.match(metrics)
    print(f"  匹配卦象: {pattern.name} (第{pattern.number}卦)")
    print(f"  置信度: {confidence:.2%}")
    print(f"  风险等级: {pattern.risk_level}")
    print(f"  推荐策略: {pattern.strategy['priority']}")
    
    # 测试场景2：低成功率、负增长（否卦）
    print("\n【场景2：危机期】")
    metrics = {
        "success_rate": 0.2,
        "growth_rate": -0.3,
        "stability": 0.3,
        "resource_usage": 0.8,
    }
    pattern, confidence = matcher.match(metrics)
    print(f"  匹配卦象: {pattern.name} (第{pattern.number}卦)")
    print(f"  置信度: {confidence:.2%}")
    print(f"  风险等级: {pattern.risk_level}")
    print(f"  推荐策略: {pattern.strategy['priority']}")
    print(f"  建议行动: {', '.join(pattern.strategy['actions'][:2])}")
    
    # 测试场景3：中等成功率、高波动（屯卦）
    print("\n【场景3：困难期】")
    metrics = {
        "success_rate": 0.5,
        "growth_rate": 0.0,
        "stability": 0.3,
        "resource_usage": 0.7,
    }
    pattern, confidence = matcher.match(metrics)
    print(f"  匹配卦象: {pattern.name} (第{pattern.number}卦)")
    print(f"  置信度: {confidence:.2%}")
    print(f"  风险等级: {pattern.risk_level}")
    print(f"  推荐策略: {pattern.strategy['priority']}")
    
    # 测试场景4：稳定状态（恒卦）
    print("\n【场景4：稳定期】")
    metrics = {
        "success_rate": 0.8,
        "growth_rate": 0.0,
        "stability": 0.9,
        "resource_usage": 0.4,
    }
    pattern, confidence = matcher.match(metrics)
    print(f"  匹配卦象: {pattern.name} (第{pattern.number}卦)")
    print(f"  置信度: {confidence:.2%}")
    print(f"  风险等级: {pattern.risk_level}")
    print(f"  推荐策略: {pattern.strategy['priority']}")


def test_pattern_recognizer():
    """测试模式识别Agent"""
    print("\n" + "=" * 60)
    print("测试3: PatternRecognizer Agent - 完整分析")
    print("=" * 60)
    
    agent = PatternRecognizerAgent()
    
    # 生成摘要报告
    print("\n" + agent.generate_summary_report())


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AIOS Pattern Recognition 系统测试")
    print("基于易经64卦的系统状态识别与策略推荐")
    print("=" * 60)
    
    try:
        # 测试1：变化检测
        test_change_detector()
        
        # 测试2：卦象匹配
        test_hexagram_matcher()
        
        # 测试3：完整分析（需要真实数据）
        test_pattern_recognizer()
        
        print("\n" + "=" * 60)
        print("[OK] 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
