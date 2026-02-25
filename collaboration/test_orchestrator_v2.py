"""测试 Orchestrator v2：降级判定 + 失败策略 + SLA"""

import json
import shutil
import time
from pathlib import Path

# 清理测试数据
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "collaboration"
PLANS_FILE = DATA_DIR / "plans.json"
if PLANS_FILE.exists():
    PLANS_FILE.unlink()

from .orchestrator import Orchestrator, FailureType, RetryPolicy, ExecutionSLA

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}")


print("=" * 50)
print("Orchestrator v2 Tests")
print("=" * 50)

# ── Test 1: 失败分类 ──
print("\n[1] FailureType.classify")
test("502 → gateway_502", FailureType.classify("502 Bad Gateway") == "gateway_502")
test("timeout → timeout", FailureType.classify("Request timed out") == "timeout")
test("429 → rate_limit", FailureType.classify("429 Too Many Requests") == "rate_limit")
test("json → parse_error", FailureType.classify("json decode error") == "parse_error")
test("unknown → unknown", FailureType.classify("something weird") == "unknown")

# ── Test 2: 重试策略 ──
print("\n[2] RetryPolicy")
rp = RetryPolicy(base_delay=2.0, backoff_factor=2.0, max_delay=30.0)
test("attempt 0 delay = 2s", rp.delay_for_attempt(0) == 2.0)
test("attempt 1 delay = 4s", rp.delay_for_attempt(1) == 4.0)
test("attempt 2 delay = 8s", rp.delay_for_attempt(2) == 8.0)
test("attempt 5 delay capped at 30s", rp.delay_for_attempt(5) == 30.0)

# ── Test 3: 全部成功 ──
print("\n[3] 全部成功场景")
orch = Orchestrator()
plan = orch.create_plan("test_all_ok", "测试任务", [
    {"id": "t1", "description": "代码分析", "role": "coder"},
    {"id": "t2", "description": "代码审查", "role": "reviewer"},
    {"id": "t3", "description": "研究对比", "role": "researcher"},
], sla={"required_roles": ["coder", "reviewer"], "max_failures": 1, "total_timeout": 180})

orch.mark_spawned("test_all_ok", "t1", "collab_t1")
orch.mark_spawned("test_all_ok", "t2", "collab_t2")
orch.mark_spawned("test_all_ok", "t3", "collab_t3")
orch.mark_done("test_all_ok", "t1", "分析结果...")
orch.mark_done("test_all_ok", "t2", "审查结果...")
orch.mark_done("test_all_ok", "t3", "研究结果...")

v = orch.evaluate("test_all_ok")
test("verdict = done", v["verdict"] == "done")
test("confidence = 1.0", v["confidence"] == 1.0)
test("degraded = False", v["degraded"] == False)
test("no failed agents", v["failed_agents"] == [])

p = orch.get_plan("test_all_ok")
test("plan status = done", p.status == "done")

# ── Test 4: 降级交付（1个失败，在容忍范围内）──
print("\n[4] 降级交付场景")
# 重新创建
if PLANS_FILE.exists():
    PLANS_FILE.unlink()
orch2 = Orchestrator()
plan2 = orch2.create_plan("test_degraded", "降级测试", [
    {"id": "t1", "description": "代码分析", "role": "coder"},
    {"id": "t2", "description": "代码审查", "role": "reviewer"},
    {"id": "t3", "description": "研究对比", "role": "researcher"},
], sla={"required_roles": ["coder", "reviewer"], "max_failures": 1, "total_timeout": 180})

orch2.mark_spawned("test_degraded", "t1", "collab_t1")
orch2.mark_spawned("test_degraded", "t2", "collab_t2")
orch2.mark_spawned("test_degraded", "t3", "collab_t3")
orch2.mark_done("test_degraded", "t1", "分析结果...")
orch2.mark_done("test_degraded", "t2", "审查结果...")

# researcher 失败 4 次（3次重试 + 最终失败）
for i in range(4):
    result = orch2.mark_failed("test_degraded", "t3", "502 Bad Gateway error")

test("最终 action = degrade", result["action"] == "degrade")
test("failure_type = gateway_502", result["failure_type"] == "gateway_502")

v2 = orch2.evaluate("test_degraded")
test("verdict = degraded", v2["verdict"] == "degraded")
test("degraded = True", v2["degraded"] == True)
test("confidence < 1.0", v2["confidence"] < 1.0)
test("confidence >= 0.3", v2["confidence"] >= 0.3)
test("failed_agents includes t3", "t3" in v2["failed_agents"])

p2 = orch2.get_plan("test_degraded")
test("plan status = degraded", p2.status == "degraded")
test("plan.degraded = True", p2.degraded == True)

# ── Test 5: SLA 中止（必需角色失败）──
print("\n[5] SLA 中止场景")
if PLANS_FILE.exists():
    PLANS_FILE.unlink()
orch3 = Orchestrator()
plan3 = orch3.create_plan("test_abort", "中止测试", [
    {"id": "t1", "description": "代码分析", "role": "coder"},
    {"id": "t2", "description": "代码审查", "role": "reviewer"},
], sla={"required_roles": ["coder", "reviewer"], "max_failures": 0, "total_timeout": 180})

orch3.mark_spawned("test_abort", "t1", "collab_t1")
orch3.mark_spawned("test_abort", "t2", "collab_t2")
orch3.mark_done("test_abort", "t1", "分析结果...")

# reviewer（必需角色）失败
for i in range(4):
    orch3.mark_failed("test_abort", "t2", "timeout error")

v3 = orch3.evaluate("test_abort")
test("verdict = abort", v3["verdict"] == "abort")
test("reason mentions 必需角色", "必需" in v3["reason"] or "失败" in v3["reason"])

p3 = orch3.get_plan("test_abort")
test("plan status = failed", p3.status == "failed")

# ── Test 6: 重试机制 ──
print("\n[6] 重试机制")
if PLANS_FILE.exists():
    PLANS_FILE.unlink()
orch4 = Orchestrator()
plan4 = orch4.create_plan("test_retry", "重试测试", [
    {"id": "t1", "description": "会失败的任务", "role": "researcher"},
])

orch4.mark_spawned("test_retry", "t1", "collab_t1")

# 第一次失败 → 应该重试
r1 = orch4.mark_failed("test_retry", "t1", "502 Bad Gateway")
test("第1次失败 → retry", r1["action"] == "retry")
test("retry delay > 0", r1["retry_delay"] > 0)

# 任务应该回到 pending
st = [s for s in orch4.get_plan("test_retry").subtasks if s["id"] == "t1"][0]
test("status 回到 pending", st["status"] == "pending")

# 第二次失败
orch4.mark_spawned("test_retry", "t1", "collab_t1")
r2 = orch4.mark_failed("test_retry", "t1", "502 Bad Gateway")
test("第2次失败 → retry", r2["action"] == "retry")
test("delay 递增", r2["retry_delay"] > r1["retry_delay"])

# 第三次失败
orch4.mark_spawned("test_retry", "t1", "collab_t1")
r3 = orch4.mark_failed("test_retry", "t1", "502 Bad Gateway")
test("第3次失败 → retry", r3["action"] == "retry")

# 第四次失败 → 耗尽
orch4.mark_spawned("test_retry", "t1", "collab_t1")
r4 = orch4.mark_failed("test_retry", "t1", "502 Bad Gateway")
test("第4次失败 → degrade", r4["action"] == "degrade")

# ── Test 7: 降级报告生成 ──
print("\n[7] 降级报告")
if PLANS_FILE.exists():
    PLANS_FILE.unlink()
orch5 = Orchestrator()
orch5.create_plan("test_report", "报告测试", [
    {"id": "t1", "description": "成功任务", "role": "coder"},
    {"id": "t2", "description": "失败任务", "role": "researcher"},
], sla={"required_roles": ["coder"], "max_failures": 1, "total_timeout": 180})

orch5.mark_spawned("test_report", "t1", "c_t1")
orch5.mark_spawned("test_report", "t2", "c_t2")
orch5.mark_done("test_report", "t1", "成功的结果")
for i in range(4):
    orch5.mark_failed("test_report", "t2", "502 Bad Gateway from API")

report = orch5.build_report("test_report")
test("报告包含降级标记", "降级" in report or "⚠️" in report)
test("报告包含失败类型", "gateway_502" in report)
test("报告包含重试次数", "重试" in report)
test("报告包含 SLA 摘要", "SLA" in report)
test("报告包含成功结果", "成功的结果" in report)

# ── 汇总 ──
print(f"\n{'=' * 50}")
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
print(f"{'=' * 50}")

if failed:
    exit(1)
