"""Clean ALL test data from agent_traces.jsonl"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

traces_file = r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\traces\agent_traces.jsonl"

# Test patterns to remove
test_patterns = [
    'test_task',
    'test-',  # test agent IDs
    '优化数据库查询',
    '任务 1',
    '任务 2', 
    '任务 3',
    '搜索文档',
]

real_traces = []
removed_count = 0

with open(traces_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
            agent_id = ev.get('agent_id', '')
            task = ev.get('task', '') or ''
            env = ev.get('env', '')
            
            # Check if it's test data
            is_test = (
                agent_id.startswith('test-') or
                env == 'test' or
                any(p in task for p in test_patterns)
            )
            
            if is_test:
                removed_count += 1
            else:
                real_traces.append(line)
        except:
            real_traces.append(line)

print(f"Removed {removed_count} test traces")
print(f"Keeping {len(real_traces)} real production traces")

# Write back
with open(traces_file, 'w', encoding='utf-8') as f:
    for line in real_traces:
        f.write(line + '\n')

print("Done!")
