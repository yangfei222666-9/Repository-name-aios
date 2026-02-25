"""Search all AIOS data files for division by zero errors"""
import json
import os
import sys
import re
import collections

sys.stdout.reconfigure(encoding='utf-8')

base = r"C:\Users\A\.openclaw\workspace\aios"

# Search all jsonl files
division_hits = []
all_error_lines = []

for root, dirs, files in os.walk(base):
    # Skip backups and tests
    if 'backups' in root or 'tests' in root:
        continue
    for fname in files:
        if not fname.endswith('.jsonl'):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    low = line.lower()
                    if 'division' in low or 'zerodivision' in low:
                        division_hits.append((fpath, line_no, line.strip()[:300]))
                    if 'error' in low and ('division' in low or 'zero' in low):
                        all_error_lines.append((fpath, line_no, line.strip()[:300]))
        except:
            pass

print(f"Lines containing 'division': {len(division_hits)}")
for fpath, ln, content in division_hits[:20]:
    rel = os.path.relpath(fpath, base)
    print(f"  {rel}:{ln} -> {content[:200]}")

print()
print(f"Lines with 'error' + 'division/zero': {len(all_error_lines)}")
for fpath, ln, content in all_error_lines[:10]:
    rel = os.path.relpath(fpath, base)
    print(f"  {rel}:{ln} -> {content[:200]}")

# Now let's look at agent traces for failures
print()
print("=" * 60)
print("Agent traces - failures:")
print("=" * 60)

traces_file = os.path.join(base, "agent_system", "data", "traces", "agent_traces.jsonl")
if os.path.exists(traces_file):
    failures = []
    total = 0
    error_categories = collections.Counter()
    with open(traces_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                total += 1
                status = ev.get('status', '') or ev.get('result', '')
                error = ev.get('error', '') or ev.get('detail', '') or ''
                if status in ('failed', 'error', 'timeout') or 'error' in str(error).lower():
                    failures.append(ev)
                    err_str = str(error).lower()
                    if 'division' in err_str or 'zerodivision' in err_str:
                        error_categories['division_by_zero'] += 1
                    elif 'timeout' in err_str:
                        error_categories['timeout'] += 1
                    elif 'import' in err_str:
                        error_categories['import'] += 1
                    else:
                        error_categories[err_str[:60] if err_str else status] += 1
            except:
                pass
    
    print(f"Total traces: {total}, Failures: {len(failures)}")
    print()
    print("Failure categories:")
    for cat, cnt in error_categories.most_common(20):
        print(f"  {cnt}x  {cat}")
    
    print()
    print("Sample failures (first 10):")
    for i, ev in enumerate(failures[:10]):
        print(f"\n  --- Failure {i+1} ---")
        for k in ['timestamp', 'ts', 'agent', 'agent_id', 'task', 'task_type', 'status', 'result', 'error', 'detail']:
            v = ev.get(k)
            if v:
                print(f"    {k}: {str(v)[:200]}")

# Also check fix_history
print()
print("=" * 60)
print("Fix history (recent):")
print("=" * 60)
fix_file = os.path.join(base, "agent_system", "data", "fixes", "fix_history.jsonl")
if os.path.exists(fix_file):
    fixes = []
    with open(fix_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                fixes.append(json.loads(line))
            except:
                pass
    print(f"Total fixes: {len(fixes)}")
    for fix in fixes[-5:]:
        print(f"  {fix}")

# Check decisions.jsonl for error patterns
print()
print("=" * 60)
print("Decisions with errors:")
print("=" * 60)
dec_file = os.path.join(base, "data", "decisions.jsonl")
if os.path.exists(dec_file):
    error_decisions = []
    total_dec = 0
    with open(dec_file, 'r', encoding='utf-8') as f:
        for line in f:
            total_dec += 1
            if 'division' in line.lower() or 'error' in line.lower():
                try:
                    d = json.loads(line.strip())
                    if 'division' in str(d).lower():
                        error_decisions.append(d)
                except:
                    pass
    print(f"Total decisions: {total_dec}, with 'division': {len(error_decisions)}")
