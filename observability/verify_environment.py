"""
AIOS v2.0 - 快速验证脚本
验证监控环境是否正常工作
"""

import requests
import time
import json
from pathlib import Path

def test_metrics_exporter():
    """测试Metrics Exporter"""
    print("[TEST] Metrics Exporter...")
    try:
        # 健康检查
        resp = requests.get("http://localhost:9090/health", timeout=5)
        assert resp.status_code == 200
        print("  ✓ Health check OK")
        
        # 统计信息
        resp = requests.get("http://localhost:9090/stats", timeout=5)
        assert resp.status_code == 200
        stats = resp.json()
        print(f"  ✓ Stats OK (agents: {len(stats.get('agents', {}))})")
        
        # Prometheus指标
        resp = requests.get("http://localhost:9090/metrics", timeout=5)
        assert resp.status_code == 200
        assert "task_latency_seconds" in resp.text
        print("  ✓ Prometheus metrics OK")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def test_prometheus():
    """测试Prometheus"""
    print("\n[TEST] Prometheus...")
    try:
        resp = requests.get("http://localhost:9091/-/healthy", timeout=5)
        assert resp.status_code == 200
        print("  ✓ Prometheus healthy")
        
        # 查询指标
        resp = requests.get(
            "http://localhost:9091/api/v1/query",
            params={"query": "up"},
            timeout=5
        )
        assert resp.status_code == 200
        print("  ✓ Query API OK")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def test_grafana():
    """测试Grafana"""
    print("\n[TEST] Grafana...")
    try:
        resp = requests.get("http://localhost:3000/api/health", timeout=5)
        assert resp.status_code == 200
        print("  ✓ Grafana healthy")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def simulate_tasks():
    """模拟提交任务"""
    print("\n[TEST] Simulating tasks...")
    queue_file = Path("aios/agent_system/task_queue.jsonl")
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    
    for i in range(5):
        task = {
            "task_id": f"test-{int(time.time())}-{i}",
            "task_type": "code_generation",
            "description": f"Test task {i}",
            "priority": "normal",
            "status": "pending",
            "submitted_at": time.time()
        }
        
        with open(queue_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
        
        print(f"  ✓ Task {i+1}/5 submitted")
        time.sleep(0.5)
    
    return True


def main():
    print("=" * 60)
    print("AIOS v2.0 - 监控环境验证")
    print("=" * 60)
    
    results = {
        "Metrics Exporter": test_metrics_exporter(),
        "Prometheus": test_prometheus(),
        "Grafana": test_grafana(),
        "Task Simulation": simulate_tasks()
    }
    
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有测试通过！环境就绪，可以开始12小时压测")
        print("\n下一步:")
        print("  cd aios/observability")
        print("  locust -f stress_test.py --host=http://localhost:9090 \\")
        print("         --users 5 --spawn-rate 5 --run-time 12h \\")
        print("         --html report_12h.html")
    else:
        print("\n❌ 部分测试失败，请检查服务状态")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
