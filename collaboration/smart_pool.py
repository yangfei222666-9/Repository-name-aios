"""
Smart Agent Pool - 整合学习功能的 Agent 管理
在原有 pool.py 基础上增加：
1. 启动前预检查（agent_precheck）
2. 失败自动降级（agent_fallback）
3. 闭环学习（agent_learning）
"""

import sys
from pathlib import Path

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))
sys.path.insert(0, str(AIOS_ROOT))

from agent_precheck import agent_pre_check, inject_warnings_to_prompt
from agent_fallback import AgentFallback
from agent_learning import AgentLearningLoop

from collaboration.pool import AgentPool, AgentType, PooledAgent


class SmartAgentPool(AgentPool):
    """
    智能 Agent 池，整合学习功能
    """

    def spawn_spec(
        self,
        agent_id: str,
        template: str = "",
        agent_type: AgentType = AgentType.ON_DEMAND,
        capabilities: list = None,
        model: str = "",
        max_tasks: int = 0,
        task_description: str = "",
    ) -> dict:
        """
        生成 spawn 规范，增加学习功能
        """
        # 1. 预检查：检查历史错误
        print(f"🔍 Pre-check: 检查 {agent_id} 的历史错误...")
        check_result = agent_pre_check(task_description)

        if check_result["total_errors"] > 0:
            print(f"⚠️  发现 {check_result['total_errors']} 个历史错误")
            print(f"   {check_result['warnings']}")
        else:
            print(f"✅ 没有发现历史错误")

        # 2. 获取基础 spawn spec
        spec = super().spawn_spec(
            agent_id=agent_id,
            template=template,
            agent_type=agent_type,
            capabilities=capabilities,
            model=model,
            max_tasks=max_tasks,
        )

        # 3. 注入历史教训到 prompt
        learning_loop = AgentLearningLoop(agent_id)
        lessons = learning_loop.get_relevant_lessons(task_description)

        if lessons:
            print(f"📚 找到 {len(lessons)} 条相关教训")
            base_prompt = spec.get("task", "")
            enhanced_prompt = learning_loop.inject_lessons_to_prompt(
                base_prompt, task_description
            )
            spec["task"] = enhanced_prompt

        # 4. 注入预检查警告
        if check_result["total_errors"] > 0:
            base_prompt = spec.get("task", "")
            enhanced_prompt = inject_warnings_to_prompt(base_prompt, check_result)
            spec["task"] = enhanced_prompt

        # 5. 保存任务描述（用于后续学习）
        spec["_task_description"] = task_description
        spec["_agent_id"] = agent_id

        return spec

    def record_result(
        self, agent_id: str, task: str, result: dict, success: bool, error: str = None
    ):
        """
        记录 Agent 执行结果，用于学习
        """
        learning_loop = AgentLearningLoop(agent_id)
        learning_loop.record_execution(task, result, success, error)

        if not success and error:
            print(f"❌ {agent_id} 执行失败: {error}")
            print(f"📝 已记录到学习日志")

    def handle_failure(
        self, agent_id: str, error: str, retry_count: int, current_config: dict
    ) -> dict:
        """
        处理 Agent 失败，自动降级
        返回新的配置，如果无法降级则返回 None
        """
        fallback = AgentFallback(agent_id, current_config)
        strategy = fallback.apply_fallback(error, retry_count)

        if strategy:
            print(f"🔄 {agent_id} 降级策略: {strategy['action']}")
            print(f"   模型: {strategy['model']}")
            print(f"   Thinking: {strategy['thinking']}")
            print(f"   超时: {strategy['timeout']}s")
            if strategy["wait_seconds"] > 0:
                print(f"   等待: {strategy['wait_seconds']}s")
        else:
            print(f"❌ {agent_id} 无法降级，放弃")

        return strategy


# ── CLI 演示 ──

if __name__ == "__main__":
    from collaboration.registry import AgentRegistry

    print("=" * 60)
    print("Smart Agent Pool 演示")
    print("=" * 60)

    # 创建智能池
    registry = AgentRegistry()
    pool = SmartAgentPool(registry)

    # 测试 1: 创建 Agent（带预检查和教训注入）
    print("\n🧪 测试 1: 创建 Agent（带学习功能）")
    spec = pool.spawn_spec(
        agent_id="test-coder-001",
        template="coder",
        task_description="编写一个 Python 网络爬虫",
    )

    print(f"\n生成的 spawn spec:")
    print(f"  模型: {spec.get('model', 'N/A')}")
    print(f"  任务: {spec.get('task', 'N/A')[:200]}...")

    # 测试 2: 记录失败
    print("\n🧪 测试 2: 记录失败")
    pool.record_result(
        agent_id="test-coder-001",
        task="编写 Python 爬虫",
        result={"duration_sec": 10},
        success=False,
        error="Network error: 502 Bad Gateway",
    )

    # 测试 3: 处理失败（自动降级）
    print("\n🧪 测试 3: 处理失败（自动降级）")
    current_config = {"model": "claude-opus-4-6", "thinking": "high", "timeout": 60}

    for retry in range(3):
        print(f"\n重试 {retry + 1}:")
        strategy = pool.handle_failure(
            agent_id="test-coder-001",
            error="Network error: 502 Bad Gateway",
            retry_count=retry,
            current_config=current_config,
        )

        if not strategy:
            break

        # 更新配置
        current_config.update(strategy)

    print("\n" + "=" * 60)
    print("✅ 演示完成")
