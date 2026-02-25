# tests/test_auto_switch_real.py - 自动模型切换实战测试
"""
模拟真实对话场景，验证自动切换逻辑。

测试场景：
1. 闲聊 → sonnet
2. 复杂任务开始 → 切 opus
3. 任务进行中 → 保持 opus
4. 任务完成 → 切回 sonnet
5. 简单查询 → 保持 sonnet
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\scripts')
from auto_model import should_switch, _load_state, _save_state, AutoModelState

# 重置状态
state = AutoModelState(current_model="sonnet", turns_since_switch=999)
_save_state(state)

scenarios = [
    ("hi", "sonnet", "闲聊保持 sonnet"),
    ("帮我重构autolearn的模糊匹配", "opus", "复杂任务切 opus"),
    ("继续优化性能", "opus", "任务中保持 opus"),
    ("测试通过了", "opus", "任务中保持 opus"),
    ("还有别的要改吗", "opus", "任务中保持 opus（第4轮）"),
    ("好的谢谢", "sonnet", "任务完成切回 sonnet（已满3轮）"),
    ("今天天气怎么样", "sonnet", "简单查询保持 sonnet"),
]

print("场景测试：")
print()

passed = 0
failed = 0

for i, (msg, expected, desc) in enumerate(scenarios, 1):
    result = should_switch(msg)
    actual = result["to"]
    status = "✓" if actual == expected else "✗"
    
    if actual == expected:
        passed += 1
    else:
        failed += 1
    
    switch_str = f"→{actual}" if result["should_switch"] else f"保持{actual}"
    print(f"{status} 场景{i}: {desc}")
    print(f"   消息: {msg}")
    print(f"   预期: {expected}, 实际: {switch_str}")
    print(f"   原因: {result['reason']}")
    print()

print(f"结果: {passed}/{len(scenarios)} 通过")

if failed > 0:
    print(f"\n⚠️  {failed} 个场景失败，需要调整规则")
    sys.exit(1)
else:
    print("\n✅ 所有场景通过")
