"""
AIOS 每日简报生成器 - 完整版（珊瑚海优化版）
集成：数据统计 + 卦象分析 + 历史趋势 + 行动建议
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

def generate_daily_report_v2(date: str = None) -> str:
    """
    生成完整版每日简报
    
    Args:
        date: 日期字符串（默认今天）
    
    Returns:
        格式化的简报文本
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 读取数据
    data_dir = Path(__file__).parent.parent / "data"
    agent_system_dir = Path(__file__).parent.parent / "agent_system"
    
    # 1. 读取任务数据
    task_stats = _load_task_stats(agent_system_dir)
    
    # 2. 读取卦象数据
    pattern_file = data_dir / "latest_pattern_report.json"
    if pattern_file.exists():
        with open(pattern_file, 'r', encoding='utf-8') as f:
            pattern_data = json.load(f)
    else:
        pattern_data = {}
    
    # 3. 读取卦象历史
    history_file = data_dir / "pattern_history.jsonl"
    pattern_history = _load_pattern_history(history_file, limit=10)
    
    # 4. 读取报警
    alerts_file = agent_system_dir / "alerts.jsonl"
    alerts = _load_recent_alerts(alerts_file)
    
    # 5. 生成报告
    report = _format_report(date, task_stats, pattern_data, pattern_history, alerts)
    
    return report


def _load_task_stats(agent_system_dir: Path) -> Dict:
    """加载任务统计数据"""
    task_queue = agent_system_dir / "task_queue.jsonl"
    
    if not task_queue.exists():
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "success_rate": 0,
            "total_cost": 0,
            "avg_time": 0,
            "task_trend": "stable",
            "task_change": 0,
            "stability_score": 0
        }
    
    # 读取最近24小时的任务
    cutoff_time = datetime.now() - timedelta(hours=24)
    yesterday_cutoff = datetime.now() - timedelta(hours=48)
    
    today_tasks = []
    yesterday_tasks = []
    
    with open(task_queue, 'r', encoding='utf-8') as f:
        for line in f:
            task = json.loads(line)
            updated_at = task.get('updated_at')
            if updated_at:
                task_time = datetime.fromtimestamp(updated_at)
                if task_time >= cutoff_time:
                    today_tasks.append(task)
                elif task_time >= yesterday_cutoff:
                    yesterday_tasks.append(task)
    
    # 统计今天
    total_tasks = len(today_tasks)
    completed_tasks = sum(1 for t in today_tasks if t.get('status') == 'completed')
    success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # 计算成本和耗时
    total_cost = 0
    total_duration = 0
    duration_count = 0
    
    for task in today_tasks:
        result = task.get('result', {})
        tokens = result.get('tokens', {})
        input_tokens = tokens.get('input', 0)
        output_tokens = tokens.get('output', 0)
        cost = (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.015)
        total_cost += cost
        
        duration = result.get('duration', 0)
        if duration > 0:
            total_duration += duration
            duration_count += 1
    
    avg_time = (total_duration / duration_count) if duration_count > 0 else 0
    
    # 计算趋势
    yesterday_total = len(yesterday_tasks)
    if yesterday_total > 0:
        task_change = ((total_tasks - yesterday_total) / yesterday_total * 100)
        if task_change > 10:
            task_trend = "上升"
        elif task_change < -10:
            task_trend = "下降"
        else:
            task_trend = "稳定"
    else:
        task_change = 0
        task_trend = "稳定"
    
    # 计算稳定性（基于成功率和任务数波动）
    stability_score = success_rate * (1 - abs(task_change) / 100)
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "success_rate": success_rate,
        "total_cost": total_cost,
        "avg_time": avg_time,
        "task_trend": task_trend,
        "task_change": task_change,
        "stability_score": stability_score
    }


def _load_pattern_history(history_file: Path, limit: int = 10) -> List[Dict]:
    """加载卦象历史"""
    if not history_file.exists():
        return []
    
    history = []
    with open(history_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                if record.get('status') == 'success':
                    history.append(record)
            except:
                continue
    
    # 返回最近N条
    return history[-limit:] if len(history) > limit else history


def _load_recent_alerts(alerts_file: Path) -> List[Dict]:
    """加载最近的报警"""
    if not alerts_file.exists():
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=24)
    alerts = []
    
    with open(alerts_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                alert = json.loads(line)
                alert_time = datetime.fromisoformat(alert['timestamp'])
                if alert_time >= cutoff_time and not alert.get('sent', False):
                    alerts.append(alert)
            except:
                continue
    
    return alerts


def _format_report(date: str, task_stats: Dict, pattern_data: Dict, pattern_history: List[Dict], alerts: List[Dict]) -> str:
    """格式化报告"""
    
    # 提取卦象数据
    primary_pattern = pattern_data.get('primary_pattern', {})
    system_metrics = pattern_data.get('system_metrics', {})
    recommended_strategy = pattern_data.get('recommended_strategy', {})
    
    hex_name = primary_pattern.get('name', '未知')
    hex_num = primary_pattern.get('number', 0)
    confidence = primary_pattern.get('confidence', 0) * 100
    risk_level = primary_pattern.get('risk_level', 'unknown')
    hex_meaning = primary_pattern.get('description', '暂无描述')
    
    # 卦象象辞（简化版）
    hex_images = {
        8: "地上有水，比；先王以建万国，亲诸侯",
        28: "泽灭木，大过；君子以独立不惧，遁世无闷",
        3: "云雷屯，君子以经纶",
        33: "天下有山，遁；君子以远小人，不恶而严"
    }
    hex_image = hex_images.get(hex_num, "")
    
    # 检测转变
    change_description = "无"
    if len(pattern_history) >= 2:
        prev_pattern = pattern_history[-2].get('primary_pattern', {})
        curr_pattern = pattern_history[-1].get('primary_pattern', {})
        if prev_pattern.get('name') != curr_pattern.get('name'):
            change_description = f"{prev_pattern.get('name')} → {curr_pattern.get('name')} (风险: {prev_pattern.get('risk_level')} → {curr_pattern.get('risk_level')})"
    
    # 策略列表
    strategy_list = ""
    for i, action in enumerate(recommended_strategy.get('actions', [])[:3], 1):
        strategy_list += f"{i}. {action}\n"
    
    # 卦象变化历史表格
    change_table = "| 时间 | 卦象 | 置信度 | 风险 | 成功率 |\n"
    change_table += "|------|------|--------|------|--------|\n"
    for record in pattern_history[-10:]:
        timestamp = record.get('timestamp', '')[:16]
        pattern = record.get('primary_pattern', {})
        metrics = record.get('system_metrics', {})
        change_table += f"| {timestamp} | {pattern.get('name', '?')} | {pattern.get('confidence', 0)*100:.1f}% | {pattern.get('risk_level', '?')} | {metrics.get('success_rate', 0)*100:.1f}% |\n"
    
    # 报警与优化建议
    alert_section = ""
    if alerts:
        for alert in alerts:
            level_emoji = {"critical": "🚨", "warning": "⚠️", "info": "💡"}.get(alert.get('level', 'info'), "ℹ️")
            alert_section += f"{level_emoji} **{alert.get('title', '未知报警')}**\n"
            alert_section += f"{alert.get('body', '')[:200]}...\n\n"
    else:
        alert_section = "✅ 无报警，系统运行正常"
    
    # 明日行动建议
    actions = recommended_strategy.get('actions', [])
    action1 = actions[0] if len(actions) > 0 else "继续保持当前策略"
    action2 = actions[1] if len(actions) > 1 else "监控系统指标"
    action3 = actions[2] if len(actions) > 2 else "记录经验教训"
    
    # 生成报告
    report = f"""# 🚀 AIOS 每日简报 - {date}

## 📊 数据概览

- **任务完成**：{task_stats['completed_tasks']}/{task_stats['total_tasks']} ({task_stats['success_rate']:.1f}%)
- **总成本**：${task_stats['total_cost']:.4f}
- **平均耗时**：{task_stats['avg_time']:.1f}s
- **任务数趋势**：{task_stats['task_trend']}（较昨日{task_stats['task_change']:+.1f}%）
- **系统稳定性**：{task_stats['stability_score']:.1f}%

## 🔮 卦象分析

**当前主卦**：**{hex_name}（第{hex_num}卦）**

**置信度**：{confidence:.1f}%  
**风险等级**：**{risk_level}**  
**成功率（滑动窗口）**：{system_metrics.get('success_rate', 0)*100:.1f}%

> {hex_meaning}

> {hex_image}

**今日关键转变**：{change_description}

## 💡 今日策略（{hex_name}专属）

{strategy_list}

## 📈 卦象变化历史（最近10次）

{change_table}

## ⚠️ 报警与优化建议

{alert_section}

## 🎯 明日行动建议

1. {action1}
2. {action2}
3. {action3}

---

*AIOS 64卦系统 · 生产就绪 · 明天 09:15 自动发送*

*如需手动触发：运行 `python run_pattern_analysis.py --manual`*
"""
    
    return report


def main():
    """生成并保存报告"""
    report = generate_daily_report_v2()
    
    # 保存
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "daily_report_v2.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已生成：{output_file}")
    print("\n" + "="*60)
    print("报告预览：")
    print("="*60)
    print(report)


if __name__ == "__main__":
    main()
