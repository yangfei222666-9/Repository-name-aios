#!/usr/bin/env python3
"""test_optimization.py - 优化后的补充测试

覆盖场景：
1. Evolution 安全护栏
2. API Server 输入验证
3. ScoreEngine 滑动窗口
4. Reactor 边界情况
5. Playbook 匹配边界
"""
import sys, json, time, tempfile, shutil
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

passed = 0
failed = 0


def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}")


# ══════════════════════════════════════════
# 1. Evolution 安全护栏测试
# ══════════════════════════════════════════
print("\n🛡️ Evolution 安全护栏测试:")

from agent_system.auto_evolution import AutoEvolution

# 使用临时目录避免污染真实数据
tmp_dir = Path(tempfile.mkdtemp())
try:
    auto_evo = AutoEvolution(data_dir=str(tmp_dir))

    # 初始状态应该安全
    safe, reason = auto_evo._check_safety_guardrails("test-agent")
    test("初始状态安全", safe)

    # 模拟超过每日上限
    evo_log = auto_evo.evolution_dir / "evolution_history.jsonl"
    evo_log.parent.mkdir(parents=True, exist_ok=True)
    with open(evo_log, "w", encoding="utf-8") as f:
        for i in range(auto_evo.MAX_EVOLUTIONS_PER_DAY):
            record = {
                "timestamp": int(time.time()) - 100 + i,
                "agent_id": "test-agent",
                "evolution_type": "increase_thinking",
                "changes": {},
                "reason": "test",
            }
            f.write(json.dumps(record) + "\n")

    safe, reason = auto_evo._check_safety_guardrails("test-agent")
    test("超过每日上限被阻止", not safe)
    test("原因包含上限信息", "上限" in reason)

    # 不同 agent 不受影响
    safe, reason = auto_evo._check_safety_guardrails("other-agent")
    test("其他 Agent 不受影响", safe)

    # 模拟回滚冷却
    with open(evo_log, "w", encoding="utf-8") as f:
        record = {
            "timestamp": int(time.time()) - 60,  # 1 分钟前回滚
            "agent_id": "rollback-agent",
            "evolution_type": "rollback",
            "changes": {},
            "reason": "test rollback",
        }
        f.write(json.dumps(record) + "\n")

    safe, reason = auto_evo._check_safety_guardrails("rollback-agent")
    test("回滚冷却期内被阻止", not safe)
    test("原因包含冷却信息", "冷却" in reason)

finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ══════════════════════════════════════════
# 2. ScoreEngine 滑动窗口测试
# ══════════════════════════════════════════
print("\n📊 ScoreEngine 滑动窗口测试:")

from core.toy_score_engine import ToyScoreEngine
from core.event import create_event, EventType
from core.event_bus import EventBus

bus = EventBus()
engine = ToyScoreEngine(bus=bus)
engine.start()

# 发送大量成功事件
for i in range(10):
    bus.emit(create_event("test.success", "test", duration_ms=50))

test("初始评分 > 0.8（全部成功）", engine.current_score > 0.8)

# 发送大量失败事件
for i in range(20):
    bus.emit(create_event("test.failed", "test", error="boom"))

test("大量失败后评分下降", engine.current_score < 0.8)

# 滑动窗口应该有数据
test("滑动窗口有记录", len(engine._recent_events) > 0)
test("滑动窗口不超过上限", len(engine._recent_events) <= engine.WINDOW_SIZE)


# ══════════════════════════════════════════
# 3. Playbook 匹配边界测试
# ══════════════════════════════════════════
print("\n📋 Playbook 匹配边界测试:")

from core.playbook import match_alert, load_playbooks

pbs = load_playbooks()

# 空告警
empty_alert = {}
for pb in pbs:
    test(f"空告警不匹配 {pb['id']}", not match_alert(pb, empty_alert))
    break  # 只测一个就够了

# severity 为 None
none_sev_alert = {"rule_id": "backup", "severity": None, "hit_count": 5}
backup_pb = [p for p in pbs if p["id"] == "backup_expired"][0]
test("severity=None 不匹配", not match_alert(backup_pb, none_sev_alert))

# 超长 message
long_msg_alert = {
    "rule_id": "event_severity",
    "severity": "CRIT",
    "message": "死循环" + "x" * 10000,
    "hit_count": 1,
}
loop_pb = [p for p in pbs if p["id"] == "loop_breaker_alert"][0]
test("超长 message 仍能匹配", match_alert(loop_pb, long_msg_alert))


# ══════════════════════════════════════════
# 4. Reactor 边界测试
# ══════════════════════════════════════════
print("\n⚡ Reactor 边界测试:")

from core.reactor import react, execute_action

# 空告警
results = react({}, mode="dry_run")
test("空告警返回 no_match", any(r.get("status") == "no_match" for r in results))

# 超长 message 不崩溃
long_alert = {
    "id": "long1",
    "rule_id": "backup",
    "severity": "WARN",
    "message": "A" * 100000,
    "hit_count": 5,
    "status": "OPEN",
}
results = react(long_alert, mode="dry_run")
test("超长 message 不崩溃", len(results) > 0)

# execute_action 空 target
ok, output = execute_action({"type": "shell", "target": "", "timeout": 5})
test("空 target 不崩溃", isinstance(ok, bool))

# execute_action 超大 timeout 被限制（应该不会真等那么久）
ok, output = execute_action(
    {"type": "shell", "target": "echo fast", "timeout": 999999}
)
test("大 timeout 仍能执行", ok)


# ══════════════════════════════════════════
# 5. Decision Log 边界测试
# ══════════════════════════════════════════
print("\n📝 Decision Log 边界测试:")

from core.decision_log import log_decision, get_decision, update_outcome

# 正常记录
did = log_decision(
    context="test_context",
    options=["a", "b"],
    chosen="a",
    reason="test",
    confidence=0.8,
)
test("log_decision 返回 UUID", len(did) == 36)

# 获取决策
d = get_decision(did)
test("get_decision 返回正确记录", d is not None and d["chosen"] == "a")

# confidence 边界
did2 = log_decision(
    context="test", options=[], chosen="x", reason="y", confidence=999.0
)
d2 = get_decision(did2)
test("confidence 被 clamp 到 1.0", d2["confidence"] == 1.0)

did3 = log_decision(
    context="test", options=[], chosen="x", reason="y", confidence=-5.0
)
d3 = get_decision(did3)
test("confidence 被 clamp 到 0.0", d3["confidence"] == 0.0)

# 无效 outcome
result = update_outcome(did, "invalid_status")
test("无效 outcome 返回 False", not result)

# 不存在的 ID
result = update_outcome("nonexistent-id-12345", "success")
test("不存在的 ID 返回 False", not result)


# ══════════════════════════════════════════
# 6. Verifier 边界测试
# ══════════════════════════════════════════
print("\n🔍 Verifier 边界测试:")

from core.verifier import verify_reaction

# 空 reaction
result = verify_reaction({})
test("空 reaction 不崩溃", result is not None)
test("空 reaction 默认通过", result["passed"])

# 不存在的 playbook_id
result = verify_reaction(
    {"reaction_id": "r1", "alert_id": "a1", "playbook_id": "nonexistent_xyz"}
)
test("不存在的 playbook 默认通过", result["passed"])


# ══════════════════════════════════════════
# 7. Evolution 分析边界测试
# ══════════════════════════════════════════
print("\n🧬 Evolution 分析边界测试:")

from agent_system.evolution import AgentEvolution

tmp_dir2 = Path(tempfile.mkdtemp())
try:
    evo = AgentEvolution(data_dir=str(tmp_dir2))

    # 无数据时分析
    analysis = evo.analyze_failures("ghost-agent", lookback_hours=24)
    test("无数据分析不崩溃", analysis["total_tasks"] == 0)
    test("无数据失败率为 0", analysis["failure_rate"] == 0.0)

    # 记录一些任务
    evo.log_task_execution("test-agent", "code", True, 1.0)
    evo.log_task_execution("test-agent", "code", False, 2.0, error_msg="timeout error")
    evo.log_task_execution("test-agent", "code", False, 3.0, error_msg="permission denied")

    analysis = evo.analyze_failures("test-agent", lookback_hours=24)
    test("分析返回正确总数", analysis["total_tasks"] == 3)
    test("分析返回正确失败数", analysis["failed_tasks"] == 2)
    test("失败率约 66%", abs(analysis["failure_rate"] - 2 / 3) < 0.01)

    # 建议生成
    test("生成了改进建议", len(analysis["suggestions"]) > 0)

    # 进化历史
    evo.apply_evolution(
        "test-agent",
        {"type": "increase_thinking", "changes": {"thinking": "high"}, "reason": "test"},
    )
    history = evo.get_evolution_history("test-agent")
    test("进化历史有记录", len(history) > 0)

    # 报告生成
    report = evo.generate_evolution_report("test-agent")
    test("报告包含标题", "进化报告" in report)
    test("报告包含失败率", "失败率" in report)

finally:
    shutil.rmtree(tmp_dir2, ignore_errors=True)


# ══════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════
print(f"\n{'='*50}")
total = passed + failed
print(f"📊 优化测试总计: {total} | ✅ {passed} | ❌ {failed}")
if failed == 0:
    print("🎉 全部通过!")
else:
    print(f"⚠️ {failed} 个失败")
    sys.exit(1)
