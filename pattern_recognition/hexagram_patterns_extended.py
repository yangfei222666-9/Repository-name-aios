"""
64卦扩展生成器
根据易经理论自动生成完整的64卦映射表
"""
from hexagram_patterns import HexagramPattern, HEXAGRAM_PATTERNS


# 剩余卦象的定义（25-64）
EXTENDED_HEXAGRAMS = {
    # ===== 第四组：转型期（25-32卦）=====
    25: {
        "name": "无妄卦",
        "description": "天下雷行，物与无妄；先王以茂对时，育万物",
        "success_rate": (0.6, 0.8),
        "growth_rate": (0.0, 0.2),
        "stability": (0.6, 0.8),
        "priority": "authenticity",
        "actions": ["stay_true", "avoid_speculation", "focus_on_fundamentals"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    26: {
        "name": "大畜卦",
        "description": "天在山中，大畜；君子以多识前言往行，以畜其德",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.1, 0.3),
        "stability": (0.7, 0.9),
        "priority": "accumulation",
        "actions": ["build_reserves", "strengthen_foundation", "prepare_for_future"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    27: {
        "name": "颐卦",
        "description": "山下有雷，颐；君子以慎言语，节饮食",
        "success_rate": (0.6, 0.8),
        "growth_rate": (0.0, 0.1),
        "stability": (0.6, 0.8),
        "priority": "nourishment",
        "actions": ["maintain_health", "conserve_energy", "sustainable_growth"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    28: {
        "name": "大过卦",
        "description": "泽灭木，大过；君子以独立不惧，遁世无闷",
        "success_rate": (0.4, 0.6),
        "growth_rate": (-0.1, 0.1),
        "stability": (0.3, 0.5),
        "priority": "crisis_management",
        "actions": ["handle_extreme_situation", "make_bold_decisions", "accept_risks"],
        "model": "opus",
        "risk": "high",
        "level": "high"
    },
    29: {
        "name": "坎卦",
        "description": "水洊至，习坎；君子以常德行，习教事",
        "success_rate": (0.3, 0.6),
        "growth_rate": (-0.2, 0.0),
        "stability": (0.3, 0.6),
        "priority": "perseverance",
        "actions": ["persist_through_difficulty", "learn_from_challenges", "stay_focused"],
        "model": "sonnet",
        "risk": "high",
        "level": "high"
    },
    30: {
        "name": "离卦",
        "description": "明两作，离；大人以继明照于四方",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.1, 0.3),
        "stability": (0.6, 0.8),
        "priority": "clarity",
        "actions": ["illuminate_problems", "provide_guidance", "maintain_visibility"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    31: {
        "name": "咸卦",
        "description": "山上有泽，咸；君子以虚受人",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.1, 0.3),
        "stability": (0.6, 0.8),
        "priority": "influence",
        "actions": ["build_relationships", "mutual_attraction", "harmonize"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    32: {
        "name": "恒卦",
        "description": "雷风，恒；君子以立不易方",
        "success_rate": (0.7, 0.9),
        "growth_rate": (-0.05, 0.05),
        "stability": (0.8, 1.0),
        "priority": "maintenance",
        "actions": ["maintain_steady_state", "incremental_improvements", "routine_optimization"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    
    # ===== 第五组：优化期（33-40卦）=====
    33: {
        "name": "遁卦",
        "description": "天下有山，遁；君子以远小人，不恶而严",
        "success_rate": (0.5, 0.7),
        "growth_rate": (-0.1, 0.1),
        "stability": (0.5, 0.7),
        "priority": "retreat",
        "actions": ["strategic_withdrawal", "avoid_conflict", "preserve_strength"],
        "model": "sonnet",
        "risk": "medium",
        "level": "medium"
    },
    34: {
        "name": "大壮卦",
        "description": "雷在天上，大壮；君子以非礼弗履",
        "success_rate": (0.8, 1.0),
        "growth_rate": (0.2, 0.4),
        "stability": (0.6, 0.8),
        "priority": "strength",
        "actions": ["use_power_wisely", "maintain_discipline", "avoid_recklessness"],
        "model": "opus",
        "risk": "medium",
        "level": "low"
    },
    35: {
        "name": "晋卦",
        "description": "明出地上，晋；君子以自昭明德",
        "success_rate": (0.8, 1.0),
        "growth_rate": (0.2, 0.4),
        "stability": (0.7, 0.9),
        "priority": "progress",
        "actions": ["advance_confidently", "seize_opportunities", "expand_influence"],
        "model": "opus",
        "risk": "low",
        "level": "low"
    },
    36: {
        "name": "明夷卦",
        "description": "明入地中，明夷；君子以莅众，用晦而明",
        "success_rate": (0.3, 0.6),
        "growth_rate": (-0.2, 0.0),
        "stability": (0.3, 0.6),
        "priority": "concealment",
        "actions": ["hide_capabilities", "wait_for_better_time", "protect_core"],
        "model": "haiku",
        "risk": "high",
        "level": "high"
    },
    37: {
        "name": "家人卦",
        "description": "风自火出，家人；君子以言有物，而行有恒",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.0, 0.2),
        "stability": (0.7, 0.9),
        "priority": "internal_harmony",
        "actions": ["strengthen_team", "establish_order", "maintain_discipline"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    38: {
        "name": "睽卦",
        "description": "上火下泽，睽；君子以同而异",
        "success_rate": (0.4, 0.7),
        "growth_rate": (-0.1, 0.1),
        "stability": (0.4, 0.7),
        "priority": "reconciliation",
        "actions": ["resolve_differences", "find_common_ground", "manage_diversity"],
        "model": "sonnet",
        "risk": "medium",
        "level": "medium"
    },
    39: {
        "name": "蹇卦",
        "description": "山上有水，蹇；君子以反身修德",
        "success_rate": (0.3, 0.6),
        "growth_rate": (-0.2, 0.0),
        "stability": (0.3, 0.6),
        "priority": "difficulty",
        "actions": ["face_obstacles", "seek_help", "improve_self"],
        "model": "sonnet",
        "risk": "high",
        "level": "high"
    },
    40: {
        "name": "解卦",
        "description": "雷雨作，解；君子以赦过宥罪",
        "success_rate": (0.6, 0.8),
        "growth_rate": (0.1, 0.3),
        "stability": (0.5, 0.7),
        "priority": "liberation",
        "actions": ["remove_obstacles", "forgive_mistakes", "move_forward"],
        "model": "sonnet",
        "risk": "medium",
        "level": "low"
    },
    
    # ===== 第六组：衰退期（41-48卦）=====
    41: {
        "name": "损卦",
        "description": "山下有泽，损；君子以惩忿窒欲",
        "success_rate": (0.5, 0.7),
        "growth_rate": (-0.1, 0.1),
        "stability": (0.5, 0.7),
        "priority": "reduction",
        "actions": ["cut_costs", "simplify_operations", "focus_on_essentials"],
        "model": "haiku",
        "risk": "medium",
        "level": "medium"
    },
    42: {
        "name": "益卦",
        "description": "风雷，益；君子以见善则迁，有过则改",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.2, 0.4),
        "stability": (0.6, 0.8),
        "priority": "increase",
        "actions": ["add_value", "improve_continuously", "seize_growth"],
        "model": "opus",
        "risk": "low",
        "level": "low"
    },
    43: {
        "name": "夬卦",
        "description": "泽上于天，夬；君子以施禄及下，居德则忌",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.1, 0.3),
        "stability": (0.5, 0.7),
        "priority": "breakthrough",
        "actions": ["make_decisive_action", "eliminate_problems", "be_resolute"],
        "model": "opus",
        "risk": "medium",
        "level": "low"
    },
    44: {
        "name": "姤卦",
        "description": "天下有风，姤；后以施命诰四方",
        "success_rate": (0.6, 0.8),
        "growth_rate": (0.0, 0.2),
        "stability": (0.5, 0.7),
        "priority": "encounter",
        "actions": ["handle_unexpected", "be_cautious", "avoid_temptation"],
        "model": "sonnet",
        "risk": "medium",
        "level": "medium"
    },
    45: {
        "name": "萃卦",
        "description": "泽上于地，萃；君子以除戎器，戒不虞",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.1, 0.3),
        "stability": (0.6, 0.8),
        "priority": "gathering",
        "actions": ["unite_forces", "consolidate_resources", "prepare_defense"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    46: {
        "name": "升卦",
        "description": "地中生木，升；君子以顺德，积小以高大",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.2, 0.4),
        "stability": (0.6, 0.8),
        "priority": "ascent",
        "actions": ["grow_gradually", "build_momentum", "rise_steadily"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    47: {
        "name": "困卦",
        "description": "泽无水，困；君子以致命遂志",
        "success_rate": (0.2, 0.5),
        "growth_rate": (-0.3, -0.1),
        "stability": (0.2, 0.5),
        "priority": "adversity",
        "actions": ["endure_hardship", "maintain_integrity", "wait_for_change"],
        "model": "haiku",
        "risk": "critical",
        "level": "critical"
    },
    48: {
        "name": "井卦",
        "description": "木上有水，井；君子以劳民劝相",
        "success_rate": (0.6, 0.8),
        "growth_rate": (0.0, 0.2),
        "stability": (0.7, 0.9),
        "priority": "nourishment",
        "actions": ["provide_resources", "maintain_infrastructure", "serve_others"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    
    # ===== 第七组：重生期（49-56卦）=====
    49: {
        "name": "革卦",
        "description": "泽中有火，革；君子以治历明时",
        "success_rate": (0.5, 0.7),
        "growth_rate": (0.0, 0.2),
        "stability": (0.3, 0.6),
        "priority": "revolution",
        "actions": ["make_radical_changes", "transform_system", "embrace_new"],
        "model": "opus",
        "risk": "high",
        "level": "high"
    },
    50: {
        "name": "鼎卦",
        "description": "木上有火，鼎；君子以正位凝命",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.1, 0.3),
        "stability": (0.7, 0.9),
        "priority": "establishment",
        "actions": ["establish_order", "consolidate_power", "maintain_stability"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    51: {
        "name": "震卦",
        "description": "洊雷，震；君子以恐惧修省",
        "success_rate": (0.5, 0.7),
        "growth_rate": (0.0, 0.2),
        "stability": (0.4, 0.6),
        "priority": "shock",
        "actions": ["respond_to_crisis", "stay_calm", "learn_from_shock"],
        "model": "sonnet",
        "risk": "high",
        "level": "medium"
    },
    52: {
        "name": "艮卦",
        "description": "兼山，艮；君子以思不出其位",
        "success_rate": (0.6, 0.8),
        "growth_rate": (-0.1, 0.1),
        "stability": (0.7, 0.9),
        "priority": "stillness",
        "actions": ["pause_and_reflect", "know_limits", "stay_grounded"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    53: {
        "name": "渐卦",
        "description": "山上有木，渐；君子以居贤德善俗",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.1, 0.3),
        "stability": (0.7, 0.9),
        "priority": "gradual_progress",
        "actions": ["advance_step_by_step", "build_systematically", "be_patient"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    54: {
        "name": "归妹卦",
        "description": "泽上有雷，归妹；君子以永终知敝",
        "success_rate": (0.5, 0.7),
        "growth_rate": (0.0, 0.2),
        "stability": (0.4, 0.6),
        "priority": "caution",
        "actions": ["be_careful", "avoid_mistakes", "think_long_term"],
        "model": "sonnet",
        "risk": "medium",
        "level": "medium"
    },
    55: {
        "name": "丰卦",
        "description": "雷电皆至，丰；君子以折狱致刑",
        "success_rate": (0.8, 1.0),
        "growth_rate": (0.2, 0.4),
        "stability": (0.6, 0.8),
        "priority": "abundance",
        "actions": ["maximize_output", "enjoy_success", "prepare_for_decline"],
        "model": "opus",
        "risk": "low",
        "level": "low"
    },
    56: {
        "name": "旅卦",
        "description": "山上有火，旅；君子以明慎用刑，而不留狱",
        "success_rate": (0.5, 0.7),
        "growth_rate": (0.0, 0.2),
        "stability": (0.4, 0.6),
        "priority": "travel",
        "actions": ["be_adaptable", "stay_humble", "avoid_attachment"],
        "model": "sonnet",
        "risk": "medium",
        "level": "medium"
    },
    
    # ===== 第八组：完成期（57-64卦）=====
    57: {
        "name": "巽卦",
        "description": "随风，巽；君子以申命行事",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.1, 0.3),
        "stability": (0.6, 0.8),
        "priority": "penetration",
        "actions": ["influence_gradually", "be_persistent", "adapt_flexibly"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    58: {
        "name": "兑卦",
        "description": "丽泽，兑；君子以朋友讲习",
        "success_rate": (0.8, 1.0),
        "growth_rate": (0.1, 0.3),
        "stability": (0.7, 0.9),
        "priority": "joy",
        "actions": ["celebrate_success", "share_happiness", "maintain_harmony"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    59: {
        "name": "涣卦",
        "description": "风行水上，涣；先王以享于帝立庙",
        "success_rate": (0.5, 0.7),
        "growth_rate": (0.0, 0.2),
        "stability": (0.4, 0.6),
        "priority": "dispersion",
        "actions": ["break_up_stagnation", "redistribute_resources", "renew_energy"],
        "model": "sonnet",
        "risk": "medium",
        "level": "medium"
    },
    60: {
        "name": "节卦",
        "description": "泽上有水，节；君子以制数度，议德行",
        "success_rate": (0.7, 0.9),
        "growth_rate": (0.0, 0.2),
        "stability": (0.7, 0.9),
        "priority": "moderation",
        "actions": ["set_limits", "maintain_balance", "avoid_excess"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    61: {
        "name": "中孚卦",
        "description": "泽上有风，中孚；君子以议狱缓死",
        "success_rate": (0.8, 1.0),
        "growth_rate": (0.1, 0.3),
        "stability": (0.7, 0.9),
        "priority": "sincerity",
        "actions": ["build_trust", "be_authentic", "maintain_integrity"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    62: {
        "name": "小过卦",
        "description": "山上有雷，小过；君子以行过乎恭，丧过乎哀，用过乎俭",
        "success_rate": (0.6, 0.8),
        "growth_rate": (0.0, 0.2),
        "stability": (0.6, 0.8),
        "priority": "small_excess",
        "actions": ["make_minor_adjustments", "be_cautious", "avoid_overreach"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    63: {
        "name": "既济卦",
        "description": "水在火上，既济；君子以思患而预防之",
        "success_rate": (0.8, 1.0),
        "growth_rate": (0.0, 0.2),
        "stability": (0.7, 0.9),
        "priority": "completion",
        "actions": ["maintain_success", "prepare_for_change", "stay_vigilant"],
        "model": "sonnet",
        "risk": "low",
        "level": "low"
    },
    64: {
        "name": "未济卦",
        "description": "火在水上，未济；君子以慎辨物居方",
        "success_rate": (0.5, 0.7),
        "growth_rate": (0.0, 0.2),
        "stability": (0.5, 0.7),
        "priority": "incompletion",
        "actions": ["continue_efforts", "stay_focused", "prepare_for_new_cycle"],
        "model": "sonnet",
        "risk": "medium",
        "level": "medium"
    },
}


def generate_hexagram_pattern(number: int, data: dict) -> HexagramPattern:
    """从简化数据生成完整的 HexagramPattern"""
    return HexagramPattern(
        name=data["name"],
        number=number,
        description=data["description"],
        system_state={
            "success_rate": data["success_rate"],
            "growth_rate": data["growth_rate"],
            "stability": data["stability"],
            "resource_usage": (0.3, 0.7),  # 默认值
        },
        strategy={
            "priority": data["priority"],
            "actions": data["actions"],
            "model_preference": data["model"],
            "risk_tolerance": data["risk"],
        },
        risk_level=data["level"]
    )


def extend_hexagram_patterns():
    """扩展 HEXAGRAM_PATTERNS 到完整的64卦"""
    for number, data in EXTENDED_HEXAGRAMS.items():
        if number not in HEXAGRAM_PATTERNS:
            HEXAGRAM_PATTERNS[number] = generate_hexagram_pattern(number, data)
    
    print(f"[OK] 扩展完成！当前共有 {len(HEXAGRAM_PATTERNS)} 个卦象")
    return HEXAGRAM_PATTERNS


if __name__ == "__main__":
    # 扩展卦象
    patterns = extend_hexagram_patterns()
    
    # 验证
    print("\n=== 64卦列表 ===")
    for i in range(1, 65):
        if i in patterns:
            print(f"{i:2d}. {patterns[i].name} - {patterns[i].risk_level}")
        else:
            print(f"{i:2d}. [缺失]")
