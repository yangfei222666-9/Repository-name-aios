"""
测试 Provider Manager - 容灾三件套
模拟 502 错误场景
"""
import sys
import time
sys.path.insert(0, r"C:\Users\A\.openclaw\workspace\aios")

from core.provider_manager import get_provider_manager


# 模拟 LLM 调用函数
def mock_llm_call(provider_name: str, payload: dict) -> dict:
    """
    模拟 LLM 调用
    
    Args:
        provider_name: Provider 名称
        payload: 请求参数
    
    Returns:
        响应结果
    """
    print(f"  → 调用 {provider_name}...")
    
    # 模拟不同 provider 的行为
    if provider_name == "claude-sonnet-4-6":
        # 模拟 502 错误
        raise Exception("FailoverError: The AI service is temporarily unavailable (HTTP 502)")
    
    elif provider_name == "claude-opus-4-6":
        # 模拟超时
        raise Exception("FailoverError: The AI service is temporarily unavailable (HTTP 502) (timeout)")
    
    elif provider_name == "claude-haiku-4-5":
        # 成功
        return {
            "response": "Hello from Haiku!",
            "model": provider_name
        }
    
    else:
        raise Exception(f"Unknown provider: {provider_name}")


def test_failover():
    """测试 Failover 机制"""
    print("=" * 60)
    print("测试 1: Failover 机制")
    print("=" * 60)
    
    manager = get_provider_manager()
    
    # 执行任务
    result = manager.execute_with_failover(
        task_type="llm_call",
        task_payload={"prompt": "Hello, world!"},
        execute_fn=mock_llm_call
    )
    
    print("\n结果:")
    print(f"  成功: {result['success']}")
    if result['success']:
        print(f"  Provider: {result['provider']}")
        print(f"  尝试次数: {result['attempt']}")
        print(f"  响应: {result['result']}")
    else:
        print(f"  错误: {result['error']}")
        print(f"  DLQ: {result.get('dlq', False)}")


def test_dlq():
    """测试 DLQ"""
    print("\n" + "=" * 60)
    print("测试 2: DLQ（死信队列）")
    print("=" * 60)
    
    manager = get_provider_manager()
    
    # 查看 DLQ
    tasks = manager.get_dlq_tasks()
    print(f"\nDLQ 中的任务数: {len(tasks)}")
    
    for i, task in enumerate(tasks[:5], 1):
        print(f"\n任务 {i}:")
        print(f"  ID: {task.id}")
        print(f"  类型: {task.task_type}")
        print(f"  失败时间: {task.failed_at}")
        print(f"  重试次数: {task.retry_count}/{task.max_retries}")
        print(f"  错误: {task.error[:100]}...")


def test_all_fail():
    """测试所有 provider 都失败的情况"""
    print("\n" + "=" * 60)
    print("测试 3: 所有 Provider 都失败")
    print("=" * 60)
    
    manager = get_provider_manager()
    
    # 模拟所有 provider 都失败
    def all_fail(provider_name: str, payload: dict):
        raise Exception(f"FailoverError: {provider_name} is down (HTTP 502)")
    
    result = manager.execute_with_failover(
        task_type="llm_call",
        task_payload={"prompt": "This will fail"},
        execute_fn=all_fail
    )
    
    print("\n结果:")
    print(f"  成功: {result['success']}")
    print(f"  错误: {result['error']}")
    print(f"  任务 ID: {result.get('task_id')}")
    print(f"  进入 DLQ: {result.get('dlq', False)}")


def test_circuit_breaker():
    """测试熔断器"""
    print("\n" + "=" * 60)
    print("测试 4: 熔断器")
    print("=" * 60)
    
    manager = get_provider_manager()
    
    # 连续失败 3 次触发熔断
    def always_fail(provider_name: str, payload: dict):
        raise Exception("HTTP 502")
    
    print("\n连续失败 3 次...")
    for i in range(3):
        print(f"\n尝试 {i + 1}:")
        result = manager.execute_with_failover(
            task_type="test",
            task_payload={},
            execute_fn=always_fail
        )
    
    print("\n熔断器状态:")
    for provider, cb in manager.circuit_breakers.items():
        print(f"  {provider}: {cb['state']} (失败次数: {cb['failure_count']})")


if __name__ == "__main__":
    print("🛡️  Provider Manager 容灾测试\n")
    
    # 测试 1: Failover
    test_failover()
    
    # 测试 2: DLQ
    test_dlq()
    
    # 测试 3: 所有失败
    test_all_fail()
    
    # 测试 4: 熔断器
    test_circuit_breaker()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
