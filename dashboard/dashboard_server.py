"""
AIOS Dashboard Server - 轻量级 HTTP 服务器
提供 Dashboard 数据 API
"""
import json
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

AIOS_ROOT = Path(__file__).parent.parent


class DashboardHandler(SimpleHTTPRequestHandler):
    """Dashboard HTTP 处理器"""
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        
        # API 路由
        if parsed_path.path == '/api/metrics':
            self.serve_metrics()
        elif parsed_path.path == '/api/traces':
            self.serve_traces()
        elif parsed_path.path == '/api/events':
            self.serve_events()
        elif parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.serve_dashboard()
        else:
            self.send_error(404, "File not found")
    
    def serve_dashboard(self):
        """提供 Dashboard HTML"""
        dashboard_file = AIOS_ROOT / "dashboard" / "index.html"
        
        if not dashboard_file.exists():
            self.send_error(404, "Dashboard not found")
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        with open(dashboard_file, 'rb') as f:
            self.wfile.write(f.read())
    
    def serve_metrics(self):
        """提供 Metrics 数据"""
        try:
            from aios.observability.metrics import METRICS
            data = METRICS.snapshot()
        except Exception as e:
            data = {"error": str(e), "counters": [], "histograms": []}
        
        self.send_json(data)
    
    def serve_traces(self):
        """提供 Traces 数据"""
        traces_dir = AIOS_ROOT / "observability" / "traces"
        traces = []
        
        if traces_dir.exists():
            # 读取最近 10 个 trace 文件
            trace_files = sorted(traces_dir.glob("trace_*.json"), key=os.path.getmtime, reverse=True)[:10]
            
            for trace_file in trace_files:
                try:
                    with open(trace_file, 'r', encoding='utf-8') as f:
                        trace_data = json.load(f)
                        
                        # 提取关键信息
                        if trace_data.get('spans'):
                            root_span = trace_data['spans'][0]
                            traces.append({
                                'trace_id': trace_data['trace_id'],
                                'name': root_span['name'],
                                'duration_ms': root_span.get('duration_ms', 0),
                                'status': root_span.get('status', 'unknown'),
                                'timestamp': trace_data['timestamp']
                            })
                except Exception as e:
                    print(f"Error reading trace file {trace_file}: {e}")
        
        self.send_json(traces)
    
    def serve_events(self):
        """提供 Events 数据"""
        events_file = AIOS_ROOT.parent / "events.jsonl"
        events = []
        
        if events_file.exists():
            try:
                # 读取最后 20 行
                with open(events_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line in lines[-20:]:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except:
                            pass
            except Exception as e:
                print(f"Error reading events: {e}")
        
        # 反转顺序（最新的在前）
        events.reverse()
        
        self.send_json(events)
    
    def send_json(self, data):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[Dashboard] {self.address_string()} - {format % args}")


def start_dashboard(port=8080):
    """启动 Dashboard 服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    print(f"🚀 AIOS Dashboard 启动成功!")
    print(f"📊 访问地址: http://localhost:{port}")
    print(f"🔄 按 Ctrl+C 停止服务器")
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Dashboard 服务器已停止")
        httpd.shutdown()


if __name__ == "__main__":
    import sys
    
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            print("Usage: python dashboard_server.py [port]")
            sys.exit(1)
    
    start_dashboard(port)
