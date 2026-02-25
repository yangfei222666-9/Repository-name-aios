"""
测试阈值监控器（持续时间 + 滞回）
验证：
1. 短峰值不触发（< 10s）
2. 持续峰值触发（≥ 10s）
3. 滞回恢复（触发 80% / 恢复 70%）
4. 临界点抖动不触发
"""
import sys
import time
from pathlib import Path

# 添加路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aios.core.threshold_monitor import ThresholdMonitor
from aios.core.event_bus import EventBus, get_event_bus
from aios.core.event import EventType


def test_short_spike_no_trigger():
    """测试1：短峰值不触发（< 10s）"""
    print("\n" + "="*60)
    print("测试1：短峰值不触发（< 10s）")
    print("="*60)
    
    monitor = ThresholdMonitor(
        cpu_trigger_threshold=80.0,
        cpu_duration_seconds=10
    )
    
    bus = get_event_bus()
    events = []
    
    def capture(event):
        events.append(event)
    
    bus.subscribe("resource.*", capture)
    
    # 模拟短峰值（5 秒）
    for i in range(5):
        monitor.check_cpu(85.0)
        time.sleep(1)
        print(f"  {i+1}s: CPU 85%")
    
    # 回落
    monitor.check_cpu(70.0)
    print("  回落: CPU 70%")
    
    # 检查事件
    candidate_events = [e for e in events if e.type == EventType.RESOURCE_THRESHOLD_CANDIDATE]
    confirmed_events = [e for e in events if e.type == EventType.RESOURCE_THRESHOLD_CONFIRMED]
    
    assert len(candidate_events) == 1, f"应该有 1 个 candidate 事件，实际 {len(candidate_events)}"
    assert len(confirmed_events) == 0, f"不应该有 confirmed 事件，实际 {len(confirmed_events)}"
    
    print("✅ 测试1通过：短峰值不触发")


def test_sustained_spike_triggers():
    """测试2：持续峰值触发（≥ 10s）"""
    print("\n" + "="*60)
    print("测试2：持续峰值触发（≥ 10s）")
    print("="*60)
    
    monitor = ThresholdMonitor(
        cpu_trigger_threshold=80.0,
        cpu_duration_seconds=10
    )
    
    bus = get_event_bus()
    events = []
    
    def capture(event):
        events.append(event)
    
    bus.subscribe("resource.*", capture)
    
    # 模拟持续峰值（12 秒）
    for i in range(12):
        monitor.check_cpu(85.0)
        time.sleep(1)
        print(f"  {i+1}s: CPU 85%")
    
    # 检查事件
    candidate_events = [e for e in events if e.type == EventType.RESOURCE_THRESHOLD_CANDIDATE]
    confirmed_events = [e for e in events if e.type == EventType.RESOURCE_THRESHOLD_CONFIRMED]
    
    assert len(candidate_events) == 1, f"应该有 1 个 candidate 事件，实际 {len(candidate_events)}"
    assert len(confirmed_events) == 1, f"应该有 1 个 confirmed 事件，实际 {len(confirmed_events)}"
    
    print("✅ 测试2通过：持续峰值触发")


def test_hysteresis_recovery():
    """测试3：滞回恢复（触发 80% / 恢复 70%）"""
    print("\n" + "="*60)
    print("测试3：滞回恢复（触发 80% / 恢复 70%）")
    print("="*60)
    
    monitor = ThresholdMonitor(
        cpu_trigger_threshold=80.0,
        cpu_recover_threshold=70.0,
        cpu_duration_seconds=5  # 短持续时间便于测试
    )
    
    bus = get_event_bus()
    events = []
    
    def capture(event):
        events.append(event)
    
    bus.subscribe("resource.*", capture)
    
    # 触发
    for i in range(6):
        monitor.check_cpu(85.0)
        time.sleep(1)
    
    print("  已触发")
    
    # 回落到 75%（在触发阈值和恢复阈值之间）
    monitor.check_cpu(75.0)
    print("  CPU 75%（仍在告警中）")
    
    # 检查是否仍在告警
    assert monitor.cpu_confirmed == True, "应该仍在告警状态"
    
    # 回落到 70%（恢复阈值）
    monitor.check_cpu(70.0)
    print("  CPU 70%（恢复）")
    
    # 检查是否恢复
    assert monitor.cpu_confirmed == False, "应该已恢复"
    
    # 检查恢复事件
    recovered_events = [e for e in events if e.type == EventType.RESOURCE_RECOVERED]
    assert len(recovered_events) == 1, f"应该有 1 个 recovered 事件，实际 {len(recovered_events)}"
    
    print("✅ 测试3通过：滞回恢复")


def test_threshold_jitter_no_trigger():
    """测试4：临界点抖动不触发"""
    print("\n" + "="*60)
    print("测试4：临界点抖动不触发")
    print("="*60)
    
    monitor = ThresholdMonitor(
        cpu_trigger_threshold=80.0,
        cpu_duration_seconds=10
    )
    
    bus = get_event_bus()
    events = []
    
    def capture(event):
        events.append(event)
    
    bus.subscribe("resource.*", capture)
    
    # 模拟临界点抖动（79% → 81% → 79% → 81%）
    values = [79, 81, 79, 81, 79, 81, 79, 81]
    for i, val in enumerate(values):
        monitor.check_cpu(val)
        time.sleep(1)
        print(f"  {i+1}s: CPU {val}%")
    
    # 检查事件
    confirmed_events = [e for e in events if e.type == EventType.RESOURCE_THRESHOLD_CONFIRMED]
    
    assert len(confirmed_events) == 0, f"不应该有 confirmed 事件，实际 {len(confirmed_events)}"
    
    print("✅ 测试4通过：临界点抖动不触发")


def main():
    """运行所有测试"""
    print("="*60)
    print("阈值监控器测试套件")
    print("="*60)
    
    try:
        test_short_spike_no_trigger()
        test_sustained_spike_triggers()
        test_hysteresis_recovery()
        test_threshold_jitter_no_trigger()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
