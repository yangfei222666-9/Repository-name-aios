"""
AIOS Observability - 统一入口
"""
from .tracer import start_trace, span, ensure_task_id, current_trace_id, current_span_id
from .metrics import METRICS, MetricsRegistry
from .logger import get_logger, StructuredLogger

# 简单包装类（兼容旧代码）
class Tracer:
    """Tracer 包装类"""
    def start_trace(self, name):
        """启动一个 trace"""
        return start_trace(name)
    
    def start_as_current_span(self, name, **kwargs):
        """启动一个 span"""
        return span(name, **kwargs)

# 工厂函数（兼容旧代码）
def get_tracer(name=None):
    """获取 Tracer 实例"""
    return Tracer()

def get_metrics():
    """获取 Metrics 实例"""
    return METRICS

__all__ = [
    "start_trace",
    "span",
    "ensure_task_id",
    "current_trace_id",
    "current_span_id",
    "METRICS",
    "MetricsRegistry",
    "get_logger",
    "StructuredLogger",
    "get_tracer",
    "get_metrics",
    "Tracer"
]
