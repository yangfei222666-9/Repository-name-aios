#!/usr/bin/env python3
"""
Router 监控脚本 - 集成到 Heartbeat 和每日简报
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

def get_router_stats(hours: int = 24) -> dict:
    """获取 Router 统计数据（最近 N 小时）"""
    log_file = Path(__file__).parent / "router_decisions.jsonl"
    
    if not log_file.exists():
        return {
            "total": 0,
            "fast": 0,
            "slow": 0,
            "fast_ratio": 0.0,
            "slow_ratio": 0.0,
            "kun_gua_bonus": 0,
            "evolution_low": 0
        }
    
    # 读取最近 N 小时的决策
    cutoff_time = datetime.now() - timedelta(hours=hours)
    decisions = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                timestamp = datetime.fromisoformat(record.get('timestamp', ''))
                if timestamp >= cutoff_time:
                    decisions.append(record)
            except:
                continue
    
    if not decisions:
        return {
            "total": 0,
            "fast": 0,
            "slow": 0,
            "fast_ratio": 0.0,
            "slow_ratio": 0.0,
            "kun_gua_bonus": 0,
            "evolution_low": 0
        }
    
    # 统计
    total = len(decisions)
    fast = sum(1 for d in decisions if d.get('model') == 'fast')
    slow = sum(1 for d in decisions if d.get('model') == 'slow')
    kun_gua_bonus = sum(1 for d in decisions if d.get('gua_bonus', 0) > 0)
    evolution_low = sum(1 for d in decisions if d.get('evolution_conf', 1.0) < 0.90)
    
    return {
        "total": total,
        "fast": fast,
        "slow": slow,
        "fast_ratio": fast / total if total > 0 else 0.0,
        "slow_ratio": slow / total if total > 0 else 0.0,
        "kun_gua_bonus": kun_gua_bonus,
        "evolution_low": evolution_low
    }

def generate_router_report(hours: int = 24) -> str:
    """生成 Router 报告（Markdown 格式）"""
    stats = get_router_stats(hours)
    
    if stats['total'] == 0:
        return "📊 **Router 统计：** 暂无数据\n"
    
    report = f"""
📊 **Router 统计（最近 {hours} 小时）**

- **总决策数：** {stats['total']}
- **Fast 模型：** {stats['fast']} ({stats['fast_ratio']*100:.1f}%)
- **Slow 模型：** {stats['slow']} ({stats['slow_ratio']*100:.1f}%)
- **坤卦加成：** {stats['kun_gua_bonus']} 次
- **低置信强制慢模型：** {stats['evolution_low']} 次

**预期成本节省：** {stats['fast_ratio']*100:.1f}% 任务用 Fast 模型 → 节省约 {stats['fast_ratio']*35:.1f}% 成本
"""
    
    return report.strip()

def log_router_decision(task_id: str, model: str, complexity: float, 
                       evolution_conf: float, current_gua: str, gua_bonus: float):
    """记录 Router 决策到日志"""
    log_file = Path(__file__).parent / "router_decisions.jsonl"
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "model": model,
        "complexity": complexity,
        "evolution_conf": evolution_conf,
        "current_gua": current_gua,
        "gua_bonus": gua_bonus
    }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    # 测试
    print(generate_router_report(24))
