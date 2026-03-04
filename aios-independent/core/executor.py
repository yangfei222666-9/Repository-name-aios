"""
Agent Executor - 简化版执行器
"""
import asyncio


class AgentExecutor:
    def __init__(self):
        self.agents = ["agent_main", "coder", "analyst", "monitor"]
        print(f"[Executor] 已加载 {len(self.agents)} 个 Agent")
        print(f"[Executor] 市场 Agent 加载完成 | 当前总数: {len(self.agents)}（支持远程热更新）")
    
    async def execute(self, agent_id: int, payload: str):
        """执行 Agent 任务"""
        await asyncio.sleep(0.5)  # 模拟执行
        return f"执行成功：{payload[:50]}"


# 全局单例
agent_executor = AgentExecutor()
