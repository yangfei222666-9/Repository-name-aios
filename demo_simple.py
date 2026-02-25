#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS 简单演示 - 10秒快速体验
展示核心功能：事件记录 + 指标追踪 + 日志输出
"""
import sys
from pathlib import Path
import time

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from observability import span, METRICS, get_logger

def print_banner(text: str):
    """打印横幅"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def main():
    """主函数"""
    print_banner("🚀 AIOS 简单演示 - 核心功能展示")
    
    logger = get_logger("Demo")
    
    # 场景 1: 追踪一个任务
    print("\n📝 场景 1: 任务追踪")
    with span("demo-task-1"):
        logger.info("开始执行代码分析任务")
        METRICS.inc_counter("tasks.started", 1, labels={"type": "code"})
        time.sleep(0.5)
        logger.info("代码分析完成")
        METRICS.inc_counter("tasks.completed", 1, labels={"type": "code", "status": "success"})
    
    print("   ✅ 任务追踪完成")
    
    # 场景 2: 记录指标
    print("\n📊 场景 2: 指标记录")
    METRICS.set_gauge("system.cpu", 45.2, labels={"host": "localhost"})
    METRICS.set_gauge("system.memory", 62.8, labels={"host": "localhost"})
    METRICS.observe("task.duration", 0.5, labels={"type": "code"})
    print("   ✅ 指标记录完成")
    
    # 场景 3: 结构化日志
    print("\n📜 场景 3: 结构化日志")
    logger.info("系统启动", version="v1.0", mode="demo")
    logger.info("资源使用率", cpu=75.5, memory=82.3)
    logger.info("任务执行", task_type="code", duration=0.5)
    print("   ✅ 日志输出完成")
    
    # 显示统计
    print_banner("📊 统计摘要")
    snapshot = METRICS.snapshot()
    
    # 提取指标值
    tasks_completed = 0
    cpu_usage = 0
    memory_usage = 0
    avg_duration = 0
    
    for counter in snapshot.get("counters", []):
        if counter["name"] == "tasks.completed":
            tasks_completed = counter["value"]
    
    for gauge in snapshot.get("gauges", []):
        if gauge["name"] == "system.cpu":
            cpu_usage = gauge["value"]
        elif gauge["name"] == "system.memory":
            memory_usage = gauge["value"]
    
    for hist in snapshot.get("histograms", []):
        if hist["name"] == "task.duration":
            avg_duration = hist["value"].get("avg", 0)
    
    print(f"\n✅ 任务完成: {int(tasks_completed)}")
    print(f"📈 CPU 使用率: {cpu_usage:.1f}%")
    print(f"💾 内存使用率: {memory_usage:.1f}%")
    print(f"⏱️  平均耗时: {avg_duration:.2f}s")
    
    print_banner("✅ 演示完成！")
    print("\n💡 下一步:")
    print("   1. 查看日志: aios/logs/")
    print("   2. 查看指标: aios/data/metrics.jsonl")
    print("   3. 启动 Dashboard: python aios.py dashboard")
    print("   4. 查看完整文档: aios/README.md")

if __name__ == "__main__":
    main()
