"""
Collaboration Layer Demo - 端到端演示

场景：用户提交一个"分析代码质量"任务
1. 注册 3 个专业 Agent（coder, reviewer, researcher）
2. 主 Agent 拆分任务为 3 个子任务（有依赖关系）
3. 自动分配给最佳 Agent
4. 模拟执行 + 返回结果
5. 关键决策走投票共识
6. 汇总最终报告
"""

import json
import time
import shutil
from pathlib import Path

# 清理旧数据
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "collaboration"
if DATA_DIR.exists():
    shutil.rmtree(DATA_DIR)

from .registry import AgentRegistry, AgentProfile
from .messenger import Messenger, MsgType
from .delegator import Delegator
from .consensus import Consensus, Protocol, cross_check
from .pool import AgentPool, AgentType

SEP = "─" * 50


def demo():
    print(f"\n{'═' * 50}")
    print("  🤖 AIOS Collaboration Layer v0.1.0 Demo")
    print(f"{'═' * 50}\n")

    # ── Step 1: 初始化 ──
    print(f"{SEP}")
    print("📋 Step 1: 注册 Agent")
    print(f"{SEP}")

    registry = AgentRegistry()
    pool = AgentPool(registry)

    # 用模板生成 3 个专业 Agent
    agents = {}
    for name in ["coder", "reviewer", "researcher"]:
        spec = pool.spawn_spec(
            f"agent_{name}", template=name, agent_type=AgentType.ON_DEMAND
        )
        pool.mark_ready(f"agent_{name}", session_key=f"session_{name}")
        agents[name] = spec
        print(
            f"  ✅ {spec['agent_id']:20s}  能力={spec['capabilities']}  模型={spec['model']}"
        )

    print(f"\n  Registry 总计: {len(registry.list_all())} agents")

    # ── Step 2: 消息传递 ──
    print(f"\n{SEP}")
    print("💬 Step 2: Agent 间通信")
    print(f"{SEP}")

    m_orchestrator = Messenger("orchestrator")
    m_coder = Messenger("agent_coder")
    m_reviewer = Messenger("agent_reviewer")

    # orchestrator 给 coder 发请求
    msg = m_orchestrator.request(
        "agent_coder", {"action": "analyze", "target": "main.py"}
    )
    print(f"  📤 orchestrator → agent_coder: {msg.payload}")

    # orchestrator 广播通知
    m_orchestrator.broadcast({"event": "new_delegation", "id": "demo_001"})
    print(f"  📢 orchestrator → *: 广播新任务通知")

    # coder 收消息
    inbox = m_coder.receive()
    print(f"  📥 agent_coder 收到 {len(inbox)} 条消息:")
    for m in inbox:
        print(f"      [{m.msg_type}] from={m.sender} → {m.payload}")

    # reviewer 也收到广播
    inbox2 = m_reviewer.receive()
    print(f"  📥 agent_reviewer 收到 {len(inbox2)} 条消息:")
    for m in inbox2:
        print(f"      [{m.msg_type}] from={m.sender} → {m.payload}")

    # ── Step 3: 任务拆分与分配 ──
    print(f"\n{SEP}")
    print("🔀 Step 3: 任务拆分 + 自动分配")
    print(f"{SEP}")

    delegator = Delegator(registry)

    # 创建一个复杂任务，拆成 3 个子任务（有依赖）
    dlg = delegator.create_delegation(
        description="分析项目代码质量并生成报告",
        subtask_specs=[
            {
                "description": "扫描代码结构，统计文件/函数/类数量",
                "caps": ["code"],
                "priority": 1,
            },
            {
                "description": "搜索业界最佳实践作为对比基准",
                "caps": ["research"],
                "priority": 2,
            },
            {
                "description": "审查代码风格、安全漏洞、性能问题",
                "caps": ["review"],
                "priority": 3,
                "depends_on": [],  # 可以并行
            },
        ],
        requester="user",
    )

    print(f"  📦 创建委派: {dlg.delegation_id}")
    print(f"  📝 子任务数: {len(dlg.subtasks)}")

    # 自动分配
    assigned = delegator.assign_ready_tasks(dlg.delegation_id)
    print(f"  🎯 已分配: {len(assigned)} 个任务")
    for t in assigned:
        print(f"      {t.task_id} → {t.assigned_to} ({t.description[:40]}...)")

    # ── Step 4: 模拟执行 ──
    print(f"\n{SEP}")
    print("⚡ Step 4: 模拟执行")
    print(f"{SEP}")

    # 模拟各 agent 完成任务
    results = {
        0: {
            "files": 42,
            "functions": 156,
            "classes": 23,
            "lines": 4800,
            "test_coverage": "78%",
        },
        1: {
            "benchmarks": ["Google Style Guide", "PEP 8", "OWASP Top 10"],
            "score": "B+",
        },
        2: {
            "issues": 7,
            "critical": 1,
            "warnings": 6,
            "style_score": 85,
            "security_score": 92,
        },
    }

    for i in range(3):
        task_id = f"{dlg.delegation_id}_{i}"
        task = delegator._tasks[task_id]
        task.status = "running"
        print(f"  ⏳ {task.assigned_to} 执行中: {task.description[:40]}...")
        time.sleep(0.1)  # 模拟耗时
        delegator.update_task(task_id, "done", result=results[i])
        pool.mark_done(task.assigned_to)
        print(
            f"  ✅ {task.assigned_to} 完成! 结果: {json.dumps(results[i], ensure_ascii=False)[:60]}..."
        )

    # 查看状态
    status = delegator.get_status(dlg.delegation_id)
    print(f"\n  📊 委派状态: {status['status']}  进度: {status['progress']}")

    # ── Step 5: 共识投票 ──
    print(f"\n{SEP}")
    print("🗳️ Step 5: 共识投票 — 代码质量评级")
    print(f"{SEP}")

    # 3 个 agent 对代码质量评级投票
    result = cross_check(
        question="项目代码质量评级",
        agent_results={
            "agent_coder": "B+",
            "agent_reviewer": "B+",
            "agent_researcher": "A-",
        },
        protocol=Protocol.MAJORITY,
    )

    print(f"  🏷️ 问题: {result['question']}")
    print(f"  📊 投票结果:")
    for d in result["details"]:
        print(f"      {d['voter']:20s} → {d['choice']}")
    print(f"  🏆 共识决定: {result['decision']}  (协议: MAJORITY)")
    print(f"  📈 状态: {result['status']}")

    # ── Step 6: 加权投票 demo ──
    print(f"\n{SEP}")
    print("⚖️ Step 6: 加权投票 — 是否重构")
    print(f"{SEP}")

    consensus = Consensus()
    req = consensus.create_request(
        question="是否需要重构核心模块？",
        options=["重构", "不重构", "部分重构"],
        protocol=Protocol.WEIGHTED,
        min_voters=3,
        weights={"agent_coder": 2.0, "agent_reviewer": 1.5, "agent_researcher": 0.5},
    )

    consensus.cast_vote(
        req,
        "agent_coder",
        "部分重构",
        confidence=0.9,
        reasoning="核心逻辑OK，边缘模块需要清理",
    )
    consensus.cast_vote(
        req,
        "agent_reviewer",
        "部分重构",
        confidence=0.8,
        reasoning="安全问题集中在2个模块",
    )
    consensus.cast_vote(
        req,
        "agent_researcher",
        "重构",
        confidence=0.6,
        reasoning="业界趋势倾向微服务化",
    )

    wr = consensus.get_result(req)
    print(f"  🏷️ 问题: {wr['question']}")
    print(f"  📊 投票详情:")
    for d in wr["details"]:
        print(
            f"      {d['voter']:20s} → {d['choice']:8s}  信心={d['confidence']:.1f}  理由: {d['reasoning']}"
        )
    print(f"  🏆 加权决定: {wr['decision']}")

    # ── Step 7: Pool 统计 ──
    print(f"\n{SEP}")
    print("📈 Step 7: Agent Pool 统计")
    print(f"{SEP}")

    stats = pool.stats()
    print(f"  总 Agent 数: {stats['total']}")
    print(f"  就绪: {stats['ready']}  忙碌: {stats['busy']}  停止: {stats['stopped']}")
    print(f"  总完成任务: {stats['total_tasks']}")

    # ── 最终报告 ──
    print(f"\n{'═' * 50}")
    print("  📋 最终汇总报告")
    print(f"{'═' * 50}")

    dlg_obj = delegator.get_delegation(dlg.delegation_id)
    if dlg_obj and dlg_obj.aggregated_result:
        agg = dlg_obj.aggregated_result
        print(f"  子任务数: {agg['subtask_count']}")
        print(f"  总耗时: {agg['total_time']:.2f}s")
        print(f"  代码质量共识: {result['decision']}")
        print(f"  重构建议共识: {wr['decision']}")
        print(f"\n  ✅ 所有模块协作完成！")

    print(f"\n{'═' * 50}\n")


if __name__ == "__main__":
    demo()
