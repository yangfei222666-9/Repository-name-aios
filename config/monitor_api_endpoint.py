#!/usr/bin/env python3
"""
API Endpoint Health Monitor
监控 apiport.cc.cd 状态，恢复后自动通知
"""

import os
import sys
import time
import requests
from datetime import datetime

def check_endpoint_health(base_url, api_key):
    """检查 API 端点健康状态"""
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-opus-4-6",
            "max_tokens": 10,
            "messages": [
                {"role": "user", "content": "ping"}
            ]
        }
        
        response = requests.post(
            f"{base_url}/v1/messages",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "OK", response.status_code
        else:
            return False, response.text[:200], response.status_code
            
    except requests.exceptions.Timeout:
        return False, "Timeout", None
    except requests.exceptions.ConnectionError:
        return False, "Connection Error", None
    except Exception as e:
        return False, str(e)[:200], None

def send_telegram_notification(message):
    """发送 Telegram 通知"""
    # 这里使用 OpenClaw 的 message 工具
    # 实际使用时需要通过 OpenClaw CLI 调用
    print(f"\n[NOTIFICATION] {message}")
    print("(Use OpenClaw message tool to send to Telegram)")

def monitor_loop(base_url, api_key, check_interval=60, max_checks=60):
    """
    监控循环
    
    Args:
        base_url: API 端点 URL
        api_key: API Key
        check_interval: 检查间隔（秒）
        max_checks: 最大检查次数（0=无限）
    """
    print("=" * 60)
    print("API Endpoint Health Monitor")
    print("=" * 60)
    print(f"Target: {base_url}")
    print(f"Check interval: {check_interval}s")
    print(f"Max checks: {max_checks if max_checks > 0 else 'Unlimited'}")
    print("=" * 60)
    print()
    
    check_count = 0
    consecutive_failures = 0
    last_status = None
    
    while True:
        check_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"[{timestamp}] Check #{check_count}...", end=" ")
        
        is_healthy, message, status_code = check_endpoint_health(base_url, api_key)
        
        if is_healthy:
            print(f"[OK] Status: {status_code}")
            consecutive_failures = 0
            
            # 如果之前是失败状态，现在恢复了，发送通知
            if last_status == False:
                notification = f"🟢 API Endpoint Recovered!\n\nEndpoint: {base_url}\nStatus: {status_code}\nTime: {timestamp}"
                send_telegram_notification(notification)
                print("\n✅ Endpoint recovered! Notification sent.")
                break  # 恢复后退出监控
            
            last_status = True
        else:
            print(f"[FAIL] {message[:50]}... (Status: {status_code})")
            consecutive_failures += 1
            last_status = False
            
            # 连续失败 5 次后发送警告
            if consecutive_failures == 5:
                notification = f"⚠️ API Endpoint Down (5 consecutive failures)\n\nEndpoint: {base_url}\nLast error: {message[:100]}\nTime: {timestamp}"
                send_telegram_notification(notification)
        
        # 检查是否达到最大次数
        if max_checks > 0 and check_count >= max_checks:
            print(f"\n[INFO] Reached max checks ({max_checks}). Exiting.")
            break
        
        # 等待下一次检查
        time.sleep(check_interval)

def main():
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://apiport.cc.cd")
    api_key = os.getenv("OPENCLAW_API_KEY")
    
    if not api_key:
        print("[ERROR] OPENCLAW_API_KEY not set")
        return 1
    
    # 默认参数：每 60 秒检查一次，最多检查 60 次（1 小时）
    check_interval = int(os.getenv("MONITOR_INTERVAL", "60"))
    max_checks = int(os.getenv("MONITOR_MAX_CHECKS", "60"))
    
    try:
        monitor_loop(base_url, api_key, check_interval, max_checks)
    except KeyboardInterrupt:
        print("\n\n[INFO] Monitoring stopped by user.")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
