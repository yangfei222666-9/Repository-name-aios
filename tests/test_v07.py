#!/usr/bin/env python3
"""test_v07.py - AIOS v0.7 自适应学习层测试"""
import sys, json
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

# ── Feedback Loop ──
print("\n🔄 Feedback Loop 测试:")

from core.feedback_loop import analyze_playbook_patterns, generate_suggestions

patterns = analyze_playbook_patterns(168)
test("analyze 返回字典", isinstance(patterns, dict))
test("backup_expired 有数据", 'backup_expired' in patterns)

bp = patterns.get('backup_expired', {})
test("backup 成功率 > 0", bp.get('success_rate', 0) > 0)
test("backup 有 total 字段", 'total' in bp)
test("backup 有 verify_rate 字段", 'verify_rate' in bp)

suggestions = generate_suggestions(168)
test("suggest 返回列表", isinstance(suggestions, list))
# disk_full 应该有建议（成功率 0%）
disk_suggestions = [s for s in suggestions if s.get('playbook_id') == 'disk_full']
test("disk_full 有优化建议", len(disk_suggestions) > 0)

# ── Policy Learner ──
print("\n🧠 Policy Learner 测试:")

from core.policy_learner import learn_and_adjust, generate_draft_playbook, rollback_last_change, _load_pb_stats

changes = learn_and_adjust()
test("learn 返回列表", isinstance(changes, list))

# 生成 draft playbook
draft = generate_draft_playbook("test_rule", "WARN", "测试模式")
test("draft 生成成功", draft is not None)
test("draft 默认禁用", draft.get('enabled') == False)
test("draft 需确认", draft.get('require_confirm') == True)
test("draft 有 id", 'id' in draft)

# 回滚测试
last, msg = rollback_last_change()
test("回滚返回消息", msg is not None)

# ── Evolution v2 ──
print("\n📈 Evolution v2 测试:")

from core.evolution import compute_evolution_v2, compute_reactor_score, get_trend

reactor = compute_reactor_score()
test("reactor_score 返回字典", isinstance(reactor, dict))
test("有 auto_fix_rate", 'auto_fix_rate' in reactor)
test("有 false_positive_rate", 'false_positive_rate' in reactor)
test("有 auto_close_rate", 'auto_close_rate' in reactor)
test("reactor_score 在 [0,1]", 0 <= reactor['reactor_score'] <= 1)

result = compute_evolution_v2()
test("evolution_v2 返回字典", isinstance(result, dict))
test("有 evolution_v2 分数", 'evolution_v2' in result)
test("有 grade", result.get('grade') in ('healthy', 'degraded', 'critical'))
test("有 base_score", 'base_score' in result)
test("有 reactor_score", 'reactor_score' in result)
test("v2 分数在 [0,1]", 0 <= result['evolution_v2'] <= 1)

trend = get_trend(7)
test("trend 返回列表", isinstance(trend, list))
test("trend 有数据", len(trend) > 0)

# ── 汇总 ──
print(f"\n{'='*40}")
total = passed + failed
print(f"📊 总计: {total} | ✅ {passed} | ❌ {failed}")
if failed == 0:
    print("🎉 全部通过!")
else:
    print(f"⚠️ {failed} 个失败")
    sys.exit(1)
