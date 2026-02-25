"""
测试 Production Scheduler - 优先级队列 + 并发
"""
import sys
import time
sys.path.insert(0, r"C:\Users\A\.openclaw\workspace\aios")

from core.production_scheduler import get_scheduler, Priority


def test_basic():
    """测试基本功能"""
    print("=" * 60)
    print("测试 1: 基本功能")
    print("=" * 60)
    
    scheduler = get_scheduler()
    scheduler.start()
    
    # 提交几个任务
    task1 = scheduler.submit("resource_check", {}, Priority.P3_LOW)
    task2 = scheduler.submit("trigger_reactor", {"reason": "cpu_spike"}, Priority.P1_HIGH)
    task3 = scheduler.submit("agent_spawn", {"template": "coder"}, Priority.P2_MEDIUM)
    
    print(f"\n提交了 3 个任务: {task1}, {task2}, {task3}")
    
    # 等待完成
    time.sleep(3)
    
    # 查看状态
    status = scheduler.get_status()
    print(f"\n调度器状态:")
    print(f"  队列大小: {status['queue_size']}")
    print(f"  运行中: {status['running_tasks']}")
    print(f"  已完成: {status['completed_count']}")
    print(f"  失败: {status['failed_count']}")


def test_priority():
    """测试优先级"""
    print("\n" + "=" * 60)
    print("测试 2: 优先级调度")
    print("=" * 60)
    
    scheduler = get_scheduler()
    
    # 提交不同优先级的任务
    print("\n提交任务（注意执行顺序）:")
    scheduler.submit("task_low_1", {}, Priority.P3_LOW)
    scheduler.submit("task_critical", {}, Priority.P0_CRITICAL)
    scheduler.submit("task_low_2", {}, Priority.P3_LOW)
    scheduler.submit("task_high", {}, Priority.P1_HIGH)
    scheduler.submit("task_medium", {}, Priority.P2_MEDIUM)
    
    # 等待完成
    time.sleep(3)
    
    print("\n预期执行顺序: P0 → P1 → P2 → P3 → P3")


def test_concurrent():
    """测试并发"""
    print("\n" + "=" * 60)
    print("测试 3: 并发处理（最多 5 个同时跑）")
    print("=" * 60)
    
    scheduler = get_scheduler()
    
    # 提交 10 个任务
    print("\n提交 10 个任务...")
    for i in range(10):
        scheduler.submit(f"task_{i}", {"index": i}, Priority.P3_LOW)
    
    # 观察并发
    for _ in range(5):
        status = scheduler.get_status()
        print(f"  运行中: {status['running_tasks']}, 队列: {status['queue_size']}")
        time.sleep(0.5)
    
    # 等待全部完成
    time.sleep(3)
    
    status = scheduler.get_status()
    print(f"\n最终状态:")
    print(f"  已完成: {status['completed_count']}")
    print(f"  失败: {status['failed_count']}")


def test_stats():
    """测试统计"""
    print("\n" + "=" * 60)
    print("测试 4: 统计信息")
    print("=" * 60)
    
    scheduler = get_scheduler()
    status = scheduler.get_status()
    
    print(f"\n统计:")
    for key, value in status['stats'].items():
        print(f"  {key}: {value}")


def test_stop():
    """测试停止"""
    print("\n" + "=" * 60)
    print("测试 5: 停止调度器")
    print("=" * 60)
    
    scheduler = get_scheduler()
    
    # 提交一些任务
    for i in range(5):
        scheduler.submit(f"final_task_{i}", {}, Priority.P3_LOW)
    
    # 等待一会
    time.sleep(2)
    
    # 停止
    scheduler.stop()
    
    print("✅ 调度器已停止")


if __name__ == "__main__":
    print("🎯 Production Scheduler 测试\n")
    
    # 测试 1: 基本功能
    test_basic()
    
    # 测试 2: 优先级
    test_priority()
    
    # 测试 3: 并发
    test_concurrent()
    
    # 测试 4: 统计
    test_stats()
    
    # 测试 5: 停止
    test_stop()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
