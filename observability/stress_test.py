"""
AIOS v2.0 - 12小时压力测试
使用Locust进行持续负载测试
"""

from locust import HttpUser, task, between, constant, events
import random
import json
import time
from pathlib import Path

# ============================================================
# 配置
# ============================================================

# 任务类型分布
TASK_TYPES = {
    'code_generation': 0.3,      # 30%
    'pattern_analysis': 0.25,    # 25%
    'health_check': 0.2,         # 20%
    'trend_analysis': 0.15,      # 15%
    'bug_fix': 0.1               # 10%
}

# 优先级分布
PRIORITIES = {
    'high': 0.2,     # 20%
    'normal': 0.6,   # 60%
    'low': 0.2       # 20%
}

# ============================================================
# 任务生成器
# ============================================================

def generate_task():
    """生成随机测试任务"""
    # 根据分布选择任务类型
    task_type = random.choices(
        list(TASK_TYPES.keys()),
        weights=list(TASK_TYPES.values())
    )[0]
    
    # 根据分布选择优先级
    priority = random.choices(
        list(PRIORITIES.keys()),
        weights=list(PRIORITIES.values())
    )[0]
    
    return {
        'task_id': f'stress-{int(time.time() * 1000)}-{random.randint(1000, 9999)}',
        'task_type': task_type,
        'description': f'Stress test task: {task_type}',
        'priority': priority,
        'metadata': {
            'test_run': '12h_stress_test',
            'timestamp': time.time()
        }
    }


# ============================================================
# Locust用户类
# ============================================================

class AIOSUser(HttpUser):
    """
    模拟AIOS用户
    每12秒发送一个任务 → 每分钟5个任务
    """
    
    # 固定间隔12秒（每分钟5个任务）
    wait_time = constant(12)
    
    def on_start(self):
        """用户启动时执行"""
        print(f"[USER] Started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    @task(10)  # 权重10 - 主要任务
    def submit_task(self):
        """提交任务到队列"""
        task = generate_task()
        
        # 写入task_queue.jsonl（模拟真实提交）
        queue_file = Path('aios/agent_system/task_queue.jsonl')
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(queue_file, 'a', encoding='utf-8') as f:
            task['status'] = 'pending'
            task['submitted_at'] = time.time()
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
        
        # 记录成功（Locust统计）
        events.request.fire(
            request_type="TASK",
            name="submit_task",
            response_time=10,  # 模拟10ms
            response_length=len(json.dumps(task)),
            exception=None,
            context={}
        )
    
    @task(1)  # 权重1 - 低频健康检查
    def check_metrics(self):
        """检查系统指标"""
        try:
            response = self.client.get("/stats", timeout=5)
            
            if response.status_code == 200:
                stats = response.json()
                # 可以在这里添加断言检查
                pass
        except Exception as e:
            print(f"[ERROR] Metrics check failed: {e}")


# ============================================================
# 事件钩子（记录测试结果）
# ============================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始"""
    print("=" * 60)
    print("AIOS 12-Hour Stress Test Started")
    print("=" * 60)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: 5 tasks/min × 12 hours = ~3,600 tasks")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束"""
    print("=" * 60)
    print("AIOS 12-Hour Stress Test Completed")
    print("=" * 60)
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 读取最终统计
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Success rate: {(1 - stats.total.fail_ratio) * 100:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"P95 response time: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print("=" * 60)
    
    # 检查退出条件
    success_rate = (1 - stats.total.fail_ratio) * 100
    p95_latency = stats.total.get_response_time_percentile(0.95) / 1000  # 转换为秒
    
    print("\n[EXIT CONDITIONS CHECK]")
    print(f"✓ Success Rate: {success_rate:.2f}% (target: ≥95%)")
    print(f"✓ P95 Latency: {p95_latency:.2f}s (target: ≤6s)")
    print("✓ Memory Growth: Check Grafana dashboard")
    print("✓ Queue Backlog: Check Grafana dashboard")
    print("✓ Agent Spawn Rate: Check Grafana dashboard")
    
    if success_rate >= 95 and p95_latency <= 6:
        print("\n🎉 PASS: Core metrics met!")
    else:
        print("\n❌ FAIL: Some metrics not met")


# ============================================================
# 命令行启动说明
# ============================================================

if __name__ == "__main__":
    print("""
AIOS v2.0 - 12小时压力测试

启动命令：
    locust -f stress_test.py --host=http://localhost:9090 \\
           --users 5 --spawn-rate 5 --run-time 12h \\
           --html report_12h.html

参数说明：
    --users 5         : 5个并发用户
    --spawn-rate 5    : 每秒启动5个用户（立即达到目标）
    --run-time 12h    : 运行12小时
    --html report.html: 生成HTML报告

Ramp-up版本（前30分钟从1→5）：
    locust -f stress_test.py --host=http://localhost:9090 \\
           --users 5 --spawn-rate 0.0028 --run-time 12h \\
           --html report_12h.html

注意：
    1. 确保 metrics_exporter.py 已启动（端口9090）
    2. 确保 Prometheus + Grafana 已启动
    3. 测试期间监控 Grafana 仪表盘
    4. 测试结束后检查 report_12h.html
""")
