"""
AIOS v0.6 心跳集成（使用 Production Scheduler/Reactor）
每次心跳自动运行，监控系统健康度并自动修复

使用方法：
在心跳时调用：python -X utf8 aios/heartbeat_runner.py
"""
import sys
import time
from pathlib import Path

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import EventType, create_event
from core.event_bus import EventBus
from core.production_scheduler import get_scheduler, Priority
from core.production_reactor import get_reactor
from core.toy_score_engine import ToyScoreEngine
from core.notification_handler import start_notification_handler


def run_heartbeat():
    """心跳运行 AIOS v0.6（使用 Production 组件）"""
    
    # 使用持久化的 EventBus
    events_file = AIOS_ROOT / "data" / "events.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)
    
    bus = EventBus(storage_path=events_file)
    
    # 启动 Production Scheduler（如果还没启动）
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
    
    # 启动 Production Reactor
    reactor = get_reactor()
    
    # 启动 Score Engine（暂时保留旧版）
    score_engine = ToyScoreEngine(bus=bus)
    score_engine.start()
    
    # 启动通知处理器
    notification_handler = start_notification_handler()
    notification_handler.bus = bus
    
    # 检查系统资源
    import psutil
    from core.engine import log_kernel
    
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    
    # 记录资源使用到 events.jsonl（用于 baseline 分析）
    log_kernel("resource_snapshot", "ok", 
               cpu_percent=cpu_percent, 
               memory_percent=memory_percent)
    
    # 如果资源超标，提交任务到 Scheduler
    if cpu_percent > 80:
        event = create_event(
            EventType.RESOURCE_CPU_SPIKE,
            source="heartbeat_monitor",
            cpu_percent=cpu_percent,
            threshold=80.0
        )
        bus.emit(event)
        
        # 提交到 Scheduler
        scheduler.submit(
            task_type="trigger_reactor",
            payload={"event": event.to_dict(), "reason": "CPU spike"},
            priority=Priority.P1_HIGH
        )
    
    if memory_percent > 85:
        event = create_event(
            EventType.RESOURCE_MEMORY_HIGH,
            source="heartbeat_monitor",
            memory_percent=memory_percent,
            threshold=85.0
        )
        bus.emit(event)
        
        # 提交到 Scheduler
        scheduler.submit(
            task_type="trigger_reactor",
            payload={"event": event.to_dict(), "reason": "Memory high"},
            priority=Priority.P1_HIGH
        )
    
    # 等待事件处理
    time.sleep(0.5)
    
    # 检查评分
    current_score = score_engine.get_score()
    
    # 获取 Scheduler 状态
    scheduler_status = scheduler.get_status()
    
    # 如果评分低于阈值，报告
    if current_score < 0.5:
        print(f"⚠️ AIOS 系统降级：Score = {current_score:.3f}")
        print(f"   Scheduler 队列: {scheduler_status['queue_size']}")
        print(f"   Scheduler 运行中: {scheduler_status['running_tasks']}")
        print(f"   Reactor 匹配: {reactor.stats['total_matched']}")
        return f"AIOS_DEGRADED:{current_score:.3f}"
    
    # 如果有自动修复，报告
    if reactor.stats['total_executed'] > 0:
        print(f"ℹ️ AIOS 自动修复: {reactor.stats['total_executed']} 次")
        return f"AIOS_AUTO_FIXED:{reactor.stats['total_executed']}"
    
    # 正常情况，静默
    return "HEARTBEAT_OK"


if __name__ == "__main__":
    try:
        result = run_heartbeat()
        print(result)
    except Exception as e:
        print(f"❌ AIOS 心跳失败: {e}")
        import traceback
        traceback.print_exc()
