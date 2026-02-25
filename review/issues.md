# AIOS 问题清单

**更新日期**: 2026-02-24
**排序**: 按严重程度 (CRITICAL > HIGH > MEDIUM > LOW)

---

## CRITICAL（必须修复）

### C-01: EventBus 三重实现，事件系统碎片化
- **文件**: `aios/event_bus.py`, `aios/core/event_bus.py`, `aios/core/engine.py`
- **描述**: 三套独立的事件总线实现，接口不兼容。`scheduler.py` 使用顶层 EventBus，`circuit_breaker.py` 使用 core EventBus，`reactor.py` 使用 engine.emit()。事件无法跨模块流通。
- **影响**: 系统核心通信机制断裂，模块间无法正确协作
- **建议**: 统一为 `core/event_bus.py` 的 Event 对象模式，废弃其他两个

### C-02: decision_log.py 全文件重写存在竞态条件
- **文件**: `aios/core/decision_log.py` → `update_outcome()`
- **描述**: 读取全部记录到内存 → 修改 → 重写整个文件，无文件锁
- **影响**: 并发调用时数据丢失
- **建议**: 使用文件锁（`fcntl`/`msvcrt`）或改用 SQLite

### C-03: orchestrator.py (core) 的 _save_all_tasks 无并发保护
- **文件**: `aios/core/orchestrator.py` → `dequeue()`, `mark_done()`, `mark_failed()`
- **描述**: 多个函数执行 load → modify → save 全量覆写，无锁
- **影响**: 多进程并发时任务状态丢失
- **建议**: 引入文件锁或迁移到数据库

### C-04: reactor.py 可执行任意 shell/python 命令
- **文件**: `aios/core/reactor.py` → `execute_action()`
- **描述**: playbook 中的 `target` 字段直接传给 `subprocess.run()`，无白名单校验
- **影响**: 配置文件被篡改时可执行任意命令
- **建议**: 添加命令白名单、playbook 文件完整性校验

---

## HIGH（应尽快修复）

### H-01: Python 解释器路径硬编码
- **文件**: `reactor.py`, `verifier.py`, `playbook.py`
- **描述**: `PYTHON = r"C:\Program Files\Python312\python.exe"` 硬编码在多个文件中
- **影响**: 无法在其他环境运行
- **建议**: 使用 `sys.executable` 或从 `config.yaml` 读取

### H-02: JSONL 文件无轮转/清理机制
- **文件**: `events/events.jsonl`, `data/reactions.jsonl`, `data/decisions.jsonl`, `data/pipeline_runs.jsonl`, `events/execution_log.jsonl` 等
- **描述**: 所有 JSONL 文件只追加不清理，`load_events()` 等函数每次全量读取
- **影响**: 长期运行后文件无限增长，读取性能持续下降
- **建议**: 实现按日期轮转 + 定期归档压缩

### H-03: bare except 泛滥（40+ 处）
- **文件**: 全局，尤其是 `engine.py`, `pipeline.py`, `evolution.py`, `sensors.py`
- **描述**: `except:` 或 `except Exception: pass/continue` 静默吞掉所有异常
- **影响**: 隐藏真实错误，调试困难
- **建议**: 捕获具体异常类型，至少记录日志

### H-04: sys.path.insert 操控泛滥
- **文件**: `reactor.py`, `executor.py`, `pipeline.py`, `decision_log.py`, `evolution.py`, `feedback_loop.py` 等 10+ 文件
- **描述**: 几乎每个可独立运行的模块都在文件头部 `sys.path.insert(0, ...)`
- **影响**: 导入路径不可预测，可能导致同名模块冲突
- **建议**: 使用 `setup.py`/`pyproject.toml` 正确安装包，或统一使用相对导入

### H-05: sensors.py 状态文件无原子写入
- **文件**: `aios/core/sensors.py` → `_save_state()`
- **描述**: 直接 `write_text()` 覆写状态文件，崩溃时文件可能被截断
- **影响**: 传感器状态丢失，可能导致重复告警或漏报
- **建议**: 使用 write-to-temp + atomic rename 模式

### H-06: dispatcher.py 的 unsubscribe 签名不匹配
- **文件**: `aios/core/dispatcher.py` → `dispatch()`
- **描述**: 调用 `bus.unsubscribe(handler)` 只传一个参数，但 `core/event_bus.py` 的 `unsubscribe` 需要两个参数 `(event_type, handler)`
- **影响**: 订阅清理失败，可能导致重复处理
- **建议**: 修正调用签名

---

## MEDIUM（建议修复）

### M-01: 类型注解覆盖率低
- **文件**: 全局，尤其是 `reactor.py`, `playbook.py`, `feedback_loop.py`
- **描述**: 大量函数缺少参数类型和返回值类型注解
- **影响**: IDE 无法提供准确补全，重构风险高
- **建议**: 逐步添加类型注解，优先覆盖核心模块的公开 API

### M-02: pipeline.py 的 stage_alerts 缩进异常
- **文件**: `aios/pipeline.py` → `stage_alerts()`
- **描述**: return 字典中 `"overdue"` 等键的缩进与前两个键不一致
- **影响**: 代码可读性差，可能掩盖逻辑错误
- **建议**: 统一缩进

### M-03: circuit_breaker.py 重复导入
- **文件**: `aios/core/circuit_breaker.py`
- **描述**: `import time` 和 `import json` 各出现两次
- **影响**: 代码冗余
- **建议**: 删除重复导入

### M-04: config.py 的 get_path 返回类型不准确
- **文件**: `aios/core/config.py` → `get_path()`
- **描述**: 标注返回 `Path`，实际可能返回 `None`
- **影响**: 调用方可能在 None 上调用 Path 方法导致 AttributeError
- **建议**: 改为 `Optional[Path]`

### M-05: app_alias.py 的 _T2S 映射表有重复
- **文件**: `aios/core/app_alias.py`
- **描述**: 繁简映射表后半部分是前半部分的复制粘贴
- **影响**: 浪费空间，后续维护容易引入错误
- **建议**: 去重，保留唯一映射

### M-06: model_router.py 和 model_router_v2.py 共存
- **文件**: `aios/core/model_router.py`, `aios/core/model_router_v2.py`
- **描述**: v1 和 v2 同时存在，v1 的 `route_model` 函数名与 v2 的便捷函数同名
- **影响**: 导入时可能混淆
- **建议**: 确认 v1 是否仍被使用，如否则移入 _deprecated

### M-07: reactor.py 的 _record_fuse_success 是空函数
- **文件**: `aios/core/reactor.py`
- **描述**: 函数体只有 `pass`，且从未被调用
- **影响**: 误导阅读者
- **建议**: 删除或实现

### M-08: scheduler.py 引用不存在的 EventType 属性
- **文件**: `aios/scheduler.py`
- **描述**: 引用 `EventType.RESOURCE_SPIKE`, `EventType.TASK_FAILED` 等，但这些在顶层 `event_bus.py` 的 EventType 中定义为不同的名称（如 `RESOURCE_SPIKE` vs `RESOURCE_CPU_SPIKE`）
- **影响**: 事件订阅可能无法匹配
- **建议**: 统一 EventType 常量

### M-09: 测试文件缺少 pytest 框架
- **文件**: `aios/tests/` 目录
- **描述**: 测试文件多为独立脚本，无法通过 `pytest` 统一运行
- **影响**: 无法集成 CI/CD，回归测试困难
- **建议**: 迁移到 pytest 框架

### M-10: verifier.py 的验证命令使用字符串拼接
- **文件**: `aios/core/verifier.py` → `VERIFY_RULES`
- **描述**: 路径直接拼接到 Python 代码字符串中
- **影响**: 路径含特殊字符时可能导致注入或语法错误
- **建议**: 使用参数化方式传递路径

---

## LOW（可选修复）

### L-01: _deprecated 目录未清理
- **文件**: `aios/agent_system/_deprecated/`
- **描述**: 5 个废弃文件仍保留在代码库中
- **建议**: 确认无引用后删除

### L-02: 配置常量分散在各模块
- **文件**: `reactor.py`, `sensors.py`, `executor.py` 等
- **描述**: 冷却时间、阈值等配置硬编码在各模块中
- **建议**: 统一到 `config.yaml`

### L-03: CLI 入口不统一
- **文件**: 多个模块的 `if __name__ == "__main__"` 块
- **描述**: 每个模块自带 CLI，参数解析方式不一致（有的用 argparse，有的用 sys.argv）
- **建议**: 统一使用 argparse 或 click

### L-04: dashboard/server.py 过长（812 行）
- **文件**: `aios/dashboard/server.py`
- **描述**: 单文件包含路由、数据聚合、WebSocket 管理、HTML 模板
- **建议**: 拆分为 routes.py, data.py, ws.py 等

### L-05: 日志输出不统一
- **描述**: 部分模块使用 `print()`，部分使用 `engine.emit()`，无标准 logging
- **建议**: 引入 Python 标准 `logging` 模块

### L-06: collaboration/orchestrator.py 与 core/orchestrator.py 命名冲突
- **文件**: 两个同名模块
- **描述**: `collaboration/orchestrator.py` 是多 Agent 编排器，`core/orchestrator.py` 是子任务队列
- **建议**: 重命名以区分职责，如 `core/task_queue.py`
