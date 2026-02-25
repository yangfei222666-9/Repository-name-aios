# tests/test_realistic_flow.py - 真实对话流程测试
"""
模拟完整的真实对话流程，验证自动切换。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\scripts')
from auto_model import should_switch, _save_state, AutoModelState

# 重置到 sonnet
state = AutoModelState(current_model="sonnet", turns_since_switch=999)
_save_state(state)

# 真实对话流程
conversation = [
    ("hi", "sonnet", "闲聊"),
    ("今天天气怎么样", "sonnet", "简单查询"),
    ("帮我重构autolearn的模糊匹配模块", "opus", "复杂任务开始"),
    ("具体要改哪些地方", "opus", "任务讨论"),
    ("好的开始吧", "opus", "任务确认"),
    ("这个报错是什么意思", "opus", "任务中遇到问题"),
    ("继续优化", "opus", "任务继续"),
    ("测试通过了吗", "opus", "任务检查"),
    ("好的谢谢", "sonnet", "任务完成"),
    ("查一下新山的餐厅", "sonnet", "新的简单任务"),
]

print("真实对话流程测试：\n")

passed = 0
failed = 0

for i, (msg, expected, desc) in enumerate(conversation, 1):
    result = should_switch(msg)
    actual = result["to"]
    
    if actual == expected:
        status = "✓"
        passed += 1
    else:
        status = "✗"
        failed += 1
    
    switch_str = f"→{actual}" if result["should_switch"] else f"={actual}"
    print(f"{status} 轮{i:2d}: {msg:30s} | {switch_str:8s} | {desc}")
    if actual != expected:
        print(f"        预期 {expected}, 原因: {result['reason']}")

print(f"\n结果: {passed}/{len(conversation)} 正确")

if failed > 0:
    print(f"\n误切率: {failed/len(conversation):.1%}")
else:
    print("\n✅ 完美")
