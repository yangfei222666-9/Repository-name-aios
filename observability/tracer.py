# aios/observability/tracer.py
from __future__ import annotations
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_span_id: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
_parent_span_id: ContextVar[Optional[str]] = ContextVar("parent_span_id", default=None)

def _new_id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex}"

def current_trace_id() -> Optional[str]:
    return _trace_id.get()

def current_span_id() -> Optional[str]:
    return _span_id.get()

def current_parent_span_id() -> Optional[str]:
    return _parent_span_id.get()

def ensure_task_id(task: Dict[str, Any]) -> str:
    """
    强约束：task_id 永远非空。
    优先级：task['id'] / task['task_id'] -> source_path/path -> uuid
    """
    tid = task.get("id") or task.get("task_id")
    if tid and str(tid).strip():
        tid = str(tid).strip()
        task["id"] = tid
        return tid
    
    src = task.get("source_path") or task.get("path")
    if src and str(src).strip():
        tid = f"file:{str(src).strip()}"
        task["id"] = tid
        return tid
    
    tid = _new_id("task")
    task["id"] = tid
    return tid

@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    attributes: Dict[str, Any] = field(default_factory=dict)
    start_ns: int = field(default_factory=time.time_ns)
    end_ns: Optional[int] = None
    
    def end(self) -> None:
        if self.end_ns is None:
            self.end_ns = time.time_ns()
    
    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_ns is None:
            return None
        return (self.end_ns - self.start_ns) / 1_000_000.0

@contextmanager
def start_trace(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    创建一个新的 trace（root span）。
    """
    trace_id = _new_id("trace")
    span_id = _new_id("span")
    
    token_trace = _trace_id.set(trace_id)
    token_parent = _parent_span_id.set(None)
    token_span = _span_id.set(span_id)
    
    sp = Span(
        name=name,
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=None,
        attributes=attributes or {},
    )
    
    try:
        yield sp
    finally:
        sp.end()
        _span_id.reset(token_span)
        _parent_span_id.reset(token_parent)
        _trace_id.reset(token_trace)

@contextmanager
def span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    在当前 trace 下创建子 span；如果当前没有 trace，则自动创建一个 trace。
    """
    if current_trace_id() is None:
        with start_trace(name=f"auto:{name}", attributes=attributes) as root:
            yield root
        return
    
    parent = current_span_id()
    trace_id = current_trace_id() or _new_id("trace")
    span_id = _new_id("span")
    
    token_parent = _parent_span_id.set(parent)
    token_span = _span_id.set(span_id)
    
    sp = Span(
        name=name,
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent,
        attributes=attributes or {},
    )
    
    try:
        yield sp
    finally:
        sp.end()
        _span_id.reset(token_span)
        _parent_span_id.reset(token_parent)
