"""Find unprotected division operations in AIOS production code"""
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

base = r"C:\Users\A\.openclaw\workspace\aios"
skip_dirs = {'tests', 'backups', '__pycache__', 'benchmarks', 'scripts'}
skip_files = {'find_division_errors.py', 'scan_all_errors.py', 'analyze_logic_errors.py'}

# Pattern: division without "if ... > 0 else" or "if ... else" guard
unprotected = []

for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for fname in files:
        if not fname.endswith('.py') or fname in skip_files:
            continue
        if 'test' in fname.lower():
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # Skip comments, imports, docstrings
                if stripped.startswith('#') or stripped.startswith('import') or stripped.startswith('from'):
                    continue
                if '"""' in stripped or "'''" in stripped:
                    continue
                
                # Find division operations
                # Match patterns like: x / y, x / len(y), x / total
                div_matches = re.findall(r'\w+\s*/\s*(?:len\([^)]+\)|\w+)', stripped)
                if not div_matches:
                    continue
                
                # Check if it has a guard
                has_guard = ('if' in stripped and ('> 0' in stripped or 'else' in stripped)) or \
                           ('if' in stripped and 'else' in stripped)
                
                if not has_guard and '/ 0' not in stripped and 'lambda' not in stripped:
                    # Check if previous lines have a guard
                    prev_lines = ''.join(lines[max(0,i-3):i-1])
                    has_prev_guard = ('if' in prev_lines and ('> 0' in prev_lines or '== 0' in prev_lines or 'not ' in prev_lines))
                    
                    if not has_prev_guard:
                        rel = os.path.relpath(fpath, base)
                        unprotected.append((rel, i, stripped))
        except:
            pass

print(f"Potentially unprotected divisions: {len(unprotected)}")
print()
for rel, line_no, code in unprotected:
    print(f"  {rel}:{line_no}")
    print(f"    {code}")
    print()
