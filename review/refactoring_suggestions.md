# AIOS 重构建议

**更新日期**: 2026-02-24
**排序**: 按优先级 (P0 紧急 > P1 高 > P2 中 > P3 低)

---

## P0 — 紧急（影响系统正确性）

### R-01: 统一 EventBus 为单一实现

**现状**: 三套 EventBus（`aios/event_bus.py`, `core/event_bus.py`, `core/engine.py`），接口不兼容。

**方案**:
1. 以 `core/event_bus.py` + `core/event.py` 的 Event 对象模式为标准
2. 将 `core/engine.py` 的 5 层 emit 改为 EventBus 的适配器（保留 JSONL 写入能力）
3. 将顶层 `aios/event_bus.py` 标记为 deprecated，逐步迁移 `scheduler.py` 等引用方
4. 统一 `EventType` 常量到 `core/event.py`

**工作量**: ~2-3 天
**风险**: 中（需要逐个模块验证导入）

```
迁移路径:
aios/event_bus.py → deprecated, 加 import warning
aios/scheduler.py → 改用 core.event_bus
aios/core/engine.py → 保留 emit() 但内部调用 core.event_bus
```

### R-02: 修复文件读写竞态

**现状**: `decision_log.py`, `core/orchestrator.py` 的全文件重写无锁。

**方案**:
1. 短期：使用 `filelock` 库（pip install filelock）包装读写操作
2. 中期：将频繁读写的状态迁移到 SQLite（`aios/data/aios.db`）

**短期实现示例**:
```python
from filelock import FileLock

def update_outcome(decision_id: str, outcome: str) -> bool:
    lock = FileLock(str(_decisions_path()) + ".lock")
    with lock:
        records = _load_all()
        # ... modify ...
        _save_all(records)
```

**工作量**: 短期 0.5 天，中期 2-3 天

### R-03: 消除硬编码 Python 路径

**方案**: 在 `core/config.py` 中添加：
```python
import sys

def get_python() -> str:
    """获取 Python 解释器路径"""
    return get("paths.python", sys.executable)
```

然后全局替换 `PYTHON = r"C:\Program Files\Python312\python.exe"` 为 `from core.config import get_python`。

**工作量**: 0.5 天

---

## P1 — 高优先级（影响可维护性和可靠性）

### R-04: 实现 JSONL 文件轮转

**方案**: 创建 `core/log_rotate.py`：
```python
def rotate_jsonl(path: Path, max_size_mb: float = 10, keep_days: int = 30):
    """
    当文件超过 max_size_mb 时：
    1. 按日期归档: events.jsonl → events.2026-02-24.jsonl.gz
    2. 清理超过 keep_days 的归档
    3. 创建新的空文件
    """
```

在 pipeline 的每次运行末尾调用轮转检查。

**工作量**: 1 天

### R-05: 修复 bare except，引入结构化日志

**方案**:
1. 引入 Python 标准 `logging` 模块，配置统一的 logger
2. 将所有 `except: pass/continue` 改为：
   ```python
   except json.JSONDecodeError:
       logger.debug("Skipping malformed JSON line")
   except (IOError, OSError) as e:
       logger.warning(f"File operation failed: {e}")
   ```
3. 优先修复 `pipeline.py`, `reactor.py`, `engine.py` 中的关键路径

**工作量**: 2 天（逐步进行）

### R-06: 消除 sys.path 操控

**方案**:
1. 创建 `pyproject.toml`，将 aios 注册为可安装包
2. 使用 `pip install -e .` 开发模式安装
3. 所有导入改为绝对导入：`from aios.core.config import get`
4. 删除所有 `sys.path.insert` 调用

**pyproject.toml 示例**:
```toml
[project]
name = "aios"
version = "0.7.0"

[tool.setuptools.packages.find]
where = ["."]
include = ["aios*"]
```

**工作量**: 1-2 天

### R-07: 原子文件写入工具函数

**方案**: 在 `core/utils.py` 中提供：
```python
import tempfile, os

def atomic_write(path: Path, content: str, encoding: str = "utf-8"):
    """原子写入：先写临时文件，再 rename"""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        os.replace(tmp, str(path))  # 原子操作
    except:
        os.unlink(tmp)
        raise
```

替换 `sensors.py`, `executor.py`, `playbook.py` 等中的直接 `write_text()`。

**工作量**: 0.5 天

---

## P2 — 中优先级（提升代码质量）

### R-08: 添加类型注解

**优先级顺序**:
1. `core/event.py` — 已有，作为参考
2. `core/reactor.py` — 核心模块，参数多为 dict，需要 TypedDict 或 dataclass
3. `core/playbook.py` — 同上
4. `core/executor.py` — 公开 API 需要明确类型
5. `core/dispatcher.py` — 事件处理器签名

**示例**:
```python
from typing import TypedDict

class Alert(TypedDict):
    id: str
    rule_id: str
    severity: str
    message: str
    hit_count: int
    status: str

def react(alert: Alert, mode: str = "auto") -> list[dict]:
    ...
```

**工作量**: 2-3 天（逐步进行）

### R-09: 迁移测试到 pytest 框架

**方案**:
1. 安装 pytest: `pip install pytest pytest-cov`
2. 将 `tests/` 下的脚本改为 pytest 测试函数
3. 添加 fixtures 替代文件系统依赖
4. 添加 `conftest.py` 提供公共 fixture

**示例迁移**:
```python
# 旧: tests/test_circuit_breaker.py
if __name__ == "__main__":
    breaker = CircuitBreaker()
    breaker.record_failure("test", "pb1")
    assert breaker.states[("test", "pb1")] == "closed"

# 新:
import pytest
from aios.core.circuit_breaker import CircuitBreaker

@pytest.fixture
def breaker(tmp_path):
    cb = CircuitBreaker()
    cb.state_file = tmp_path / "state.json"
    return cb

def test_single_failure_stays_closed(breaker):
    breaker.record_failure("test", "pb1")
    assert breaker.states[("test", "pb1")] == CircuitBreaker.CLOSED
```

**工作量**: 3-5 天

### R-10: 合并重复模块

**需要合并的模块对**:
| 模块 A | 模块 B | 建议 |
|--------|--------|------|
| `model_router.py` | `model_router_v2.py` | 保留 v2，废弃 v1 |
| `core/orchestrator.py` | `collaboration/orchestrator.py` | 重命名 core 版为 `task_queue.py` |
| `core/circuit_breaker.py` | `agent_system/circuit_breaker.py` | 统一为 core 版 |
| `event_bus.py` (顶层) | `core/event_bus.py` | 见 R-01 |

**工作量**: 1-2 天

### R-11: 统一配置管理

**方案**: 将分散在各模块的常量迁移到 `config.yaml`：

```yaml
# config.yaml 新增
reactor:
  fuse_window_min: 30
  fuse_fail_threshold: 5
  fuse_cooldown_min: 60

sensors:
  cooldowns:
    file_modified: 600
    process_started: 300
    system_health: 1800

executor:
  dedup_window: 60
  non_retryable_patterns:
    - WnsUniversalSDK
    - FileNotFoundError
```

**工作量**: 1 天

---

## P3 — 低优先级（锦上添花）

### R-12: 拆分 dashboard/server.py

**现状**: 812 行单文件。

**建议拆分**:
```
dashboard/
  server.py          → FastAPI app 初始化 + 启动
  routes.py          → HTTP 路由
  websocket.py       → WebSocket 管理
  data_aggregator.py → 数据聚合逻辑
  templates/         → HTML 模板
```

### R-13: 清理 _deprecated 目录

确认以下文件无引用后删除：
- `agent_system/_deprecated/core_task_router.py`
- `agent_system/_deprecated/production_router.py`
- `agent_system/_deprecated/simple_router.py`
- `agent_system/_deprecated/task_router.py`
- `agent_system/_deprecated/unified_router.py`

### R-14: 统一 CLI 入口

**方案**: 创建 `aios/__main__.py` 作为统一入口：
```python
# python -m aios reactor scan
# python -m aios pipeline run
# python -m aios evolution score
```

使用 `click` 或 `argparse` 子命令模式，替代各模块独立的 CLI。

### R-15: 引入 pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks: [{id: black}]
  - repo: https://github.com/pycqa/isort
    hooks: [{id: isort}]
  - repo: https://github.com/pycqa/flake8
    hooks: [{id: flake8}]
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks: [{id: mypy, additional_dependencies: [types-requests]}]
```

---

## 重构路线图建议

```
Phase 1 (1 周): P0 全部 + R-05 (bare except)
  → 系统正确性保障

Phase 2 (1 周): R-04 (日志轮转) + R-06 (消除 sys.path) + R-07 (原子写入)
  → 可靠性提升

Phase 3 (2 周): R-08 (类型注解) + R-09 (pytest) + R-10 (合并模块)
  → 可维护性提升

Phase 4 (持续): P3 项目 + 新功能开发中同步改进
  → 代码质量持续提升
```
