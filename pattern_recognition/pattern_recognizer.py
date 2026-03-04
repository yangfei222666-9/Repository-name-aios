"""
PatternRecognizer Agent - 模式识别Agent
基于易经64卦理论，识别系统状态模式并推荐应对策略
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from change_detector import SystemChangeMonitor, ChangeDetector
from hexagram_patterns import HexagramMatcher, get_strategy_for_state, HEXAGRAM_PATTERNS


class PatternRecognizerAgent:
    """模式识别Agent - 识别系统状态并推荐策略"""
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        
        # 初始化组件
        self.change_monitor = SystemChangeMonitor(data_dir)
        self.hexagram_matcher = HexagramMatcher()
        
        # 状态历史
        self.state_history_file = self.data_dir / "pattern_history.jsonl"
        self.state_history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def analyze_current_state(self) -> Dict:
        """
        分析当前系统状态
        
        Returns:
            完整的分析报告
        """
        # 1. 加载最近任务数据
        tasks = self.change_monitor.load_recent_tasks(hours=24)
        
        if not tasks:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "no_data",
                "message": "没有足够的任务数据进行分析",
            }
        
        # 2. 更新变化检测器
        self.change_monitor.update_from_tasks(tasks)
        
        # 3. 获取所有指标趋势
        trends = self.change_monitor.get_all_trends()
        
        # 4. 计算系统指标（用于卦象匹配）
        system_metrics = self._calculate_system_metrics(trends)
        
        # 5. 匹配卦象
        pattern, confidence = self.hexagram_matcher.match(system_metrics)
        
        # 6. 获取前3个最匹配的卦象
        top_matches = self.hexagram_matcher.get_top_matches(system_metrics, top_n=3)
        
        # 7. 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "data_points": len(tasks),
            "time_range_hours": 24,
            
            # 趋势分析
            "trends": trends,
            
            # 系统指标
            "system_metrics": system_metrics,
            
            # 最佳匹配卦象
            "primary_pattern": {
                "name": pattern.name,
                "number": pattern.number,
                "description": pattern.description,
                "confidence": round(confidence, 3),
                "risk_level": pattern.risk_level,
            },
            
            # 备选卦象
            "alternative_patterns": [
                {
                    "name": p.name,
                    "number": p.number,
                    "confidence": round(c, 3),
                }
                for p, c in top_matches[1:3]
            ],
            
            # 推荐策略
            "recommended_strategy": pattern.strategy,
        }
        
        # 8. 保存到历史
        self._save_to_history(report)
        
        return report
    
    def _calculate_system_metrics(self, trends: Dict) -> Dict:
        """从趋势数据计算系统指标"""
        success_rate = trends["success_rate"]["current_value"] or 0.5
        error_rate = trends["error_rate"]["current_value"] or 0.5
        
        # 计算增长率（基于趋势）
        success_trend = trends["success_rate"]["trend"]
        if success_trend == ChangeDetector.TREND_RISING:
            growth_rate = 0.2
        elif success_trend == ChangeDetector.TREND_FALLING:
            growth_rate = -0.2
        else:
            growth_rate = 0.0
        
        # 计算稳定性（基于标准差）
        success_std = trends["success_rate"]["std_dev"] or 0.1
        stability = max(0, 1.0 - success_std * 2)
        
        # 计算资源使用率（基于成本和耗时）
        avg_duration = trends["avg_duration"]["current_value"] or 30
        avg_cost = trends["cost"]["current_value"] or 0.01
        
        # 归一化资源使用率（假设30s和0.01$是基准）
        duration_ratio = min(avg_duration / 30, 2.0)
        cost_ratio = min(avg_cost / 0.01, 2.0)
        resource_usage = (duration_ratio + cost_ratio) / 4  # 0-1范围
        
        return {
            "success_rate": success_rate,
            "growth_rate": growth_rate,
            "stability": stability,
            "resource_usage": resource_usage,
        }
    
    def _save_to_history(self, report: Dict):
        """保存分析报告到历史"""
        with open(self.state_history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False) + "\n")
    
    def get_recent_patterns(self, hours: int = 24) -> List[Dict]:
        """获取最近的模式历史"""
        if not self.state_history_file.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        patterns = []
        
        with open(self.state_history_file, "r", encoding="utf-8") as f:
            for line in f:
                report = json.loads(line)
                report_time = datetime.fromisoformat(report["timestamp"])
                if report_time >= cutoff_time:
                    patterns.append(report)
        
        return patterns
    
    def detect_pattern_shift(self) -> Optional[Dict]:
        """
        检测模式转变（卦象变化）
        
        Returns:
            如果检测到转变，返回转变信息；否则返回None
        """
        recent = self.get_recent_patterns(hours=24)
        if len(recent) < 2:
            return None
        
        # 比较最新和前一个
        current = recent[-1]
        previous = recent[-2]
        
        current_pattern = current.get("primary_pattern", {}).get("name")
        previous_pattern = previous.get("primary_pattern", {}).get("name")
        
        if current_pattern != previous_pattern:
            return {
                "timestamp": datetime.now().isoformat(),
                "shift_detected": True,
                "from_pattern": previous_pattern,
                "to_pattern": current_pattern,
                "from_risk": previous.get("primary_pattern", {}).get("risk_level"),
                "to_risk": current.get("primary_pattern", {}).get("risk_level"),
                "message": f"系统状态从 {previous_pattern} 转变为 {current_pattern}",
            }
        
        return None
    
    def generate_summary_report(self) -> str:
        """生成人类可读的摘要报告"""
        report = self.analyze_current_state()
        
        if report["status"] == "no_data":
            return report["message"]
        
        # 格式化输出
        lines = [
            "=== AIOS 模式识别报告 ===",
            f"时间: {report['timestamp']}",
            f"数据点: {report['data_points']} 个任务（最近24小时）",
            "",
            "【当前卦象】",
            f"  {report['primary_pattern']['name']} (第{report['primary_pattern']['number']}卦)",
            f"  {report['primary_pattern']['description']}",
            f"  置信度: {report['primary_pattern']['confidence'] * 100:.1f}%",
            f"  风险等级: {report['primary_pattern']['risk_level']}",
            "",
            "【系统指标】",
            f"  成功率: {report['system_metrics']['success_rate'] * 100:.1f}%",
            f"  增长率: {report['system_metrics']['growth_rate'] * 100:+.1f}%",
            f"  稳定性: {report['system_metrics']['stability'] * 100:.1f}%",
            f"  资源使用: {report['system_metrics']['resource_usage'] * 100:.1f}%",
            "",
            "【趋势分析】",
        ]
        
        for metric, trend_data in report["trends"].items():
            trend = trend_data["trend"]
            confidence = trend_data["confidence"]
            lines.append(f"  {metric}: {trend} (置信度: {confidence * 100:.1f}%)")
        
        lines.extend([
            "",
            "【推荐策略】",
            f"  优先级: {report['recommended_strategy']['priority']}",
            f"  模型偏好: {report['recommended_strategy']['model_preference']}",
            f"  风险容忍度: {report['recommended_strategy']['risk_tolerance']}",
            "  建议行动:",
        ])
        
        for action in report['recommended_strategy']['actions']:
            lines.append(f"    - {action}")
        
        # 检测模式转变
        shift = self.detect_pattern_shift()
        if shift:
            lines.extend([
                "",
                "【⚠️ 模式转变检测】",
                f"  {shift['message']}",
                f"  风险变化: {shift['from_risk']} → {shift['to_risk']}",
            ])
        
        return "\n".join(lines)


def main():
    """测试 PatternRecognizer Agent"""
    print("=== PatternRecognizer Agent 测试 ===\n")
    
    agent = PatternRecognizerAgent()
    
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


if __name__ == "__main__":
    main()
