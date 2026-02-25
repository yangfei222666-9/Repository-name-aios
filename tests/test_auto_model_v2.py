import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\scripts')
from auto_model import should_switch

tests = [
    ('帮我重构autolearn的模糊匹配', 'opus'),
    ('今天天气怎么样', 'sonnet'),
    ('好的', 'sonnet'),
    ('帮我分析AIOS baseline性能瓶颈', 'opus'),
]

for msg, expected in tests:
    r = should_switch(msg)
    icon = '✓' if r['to'] == expected else '✗'
    switch_str = '→' + r['to'] if r['should_switch'] else '保持'
    from_model = r['from']
    reason = r['reason'][:40]
    print(f"{icon} {msg[:25]:25s} | {from_model:6s} {switch_str:10s} | {reason}")
