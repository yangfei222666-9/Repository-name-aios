#!/usr/bin/env python3
"""test_pipeline.py - Pipeline 集成测试"""
import sys, json
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

print("\n🔄 Pipeline 集成测试:")

from pipeline import run_pipeline, format_report

# 执行 pipeline
report = run_pipeline()

test("pipeline 返回字典", isinstance(report, dict))
test("有 ts", 'ts' in report)
test("有 stages", 'stages' in report)
test("有 total_ms", 'total_ms' in report)
test("7 个阶段", len(report['stages']) == 7)

# 每个阶段都有结果
for name in ['sensors', 'alerts', 'reactor', 'verifier', 'convergence', 'feedback', 'evolution']:
    s = report['stages'].get(name, {})
    test(f"{name} 有 ok 字段", 'ok' in s)
    test(f"{name} 有 result", 'result' in s)

# evolution 结果
evo = report['stages'].get('evolution', {}).get('result', {})
test("evolution 有 v2_score", 'v2_score' in evo)
test("evolution 有 grade", evo.get('grade') in ('healthy', 'degraded', 'critical'))

# 格式化
default_fmt = format_report(report, "default")
test("default 格式非空", len(default_fmt) > 0)
test("default 包含 Pipeline", "Pipeline" in default_fmt)

tg_fmt = format_report(report, "telegram")
test("telegram 格式非空", len(tg_fmt) > 0)
test("telegram 包含 Evolution", "Evolution" in tg_fmt)

# 性能
test(f"总耗时 < 30s ({report['total_ms']}ms)", report['total_ms'] < 30000)

# 错误数
test(f"错误数 <= 1 ({len(report['errors'])})", len(report['errors']) <= 1)

# ── 汇总 ──
print(f"\n{'='*40}")
total = passed + failed
print(f"📊 总计: {total} | ✅ {passed} | ❌ {failed}")
if failed == 0:
    print("🎉 全部通过!")
else:
    print(f"⚠️ {failed} 个失败")
    sys.exit(1)
