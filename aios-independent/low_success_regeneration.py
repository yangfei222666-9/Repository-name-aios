"""
LowSuccess_Agent Phase 2 - 真实 sessions_spawn 版本
从模拟逻辑升级到真实执行
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from core.real_spawn import real_spawner
from config import MEMORY_DIR


async def scan_failed_tasks():
    """扫描失败任务（从 lessons.json 或 task_queue.jsonl）"""
    # 优先从 lessons.json 读取
    lessons_path = MEMORY_DIR / "lessons.json"
    if lessons_path.exists():
        with open(lessons_path, encoding="utf-8") as f:
            lessons = json.load(f)
            return [
                {
                    "task_id": lesson.get("id", f"lesson-{i}"),
                    "agent_id": "LowSuccess_Agent",
                    "payload": f"修复失败任务: {lesson.get('error_type', 'unknown')} - {lesson.get('context', '')}"
                }
                for i, lesson in enumerate(lessons.get("lessons", []))
                if lesson.get("status") != "resolved"
            ]
    
    # 备选：从 task_queue.jsonl 读取
    queue_path = MEMORY_DIR / "task_queue.jsonl"
    if queue_path.exists():
        with open(queue_path, encoding="utf-8") as f:
            return [
                json.loads(line)
                for line in f
                if json.loads(line).get("status") == "failed"
            ]
    
    return []


async def regenerate_low_success_agents():
    """Phase 2 主循环：真实重生失败任务"""
    print("=" * 60)
    print("🚀 LowSuccess_Agent Phase 2 已启动")
    print("   模式: 真实 sessions_spawn")
    print("   引擎: RealAgentSpawner")
    print("=" * 60)
    
    iteration = 0
    while True:
        iteration += 1
        print(f"\n📊 [迭代 {iteration}] 当前成功率: {real_spawner.success_rate}%")
        
        # 扫描失败任务
        failed_tasks = await scan_failed_tasks()
        
        if not failed_tasks:
            print("✅ 没有失败任务，系统健康")
            # 模拟一个测试任务（演示用）
            if iteration == 1:
                print("🧪 执行测试任务（演示真实spawn）")
                await real_spawner.spawn_and_execute(
                    task_id=f"test_task_{iteration}",
                    agent_id="agent_main",
                    payload="测试任务：验证真实spawn执行流程"
                )
        else:
            print(f"🔍 发现 {len(failed_tasks)} 个失败任务，开始重生...")
            for task in failed_tasks[:3]:  # 每次最多处理3个
                await real_spawner.spawn_and_execute(
                    task_id=task["task_id"],
                    agent_id=task["agent_id"],
                    payload=task["payload"]
                )
                await asyncio.sleep(2)  # 避免过载
        
        # 显示统计
        stats = real_spawner.get_stats()
        print(f"\n📈 统计信息:")
        print(f"   总任务: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failed']}")
        print(f"   成功率: {stats['success_rate']}%")
        
        # 检查是否达标
        if stats['success_rate'] >= 85.0:
            print("\n🎉 成功率已达标 85%+！Phase 2 完成！")
            break
        
        # 等待下一轮（真实后台间隔30秒）
        print(f"\n⏳ 等待30秒后进行下一轮扫描...")
        await asyncio.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(regenerate_low_success_agents())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断，Phase 2 停止")
        stats = real_spawner.get_stats()
        print(f"最终成功率: {stats['success_rate']}%")
