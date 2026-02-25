"""
简单的测试服务器 - 只为 Pixel Agents 服务
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import subprocess
import json

app = FastAPI()

# 挂载 pixel_view
PIXEL_VIEW_DIR = Path(__file__).parent / "pixel_view"
if PIXEL_VIEW_DIR.exists():
    app.mount("/pixel_view", StaticFiles(directory=str(PIXEL_VIEW_DIR), html=True), name="pixel_view")
    print(f"✅ Pixel view 已挂载: {PIXEL_VIEW_DIR}")
else:
    print(f"❌ Pixel view 目录不存在: {PIXEL_VIEW_DIR}")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Pixel Agents Test Server"}

@app.get("/api/agents/status")
async def get_agents():
    """获取 Agent 状态"""
    try:
        # 直接读取 agents.jsonl 文件
        agents_file = Path(__file__).parent.parent / "agent_system" / "data" / "agents.jsonl"
        
        if not agents_file.exists():
            return JSONResponse({"error": "agents.jsonl not found"}, status_code=404)
        
        # 读取所有 Agent
        lines = agents_file.read_text(encoding="utf-8").strip().split("\n")
        all_agents = [json.loads(line) for line in lines if line.strip()]
        
        # 只保留 active 状态的 Agent
        active_agents = [a for a in all_agents if a.get("status") == "active"]
        
        # 读取任务队列，匹配当前任务
        task_queue_file = Path(__file__).parent.parent / "agent_system" / "task_queue.jsonl"
        current_tasks = {}
        if task_queue_file.exists():
            task_lines = task_queue_file.read_text(encoding="utf-8").strip().split("\n")
            for line in task_lines:
                if line.strip():
                    task = json.loads(line)
                    if task.get("status") == "running":
                        agent_id = task.get("agent_id")
                        if agent_id:
                            current_tasks[agent_id] = task.get("message", "执行中...")
        
        # 按 template 分组
        by_template = {}
        for agent in active_agents:
            template = agent.get("template", "unknown")
            if template not in by_template:
                by_template[template] = []
            
            agent_id = agent.get("id")
            task_desc = agent.get("task_description") or current_tasks.get(agent_id)
            
            by_template[template].append({
                "id": agent_id,
                "name": agent.get("name"),
                "tasks_completed": agent.get("stats", {}).get("tasks_completed", 0),
                "success_rate": agent.get("stats", {}).get("success_rate", 0.0),
                "last_active": agent.get("stats", {}).get("last_active"),
                "current_task": task_desc,
                "status": "running" if task_desc else "idle"
            })
        
        return JSONResponse({
            "summary": {
                "total_agents": len(all_agents),
                "active": len(active_agents),
                "archived": len(all_agents) - len(active_agents),
                "by_template": {k: len(v) for k, v in by_template.items()}
            },
            "active_agents_by_template": by_template
        })
        
    except Exception as e:
        print(f"Error getting agents: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/events/recent")
async def get_events(limit: int = 10):
    """获取最近事件"""
    events_file = Path(__file__).parent.parent / "data" / "events.jsonl"
    if not events_file.exists():
        return JSONResponse({"events": []})
    
    lines = events_file.read_text(encoding="utf-8").strip().split("\n")
    events = [json.loads(line) for line in lines[-limit:] if line.strip()]
    return JSONResponse({"events": events})

if __name__ == "__main__":
    print("=" * 60)
    print("Pixel Agents Test Server")
    print("=" * 60)
    print(f"URL: http://127.0.0.1:9092/pixel_view/")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=9093, log_level="info")
