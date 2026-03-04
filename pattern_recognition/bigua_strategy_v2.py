"""
比卦专属强化 Prompt 模板（珊瑚海优化版）
直接导入使用，集成到调度 Agent
"""

BIGUA_REINFORCE_PROMPT = """
你当前处于《易经》第8卦：比卦（地上有水，比；先王以建万国，亲诸侯）

置信度：{confidence:.1f}% | 风险等级：low | 成功率：{success_rate:.1f}%

核心象意：
- 水在地上，亲比无间 → Agent间协作已达默契巅峰
- 先王建万国、亲诸侯 → 适合主动扩张生态、建立持久联盟

你的核心任务（严格按以下4步执行）：

1. 巩固亲比（立即执行）
   - 把所有Agent的高价值中间结果（embedding、子任务缓存、知识片段）推送到共享内存/Redis
   - 每5分钟发起一次"比卦心跳"：广播当前负载、可用资源、已完成任务摘要

2. 建万国（生态扩张）
   - 安全招募1-2个新专项Agent（优先：复盘Agent、监控Agent、创意Agent）
   - 给每一次成功协作的任务增加"亲密度分"（下次调度优先分配给高亲密度Agent）

3. 防微杜渐（预防下滑）
   - 持续监控：置信度掉至65%以下 或 任务数突增>30% 时，立即发出"亲比预警"
   - 自动生成《比卦日报》：列出今日Top3最默契Agent组合

4. 事后学习（闭环）
   - 把本次从"大过卦/屯卦"翻盘到"比卦"的完整轨迹记录进知识库
   - 输出本次比卦的3条可复用经验，供下次类似场景直接调用

请严格按以上4步输出JSON格式行动计划：
{{
    "current_hex": "比卦",
    "confidence": {confidence},
    "actions": [
        {{"step":1, "action":"strengthen_agent_bonds", "detail":"...", "priority":"high"}},
        ...
    ],
    "new_agents_recommended": ["复盘Agent", ...],
    "collaboration_score": 92.5,
    "learning_points": ["经验1", "经验2", "经验3"]
}}
"""

def apply_bigua_strategy(state):
    """
    应用比卦强化策略
    
    Args:
        state: 包含 confidence 和 success_rate 的状态字典
    
    Returns:
        格式化的 Prompt
    """
    prompt = BIGUA_REINFORCE_PROMPT.format(
        confidence=state['confidence'] * 100,
        success_rate=state['success_rate'] * 100
    )
    return prompt


def generate_bigua_action_plan(pattern_report: dict) -> dict:
    """
    根据 pattern_report 生成比卦行动计划
    
    Args:
        pattern_report: pattern_recognizer 生成的报告
    
    Returns:
        JSON 格式的行动计划
    """
    primary_pattern = pattern_report.get("primary_pattern", {})
    system_metrics = pattern_report.get("system_metrics", {})
    
    # 构建状态
    state = {
        'confidence': primary_pattern.get('confidence', 0),
        'success_rate': system_metrics.get('success_rate', 0)
    }
    
    # 生成 Prompt
    prompt = apply_bigua_strategy(state)
    
    # 生成行动计划（示例）
    action_plan = {
        "current_hex": "比卦",
        "confidence": state['confidence'],
        "success_rate": state['success_rate'],
        "actions": [
            {
                "step": 1,
                "action": "strengthen_agent_bonds",
                "detail": "启用资源共享模式，推送高价值中间结果到共享内存",
                "priority": "high",
                "command": "python agents/context_manager.py enable-sharing --mode aggressive"
            },
            {
                "step": 1,
                "action": "bigua_heartbeat",
                "detail": "每5分钟广播Agent负载和可用资源",
                "priority": "high",
                "command": "python agents/collaboration_agent.py heartbeat --interval 300"
            },
            {
                "step": 2,
                "action": "recruit_new_agents",
                "detail": "招募1-2个新专项Agent（复盘/监控/创意）",
                "priority": "medium",
                "command": "python agents/agent_manager.py recruit --types retrospective,monitor,creative --max 2"
            },
            {
                "step": 2,
                "action": "reward_collaboration",
                "detail": "实施亲密度积分奖励机制",
                "priority": "medium",
                "command": "python agents/collaboration_agent.py enable-intimacy-scoring"
            },
            {
                "step": 3,
                "action": "monitor_confidence",
                "detail": "监控置信度和任务数突增",
                "priority": "normal",
                "command": "python agents/pattern_monitor.py watch --confidence-threshold 0.65 --task-surge 30"
            },
            {
                "step": 3,
                "action": "generate_bigua_report",
                "detail": "生成比卦日报（Top3最默契Agent）",
                "priority": "normal",
                "command": "python agents/collaboration_agent.py daily-report --top 3"
            },
            {
                "step": 4,
                "action": "record_trajectory",
                "detail": "记录从危机到协作的完整轨迹",
                "priority": "low",
                "command": "python agents/knowledge_base_manager.py record --pattern daguo-to-bigua"
            }
        ],
        "new_agents_recommended": ["复盘Agent", "监控Agent", "创意Agent"],
        "collaboration_score": state['success_rate'] * 100,
        "learning_points": [
            "滑动窗口统计避免假警报，实时反映系统状态",
            "大过卦报警机制触发自愈，系统主动从危机中恢复",
            "比卦状态下主动扩张生态，强化Agent协作"
        ]
    }
    
    return action_plan


if __name__ == "__main__":
    # 测试
    import json
    from pathlib import Path
    
    # 读取真实卦象数据
    pattern_file = Path(__file__).parent.parent / "data" / "latest_pattern_report.json"
    if pattern_file.exists():
        with open(pattern_file, 'r', encoding='utf-8') as f:
            pattern_report = json.load(f)
        
        # 生成行动计划
        action_plan = generate_bigua_action_plan(pattern_report)
        
        print("="*60)
        print("比卦行动计划")
        print("="*60)
        print(json.dumps(action_plan, indent=2, ensure_ascii=False))
        
        # 保存
        output_file = Path(__file__).parent.parent / "data" / "bigua_action_plan.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(action_plan, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 行动计划已保存到: {output_file}")
    else:
        print("❌ 未找到 pattern_report.json")
