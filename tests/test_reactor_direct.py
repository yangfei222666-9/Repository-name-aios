"""
直接创建 alerts 来测试 Reactor
绕过 alerts.py 的规则检测，直接写入 alert_fsm
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加路径
WS = Path(r'C:\Users\A\.openclaw\workspace')
sys.path.insert(0, str(WS / 'scripts'))
sys.path.insert(0, str(WS / 'aios'))

import alert_fsm

def create_test_alert(rule_id, severity, message):
    """创建测试告警"""
    alert = alert_fsm.open_alert(
        rule_id=rule_id,
        severity=severity,
        message=message,
        scope="test"
    )
    return alert['id']

def test_network_error_alert():
    """测试网络错误告警"""
    print("🧪 测试 1: 创建网络错误告警")
    alert_id = create_test_alert(
        rule_id="network_error",
        severity="ERR",
        message="Network error: 502 Bad Gateway - failed to connect to API server"
    )
    print(f"✅ 告警已创建：{alert_id}")
    return alert_id

def test_rate_limit_alert():
    """测试 API 限流告警"""
    print("\n🧪 测试 2: 创建 API 限流告警")
    alert_id = create_test_alert(
        rule_id="rate_limit",
        severity="WARN",
        message="API rate limit exceeded: 429 Too Many Requests"
    )
    print(f"✅ 告警已创建：{alert_id}")
    return alert_id

def test_memory_high_alert():
    """测试内存占用告警"""
    print("\n🧪 测试 3: 创建内存占用告警")
    alert_id = create_test_alert(
        rule_id="memory_high",
        severity="WARN",
        message="High memory usage detected: 85% of RAM in use"
    )
    print(f"✅ 告警已创建：{alert_id}")
    return alert_id

if __name__ == "__main__":
    print("=" * 50)
    print("Reactor 直接测试（创建 Alerts）")
    print("=" * 50)
    
    alert_ids = []
    alert_ids.append(test_network_error_alert())
    alert_ids.append(test_rate_limit_alert())
    alert_ids.append(test_memory_high_alert())
    
    print("\n" + "=" * 50)
    print(f"✅ 创建了 {len(alert_ids)} 个测试告警")
    print("=" * 50)
    
    # 显示当前告警状态
    print("\n📊 当前告警状态：")
    stats = alert_fsm.stats()
    print(f"  - OPEN: {stats.get('open', 0)}")
    print(f"  - ACK: {stats.get('ack', 0)}")
    print(f"  - RESOLVED: {stats.get('resolved_today', 0)}")
    
    print("\n下一步：运行 pipeline.py 查看 Reactor 是否匹配并执行")
    print("命令：python -X utf8 C:\\Users\\A\\.openclaw\\workspace\\aios\\pipeline.py run")
