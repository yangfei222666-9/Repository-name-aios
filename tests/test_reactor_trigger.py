"""
测试 Reactor 自动修复机制
故意触发错误，验证 Reactor 是否能自动修复
"""
import json
from pathlib import Path
from datetime import datetime

# 事件队列目录
QUEUE_DIR = Path(__file__).resolve().parent.parent / "events" / "queue"
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

# 今天的队列文件
today = datetime.now().strftime("%Y-%m-%d")
queue_file = QUEUE_DIR / f"{today}.jsonl"

def emit_event(layer, level, msg, meta=None):
    """发射事件到队列"""
    event = {
        "ts": datetime.now().isoformat(),
        "layer": layer,
        "level": level,
        "msg": msg,
        "meta": meta or {}
    }
    with open(queue_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

def test_network_error():
    """测试网络错误自动重试"""
    print("🧪 测试 1: 网络错误自动重试")
    emit_event(
        layer="TOOL",
        level="ERR",
        msg="Network error: 502 Bad Gateway - failed to connect to API server",
        meta={"test": True, "playbook": "pb-001-network-retry"}
    )
    print("✅ 网络错误事件已发射")

def test_rate_limit():
    """测试 API 限流自动等待"""
    print("\n🧪 测试 2: API 限流自动等待")
    emit_event(
        layer="COMMS",
        level="WARN",
        msg="API rate limit exceeded: 429 Too Many Requests",
        meta={"test": True, "playbook": "pb-004-api-rate-limit"}
    )
    print("✅ 限流事件已发射")

def test_memory_high():
    """测试内存占用告警"""
    print("\n🧪 测试 3: 内存占用告警")
    emit_event(
        layer="KERNEL",
        level="WARN",
        msg="High memory usage detected: 85% of RAM in use",
        meta={"test": True, "playbook": "pb-005-memory-leak"}
    )
    print("✅ 内存告警事件已发射")

if __name__ == "__main__":
    print("=" * 50)
    print("Reactor 自动修复测试")
    print("=" * 50)
    
    test_network_error()
    test_rate_limit()
    test_memory_high()
    
    print("\n" + "=" * 50)
    print("✅ 测试事件发射完成")
    print(f"📁 事件已写入：{queue_file}")
    print("=" * 50)
    print("\n下一步：运行 pipeline.py 查看 Reactor 是否匹配并执行")
    print("命令：python -X utf8 C:\\Users\\A\\.openclaw\\workspace\\aios\\pipeline.py run")

