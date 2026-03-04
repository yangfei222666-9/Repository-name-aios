"""
AIOS 每日简报 Markdown 模板生成器
集成：数据统计 + 策略反思 + 卦象分析
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

def generate_daily_report(
    insight_data: Dict,
    reflection_data: Dict,
    pattern_data: Dict,
    output_format: str = "markdown"
) -> str:
    """
    生成每日简报
    
    Args:
        insight_data: insight.py 生成的数据
        reflection_data: reflect.py 生成的反思数据
        pattern_data: pattern_recognizer.py 生成的卦象数据
        output_format: 输出格式（markdown/telegram）
    
    Returns:
        格式化的简报文本
    """
    
    if output_format == "telegram":
        return _generate_telegram_report(insight_data, reflection_data, pattern_data)
    else:
        return _generate_markdown_report(insight_data, reflection_data, pattern_data)


def _generate_markdown_report(insight_data: Dict, reflection_data: Dict, pattern_data: Dict) -> str:
    """生成完整 Markdown 报告"""
    
    report = f"""# 🚀 AIOS 每日简报

**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 数据概览

### 任务执行情况
- **总任务数：** {insight_data.get('total_tasks', 0)}
- **已完成：** {insight_data.get('completed_tasks', 0)} ({insight_data.get('success_rate', 0)*100:.1f}%)
- **失败：** {insight_data.get('failed_tasks', 0)}
- **待处理：** {insight_data.get('pending_tasks', 0)}

### Agent 性能
- **活跃 Agent：** {insight_data.get('active_agents', 0)}
- **平均执行时间：** {insight_data.get('avg_duration', 0):.1f}s
- **最快任务：** {insight_data.get('min_duration', 0):.1f}s
- **最慢任务：** {insight_data.get('max_duration', 0):.1f}s

### 成本统计
- **总成本：** ${insight_data.get('total_cost', 0):.4f}
- **平均成本：** ${insight_data.get('avg_cost', 0):.4f}/任务
- **Token 使用：** {insight_data.get('total_tokens', 0):,}

---

## 💡 今日策略

### 反思总结
{reflection_data.get('summary', '暂无反思数据')}

### 行动建议
"""
    
    for i, action in enumerate(reflection_data.get('actions', []), 1):
        report += f"{i}. {action}\n"
    
    report += f"""
### 优先级
- **高优先级：** {reflection_data.get('high_priority', '无')}
- **中优先级：** {reflection_data.get('medium_priority', '无')}
- **低优先级：** {reflection_data.get('low_priority', '无')}

---

## 🔮 卦象分析

### 当前卦象
**{pattern_data.get('primary_pattern', {}).get('name', '未知')}（第{pattern_data.get('primary_pattern', {}).get('number', 0)}卦）**

> {pattern_data.get('primary_pattern', {}).get('description', '暂无描述')}

- **置信度：** {pattern_data.get('primary_pattern', {}).get('confidence', 0)*100:.1f}%
- **风险等级：** {pattern_data.get('primary_pattern', {}).get('risk_level', 'unknown')}

### 系统指标
- **成功率：** {pattern_data.get('system_metrics', {}).get('success_rate', 0)*100:.1f}%
- **增长率：** {pattern_data.get('system_metrics', {}).get('growth_rate', 0)*100:+.1f}%
- **稳定性：** {pattern_data.get('system_metrics', {}).get('stability', 0)*100:.1f}%
- **资源使用：** {pattern_data.get('system_metrics', {}).get('resource_usage', 0)*100:.1f}%

### 趋势分析
"""
    
    for metric, trend_data in pattern_data.get('trends', {}).items():
        trend = trend_data.get('trend', 'stable')
        confidence = trend_data.get('confidence', 0)
        report += f"- **{metric}:** {trend} (置信度: {confidence*100:.1f}%)\n"
    
    report += f"""
### 推荐策略
- **优先级：** {pattern_data.get('recommended_strategy', {}).get('priority', 'normal')}
- **模型偏好：** {pattern_data.get('recommended_strategy', {}).get('model_preference', 'sonnet')}
- **风险容忍度：** {pattern_data.get('recommended_strategy', {}).get('risk_tolerance', 'medium')}

### 建议行动
"""
    
    for action in pattern_data.get('recommended_strategy', {}).get('actions', []):
        report += f"- {action}\n"
    
    # 模式转变检测
    if pattern_data.get('pattern_shift'):
        shift = pattern_data['pattern_shift']
        report += f"""
---

## ⚠️ 模式转变检测

**系统状态从 {shift.get('from_pattern')} 转变为 {shift.get('to_pattern')}**

- **风险变化：** {shift.get('from_risk')} → {shift.get('to_risk')}
- **时间：** {shift.get('timestamp')}

{shift.get('message', '')}
"""
    
    report += """
---

## 📈 系统健康度

"""
    
    health_score = pattern_data.get('system_metrics', {}).get('success_rate', 0) * 100
    if health_score >= 80:
        status = "🟢 优秀"
    elif health_score >= 60:
        status = "🟡 良好"
    else:
        status = "🔴 需要关注"
    
    report += f"**{health_score:.1f}/100** {status}\n\n"
    
    report += """
---

*本报告由 AIOS 自动生成*
"""
    
    return report


def _generate_telegram_report(insight_data: Dict, reflection_data: Dict, pattern_data: Dict) -> str:
    """生成 Telegram 精简版报告"""
    
    report = f"""🚀 AIOS 每日简报

📊 数据概览
• 任务：{insight_data.get('completed_tasks', 0)}/{insight_data.get('total_tasks', 0)} ({insight_data.get('success_rate', 0)*100:.1f}%)
• 成本：${insight_data.get('total_cost', 0):.4f}
• 平均耗时：{insight_data.get('avg_duration', 0):.1f}s

💡 今日策略
{reflection_data.get('summary', '暂无')}

🔮 卦象分析
{pattern_data.get('primary_pattern', {}).get('name', '未知')}（第{pattern_data.get('primary_pattern', {}).get('number', 0)}卦）
• 置信度：{pattern_data.get('primary_pattern', {}).get('confidence', 0)*100:.1f}%
• 风险：{pattern_data.get('primary_pattern', {}).get('risk_level', 'unknown')}
• 成功率：{pattern_data.get('system_metrics', {}).get('success_rate', 0)*100:.1f}%

建议行动：
"""
    
    for i, action in enumerate(pattern_data.get('recommended_strategy', {}).get('actions', [])[:3], 1):
        report += f"{i}. {action}\n"
    
    # 模式转变
    if pattern_data.get('pattern_shift'):
        shift = pattern_data['pattern_shift']
        report += f"\n⚠️ 卦象转变：{shift.get('from_pattern')} → {shift.get('to_pattern')}\n"
        report += f"风险：{shift.get('from_risk')} → {shift.get('to_risk')}\n"
    
    return report


def main():
    """测试报告生成"""
    # 模拟数据
    insight_data = {
        "total_tasks": 62,
        "completed_tasks": 60,
        "failed_tasks": 1,
        "pending_tasks": 1,
        "success_rate": 0.968,
        "active_agents": 27,
        "avg_duration": 7.87,
        "min_duration": 4.33,
        "max_duration": 36.79,
        "total_cost": 0.1234,
        "avg_cost": 0.002,
        "total_tokens": 50000
    }
    
    reflection_data = {
        "summary": "系统运行稳定，Agent协作良好，建议继续保持当前策略。",
        "actions": [
            "继续优化任务分配算法",
            "增加Agent间的资源共享",
            "监控成本增长趋势"
        ],
        "high_priority": "优化任务分配",
        "medium_priority": "资源共享",
        "low_priority": "成本监控"
    }
    
    # 读取真实卦象数据
    pattern_file = Path(__file__).parent.parent / "data" / "latest_pattern_report.json"
    if pattern_file.exists():
        with open(pattern_file, 'r', encoding='utf-8') as f:
            pattern_data = json.load(f)
    else:
        pattern_data = {
            "primary_pattern": {
                "name": "比卦",
                "number": 8,
                "description": "地上有水，比；先王以建万国，亲诸侯",
                "confidence": 0.799,
                "risk_level": "low"
            },
            "system_metrics": {
                "success_rate": 1.0,
                "growth_rate": 0.0,
                "stability": 0.8,
                "resource_usage": 0.34
            },
            "trends": {
                "success_rate": {"trend": "stable", "confidence": 0.0},
                "avg_duration": {"trend": "stable", "confidence": 0.0}
            },
            "recommended_strategy": {
                "priority": "alliance",
                "model_preference": "sonnet",
                "risk_tolerance": "low",
                "actions": [
                    "strengthen_agent_bonds",
                    "share_resources",
                    "mutual_support"
                ]
            }
        }
    
    # 生成报告
    markdown_report = generate_daily_report(insight_data, reflection_data, pattern_data, "markdown")
    telegram_report = generate_daily_report(insight_data, reflection_data, pattern_data, "telegram")
    
    # 保存
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "daily_report.md", 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    with open(output_dir / "daily_report_telegram.txt", 'w', encoding='utf-8') as f:
        f.write(telegram_report)
    
    print("✅ 报告已生成：")
    print(f"  - {output_dir / 'daily_report.md'}")
    print(f"  - {output_dir / 'daily_report_telegram.txt'}")
    print("\n" + "="*60)
    print("Telegram 版本预览：")
    print("="*60)
    print(telegram_report)


if __name__ == "__main__":
    main()
