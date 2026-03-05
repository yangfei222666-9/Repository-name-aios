"""
AIOS Hexagram Detector - 六十四卦状态检测
职责: 上卦 + 下卦 → 六十四卦（8×8 状态空间）
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from .hexagram_logger import append_hexagram_state


@dataclass
class HexagramResult:
    """六十四卦检测结果"""
    number: int            # 卦序（1-64）
    name: str              # 卦名
    upper: str             # 上卦（外卦）
    lower: str             # 下卦（内卦）
    phase: str             # 系统阶段
    description: str       # 卦象描述


# 六十四卦映射表（上卦 × 下卦 → 卦名）
# 格式: (上卦, 下卦): (卦序, 卦名, 系统阶段, 描述)
HEXAGRAM_MAP = {
    # 乾上
    ("乾", "乾"): (1,  "乾",   "Full Power",       "纯阳，系统全力运行"),
    ("乾", "坤"): (11, "泰",   "Harmony",          "天地交泰，系统和谐"),
    ("乾", "震"): (34, "大壮", "Surge Power",      "雷天大壮，任务激增且高效"),
    ("乾", "巽"): (9,  "小畜", "Fine Tuning",      "风天小畜，微调积累"),
    ("乾", "坎"): (5,  "需",   "Waiting",          "水天需，等待时机"),
    ("乾", "离"): (14, "大有", "Peak Load",        "火天大有，高负载高产出"),
    ("乾", "艮"): (26, "大畜", "Accumulate",       "山天大畜，积累资源"),
    ("乾", "兑"): (43, "夬",   "Breakthrough",     "泽天夬，突破瓶颈"),
    # 坤上
    ("坤", "乾"): (12, "否",   "Blocked",          "天地否，系统阻塞"),
    ("坤", "坤"): (2,  "坤",   "Stable",           "纯阴，系统稳定运行"),
    ("坤", "震"): (16, "豫",   "Ready",            "雷地豫，准备就绪"),
    ("坤", "巽"): (20, "观",   "Observing",        "风地观，观察调整"),
    ("坤", "坎"): (8,  "比",   "Cooperation",      "水地比，协作运行"),
    ("坤", "离"): (35, "晋",   "Progress",         "火地晋，稳步进展"),
    ("坤", "艮"): (15, "谦",   "Humble",           "山地谦，谦逊稳健"),
    ("坤", "兑"): (45, "萃",   "Gathering",        "泽地萃，资源聚集"),
    # 坎上
    ("坎", "乾"): (6,  "讼",   "Conflict",         "天水讼，任务冲突"),
    ("坎", "坤"): (7,  "师",   "Discipline",       "地水师，有序执行"),
    ("坎", "震"): (40, "解",   "Release",          "雷水解，解除风险"),
    ("坎", "巽"): (59, "涣",   "Dispersing",       "风水涣，分散处理"),
    ("坎", "坎"): (29, "坎",   "Deep Risk",        "重坎，深度风险"),
    ("坎", "离"): (64, "未济", "Incomplete",       "火水未济，任务未完成"),
    ("坎", "艮"): (39, "蹇",   "Obstacle",         "山水蹇，遇到障碍"),
    ("坎", "兑"): (47, "困",   "Exhausted",        "泽水困，资源耗尽"),
    # 离上
    ("离", "乾"): (13, "同人", "Teamwork",         "天火同人，团队协作"),
    ("离", "坤"): (36, "明夷", "Hidden",           "地火明夷，低调运行"),
    ("离", "震"): (55, "丰",   "Abundance",        "雷火丰，高产出"),
    ("离", "巽"): (37, "家人", "Organized",        "风火家人，有序组织"),
    ("离", "坎"): (63, "既济", "Completed",        "水火既济，任务完成"),
    ("离", "离"): (30, "离",   "Blazing",          "重离，极高负载"),
    ("离", "艮"): (56, "旅",   "Transient",        "山火旅，临时状态"),
    ("离", "兑"): (49, "革",   "Transform",        "泽火革，系统变革"),
    # 震上
    ("震", "乾"): (25, "无妄", "Unexpected",       "天雷无妄，意外事件"),
    ("震", "坤"): (24, "复",   "Recovery",         "地雷复，系统恢复"),
    ("震", "震"): (51, "震",   "Shock",            "重震，连续冲击"),
    ("震", "巽"): (42, "益",   "Growth",           "风雷益，快速增长"),
    ("震", "坎"): (3,  "屯",   "Starting",         "水雷屯，艰难启动"),
    ("震", "离"): (21, "噬嗑", "Resolving",        "火雷噬嗑，解决问题"),
    ("震", "艮"): (27, "颐",   "Nurturing",        "山雷颐，培育资源"),
    ("震", "兑"): (17, "随",   "Following",        "泽雷随，跟随趋势"),
    # 巽上
    ("巽", "乾"): (44, "姤",   "Encounter",        "天风姤，意外相遇"),
    ("巽", "坤"): (46, "升",   "Ascending",        "地风升，逐步提升"),
    ("巽", "震"): (32, "恒",   "Persistent",       "雷风恒，持续运行"),
    ("巽", "巽"): (57, "巽",   "Gentle",           "重巽，持续微调"),
    ("巽", "坎"): (48, "井",   "Resource",         "水风井，资源稳定"),
    ("巽", "离"): (50, "鼎",   "Transformation",   "火风鼎，系统升级"),
    ("巽", "艮"): (18, "蛊",   "Repair",           "山风蛊，修复问题"),
    ("巽", "兑"): (28, "大过", "Overload",         "泽风大过，严重过载"),
    # 艮上
    ("艮", "乾"): (33, "遁",   "Retreat",          "天山遁，主动退让"),
    ("艮", "坤"): (15, "谦",   "Humble",           "地山谦，谦逊稳健"),
    ("艮", "震"): (62, "小过", "Minor Error",      "雷山小过，小错误"),
    ("艮", "巽"): (53, "渐",   "Gradual",          "风山渐，渐进改善"),
    ("艮", "坎"): (39, "蹇",   "Obstacle",         "山水蹇，遇到障碍"),
    ("艮", "离"): (56, "旅",   "Transient",        "山火旅，临时状态"),
    ("艮", "艮"): (52, "艮",   "Still",            "重艮，系统静止"),
    ("艮", "兑"): (31, "咸",   "Resonance",        "泽山咸，系统共鸣"),
    # 兑上
    ("兑", "乾"): (10, "履",   "Careful",          "天泽履，谨慎前行"),
    ("兑", "坤"): (19, "临",   "Approaching",      "地泽临，临近目标"),
    ("兑", "震"): (54, "归妹", "Subordinate",      "雷泽归妹，从属执行"),
    ("兑", "巽"): (61, "中孚", "Trust",            "风泽中孚，信任协作"),
    ("兑", "坎"): (60, "节",   "Regulate",         "水泽节，节制资源"),
    ("兑", "离"): (38, "睽",   "Diverge",          "火泽睽，策略分歧"),
    ("兑", "艮"): (41, "损",   "Reduce",           "山泽损，减少负载"),
    ("兑", "兑"): (58, "兑",   "Joyful",           "重兑，协同愉快"),
}


def get_hexagram(upper: str, lower: str, metrics: dict = None, log: bool = True) -> HexagramResult:
    """
    从上卦和下卦推导六十四卦
    
    Args:
        upper: 上卦（外卦）名称
        lower: 下卦（内卦）名称
        metrics: 原始指标（可选，用于记录）
        log: 是否记录到历史文件（默认True）
    
    Returns:
        HexagramResult: 六十四卦结果
    """
    key = (upper, lower)
    if key in HEXAGRAM_MAP:
        number, name, phase, description = HEXAGRAM_MAP[key]
        result = HexagramResult(
            number=number,
            name=name,
            upper=upper,
            lower=lower,
            phase=phase,
            description=description
        )
    else:
        # 未找到映射，返回默认
        result = HexagramResult(
            number=2,
            name="坤",
            upper=upper,
            lower=lower,
            phase="Stable",
            description="默认稳定状态"
        )
    
    # 自动记录到历史文件（如果提供了 metrics）
    if log and metrics:
        try:
            append_hexagram_state(
                trigram_upper=upper,
                trigram_lower=lower,
                hexagram=result.name,
                success_rate=metrics.get("success_rate", 0.0),
                latency=metrics.get("latency", 0.0),
                debate_rate=metrics.get("debate_rate", 0.0),
                metrics=metrics
            )
        except Exception as e:
            # 记录失败不影响主流程
            pass
    
    return result


if __name__ == "__main__":
    # 测试六十四卦检测
    test_cases = [
        ("乾", "坤"),  # 泰卦
        ("坎", "离"),  # 未济卦
        ("离", "坎"),  # 既济卦
        ("坤", "坤"),  # 坤卦
        ("坎", "坎"),  # 重坎
        ("巽", "兑"),  # 大过卦
    ]
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  AIOS Hexagram Detector - Test Suite  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    for upper, lower in test_cases:
        result = get_hexagram(upper, lower)
        print(f"  {upper} + {lower} → No.{result.number} {result.name}")
        print(f"    Phase: {result.phase}")
        print(f"    Description: {result.description}")
        print()
    
    print(f"[OK] Total hexagrams mapped: {len(HEXAGRAM_MAP)}/64")
