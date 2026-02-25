#!/usr/bin/env python3
"""
AIOS 性能监控脚本
实时监控路由延迟、决策质量、资源使用情况
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import statistics

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class PerformanceMonitor:
    """AIOS 性能监控器"""
    
    def __init__(self, workspace_dir: str = None):
        if workspace_dir is None:
            workspace_dir = Path(__file__).parent.parent
        self.workspace_dir = Path(workspace_dir)
        self.data_dir = self.workspace_dir / "data"
        self.decisions_file = self.data_dir / "router_decisions.jsonl"
        self.sticky_file = self.data_dir / "router_sticky.json"
        
    def load_decisions(self) -> List[Dict[str, Any]]:
        """加载路由决策数据"""
        decisions = []
        if not self.decisions_file.exists():
            return decisions
            
        with open(self.decisions_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        decisions.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return decisions
    
    def analyze_latency(self, decisions: List[Dict]) -> Dict[str, Any]:
        """分析路由延迟"""
        durations = [d.get('duration_ms', 0) for d in decisions]
        
        if not durations:
            return {
                'count': 0,
                'avg': 0,
                'p50': 0,
                'p95': 0,
                'p99': 0,
                'anomalies': []
            }
        
        sorted_durations = sorted(durations)
        n = len(sorted_durations)
        
        # 计算百分位数
        p50 = sorted_durations[int(n * 0.5)] if n > 0 else 0
        p95 = sorted_durations[int(n * 0.95)] if n > 0 else 0
        p99 = sorted_durations[int(n * 0.99)] if n > 0 else 0
        
        # 检测异常（延迟 >10ms）
        anomalies = []
        for i, d in enumerate(decisions):
            duration = d.get('duration_ms', 0)
            if duration > 10:
                anomalies.append({
                    'index': i,
                    'duration_ms': duration,
                    'timestamp': d.get('timestamp', 'unknown'),
                    'task_id': d.get('input_snapshot', {}).get('task_id', 'unknown')
                })
        
        return {
            'count': n,
            'avg': statistics.mean(durations),
            'p50': p50,
            'p95': p95,
            'p99': p99,
            'anomalies': anomalies
        }
    
    def analyze_decision_quality(self, decisions: List[Dict]) -> Dict[str, Any]:
        """分析决策质量"""
        agent_counts = {}
        reason_counts = {}
        confidences = []
        low_confidence_decisions = []
        
        for i, d in enumerate(decisions):
            # 统计 agent 使用频率
            plan = d.get('plan', {})
            decision = d.get('decision', {})
            
            agent = plan.get('agent_type') or decision.get('agent')
            if agent:
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            # 统计 reason_code 频率
            reason_codes = plan.get('reason_codes', [])
            for code in reason_codes:
                reason_counts[code] = reason_counts.get(code, 0) + 1
            
            # 收集置信度
            confidence = plan.get('confidence') or decision.get('confidence')
            if confidence is not None:
                confidences.append(confidence)
                
                # 检测低置信度决策
                if confidence < 0.5:
                    low_confidence_decisions.append({
                        'index': i,
                        'confidence': confidence,
                        'agent': agent,
                        'timestamp': d.get('timestamp', 'unknown'),
                        'task_id': d.get('input_snapshot', {}).get('task_id', 'unknown')
                    })
        
        avg_confidence = statistics.mean(confidences) if confidences else 0
        
        return {
            'agent_usage': agent_counts,
            'reason_codes': reason_counts,
            'avg_confidence': avg_confidence,
            'low_confidence_count': len(low_confidence_decisions),
            'low_confidence_decisions': low_confidence_decisions
        }
    
    def analyze_resources(self) -> Dict[str, Any]:
        """分析资源使用"""
        resources = {
            'files': {},
            'cpu_usage': None,
            'memory_usage': None,
            'anomalies': []
        }
        
        # 文件大小
        if self.decisions_file.exists():
            size_bytes = self.decisions_file.stat().st_size
            resources['files']['router_decisions.jsonl'] = {
                'size_bytes': size_bytes,
                'size_kb': round(size_bytes / 1024, 2),
                'size_mb': round(size_bytes / (1024 * 1024), 2)
            }
        
        if self.sticky_file.exists():
            size_bytes = self.sticky_file.stat().st_size
            resources['files']['router_sticky.json'] = {
                'size_bytes': size_bytes,
                'size_kb': round(size_bytes / 1024, 2),
                'size_mb': round(size_bytes / (1024 * 1024), 2)
            }
        
        # CPU/内存使用率（跨平台）
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            resources['cpu_usage'] = cpu_percent
            resources['memory_usage'] = memory_percent
            
            # 检测资源异常
            if cpu_percent > 80:
                resources['anomalies'].append({
                    'type': 'high_cpu',
                    'value': cpu_percent,
                    'threshold': 80
                })
            
            if memory_percent > 80:
                resources['anomalies'].append({
                    'type': 'high_memory',
                    'value': memory_percent,
                    'threshold': 80
                })
        except ImportError:
            resources['note'] = 'psutil not installed, CPU/memory monitoring unavailable'
        
        return resources
    
    def generate_report(self) -> str:
        """生成性能报告"""
        decisions = self.load_decisions()
        latency = self.analyze_latency(decisions)
        quality = self.analyze_decision_quality(decisions)
        resources = self.analyze_resources()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""# AIOS 性能监控报告

生成时间：{timestamp}

## 1. 路由延迟统计

- 决策总数：{latency['count']}
- 平均延迟：{latency['avg']:.2f} ms
- P50 延迟：{latency['p50']:.2f} ms
- P95 延迟：{latency['p95']:.2f} ms
- P99 延迟：{latency['p99']:.2f} ms
- 异常数量（>10ms）：{len(latency['anomalies'])}

"""
        
        if latency['anomalies']:
            report += "### 延迟异常详情\n\n"
            for anomaly in latency['anomalies'][:5]:  # 只显示前5个
                report += f"- Task {anomaly['task_id']}: {anomaly['duration_ms']:.2f} ms @ {anomaly['timestamp']}\n"
            if len(latency['anomalies']) > 5:
                report += f"- ... 还有 {len(latency['anomalies']) - 5} 个异常\n"
            report += "\n"
        
        report += f"""## 2. 决策质量分析

- 平均置信度：{quality['avg_confidence']:.2f}
- 低置信度决策数（<0.5）：{quality['low_confidence_count']}

### Agent 使用频率

"""
        
        for agent, count in sorted(quality['agent_usage'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / latency['count'] * 100) if latency['count'] > 0 else 0
            report += f"- {agent}: {count} 次 ({percentage:.1f}%)\n"
        
        report += "\n### Reason Code 频率\n\n"
        
        for code, count in sorted(quality['reason_codes'].items(), key=lambda x: x[1], reverse=True):
            report += f"- {code}: {count} 次\n"
        
        if quality['low_confidence_decisions']:
            report += "\n### 低置信度决策详情\n\n"
            for decision in quality['low_confidence_decisions'][:5]:
                report += f"- Task {decision['task_id']}: 置信度 {decision['confidence']:.2f}, Agent: {decision['agent']}\n"
            if len(quality['low_confidence_decisions']) > 5:
                report += f"- ... 还有 {len(quality['low_confidence_decisions']) - 5} 个低置信度决策\n"
        
        report += "\n## 3. 资源使用情况\n\n"
        
        if resources['cpu_usage'] is not None:
            report += f"- CPU 使用率：{resources['cpu_usage']:.1f}%\n"
        if resources['memory_usage'] is not None:
            report += f"- 内存使用率：{resources['memory_usage']:.1f}%\n"
        
        if 'note' in resources:
            report += f"\n注意：{resources['note']}\n"
        
        report += "\n### 文件大小\n\n"
        
        for filename, info in resources['files'].items():
            report += f"- {filename}: {info['size_kb']:.2f} KB ({info['size_bytes']} bytes)\n"
        
        if resources['anomalies']:
            report += "\n### 资源异常告警\n\n"
            for anomaly in resources['anomalies']:
                report += f"- ⚠️ {anomaly['type']}: {anomaly['value']:.1f}% (阈值: {anomaly['threshold']}%)\n"
        
        report += "\n## 4. 优化建议\n\n"
        
        suggestions = []
        
        # 基于延迟的建议
        if latency['avg'] > 5:
            suggestions.append("- 平均延迟较高，考虑优化路由决策算法")
        if len(latency['anomalies']) > latency['count'] * 0.1:
            suggestions.append("- 延迟异常比例较高（>10%），检查是否有性能瓶颈")
        
        # 基于决策质量的建议
        if quality['avg_confidence'] < 0.7:
            suggestions.append("- 平均置信度偏低，考虑优化决策规则或增加训练数据")
        if quality['low_confidence_count'] > latency['count'] * 0.2:
            suggestions.append("- 低置信度决策过多（>20%），需要审查决策逻辑")
        
        # 基于资源的建议
        for anomaly in resources['anomalies']:
            if anomaly['type'] == 'high_cpu':
                suggestions.append("- CPU 使用率过高，考虑优化计算密集型操作")
            elif anomaly['type'] == 'high_memory':
                suggestions.append("- 内存使用率过高，检查是否有内存泄漏")
        
        # 基于文件大小的建议
        for filename, info in resources['files'].items():
            if info['size_mb'] > 10:
                suggestions.append(f"- {filename} 文件较大（{info['size_mb']:.2f} MB），考虑定期归档或清理")
        
        if not suggestions:
            suggestions.append("- 系统运行正常，暂无优化建议")
        
        report += "\n".join(suggestions)
        report += "\n"
        
        return report
    
    def run(self):
        """运行监控并生成报告"""
        print("正在分析 AIOS 性能数据...")
        
        report = self.generate_report()
        
        # 保存报告
        report_file = self.data_dir / "performance_report.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[OK] 性能报告已生成：{report_file}")
        print("\n" + "="*60)
        print(report)
        print("="*60)
        
        return report


if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.run()
