#!/usr/bin/env python3
"""
比卦优化建议系统
当系统进入"比卦"状态时，发送协作优化建议（非紧急报警）
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class BiguaOptimizationSystem:
    """比卦优化建议系统"""
    
    def __init__(self, alert_file: Path = None):
        if alert_file is None:
            alert_file = Path(__file__).parent.parent / "agent_system" / "alerts.jsonl"
        self.alert_file = Path(alert_file)
        self.alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 比卦相关配置
        self.bigua_number = 8
        self.bigua_name = "比卦"
        self.confidence_threshold = 0.75  # 置信度阈值
        self.consecutive_threshold = 2  # 连续出现次数阈值
        
        # 状态文件
        self.state_file = Path(__file__).parent.parent / "data" / "bigua_state.json"
        self.load_state()
    
    def load_state(self):
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "consecutive_bigua_count": 0,
                "last_bigua_time": None,
                "total_bigua_count": 0,
                "last_suggestion_time": None
            }
    
    def save_state(self):
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def check_bigua(self, pattern_report: Dict) -> Optional[Dict]:
        """
        检查是否为比卦
        
        Args:
            pattern_report: pattern_recognizer 生成的报告
        
        Returns:
            如果需要发送建议，返回建议信息；否则返回 None
        """
        if pattern_report.get("status") != "success":
            return None
        
        primary_pattern = pattern_report.get("primary_pattern", {})
        pattern_number = primary_pattern.get("number")
        confidence = primary_pattern.get("confidence", 0)
        
        # 检查是否为比卦
        if pattern_number == self.bigua_number and confidence >= self.confidence_threshold:
            # 更新状态
            self.state["consecutive_bigua_count"] += 1
            self.state["last_bigua_time"] = datetime.now().isoformat()
            self.state["total_bigua_count"] += 1
            
            # 判断是否需要发送建议
            if self.state["consecutive_bigua_count"] >= self.consecutive_threshold:
                suggestion = self._generate_suggestion(pattern_report)
                self.state["last_suggestion_time"] = datetime.now().isoformat()
                self.save_state()
                return suggestion
            
            self.save_state()
            return None
        else:
            # 重置连续计数
            if self.state["consecutive_bigua_count"] > 0:
                self.state["consecutive_bigua_count"] = 0
                self.save_state()
            return None
    
    def _generate_suggestion(self, pattern_report: Dict) -> Dict:
        """生成优化建议"""
        primary_pattern = pattern_report.get("primary_pattern", {})
        system_metrics = pattern_report.get("system_metrics", {})
        
        # 构建建议消息
        suggestion_message = f"""💡 比卦协作优化建议

【卦象信息】
  {primary_pattern.get('name')} (第{primary_pattern.get('number')}卦)
  {primary_pattern.get('description')}
  置信度: {primary_pattern.get('confidence', 0)*100:.1f}%
  风险等级: {primary_pattern.get('risk_level')}

【系统状态】
  成功率: {system_metrics.get('success_rate', 0)*100:.1f}%
  稳定性: {system_metrics.get('stability', 0)*100:.1f}%
  资源使用: {system_metrics.get('resource_usage', 0)*100:.1f}%

【连续出现】
  连续次数: {self.state['consecutive_bigua_count']}
  总出现次数: {self.state['total_bigua_count']}

【优化建议】（当前系统协作状态良好，适合）

1️⃣ 巩固亲比（最重要）
  • 启用资源共享模式（embedding、缓存共享）
  • 每5分钟做一次比卦心跳（Agent负载广播）

2️⃣ 建万国（生态扩张）
  • 招募1-2个新Agent（专攻复盘/优化）
  • 实施协作奖励机制（亲密度积分）

3️⃣ 防微杜渐（持续监控）
  • 监控置信度（<65%触发预警）
  • 生成比卦日报（Top3最亲密Agent）

4️⃣ 事后学习
  • 记录从危机到协作的完整轨迹
  • 更新知识库供未来参考

【象辞】
  地上有水，比；先王以建万国，亲诸侯。
  
💡 系统建议：趁low risk，主动扩张生态，强化协作。
"""
        
        # 创建建议记录
        suggestion = {
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "title": f"💡 比卦协作优化建议（第{self.state['consecutive_bigua_count']}次）",
            "body": suggestion_message,
            "sent": False,
            "metadata": {
                "pattern_number": primary_pattern.get('number'),
                "pattern_name": primary_pattern.get('name'),
                "confidence": primary_pattern.get('confidence'),
                "risk_level": primary_pattern.get('risk_level'),
                "consecutive_count": self.state['consecutive_bigua_count'],
                "system_metrics": system_metrics,
                "suggestion_type": "optimization"
            }
        }
        
        # 保存到 alerts.jsonl
        with open(self.alert_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(suggestion, ensure_ascii=False) + '\n')
        
        return suggestion


def main():
    """测试比卦优化建议系统"""
    import sys
    
    optimization_system = BiguaOptimizationSystem()
    
    if len(sys.argv) < 2:
        print("Usage: python bigua_optimization.py <pattern_report.json>")
        sys.exit(1)
    
    report_file = Path(sys.argv[1])
    if not report_file.exists():
        print(f"Error: {report_file} not found")
        sys.exit(1)
    
    with open(report_file, 'r', encoding='utf-8') as f:
        pattern_report = json.load(f)
    
    # 检查比卦
    suggestion = optimization_system.check_bigua(pattern_report)
    
    if suggestion:
        print("💡 比卦优化建议触发！")
        print(json.dumps(suggestion, indent=2, ensure_ascii=False))
    else:
        print("✅ 无需发送建议")
        print(f"当前状态: {json.dumps(optimization_system.state, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
