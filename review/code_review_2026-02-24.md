# AIOS 代码审查报告

**日期**: 2026-02-24
**审查范围**: aios/ 全目录（172 个 Python 文件，约 31,868 行代码）
**审查人**: 代码审查专员

---

## 一、代码规模概览

| 指标 | 数值 |
|------|------|
| Python 文件总数 | 172 |
| 代码总行数 | ~31,868 |
| 核心模块 (core/) | ~30 文件 |
| 超过 400 行的文件 | 8 个 |
| 最大文件 | dashboard/server.py (812 行) |
| _deprecated 目录文件 | 5 个 |

---

## 二、代码规范评分

| 维度 | 评分 (1-10) | 说明 |
|------|-------------|------|
| 命名规范 | 7/10 | 函数/变量命名基本遵循 snake_case，但存在不一致 |
| 代码格式 | 6/10 | 缩进一致，但部分文件行过长，空行使用不规范 |
| 注释完整性 | 7/10 | 模块级 docstring 较好，函数级 docstring 覆盖不完整 |
| 类型注解 | 4/10 | 核心模块部分有注解，大量函数缺少参数/返回值类型 |
| 错误处理 | 5/10 | 大量 bare except，异常被静默吞掉 |
| 模块化 | 6/10 | 存在重复实现和职责不清的模块 |
| 测试覆盖 | 5/10 | 有测试文件但多为手动测试脚本，缺少单元测试框架 |

**综合评分: 5.7 / 10**

---

## 三、架构层面发现

### 3.1 EventBus 三重实现（严重）

项目中存在三个独立的 EventBus 实现，接口不兼容：

| 文件 | 类名 | emit 签名 | 备注 |
|------|------|-----------|------|
| `aios/event_bus.py` | EventBus | `emit(event_type: str, data: dict)` | 顶层模块，scheduler.py 使用 |
| `aios/core/event_bus.py` | EventBus | `emit(event: Event)` | 接受 Event 对象，v0.5 标准 |
| `aios/core/engine.py` | — | `emit(layer, event, status, ...)` | 5 层架构，JSONL 写入 |

**影响**: `scheduler.py` 引用 `event_bus.EventType`（顶层），而 `core/circuit_breaker.py` 引用 `core.event_bus.emit`（核心层），两者的 `EventType` 常量集合不同，事件无法互通。`dispatcher.py` 又使用 `core.event_bus.get_bus()` 的另一套 API（`bus.emit(topic, payload, priority, source)`），这是第四种调用方式。

### 3.2 sys.path 操控泛滥

几乎每个可独立运行的模块都在文件头部执行 `sys.path.insert(0, ...)`：

```python
# reactor.py
sys.path.insert(0, str(AIOS_ROOT))

# executor.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# pipeline.py
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(WS / "scripts"))
```

这导致导入路径不可预测，同名模块可能被错误覆盖。

### 3.3 硬编码路径

```python
# reactor.py
PYTHON = r"C:\Program Files\Python312\python.exe"

# verifier.py
PYTHON = r"C:\Program Files\Python312\python.exe"

# playbook.py 内置剧本
"target": '& "C:\\Program Files\\Python312\\python.exe" -m autolearn backup'
```

Python 解释器路径在至少 3 个文件中硬编码，无法在其他环境运行。

---

## 四、代码规范问题

### 4.1 Bare except 泛滥

以下模式在整个代码库中出现超过 40 次：

```python
except:
    continue

except Exception:
    pass
```

典型位置：
- `engine.py:load_events()` — 解析失败静默跳过
- `pipeline.py:stage_alerts()` — 整个告警阶段的内部异常被吞掉
- `evolution.py:compute_base_score()` — 导入失败返回默认值，无日志
- `sensors.py` — 多处 subprocess 调用异常被忽略

### 4.2 类型注解缺失

核心函数缺少类型注解的典型案例：

```python
# reactor.py
def react(alert, mode="auto"):  # alert: dict? Alert? 无从得知
    ...

# playbook.py
def match_alert(playbook, alert):  # 两个参数都是 dict，无类型提示
    ...

# feedback_loop.py
def analyze_playbook_patterns(since_hours=168):  # 返回值类型未标注
    ...
```

### 4.3 重复导入 / 冗余导入

```python
# circuit_breaker.py 第 10-11 行
import time
import json
# ... 第 14-15 行又重复了
import time
import json
```

### 4.4 不一致的编码声明

部分文件使用 `encoding="utf-8"` 打开文件，部分不指定。Windows 环境下默认编码非 UTF-8，可能导致读取失败。

---

## 五、潜在 Bug

### 5.1 [严重] decision_log.py 的 update_outcome 全文件重写竞态

```python
def update_outcome(decision_id: str, outcome: str) -> bool:
    # 读取所有记录
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f: ...
    # 重写文件
    with path.open("w", encoding="utf-8") as f:
        for record in records: ...
```

如果两个进程同时调用 `update_outcome`，会导致数据丢失。reactor 在执行多个 playbook 时可能并发触发此函数。

### 5.2 [严重] orchestrator.py 的 _save_all_tasks 全文件覆写

```python
def _save_all_tasks(tasks):
    with open(SUBTASKS_FILE, "w", encoding="utf-8") as f:
        for task in tasks: ...
```

`dequeue()` 调用 `_load_all_tasks()` + `_save_all_tasks()`，无文件锁。多进程并发时会丢失任务。

### 5.3 [中等] sensors.py 的 _save_state 无原子写入

```python
def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ...), encoding="utf-8")
```

如果写入过程中进程崩溃，状态文件会被截断为空。应使用 write-to-temp + rename 模式。

### 5.4 [中等] reactor.py 的 _record_fuse_success 是空函数

```python
def _record_fuse_success():
    """记录一次成功（不重置熔断，但记录）"""
    pass  # 熔断只看失败数，成功不影响
```

函数存在但从未被调用，且注释说"记录"但实际什么都不做。如果设计意图是成功不影响熔断，应删除此函数避免误导。

### 5.5 [中等] pipeline.py 的 stage_alerts 缩进错误

```python
def stage_alerts():
    try:
        ...
        return {
            "open": stats.get("open", 0),
            "ack": stats.get("ack", 0),
        "overdue": stats.get("overdue", 0),      # ← 缩进错误
        "resolved_today": stats.get("resolved_today", 0),
        ...
    }
    except Exception as e:
        return {"error": str(e)[:200]}
```

`"overdue"` 和后续键的缩进与前两个键不一致。虽然 Python 字典字面量允许这种写法，但这是明显的格式错误，可能掩盖了 try/except 范围问题。

### 5.6 [低] config.py 的 get_path 返回 None 无类型标注

```python
def get_path(key: str) -> Path:
    raw = get(key)
    if not raw:
        return None  # 返回值标注为 Path，实际可能返回 None
```

应标注为 `Optional[Path]`。

### 5.7 [低] app_alias.py 的 _T2S 映射表有重复字符

繁简映射表 `_T2S` 中存在大量重复的字符对（表的后半部分是前半部分的复制粘贴），`str.maketrans` 会用后出现的映射覆盖前面的，虽然不会报错但浪费空间且容易引入错误。

---

## 六、资源管理问题

### 6.1 文件句柄未使用 with 语句

大部分文件操作已使用 `with` 语句，但以下位置例外：

- `dashboard/server.py` 中的 `DashboardData.load_jsonl()` 使用 `path.read_text()` 一次性读取，对于大文件可能导致内存问题。

### 6.2 JSONL 文件无限增长

以下 JSONL 文件没有轮转/清理机制：
- `events/events.jsonl`
- `data/reactions.jsonl`
- `data/decisions.jsonl`
- `data/pipeline_runs.jsonl`
- `events/execution_log.jsonl`
- `data/feedback_suggestions.jsonl`

长期运行后这些文件会无限增长，`load_events()` 等函数每次全量读取会越来越慢。

### 6.3 subprocess 调用无资源限制

`sensors.py` 中多个 `subprocess.run()` 调用虽然设置了 timeout，但没有限制输出大小。恶意或异常的进程输出可能导致内存耗尽。

---

## 七、设计模式问题

### 7.1 全局单例不一致

项目中有多种单例实现方式：
- `event_bus.py`: 模块级 `_event_bus = None` + `get_event_bus()`
- `core/event_bus.py`: 模块级 `_global_bus = None` + `get_event_bus()`
- `core/circuit_breaker.py`: 模块级 `_circuit_breaker = None` + `get_circuit_breaker()`
- `core/model_router_v2.py`: 模块级 `_router = None` + `get_router()`

建议统一为一种模式，或使用 `functools.lru_cache` 简化。

### 7.2 配置管理分散

- `core/config.py` 提供了统一的配置加载
- 但 `reactor.py` 直接硬编码常量 `FUSE_WINDOW_MIN = 30`
- `sensors.py` 硬编码 `DEFAULT_COOLDOWNS` 字典
- `executor.py` 硬编码 `DEFAULT_DEDUP_WINDOW = 60`

这些应该统一到 `config.yaml` 中管理。

### 7.3 _deprecated 目录仍被引用

`agent_system/_deprecated/` 下有 5 个文件，应确认是否仍有代码引用它们，如果没有应彻底移除。

---

## 八、安全问题

### 8.1 [严重] reactor.py 执行任意 shell 命令

```python
def execute_action(action, dry_run=False):
    if atype == "shell":
        result = subprocess.run(
            ["powershell", "-Command", target],
            ...
        )
    elif atype == "python":
        result = subprocess.run(
            [PYTHON, "-X", "utf8", "-c", target],
            ...
        )
```

`target` 来自 playbook 配置文件，如果配置文件被篡改，可以执行任意命令。建议：
1. 对 playbook 文件做完整性校验
2. 限制可执行命令的白名单
3. 使用沙箱环境执行

### 8.2 [中等] verifier.py 的验证命令包含路径拼接

```python
VERIFY_RULES = {
    "backup_expired": {
        "command": f'& "{PYTHON}" -X utf8 -c "from pathlib import Path; ...; backup_dir = Path(r\'{WS / "autolearn" / "backups"}\'); ..."',
    },
}
```

路径直接拼接到 Python 代码字符串中，如果路径包含特殊字符可能导致注入。

---

## 九、测试质量

### 9.1 测试文件多为脚本式

`tests/` 目录下的文件大多是独立运行的脚本，而非使用 pytest/unittest 框架：

```python
# test_circuit_breaker.py, test_reactor.py 等
if __name__ == "__main__":
    # 手动测试代码
```

这意味着无法通过 `pytest` 一键运行所有测试，也无法集成到 CI/CD。

### 9.2 缺少 mock/fixture

测试直接依赖文件系统和外部进程（如 `tasklist`、`nvidia-smi`），无法在 CI 环境中运行。

---

## 十、总结

AIOS 项目展现了清晰的架构思路（感知→告警→响应→验证→反馈→进化），模块划分合理，版本迭代有序。主要问题集中在：

1. **EventBus 三重实现**是最大的架构债务，需要优先统一
2. **并发安全**问题在多个文件读写操作中存在
3. **错误处理**过于宽泛，大量异常被静默吞掉
4. **类型注解**覆盖率低，影响代码可维护性
5. **JSONL 文件无限增长**是潜在的性能定时炸弹

建议按优先级逐步修复，详见 `refactoring_suggestions.md`。
