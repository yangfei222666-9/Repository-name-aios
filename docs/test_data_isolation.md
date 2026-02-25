# 测试数据隔离使用指南

## 快速开始

### 1. 在测试代码开头设置环境变量
```python
import os
os.environ['AIOS_ENV'] = 'test'
```

### 2. 使用隔离的事件存储
```python
from aios.core.isolated_event_store import get_isolated_store

store = get_isolated_store()
store.append({
    'event': 'test.event',
    'severity': 'INFO',
    'payload': {'test': True}
})
```

### 3. 文件路径
- **生产环境：** `aios/events/events.jsonl`
- **测试环境：** `aios/events/test_events.jsonl`

## 集成到现有测试

### stress_test.py
```python
# 在文件开头添加
import os
os.environ['AIOS_ENV'] = 'test'

# 使用隔离存储
from aios.core.isolated_event_store import get_isolated_store
store = get_isolated_store()
```

### generate_*.py 脚本
所有生成测试数据的脚本都应该：
1. 设置 `AIOS_ENV=test`
2. 使用 `isolated_event_store`
3. 写入 `test_events.jsonl`

## 清理测试数据

```bash
# 删除测试事件
rm aios/events/test_events.jsonl

# 或者使用 Python
python -c "from pathlib import Path; Path('aios/events/test_events.jsonl').unlink(missing_ok=True)"
```

## 验证隔离

```python
# 检查生产日志是否干净
import json
from pathlib import Path

prod_file = Path('aios/events/events.jsonl')
with open(prod_file, 'r', encoding='utf-8') as f:
    for line in f:
        event = json.loads(line)
        if event.get('env') == 'test':
            print(f"WARNING: Test event in production log: {event}")
```

## 自动化

### pytest 集成
```python
# conftest.py
import pytest
import os

@pytest.fixture(autouse=True)
def isolate_test_events():
    """自动隔离测试事件"""
    os.environ['AIOS_ENV'] = 'test'
    yield
    # 测试后清理（可选）
    # Path('aios/events/test_events.jsonl').unlink(missing_ok=True)
```

### unittest 集成
```python
import unittest
import os

class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['AIOS_ENV'] = 'test'
```

## 注意事项

1. **环境变量优先级：** 必须在导入任何 AIOS 模块前设置
2. **清理策略：** 定期清理 test_events.jsonl（如每周一次）
3. **CI/CD：** 在 CI 环境中自动设置 `AIOS_ENV=test`
4. **监控：** 定期检查生产日志是否有 `env=test` 的事件

## 迁移现有测试

### 步骤 1：识别测试脚本
```bash
find aios -name "*test*.py" -o -name "generate_*.py"
```

### 步骤 2：批量添加环境变量
在每个测试文件开头添加：
```python
import os
os.environ['AIOS_ENV'] = 'test'
```

### 步骤 3：验证
运行测试，检查 test_events.jsonl 是否有新事件

---

**创建时间：** 2026-02-25  
**状态：** ✅ 已实现  
**测试：** ✅ 通过
