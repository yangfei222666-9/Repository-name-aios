#!/usr/bin/env python3
"""
Pattern Recognizer Wrapper - 使用 task_queue.jsonl 数据
集成修复：
1. 使用滑动窗口代替按小时分组（避免假警报）
2. 集成大过卦报警系统
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 添加 pattern_recognition 到路径
sys.path.insert(0, str(Path(__file__).parent))

# 先导入修复版的 change_detector，替换原版
import change_detector_fixed as change_detector
sys.modules['change_detector'] = change_detector

from pattern_recognizer import PatternRecognizerAgent
from daguo_alert import DaguoAlertSystem
from bigua_optimization import BiguaOptimizationSystem

# 使用修复版的 SystemChangeMonitor
SystemChangeMonitor = change_detector.SystemChangeMonitor

# 猴子补丁：修改 load_recent_tasks 方法
original_load = SystemChangeMonitor.load_recent_tasks

def patched_load_recent_tasks(self, hours: int = 24):
    """加载最近的任务数据（从 task_queue.jsonl）"""
    tasks_file = self.data_dir / "task_queue.jsonl"
    if not tasks_file.exists():
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    tasks = []
    
    with open(tasks_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                task = json.loads(line)
                
                # 只处理已完成的任务
                if task.get("status") != "completed":
                    continue
                
                # 检查时间
                updated_at = task.get("updated_at")
                if updated_at:
                    task_time = datetime.fromtimestamp(updated_at)
                    if task_time < cutoff_time:
                        continue
                
                # 提取关键信息
                result = task.get("result", {})
                timestamp = task_time if updated_at else datetime.now()
                
                # 计算成本（基于 tokens）
                tokens = result.get("tokens", {})
                input_tokens = tokens.get("input", 0)
                output_tokens = tokens.get("output", 0)
                # 假设成本：input $0.003/1K tokens, output $0.015/1K tokens
                cost = (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.015)
                
                tasks.append({
                    "id": task.get("id"),
                    "type": task.get("type"),
                    "status": "completed",
                    "success": result.get("success", True),
                    "duration": result.get("duration", 0),
                    "cost": cost,  # 添加成本字段
                    "tokens": tokens,
                    "timestamp": timestamp.isoformat()  # 转换为 ISO 格式字符串
                })
            except Exception as e:
                continue
    
    return tasks

# 应用补丁
SystemChangeMonitor.load_recent_tasks = patched_load_recent_tasks

def main():
    # 使用 agent_system 目录作为数据源
    data_dir = Path(__file__).parent.parent / "agent_system"
    
    # 初始化 Agent 和报警系统
    agent = PatternRecognizerAgent(data_dir=data_dir)
    daguo_alert = DaguoAlertSystem()
    bigua_optimization = BiguaOptimizationSystem()
    
    # 生成摘要报告
    summary = agent.generate_summary_report()
    print(summary)
    
    # 保存详细报告
    report = agent.analyze_current_state()
    report_file = Path(__file__).parent.parent / "data" / "latest_pattern_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {report_file}")
    
    # 检查大过卦报警
    daguo_alert_result = daguo_alert.check_daguo(report)
    if daguo_alert_result:
        print("\n" + "="*60)
        print("🚨 大过卦报警触发！")
        print("="*60)
        print(daguo_alert_result["body"])
        print("\n💡 报警已记录到 alerts.jsonl，将在下次心跳时发送通知")
    else:
        # 显示当前状态
        if daguo_alert.state["consecutive_daguo_count"] > 0:
            print(f"\n⚠️ 大过卦连续出现 {daguo_alert.state['consecutive_daguo_count']} 次")
            print(f"   （阈值：{daguo_alert.consecutive_threshold} 次）")
    
    # 检查比卦优化建议
    bigua_suggestion = bigua_optimization.check_bigua(report)
    if bigua_suggestion:
        print("\n" + "="*60)
        print("💡 比卦优化建议触发！")
        print("="*60)
        print(bigua_suggestion["body"])
        print("\n💡 建议已记录到 alerts.jsonl，将在下次心跳时发送通知")
    else:
        # 显示当前状态
        if bigua_optimization.state["consecutive_bigua_count"] > 0:
            print(f"\n💡 比卦连续出现 {bigua_optimization.state['consecutive_bigua_count']} 次")
            print(f"   （阈值：{bigua_optimization.consecutive_threshold} 次）")

if __name__ == "__main__":
    main()
