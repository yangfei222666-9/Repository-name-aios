"""
AIOS v0.6 心跳优化版本
减少延迟，提高性能

优化点：
1. 使用非阻塞的 CPU 检测（interval=0）
2. 移除不必要的 sleep
3. 缓存组件实例
4. 延迟初始化
5. 批量处理事件
6. 集成性能监控
7. 启动时预热组件
"""
import sys
import time
from pathlib import Path
from typing import Optional

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import EventType, Event
from core.event_bus import EventBus
from core.production_scheduler import get_scheduler, Priority
from core.production_reactor import get_reactor
from core.toy_score_engine import ToyScoreEngine
from core.notification_handler import start_notification_handler
from performance_monitor import get_monitor


# 全局缓存组件实例
_cached_components = {
    "bus": None,
    "scheduler": None,
    "reactor": None,
    "score_engine": None,
    "notification_handler": None,
    "last_init_time": 0,
    "warmed_up": False
}


def warmup_components():
    """预热组件（启动时调用）"""
    print("[AIOS] 预热组件中...")
    start_time = time.time()
    
    # 初始化所有组件
    components = get_or_create_components()
    
    # 标记为已预热
    _cached_components["warmed_up"] = True
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    print(f"[AIOS] ✅ 组件预热完成 ({elapsed_ms}ms)")
    
    return components


def get_or_create_components():
    """获取或创建组件（缓存）"""
    now = time.time()
    
    # 如果组件已初始化且在 5 分钟内，直接返回
    if _cached_components["bus"] and (now - _cached_components["last_init_time"]) < 300:
        return _cached_components
    
    # 初始化组件
    events_file = AIOS_ROOT / "data" / "events.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not _cached_components["bus"]:
        _cached_components["bus"] = EventBus(storage_path=events_file)
    
    if not _cached_components["scheduler"]:
        _cached_components["scheduler"] = get_scheduler()
        if not _cached_components["scheduler"].running:
            _cached_components["scheduler"].start()
    
    if not _cached_components["reactor"]:
        _cached_components["reactor"] = get_reactor()
    
    if not _cached_components["score_engine"]:
        _cached_components["score_engine"] = ToyScoreEngine(bus=_cached_components["bus"])
        _cached_components["score_engine"].start()
    
    if not _cached_components["notification_handler"]:
        _cached_components["notification_handler"] = start_notification_handler()
        _cached_components["notification_handler"].bus = _cached_components["bus"]
    
    _cached_components["last_init_time"] = now
    
    return _cached_components


def check_resources_fast():
    """快速检查系统资源（非阻塞）"""
    import psutil
    
    # 使用 interval=None 获取上次调用后的平均值（最快）
    # 第一次调用会返回 0，但后续调用会很快
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_percent = psutil.virtual_memory().percent
    
    # 如果 CPU 为 0（第一次调用），使用内存占用作为参考
    # 或者直接返回 0（表示未知）
    if cpu_percent == 0.0:
        # 不等待，直接返回 0
        pass
    
    return cpu_percent, memory_percent


# 全局采样计数器
_snapshot_counter = 0
_SNAPSHOT_SAMPLE_RATE = 3  # 每 3 次心跳记录 1 次快照（从 100% 降到 33%）

def log_resource_snapshot(cpu_percent, memory_percent):
    """记录资源快照（采样策略）"""
    global _snapshot_counter
    
    # 采样：每 N 次记录 1 次
    _snapshot_counter += 1
    if _snapshot_counter % _SNAPSHOT_SAMPLE_RATE != 0:
        return  # 跳过这次记录
    
    from core.engine import log_kernel
    
    try:
        log_kernel("resource_snapshot", "ok", 
                   cpu_percent=cpu_percent, 
                   memory_percent=memory_percent)
    except Exception as e:
        # 静默失败，不影响心跳
        pass


def run_heartbeat_optimized():
    """优化的心跳运行"""
    start_time = time.time()
    monitor = get_monitor()
    
    # 获取缓存的组件
    components = get_or_create_components()
    bus = components["bus"]
    scheduler = components["scheduler"]
    reactor = components["reactor"]
    score_engine = components["score_engine"]
    
    # 快速检查资源
    cpu_percent, memory_percent = check_resources_fast()
    
    # 记录资源使用
    monitor.record_resources(cpu_percent, memory_percent)
    
    # 异步记录资源快照（不等待）
    log_resource_snapshot(cpu_percent, memory_percent)
    
    # 批量收集需要处理的事件
    events_to_emit = []
    
    # 检查 CPU
    if cpu_percent > 80:
        event = Event.create(
            EventType.RESOURCE_CPU_SPIKE,
            source="heartbeat_monitor",
            payload={
                "cpu_percent": cpu_percent,
                "threshold": 80.0
            }
        )
        events_to_emit.append(event)
        
        # 提交到 Scheduler（异步）
        scheduler.submit(
            task_type="trigger_reactor",
            payload={"event": event.to_dict(), "reason": "CPU spike"},
            priority=Priority.P1_HIGH
        )
        
        # 记录告警
        monitor.record_alert("cpu_spike", f"CPU 使用率 {cpu_percent:.1f}% 超过阈值 80%")
    
    # 检查内存
    if memory_percent > 85:
        event = Event.create(
            EventType.RESOURCE_MEMORY_HIGH,
            source="heartbeat_monitor",
            payload={
                "memory_percent": memory_percent,
                "threshold": 85.0
            }
        )
        events_to_emit.append(event)
        
        # 提交到 Scheduler（异步）
        scheduler.submit(
            task_type="trigger_reactor",
            payload={"event": event.to_dict(), "reason": "Memory high"},
            priority=Priority.P1_HIGH
        )
        
        # 记录告警
        monitor.record_alert("memory_high", f"内存使用率 {memory_percent:.1f}% 超过阈值 85%")
    
    # 批量发布事件
    for event in events_to_emit:
        bus.emit(event)
    
    # 快速获取状态（不等待）
    current_score = score_engine.get_score()
    scheduler_status = scheduler.get_status()
    
    # 计算耗时
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # 决定输出
    result = None
    if current_score < 0.5:
        result = f"AIOS_DEGRADED:{current_score:.3f} ({elapsed_ms}ms)"
        monitor.record_alert("score_degraded", f"Evolution Score 降级: {current_score:.3f}")
    elif reactor.stats['total_executed'] > 0:
        result = f"AIOS_AUTO_FIXED:{reactor.stats['total_executed']} ({elapsed_ms}ms)"
    else:
        result = f"HEARTBEAT_OK ({elapsed_ms}ms)"
    
    # 记录心跳性能
    monitor.record_heartbeat(elapsed_ms, result)
    
    return result


def run_heartbeat_minimal():
    """最小化心跳（仅监控，不修复）"""
    start_time = time.time()
    monitor = get_monitor()
    
    # 如果还没预热，先预热
    if not _cached_components["warmed_up"]:
        warmup_components()
    
    # 快速检查资源
    cpu_percent, memory_percent = check_resources_fast()
    
    # 记录资源使用
    monitor.record_resources(cpu_percent, memory_percent)
    
    # 异步记录
    log_resource_snapshot(cpu_percent, memory_percent)
    
    # 计算耗时
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # 如果资源正常，直接返回
    if cpu_percent < 80 and memory_percent < 85:
        result = f"HEARTBEAT_OK ({elapsed_ms}ms)"
        monitor.record_heartbeat(elapsed_ms, result)
        return result
    
    # 如果资源异常，才初始化完整组件
    return run_heartbeat_optimized()


def warmup_on_import():
    """模块导入时自动预热（可选）"""
    if not _cached_components["warmed_up"]:
        try:
            warmup_components()
        except Exception as e:
            print(f"[AIOS] 预热失败: {e}")


# 可选：导入时自动预热（取消注释以启用）
# warmup_on_import()


if __name__ == "__main__":
    try:
        # 使用最小化心跳（更快）
        result = run_heartbeat_minimal()
        print(result)
    except Exception as e:
        print(f"❌ AIOS 心跳失败: {e}")
        import traceback
        traceback.print_exc()
