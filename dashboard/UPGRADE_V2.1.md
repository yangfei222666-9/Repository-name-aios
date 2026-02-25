# Dashboard v2.1 升级方案 - 补齐实时信号层

## 🎯 核心问题
当前 v2 版本"结构对了"，但"内容少"，因为：
1. 只展示统计结果（1h/24h/7d），系统空闲时天然是 `--`
2. 缺少"永远有值的信号"（队列、熔断、Provider、心跳、事件流、告警）

## ✅ 解决方案：Show activity, not only metrics

---

## 📊 UI 结构升级（3层 + 1条状态栏）

### 0️⃣ 顶部状态栏（永远有内容）
放在标题右侧或第一行最上方：

```
┌─────────────────────────────────────────────────────────────────┐
│ 🟢 Normal | Provider: claude-sonnet-4-6 (OK) | 熔断: CLOSED     │
│ 队列: 0/0/0/0 (0/5) | 心跳: 33秒前 | [一键冒烟] [维护] [重放DLQ] │
└─────────────────────────────────────────────────────────────────┘
```

**字段说明：**
- 模式：Normal / Degraded / Recovery / Maintenance / Circuit Open
- Provider：当前模型 + 状态（OK/抖动/不可用）
- 熔断：CLOSED/HALF/OPEN（如果 OPEN：剩余 xx 秒）
- 队列：ready/running/retrying/dlq (used/max)
- 心跳：上次心跳 xx 秒前
- 快捷按钮：一键冒烟、触发维护、重放DLQ(10)

---

### 1️⃣ 第一层：表格 + 趋势列
保留现有两张表，每行右侧加一列：

```
指标          当前    1h     24h    7d     Δ24h
─────────────────────────────────────────────────
决策次数      --      12     83     420    ↑ +2%
执行成功率    --      92%    88%    85%    ↓ -4%
```

**实现：**
- 计算 `(24h - 7d/7) / (7d/7)` 得到变化率
- 用箭头 ↑/↓ 表示趋势

---

### 2️⃣ 第二层：事件流 + 行为记录（左右分栏）

#### 左侧：事件流（最近20条，实时滚动）
```
时间    | 类型                      | 状态 | 延迟  | Trace ID
────────────────────────────────────────────────────────────
13:29   | kernel.resource_snapshot  | ok   | 12ms  | abc123
13:08   | kernel.resource_snapshot  | ok   | 15ms  | def456
```

**过滤按钮：**
- 只看错误
- 只看关键（scheduler/reactor/provider/skill/alert）
- 只看DLQ

**数据源：**
```python
events = DashboardData.load_jsonl(EVENTS_FILE, limit=20)
# 就算系统空闲也会有 resource_snapshot/heartbeat，不会空
```

#### 右侧：最近10次行为（Tab 切换）
**Tab1: Reactor Runs**
```
时间    | 触发原因        | 动作              | 结果  | 耗时
──────────────────────────────────────────────────────────
19:02   | provider.error | provider_failover | 成功  | 820ms
18:44   | task.timeout   | retry             | 失败  | 900ms
```

**Tab2: Scheduler Decisions**
```
决策类型              | 次数 | 平均延迟 | 失败率
────────────────────────────────────────────
resource_allocation  | 45   | 280ms    | 2%
task_routing         | 32   | 150ms    | 0%
```

---

### 3️⃣ 第三层：图表 + 兜底策略

**兜底策略：**
- 少于 2 个点：显示 "上次值 + 最近更新时间"（别画空图）
- 无数据：显示 "暂无数据（过去7天），[生成测试负载]" 按钮

**新增 2 张图（比 evolution 更直观）：**
1. 失败率（7d）
2. p95 延迟（7d）
3. 队列长度（1h，5min bucket）（最像 OS）

---

## 🔧 4 张"永远有值的卡"（放在表格下方）

```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Queue & Concur  │ Circuit & Fail  │ DLQ             │ Skills          │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Ready: 0        │ 状态: CLOSED    │ 当前: 0 条      │ Top5 调用(1h)   │
│ Running: 0      │ 24h 触发: 0 次  │ 今日新增: 0     │ read_logs: 12   │
│ Retrying: 0     │ 最近切换:       │ [重放10][清空]  │ exec: 8         │
│ DLQ: 0          │ 无              │                 │ web_fetch: 5    │
│ 并发: 0/5       │                 │                 │                 │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

---

## 📦 后端补齐：snapshot v2.1 结构

### 新增字段（基于现有 events.jsonl）

```json
{
  "meta": { ... },
  "system": {
    "mode": "NORMAL",
    "health": "idle",
    "run_state": "idle",
    "provider": {
      "current": "claude-sonnet-4-6",
      "status": "OK",
      "circuit": {"state": "CLOSED", "opened_count_24h": 0}
    },
    "heartbeat": {
      "last_seen_sec_ago": 33,
      "last_ok_at": "2026-02-24T13:53:58"
    }
  },
  
  // ✅ 新增：Scheduler 队列状态
  "scheduler": {
    "queue": {
      "ready": 0,
      "running": 0,
      "retrying": 0,
      "dlq": 0,
      "concurrency": {"used": 0, "max": 5}
    },
    "last_completed": {
      "ts": "2026-02-24T13:29:20",
      "task": "resource_snapshot",
      "duration_ms": 12
    }
  },
  
  // ✅ 新增：事件流 tail（最近20条）
  "events_tail": {
    "items": [
      {
        "ts": "2026-02-24T13:29:20",
        "layer": "KERNEL",
        "event": "resource_snapshot",
        "status": "ok",
        "severity": "INFO",
        "latency_ms": 12,
        "trace_id": "abc123"
      }
    ]
  },
  
  // ✅ 新增：告警统计
  "alerts": {
    "crit": 0,
    "warn": 1,
    "info": 3,
    "unacked": 1
  },
  
  // ✅ 新增：技能调用统计（1h Top5）
  "skills": {
    "top_calls_1h": [
      {
        "name": "read_logs",
        "count": 12,
        "ok_rate": 0.92,
        "avg_ms": 80
      }
    ]
  },
  
  "summary": { ... },
  "activity": { ... },
  "trends": { ... }
}
```

---

## 🔨 实现代码（最小补齐）

### 1️⃣ 补齐 events_tail

```python
def get_events_tail_v2(limit: int = 20) -> Dict[str, Any]:
    """事件流 tail（最近20条）"""
    events = DashboardData.load_jsonl(EVENTS_FILE, limit=limit)
    
    items = []
    for event in events:
        items.append({
            "ts": event.get("ts", ""),
            "layer": event.get("layer", "UNKNOWN"),
            "event": event.get("event", "unknown"),
            "status": event.get("status", "ok"),
            "severity": event.get("severity", "INFO"),
            "latency_ms": event.get("payload", {}).get("duration_ms", 0),
            "trace_id": event.get("id", "")[:8]
        })
    
    return {"items": items}
```

### 2️⃣ 补齐 scheduler queue

```python
def get_scheduler_queue_v2() -> Dict[str, Any]:
    """Scheduler 队列状态"""
    # TODO: 从 scheduler 内存读取真实队列
    # 现在先从 events 推断
    events = DashboardData.load_jsonl(EVENTS_FILE, limit=100)
    
    # 统计最近的任务状态
    recent_tasks = [
        e for e in events
        if e.get("layer") == "KERNEL" and "task" in e.get("event", "").lower()
    ]
    
    running = sum(1 for e in recent_tasks if "running" in e.get("event", "").lower())
    
    return {
        "queue": {
            "ready": 0,
            "running": running,
            "retrying": 0,
            "dlq": 0,
            "concurrency": {"used": running, "max": 5}
        },
        "last_completed": {
            "ts": events[-1].get("ts", "") if events else None,
            "task": events[-1].get("event", "unknown") if events else None,
            "duration_ms": events[-1].get("payload", {}).get("duration_ms", 0) if events else 0
        }
    }
```

### 3️⃣ 补齐 alerts

```python
def get_alerts_v2() -> Dict[str, Any]:
    """告警统计"""
    alerts = DashboardData.load_jsonl(ALERTS_FILE)
    
    crit = sum(1 for a in alerts if a.get("severity") == "CRIT")
    warn = sum(1 for a in alerts if a.get("severity") == "WARN")
    info = sum(1 for a in alerts if a.get("severity") == "INFO")
    unacked = sum(1 for a in alerts if a.get("state") == "OPEN")
    
    return {
        "crit": crit,
        "warn": warn,
        "info": info,
        "unacked": unacked
    }
```

### 4️⃣ 补齐 skills

```python
def get_skills_v2() -> Dict[str, Any]:
    """技能调用统计（1h Top5）"""
    events = DashboardData.load_jsonl(EVENTS_FILE, limit=1000)
    now_ms = int(datetime.now().timestamp() * 1000)
    cutoff_ms = now_ms - 3600000  # 1h
    
    tool_events = [
        e for e in events
        if e.get("layer") == "TOOL" and e.get("timestamp", 0) > cutoff_ms
    ]
    
    from collections import defaultdict
    stats = defaultdict(lambda: {"count": 0, "ok": 0, "latencies": []})
    
    for event in tool_events:
        tool = event.get("payload", {}).get("type", "unknown")
        stats[tool]["count"] += 1
        
        if event.get("status") == "ok":
            stats[tool]["ok"] += 1
        
        if event.get("latency_ms"):
            stats[tool]["latencies"].append(event.get("latency_ms"))
    
    # 计算并排序
    items = []
    for tool, data in stats.items():
        ok_rate = data["ok"] / data["count"] if data["count"] > 0 else 0
        avg_ms = int(sum(data["latencies"]) / len(data["latencies"])) if data["latencies"] else 0
        
        items.append({
            "name": tool,
            "count": data["count"],
            "ok_rate": round(ok_rate, 2),
            "avg_ms": avg_ms
        })
    
    items.sort(key=lambda x: x["count"], reverse=True)
    
    return {"top_calls_1h": items[:5]}
```

---

## 🚀 "生成测试负载"按钮（强烈建议）

```python
@app.post("/api/actions/generate_test_load")
async def generate_test_load():
    """生成测试负载（30s）"""
    import subprocess
    
    try:
        # 1. Enqueue 10 个测试任务
        for i in range(10):
            task = {
                "id": f"test_{i}",
                "type": "noop" if i % 3 == 0 else "sleep" if i % 3 == 1 else "fail_once",
                "created_at": datetime.now().isoformat()
            }
            # TODO: 写入任务队列
        
        # 2. 触发 2 个 Reactor 规则
        # TODO: 模拟错误触发 Reactor
        
        # 3. 写入 1 条告警
        alert = {
            "id": "test_alert",
            "severity": "WARN",
            "message": "测试告警",
            "state": "OPEN",
            "created_at": datetime.now().isoformat()
        }
        # TODO: 写入告警
        
        return JSONResponse({"success": True, "message": "已生成测试负载"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
```

---

## 📋 字段映射表（现有 → v2.1）

| 现有字段 | v2.1 位置 | 说明 |
|---------|----------|------|
| `events.jsonl` 最近20条 | `events_tail.items` | 事件流 |
| `events.jsonl` KERNEL 层 | `scheduler.last_completed` | 最近完成任务 |
| `alert_fsm.jsonl` | `alerts` | 告警统计 |
| `events.jsonl` TOOL 层 | `skills.top_calls_1h` | 技能调用 |
| `system_health.events_1h` | `system.run_state` | idle/running |
| `system_health.last_event.timestamp` | `system.heartbeat.last_seen_sec_ago` | 心跳 |

---

## ✅ 立刻能见效的改动（优先级排序）

### 高优先级（今天完成）
1. ✅ 补齐 `events_tail` - 事件流永远有内容
2. ✅ 补齐 `scheduler.queue` - 队列状态
3. ✅ 补齐 `alerts` - 告警统计
4. ✅ 补齐 `skills` - 技能调用

### 中优先级（明天完成）
5. ⏳ 顶部状态栏 UI
6. ⏳ 4 张"永远有值的卡"
7. ⏳ 事件流过滤按钮

### 低优先级（有空再做）
8. ⏳ "生成测试负载"按钮
9. ⏳ 趋势列（Δ24h）
10. ⏳ 图表兜底策略

---

## 🎯 一句话总结

**Show activity, not only metrics.**

空闲时也要显示：
- 事件流（resource_snapshot）
- 队列状态（0/0/0/0）
- 心跳（33秒前）
- 最近完成任务（resource_snapshot, 12ms）

这样"空闲不空"！
