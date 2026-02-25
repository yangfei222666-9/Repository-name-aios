"""
aios/learning/feedback/integration.py - 反馈系统集成

在主对话流程中自动检测和记录反馈
"""

from typing import Optional
from learning.feedback.tracker import (
    detect_feedback_in_message,
    auto_associate_feedback,
    record_action,
    get_feedback_stats,
)


def process_user_message(
    message: str, timestamp: Optional[float] = None
) -> Optional[dict]:
    """
    处理用户消息，检测反馈

    Args:
        message: 用户消息
        timestamp: 时间戳

    Returns:
        反馈信息字典，如果没有检测到反馈则返回 None
    """
    feedback_value = detect_feedback_in_message(message)

    if feedback_value:
        feedback_id = auto_associate_feedback(
            value=feedback_value, user_message=message, timestamp=timestamp
        )

        if feedback_id:
            return {
                "detected": True,
                "value": feedback_value,
                "feedback_id": feedback_id,
                "associated": True,
            }
        else:
            return {
                "detected": True,
                "value": feedback_value,
                "feedback_id": None,
                "associated": False,
                "reason": "no_recent_action",
            }

    return None


def record_assistant_action(
    action_id: str,
    action_type: str,
    category: str,
    message: str,
    timestamp: Optional[float] = None,
):
    """
    记录助手的行动（供后续反馈关联）

    Args:
        action_id: 行动 ID
        action_type: 行动类型（suggestion/reminder/alert/answer）
        category: 类别
        message: 消息内容
        timestamp: 时间戳
    """
    record_action(
        action_id=action_id,
        action_type=action_type,
        category=category,
        message=message,
        timestamp=timestamp,
    )


def should_ask_for_feedback() -> bool:
    """
    判断是否应该主动询问反馈

    策略：
    - 每 20 条消息询问一次
    - 最近 24 小时内没有反馈时询问

    Returns:
        是否应该询问
    """
    # TODO: 实现更智能的询问策略
    # 当前简单实现：不主动询问，依赖用户自然反馈
    return False


def get_feedback_summary(days: int = 7) -> dict:
    """
    获取反馈摘要（供心跳报告使用）

    Args:
        days: 统计天数

    Returns:
        摘要字典
    """
    stats = get_feedback_stats(days)

    if stats["total"] == 0:
        return {"has_data": False, "message": f"最近 {days} 天暂无反馈数据"}

    return {
        "has_data": True,
        "total": stats["total"],
        "acceptance_rate": stats["acceptance_rate"],
        "message": f"最近 {days} 天：{stats['total']} 条反馈，接受率 {stats['acceptance_rate']*100:.0f}%",
    }


if __name__ == "__main__":
    # 测试
    test_messages = ["有用", "这个建议不错", "没用", "别这样", "今天天气怎么样"]

    for msg in test_messages:
        result = process_user_message(msg)
        print(f"消息: {msg}")
        print(f"结果: {result}")
        print()
