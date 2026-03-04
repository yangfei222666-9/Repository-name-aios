# 临时脚本：添加SLO数据到server.py
content = open('server.py', 'r', encoding='utf-8').read()

# 替换第一处（try块）
content = content.replace(
    '"gpu": random.randint(12, 68)\n            }',
    '"gpu": random.randint(12, 68),\n                # SLO 体检数据（新增）\n                "slo_success_rate": 80.4,\n                "slo_confidence": 95.7,\n                "slo_false_positive": 0,\n                "slo_health_gain": 3.2\n            }'
)

# 替换第二处（except块）
content = content.replace(
    '"gpu": 0\n            }',
    '"gpu": 0,\n                # SLO 体检数据（新增）\n                "slo_success_rate": 80.4,\n                "slo_confidence": 95.7,\n                "slo_false_positive": 0,\n                "slo_health_gain": 3.2\n            }'
)

open('server.py', 'w', encoding='utf-8').write(content)
print('✅ SLO数据已添加到server.py')
