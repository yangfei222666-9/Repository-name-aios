"""Clean test data from production agent_traces.jsonl"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

traces_file = r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\traces\agent_traces.jsonl"

prod_lines = []
test_count = 0

with open(traces_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
            agent_id = ev.get('agent_id', '')
            env = ev.get('env', '')
            if agent_id.startswith('test-') or env == 'test':
                test_count += 1
            else:
                prod_lines.append(line)
        except:
            prod_lines.append(line)

print(f"Removed {test_count} test traces, keeping {len(prod_lines)} production traces")

with open(traces_file, 'w', encoding='utf-8') as f:
    for line in prod_lines:
        f.write(line + '\n')

print("Done!")
