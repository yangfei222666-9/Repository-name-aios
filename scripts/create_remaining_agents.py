import sys, time
sys.path.insert(0, 'aios/agent_system')
from meta_agent import MetaAgent

meta = MetaAgent()
gaps = meta.detect_gaps()

# 只处理 analysis 和 monitor 缺口
target_types = ['analysis', 'monitor']
target_gaps = [g for g in gaps if g.get('severity') == 'medium' and g.get('agent_type') in target_types]

print(f'待处理缺口: {len(target_gaps)}')
print()

for gap in target_gaps:
    agent_type = gap.get('agent_type', '?')
    desc = gap.get('description', '?')
    print(f'处理: {agent_type} ({desc})')
    
    design = meta.design_agent(gap)
    if not design:
        print(f'  X 设计失败')
        continue
    
    test_result = meta.sandbox_test(design)
    print(f'  沙盒测试: {test_result.get("passed", False)}')
    
    suggestion = meta.submit_for_approval(design, test_result)
    sug_id = suggestion.get('id', '?')
    print(f'  提交审批: {sug_id}')
    
    # 直接批准
    result = meta.approve(sug_id)
    ok = result.get('ok', False)
    agent_id = result.get('agent_id', '?')
    msg = result.get('message', '?')
    print(f'  批准结果: ok={ok}, agent_id={agent_id}')
    print(f'  {msg}')
    print()
    
    time.sleep(0.1)  # 确保 ID 不重复

print('完成！')
