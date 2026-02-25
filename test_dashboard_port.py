"""
测试 Dashboard 端口自动切换
"""
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from dashboard.server import is_port_in_use, find_available_port

print("=" * 60)
print("Dashboard 端口检测测试")
print("=" * 60)

# 测试端口检测
print("\n1. 测试端口检测...")
for port in [9091, 9092, 9093]:
    in_use = is_port_in_use(port)
    status = "❌ 占用" if in_use else "✅ 可用"
    print(f"   端口 {port}: {status}")

# 测试查找可用端口
print("\n2. 测试查找可用端口...")
try:
    available_port = find_available_port(9091)
    print(f"   ✅ 找到可用端口: {available_port}")
except RuntimeError as e:
    print(f"   ❌ {e}")

print("\n" + "=" * 60)
print("✅ 测试完成")
print("=" * 60)
