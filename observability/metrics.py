# aios/observability/metrics.py
from __future__ import annotations
import json
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

def _labels_key(labels: Optional[Dict[str, Any]]) -> Tuple[Tuple[str, str], ...]:
    if not labels:
        return tuple()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))

@dataclass
class Histogram:
    count: int = 0
    total: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    
    def observe(self, v: float) -> None:
        self.count += 1
        self.total += v
        if v < self.min:
            self.min = v
        if v > self.max:
            self.max = v
    
    def to_dict(self) -> Dict[str, Any]:
        avg = (self.total / self.count) if self.count else 0.0
        return {
            "count": self.count,
            "sum": self.total,
            "min": 0.0 if self.min == float("inf") else self.min,
            "max": 0.0 if self.max == float("-inf") else self.max,
            "avg": avg,
        }

class MetricsRegistry:
    """
    线程安全、零依赖的指标收集：
    - counter: inc
    - gauge: set
    - histogram: observe（输出 count/sum/min/max/avg）
    """
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
        self._gauges: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
        self._hists: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], Histogram] = {}
        self._created_at = time.time()
    
    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, Any]] = None) -> None:
        key = (name, _labels_key(labels))
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + float(value)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, Any]] = None) -> None:
        key = (name, _labels_key(labels))
        with self._lock:
            self._gauges[key] = float(value)
    
    def observe(self, name: str, value: float, labels: Optional[Dict[str, Any]] = None) -> None:
        key = (name, _labels_key(labels))
        with self._lock:
            h = self._hists.get(key)
            if h is None:
                h = Histogram()
                self._hists[key] = h
            h.observe(float(value))
    
    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            counters = [
                {"name": n, "labels": dict(k), "value": v}
                for (n, k), v in self._counters.items()
            ]
            gauges = [
                {"name": n, "labels": dict(k), "value": v}
                for (n, k), v in self._gauges.items()
            ]
            hists = [
                {"name": n, "labels": dict(k), "value": h.to_dict()}
                for (n, k), h in self._hists.items()
            ]
            
            return {
                "created_at": self._created_at,
                "snapshot_at": time.time(),
                "counters": counters,
                "gauges": gauges,
                "histograms": hists,
            }
    
    def snapshot_json(self, indent: int = 2) -> str:
        return json.dumps(self.snapshot(), ensure_ascii=False, indent=indent)
    
    def write_snapshot(self, path: str) -> None:
        import pathlib
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.snapshot_json(indent=2), encoding="utf-8")

# 全局单例（你在任何地方 import METRICS 就能用）
METRICS = MetricsRegistry()
