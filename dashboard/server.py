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
            
            # 模拟数据计数器
            demo_counter = 0
            shared_metrics_file = Path(__file__).parent.parent / "data" / "metrics_shared.json"
            
            while True:
                try:
                    data = {
                        "timestamp": int(time.time() * 1000),
                        "counters": {},
                        "gauges": {},
                        "histograms": {}
                    }
                    
                    # 优先读取共享文件（真实数据）
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
                                    
                                    # 添加数据来源标记
                                    data["_source"] = "demo"
                                    data["_age"] = int(age)
                                else:
                                    # 文件过期（>30秒），使用模拟数据
                                    demo_counter += 1
                                    data["counters"] = {
                                        "demo.heartbeats": demo_counter,
                                        "demo.requests": demo_counter * 3,
                                        "demo.events": demo_counter * 2
                                    }
                                    data["gauges"] = {
                                        "demo.cpu": 35 + (demo_counter % 20),
                                        "demo.memory": 60 + (demo_counter % 15),
                                        "demo.connections": 5 + (demo_counter % 10)
                                    }
                                    data["_source"] = "mock"
                        except:
                            # 读取失败，使用模拟数据
                            demo_counter += 1
                            data["counters"] = {
                                "demo.heartbeats": demo_counter,
                                "demo.requests": demo_counter * 3,
                                "demo.events": demo_counter * 2
                            }
                            data["gauges"] = {
                                "demo.cpu": 35 + (demo_counter % 20),
                                "demo.memory": 60 + (demo_counter % 15),
                                "demo.connections": 5 + (demo_counter % 10)
                            }
                            data["_source"] = "mock"
                    else:
                        # 没有共享文件，使用模拟数据
                        demo_counter += 1
                        data["counters"] = {
                            "demo.heartbeats": demo_counter,
                            "demo.requests": demo_counter * 3,
                            "demo.events": demo_counter * 2
                        }
                        data["gauges"] = {
                            "demo.cpu": 35 + (demo_counter % 20),
                            "demo.memory": 60 + (demo_counter % 15),
                            "demo.connections": 5 + (demo_counter % 10)
                        }
                        data["_source"] = "mock"
                    
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
