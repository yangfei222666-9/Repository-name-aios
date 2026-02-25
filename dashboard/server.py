#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS Dashboard Server - 实时推送版本
使用 Server-Sent Events (SSE) 实现零依赖实时推送
"""
import http.server
import socketserver
import json
import time
import threading
from pathlib import Path
from urllib.parse import urlparse

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability import METRICS

# 允许端口复用
socketserver.TCPServer.allow_reuse_address = True

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Dashboard HTTP 处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/api/metrics/stream":
            self.handle_metrics_stream()
        elif parsed_path.path == "/api/events":
            self.handle_events()
        else:
            super().do_GET()
    
    def handle_events(self):
        """处理事件历史请求"""
        try:
            # 读取最近的事件
            events_file = Path(__file__).parent.parent / "data" / "events.jsonl"
            events = []
            
            if events_file.exists():
                with open(events_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # 只返回最近100条
                    for line in lines[-100:]:
                        try:
                            event = json.loads(line.strip())
                            events.append(event)
                        except:
                            pass
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(events, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def handle_metrics_stream(self):
        """处理指标流（SSE）"""
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            shared_metrics_file = Path(__file__).parent.parent / "data" / "metrics_shared.json"
            aios_events_file = Path(__file__).parent.parent / "data" / "events.jsonl"
            
            while True:
                try:
                    data = {
                        "timestamp": int(time.time() * 1000),
                        "counters": {},
                        "gauges": {},
                        "histograms": {},
                        "_source": "aios"
                    }
                    
                    # 优先读取共享文件（Demo 真实数据）
                    demo_data_loaded = False
                    if shared_metrics_file.exists():
                        try:
                            with open(shared_metrics_file, "r", encoding="utf-8") as f:
                                shared_data = json.load(f)
                                
                                # 检查文件是否新鲜（30秒内）
                                snapshot_at = shared_data.get("snapshot_at", 0)
                                age = time.time() - snapshot_at
                                
                                if age < 30:
                                    # 使用共享文件的真实数据
                                    for counter in shared_data.get("counters", []):
                                        key = counter["name"]
                                        if counter.get("labels"):
                                            key += f"[{','.join(f'{k}={v}' for k, v in counter['labels'].items())}]"
                                        data["counters"][key] = counter["value"]
                                    
                                    for gauge in shared_data.get("gauges", []):
                                        key = gauge["name"]
                                        if gauge.get("labels"):
                                            key += f"[{','.join(f'{k}={v}' for k, v in gauge['labels'].items())}]"
                                        data["gauges"][key] = gauge["value"]
                                    
                                    for hist in shared_data.get("histograms", []):
                                        key = hist["name"]
                                        if hist.get("labels"):
                                            key += f"[{','.join(f'{k}={v}' for k, v in hist['labels'].items())}]"
                                        data["histograms"][key] = hist["value"]
                                    
                                    data["_source"] = "demo"
                                    data["_age"] = int(age)
                                    demo_data_loaded = True
                        except:
                            pass
                    
                    # 如果没有 Demo 数据，显示 AIOS 系统数据
                    if not demo_data_loaded:
                        # 读取 AIOS 事件统计
                        if aios_events_file.exists():
                            try:
                                with open(aios_events_file, "r", encoding="utf-8") as f:
                                    lines = f.readlines()
                                    total_events = len(lines)
                                    
                                    # 统计最近1小时的事件
                                    recent_events = 0
                                    error_events = 0
                                    success_events = 0
                                    
                                    current_time = time.time()
                                    for line in lines[-1000:]:  # 最近1000条
                                        try:
                                            event = json.loads(line.strip())
                                            event_time = event.get("timestamp", 0)
                                            if current_time - event_time < 3600:  # 1小时内
                                                recent_events += 1
                                                if event.get("level") == "error":
                                                    error_events += 1
                                                else:
                                                    success_events += 1
                                        except:
                                            pass
                                    
                                    data["counters"] = {
                                        "aios.events.total": total_events,
                                        "aios.events.recent_1h": recent_events,
                                        "aios.events.errors": error_events,
                                        "aios.events.success": success_events
                                    }
                                    
                                    # 计算成功率
                                    if recent_events > 0:
                                        success_rate = (success_events / recent_events) * 100
                                        data["gauges"]["aios.success_rate"] = round(success_rate, 1)
                            except:
                                pass
                        
                        # 如果连 AIOS 数据都没有，显示提示
                        if not data["counters"]:
                            data["counters"] = {
                                "aios.status": 1
                            }
                            data["gauges"] = {
                                "aios.uptime": int(time.time() % 86400)
                            }
                            data["_source"] = "system"
                    
                    message = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    self.wfile.write(message.encode('utf-8'))
                    self.wfile.flush()
                    
                    time.sleep(1)
                    
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
                    break
        except Exception:
            pass
    
    def log_message(self, format, *args):
        if "/api/metrics/stream" not in str(args):
            super().log_message(format, *args)

def start_server(port=9091, open_browser=False):
    """启动 Dashboard 服务器"""
    try:
        with socketserver.ThreadingTCPServer(("", port), DashboardHandler) as httpd:
            url = f"http://127.0.0.1:{port}"
            print(f"🌐 AIOS Dashboard 已启动")
            print(f"   访问: {url}")
            print(f"   实时推送: 已启用（SSE）")
            print(f"\n按 Ctrl+C 停止服务器")
            
            # 自动打开浏览器（默认关闭，由 aios.py 控制）
            if open_browser:
                import webbrowser
                threading.Timer(1.0, lambda: webbrowser.open(url)).start()
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard 已停止")
    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            print(f"❌ 端口 {port} 已被占用，尝试 {port + 1}...")
            start_server(port + 1, open_browser)
        else:
            raise

if __name__ == "__main__":
    start_server()
