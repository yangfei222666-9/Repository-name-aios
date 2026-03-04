#!/usr/bin/env python3
"""
大过卦报警系统
当系统进入"大过卦"状态时，立即触发报警并执行自愈策略
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class DaguoAlertSystem:
    """大过卦报警系统"""
    
    def __init__(self, alert_file: Path = None):
        if alert_file is None:
            alert_file = Path(__file__).parent.parent / "agent_system" / "alerts.jsonl"
        self.alert_file = Path(alert_file)
        self.alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 大过卦相关配置
        self.daguo_number = 28
        self.daguo_name = "大过卦"
        self.alert_threshold = 0.7  # 置信度阈值
        self.consecutive_threshold = 2  # 连续出现次数阈值
        
        # 状态文件
        self.state_file = Path(__file__).parent.parent / "data" / "daguo_state.json"
        self.load_state()
    
    def load_state(self):
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "consecutive_daguo_count": 0,
                "last_daguo_time": None,
                "total_daguo_count": 0,
                "last_alert_time": None
            }
    
    def save_state(self):
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def check_daguo(self, pattern_report: Dict) -> Optional[Dict]:
        """
        检查是否为大过卦
        
        Args:
            pattern_report: pattern_recognizer 生成的报告
        
        Returns:
            如果需要报警，返回报警信息；否则返回 None
        """
        if pattern_report.get("status") != "success":
            return None
        
        primary_pattern = pattern_report.get("primary_pattern", {})
        pattern_number = primary_pattern.get("number")
        pattern_name = primary_pattern.get("name")
        confidence = primary_pattern.get("confidence", 0)
        risk_level = primary_pattern.get("risk_level", "low")
        
        # 检查是否为大过卦
        if pattern_number == self.daguo_number and confidence >= self.alert_threshold:
            # 更新状态
            self.state["consecutive_daguo_count"] += 1
            self.state["last_daguo_time"] = datetime.now().isoformat()
            self.state["total_daguo_count"] += 1
            
            # 判断是否需要报警
            if self.state["consecutive_daguo_count"] >= self.consecutive_threshold:
                alert = self._generate_alert(pattern_report)
                self.state["last_alert_time"] = datetime.now().isoformat()
                self.save_state()
                return alert
            
            self.save_state()
            return None
        else:
            # 重置连续计数
            if self.state["consecutive_daguo_count"] > 0:
                self.state["consecutive_daguo_count"] = 0
                self.save_state()
            return None
    
    def _generate_alert(self, pattern_report: Dict) -> Dict:
        """生成报警信息"""
        primary_pattern = pattern_report.get("primary_pattern", {})
        system_metrics = pattern_report.get("system_metrics", {})
        recommended_strategy = pattern_report.get("recommended_strategy", {})
        
        # 构建报警消息
        alert_message = f"""⚠️ 大过卦持续预警！

【卦象信息】
  {primary_pattern.get('name')} (第{primary_pattern.get('number')}卦)
  {primary_pattern.get('description')}
  置信度: {primary_pattern.get('confidence', 0)*100:.1f}%
  风险等级: {primary_pattern.get('risk_level')}

【系统指标】
  成功率: {system_metrics.get('success_rate', 0)*100:.1f}%
  增长率: {system_metrics.get('growth_rate', 0)*100:+.1f}%
  稳定性: {system_metrics.get('stability', 0)*100:.1f}%
  资源使用: {system_metrics.get('resource_usage', 0)*100:.1f}%

【连续出现】
  连续次数: {self.state['consecutive_daguo_count']}
  总出现次数: {self.state['total_daguo_count']}

【推荐策略】
  优先级: {recommended_strategy.get('priority')}
  模型偏好: {recommended_strategy.get('model_preference')}
  风险容忍度: {recommended_strategy.get('risk_tolerance')}

【建议行动】（立即执行）
"""
        
        for action in recommended_strategy.get('actions', []):
            alert_message += f"  • {action}\n"
        
        alert_message += "\n💡 大过卦象辞：泽灭木，大过。君子以独立不惧，遁世无闷。"
        alert_message += "\n🔧 系统建议：立即减负、加固梁柱、必要时求助外部。"
        
        # 创建报警记录
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": "critical",
            "title": f"⚠️ 大过卦持续预警（第{self.state['consecutive_daguo_count']}次）",
            "body": alert_message,
            "sent": False,
            "metadata": {
                "pattern_number": primary_pattern.get('number'),
                "pattern_name": primary_pattern.get('name'),
                "confidence": primary_pattern.get('confidence'),
                "risk_level": primary_pattern.get('risk_level'),
                "consecutive_count": self.state['consecutive_daguo_count'],
                "system_metrics": system_metrics
            }
        }
        
        # 保存到 alerts.jsonl
        with open(self.alert_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(alert, ensure_ascii=False) + '\n')
        
        return alert
    
    def get_self_healing_actions(self, pattern_report: Dict) -> Dict:
        """
        生成自愈行动清单
        
        Returns:
            自愈行动的详细配置
        """
        return {
            "immediate_actions": [
                {
                    "action": "reduce_task_generation",
                    "description": "暂停非核心任务生成10-15分钟",
                    "priority": 1,
                    "command": "python agents/task_scheduler.py pause --duration 15"
                },
                {
                    "action": "prioritize_backlog",
                    "description": "优先执行已堆积的高价值任务",
                    "priority": 2,
                    "command": "python agents/task_scheduler.py prioritize --strategy value"
                }
            ],
            "reinforcement_actions": [
                {
                    "action": "increase_timeout",
                    "description": "增加任务超时时间（60s → 120s）",
                    "priority": 3,
                    "command": "python agents/task_scheduler.py set-timeout 120"
                },
                {
                    "action": "check_task_loops",
                    "description": "检查是否出现任务死循环/重复生成",
                    "priority": 4,
                    "command": "python agents/task_scheduler.py check-loops"
                }
            ],
            "escalation_actions": [
                {
                    "action": "request_help",
                    "description": "如果大过卦持续>3次，拉起协作求援模式",
                    "priority": 5,
                    "condition": "consecutive_count >= 3",
                    "command": "python agents/collaboration_agent.py request-help --reason daguo"
                }
            ],
            "post_recovery_actions": [
                {
                    "action": "log_incident",
                    "description": "记录本次大过卦的触发特征",
                    "priority": 6,
                    "command": "python agents/incident_logger.py log --pattern daguo"
                }
            ]
        }


def main():
    """测试大过卦报警系统"""
    import sys
    
    alert_system = DaguoAlertSystem()
    
    if len(sys.argv) < 2:
        print("Usage: python daguo_alert.py <pattern_report.json>")
        sys.exit(1)
    
    report_file = Path(sys.argv[1])
    if not report_file.exists():
        print(f"Error: {report_file} not found")
        sys.exit(1)
    
    with open(report_file, 'r', encoding='utf-8') as f:
        pattern_report = json.load(f)
    
    # 检查大过卦
    alert = alert_system.check_daguo(pattern_report)
    
    if alert:
        print("🚨 大过卦报警触发！")
        print(json.dumps(alert, indent=2, ensure_ascii=False))
        
        # 生成自愈行动
        actions = alert_system.get_self_healing_actions(pattern_report)
        print("\n🔧 自愈行动清单：")
        print(json.dumps(actions, indent=2, ensure_ascii=False))
    else:
        print("✅ 无需报警")
        print(f"当前状态: {json.dumps(alert_system.state, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
