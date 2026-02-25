"""Find all division by zero errors in events.jsonl"""
import json
import collections
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

errors = []
with open('aios/events.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
            detail = str(ev.get('detail', '') or '')
            data = ev.get('data', {}) or {}
            data_detail = str(data.get('detail', '') or '')
            data_error = str(data.get('error', '') or '')
            combined = detail + data_detail + data_error
            
            if 'division by zero' in combined.lower() or 'ZeroDivisionError' in combined:
                errors.append(ev)
        except:
            pass

print(f"Total division by zero errors: {len(errors)}")
print()

# Group by source file
sources = collections.Counter()
for e in errors:
    detail = str(e.get('detail', '') or '')
    data = e.get('data', {}) or {}
    data_detail = str(data.get('detail', '') or '')
    data_error = str(data.get('error', '') or '')
    combined = detail + data_detail + data_error
    
    files = re.findall(r'File "([^"]+)", line (\d+)', combined)
    if files:
        for f_path, line_no in files:
            if 'aios' in f_path or 'openclaw' in f_path:
                sources[f"{f_path}:{line_no}"] += 1
    else:
        src = e.get('source', '') or e.get('agent', '') or e.get('type', '') or 'unknown'
        sources[src] += 1

print("Top sources:")
for src, count in sources.most_common(20):
    print(f"  {count}x  {src}")

print()
print("=" * 60)
print("Sample error details (first 5):")
print("=" * 60)
for i, e in enumerate(errors[:5]):
    ts = e.get('timestamp', '?')
    if isinstance(ts, str):
        ts = ts[:19]
    detail = str(e.get('detail', '') or '')[:300]
    data = e.get('data', {}) or {}
    data_detail = str(data.get('detail', '') or '')[:300]
    data_error = str(data.get('error', '') or '')[:300]
    
    print(f"\n--- Error {i+1} [{ts}] ---")
    print(f"  type: {e.get('type', '?')}")
    print(f"  source: {e.get('source', '?')}")
    print(f"  agent: {e.get('agent', '?')}")
    if detail:
        print(f"  detail: {detail}")
    if data_detail:
        print(f"  data.detail: {data_detail}")
    if data_error:
        print(f"  data.error: {data_error}")

# Also check for patterns - are they all from the same operation?
print()
print("=" * 60)
print("Error timeline (all):")
print("=" * 60)
for e in errors:
    ts = str(e.get('timestamp', '?'))[:19]
    src = e.get('source', '') or e.get('agent', '') or '?'
    typ = e.get('type', '?')
    print(f"  {ts}  [{typ}]  src={src}")
