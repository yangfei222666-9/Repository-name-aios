#!/usr/bin/env python3
"""
AIOS v0.5 性能深度分析工具
分析所有事件日志，生成完整的性能报告
"""

import json
import os
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import statistics

class PerformanceAnalyzer:
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.events = []
        self.reactor_logs = []
        self.execution_logs = []
        
        # 统计数据
        self.stats = {
            'total_events': 0,
            'by_layer': defaultdict(int),
            'by_event_type': defaultdict(int),
            'by_status': defaultdict(int),
            'latency_by_event': defaultdict(list),
            'errors': [],
            'cpu_spikes': [],
            'reactor_performance': {
                'total': 0,
                'success': 0,
                'failed': 0,
                'by_playbook': defaultdict(lambda: {'success': 0, 'failed': 0})
            },
            'execution_states': defaultdict(int),
            'action_performance': {
                'enqueued': 0,
                'succeeded': 0,
                'failed': 0,
                'skipped': 0,
                'by_type': defaultdict(lambda: {'success': 0, 'failed': 0})
            }
        }
    
    def load_jsonl(self, filepath: Path) -> List[Dict]:
        """加载 JSONL 文件"""
        data = []
        if not filepath.exists():
            return data
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"JSON 解析错误 {filepath}: {e}")
        return data
    
    def load_all_events(self):
        """加载所有事件文件"""
        event_files = [
            self.workspace / 'events.jsonl',
            self.workspace / 'events' / 'events.jsonl',
            self.workspace / 'data' / 'events.jsonl',
        ]
        
        for filepath in event_files:
            events = self.load_jsonl(filepath)
            self.events.extend(events)
            print(f"加载 {filepath.name}: {len(events)} 条事件")
        
        # 加载 reactor 日志
        reactor_file = self.workspace / 'reactor_log.jsonl'
        self.reactor_logs = self.load_jsonl(reactor_file)
        print(f"加载 reactor_log.jsonl: {len(self.reactor_logs)} 条记录")
        
        # 加载执行日志
        exec_file = self.workspace / 'events' / 'execution_log.jsonl'
        self.execution_logs = self.load_jsonl(exec_file)
        print(f"加载 execution_log.jsonl: {len(self.execution_logs)} 条记录")
    
    def analyze_events(self):
        """分析事件数据"""
        self.stats['total_events'] = len(self.events)
        
        for event in self.events:
            # 按层统计
            layer = event.get('layer', 'UNKNOWN')
            self.stats['by_layer'][layer] += 1
            
            # 按事件类型统计
            event_type = event.get('event') or event.get('type', 'unknown')
            self.stats['by_event_type'][event_type] += 1
            
            # 按状态统计
            status = event.get('status', 'unknown')
            self.stats['by_status'][status] += 1
            
            # 延迟统计
            latency = event.get('latency_ms')
            if latency is not None:
                self.stats['latency_by_event'][event_type].append(latency)
            
            # 错误收集
            if status in ['err', 'error']:
                self.stats['errors'].append({
                    'timestamp': event.get('ts') or event.get('timestamp'),
                    'layer': layer,
                    'event': event_type,
                    'payload': event.get('payload', {})
                })
            
            # CPU 峰值
            if event_type in ['cpu_high', 'resource.cpu_spike']:
                cpu_percent = event.get('payload', {}).get('cpu_percent')
                self.stats['cpu_spikes'].append({
                    'timestamp': event.get('ts') or event.get('timestamp'),
                    'cpu_percent': cpu_percent
                })
            
            # Action 性能
            if 'action_enqueued' in event_type:
                self.stats['action_performance']['enqueued'] += 1
            elif 'action_succeeded' in event_type:
                self.stats['action_performance']['succeeded'] += 1
                action_type = event.get('payload', {}).get('type', 'unknown')
                self.stats['action_performance']['by_type'][action_type]['success'] += 1
            elif 'action_failed' in event_type:
                self.stats['action_performance']['failed'] += 1
                action_type = event.get('payload', {}).get('type', 'unknown')
                self.stats['action_performance']['by_type'][action_type]['failed'] += 1
            elif 'action_skipped' in event_type:
                self.stats['action_performance']['skipped'] += 1
    
    def analyze_reactor(self):
        """分析 Reactor 性能"""
        for log in self.reactor_logs:
            self.stats['reactor_performance']['total'] += 1
            
            status = log.get('status')
            playbook_id = log.get('playbook_id', 'unknown')
            
            if status == 'success':
                self.stats['reactor_performance']['success'] += 1
                self.stats['reactor_performance']['by_playbook'][playbook_id]['success'] += 1
            elif status == 'failed':
                self.stats['reactor_performance']['failed'] += 1
                self.stats['reactor_performance']['by_playbook'][playbook_id]['failed'] += 1
    
    def analyze_execution(self):
        """分析执行日志"""
        for log in self.execution_logs:
            state = log.get('terminal_state', 'UNKNOWN')
            self.stats['execution_states'][state] += 1
    
    def calculate_latency_stats(self, latencies: List[float]) -> Dict:
        """计算延迟统计"""
        if not latencies:
            return {}
        
        return {
            'count': len(latencies),
            'min': min(latencies),
            'max': max(latencies),
            'mean': statistics.mean(latencies),
            'median': statistics.median(latencies),
            'p95': sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0],
            'p99': sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]
        }
    
    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 1. 错误率分析
        error_rate = self.stats['by_status']['err'] / max(self.stats['total_events'], 1) * 100
        if error_rate > 10:
            recommendations.append(f"🔴 错误率过高 ({error_rate:.1f}%)，需要加强错误处理和重试机制")
        elif error_rate > 5:
            recommendations.append(f"🟡 错误率偏高 ({error_rate:.1f}%)，建议优化错误恢复策略")
        
        # 2. Reactor 成功率
        if self.stats['reactor_performance']['total'] > 0:
            reactor_success_rate = self.stats['reactor_performance']['success'] / self.stats['reactor_performance']['total'] * 100
            if reactor_success_rate < 80:
                recommendations.append(f"🔴 Reactor 成功率过低 ({reactor_success_rate:.1f}%)，需要修复失败的 Playbook")
            
            # 识别失败的 Playbook
            for playbook_id, stats in self.stats['reactor_performance']['by_playbook'].items():
                total = stats['success'] + stats['failed']
                if total > 0 and stats['failed'] / total > 0.5:
                    recommendations.append(f"🔴 Playbook '{playbook_id}' 失败率过高，需要修复")
        
        # 3. CPU 峰值分析
        if len(self.stats['cpu_spikes']) > 5:
            avg_cpu = statistics.mean([s['cpu_percent'] for s in self.stats['cpu_spikes'] if s['cpu_percent']])
            recommendations.append(f"⚠️ 检测到 {len(self.stats['cpu_spikes'])} 次 CPU 峰值（平均 {avg_cpu:.1f}%），建议优化资源密集型操作")
        
        # 4. 延迟分析
        slow_events = []
        for event_type, latencies in self.stats['latency_by_event'].items():
            stats = self.calculate_latency_stats(latencies)
            if stats.get('p95', 0) > 1000:  # P95 > 1s
                slow_events.append((event_type, stats['p95']))
        
        if slow_events:
            recommendations.append(f"🐌 发现 {len(slow_events)} 种慢事件（P95 > 1s），需要性能优化")
            for event, p95 in sorted(slow_events, key=lambda x: x[1], reverse=True)[:3]:
                recommendations.append(f"   - {event}: P95 = {p95:.0f}ms")
        
        # 5. Action 执行效率
        if self.stats['action_performance']['enqueued'] > 0:
            skip_rate = self.stats['action_performance']['skipped'] / self.stats['action_performance']['enqueued'] * 100
            fail_rate = self.stats['action_performance']['failed'] / self.stats['action_performance']['enqueued'] * 100
            
            if skip_rate > 30:
                recommendations.append(f"⏭️ Action 跳过率过高 ({skip_rate:.1f}%)，可能存在重复操作或过度保护")
            
            if fail_rate > 20:
                recommendations.append(f"❌ Action 失败率过高 ({fail_rate:.1f}%)，需要改进执行逻辑")
        
        # 6. 执行状态分析
        total_exec = sum(self.stats['execution_states'].values())
        if total_exec > 0:
            noop_rate = (self.stats['execution_states']['NOOP_DEDUP'] + 
                        self.stats['execution_states']['NOOP_ALREADY_RUNNING']) / total_exec * 100
            if noop_rate > 40:
                recommendations.append(f"🔄 NOOP 比例过高 ({noop_rate:.1f}%)，建议优化去重策略")
        
        # 7. 内存和上下文管理
        context_prunes = self.stats['by_event_type'].get('context_prune', 0)
        if context_prunes > 10:
            recommendations.append(f"💾 频繁的上下文修剪 ({context_prunes} 次)，考虑增加上下文窗口或优化内存管理")
        
        # 8. 工具调用优化
        tool_execs = self.stats['by_event_type'].get('tool_exec', 0)
        if tool_execs > 50:
            recommendations.append(f"🔧 工具调用频繁 ({tool_execs} 次)，考虑批量操作或缓存结果")
        
        # 9. 网络错误
        network_errors = len([e for e in self.stats['errors'] if 'network' in str(e.get('event', '')).lower()])
        if network_errors > 3:
            recommendations.append(f"🌐 网络错误频繁 ({network_errors} 次)，建议增强重试机制和超时配置")
        
        # 10. 断路器触发
        circuit_breaker = self.stats['by_event_type'].get('circuit_breaker_tripped', 0)
        deadloop_breaker = self.stats['by_event_type'].get('deadloop_breaker_tripped', 0)
        if circuit_breaker + deadloop_breaker > 0:
            recommendations.append(f"🚨 断路器触发 {circuit_breaker + deadloop_breaker} 次，系统存在稳定性问题")
        
        # 11. Agent 错误
        agent_errors = len([e for e in self.events if e.get('type') == 'agent.error'])
        if agent_errors > 0:
            recommendations.append(f"🤖 Agent 执行失败 {agent_errors} 次，需要改进任务处理逻辑")
        
        # 12. 通用建议
        if len(recommendations) == 0:
            recommendations.append("✅ 系统整体运行良好，继续保持")
        
        recommendations.append("📊 建议定期监控关键指标：错误率、P95延迟、CPU使用率、Reactor成功率")
        recommendations.append("🔍 建议实施分布式追踪，更好地理解请求链路")
        recommendations.append("⚡ 考虑实施性能预算，为关键操作设置延迟阈值")
        
        return recommendations
    
    def generate_visualization_data(self) -> Dict:
        """生成可视化数据（JSON 格式）"""
        viz_data = {
            'summary': {
                'total_events': self.stats['total_events'],
                'error_rate': self.stats['by_status']['err'] / max(self.stats['total_events'], 1) * 100,
                'reactor_success_rate': (self.stats['reactor_performance']['success'] / 
                                        max(self.stats['reactor_performance']['total'], 1) * 100),
                'cpu_spike_count': len(self.stats['cpu_spikes'])
            },
            'events_by_layer': dict(self.stats['by_layer']),
            'events_by_type': dict(sorted(self.stats['by_event_type'].items(), 
                                         key=lambda x: x[1], reverse=True)[:20]),
            'latency_stats': {
                event_type: self.calculate_latency_stats(latencies)
                for event_type, latencies in self.stats['latency_by_event'].items()
                if latencies
            },
            'cpu_spikes': self.stats['cpu_spikes'],
            'reactor_performance': {
                'total': self.stats['reactor_performance']['total'],
                'success': self.stats['reactor_performance']['success'],
                'failed': self.stats['reactor_performance']['failed'],
                'by_playbook': dict(self.stats['reactor_performance']['by_playbook'])
            },
            'action_performance': {
                'enqueued': self.stats['action_performance']['enqueued'],
                'succeeded': self.stats['action_performance']['succeeded'],
                'failed': self.stats['action_performance']['failed'],
                'skipped': self.stats['action_performance']['skipped'],
                'by_type': dict(self.stats['action_performance']['by_type'])
            },
            'execution_states': dict(self.stats['execution_states']),
            'top_errors': self.stats['errors'][:10]
        }
        return viz_data
    
    def generate_report(self, output_path: Path):
        """生成完整报告"""
        recommendations = self.generate_recommendations()
        viz_data = self.generate_visualization_data()
        
        # 保存可视化数据
        viz_path = output_path.parent / 'performance_visualization.json'
        with open(viz_path, 'w', encoding='utf-8') as f:
            json.dump(viz_data, f, indent=2, ensure_ascii=False)
        
        # 生成 Markdown 报告
        report = []
        report.append("# AIOS v0.5 性能深度分析报告\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("---\n")
        
        # 1. 执行摘要
        report.append("## 📊 执行摘要\n")
        report.append(f"- **总事件数**: {self.stats['total_events']:,}")
        report.append(f"- **错误率**: {viz_data['summary']['error_rate']:.2f}%")
        report.append(f"- **Reactor 成功率**: {viz_data['summary']['reactor_success_rate']:.2f}%")
        report.append(f"- **CPU 峰值次数**: {viz_data['summary']['cpu_spike_count']}")
        report.append(f"- **分析时间范围**: {self._get_time_range()}\n")
        
        # 2. 事件分布
        report.append("## 📈 事件分布分析\n")
        report.append("### 按层级统计\n")
        for layer, count in sorted(self.stats['by_layer'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / self.stats['total_events'] * 100
            report.append(f"- **{layer}**: {count} ({percentage:.1f}%)")
        report.append("")
        
        report.append("### 按事件类型统计（Top 15）\n")
        for event_type, count in sorted(self.stats['by_event_type'].items(), 
                                       key=lambda x: x[1], reverse=True)[:15]:
            percentage = count / self.stats['total_events'] * 100
            report.append(f"- **{event_type}**: {count} ({percentage:.1f}%)")
        report.append("")
        
        # 3. 性能指标
        report.append("## ⚡ 性能指标\n")
        report.append("### 延迟分布（Top 10 慢事件）\n")
        
        latency_items = []
        for event_type, latencies in self.stats['latency_by_event'].items():
            stats = self.calculate_latency_stats(latencies)
            if stats:
                latency_items.append((event_type, stats))
        
        for event_type, stats in sorted(latency_items, key=lambda x: x[1]['p95'], reverse=True)[:10]:
            report.append(f"\n**{event_type}**")
            report.append(f"- 调用次数: {stats['count']}")
            report.append(f"- 平均延迟: {stats['mean']:.1f}ms")
            report.append(f"- 中位数: {stats['median']:.1f}ms")
            report.append(f"- P95: {stats['p95']:.1f}ms")
            report.append(f"- P99: {stats['p99']:.1f}ms")
            report.append(f"- 最大值: {stats['max']:.1f}ms")
        report.append("")
        
        # 4. CPU 峰值分析
        if self.stats['cpu_spikes']:
            report.append("## 🔥 CPU 峰值分析\n")
            cpu_values = [s['cpu_percent'] for s in self.stats['cpu_spikes'] if s['cpu_percent']]
            if cpu_values:
                report.append(f"- **峰值次数**: {len(cpu_values)}")
                report.append(f"- **平均 CPU**: {statistics.mean(cpu_values):.1f}%")
                report.append(f"- **最高 CPU**: {max(cpu_values):.1f}%")
                report.append(f"- **最低 CPU**: {min(cpu_values):.1f}%\n")
        
        # 5. Reactor 执行效率
        report.append("## 🎯 Reactor 执行效率\n")
        report.append(f"- **总执行次数**: {self.stats['reactor_performance']['total']}")
        report.append(f"- **成功次数**: {self.stats['reactor_performance']['success']}")
        report.append(f"- **失败次数**: {self.stats['reactor_performance']['failed']}")
        if self.stats['reactor_performance']['total'] > 0:
            success_rate = self.stats['reactor_performance']['success'] / self.stats['reactor_performance']['total'] * 100
            report.append(f"- **成功率**: {success_rate:.2f}%\n")
        
        report.append("### Playbook 性能\n")
        for playbook_id, stats in self.stats['reactor_performance']['by_playbook'].items():
            total = stats['success'] + stats['failed']
            success_rate = stats['success'] / total * 100 if total > 0 else 0
            status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
            report.append(f"{status_icon} **{playbook_id}**: {stats['success']}/{total} ({success_rate:.1f}%)")
        report.append("")
        
        # 6. Action 执行分析
        if self.stats['action_performance']['enqueued'] > 0:
            report.append("## 🎬 Action 执行分析\n")
            report.append(f"- **入队数量**: {self.stats['action_performance']['enqueued']}")
            report.append(f"- **成功执行**: {self.stats['action_performance']['succeeded']}")
            report.append(f"- **执行失败**: {self.stats['action_performance']['failed']}")
            report.append(f"- **被跳过**: {self.stats['action_performance']['skipped']}")
            
            success_rate = self.stats['action_performance']['succeeded'] / self.stats['action_performance']['enqueued'] * 100
            skip_rate = self.stats['action_performance']['skipped'] / self.stats['action_performance']['enqueued'] * 100
            fail_rate = self.stats['action_performance']['failed'] / self.stats['action_performance']['enqueued'] * 100
            
            report.append(f"- **成功率**: {success_rate:.1f}%")
            report.append(f"- **跳过率**: {skip_rate:.1f}%")
            report.append(f"- **失败率**: {fail_rate:.1f}%\n")
            
            report.append("### 按类型统计\n")
            for action_type, stats in sorted(self.stats['action_performance']['by_type'].items(),
                                            key=lambda x: x[1]['success'] + x[1]['failed'], reverse=True):
                total = stats['success'] + stats['failed']
                if total > 0:
                    success_rate = stats['success'] / total * 100
                    report.append(f"- **{action_type}**: {stats['success']}/{total} ({success_rate:.1f}%)")
            report.append("")
        
        # 7. 执行状态分析
        if self.stats['execution_states']:
            report.append("## 🔄 执行状态分析\n")
            total_exec = sum(self.stats['execution_states'].values())
            for state, count in sorted(self.stats['execution_states'].items(), 
                                      key=lambda x: x[1], reverse=True):
                percentage = count / total_exec * 100
                report.append(f"- **{state}**: {count} ({percentage:.1f}%)")
            report.append("")
        
        # 8. 错误分析
        if self.stats['errors']:
            report.append("## ❌ 错误分析\n")
            report.append(f"- **总错误数**: {len(self.stats['errors'])}")
            report.append(f"- **错误率**: {len(self.stats['errors']) / self.stats['total_events'] * 100:.2f}%\n")
            
            # 错误类型统计
            error_types = Counter([e['event'] for e in self.stats['errors']])
            report.append("### 错误类型分布\n")
            for error_type, count in error_types.most_common(10):
                report.append(f"- **{error_type}**: {count}")
            report.append("")
            
            # 最近的错误
            report.append("### 最近的错误（Top 5）\n")
            for error in self.stats['errors'][-5:]:
                report.append(f"\n**{error['event']}** @ {error['timestamp']}")
                report.append(f"- Layer: {error['layer']}")
                payload = error.get('payload', {})
                if 'error' in payload:
                    report.append(f"- Error: {payload['error']}")
                if 'detail' in payload:
                    report.append(f"- Detail: {payload['detail']}")
            report.append("")
        
        # 9. 优化建议
        report.append("## 💡 优化建议\n")
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")
        report.append("")
        
        # 10. 附录
        report.append("## 📎 附录\n")
        report.append(f"- **可视化数据**: `{viz_path.name}`")
        report.append(f"- **分析脚本**: `scripts/performance_analyzer.py`")
        report.append(f"- **数据源**: events.jsonl, reactor_log.jsonl, execution_log.jsonl")
        report.append("\n---")
        report.append("*本报告由 AIOS 性能分析工具自动生成*")
        
        # 写入报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"\n✅ 报告已生成: {output_path}")
        print(f"✅ 可视化数据已保存: {viz_path}")
    
    def _get_time_range(self) -> str:
        """获取时间范围"""
        timestamps = []
        for event in self.events:
            ts = event.get('ts') or event.get('timestamp') or event.get('epoch')
            if ts:
                timestamps.append(ts)
        
        if not timestamps:
            return "N/A"
        
        # 尝试解析时间戳
        try:
            if isinstance(timestamps[0], str):
                # ISO 格式
                times = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps if isinstance(ts, str)]
            else:
                # Unix 时间戳
                times = [datetime.fromtimestamp(ts) for ts in timestamps if isinstance(ts, (int, float))]
            
            if times:
                return f"{min(times).strftime('%Y-%m-%d %H:%M')} ~ {max(times).strftime('%Y-%m-%d %H:%M')}"
        except:
            pass
        
        return f"{len(timestamps)} events"
    
    def run(self):
        """运行完整分析"""
        print("=" * 60)
        print("AIOS v0.5 性能深度分析")
        print("=" * 60)
        
        print("\n[1/5] 加载事件数据...")
        self.load_all_events()
        
        print("\n[2/5] 分析事件...")
        self.analyze_events()
        
        print("\n[3/5] 分析 Reactor 性能...")
        self.analyze_reactor()
        
        print("\n[4/5] 分析执行日志...")
        self.analyze_execution()
        
        print("\n[5/5] 生成报告...")
        output_path = self.workspace / 'reports' / 'performance_deep_analysis.md'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.generate_report(output_path)
        
        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)


if __name__ == '__main__':
    workspace = Path(__file__).parent.parent
    analyzer = PerformanceAnalyzer(workspace)
    analyzer.run()
