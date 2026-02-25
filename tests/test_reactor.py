#!/usr/bin/env python3
"""test_reactor.py - Reactor v0.6 集成测试"""
import sys, json, tempfile, shutil
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT.parent / "scripts"))

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

# ── Test Playbook ──
print("\n📋 Playbook 测试:")

from core.playbook import load_playbooks, match_alert, find_matching_playbooks, check_cooldown

pbs = load_playbooks()
test("加载剧本 >= 4", len(pbs) >= 4)

# 匹配测试
backup_alert = {
    "id": "test1", "rule_id": "backup", "severity": "WARN",
    "message": "备份过期", "hit_count": 3, "status": "OPEN"
}
backup_pb = [p for p in pbs if p['id'] == 'backup_expired'][0]
test("backup 告警匹配 backup_expired 剧本", match_alert(backup_pb, backup_alert))

# 不匹配测试
wrong_alert = {
    "id": "test2", "rule_id": "unknown", "severity": "INFO",
    "message": "nothing", "hit_count": 1, "status": "OPEN"
}
test("无关告警不匹配 backup_expired", not match_alert(backup_pb, wrong_alert))

# hit_count 不足
low_hit = {
    "id": "test3", "rule_id": "backup", "severity": "WARN",
    "message": "备份过期", "hit_count": 1, "status": "OPEN"
}
test("hit_count=1 不满足 min_hit_count=2", not match_alert(backup_pb, low_hit))

# severity 不匹配
info_alert = {
    "id": "test4", "rule_id": "backup", "severity": "INFO",
    "message": "备份过期", "hit_count": 5, "status": "OPEN"
}
test("INFO severity 不匹配 [WARN,CRIT]", not match_alert(backup_pb, info_alert))

# message_contains 测试
loop_pb = [p for p in pbs if p['id'] == 'loop_breaker_alert'][0]
loop_alert = {
    "id": "test5", "rule_id": "event_severity", "severity": "CRIT",
    "message": "死循环检测异常: 快速重复失败", "hit_count": 1, "status": "OPEN"
}
test("死循环告警匹配 loop_breaker 剧本", match_alert(loop_pb, loop_alert))

no_loop_alert = {
    "id": "test6", "rule_id": "event_severity", "severity": "CRIT",
    "message": "其他严重错误", "hit_count": 1, "status": "OPEN"
}
test("非死循环 CRIT 不匹配 loop_breaker", not match_alert(loop_pb, no_loop_alert))

# disabled 测试
disabled_pb = dict(backup_pb)
disabled_pb['enabled'] = False
test("disabled 剧本不匹配", not match_alert(disabled_pb, backup_alert))

# ── Test Reactor ──
print("\n⚡ Reactor 测试:")

from core.reactor import react, execute_action
from core.reactor import _save_fuse as _reset_fuse_for_test

# dry_run 模式
results = react(backup_alert, mode="dry_run")
test("dry_run 返回结果", len(results) > 0)
test("dry_run 状态正确", any(r.get('mode') == 'dry_run' or r.get('status') == 'no_match' for r in results))

# execute_action dry_run
ok, output = execute_action({"type": "shell", "target": "echo hello"}, dry_run=True)
test("execute_action dry_run 成功", ok)
test("execute_action dry_run 输出包含 DRY_RUN", "DRY_RUN" in output)

# execute_action 真实执行
ok, output = execute_action({"type": "shell", "target": "echo test_ok", "timeout": 10})
test("execute_action shell echo 成功", ok)
test("execute_action shell echo 输出正确", "test_ok" in output)

# execute_action 失败
ok, output = execute_action({"type": "shell", "target": "exit 1", "timeout": 5})
test("execute_action 失败返回 False", not ok)

# execute_action 超时
ok, output = execute_action({"type": "shell", "target": "Start-Sleep 10", "timeout": 2})
test("execute_action 超时处理", not ok and "TIMEOUT" in output)

# unknown type
ok, output = execute_action({"type": "magic", "target": "abracadabra"})
test("未知 action type 返回失败", not ok)

# confirm 模式 - CRIT + medium risk
# 先重置熔断状态，确保测试独立
_reset_fuse_for_test({"failures": [], "tripped": False, "tripped_at": None})
crit_alert = {
    "id": "testC", "rule_id": "system_health", "severity": "CRIT",
    "message": "磁盘空间不足", "hit_count": 1, "status": "OPEN"
}
results = react(crit_alert, mode="auto")
has_pending = any(r.get('status') == 'pending_confirm' for r in results)
has_no_match = len(results) == 0 or any(r.get('status') == 'no_match' for r in results)
test("CRIT+medium risk 需确认或无匹配", has_pending or has_no_match)

# ── Test Verifier ──
print("\n🔍 Verifier 测试:")

from core.verifier import verify_reaction, _make_result

# 无验证规则
fake_reaction = {"reaction_id": "fake1", "alert_id": "a1", "playbook_id": "nonexistent"}
result = verify_reaction(fake_reaction)
test("无验证规则默认通过", result['passed'])
test("验证方法为 no_verify_rule", result['verify_method'] == 'no_verify_rule')

# _make_result
r = _make_result(fake_reaction, True, "test", "test detail")
test("_make_result 结构正确", r['passed'] and r['verify_method'] == 'test')

# ── Test 全局熔断 ──
print("\n🔒 全局熔断测试:")

from core.reactor import _load_fuse, _save_fuse, _record_fuse_failure, is_fuse_tripped, FUSE_FAIL_THRESHOLD

# 重置熔断状态
_save_fuse({"failures": [], "tripped": False, "tripped_at": None})
test("初始状态未熔断", not is_fuse_tripped())

# 累积失败
for i in range(FUSE_FAIL_THRESHOLD):
    _record_fuse_failure()
test(f"{FUSE_FAIL_THRESHOLD} 次失败后熔断触发", is_fuse_tripped())

# 重置
_save_fuse({"failures": [], "tripped": False, "tripped_at": None})
test("重置后恢复", not is_fuse_tripped())

# ── Test 剧本成功率 ──
print("\n📊 剧本成功率测试:")

from core.reactor import record_pb_outcome, get_pb_success_rate, get_dynamic_cooldown, _save_pb_stats

# 重置
_save_pb_stats({})

record_pb_outcome("test_pb", True)
record_pb_outcome("test_pb", True)
record_pb_outcome("test_pb", False)
test("成功率 2/3 ≈ 66%", abs(get_pb_success_rate("test_pb") - 2/3) < 0.01)

# 动态冷却
cd = get_dynamic_cooldown("test_pb", 60)
test("成功率 66% > 50% 冷却不变", cd == 60)

record_pb_outcome("test_pb", False)
record_pb_outcome("test_pb", False)
# 现在 2/5 = 40%
cd = get_dynamic_cooldown("test_pb", 60)
test("成功率 40% < 50% 冷却翻倍", cd == 120)

# 清理测试数据
_save_pb_stats({})
_save_fuse({"failures": [], "tripped": False, "tripped_at": None})

# ── Test Dashboard 指标 ──
print("\n📈 Dashboard 指标测试:")

from core.reactor import dashboard_metrics

m = dashboard_metrics()
test("metrics 返回字典", isinstance(m, dict))
test("metrics 包含 fuse_status", 'fuse_status' in m)
test("metrics 包含 auto_exec_rate", 'auto_exec_rate' in m)

# ── 汇总 ──
print(f"\n{'='*40}")
total = passed + failed
print(f"📊 总计: {total} | ✅ {passed} | ❌ {failed}")
if failed == 0:
    print("🎉 全部通过!")
else:
    print(f"⚠️ {failed} 个失败")
    sys.exit(1)
