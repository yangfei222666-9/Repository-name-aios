import sys
sys.path.insert(0, 'aios/agent_system')
from meta_agent import MetaAgent

meta = MetaAgent()
gaps = meta.detect_gaps()

# 只处理高优先级的缺口（频繁失败）
high_priority = [g for g in gaps if g.get('severity') == 'medium']

print(f'高优先级缺口: {len(high_priority)}')
print()

for gap in high_priority:
    agent_type = gap.get('agent_type', '?')
    desc = gap.get('description', '?')
    print(f'处理缺口: {agent_type} ({desc})')
    
    # 生成建议
    suggestion = meta.generate_suggestion(gap)
    if suggestion:
        sug_id = suggestion.get('id', '?')
        sug_type = suggestion.get('agent_type', '?')
        priority = suggestion.get('priority', '?')
        print(f'  建议 ID: {sug_id}')
        print(f'  Agent 类型: {sug_type}')
        print(f'  优先级: {priority}')
        print()
