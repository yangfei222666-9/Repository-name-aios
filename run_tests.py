"""
AIOS 测试运行器
运行所有测试并生成报告
"""
import sys
import subprocess
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
TESTS_DIR = AIOS_ROOT / "tests"

# 测试文件列表
test_files = [
    "test_event_bus.py",
    "test_integration.py",
    "test_full_loop.py",
    "test_full_system.py",
    "test_e2e_heartbeat.py",
    "test_e2e_dashboard.py",
]

print("=" * 60)
print("AIOS 测试套件")
print("=" * 60)

passed = 0
failed = 0
errors = []

for test_file in test_files:
    test_path = TESTS_DIR / test_file
    
    if not test_path.exists():
        print(f"\n⚠️  跳过: {test_file} (文件不存在)")
        continue
    
    print(f"\n运行: {test_file}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(test_path)],
            cwd=str(AIOS_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {test_file} 通过")
            passed += 1
        else:
            print(f"❌ {test_file} 失败")
            print(f"错误输出:\n{result.stderr}")
            failed += 1
            errors.append((test_file, result.stderr))
    
    except subprocess.TimeoutExpired:
        print(f"⏱️  {test_file} 超时")
        failed += 1
        errors.append((test_file, "测试超时"))
    
    except Exception as e:
        print(f"💥 {test_file} 异常: {e}")
        failed += 1
        errors.append((test_file, str(e)))

# 总结
print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)
print(f"总计: {passed + failed}")
print(f"通过: {passed}")
print(f"失败: {failed}")

if errors:
    print("\n失败详情:")
    for test_file, error in errors:
        print(f"\n{test_file}:")
        print(f"  {error[:200]}")

if failed == 0:
    print("\n🎉 所有测试通过！")
    sys.exit(0)
else:
    print(f"\n⚠️  {failed} 个测试失败")
    sys.exit(1)
