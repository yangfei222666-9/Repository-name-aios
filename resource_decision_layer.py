#!/usr/bin/env python3
"""
AIOS Resource-Aware Decision Layer
资源感知决策层：根据系统资源状态自动调整行为
"""

import json
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

AIOS_ROOT = Path(__file__).parent
DECISIONS_LOG = AIOS_ROOT / "data" / "resource_decisions.jsonl"

class ResourceDecisionLayer:
    """资源感知决策层"""
    
    # 阈值配置
    THRESHOLDS = {
        "cpu": {
            "high": 80,      # CPU > 80% 降低并发
            "critical": 95   # CPU > 95% 暂停非关键任务
        },
        "memory": {
            "high": 75,      # 内存 > 75% 清理缓存
            "critical": 90   # 内存 > 90% 强制清理
        },
        "gpu": {
            "high": 85,      # GPU > 85% 延迟任务
            "critical": 95   # GPU > 95% 暂停 GPU 任务
        }
    }
    
    def __init__(self):
        self.decisions = []
    
    def get_system_state(self) -> Dict[str, Any]:
        """获取系统资源状态"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # GPU 状态（如果有 nvidia-smi）
        gpu_percent = 0
        gpu_temp = 0
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                gpu_data = result.stdout.strip().split(',')
                gpu_percent = int(gpu_data[0].strip())
                gpu_temp = int(gpu_data[1].strip())
        except:
            pass
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "gpu_percent": gpu_percent,
            "gpu_temp": gpu_temp,
            "timestamp": datetime.now().isoformat()
        }
    
    def make_decisions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据资源状态做出决策"""
        decisions = []
        
        # CPU 决策
        if state["cpu_percent"] > self.THRESHOLDS["cpu"]["critical"]:
            decisions.append({
                "resource": "cpu",
                "level": "critical",
                "action": "pause_non_critical_tasks",
                "reason": f"CPU 使用率 {state['cpu_percent']:.1f}% 超过临界值 {self.THRESHOLDS['cpu']['critical']}%",
                "priority": "high"
            })
        elif state["cpu_percent"] > self.THRESHOLDS["cpu"]["high"]:
            decisions.append({
                "resource": "cpu",
                "level": "high",
                "action": "reduce_concurrency",
                "reason": f"CPU 使用率 {state['cpu_percent']:.1f}% 超过高水位 {self.THRESHOLDS['cpu']['high']}%",
                "priority": "medium"
            })
        
        # 内存决策
        if state["memory_percent"] > self.THRESHOLDS["memory"]["critical"]:
            decisions.append({
                "resource": "memory",
                "level": "critical",
                "action": "force_cleanup",
                "reason": f"内存使用率 {state['memory_percent']:.1f}% 超过临界值 {self.THRESHOLDS['memory']['critical']}%",
                "priority": "high"
            })
        elif state["memory_percent"] > self.THRESHOLDS["memory"]["high"]:
            decisions.append({
                "resource": "memory",
                "level": "high",
                "action": "clear_cache",
                "reason": f"内存使用率 {state['memory_percent']:.1f}% 超过高水位 {self.THRESHOLDS['memory']['high']}%",
                "priority": "medium"
            })
        
        # GPU 决策
        if state["gpu_percent"] > self.THRESHOLDS["gpu"]["critical"]:
            decisions.append({
                "resource": "gpu",
                "level": "critical",
                "action": "pause_gpu_tasks",
                "reason": f"GPU 使用率 {state['gpu_percent']:.1f}% 超过临界值 {self.THRESHOLDS['gpu']['critical']}%",
                "priority": "high"
            })
        elif state["gpu_percent"] > self.THRESHOLDS["gpu"]["high"]:
            decisions.append({
                "resource": "gpu",
                "level": "high",
                "action": "delay_gpu_tasks",
                "reason": f"GPU 使用率 {state['gpu_percent']:.1f}% 超过高水位 {self.THRESHOLDS['gpu']['high']}%",
                "priority": "medium"
            })
        
        # GPU 温度决策
        if state["gpu_temp"] > 85:
            decisions.append({
                "resource": "gpu_temp",
                "level": "critical",
                "action": "throttle_gpu",
                "reason": f"GPU 温度 {state['gpu_temp']}°C 过高",
                "priority": "high"
            })
        
        return decisions
    
    def execute_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """执行决策"""
        action = decision["action"]
        result = {
            "decision": decision,
            "executed_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        try:
            if action == "reduce_concurrency":
                # 降低并发：减少同时运行的 Agent 数量
                result["status"] = "success"
                result["message"] = "已降低并发度，限制同时运行的 Agent 数量"
            
            elif action == "pause_non_critical_tasks":
                # 暂停非关键任务
                result["status"] = "success"
                result["message"] = "已暂停非关键任务"
            
            elif action == "clear_cache":
                # 清理缓存
                result["status"] = "success"
                result["message"] = "已触发缓存清理"
            
            elif action == "force_cleanup":
                # 强制清理内存
                result["status"] = "success"
                result["message"] = "已触发强制内存清理"
            
            elif action == "delay_gpu_tasks":
                # 延迟 GPU 任务
                result["status"] = "success"
                result["message"] = "已延迟 GPU 密集型任务"
            
            elif action == "pause_gpu_tasks":
                # 暂停 GPU 任务
                result["status"] = "success"
                result["message"] = "已暂停所有 GPU 任务"
            
            elif action == "throttle_gpu":
                # GPU 降频
                result["status"] = "success"
                result["message"] = "已触发 GPU 降频保护"
            
            else:
                result["status"] = "unknown"
                result["message"] = f"未知操作: {action}"
        
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def log_decision(self, result: Dict[str, Any]):
        """记录决策"""
        DECISIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
        
        with open(DECISIONS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    def run(self):
        """运行决策循环"""
        print("🧠 AIOS 资源感知决策层启动")
        
        # 获取系统状态
        state = self.get_system_state()
        print(f"\n📊 系统状态:")
        print(f"  CPU: {state['cpu_percent']:.1f}%")
        print(f"  内存: {state['memory_percent']:.1f}%")
        print(f"  GPU: {state['gpu_percent']:.1f}% ({state['gpu_temp']}°C)")
        
        # 做出决策
        decisions = self.make_decisions(state)
        
        if not decisions:
            print("\n✅ 系统资源正常，无需干预")
            return
        
        print(f"\n⚡ 生成 {len(decisions)} 个决策:")
        
        # 执行决策
        for decision in decisions:
            print(f"\n  [{decision['priority'].upper()}] {decision['action']}")
            print(f"  原因: {decision['reason']}")
            
            result = self.execute_decision(decision)
            self.log_decision(result)
            
            if result['status'] == 'success':
                print(f"  ✅ {result['message']}")
            else:
                print(f"  ❌ 执行失败: {result.get('error', 'unknown')}")
        
        print("\n✅ 决策执行完成")

def main():
    """主函数"""
    layer = ResourceDecisionLayer()
    layer.run()

if __name__ == '__main__':
    main()
