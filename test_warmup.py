"""
测试预热效果
"""
import time
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from heartbeat_runner_optimized import warmup_components, run_heartbeat_minimal


print("=" * 60)
print("测试预热效果")
print("=" * 60)

# 第一步：预热
print("\n1. 预热组件...")
warmup_components()

# 第二步：测试心跳性能
print("\n2. 测试心跳性能（10 次）...")
times = []

for i in range(10):
    start = time.time()
    result = run_heartbeat_minimal()
    elapsed_ms = (time.time() - start) * 1000
    times.append(elapsed_ms)
    print(f"   Run {i+1}: {elapsed_ms:.1f}ms - {result}")

# 统计
print("\n3. 性能统计:")
print(f"   平均: {sum(times)/len(times):.1f}ms")
print(f"   最快: {min(times):.1f}ms")
print(f"   最慢: {max(times):.1f}ms")

# 判断
avg = sum(times) / len(times)
if avg < 10:
    print(f"\n✅ 预热成功！平均延迟 {avg:.1f}ms < 10ms")
else:
    print(f"\n⚠️ 预热效果不佳，平均延迟 {avg:.1f}ms")

print("\n" + "=" * 60)
