# aios/observability/logger.py
from __future__ import annotations
import json
import os
import threading
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# 直接从同目录导入
from .tracer import current_trace_id, current_span_id, current_parent_span_id

def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _safe(obj: Any) -> Any:
    try:
        json.dumps(obj, ensure_ascii=False)
        return obj
    except Exception:
        return str(obj)

@dataclass
class LogConfig:
    log_path: str = os.getenv("AIOS_LOG_PATH", "aios/logs/aios.jsonl")
    events_path: str = os.getenv("AIOS_EVENTS_PATH", "events.jsonl")

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO", cfg: Optional[LogConfig] = None) -> None:
        self.name = name
        self.level = level.upper()
        self.cfg = cfg or LogConfig()
        self._lock = threading.Lock()
        
        self._log_file = Path(self.cfg.log_path)
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._events_file = Path(self.cfg.events_path)
        self._events_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _level_ok(self, level: str) -> bool:
        order = {"DEBUG": 10, "INFO": 20, "WARN": 30, "WARNING": 30, "ERROR": 40}
        return order.get(level, 20) >= order.get(self.level, 20)
    
    def _write_jsonl(self, path: Path, obj: Dict[str, Any]) -> None:
        line = json.dumps({k: _safe(v) for k, v in obj.items()}, ensure_ascii=False)
        with self._lock:
            path.open("a", encoding="utf-8").write(line + "\n")
    
    def log(self, level: str, message: str, **fields: Any) -> None:
        level = level.upper()
        if not self._level_ok(level):
            return
        
        record = {
            "timestamp": _utc_iso(),
            "level": level.lower() if level != "WARNING" else "warn",
            "logger": self.name,
            "message": message,
            "trace_id": current_trace_id(),
            "span_id": current_span_id(),
            "parent_span_id": current_parent_span_id(),
            **fields,
        }
        
        self._write_jsonl(self._log_file, record)
    
    def debug(self, message: str, **fields: Any) -> None:
        self.log("DEBUG", message, **fields)
    
    def info(self, message: str, **fields: Any) -> None:
        self.log("INFO", message, **fields)
    
    def warn(self, message: str, **fields: Any) -> None:
        self.log("WARN", message, **fields)
    
    def error(self, message: str, **fields: Any) -> None:
        self.log("ERROR", message, **fields)
    
    def exception(self, message: str, **fields: Any) -> None:
        fields = dict(fields)
        fields["traceback"] = traceback.format_exc()
        self.log("ERROR", message, **fields)
    
    # -------- Events (events.jsonl) --------
    def emit_event(
        self,
        event_type: str,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        severity: str = "info",
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        evt = {
            "ts": _utc_iso(),
            "type": event_type,
            "severity": severity,
            "task_id": task_id,
            "agent_id": agent_id,
            "trace_id": current_trace_id(),
            "span_id": current_span_id(),
            "payload": payload or {},
        }
        self._write_jsonl(self._events_file, evt)

def get_logger(name: str, level: str = "INFO", cfg: Optional[LogConfig] = None) -> StructuredLogger:
    return StructuredLogger(name=name, level=level, cfg=cfg)
