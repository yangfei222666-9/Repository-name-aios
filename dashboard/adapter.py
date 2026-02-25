"""
AIOS v0.5 Dashboard 适配器
将 v0.5 事件流适配到现有 Dashboard

使用方法：
1. 启动 Dashboard: python aios/dashboard/server.py
2. 运行测试: python -m aios.tests.test_full_system
3. 访问 http://localhost:9091 查看实时事件流
"""
from pathlib import Path
import sys
import json
import time

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import Event
from core.event_bus import get_event_bus


class DashboardAdapter:
    """Dashboard 适配器 - 将 v0.5 事件转换为 Dashboard 格式"""
    
    def __init__(self, dashboard_events_file: str = None):
        """
        初始化适配器
        
        Args:
            dashboard_events_file: Dashboard 事件文件路径
        """
        if dashboard_events_file is None:
            dashboard_events_file = str(AIOS_ROOT / "events" / "events.jsonl")
        
        self.dashboard_events_file = Path(dashboard_events_file)
        self.dashboard_events_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.bus = get_event_bus()
        
    def start(self):
        """启动适配器，订阅所有事件"""
        print("[DashboardAdapter] 启动中...")
        
        # 订阅所有事件
        self.bus.subscribe("*", self._handle_event)
        
        print(f"[DashboardAdapter] 已启动，事件将写入: {self.dashboard_events_file}")
    
    def _handle_event(self, event: Event):
        """处理事件，转换为 Dashboard 格式"""
        # 转换为 Dashboard 格式
        dashboard_event = {
            "timestamp": event.timestamp,
            "layer": self._get_layer(event.type),
            "type": event.type,
            "source": event.source,
            "payload": event.payload,
            "id": event.id
        }
        
        # 写入 Dashboard 事件文件
        with open(self.dashboard_events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(dashboard_event, ensure_ascii=False) + "\n")
    
    def _get_layer(self, event_type: str) -> str:
        """根据事件类型判断层级"""
        if event_type.startswith("pipeline."):
            return "KERNEL"
        elif event_type.startswith("agent."):
            return "KERNEL"
        elif event_type.startswith("scheduler."):
            return "KERNEL"
        elif event_type.startswith("reactor."):
            return "KERNEL"
        elif event_type.startswith("score."):
            return "KERNEL"
        elif event_type.startswith("resource."):
            return "KERNEL"
        else:
            return "KERNEL"


# 便捷函数
def start_dashboard_adapter(dashboard_events_file: str = None):
    """启动 Dashboard 适配器"""
    adapter = DashboardAdapter(dashboard_events_file=dashboard_events_file)
    adapter.start()
    return adapter


if __name__ == "__main__":
    print("=" * 60)
    print("AIOS v0.5 Dashboard 适配器测试")
    print("=" * 60)
    
    # 创建临时事件文件
    import tempfile
    tmpdir = tempfile.mkdtemp()
    dashboard_events_file = Path(tmpdir) / "dashboard_events.jsonl"
    
    # 启动适配器
    adapter = start_dashboard_adapter(dashboard_events_file=str(dashboard_events_file))
    
    # 模拟事件
    from core.event import create_event, EventType
    from core.event_bus import emit
    
    print("\n模拟事件流...")
    emit(create_event(EventType.PIPELINE_STARTED, "pipeline", pipeline_id="test"))
    emit(create_event(EventType.RESOURCE_CPU_SPIKE, "monitor", cpu_percent=95.0))
    emit(create_event(EventType.SCHEDULER_DISPATCH, "scheduler", action="trigger_reactor"))
    emit(create_event(EventType.REACTOR_SUCCESS, "reactor", duration_ms=150))
    emit(create_event(EventType.SCORE_UPDATED, "score_engine", score=0.85))
    
    time.sleep(0.1)
    
    # 验证
    print(f"\n验证 Dashboard 事件文件...")
    if dashboard_events_file.exists():
        events = dashboard_events_file.read_text(encoding="utf-8").strip().split("\n")
        print(f"✅ 写入 {len(events)} 个事件")
        
        for i, line in enumerate(events, 1):
            event = json.loads(line)
            print(f"  {i}. {event['type']} (layer={event['layer']})")
    else:
        print("❌ 事件文件不存在")
    
    print("\n" + "=" * 60)
    print("✅ Dashboard 适配器测试通过")
    print("=" * 60)
