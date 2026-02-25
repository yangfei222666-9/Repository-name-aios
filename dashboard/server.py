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
from urllib.parse import urlparse, parse_qs

# 添加路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability import METRICS

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Dashboard HTTP 处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        
        # SSE 端点
        if parsed_path.path == "/api/metrics/stream":
            self.handle_metrics_stream()
        # 静态文件
        else:
            super().do_GET()
    
    def handle_metrics_stream(self):
        """处理指标流（SSE）"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        try:
            while True:
                # 获取最新指标
                snapshot = METRICS.snapshot()
                
                # 转换为简化格式
                data = {
                    "timestamp": int(time.time() * 1000),
                    "counters": {},
                    "gauges": {},
                    "histograms": {}
                }
                
                for counter in snapshot.get("counters", []):
                    key = f"{counter['name']}"
                    if counter.get("labels"):
                        key += f"[{','.join(f'{k}={v}' for k, v in counter['labels'].items())}]"
                    data["counters"][key] = counter["value"]
                
                for gauge in snapshot.get("gauges", []):
                    key = f"{gauge['name']}"
                    if gauge.get("labels"):
                        key += f"[{','.join(f'{k}={v}' for k, v in gauge['labels'].items())}]"
                    data["gauges"][key] = gauge["value"]
                
                for hist in snapshot.get("histograms", []):
                    key = f"{hist['name']}"
                    if hist.get("labels"):
                        key += f"[{','.join(f'{k}={v}' for k, v in hist['labels'].items())}]"
                    data["histograms"][key] = hist["value"]
                
                # 发送 SSE 消息
                message = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                self.wfile.write(message.encode('utf-8'))
                self.wfile.flush()
                
                # 每秒推送一次
                time.sleep(1)
        
        except (BrokenPipeError, ConnectionResetError):
            # 客户端断开连接
            pass
    
    def log_message(self, format, *args):
        """自定义日志"""
        # 只记录非 SSE 请求
        if "/api/metrics/stream" not in self.path:
            super().log_message(format, *args)

def start_server(port=9091):
    """启动 Dashboard 服务器"""
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
        print(f"🌐 AIOS Dashboard 已启动")
        print(f"   访问: http://127.0.0.1:{port}")
        print(f"   实时推送: 已启用（SSE）")
        print(f"\n按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Dashboard 已停止")

if __name__ == "__main__":
    start_server()
