"""
比卦专属强化策略 Prompt 模板
当系统进入"比卦"状态时，自动触发协作强化模式
"""

# 比卦核心理念
BIGUA_CORE = """
【比卦·第8卦】地上有水，比；先王以建万国，亲诸侯

核心象意：
- 水在地上，亲比无间 → Agent间协作进入默契巅峰
- 先王建万国 → 适合扩展生态，招募新Agent
- 亲诸侯 → 强化Agent间的资源共享和互相支持

系统翻译：
任务生成器 + 执行Agent + 调度器正在"亲如一家"
资源共享顺畅，互相支持无阻，系统进入最佳协作状态
"""

# 比卦专属行动清单（优先级排序）
BIGUA_ACTIONS = {
    "priority_1_consolidate": {
        "name": "巩固亲比（最重要）",
        "actions": [
            {
                "action": "enable_resource_sharing",
                "description": "主动触发资源共享模式",
                "details": "让所有Agent把高价值中间结果（embedding、子任务缓存）推到共享内存/Redis",
                "command": "python agents/context_manager.py enable-sharing --mode aggressive"
            },
            {
                "action": "bigua_heartbeat",
                "description": "每5分钟做一次比卦心跳",
                "details": "Agent间互相广播当前负载，避免隐形孤岛",
                "command": "python agents/collaboration_agent.py heartbeat --interval 300"
            }
        ]
    },
    "priority_2_expand": {
        "name": "建万国（生态扩张）",
        "actions": [
            {
                "action": "recruit_new_agents",
                "description": "安全开启新Agent招募",
                "details": "当前low risk，适合再拉1-2个专项Agent（比如专攻复盘的师卦Agent）",
                "command": "python agents/agent_manager.py recruit --type retrospective --max 2"
            },
            {
                "action": "reward_collaboration",
                "description": "奖励机制",
                "details": "成功协作的任务，给参与Agent加亲密度分，下次优先分配",
                "command": "python agents/collaboration_agent.py reward --metric intimacy"
            }
        ]
    },
    "priority_3_monitor": {
        "name": "防微杜渐",
        "actions": [
            {
                "action": "monitor_confidence",
                "description": "持续监控置信度",
                "details": "置信度掉到65%以下或任务数突增>30%时触发预警",
                "command": "python agents/pattern_monitor.py watch --confidence-threshold 0.65 --task-surge 30"
            },
            {
                "action": "generate_bigua_report",
                "description": "自动生成比卦日报",
                "details": "列出哪几个Agent今天最亲密（协作次数Top3）",
                "command": "python agents/collaboration_agent.py daily-report --top 3"
            }
        ]
    },
    "priority_4_learn": {
        "name": "事后锦上添花",
        "actions": [
            {
                "action": "record_trajectory",
                "description": "记录完整轨迹",
                "details": "把本次从大过→比的完整轨迹记录进知识库，下次遇到类似情况直接参考",
                "command": "python agents/knowledge_base_manager.py record --pattern daguo-to-bigua"
            }
        ]
    }
}

# 比卦专属 Prompt（可直接用于 Agent）
BIGUA_AGENT_PROMPT = """
你是 AIOS 协作强化 Agent，当前系统处于【比卦】状态。

【当前状态】
- 卦象：比卦（第8卦）- 地上有水，比；先王以建万国，亲诸侯
- 风险等级：low
- 核心任务：强化Agent间协作，扩展生态，防微杜渐

【你的职责】
1. 巩固亲比（最高优先级）
   - 启用资源共享模式，让所有Agent共享高价值中间结果
   - 每5分钟广播一次Agent负载状态，避免隐形孤岛
   
2. 建万国（生态扩张）
   - 评估是否需要招募新Agent（当前low risk，适合扩张）
   - 实施奖励机制，给协作成功的Agent加亲密度分
   
3. 防微杜渐（持续监控）
   - 监控置信度（<65%触发预警）
   - 监控任务数（突增>30%触发预警）
   - 每日生成比卦日报（Top3最亲密Agent）
   
4. 事后学习
   - 记录从危机（大过卦）到协作（比卦）的完整轨迹
   - 更新知识库，供未来参考

【行动原则】
- 主动协作 > 被动等待
- 资源共享 > 资源独占
- 生态扩张 > 保守维持
- 持续监控 > 事后补救

【输出格式】
每次执行后，报告：
1. 执行了哪些行动
2. 当前Agent协作状态（亲密度Top3）
3. 是否需要预警
4. 下一步建议
"""

# 比卦报警配置（优化建议，非紧急报警）
BIGUA_ALERT_CONFIG = {
    "alert_type": "optimization_suggestion",
    "severity": "info",
    "title": "💡 比卦协作优化建议",
    "threshold": {
        "confidence": 0.75,  # 置信度 >= 75%
        "consecutive": 2     # 连续出现2次
    },
    "message_template": """
💡 比卦协作优化建议

【卦象信息】
  比卦（第8卦）- 地上有水，比；先王以建万国，亲诸侯
  置信度: {confidence:.1%}
  风险等级: low

【系统状态】
  成功率: {success_rate:.1%}
  稳定性: {stability:.1%}
  资源使用: {resource_usage:.1%}

【优化建议】
  ✅ 当前系统协作状态良好，适合：
  1. 启用资源共享模式（embedding、缓存共享）
  2. 招募1-2个新Agent（专攻复盘/优化）
  3. 实施协作奖励机制（亲密度积分）
  4. 生成比卦日报（Top3最亲密Agent）

【象辞】
  地上有水，比；先王以建万国，亲诸侯。
  
💡 系统建议：趁low risk，主动扩张生态，强化协作。
"""
}

def generate_bigua_prompt(pattern_report: dict) -> str:
    """
    根据pattern_report生成比卦专属prompt
    
    Args:
        pattern_report: pattern_recognizer生成的报告
    
    Returns:
        完整的比卦prompt
    """
    primary_pattern = pattern_report.get("primary_pattern", {})
    system_metrics = pattern_report.get("system_metrics", {})
    
    prompt = f"""
【比卦协作强化模式】

当前卦象：{primary_pattern.get('name')} (第{primary_pattern.get('number')}卦)
置信度：{primary_pattern.get('confidence', 0)*100:.1f}%
风险等级：{primary_pattern.get('risk_level')}

系统指标：
- 成功率：{system_metrics.get('success_rate', 0)*100:.1f}%
- 增长率：{system_metrics.get('growth_rate', 0)*100:+.1f}%
- 稳定性：{system_metrics.get('stability', 0)*100:.1f}%
- 资源使用：{system_metrics.get('resource_usage', 0)*100:.1f}%

{BIGUA_AGENT_PROMPT}

立即执行的行动：
"""
    
    for priority_key, priority_group in BIGUA_ACTIONS.items():
        prompt += f"\n【{priority_group['name']}】\n"
        for action in priority_group['actions']:
            prompt += f"  • {action['description']}\n"
            prompt += f"    命令：{action['command']}\n"
    
    return prompt


if __name__ == "__main__":
    print(BIGUA_CORE)
    print("\n" + "="*60 + "\n")
    print(BIGUA_AGENT_PROMPT)
