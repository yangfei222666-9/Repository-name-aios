import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\scripts')
from auto_model import classify

tests = [
    'hi',
    '今天天气怎么样',
    '帮我写一个Python爬虫',
    '谢谢',
    '帮我分析一下AIOS的baseline数据，找出性能瓶颈并优化',
    '先写代码再测试然后部署',
    '查一下新山的餐厅',
    '帮我重构autolearn的模糊匹配模块',
    '好的',
    '还有可以提升的吗',
]

for t in tests:
    r = classify(t)
    model_short = r['model'].replace('claude-', '').replace('-4-5', '').replace('-4-6', '')
    icon = '🔧' if 'opus' in r['model'] else '💬'
    print(f"{icon} [{model_short:7s}] {t:35s} | {r['reason']} ({r['confidence']})")
