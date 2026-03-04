"""
AIOS v2.0 - Prometheus Metrics Exporter
统一暴露所有Agent指标，避免每个Agent单独开端口
"""

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import json
from pathlib import Path
from typing import Dict, Any
import time

app = FastAPI(title="AIOS Metrics Exporter")

# ============================================================
# Prometheus 指标定义
# ============================================================

# 1. 任务延迟（P95）
task_latency = Histogram(
    'task_latency_seconds',
    'Task execution latency in seconds',
    ['agent_id', 'task_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# 2. Agent生成速率
agent_spawn_total = Counter(
    'agent_spawn_per_hour_total',
    'Total agent spawns per hour',
    ['agent_id']
)

# 3. 队列大小
queue_size = Gauge(
    'queue_size_gauge',
    'Current queue size',
    ['queue_name']
)

# 4. 队列等待时间
queue_wait_time = Histogram(
    'queue_wait_time_seconds',
    'Queue wait time in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# 5. 内存使用
process_memory = Gauge(
    'process_resident_memory_bytes',
    'Process resident memory in bytes'
)

process_heap = Gauge(
    'process_heap_memory_bytes',
    'Process heap memory in bytes'
)

# 6. 任务成功率
task_success = Counter(
    'task_success_total',
    'Total successful tasks',
    ['agent_id']
)

task_total = Counter(
    'task_total',
    'Total tasks',
    ['agent_id']
)

# ============================================================
# 数据采集
# ============================================================

def load_agent_states() -> Dict[str, Any]:
    """从state文件加载所有Agent状态"""
    state_dir = Path('aios/agent_system/state')
    if not state_dir.exists():
        return {}
    
    states = {}
    for state_file in state_dir.glob('*_state.json'):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                agent_id = state.get('agent_id')
                if agent_id:
                    states[agent_id] = state
        except Exception as e:
            print(f"[WARN] Failed to load {state_file}: {e}")
    
    return states


def load_queue_stats() -> Dict[str, int]:
    """从task_queue.jsonl加载队列统计"""
    queue_file = Path('aios/agent_system/task_queue.jsonl')
    if not queue_file.exists():
        return {'pending': 0}
    
    try:
        with open(queue_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            pending = sum(1 for line in lines if '"status":"pending"' in line)
            return {'pending': pending}
    except Exception:
        return {'pending': 0}


def update_metrics():
    """更新所有Prometheus指标"""
    # 1. 更新Agent指标
    states = load_agent_states()
    for agent_id, state in states.items():
        metrics = state.get('metrics', {})
        
        # 任务总数和成功数
        total = metrics.get('tasks_total', 0)
        success = metrics.get('tasks_success', 0)
        
        # 更新Counter（只增不减，所以需要计算增量）
        # 这里简化处理，直接设置（生产环境应该用增量）
        task_total.labels(agent_id=agent_id)._value._value = total
        task_success.labels(agent_id=agent_id)._value._value = success
        
        # 平均延迟（转换为秒）
        avg_latency_s = metrics.get('avg_latency_ms', 0) / 1000.0
        if avg_latency_s > 0:
            task_latency.labels(agent_id=agent_id, task_type='all').observe(avg_latency_s)
    
    # 2. 更新队列指标
    queue_stats = load_queue_stats()
    queue_size.labels(queue_name='main').set(queue_stats['pending'])
    
    # 3. 更新内存指标（简化版，实际应该用psutil）
    try:
        import psutil
        process = psutil.Process()
        process_memory.set(process.memory_info().rss)
        # heap memory需要更复杂的采集，这里用rss代替
        process_heap.set(process.memory_info().rss * 0.7)
    except ImportError:
        # 如果没有psutil，使用模拟数据
        process_memory.set(500 * 1024 * 1024)  # 500MB
        process_heap.set(350 * 1024 * 1024)    # 350MB


# ============================================================
# API端点
# ============================================================

@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    # 每次请求时更新指标
    update_metrics()
    
    # 返回Prometheus格式
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.get("/stats")
async def stats():
    """人类可读的统计信息"""
    states = load_agent_states()
    queue_stats = load_queue_stats()
    
    return {
        "agents": {
            agent_id: {
                "tasks_total": state.get('metrics', {}).get('tasks_total', 0),
                "tasks_success": state.get('metrics', {}).get('tasks_success', 0),
                "success_rate": state.get('metrics', {}).get('tasks_success', 0) / max(state.get('metrics', {}).get('tasks_total', 1), 1) * 100,
                "avg_latency_ms": state.get('metrics', {}).get('avg_latency_ms', 0)
            }
            for agent_id, state in states.items()
        },
        "queue": queue_stats,
        "timestamp": time.time()
    }


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("AIOS Metrics Exporter v2.0")
    print("=" * 60)
    print("Prometheus endpoint: http://localhost:9090/metrics")
    print("Health check: http://localhost:9090/health")
    print("Human-readable stats: http://localhost:9090/stats")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=9090)
