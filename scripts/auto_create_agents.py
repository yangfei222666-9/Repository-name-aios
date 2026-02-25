import sys
sys.path.insert(0, 'aios/agent_system')
from meta_agent import MetaAgent

meta = MetaAgent()
gaps = meta.detect_gaps()

# 只处理高优先级的缺口（频繁失败）
high_priority = [g for g in gaps if g.get('severity') == 'medium']

print(f'高优先级缺口: {len(high_priority)}')
print()

created_suggestions = []

for gap in high_priority:
    agent_type = gap.get('agent_type', '?')
    desc = gap.get('description', '?')
    print(f'处理缺口: {agent_type} ({desc})')
    
    # 设计 Agent
    design = meta.design_agent(gap)
    if not design:
        print(f'  ✗ 设计失败')
        continue
    
    # 沙盒测试
    test_result = meta.sandbox_test(design)
    print(f'  沙盒测试: {test_result.get("passed", False)}')
    
    # 提交审批
    suggestion = meta.submit_for_approval(design, test_result)
    sug_id = suggestion.get('id', '?')
    print(f'  ✓ 已提交审批: {sug_id}')
    created_suggestions.append(sug_id)
    print()

print(f'共创建 {len(created_suggestions)} 个建议，等待审批')
print()
print('查看待审批:')
print('  python aios/agent_system/meta_agent.py pending')
print()
print('批准所有:')
for sug_id in created_suggestions:
    print(f'  python aios/agent_system/meta_agent.py approve --id {sug_id}')
