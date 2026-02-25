#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS 真实场景演示 - API 健康检查
展示完整闭环：监控 → 发现 → 修复 → 验证 → 学习
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import http.server
import threading
import urllib.request
import urllib.error

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from observability import span, METRICS, get_logger

logger = get_logger("APIHealthDemo")

# 模拟 API 服务器
class MockAPIHandler(http.server.BaseHTTPRequestHandler):
    """模拟 API 服务器"""
    
    # 控制失败次数
    request_count = 0
    fail_after = 3  # 第3次请求后开始失败
    
    def do_GET(self):
        MockAPIHandler.request_count += 1
        
        if self.path == "/health":
            # 前3次正常，之后失败
            if MockAPIHandler.request_count <= MockAPIHandler.fail_after:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            else:
                # 模拟服务故障
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Internal Server Error"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # 静默日志
        pass

def start_mock_server(port=8888):
    """启动模拟服务器"""
    server = http.server.HTTPServer(("127.0.0.1", port), MockAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def check_api_health(url):
    """检查 API 健康状态"""
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            data = json.loads(response.read().decode())
            return response.status == 200, data
    except urllib.error.HTTPError as e:
        return False, {"status": "error", "code": e.code}
    except Exception as e:
        return False, {"status": "error", "message": str(e)}

def auto_fix_api(url):
    """自动修复 API（模拟重启服务）"""
    logger.info("🔧 触发自动修复", action="restart_service", url=url)
    
    # 模拟修复操作
    time.sleep(1)
    
    # 重置失败计数（模拟服务重启）
    MockAPIHandler.request_count = 0
    
    logger.info("✅ 修复完成", action="restart_service", url=url)
    return True

def print_banner(text):
    """打印横幅"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def main():
    """主函数"""
    print_banner("🚀 AIOS 真实场景演示 - API 健康检查")
    
    # 启动模拟服务器
    print("\n📡 启动模拟 API 服务器...")
    server = start_mock_server(8888)
    api_url = "http://127.0.0.1:8888/health"
    time.sleep(0.5)
    print(f"   ✅ 服务器已启动: {api_url}")
    
    # 监控循环
    print("\n🔍 开始监控 API 健康状态（每 2 秒检查一次）...")
    print("   提示：前 3 次正常，之后会故障，触发自动修复\n")
    
    check_count = 0
    failure_count = 0
    fixed = False
    
    try:
        for i in range(10):  # 检查 10 次
            check_count += 1
            
            with span(f"health-check-{check_count}"):
                # 检查健康状态
                is_healthy, data = check_api_health(api_url)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if is_healthy:
                    print(f"[{timestamp}] ✅ 检查 #{check_count}: 健康 - {data}")
                    METRICS.inc_counter("api.health.success", 1, labels={"url": api_url})
                    failure_count = 0  # 重置失败计数
                else:
                    print(f"[{timestamp}] ❌ 检查 #{check_count}: 故障 - {data}")
                    METRICS.inc_counter("api.health.failure", 1, labels={"url": api_url})
                    failure_count += 1
                    
                    # 连续失败 2 次，触发自动修复
                    if failure_count >= 2 and not fixed:
                        print(f"\n{'='*70}")
                        print("  🚨 检测到连续故障，触发 AIOS 自动修复...")
                        print(f"{'='*70}\n")
                        
                        with span("auto-fix"):
                            success = auto_fix_api(api_url)
                            
                            if success:
                                print("\n   ✅ 自动修复成功！")
                                METRICS.inc_counter("api.auto_fix.success", 1, labels={"url": api_url})
                                fixed = True
                                failure_count = 0
                            else:
                                print("\n   ❌ 自动修复失败")
                                METRICS.inc_counter("api.auto_fix.failure", 1, labels={"url": api_url})
                        
                        print(f"\n{'='*70}")
                        print("  🔄 继续监控...")
                        print(f"{'='*70}\n")
                
                # 记录响应时间
                METRICS.observe("api.response_time", 0.05, labels={"url": api_url})
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  监控已停止")
    
    finally:
        server.shutdown()
    
    # 显示统计
    print_banner("📊 监控统计")
    
    snapshot = METRICS.snapshot()
    
    success_count = 0
    failure_count_total = 0
    fix_success = 0
    
    for counter in snapshot.get("counters", []):
        if counter["name"] == "api.health.success":
            success_count = counter["value"]
        elif counter["name"] == "api.health.failure":
            failure_count_total = counter["value"]
        elif counter["name"] == "api.auto_fix.success":
            fix_success = counter["value"]
    
    total_checks = success_count + failure_count_total
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n✅ 总检查次数: {total_checks}")
    print(f"✅ 成功次数: {int(success_count)}")
    print(f"❌ 失败次数: {int(failure_count_total)}")
    print(f"📈 成功率: {success_rate:.1f}%")
    print(f"🔧 自动修复次数: {int(fix_success)}")
    
    print_banner("✅ 演示完成！")
    
    print("\n💡 这个演示展示了 AIOS 的核心能力：")
    print("   1. 🔍 持续监控 - 每 2 秒检查 API 健康状态")
    print("   2. 🚨 故障检测 - 连续失败 2 次触发告警")
    print("   3. 🔧 自动修复 - 自动重启服务（模拟）")
    print("   4. ✅ 验证恢复 - 修复后继续监控，确认恢复")
    print("   5. 📊 数据记录 - 所有事件记录到 Metrics 和 Logger")
    
    print("\n📁 查看详细数据：")
    print("   • 日志: aios/logs/aios.jsonl")
    print("   • 指标: METRICS.snapshot()")
    print("   • Dashboard: python aios.py dashboard")

if __name__ == "__main__":
    main()
