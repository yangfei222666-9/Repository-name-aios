# aios/core/test_executor.py - executor.py 契约测试
"""
4 个契约：
1. 去重命中 → NOOP_DEDUP
2. 预检 NOOP → NOOP_ALREADY_RUNNING
3. NON_RETRYABLE 不重试 → FAILED_NON_RETRYABLE
4. 重试耗尽终态 → FAILED_RETRYABLE（execute 本身不重试，由上层 job_queue 负责）
"""
import sys, time, json, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.executor import (
    execute, idempotency_guard, preflight_check, classify_error,
    SUCCESS, NOOP_DEDUP, NOOP_ALREADY_RUNNING,
    FAILED_RETRYABLE, FAILED_NON_RETRYABLE,
    DEDUP_STATE, EXEC_LOG,
)

PASS = 0
FAIL = 0


def assert_eq(name, actual, expected):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}: expected={expected}, got={actual}")


def setup():
    """清理测试状态"""
    DEDUP_STATE.unlink(missing_ok=True)
    # 不删 EXEC_LOG，追加模式无影响


def test_dedup_hit():
    """契约1: 同一 command_key 在窗口内第二次调用 → NOOP_DEDUP"""
    print("\n[契约1] 去重命中")
    setup()

    def ok_fn():
        return True, "done"

    r1 = execute("test_dedup", ok_fn, dedup_window=30)
    assert_eq("首次执行=SUCCESS", r1["terminal_state"], SUCCESS)

    r2 = execute("test_dedup", ok_fn, dedup_window=30)
    assert_eq("重复执行=NOOP_DEDUP", r2["terminal_state"], NOOP_DEDUP)

    # 不同 key 不受影响
    r3 = execute("test_dedup_other", ok_fn, dedup_window=30)
    assert_eq("不同key=SUCCESS", r3["terminal_state"], SUCCESS)


def test_preflight_noop():
    """契约2: 进程已存在 → NOOP_ALREADY_RUNNING"""
    print("\n[契约2] 预检 NOOP")
    setup()

    # explorer.exe 肯定在跑
    r = preflight_check("open_explorer", "explorer.exe")
    assert_eq("已运行进程=NOOP_ALREADY_RUNNING", r["terminal_state"], NOOP_ALREADY_RUNNING)

    # 不存在的进程 → None（通过）
    r2 = preflight_check("open_fake", "ThisDoesNotExist99.exe")
    assert_eq("不存在进程=None(通过)", r2, None)

    # execute 集成预检
    call_count = 0
    def counting_fn():
        nonlocal call_count
        call_count += 1
        return True, "ran"

    r3 = execute("preflight_test", counting_fn, dedup_window=1, process_name="explorer.exe")
    assert_eq("execute预检拦截=NOOP", r3["terminal_state"], NOOP_ALREADY_RUNNING)
    assert_eq("fn未被调用", call_count, 0)


def test_non_retryable():
    """契约3: NON_RETRYABLE 错误 → FAILED_NON_RETRYABLE，不应重试"""
    print("\n[契约3] NON_RETRYABLE 不重试")
    setup()

    # 错误分类
    assert_eq("WnsUniversalSDK=NON_RETRYABLE", classify_error("WnsUniversalSDK create failed"), "NON_RETRYABLE")
    assert_eq("FileNotFoundError=NON_RETRYABLE", classify_error("FileNotFoundError: no such file"), "NON_RETRYABLE")
    assert_eq("PermissionError=NON_RETRYABLE", classify_error("PermissionError: access denied"), "NON_RETRYABLE")
    assert_eq("timeout=RETRYABLE", classify_error("Connection timed out"), "RETRYABLE")
    assert_eq("空错误=RETRYABLE", classify_error(""), "RETRYABLE")

    # execute 集成
    def env_fail():
        return False, "WnsUniversalSDK initialization create failed"

    r = execute("non_retry_test", env_fail, dedup_window=1)
    assert_eq("execute终态=FAILED_NON_RETRYABLE", r["terminal_state"], FAILED_NON_RETRYABLE)
    assert_eq("reason=NON_RETRYABLE", r["reason_code"], "NON_RETRYABLE")


def test_retryable_terminal():
    """契约4: 可重试错误 → FAILED_RETRYABLE（execute 不自动重试，终态明确）"""
    print("\n[契约4] 重试耗尽终态")
    setup()

    def net_fail():
        return False, "Connection timed out after 30s"

    r = execute("retry_test", net_fail, dedup_window=1)
    assert_eq("execute终态=FAILED_RETRYABLE", r["terminal_state"], FAILED_RETRYABLE)
    assert_eq("reason=RETRYABLE", r["reason_code"], "RETRYABLE")

    # 异常也能正确分类
    def throw_fn():
        raise ConnectionError("network unreachable")

    time.sleep(1.1)  # 等去重窗口过期
    r2 = execute("retry_test", throw_fn, dedup_window=1)
    assert_eq("异常终态=FAILED_RETRYABLE", r2["terminal_state"], FAILED_RETRYABLE)


if __name__ == "__main__":
    test_dedup_hit()
    test_preflight_noop()
    test_non_retryable()
    test_retryable_terminal()

    print(f"\n{'='*40}")
    print(f"结果: {PASS} PASS / {FAIL} FAIL / {PASS+FAIL} TOTAL")
    if FAIL:
        sys.exit(1)
    else:
        print("ALL PASS")
