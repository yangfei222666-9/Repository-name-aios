"""
Hexagram Patterns - 64卦系统状态映射表
将易经64卦映射到AIOS系统状态和应对策略
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class HexagramPattern:
    """卦象模式"""
    name: str              # 卦名
    number: int            # 卦序（1-64）
    description: str       # 描述
    system_state: Dict     # 系统状态特征
    strategy: Dict         # 应对策略
    risk_level: str        # 风险等级（low/medium/high/critical）


# 64卦完整映射表
HEXAGRAM_PATTERNS = {
    # ===== 第一组：创业期（1-8卦）=====
    1: HexagramPattern(
        name="乾卦",
        number=1,
        description="天行健，君子以自强不息",
        system_state={
            "success_rate": (0.8, 1.0),      # 高成功率
            "growth_rate": (0.1, 0.5),       # 快速增长
            "stability": (0.7, 1.0),         # 高稳定性
            "resource_usage": (0.3, 0.6),    # 中等资源使用
        },
        strategy={
            "priority": "expansion",          # 扩张优先
            "actions": [
                "try_challenging_tasks",      # 尝试挑战性任务
                "explore_new_capabilities",   # 探索新能力
                "optimize_for_speed",         # 优化速度
            ],
            "model_preference": "opus",       # 使用高性能模型
            "risk_tolerance": "high",         # 高风险容忍度
        },
        risk_level="low"
    ),
    
    2: HexagramPattern(
        name="坤卦",
        number=2,
        description="地势坤，君子以厚德载物",
        system_state={
            "success_rate": (0.7, 0.9),
            "growth_rate": (-0.1, 0.1),      # 平稳增长
            "stability": (0.8, 1.0),         # 极高稳定性
            "resource_usage": (0.2, 0.4),    # 低资源使用
        },
        strategy={
            "priority": "stability",          # 稳定优先
            "actions": [
                "maintain_current_state",     # 保持现状
                "accumulate_resources",       # 积累资源
                "strengthen_foundation",      # 加强基础
            ],
            "model_preference": "sonnet",     # 使用平衡模型
            "risk_tolerance": "low",          # 低风险容忍度
        },
        risk_level="low"
    ),
    
    3: HexagramPattern(
        name="屯卦",
        number=3,
        description="云雷屯，君子以经纶",
        system_state={
            "success_rate": (0.3, 0.6),      # 中低成功率
            "growth_rate": (-0.2, 0.2),      # 波动增长
            "stability": (0.2, 0.5),         # 低稳定性
            "resource_usage": (0.5, 0.8),    # 高资源使用
        },
        strategy={
            "priority": "survival",           # 生存优先
            "actions": [
                "reduce_task_complexity",     # 降低任务复杂度
                "increase_retry_attempts",    # 增加重试次数
                "seek_external_help",         # 寻求外部帮助
                "focus_on_core_tasks",        # 专注核心任务
            ],
            "model_preference": "haiku",      # 使用快速模型
            "risk_tolerance": "very_low",     # 极低风险容忍度
        },
        risk_level="high"
    ),
    
    4: HexagramPattern(
        name="蒙卦",
        number=4,
        description="山下出泉，蒙；君子以果行育德",
        system_state={
            "success_rate": (0.4, 0.7),
            "growth_rate": (0.0, 0.2),
            "stability": (0.4, 0.7),
            "resource_usage": (0.3, 0.6),
            "learning_phase": True,           # 学习阶段
        },
        strategy={
            "priority": "learning",           # 学习优先
            "actions": [
                "collect_more_data",          # 收集更多数据
                "run_experiments",            # 运行实验
                "learn_from_failures",        # 从失败中学习
                "build_knowledge_base",       # 建立知识库
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "medium",
        },
        risk_level="medium"
    ),
    
    5: HexagramPattern(
        name="需卦",
        number=5,
        description="云上于天，需；君子以饮食宴乐",
        system_state={
            "success_rate": (0.6, 0.8),
            "growth_rate": (0.0, 0.1),
            "stability": (0.6, 0.8),
            "resource_usage": (0.4, 0.7),
            "waiting_for_resources": True,    # 等待资源
        },
        strategy={
            "priority": "patience",           # 耐心等待
            "actions": [
                "wait_for_better_timing",     # 等待更好时机
                "prepare_thoroughly",         # 充分准备
                "conserve_resources",         # 节约资源
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="low"
    ),
    
    6: HexagramPattern(
        name="讼卦",
        number=6,
        description="天与水违行，讼；君子以作事谋始",
        system_state={
            "success_rate": (0.3, 0.6),
            "growth_rate": (-0.3, 0.0),      # 负增长
            "stability": (0.2, 0.5),
            "resource_usage": (0.6, 0.9),
            "conflict_detected": True,        # 检测到冲突
        },
        strategy={
            "priority": "conflict_resolution", # 解决冲突
            "actions": [
                "identify_root_cause",        # 识别根本原因
                "rollback_recent_changes",    # 回滚最近更改
                "isolate_problematic_agents", # 隔离问题Agent
                "seek_mediation",             # 寻求调解
            ],
            "model_preference": "opus",       # 需要高智能分析
            "risk_tolerance": "very_low",
        },
        risk_level="critical"
    ),
    
    7: HexagramPattern(
        name="师卦",
        number=7,
        description="地中有水，师；君子以容民畜众",
        system_state={
            "success_rate": (0.5, 0.7),
            "growth_rate": (0.0, 0.2),
            "stability": (0.5, 0.7),
            "resource_usage": (0.5, 0.8),
            "team_coordination": True,        # 团队协作
        },
        strategy={
            "priority": "coordination",       # 协调优先
            "actions": [
                "organize_agent_teams",       # 组织Agent团队
                "assign_clear_roles",         # 分配明确角色
                "establish_communication",    # 建立沟通机制
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "medium",
        },
        risk_level="medium"
    ),
    
    8: HexagramPattern(
        name="比卦",
        number=8,
        description="地上有水，比；先王以建万国，亲诸侯",
        system_state={
            "success_rate": (0.7, 0.9),
            "growth_rate": (0.1, 0.3),
            "stability": (0.7, 0.9),
            "resource_usage": (0.3, 0.5),
            "collaboration": True,            # 协作良好
        },
        strategy={
            "priority": "alliance",           # 联盟优先
            "actions": [
                "strengthen_agent_bonds",     # 加强Agent联系
                "share_resources",            # 共享资源
                "mutual_support",             # 相互支持
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="low"
    ),
    
    # ===== 第二组：发展期（9-16卦）=====
    9: HexagramPattern(
        name="小畜卦",
        number=9,
        description="风行天上，小畜；君子以懿文德",
        system_state={
            "success_rate": (0.6, 0.8),
            "growth_rate": (0.0, 0.1),
            "stability": (0.6, 0.8),
            "resource_usage": (0.4, 0.6),
        },
        strategy={
            "priority": "accumulation",       # 积累优先
            "actions": [
                "save_resources",
                "small_improvements",
                "prepare_for_growth",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="low"
    ),
    
    10: HexagramPattern(
        name="履卦",
        number=10,
        description="上天下泽，履；君子以辨上下，定民志",
        system_state={
            "success_rate": (0.6, 0.8),
            "growth_rate": (0.0, 0.2),
            "stability": (0.5, 0.7),
            "resource_usage": (0.4, 0.6),
        },
        strategy={
            "priority": "caution",            # 谨慎优先
            "actions": [
                "follow_rules",
                "avoid_risks",
                "step_carefully",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="medium"
    ),
    11: HexagramPattern(
        name="泰卦",
        number=11,
        description="天地交，泰；后以财成天地之道，辅相天地之宜",
        system_state={
            "success_rate": (0.8, 1.0),
            "growth_rate": (0.2, 0.5),
            "stability": (0.7, 0.9),
            "resource_usage": (0.3, 0.5),
        },
        strategy={
            "priority": "growth",
            "actions": [
                "scale_up_operations",
                "try_ambitious_projects",
                "invest_in_innovation",
            ],
            "model_preference": "opus",
            "risk_tolerance": "high",
        },
        risk_level="low"
    ),
    
    12: HexagramPattern(
        name="否卦",
        number=12,
        description="天地不交，否；君子以俭德辟难",
        system_state={
            "success_rate": (0.0, 0.4),
            "growth_rate": (-0.5, -0.1),
            "stability": (0.1, 0.4),
            "resource_usage": (0.7, 1.0),
        },
        strategy={
            "priority": "defense",
            "actions": [
                "pause_new_tasks",
                "fix_critical_bugs",
                "rollback_to_stable_version",
                "emergency_mode",
            ],
            "model_preference": "haiku",
            "risk_tolerance": "zero",
        },
        risk_level="critical"
    ),
    
    13: HexagramPattern(
        name="同人卦",
        number=13,
        description="天与火，同人；君子以类族辨物",
        system_state={
            "success_rate": (0.7, 0.9),
            "growth_rate": (0.1, 0.3),
            "stability": (0.6, 0.8),
            "resource_usage": (0.4, 0.6),
            "collaboration": True,
        },
        strategy={
            "priority": "cooperation",
            "actions": [
                "build_alliances",
                "share_knowledge",
                "coordinate_efforts",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "medium",
        },
        risk_level="low"
    ),
    
    14: HexagramPattern(
        name="大有卦",
        number=14,
        description="火在天上，大有；君子以遏恶扬善，顺天休命",
        system_state={
            "success_rate": (0.8, 1.0),
            "growth_rate": (0.2, 0.4),
            "stability": (0.7, 0.9),
            "resource_usage": (0.2, 0.4),
        },
        strategy={
            "priority": "prosperity",
            "actions": [
                "maximize_output",
                "expand_capabilities",
                "share_success",
            ],
            "model_preference": "opus",
            "risk_tolerance": "high",
        },
        risk_level="low"
    ),
    
    15: HexagramPattern(
        name="谦卦",
        number=15,
        description="地中有山，谦；君子以裒多益寡，称物平施",
        system_state={
            "success_rate": (0.7, 0.9),
            "growth_rate": (0.0, 0.2),
            "stability": (0.7, 0.9),
            "resource_usage": (0.3, 0.5),
        },
        strategy={
            "priority": "humility",
            "actions": [
                "stay_humble",
                "continuous_improvement",
                "help_others",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="low"
    ),
    
    16: HexagramPattern(
        name="豫卦",
        number=16,
        description="雷出地奋，豫；先王以作乐崇德，殷荐之上帝",
        system_state={
            "success_rate": (0.7, 0.9),
            "growth_rate": (0.1, 0.3),
            "stability": (0.6, 0.8),
            "resource_usage": (0.4, 0.6),
        },
        strategy={
            "priority": "enthusiasm",
            "actions": [
                "maintain_momentum",
                "inspire_team",
                "celebrate_wins",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "medium",
        },
        risk_level="low"
    ),
    
    # ===== 第三组：成熟期（17-24卦）=====
    17: HexagramPattern(
        name="随卦",
        number=17,
        description="泽中有雷，随；君子以向晦入宴息",
        system_state={
            "success_rate": (0.6, 0.8),
            "growth_rate": (0.0, 0.2),
            "stability": (0.6, 0.8),
            "resource_usage": (0.4, 0.6),
        },
        strategy={
            "priority": "adaptation",
            "actions": [
                "follow_trends",
                "adapt_to_changes",
                "be_flexible",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "medium",
        },
        risk_level="low"
    ),
    
    18: HexagramPattern(
        name="蛊卦",
        number=18,
        description="山下有风，蛊；君子以振民育德",
        system_state={
            "success_rate": (0.3, 0.6),
            "growth_rate": (-0.2, 0.0),
            "stability": (0.3, 0.6),
            "resource_usage": (0.6, 0.8),
        },
        strategy={
            "priority": "repair",
            "actions": [
                "fix_legacy_issues",
                "clean_up_technical_debt",
                "refactor_code",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="high"
    ),
    
    19: HexagramPattern(
        name="临卦",
        number=19,
        description="地上有泽，临；君子以教思无穷，容保民无疆",
        system_state={
            "success_rate": (0.7, 0.9),
            "growth_rate": (0.1, 0.3),
            "stability": (0.6, 0.8),
            "resource_usage": (0.4, 0.6),
        },
        strategy={
            "priority": "supervision",
            "actions": [
                "monitor_closely",
                "provide_guidance",
                "ensure_quality",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "medium",
        },
        risk_level="low"
    ),
    
    20: HexagramPattern(
        name="观卦",
        number=20,
        description="风行地上，观；先王以省方，观民设教",
        system_state={
            "success_rate": (0.6, 0.8),
            "growth_rate": (0.0, 0.1),
            "stability": (0.6, 0.8),
            "resource_usage": (0.3, 0.5),
        },
        strategy={
            "priority": "observation",
            "actions": [
                "gather_data",
                "analyze_patterns",
                "learn_from_others",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="low"
    ),
    
    21: HexagramPattern(
        name="噬嗑卦",
        number=21,
        description="雷电噬嗑；先王以明罚敕法",
        system_state={
            "success_rate": (0.5, 0.7),
            "growth_rate": (0.0, 0.2),
            "stability": (0.4, 0.6),
            "resource_usage": (0.5, 0.7),
        },
        strategy={
            "priority": "enforcement",
            "actions": [
                "enforce_rules",
                "remove_obstacles",
                "clear_blockers",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "medium",
        },
        risk_level="medium"
    ),
    
    22: HexagramPattern(
        name="贲卦",
        number=22,
        description="山下有火，贲；君子以明庶政，无敢折狱",
        system_state={
            "success_rate": (0.7, 0.9),
            "growth_rate": (0.0, 0.2),
            "stability": (0.7, 0.9),
            "resource_usage": (0.4, 0.6),
        },
        strategy={
            "priority": "refinement",
            "actions": [
                "polish_details",
                "improve_aesthetics",
                "enhance_user_experience",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="low"
    ),
    
    23: HexagramPattern(
        name="剥卦",
        number=23,
        description="山附于地，剥；上以厚下安宅",
        system_state={
            "success_rate": (0.2, 0.5),
            "growth_rate": (-0.3, -0.1),
            "stability": (0.2, 0.5),
            "resource_usage": (0.7, 0.9),
        },
        strategy={
            "priority": "preservation",
            "actions": [
                "protect_core_assets",
                "minimize_losses",
                "wait_for_recovery",
            ],
            "model_preference": "haiku",
            "risk_tolerance": "very_low",
        },
        risk_level="critical"
    ),
    
    24: HexagramPattern(
        name="复卦",
        number=24,
        description="雷在地中，复；先王以至日闭关，商旅不行",
        system_state={
            "success_rate": (0.5, 0.7),
            "growth_rate": (0.0, 0.2),
            "stability": (0.5, 0.7),
            "resource_usage": (0.4, 0.6),
        },
        strategy={
            "priority": "recovery",
            "actions": [
                "restart_gradually",
                "rebuild_confidence",
                "learn_from_mistakes",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="medium"
    ),
    
    32: HexagramPattern(
        name="恒卦",
        number=32,
        description="雷风，恒；君子以立不易方",
        system_state={
            "success_rate": (0.7, 0.9),
            "growth_rate": (-0.05, 0.05),
            "stability": (0.8, 1.0),
            "resource_usage": (0.3, 0.5),
        },
        strategy={
            "priority": "maintenance",
            "actions": [
                "maintain_steady_state",
                "incremental_improvements",
                "routine_optimization",
            ],
            "model_preference": "sonnet",
            "risk_tolerance": "low",
        },
        risk_level="low"
    ),
}


class HexagramMatcher:
    """卦象匹配器 - 根据系统状态匹配最接近的卦象"""
    
    def __init__(self):
        self.patterns = HEXAGRAM_PATTERNS
    
    def match(self, system_metrics: Dict) -> Tuple[HexagramPattern, float]:
        """
        匹配最接近的卦象
        
        Args:
            system_metrics: 系统指标字典
                {
                    "success_rate": 0.85,
                    "growth_rate": 0.15,
                    "stability": 0.80,
                    "resource_usage": 0.45,
                    ...
                }
        
        Returns:
            (pattern, confidence) - 最匹配的卦象和置信度
        """
        best_match = None
        best_score = -1
        
        for pattern in self.patterns.values():
            score = self._calculate_match_score(system_metrics, pattern)
            if score > best_score:
                best_score = score
                best_match = pattern
        
        return best_match, best_score
    
    def _calculate_match_score(self, metrics: Dict, pattern: HexagramPattern) -> float:
        """计算匹配分数（0-1）"""
        scores = []
        
        for key, value_range in pattern.system_state.items():
            if key not in metrics:
                continue
            
            metric_value = metrics[key]
            
            # 布尔值匹配
            if isinstance(value_range, bool):
                if metric_value == value_range:
                    scores.append(1.0)
                else:
                    scores.append(0.0)
                continue
            
            # 范围匹配
            if isinstance(value_range, tuple):
                min_val, max_val = value_range
                if min_val <= metric_value <= max_val:
                    # 在范围内，计算距离中心的距离
                    center = (min_val + max_val) / 2
                    distance = abs(metric_value - center)
                    range_size = (max_val - min_val) / 2
                    score = 1.0 - (distance / range_size) if range_size > 0 else 1.0
                    scores.append(score)
                else:
                    # 在范围外，计算距离边界的距离
                    if metric_value < min_val:
                        distance = min_val - metric_value
                    else:
                        distance = metric_value - max_val
                    # 距离越远，分数越低（最低0）
                    score = max(0, 1.0 - distance)
                    scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_top_matches(self, system_metrics: Dict, top_n: int = 3) -> List[Tuple[HexagramPattern, float]]:
        """获取前N个最匹配的卦象"""
        matches = []
        for pattern in self.patterns.values():
            score = self._calculate_match_score(system_metrics, pattern)
            matches.append((pattern, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_n]


def get_strategy_for_state(system_metrics: Dict) -> Dict:
    """
    根据系统状态获取应对策略
    
    Args:
        system_metrics: 系统指标
    
    Returns:
        策略字典
    """
    matcher = HexagramMatcher()
    pattern, confidence = matcher.match(system_metrics)
    
    return {
        "hexagram": pattern.name,
        "hexagram_number": pattern.number,
        "description": pattern.description,
        "confidence": round(confidence, 3),
        "risk_level": pattern.risk_level,
        "strategy": pattern.strategy,
    }


# 简化版映射（用于快速原型）
SIMPLE_PATTERNS = {
    "泰卦": HEXAGRAM_PATTERNS[11],  # 顺利期
    "否卦": HEXAGRAM_PATTERNS[12],  # 危机期
    "屯卦": HEXAGRAM_PATTERNS[3],   # 困难期
    "恒卦": HEXAGRAM_PATTERNS[32],  # 稳定期
}


def get_simple_pattern(state_name: str) -> HexagramPattern:
    """获取简化版卦象（用于ChangeDetector集成）"""
    return SIMPLE_PATTERNS.get(state_name, HEXAGRAM_PATTERNS[32])  # 默认恒卦
