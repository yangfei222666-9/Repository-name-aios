"""
测试 Production Reactor - 规则索引 + O(1) 查找
"""
import sys
import time
sys.path.insert(0, r"C:\Users\A\.openclaw\workspace\aios")

from core.production_reactor import get_reactor


def test_basic():
    """测试基本功能"""
    print("=" * 60)
    print("测试 1: 基本匹配和执行")
    print("=" * 60)
    
    reactor = get_reactor()
    
    # 测试事件 1: 网络错误
    event1 = {
        "type": "agent.error",
        "payload": {
            "error": "FailoverError: The AI service is temporarily unavailable (HTTP 502)"
        }
    }
    
    print("\n事件 1: 网络错误（502）")
    playbook = reactor.match(event1)
    
    if playbook:
        print(f"✅ 匹配到 playbook: {playbook['name']}")
        result = reactor.execute(playbook, event1)
        print(f"执行结果: {'成功' if result['success'] else '失败'}")
    else:
        print("❌ 未匹配到 playbook")


def test_performance():
    """测试性能（O(1) vs O(n)）"""
    print("\n" + "=" * 60)
    print("测试 2: 性能对比（O(1) vs O(n)）")
    print("=" * 60)
    
    reactor = get_reactor()
    
    # 测试事件
    event = {
        "type": "resource.memory_high",
        "payload": {
            "memory_percent": 85.5
        }
    }
    
    # O(1) 查找（使用索引）
    start = time.time()
    for _ in range(1000):
        reactor.match(event)
    indexed_time = time.time() - start
    
    print(f"\nO(1) 索引查找（1000次）: {indexed_time:.4f}s")
    print(f"平均每次: {indexed_time / 1000 * 1000:.2f}ms")
    
    # 模拟 O(n) 线性查找
    start = time.time()
    for _ in range(1000):
        # 遍历所有 playbook
        for playbook in reactor.playbooks:
            if reactor._check_playbook(playbook, event):
                break
    linear_time = time.time() - start
    
    print(f"\nO(n) 线性查找（1000次）: {linear_time:.4f}s")
    print(f"平均每次: {linear_time / 1000 * 1000:.2f}ms")
    
    speedup = linear_time / indexed_time
    print(f"\n⚡ 加速比: {speedup:.1f}x")


def test_multiple_events():
    """测试多个事件"""
    print("\n" + "=" * 60)
    print("测试 3: 多个事件匹配")
    print("=" * 60)
    
    reactor = get_reactor()
    
    events = [
        {
            "type": "agent.error",
            "payload": {"error": "HTTP 502"}
        },
        {
            "type": "resource.disk_full",
            "payload": {"disk_usage": 95}
        },
        {
            "type": "resource.memory_high",
            "payload": {"memory_percent": 85}
        },
        {
            "type": "sensor.lol.version_updated",
            "payload": {"version": "16.5.1"}
        },
        {
            "type": "unknown.event",
            "payload": {"data": "test"}
        }
    ]
    
    matched = 0
    for i, event in enumerate(events, 1):
        print(f"\n事件 {i}: {event['type']}")
        playbook = reactor.match(event)
        if playbook:
            print(f"  ✅ 匹配: {playbook['name']}")
            matched += 1
        else:
            print(f"  ❌ 未匹配")
    
    print(f"\n匹配率: {matched}/{len(events)} ({matched/len(events)*100:.0f}%)")


def test_stats():
    """测试统计"""
    print("\n" + "=" * 60)
    print("测试 4: 统计信息")
    print("=" * 60)
    
    reactor = get_reactor()
    stats = reactor.get_stats()
    
    print(f"\nPlaybook 数量: {stats['playbooks_count']}")
    print(f"规则索引大小: {stats['rule_index_size']}")
    print(f"关键词索引大小: {stats['keyword_index_size']}")
    print(f"\n执行统计:")
    for key, value in stats['stats'].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    print("🎯 Production Reactor 测试\n")
    
    # 测试 1: 基本功能
    test_basic()
    
    # 测试 2: 性能
    test_performance()
    
    # 测试 3: 多个事件
    test_multiple_events()
    
    # 测试 4: 统计
    test_stats()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
