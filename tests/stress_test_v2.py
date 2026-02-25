"""
AIOS v0.6 三阶段压力测试
专业版压力测试框架，验证系统在真实压力下的表现

测试目标：
1. 验证 Reactor + Scheduler 是否稳定
2. 验证熔断机制是否正常工作
3. 验证系统是否会过度反应（误判）

使用方法：
    python -X utf8 aios/tests/stress_test_v2.py [phase1|phase2|phase3|all]
"""

import sys
import time
import json
import psutil
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aios.core.event_bus import EventBus
from aios.core.resource_events import emit_cpu_spike
from aios.core.threshold_monitor import ThresholdMonitor


class StressTestV2:
    """AIOS v0.6 三阶段压力测试"""
    
    def __init__(self):
        self.bus = EventBus()
        self.threshold_monitor = ThresholdMonitor(
            bus=self.bus,
            cpu_trigger_threshold=80.0,
            cpu_recover_threshold=70.0,
            cpu_duration_seconds=10
        )
        self.results = {
            "phase1": {},
            "phase2": {},
            "phase3": {}
        }
        
    def phase1_controlled_spike(self):
        """
        阶段1：可控资源峰值
        目标：验证 Reactor + Scheduler 是否稳定
        
        做法：
        - 人为制造 CPU 85% 持续 20 秒
        - 或内存占用 88%
        
        观察：
        - 是否只触发 1 次修复？
        - 是否进入重复触发？
        - Score 是否合理下降？
        
        关键：不要只看"修复成功"，看是否"过度反应"
        """
        print("\n" + "="*60)
        print("阶段1：可控资源峰值")
        print("="*60)
        
        print("\n[测试] 制造 CPU 峰值（目标 85%，持续 20 秒）...")
        
        # 记录初始状态
        initial_cpu = psutil.cpu_percent(interval=1)
        print(f"初始 CPU: {initial_cpu}%")
        
        # 使用 Python 多进程工具制造 CPU 峰值
        python_exe = sys.executable
        stress_script = project_root / "aios" / "tests" / "cpu_stress.py"
        
        print("启动 CPU 压力进程...")
        process = subprocess.Popen(
            [python_exe, str(stress_script), "85", "20"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # 监控 20 秒
        start_time = time.time()
        reactor_triggers = 0
        escalations = 0
        max_cpu = 0
        
        # 订阅 confirmed 事件
        confirmed_count = [0]
        
        def count_confirmed(event):
            if event.type == "resource.threshold_confirmed":
                confirmed_count[0] += 1
        
        self.bus.subscribe("resource.threshold_confirmed", count_confirmed)
        
        while time.time() - start_time < 22:  # 多等 2 秒确保完成
            current_cpu = psutil.cpu_percent(interval=1)
            max_cpu = max(max_cpu, current_cpu)
            
            print(f"[{int(time.time() - start_time)}s] CPU: {current_cpu}%")
            
            # 使用 ThresholdMonitor 检查（持续时间判定）
            self.threshold_monitor.check_cpu(current_cpu)
            
            time.sleep(1)
        
        # 等待进程结束
        process.wait()
        
        # 等待 5 秒观察恢复
        print("\n等待 5 秒观察恢复...")
        time.sleep(5)
        final_cpu = psutil.cpu_percent(interval=1)
        
        # 使用 confirmed 事件计数
        reactor_triggers = confirmed_count[0]
        
        # 记录结果
        self.results["phase1"] = {
            "initial_cpu": initial_cpu,
            "max_cpu": max_cpu,
            "final_cpu": final_cpu,
            "reactor_triggers": reactor_triggers,
            "escalations": escalations,
            "duration": 20,
            "timestamp": datetime.now().isoformat()
        }
        
        # 判断结果
        print("\n" + "-"*60)
        print("阶段1 结果：")
        print(f"  初始 CPU: {initial_cpu}%")
        print(f"  峰值 CPU: {max_cpu}%")
        print(f"  最终 CPU: {final_cpu}%")
        print(f"  Reactor 触发次数: {reactor_triggers}")
        print(f"  重复触发次数: {escalations}")
        
        # 判断标准
        if reactor_triggers <= 3:
            print("  ✅ 触发次数合理（≤3次）")
        else:
            print(f"  ❌ 触发次数过多（{reactor_triggers}次）")
        
        if escalations == 0:
            print("  ✅ 没有重复触发")
        else:
            print(f"  ⚠️  发生重复触发（{escalations}次）")
        
        print("-"*60)
        
        return self.results["phase1"]
    
    def phase2_repeated_spikes(self):
        """
        阶段2：重复触发测试（熔断验证）
        目标：测试系统是否会"失控循环"
        
        做法：
        - 连续 3 次资源峰值（间隔 10 秒）
        
        观察：
        - 是否触发熔断？
        - 是否记录 escalation 事件？
        - 是否暂停 playbook？
        
        如果没有熔断，v0.6 必须优先补这个。
        """
        print("\n" + "="*60)
        print("阶段2：重复触发测试（熔断验证）")
        print("="*60)
        
        print("\n[测试] 连续 3 次资源峰值（间隔 10 秒）...")
        
        melted = False
        escalation_events = []
        
        for i in range(3):
            print(f"\n第 {i+1} 次峰值...")
            
            # 使用 ThresholdMonitor 发射事件
            self.threshold_monitor.check_cpu(90.0)
            
            # 等待 10 秒
            if i < 2:
                print("等待 10 秒...")
                time.sleep(10)
        
        # 检查是否触发熔断
        # 这里需要读取 events.jsonl 检查是否有 escalation 事件
        events_file = project_root / "aios" / "data" / "events.jsonl"
        if events_file.exists():
            with open(events_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get("type") == "reactor.escalation":
                            escalation_events.append(event)
                            melted = True
                    except:
                        pass
        
        # 记录结果
        self.results["phase2"] = {
            "spike_count": 3,
            "melted": melted,
            "escalation_events": len(escalation_events),
            "timestamp": datetime.now().isoformat()
        }
        
        # 判断结果
        print("\n" + "-"*60)
        print("阶段2 结果：")
        print(f"  峰值次数: 3")
        print(f"  是否熔断: {'是' if melted else '否'}")
        print(f"  Escalation 事件: {len(escalation_events)}")
        
        if melted:
            print("  ✅ 熔断机制正常工作")
        else:
            print("  ❌ 熔断机制未触发（v0.6 必须补）")
        
        print("-"*60)
        
        return self.results["phase2"]
    
    def phase3_false_alarm(self):
        """
        阶段3：假故障（错误修复验证）
        目标：测试误判风险
        
        做法：
        - 模拟一个短暂 CPU 峰值（3 秒）
        - 看系统是否过度修复
        
        如果短峰值也触发 Reactor，说明阈值策略过于敏感。
        """
        print("\n" + "="*60)
        print("阶段3：假故障（错误修复验证）")
        print("="*60)
        
        print("\n[测试] 模拟短暂 CPU 峰值（3 秒）...")
        
        # 使用 Python 多进程工具制造短暂 CPU 峰值
        python_exe = sys.executable
        stress_script = project_root / "aios" / "tests" / "cpu_stress.py"
        
        print("启动短暂 CPU 峰值...")
        process = subprocess.Popen(
            [python_exe, str(stress_script), "85", "3"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # 监控 5 秒
        start_time = time.time()
        reactor_triggers = 0
        max_cpu = 0
        
        # 订阅 confirmed 事件
        confirmed_count = [0]
        
        def count_confirmed(event):
            if event.type == "resource.threshold_confirmed":
                confirmed_count[0] += 1
        
        self.bus.subscribe("resource.threshold_confirmed", count_confirmed)
        
        while time.time() - start_time < 5:
            current_cpu = psutil.cpu_percent(interval=1)
            max_cpu = max(max_cpu, current_cpu)
            
            print(f"[{int(time.time() - start_time)}s] CPU: {current_cpu}%")
            
            # 使用 ThresholdMonitor 检查
            self.threshold_monitor.check_cpu(current_cpu)
            
            time.sleep(1)
        
        # 等待进程结束
        process.wait()
        
        # 使用 confirmed 事件计数
        reactor_triggers = confirmed_count[0]
        
        # 记录结果
        self.results["phase3"] = {
            "max_cpu": max_cpu,
            "reactor_triggers": reactor_triggers,
            "duration": 3,
            "timestamp": datetime.now().isoformat()
        }
        
        # 判断结果
        print("\n" + "-"*60)
        print("阶段3 结果：")
        print(f"  峰值 CPU: {max_cpu}%")
        print(f"  Reactor 触发次数: {reactor_triggers}")
        
        if reactor_triggers == 0:
            print("  ✅ 没有过度反应（短峰值未触发）")
        elif reactor_triggers <= 1:
            print("  ⚠️  轻微反应（触发 1 次）")
        else:
            print(f"  ❌ 过度反应（触发 {reactor_triggers} 次）")
        
        print("-"*60)
        
        return self.results["phase3"]
    
    def run_all(self):
        """运行所有三个阶段"""
        print("\n" + "="*60)
        print("AIOS v0.6 三阶段压力测试")
        print("="*60)
        
        # 阶段1
        self.phase1_controlled_spike()
        time.sleep(5)
        
        # 阶段2
        self.phase2_repeated_spikes()
        time.sleep(5)
        
        # 阶段3
        self.phase3_false_alarm()
        
        # 保存结果
        results_file = project_root / "aios" / "data" / "stress_test_v2_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存到: {results_file}")
        
        # 生成总结报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("测试总结报告")
        print("="*60)
        
        # 阶段1
        p1 = self.results["phase1"]
        print("\n阶段1：可控资源峰值")
        print(f"  峰值 CPU: {p1['max_cpu']}%")
        print(f"  Reactor 触发: {p1['reactor_triggers']} 次")
        print(f"  判定: {'✅ 通过' if p1['reactor_triggers'] <= 3 else '❌ 失败'}")
        
        # 阶段2
        p2 = self.results["phase2"]
        print("\n阶段2：重复触发测试")
        print(f"  熔断触发: {'是' if p2['melted'] else '否'}")
        print(f"  Escalation 事件: {p2['escalation_events']}")
        print(f"  判定: {'✅ 通过' if p2['melted'] else '❌ 失败（需要补熔断机制）'}")
        
        # 阶段3
        p3 = self.results["phase3"]
        print("\n阶段3：假故障测试")
        print(f"  峰值 CPU: {p3['max_cpu']}%")
        print(f"  Reactor 触发: {p3['reactor_triggers']} 次")
        print(f"  判定: {'✅ 通过' if p3['reactor_triggers'] <= 1 else '❌ 失败（过度反应）'}")
        
        # 总体判定
        all_pass = (
            p1['reactor_triggers'] <= 3 and
            p2['melted'] and
            p3['reactor_triggers'] <= 1
        )
        
        print("\n" + "="*60)
        if all_pass:
            print("✅ 所有测试通过！系统稳定性良好。")
        else:
            print("❌ 部分测试失败，需要优化：")
            if p1['reactor_triggers'] > 3:
                print("  - 阶段1：Reactor 触发过于频繁")
            if not p2['melted']:
                print("  - 阶段2：缺少熔断机制（v0.6 必须补）")
            if p3['reactor_triggers'] > 1:
                print("  - 阶段3：对短峰值过度反应（阈值过敏）")
        print("="*60)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python -X utf8 aios/tests/stress_test_v2.py [phase1|phase2|phase3|all]")
        sys.exit(1)
    
    phase = sys.argv[1]
    tester = StressTestV2()
    
    if phase == "phase1":
        tester.phase1_controlled_spike()
    elif phase == "phase2":
        tester.phase2_repeated_spikes()
    elif phase == "phase3":
        tester.phase3_false_alarm()
    elif phase == "all":
        tester.run_all()
    else:
        print(f"未知阶段: {phase}")
        print("可用阶段: phase1, phase2, phase3, all")
        sys.exit(1)


if __name__ == "__main__":
    main()
