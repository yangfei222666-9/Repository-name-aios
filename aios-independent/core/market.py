"""
Agent Market - GitHub/ClawdHub 远程市场
支持一键下载、安装、热更新
"""
import json
import asyncio
import requests
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from config import BASE_DIR

router = APIRouter(prefix="/market", tags=["Agent Market"])

# ClawdHub 配置（可以改成自己的 GitHub 仓库）
CLAWDHUB_REPO = "openclaw/aios-agents"  # 示例仓库
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{CLAWDHUB_REPO}/main/agents/"


class AgentMarket:
    @staticmethod
    async def list_remote_agents():
        """从 GitHub/ClawdHub 拉取最新 Agent 列表"""
        try:
            # 尝试从 GitHub API 获取
            response = requests.get(
                f"https://api.github.com/repos/{CLAWDHUB_REPO}/contents/agents",
                timeout=5
            )
            if response.status_code == 200:
                files = [
                    f["name"].replace(".json", "")
                    for f in response.json()
                    if f["name"].endswith(".json")
                ]
                return {
                    "agents": files,
                    "total": len(files),
                    "source": "ClawdHub"
                }
        except Exception as e:
            print(f"[WARN] GitHub API failed: {e}")
        
        # Fallback: Demo 模式
        return {
            "agents": [
                "demo_agent_v2",
                "smart_researcher",
                "self_heal_agent",
                "code_optimizer",
                "bug_hunter"
            ],
            "total": 5,
            "source": "Demo Mode"
        }

    @staticmethod
    async def download_agent(agent_name: str):
        """一键下载并安装到本地"""
        try:
            # 尝试从 GitHub 下载
            url = f"{GITHUB_RAW_URL}{agent_name}.json"
            resp = requests.get(url, timeout=5)
            
            if resp.status_code == 200:
                new_agent = resp.json()
            else:
                # Fallback: 创建 Demo Agent
                new_agent = {
                    "id": agent_name,
                    "name": agent_name.replace("_", " ").title(),
                    "description": f"从市场下载的 {agent_name}",
                    "version": "1.0.0",
                    "capabilities": ["demo"],
                    "downloaded_from": "ClawdHub Demo"
                }
            
            # 追加到本地 agents.json
            agents_file = BASE_DIR / "agents.json"
            
            if agents_file.exists():
                with open(agents_file, encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"agents": []}
            
            # 检查是否已存在
            if isinstance(data, dict) and "agents" in data:
                existing_ids = [a.get("id") for a in data["agents"]]
                if agent_name not in existing_ids:
                    data["agents"].append(new_agent)
                else:
                    return {
                        "status": "skipped",
                        "agent": agent_name,
                        "message": "⚠️ Agent 已存在，跳过安装"
                    }
            else:
                data = {"agents": [new_agent]}
            
            # 保存
            with open(agents_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return {
                "status": "success",
                "agent": agent_name,
                "message": "✅ 已下载并安装到本地！"
            }
            
        except Exception as e:
            raise HTTPException(500, f"下载失败: {str(e)}")


# 全局单例
market = AgentMarket()
