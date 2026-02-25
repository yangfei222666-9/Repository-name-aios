# tests/test_edge_cases.py - 边界样本测试
"""
测试容易误切的边界样本。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\scripts')
from auto_model import should_switch, _save_state, AutoModelState

# 重置到 sonnet
state = AutoModelState(current_model="sonnet", turns_since_switch=999)
_save_state(state)

edge_cases = [
    # (消息, 预期模型, 描述)
    ("帮我查一下新山的天气", "sonnet", "简单查询，不应切 opus"),
    ("写一个 hello world", "opus", "虽然简单但是写代码，应该 opus"),
    ("这个报错是什么意思", "sonnet", "单纯问问题，sonnet 够用"),
    ("帮我分析这个报错并修复", "opus", "分析+修复，需要 opus"),
    ("好的我知道了", "sonnet", "确认回复，sonnet"),
    ("继续", "sonnet", "单字指令，上下文不足，默认 sonnet"),
    ("优化一下性能", "opus", "优化任务，opus"),
    ("性能怎么样", "sonnet", "查询性能，sonnet"),
]

print("边界样本测试：\n")

issues = []

for msg, expected, desc in edge_cases:
    result = should_switch(msg)
    actual = result["to"]
    
    if actual != expected:
        issues.append({
            "msg": msg,
            "expected": expected,
            "actual": actual,
            "reason": result["reason"],
            "score": result["score"],
            "desc": desc,
        })
        status = "✗"
    else:
        status = "✓"
    
    print(f"{status} {msg:30s} | 预期:{expected:6s} 实际:{actual:6s} | {desc}")

print(f"\n结果: {len(edge_cases) - len(issues)}/{len(edge_cases)} 正确")

if issues:
    print(f"\n⚠️  {len(issues)} 个误切样本：")
    for issue in issues:
        print(f"  - {issue['msg']}")
        print(f"    预期 {issue['expected']}, 实际 {issue['actual']}")
        print(f"    原因: {issue['reason']} (score={issue['score']})")
        print(f"    说明: {issue['desc']}")
        print()
else:
    print("\n✅ 无误切")
