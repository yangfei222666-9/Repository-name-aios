import sys
sys.path.insert(0, 'aios/agent_system')
from meta_agent import MetaAgent

meta = MetaAgent()
gaps = meta.detect_gaps()

print(f'检测到 {len(gaps)} 个缺口')
print()

for i, gap in enumerate(gaps, 1):
    gap_type = gap.get('gap_type', '?')
    agent_type = gap.get('agent_type', '?')
    desc = gap.get('description', '?')
    severity = gap.get('severity', '?')
    
    print(f'{i}. {gap_type}: {agent_type}')
    print(f'   描述: {desc}')
    print(f'   严重程度: {severity}')
    print()
