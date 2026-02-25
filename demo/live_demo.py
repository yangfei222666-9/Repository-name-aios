"""
AIOS v0.5 实时演示
展示完整系统运行，可通过 Dashboard 查看

使用方法：
1. 启动 Dashboard: python aios/dashboard/server.py
2. 运行此脚本: python -m aios.demo.live_demo
3. 访问 http://localhost:9091 查看实时事件流
"""
import time
from pathlib import Path
import sys

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import Event, EventType, create_event
from core.event_bus import EventBus
from core.toy_scheduler import ToyScheduler
from core.toy_reactor import ToyReactor
from core.toy_score_engine import ToyScoreEngine
from core.agent_state_machine import AgentStateMachine
from dashboard.adapter import DashboardAdapter


def live_demo():
    """实时演示 AIOS v0.5"""
    print("=" * 60)
    print("AIOS v0.5 实时演示")
    print("=" * 60)
    print("\n提示：启动 Dashboard 查看实时事件流")
    print("  python aios/dashboard/server.py")
    print("  访问 http://localhost:9091")
    print("\n按 Ctrl+C 停止演示")
    print("=" * 60)
    
    # 创建 EventBus（使用真实路径）
    events_file = AIOS_ROOT / "data" / "events.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)
    
    bus = EventBus(storage_path=events_file)
    
    # 启动 Dashboard 适配器
    dashboard_events_file = AIOS_ROOT / "events" / "events.jsonl"
    adapter = DashboardAdapter(dashboard_events_file=str(dashboard_events_file))
    adapter.bus = bus
    adapter.start()
    
    # 启动所有组件
    print("\n1. 启动系统组件...")
    scheduler = ToyScheduler(bus=bus)
    scheduler.start()
    
    reactor = ToyReactor(bus=bus)
    reactor.start()
    
    score_engine = ToyScoreEngine(bus=bus)
    score_engine.start()
    
    agent = AgentStateMachine("demo_agent", bus=bus)
    
    print("\n2. 开始模拟工作负载...")
    print("   （每 5 秒一个周期，按 Ctrl+C 停止）\n")
    
    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"\n[周期 {cycle}] ==================")
            
            # 场景 1: 正常任务
            print("  → Agent 开始任务")
            agent.start_task(f"Task {cycle}")
            time.sleep(1)
            
            # 场景 2: 随机资源峰值
            import random
            if random.random() > 0.5:
                print("  → 资源峰值触发")
                bus.emit(create_event(
                    EventType.RESOURCE_CPU_SPIKE,
                    source="monitor",
                    cpu_percent=random.uniform(85, 98)
                ))
                time.sleep(1)
            
            # 场景 3: 任务完成（随机成功/失败）
            success = random.random() > 0.3
            if success:
                print("  → 任务成功")
                agent.complete_task(success=True)
            else:
                print("  → 任务失败 → 学习")
                agent.complete_task(success=False)
                time.sleep(0.5)
                agent.start_learning()
                time.sleep(0.5)
                agent.finish_learning()
            
            # 场景 4: Pipeline 完成
            bus.emit(create_event(
                EventType.PIPELINE_COMPLETED,
                source="pipeline",
                duration_ms=random.randint(100, 300)
            ))
            
            # 显示当前状态
            print(f"\n  [状态] Score: {score_engine.get_score():.3f} | "
                  f"Agent: {agent.get_state().value} | "
                  f"成功率: {agent.get_success_rate():.1%}")
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("演示结束")
        print("=" * 60)
        
        # 显示最终统计
        print(f"\n[最终统计]")
        print(f"  总周期数: {cycle}")
        print(f"  Scheduler 决策: {len(scheduler.get_actions())}")
        print(f"  Reactor 执行: {len(reactor.get_executions())}")
        print(f"  系统评分: {score_engine.get_score():.3f}")
        print(f"  Agent 成功率: {agent.get_success_rate():.1%}")
        print(f"  总事件数: {bus.count_events()}")
        
        print(f"\n[事件文件]")
        print(f"  EventBus: {events_file}")
        print(f"  Dashboard: {dashboard_events_file}")
        
        print("\n提示：访问 http://localhost:9091 查看事件流")
        print("=" * 60)


if __name__ == "__main__":
    live_demo()
