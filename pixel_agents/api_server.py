"""
AIOS Pixel Agents API Server
提供 REST API 供前端调用

安全注意：
- 所有路径参数经过 sanitize 防止路径遍历
- POST body 限制 1MB 防止 DoS
- JSON 解析异常返回 400 而非 500
"""

import json
import re
import sys
import logging
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# 添加 AIOS 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import AgentSystem
from core.event_bus import EventBus

logger = logging.getLogger("aios.api_server")

# 安全常量
MAX_BODY_SIZE = 1 * 1024 * 1024  # 1MB
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


def _sanitize_id(raw_id: str) -> str:
    """校验并返回安全的 ID，不合法则抛 ValueError"""
    if not SAFE_ID_PATTERN.match(raw_id):
        raise ValueError(f"Invalid ID format: {raw_id!r}")
    return raw_id


class APIHandler(BaseHTTPRequestHandler):
    """API 请求处理器"""

    def _send_json(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_error(self, message, status=400):
        """发送错误响应"""
        self._send_json({"error": message}, status)

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        try:
            if path == "/api/agents":
                self._handle_list_agents()
            elif path == "/api/agents/stats":
                self._handle_agent_stats()
            elif path.startswith("/api/agents/") and path.endswith("/evolution"):
                agent_id = _sanitize_id(path.split("/")[3])
                self._handle_agent_evolution(agent_id)
            elif path.startswith("/api/agents/") and path.endswith("/report"):
                agent_id = _sanitize_id(path.split("/")[3])
                self._handle_evolution_report(agent_id)
            elif path == "/api/tasks":
                self._handle_list_tasks()
            elif path == "/api/events":
                self._handle_list_events(query)
            elif path == "/api/alerts":
                self._handle_list_alerts()
            elif path == "/api/system/health":
                self._handle_system_health()
            elif path == "/api/evolution/events":
                self._handle_evolution_events()
            else:
                self._send_error("Not Found", 404)
        except ValueError as e:
            self._send_error(str(e), 400)
        except Exception as e:
            logger.exception("GET %s failed", path)
            self._send_error("Internal Server Error", 500)

    def do_POST(self):
        """处理 POST 请求"""
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            # 读取请求体（限制大小）
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > MAX_BODY_SIZE:
                self._send_error("Request body too large", 413)
                return
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError as e:
                self._send_error(f"Invalid JSON: {e}", 400)
                return

            if path == "/api/agents/create":
                self._handle_create_agent(data)
            elif path == "/api/tasks/submit":
                self._handle_submit_task(data)
            elif path.startswith("/api/agents/") and path.endswith("/evolve"):
                agent_id = _sanitize_id(path.split("/")[3])
                self._handle_trigger_evolution(agent_id)
            elif path.startswith("/api/alerts/") and path.endswith("/ack"):
                alert_id = _sanitize_id(path.split("/")[3])
                self._handle_ack_alert(alert_id)
            elif path.startswith("/api/alerts/") and path.endswith("/resolve"):
                alert_id = _sanitize_id(path.split("/")[3])
                self._handle_resolve_alert(alert_id)
            else:
                self._send_error("Not Found", 404)
        except ValueError as e:
            self._send_error(str(e), 400)
        except Exception as e:
            logger.exception("POST %s failed", path)
            self._send_error("Internal Server Error", 500)

    def _handle_list_agents(self):
        """列出所有 Agents"""
        # 直接读取 Agent System 的数据文件（JSONL 格式）
        agents_file = Path(__file__).parent.parent / "agent_system" / "data" / "agents.jsonl"
        
        agents = []
        if agents_file.exists():
            with open(agents_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        agent = json.loads(line)
                        # 只返回 active 的 Agent
                        if agent.get("status") == "active":
                            agents.append(agent)
        
        self._send_json({"agents": agents})

    def _handle_agent_stats(self):
        """Agent 统计信息"""
        # 直接读取 Agent System 的数据文件（JSONL 格式）
        agents_file = Path(__file__).parent.parent / "agent_system" / "data" / "agents.jsonl"
        
        agents = []
        if agents_file.exists():
            with open(agents_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        agent = json.loads(line)
                        # 只统计 active 的 Agent
                        if agent.get("status") == "active":
                            agents.append(agent)

        stats = {
            "total": len(agents),
            "active": len(agents),  # 所有返回的都是 active 的
            "by_state": {},
            "by_template": {},
        }

        for agent in agents:
            state = agent.get("state", "idle")
            template = agent.get("template", "unknown")

            stats["by_state"][state] = stats["by_state"].get(state, 0) + 1
            stats["by_template"][template] = stats["by_template"].get(template, 0) + 1

        self._send_json(stats)

    def _handle_list_tasks(self):
        """列出任务队列"""
        task_file = Path(__file__).parent.parent / "agent_system" / "task_queue.jsonl"

        tasks = []
        if task_file.exists():
            with open(task_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        tasks.append(json.loads(line))

        self._send_json({"tasks": tasks[-50:]})  # 最近 50 个

    def _handle_list_events(self, query):
        """列出事件"""
        try:
            limit = min(int(query.get("limit", [50])[0]), 500)  # 上限 500 防止 OOM
        except (ValueError, IndexError):
            limit = 50
        event_file = Path(__file__).parent.parent / "data" / "events.jsonl"

        events = []
        if event_file.exists():
            with open(event_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))

        # 按时间倒序
        events.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        self._send_json({"events": events[:limit]})

    def _handle_list_alerts(self):
        """列出告警"""
        alert_file = Path(__file__).parent.parent / "core" / "alerts.jsonl"

        alerts = []
        if alert_file.exists():
            with open(alert_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        alert = json.loads(line)
                        if alert.get("state") != "RESOLVED":
                            alerts.append(alert)

        self._send_json({"alerts": alerts})

    def _handle_system_health(self):
        """系统健康状态"""
        # 读取最新的 evolution_score
        baseline_file = Path(__file__).parent.parent / "learning" / "baseline.jsonl"

        score = 0.0
        grade = "unknown"

        if baseline_file.exists():
            with open(baseline_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last = json.loads(lines[-1])
                    score = last.get("evolution_score", 0.0)
                    grade = last.get("grade", "unknown")

        self._send_json(
            {
                "evolution_score": score,
                "grade": grade,
                "timestamp": int(datetime.now().timestamp()),
            }
        )

    def _handle_agent_evolution(self, agent_id):
        """获取 Agent 进化状态"""
        from agent_system.evolution import AgentEvolution
        
        evolution = AgentEvolution()
        analysis = evolution.analyze_failures(agent_id, lookback_hours=24)
        history = evolution.get_evolution_history(agent_id, limit=5)
        pending = evolution.get_pending_suggestions(agent_id)
        
        self._send_json({
            "agent_id": agent_id,
            "analysis": analysis,
            "history": history,
            "pending_suggestions": pending
        })

    def _handle_evolution_report(self, agent_id):
        """生成进化报告"""
        from agent_system.evolution import AgentEvolution
        
        evolution = AgentEvolution()
        report = evolution.generate_evolution_report(agent_id)
        
        self._send_json({
            "agent_id": agent_id,
            "report": report
        })

    def _handle_trigger_evolution(self, agent_id):
        """手动触发进化"""
        from agent_system.auto_evolution import AutoEvolution
        from agent_system.core.agent_manager import AgentManager
        
        auto_evolution = AutoEvolution()
        agent_manager = AgentManager()
        
        result = auto_evolution.auto_evolve(agent_id, agent_manager)
        self._send_json(result)

    def _handle_evolution_events(self):
        """获取最近的进化事件"""
        events_file = Path.home() / ".openclaw" / "workspace" / "aios" / "data" / "events.jsonl"
        
        if not events_file.exists():
            self._send_json({"events": []})
            return
        
        # 读取最近 100 条进化事件
        evolution_events = []
        with open(events_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get("type", "").startswith("evolution."):
                        evolution_events.append(event)
                except:
                    continue
        
        # 只返回最近 100 条
        evolution_events = evolution_events[-100:]
        
        self._send_json({"events": evolution_events})

    def _handle_create_agent(self, data):
        """创建 Agent"""
        template = data.get("template", "")
        task = data.get("task", "")

        ALLOWED_TEMPLATES = {"coder", "analyst", "monitor", "researcher"}
        if not template:
            self._send_error("Missing template")
            return
        if template not in ALLOWED_TEMPLATES:
            self._send_error(f"Invalid template. Allowed: {', '.join(sorted(ALLOWED_TEMPLATES))}")
            return
        if len(task) > 2000:
            self._send_error("Task description too long (max 2000 chars)")
            return

        system = AgentSystem()
        agent = system.manager.create_agent(template, task)

        self._send_json({"success": True, "agent": agent})

    def _handle_submit_task(self, data):
        """提交任务"""
        message = data.get("message")

        if not message:
            self._send_error("Missing message")
            return

        system = AgentSystem()
        result = system.handle_task(message, auto_create=True)

        self._send_json(result)

    def _handle_ack_alert(self, alert_id):
        """确认告警"""
        alert_file = Path(__file__).parent.parent / "core" / "alerts.jsonl"

        if not alert_file.exists():
            self._send_error("Alert not found", 404)
            return

        # 读取所有告警
        alerts = []
        with open(alert_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    alerts.append(json.loads(line))

        # 更新状态
        found = False
        for alert in alerts:
            if alert.get("id") == alert_id:
                alert["state"] = "ACKNOWLEDGED"
                alert["acked_at"] = int(datetime.now().timestamp())
                found = True
                break

        if not found:
            self._send_error("Alert not found", 404)
            return

        # 写回文件
        with open(alert_file, "w", encoding="utf-8") as f:
            for alert in alerts:
                f.write(json.dumps(alert, ensure_ascii=False) + "\n")

        self._send_json({"success": True})

    def _handle_resolve_alert(self, alert_id):
        """解决告警"""
        alert_file = Path(__file__).parent.parent / "core" / "alerts.jsonl"

        if not alert_file.exists():
            self._send_error("Alert not found", 404)
            return

        # 读取所有告警
        alerts = []
        with open(alert_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    alerts.append(json.loads(line))

        # 更新状态
        found = False
        for alert in alerts:
            if alert.get("id") == alert_id:
                alert["state"] = "RESOLVED"
                alert["resolved_at"] = int(datetime.now().timestamp())
                found = True
                break

        if not found:
            self._send_error("Alert not found", 404)
            return

        # 写回文件
        with open(alert_file, "w", encoding="utf-8") as f:
            for alert in alerts:
                f.write(json.dumps(alert, ensure_ascii=False) + "\n")

        self._send_json({"success": True})

    def log_message(self, format, *args):
        """禁用默认日志"""
        pass


def run_server(port=9092):
    """启动 API 服务器"""
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"AIOS Pixel Agents API Server running on http://localhost:{port}")
    print(f"Dashboard: file:///{Path(__file__).parent}/dashboard_v3.html")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
