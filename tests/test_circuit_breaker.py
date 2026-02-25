"""
测试熔断器功能
验证：
1. 正常执行
2. 触发过密熔断
3. 失败次数熔断
4. HALF_OPEN 恢复
"""
import sys
import time
from pathlib import Path

# 添加路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aios.core.circuit_breaker import CircuitBreaker
from aios.core.event_bus import EventBus
from aios.core.event import create_event


def test_normal_execution():
    """测试1：正常执行"""
    print("\n" + "="*60)
    print("测试1：正常执行")
    print("="*60)
    
    breaker = CircuitBreaker(
        max_triggers_in_window=3,
        window_seconds=60,
        cooldown_seconds=5  # 短冷却时间便于测试
    )
    
    # 清空状态（避免旧数据干扰）
    breaker.states.clear()
    breaker.trigger_history.clear()
    breaker.failure_history.clear()
    breaker.open_time.clear()
    
    event_type = "resource.cpu_spike"
    playbook_id = "cpu_handler"
    
    # 第1次触发
    assert breaker.check(event_type, playbook_id) == True
    breaker.record_trigger(event_type, playbook_id)
    breaker.record_success(event_type, playbook_id)
    print("✅ 第1次触发成功")
    
    # 第2次触发
    print(f"触发历史: {breaker.trigger_history[(event_type, playbook_id)]}")
    assert breaker.check(event_type, playbook_id) == True
    breaker.record_trigger(event_type, playbook_id)
    breaker.record_success(event_type, playbook_id)
    print("✅ 第2次触发成功")
    
    print("✅ 测试1通过：正常执行")


def test_frequency_circuit_open():
    """测试2：触发过密熔断"""
    print("\n" + "="*60)
    print("测试2：触发过密熔断")
    print("="*60)
    
    breaker = CircuitBreaker(
        max_triggers_in_window=3,
        window_seconds=60,
        cooldown_seconds=5
    )
    
    # 清空状态
    breaker.states.clear()
    breaker.trigger_history.clear()
    breaker.failure_history.clear()
    breaker.open_time.clear()
    
    event_type = "resource.cpu_spike"
    playbook_id = "cpu_handler"
    
    # 连续3次触发（过密）
    for i in range(3):
        assert breaker.check(event_type, playbook_id) == True
        breaker.record_trigger(event_type, playbook_id)
        print(f"触发 {i+1}/3")
    
    # 第4次应该被熔断
    assert breaker.check(event_type, playbook_id) == False
    print("✅ 第4次被熔断（预期行为）")
    
    # 等待冷却
    print("等待 5 秒冷却...")
    time.sleep(5)
    
    # 应该进入 HALF_OPEN
    assert breaker.check(event_type, playbook_id) == True
    print("✅ 冷却后进入 HALF_OPEN")
    
    # 成功后应该恢复 CLOSED
    breaker.record_trigger(event_type, playbook_id)
    breaker.record_success(event_type, playbook_id)
    
    # 检查状态
    key = (event_type, playbook_id)
    state = breaker.states[key]
    print(f"当前状态: {state}")
    assert state == breaker.CLOSED, f"预期 CLOSED，实际 {state}"
    
    assert breaker.check(event_type, playbook_id) == True
    print("✅ 成功后恢复 CLOSED")
    
    print("✅ 测试2通过：触发过密熔断 + 恢复")


def test_failure_circuit_open():
    """测试3：失败次数熔断"""
    print("\n" + "="*60)
    print("测试3：失败次数熔断")
    print("="*60)
    
    breaker = CircuitBreaker(
        max_failures=2,
        failure_window_seconds=300,
        cooldown_seconds=5
    )
    
    # 清空状态
    breaker.states.clear()
    breaker.trigger_history.clear()
    breaker.failure_history.clear()
    breaker.open_time.clear()
    
    event_type = "resource.memory_high"
    playbook_id = "memory_handler"
    
    # 第1次失败
    assert breaker.check(event_type, playbook_id) == True
    breaker.record_trigger(event_type, playbook_id)
    breaker.record_failure(event_type, playbook_id)
    print("失败 1/2")
    
    # 第2次失败（触发熔断）
    assert breaker.check(event_type, playbook_id) == True
    breaker.record_trigger(event_type, playbook_id)
    breaker.record_failure(event_type, playbook_id)
    print("失败 2/2 → 熔断")
    
    # 第3次应该被熔断
    assert breaker.check(event_type, playbook_id) == False
    print("✅ 第3次被熔断（预期行为）")
    
    # 等待冷却
    print("等待 5 秒冷却...")
    time.sleep(5)
    
    # 应该进入 HALF_OPEN
    assert breaker.check(event_type, playbook_id) == True
    print("✅ 冷却后进入 HALF_OPEN")
    
    # HALF_OPEN 失败应该重新熔断
    breaker.record_trigger(event_type, playbook_id)
    breaker.record_failure(event_type, playbook_id)
    assert breaker.check(event_type, playbook_id) == False
    print("✅ HALF_OPEN 失败后重新熔断")
    
    print("✅ 测试3通过：失败次数熔断")


def test_status():
    """测试4：状态查询"""
    print("\n" + "="*60)
    print("测试4：状态查询")
    print("="*60)
    
    breaker = CircuitBreaker()
    
    # 创建一些状态
    breaker.check("event1", "playbook1")
    breaker.record_trigger("event1", "playbook1")
    
    breaker.check("event2", "playbook2")
    breaker.record_trigger("event2", "playbook2")
    breaker.record_trigger("event2", "playbook2")
    breaker.record_trigger("event2", "playbook2")  # 触发熔断
    
    status = breaker.get_status()
    
    print(f"总熔断器数: {status['total_circuits']}")
    print(f"OPEN: {status['open']}")
    print(f"HALF_OPEN: {status['half_open']}")
    print(f"CLOSED: {status['closed']}")
    
    assert status['total_circuits'] >= 2
    assert status['open'] >= 1
    
    print("✅ 测试4通过：状态查询")


def main():
    """运行所有测试"""
    print("="*60)
    print("熔断器测试套件")
    print("="*60)
    
    try:
        test_normal_execution()
        test_frequency_circuit_open()
        test_failure_circuit_open()
        test_status()
        
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
