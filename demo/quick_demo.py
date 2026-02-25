"""
AIOS v0.5 快速演示
运行 3 个周期展示完整系统
"""
import time
import random
from pathlib import Path
import sys

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import EventType, create_event
from core.event_bus import EventBus
from core.toy_scheduler import ToyScheduler
from core.toy_reactor import ToyReactor
from core.toy_score_engine import ToyScoreEngine
from core.agent_state_machine import AgentStateMachine
from dashboard.adapter import DashboardAdapter


def quick_demo():
    """快速演示 3 个周期"""
    print("=" * 60)
    print("AIOS v0.5 快速演示（3个周期）")
    print("=" * 60)
    
    # 创建 EventBus
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
    
    print("\n2. 开始演示...\n")
    
    # 运行 3 个周期
    for i in range(3):
        print(f"[周期 {i+1}] ==================")
        
        # Agent 开始任务
        print("  → Agent 开始任务")
        agent.start_task(f"Task {i+1}")
        time.sleep(0.3)
        
        # 随机资源峰值
        if random.random() > 0.5:
            print("  → 资源峰值触发")
            bus.emit(create_event(
                EventType.RESOURCE_CPU_SPIKE,
                source="monitor",
                cpu_percent=random.uniform(85, 98)
            ))
            time.sleep(0.3)
        
        # 任务完成
        success = random.random() > 0.3
        if success:
            print("  → 任务成功")
            agent.complete_task(success=True)
        else:
            print("  → 任务失败 → 学习")
            agent.complete_task(success=False)
            time.sleep(0.2)
            agent.start_learning()
            time.sleep(0.2)
            agent.finish_learning()
        
        time.sleep(0.2)
        
        # Pipeline 完成
        bus.emit(create_event(
            EventType.PIPELINE_COMPLETED,
            source="pipeline",
            duration_ms=random.randint(100, 300)
        ))
        
        # 显示状态
        print(f"  [状态] Score: {score_engine.get_score():.3f} | "
              f"Agent: {agent.get_state().value} | "
              f"成功率: {agent.get_success_rate():.1%}\n")
        
        time.sleep(0.5)
    
    # 最终统计
    print("=" * 60)
    print("演示完成")
    print("=" * 60)
    
    print(f"\n[最终统计]")
    print(f"  Scheduler 决策: {len(scheduler.get_actions())}")
    print(f"  Reactor 执行: {len(reactor.get_executions())}")
    print(f"  系统评分: {score_engine.get_score():.3f}")
    print(f"  Agent 成功率: {agent.get_success_rate():.1%}")
    print(f"  总事件数: {bus.count_events()}")
    
    print(f"\n[事件文件]")
    print(f"  EventBus: {events_file}")
    print(f"  Dashboard: {dashboard_events_file}")
    
    print("\n提示：启动 Dashboard 查看事件流")
    print("  python aios/dashboard/server.py")
    print("  访问 http://localhost:9091")
    print("=" * 60)


if __name__ == "__main__":
    quick_demo()
