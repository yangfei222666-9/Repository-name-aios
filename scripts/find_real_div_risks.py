"""Find REAL unprotected division-by-zero risks in AIOS code"""
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

base = r"C:\Users\A\.openclaw\workspace\aios"
skip_dirs = {'tests', 'backups', '__pycache__', 'benchmarks', 'scripts', '_deprecated'}
skip_files = {'find_division_errors.py', 'scan_all_errors.py', 'analyze_logic_errors.py', 'find_unprotected_div.py'}

# Real division pattern: variable / variable (not in strings, comments, URLs)
div_pattern = re.compile(r'(\w+)\s*/\s*(len\([^)]+\)|\w+)')

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
            
            in_docstring = False
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # Track docstrings
                if '"""' in stripped or "'''" in stripped:
                    count = stripped.count('"""') + stripped.count("'''")
                    if count % 2 == 1:
                        in_docstring = not in_docstring
                    continue
                if in_docstring:
                    continue
                
                # Skip comments, imports, strings-only lines, print statements
                if stripped.startswith('#') or stripped.startswith('import') or stripped.startswith('from'):
                    continue
                if stripped.startswith('print(') or stripped.startswith('"') or stripped.startswith("'"):
                    continue
                
                # Skip lines that are just string assignments or contain URLs
                if 'http://' in stripped or 'https://' in stripped or '/.openclaw/' in stripped:
                    continue
                if '/api/' in stripped or '/plugins/' in stripped:
                    continue
                
                # Find actual arithmetic division
                matches = div_pattern.findall(stripped)
                if not matches:
                    continue
                
                # Filter: divisor must be a variable that could be zero
                real_divs = []
                for numerator, divisor in matches:
                    # Skip if divisor is a constant > 0
                    if divisor in ('2', '3', '4', '10', '100', '1000', '1024', '24', '60'):
                        continue
                    # Skip path-like patterns
                    if numerator in ('aios', 'data', 'events', 'plugins', 'builtin', 'api', 'agents'):
                        continue
                    real_divs.append((numerator, divisor))
                
                if not real_divs:
                    continue
                
                # Check if there's a guard
                has_guard = False
                # Inline guard: "if x > 0 else" or "if x else"
                if 'if' in stripped and ('> 0' in stripped or 'else' in stripped):
                    has_guard = True
                # Previous line guard
                if not has_guard and i > 1:
                    prev = ''.join(lines[max(0,i-4):i-1])
                    if ('> 0' in prev or '== 0' in prev or 'not ' in prev or 
                        'if len(' in prev or 'if total' in prev or 'if count' in prev):
                        has_guard = True
                
                if not has_guard:
                    rel = os.path.relpath(fpath, base)
                    unprotected.append((rel, i, stripped, real_divs))
        except:
            pass

print(f"Unprotected divisions found: {len(unprotected)}")
print()
for rel, line_no, code, divs in unprotected:
    div_str = ', '.join(f"{n}/{d}" for n, d in divs)
    print(f"⚠️  {rel}:{line_no}  [{div_str}]")
    print(f"    {code}")
    print()
