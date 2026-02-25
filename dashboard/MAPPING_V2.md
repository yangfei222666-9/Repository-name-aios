# Dashboard v2 数据映射表

## 📋 现有数据 → v2 模型映射

### 1️⃣ Meta 信息
```python
# v2 模型
{
  "meta": {
    "version": "v2",
    "generated_at": datetime.now().isoformat(),
    "timezone": "+0800",
    "uptime_sec": 86400
  }
}

# 现有数据源
- generated_at: datetime.now().isoformat()
- uptime_sec: 需要新增（从系统启动时间计算）
```

---

### 2️⃣ System 状态
```python
# v2 模型
{
  "system": {
    "mode": "NORMAL",  # NORMAL | DEGRADED | RECOVERY | MAINTENANCE
    "health": "healthy",  # healthy | degraded | critical
    "run_state": "idle",  # idle | running | busy
    "provider": {
      "current": "claude-sonnet-4-6",
      "status": "OK",
      "circuit": {
        "state": "CLOSED",
        "opened_count_24h": 0
      }
    },
    "heartbeat": {
      "last_seen_sec_ago": 33,
      "last_ok_at": "2026-02-24T05:35:27+08:00"
    }
  }
}

# 现有数据源
system_health = DashboardData.get_system_health()
# → health: system_health["status"]  # healthy/warning/critical/idle
# → run_state: "idle" if system_health["events_1h"] == 0 else "running"

# Provider 信息（需要新增）
# → current: 从环境变量或配置读取
# → circuit.state: 从 agent_system/circuit_breaker_state.json 读取

# Heartbeat
# → last_seen_sec_ago: 从 system_health["last_event"]["timestamp"] 计算
```

---

### 3️⃣ Summary - Scheduler 表格
```python
# v2 模型
{
  "summary": {
    "scheduler": {
      "table": {
        "rows": [
          {
            "key": "decisions",
            "label": "决策次数",
            "unit": "count",
            "values": {
              "current": null,  # 当前无数据用 null
              "1h": 12,
              "24h": 83,
              "7d": 420
            },
            "empty_hint": "暂无调度（过去1小时）"
          }
        ]
      }
    }
  }
}

# 现有数据源
scheduler_stats = DashboardData.get_scheduler_stats()
# → values.1h: scheduler_stats["total_decisions"]
# → values.current: null（因为统计的是1小时，没有"当前"概念）

# 需要新增的字段
# → values.24h: 需要从 events.jsonl 统计最近24小时的决策
# → values.7d: 需要从 events.jsonl 统计最近7天的决策
```

**快速实现方案（最小改动）：**
```python
def get_scheduler_stats_v2():
    events = DashboardData.load_jsonl(EVENTS_FILE, limit=10000)
    now_ms = int(datetime.now().timestamp() * 1000)
    
    # 定义时间窗口
    windows = {
        "1h": now_ms - 3600000,
        "24h": now_ms - 86400000,
        "7d": now_ms - 604800000
    }
    
    # 筛选 KERNEL 决策事件
    scheduler_events = [
        e for e in events
        if e.get("layer") == "KERNEL" and "decision" in e.get("event", "").lower()
    ]
    
    # 统计各时间窗口
    stats = {}
    for window, cutoff_ms in windows.items():
        window_events = [e for e in scheduler_events if e.get("timestamp", 0) > cutoff_ms]
        
        total = len(window_events)
        executed = sum(1 for e in window_events if e.get("payload", {}).get("action"))
        latencies = [e.get("latency_ms", 0) for e in window_events if e.get("latency_ms")]
        
        stats[window] = {
            "decisions": total,
            "success_rate": executed / total if total > 0 else None,
            "latency_avg_ms": int(sum(latencies) / len(latencies)) if latencies else None,
            "failed": total - executed
        }
    
    return {
        "table": {
            "rows": [
                {
                    "key": "decisions",
                    "label": "决策次数",
                    "unit": "count",
                    "values": {
                        "current": None,
                        "1h": stats["1h"]["decisions"],
                        "24h": stats["24h"]["decisions"],
                        "7d": stats["7d"]["decisions"]
                    },
                    "empty_hint": "暂无调度（过去1小时）"
                },
                {
                    "key": "success_rate",
                    "label": "执行成功率",
                    "unit": "pct",
                    "values": {
                        "current": None,
                        "1h": stats["1h"]["success_rate"],
                        "24h": stats["24h"]["success_rate"],
                        "7d": stats["7d"]["success_rate"]
                    }
                },
                {
                    "key": "latency_avg_ms",
                    "label": "平均延迟",
                    "unit": "ms",
                    "values": {
                        "current": None,
                        "1h": stats["1h"]["latency_avg_ms"],
                        "24h": stats["24h"]["latency_avg_ms"],
                        "7d": stats["7d"]["latency_avg_ms"]
                    }
                },
                {
                    "key": "failed",
                    "label": "失败次数",
                    "unit": "count",
                    "values": {
                        "current": 0,
                        "1h": stats["1h"]["failed"],
                        "24h": stats["24h"]["failed"],
                        "7d": stats["7d"]["failed"]
                    }
                }
            ]
        }
    }
```

---

### 4️⃣ Summary - Reactor 表格
```python
# v2 模型
{
  "summary": {
    "reactor": {
      "table": {
        "rows": [
          {
            "key": "triggers",
            "label": "触发次数",
            "values": {"current": 2, "1h": 7, "24h": 35, "7d": 180}
          }
        ]
      }
    }
  }
}

# 现有数据源
reactor_stats = DashboardData.get_reactor_stats()
# → 当前只有总体统计，需要按时间窗口拆分

# 快速实现（类似 Scheduler）
def get_reactor_stats_v2():
    # 从 reactor_log.jsonl 或 events.jsonl 读取
    # 按 1h/24h/7d 统计触发次数、验证通过率、修复耗时、熔断次数
    pass
```

---

### 5️⃣ Activity - Reactor 最近执行
```python
# v2 模型
{
  "activity": {
    "reactor_runs": {
      "items": [
        {
          "ts": "2026-02-24T19:02:00+08:00",
          "trigger": "provider.error",
          "action": "provider_failover",
          "result": "success",
          "duration_ms": 820
        }
      ]
    }
  }
}

# 现有数据源
# 需要新增：从 reactor_log.jsonl 或 events.jsonl 读取最近10次执行记录
# 字段映射：
# - ts: event["ts"]
# - trigger: event["payload"]["trigger"] 或 event["event"]
# - action: event["payload"]["action"]
# - result: "success" if event["status"] == "success" else "failed"
# - duration_ms: event["latency_ms"]
```

---

### 6️⃣ Activity - Scheduler 最近决策 Top5
```python
# v2 模型
{
  "activity": {
    "scheduler_top_decisions": {
      "items": [
        {
          "type": "resource_allocation",
          "count": 45,
          "avg_ms": 280,
          "fail_rate": 0.02
        }
      ]
    }
  }
}

# 现有数据源
# 需要新增：从 events.jsonl 统计最近24小时的决策类型
# 按 type 分组，计算 count、avg_ms、fail_rate
```

---

### 7️⃣ Trends - 趋势图
```python
# v2 模型
{
  "trends": {
    "series": [
      {
        "key": "auto_execute_rate",
        "label": "自动执行率",
        "points": [{"ts": "2026-02-18", "v": 0.40}]
      }
    ]
  }
}

# 现有数据源
evolution_trend = DashboardData.get_evolution_trend()
# → 已有 base 和 reactor 两条线
# → 需要新增 decision_latency_p95_ms 和 failure_rate
```

---

## 🚀 最短实现路线

### Step 1: 新增 `/api/snapshot/v2` 接口
```python
@app.get("/api/snapshot/v2")
async def get_snapshot_v2():
    return JSONResponse({
        "meta": {
            "version": "v2",
            "generated_at": datetime.now().isoformat(),
            "timezone": "+0800",
            "uptime_sec": 86400  # TODO: 计算真实 uptime
        },
        "system": {
            "mode": "NORMAL",
            "health": DashboardData.get_system_health()["status"],
            "run_state": "idle",  # TODO: 根据 events_1h 判断
            "provider": {
                "current": "claude-sonnet-4-6",
                "status": "OK",
                "circuit": {"state": "CLOSED", "opened_count_24h": 0}
            },
            "heartbeat": {
                "last_seen_sec_ago": 33,  # TODO: 计算
                "last_ok_at": datetime.now().isoformat()
            }
        },
        "summary": {
            "scheduler": get_scheduler_stats_v2(),
            "reactor": get_reactor_stats_v2()
        },
        "activity": {
            "reactor_runs": get_reactor_recent_v2(),
            "scheduler_top_decisions": get_scheduler_top_v2(),
            "circuit_history": get_circuit_history_v2()
        },
        "trends": {
            "series": get_trends_v2()
        },
        "ui_hints": {
            "zero_policy": "use_null_for_no_data_show_dash",
            "dash_for_null": "--"
        }
    })
```

### Step 2: 更新前端 index_v2.html
```javascript
// 修改 pollSnapshot() 函数
async function pollSnapshot() {
    const response = await fetch('/api/snapshot/v2');  // 改为 v2 接口
    const data = await response.json();
    updateDashboard(data);
}

// 修改 updateDashboard() 函数
function updateDashboard(data) {
    // 直接按 v2 结构渲染
    const scheduler = data.summary.scheduler.table.rows;
    scheduler.forEach(row => {
        document.getElementById(`sched-1h-${row.key}`).textContent = 
            row.values["1h"] ?? "--";
        // ...
    });
}
```

---

## 📝 TODO 清单

### 高优先级（今天完成）
- [ ] 实现 `get_scheduler_stats_v2()` - 按时间窗口统计
- [ ] 实现 `get_reactor_stats_v2()` - 按时间窗口统计
- [ ] 实现 `get_reactor_recent_v2()` - 最近10次执行
- [ ] 实现 `get_scheduler_top_v2()` - Top5决策类型
- [ ] 新增 `/api/snapshot/v2` 接口
- [ ] 更新 `index_v2.html` 前端渲染逻辑

### 中优先级（明天完成）
- [ ] 实现 `get_circuit_history_v2()` - 熔断历史
- [ ] 实现 `get_trends_v2()` - 4条趋势线
- [ ] 计算真实 uptime
- [ ] 计算 heartbeat last_seen_sec_ago

### 低优先级（有空再做）
- [ ] Provider 信息自动检测
- [ ] 系统模式自动判定（NORMAL/DEGRADED/RECOVERY）
- [ ] run_state 智能判断（idle/running/busy）

---

## 🎯 一句话总结

**Use null for no data.** （优斯 纳哦 佛 No Data）

当前值为 0 或无数据时，用 `null` 而非 `0`，前端显示 `--` 或 `empty_hint`。
