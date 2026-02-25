#!/usr/bin/env python3
# aios/core/test_action_engine.py - Action Engine 契约测试
"""
测试覆盖：
1. 幂等键生成 + 去重
2. 入队 + 状态流转
3. 风险分级（low/medium/high）
4. 护栏（限额/冷却/熔断/预算压力）
5. Executor Registry
6. CLI 可运行
"""
import sys, json, time, os, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0

# 修复 Windows 控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def assert_eq(name, actual, expected):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}: expected={expected!r}, got={actual!r}")


def assert_true(name, value):
    global PASS, FAIL
    if value:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}: expected truthy, got {value!r}")


def assert_in(name, needle, haystack):
    global PASS, FAIL
    if needle in haystack:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}: {needle!r} not in {haystack!r}")


# ── Setup / Teardown ──

from core.action_engine import (
    action_hash, enqueue, run_queue, get_status, get_history,
    classify_risk, check_guardrails, ingest_pending_actions,
    get_registry, ActionResult, ShellExecutor, HttpExecutor, ToolExecutor,
    QUEUE_FILE, PENDING_ACTIONS_FILE, DATA_DIR,
    STATUS_QUEUED, STATUS_SUCCEEDED, STATUS_FAILED, STATUS_SKIPPED,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH,
    _load_queue, _save_queue,
)


def setup():
    """清理测试状态"""
    QUEUE_FILE.unlink(missing_ok=True)
    PENDING_ACTIONS_FILE.unlink(missing_ok=True)


# ── Test 1: 幂等键 ──

def test_idempotent_hash():
    print("\n[Test 1] 幂等键")
    h1 = action_hash("shell", "/tmp", {"command": "ls"})
    h2 = action_hash("shell", "/tmp", {"command": "ls"})
    h3 = action_hash("shell", "/tmp", {"command": "pwd"})

    assert_eq("same input = same hash", h1, h2)
    assert_eq("hash length = 16", len(h1), 16)
    assert_true("different params = different hash", h1 != h3)


# ── Test 2: 入队 + 去重 ──

def test_enqueue_dedup():
    print("\n[Test 2] 入队 + 去重")
    setup()

    action = {"type": "review_change", "detail": "test.py", "priority": "normal"}
    r1 = enqueue(action)
    assert_true("首次入队成功", r1 is not None)
    assert_eq("状态=queued", r1["status"], STATUS_QUEUED)

    r2 = enqueue(action)
    assert_eq("重复入队=None", r2, None)

    # 不同 action 可以入队
    action2 = {"type": "review_change", "detail": "other.py", "priority": "normal"}
    r3 = enqueue(action2)
    assert_true("不同 action 入队成功", r3 is not None)

    status = get_status()
    assert_eq("队列总数=2", status["total"], 2)
    assert_eq("queued=2", status["queued"], 2)


# ── Test 3: 风险分级 ──

def test_risk_classification():
    print("\n[Test 3] 风险分级")

    assert_eq("explicit low", classify_risk({"risk": "low"}), RISK_LOW)
    assert_eq("explicit high", classify_risk({"risk": "high"}), RISK_HIGH)
    assert_eq("priority high → high risk", classify_risk({"priority": "high"}), RISK_HIGH)
    assert_eq("priority normal → medium risk", classify_risk({"priority": "normal"}), RISK_MEDIUM)
    assert_eq("priority low → low risk", classify_risk({"priority": "low"}), RISK_LOW)


# ── Test 4: 高风险跳过 ──

def test_high_risk_skip():
    print("\n[Test 4] 高风险跳过")
    setup()

    action = {"type": "dangerous_op", "priority": "high", "risk": "high"}
    enqueue(action)

    processed = run_queue()
    assert_eq("处理数=1", len(processed), 1)
    assert_eq("状态=skipped", processed[0]["status"], STATUS_SKIPPED)
    assert_eq("原因=needs_approval", processed[0]["skip_reason"], "needs_approval")


# ── Test 5: Executor Registry ──

def test_executor_registry():
    print("\n[Test 5] Executor Registry")

    registry = get_registry()
    assert_in("shell registered", "shell", registry.names)
    assert_in("http registered", "http", registry.names)
    assert_in("tool registered", "tool", registry.names)

    # 注册自定义 tool
    def my_tool(params):
        return True, "custom tool ok"

    registry.register_tool("my_tool", my_tool)

    # 通过 tool executor 执行
    tool_exec = registry.get("tool")
    result = tool_exec.execute({"params": {"tool": "my_tool"}})
    assert_true("custom tool ok", result.ok)
    assert_in("result contains ok", "ok", result.detail)


# ── Test 6: Shell Executor ──

def test_shell_executor():
    print("\n[Test 6] Shell Executor")
    setup()

    # 入队一个 shell action
    action = {
        "type": "shell",
        "detail": "echo test",
        "params": {"command": "echo hello_action_engine"},
        "priority": "low",
        "risk": "low",
    }
    r = enqueue(action)
    assert_true("入队成功", r is not None)

    processed = run_queue()
    assert_eq("处理数=1", len(processed), 1)
    assert_eq("状态=succeeded", processed[0]["status"], STATUS_SUCCEEDED)
    assert_in("result contains hello", "hello_action_engine", processed[0]["result"])


# ── Test 7: 护栏 - 冷却 ──

def test_cooldown_guardrail():
    print("\n[Test 7] 护栏 - 冷却")
    setup()

    # 先执行一个 action
    action = {
        "type": "shell", "detail": "echo cd_test",
        "params": {"command": "echo cooldown_test"},
        "priority": "low", "risk": "low",
    }
    enqueue(action)
    run_queue()

    # 同 hash 的 action 在冷却期内应被跳过
    # 需要先让之前的 action 进入终态，然后入队同 hash 的新 action
    # 由于幂等去重，已终结的 action 不阻止入队
    r2 = enqueue(action)
    assert_true("冷却期内可入队（因为前一个已终结）", r2 is not None)

    processed = run_queue()
    assert_eq("处理数=1", len(processed), 1)
    assert_eq("状态=skipped", processed[0]["status"], STATUS_SKIPPED)
    assert_in("原因含 cooldown", "cooldown", processed[0]["skip_reason"])


# ── Test 8: 从 dispatcher 导入 ──

def test_ingest_from_dispatcher():
    print("\n[Test 8] 从 dispatcher 导入")
    setup()

    # 模拟 dispatcher 写入 pending_actions.jsonl
    PENDING_ACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    actions = [
        {"type": "review_change", "priority": "normal", "summary": "test file changed", "detail": "a.py", "trace_id": "abc123"},
        {"type": "process_alert", "priority": "high", "summary": "process stopped", "detail": "node.exe", "trace_id": "abc123"},
    ]
    with PENDING_ACTIONS_FILE.open("w", encoding="utf-8") as f:
        for a in actions:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    count = ingest_pending_actions()
    assert_eq("导入数=2", count, 2)

    status = get_status()
    assert_eq("队列总数=2", status["total"], 2)

    # pending file 应被清空
    content = PENDING_ACTIONS_FILE.read_text(encoding="utf-8").strip()
    assert_eq("pending file 已清空", content, "")


# ── Test 9: 状态查询 ──

def test_status_and_history():
    print("\n[Test 9] 状态 + 历史查询")
    setup()

    # 入队并执行
    enqueue({"type": "shell", "params": {"command": "echo status_test"}, "priority": "low", "risk": "low"})
    run_queue()

    status = get_status()
    assert_eq("succeeded=1", status["succeeded"], 1)

    history = get_history()
    assert_eq("历史数=1", len(history), 1)
    assert_eq("历史状态=succeeded", history[0]["status"], STATUS_SUCCEEDED)


# ── Test 10: 熔断 ──

def test_circuit_breaker():
    print("\n[Test 10] 熔断")
    setup()

    # 制造 3 个连续失败
    for i in range(3):
        enqueue({
            "type": "shell",
            "detail": f"fail_{i}",
            "params": {"command": "exit 1"},
            "priority": "low", "risk": "low",
        })
    run_queue(limit=3)

    # 第 4 个应被熔断
    enqueue({
        "type": "shell", "detail": "after_breaker",
        "params": {"command": "echo should_not_run"},
        "priority": "low", "risk": "low",
    })
    processed = run_queue()
    assert_eq("处理数=1", len(processed), 1)
    assert_eq("状态=skipped", processed[0]["status"], STATUS_SKIPPED)
    assert_in("原因含 circuit_breaker", "circuit_breaker", processed[0]["skip_reason"])


# ── Run All ──

if __name__ == "__main__":
    test_idempotent_hash()
    test_enqueue_dedup()
    test_risk_classification()
    test_high_risk_skip()
    test_executor_registry()
    test_shell_executor()
    test_cooldown_guardrail()
    test_ingest_from_dispatcher()
    test_status_and_history()
    test_circuit_breaker()

    print(f"\n{'='*40}")
    print(f"结果: {PASS} PASS / {FAIL} FAIL / {PASS+FAIL} TOTAL")
    if FAIL:
        sys.exit(1)
    else:
        print("ALL PASS ✅")
