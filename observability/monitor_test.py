#!/usr/bin/env python3
"""
AIOS Phase 4 - 12小时压力测试监控脚本
每2小时自动检查关键指标，发送Telegram告警
"""

import requests
import time
import json
from datetime import datetime

# 配置
METRICS_URL = "http://localhost:9090/stats"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"  # 需要配置
TELEGRAM_CHAT_ID = "7986452220"
CHECK_INTERVAL = 2 * 60 * 60  # 2小时

# Phase 4 验收标准
THRESHOLDS = {
    "success_rate": 95.0,  # ≥95%
    "p95_latency": 6.5,    # ≤6.5秒
    "memory_growth": 12.0, # ≤12%
    "queue_backlog_avg": 40,  # ≤40
    "queue_backlog_peak": 80, # ≤80
    "spawn_rate": 110,     # ≤110次/小时
    "autofixer_count": 3,  # ≤3次
    "monitor_error_rate": 2.0  # ≤2%
}

def get_metrics():
    """获取当前指标"""
    try:
        resp = requests.get(METRICS_URL, timeout=5)
        return resp.json()
    except Exception as e:
        print(f"❌ 获取指标失败: {e}")
        return None

def check_thresholds(metrics):
    """检查是否超过阈值"""
    alerts = []
    
    # 1. Success Rate
    success_rate = metrics.get("success_rate", 0)
    if success_rate < THRESHOLDS["success_rate"]:
        alerts.append(f"⚠️ Success Rate: {success_rate:.1f}% (目标: ≥{THRESHOLDS['success_rate']}%)")
    
    # 2. P95 Latency (需要从Prometheus获取)
    # TODO: 实现Prometheus查询
    
    # 3. Memory Growth (需要计算)
    # TODO: 实现内存增长监控
    
    # 4. Queue Backlog
    queue_size = metrics.get("queue_size", 0)
    if queue_size > THRESHOLDS["queue_backlog_avg"]:
        alerts.append(f"⚠️ Queue Backlog: {queue_size} (目标: ≤{THRESHOLDS['queue_backlog_avg']})")
    
    return alerts

def send_telegram(message):
    """发送Telegram消息"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"❌ 发送Telegram失败: {e}")

def main():
    """主监控循环"""
    print("=" * 60)
    print("AIOS Phase 4 - 12小时压力测试监控")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"检查间隔: {CHECK_INTERVAL // 3600} 小时")
    print("=" * 60)
    
    start_time = time.time()
    check_count = 0
    
    while True:
        check_count += 1
        elapsed = time.time() - start_time
        elapsed_hours = elapsed / 3600
        
        print(f"\n[检查 #{check_count}] 已运行: {elapsed_hours:.1f} 小时")
        
        # 获取指标
        metrics = get_metrics()
        if not metrics:
            time.sleep(60)
            continue
        
        # 检查阈值
        alerts = check_thresholds(metrics)
        
        # 显示当前状态
        print(f"  Success Rate: {metrics.get('success_rate', 0):.1f}%")
        print(f"  Total Tasks: {metrics.get('total_tasks', 0)}")
        print(f"  Queue Size: {metrics.get('queue_size', 0)}")
        print(f"  Active Agents: {metrics.get('active_agents', 0)}")
        
        # 如果有告警，发送Telegram
        if alerts:
            print("\n⚠️ 发现异常:")
            for alert in alerts:
                print(f"  {alert}")
            
            message = f"🚨 *AIOS Phase 4 告警*\n\n"
            message += f"运行时间: {elapsed_hours:.1f}h\n"
            message += f"检查次数: #{check_count}\n\n"
            message += "\n".join(alerts)
            
            # send_telegram(message)  # 取消注释以启用Telegram
        else:
            print("  ✓ 所有指标正常")
        
        # 如果超过12小时，退出
        if elapsed >= 12 * 3600:
            print("\n" + "=" * 60)
            print("✅ 12小时测试完成！")
            print("=" * 60)
            break
        
        # 等待下次检查
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
