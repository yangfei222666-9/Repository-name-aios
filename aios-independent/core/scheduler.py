"""
Scheduler - 后台任务调度器
Heartbeat v5 + RealSpawn + 自学习闭环
"""
import asyncio
from core.real_spawn import real_spawner
from core.self_learn import self_learner


async def start_background_tasks():
    """启动后台任务"""
    print("=" * 60)
    print("[SCHEDULER] AIOS 后台全自动启动")
    print("   - Heartbeat v5")
    print("   - RealSpawn 自动重生")
    print("   - Task Queue 监控")
    print("   - 自学习闭环")
    print("=" * 60)
    
    # 启动真实 LowSuccess 重生循环（每 30 秒扫描一次）
    asyncio.create_task(real_spawner.auto_regenerate_loop())
    
    # 启动自学习闭环（每 45 秒进化一次）
    asyncio.create_task(self_learner.auto_self_learn_loop())
    
    # Heartbeat 主循环
    iteration = 0
    while True:
        iteration += 1
        await asyncio.sleep(60)  # 每分钟一次心跳
        
        stats = real_spawner.get_stats()
        print(f"\n[HEARTBEAT] Tick #{iteration}")
        print(f"   成功率: {real_spawner.success_rate}%")
        print(f"   历史任务: {stats['total']}")
        print(f"   成功: {stats['success']} | 失败: {stats['failed']}")
        print(f"   进化分数: {self_learner.evolution_score['score']:.1f}")
        print(f"   教训数: {self_learner.evolution_score['lessons_learned']}")
