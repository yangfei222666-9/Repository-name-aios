import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\scripts')
from auto_model import should_switch, _load_state

# 先跑几条简单消息让 turns_since_switch 增加
for i in range(3):
    r = should_switch('好的')
    state = _load_state()
    print(f"轮{i+1}: 保持 {r['from']}, 已驻留 {state.turns_since_switch} 轮")

# 现在应该可以切了
r = should_switch('帮我重构autolearn的模糊匹配')
print(f"\n复杂任务: {r['from']} → {r['to']} (切换={r['should_switch']})")
print(f"原因: {r['reason']}")
