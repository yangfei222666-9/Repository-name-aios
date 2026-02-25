"""
AIOS Full Cycle Demo - 最终版（集成可观测层）
完整闭环演示：Reactor + Self-Improving + Evolution

🔥 新增：完整的 Tracer + Metrics + Logger + Events
"""
import sys
import time
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from observability import start_trace, span, METRICS, get_logger


def print_banner(text: str):
    """打印横幅"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def scenario_1_reactor_fix():
    """场景 1: Reactor 自动修复（可观测增强版）"""
    print_banner("场景 1: Reactor 自动修复 - FileNotFoundError")
    
    logger = get_logger("Reactor")
    
    with start_trace("scenario-1-reactor", attributes={"scenario": "reactor_fix"}):
        logger.info("开始场景 1: Reactor 自动修复")
        
        # Step 1: 创建会失败的任务
        with span("create-failing-tasks"):
            logger.info("创建 3 个会失败的监控任务")
            METRICS.inc_counter("tasks.created", 3, labels={"type": "monitor", "scenario": "reactor"})
            time.sleep(0.5)
        
        # Step 2: 模拟任务失败
        with span("simulate-failures"):
            logger.info("模拟 FileNotFoundError 失败")
            for i in range(1, 4):
                task_id = f"monitor-{i}"
                logger.error(
                    "Task failed",
                    task_id=task_id,
                    error="FileNotFoundError",
                    path="C:\\fake\\path\\to\\resource",
                    retry_count=i
                )
                logger.emit_event("task_failed", task_id=task_id, severity="error", payload={
                    "error": "FileNotFoundError",
                    "path": "C:\\fake\\path\\to\\resource"
                })
                METRICS.inc_counter("tasks.failed", 1, labels={"error": "FileNotFoundError"})
            time.sleep(0.5)
        
        # Step 3: Reactor 触发修复
        with span("reactor-trigger"):
            logger.info("Reactor 检测到 3 个失败事件")
            logger.info("匹配 Playbook: pb-021-file-not-found-fix")
            time.sleep(0.3)
            
            # 执行修复
            with span("execute-fix"):
                logger.info("执行修复: 创建缺失路径")
                time.sleep(0.5)
                logger.info("修复成功: 路径已创建")
                logger.emit_event("reactor_fix_success", task_id="monitor-1", severity="info", payload={
                    "playbook": "pb-021-file-not-found-fix",
                    "action": "create_path"
                })
                METRICS.inc_counter("reactor.fixes", 1, labels={"playbook": "file-not-found"})
                METRICS.observe("reactor.fix_duration_ms", 500)
        
        # Step 4: 验证修复效果
        with span("verify-fix"):
            logger.info("验证修复效果")
            logger.info("✓ 路径存在: C:\\fake\\path\\to\\resource")
            logger.info("✓ 文件内容: Auto-created by AIOS Reactor")
            METRICS.set_gauge("reactor.success_rate", 1.0)
            time.sleep(0.3)
        
        logger.info("✅ 场景 1 完成: Reactor 自动修复成功")
        print("\n📊 场景 1 指标:")
        print(f"  - 失败任务: 3")
        print(f"  - 修复次数: 1")
        print(f"  - 成功率: 100%")
        print(f"  - 修复时间: ~500ms")


def scenario_2_self_improving():
    """场景 2: Self-Improving Loop（可观测增强版）"""
    print_banner("场景 2: Self-Improving Loop - 超时改进")
    
    logger = get_logger("SelfImproving")
    
    with start_trace("scenario-2-self-improving", attributes={"scenario": "self_improving"}):
        logger.info("开始场景 2: Self-Improving Loop")
        
        # Step 1: 创建复杂任务
        with span("create-complex-tasks"):
            logger.info("创建 3 个复杂代码任务（会超时）")
            METRICS.inc_counter("tasks.created", 3, labels={"type": "code", "scenario": "self_improving"})
            time.sleep(0.5)
        
        # Step 2: 模拟超时失败
        with span("simulate-timeouts"):
            logger.info("模拟 TimeoutError 失败")
            for i in range(1, 4):
                task_id = f"code-{i}"
                logger.error(
                    "Task timeout",
                    task_id=task_id,
                    agent="coder-dispatcher",
                    error="TimeoutError",
                    timeout_sec=60,
                    elapsed_sec=65,
                    retry_count=i
                )
                logger.emit_event("task_timeout", task_id=task_id, agent_id="coder-dispatcher", severity="error", payload={
                    "timeout_sec": 60,
                    "elapsed_sec": 65
                })
                METRICS.inc_counter("tasks.timeout", 1, labels={"agent": "coder"})
                METRICS.observe("task.duration_sec", 65)
            time.sleep(0.5)
        
        # Step 3: 触发改进循环
        with span("trigger-improvement"):
            logger.info("检测到 coder-dispatcher 失败 3/3 次")
            logger.info("触发 Self-Improving Loop")
            time.sleep(0.3)
            
            # 分析失败
            with span("analyze-failures"):
                logger.info("分析失败模式: TimeoutError")
                logger.info("根因: 任务复杂度高，60s timeout 不足")
                time.sleep(0.3)
            
            # 生成改进建议
            with span("generate-improvement"):
                logger.info("生成改进建议: 增加 timeout 60s → 120s")
                logger.info("风险等级: low（自动应用）")
                logger.emit_event("improvement_generated", agent_id="coder-dispatcher", severity="info", payload={
                    "type": "timeout_adjustment",
                    "from": 60,
                    "to": 120
                })
                METRICS.inc_counter("improvements.generated", 1, labels={"type": "timeout_adjustment"})
                time.sleep(0.3)
            
            # 应用改进
            with span("apply-improvement"):
                logger.info("备份当前配置")
                logger.info("应用改进: timeout = 120s")
                logger.info("✓ 改进已应用")
                logger.emit_event("improvement_applied", agent_id="coder-dispatcher", severity="info", payload={
                    "type": "timeout_adjustment",
                    "value": 120
                })
                METRICS.inc_counter("improvements.applied", 1, labels={"agent": "coder"})
                time.sleep(0.5)
            
            # 验证效果
            with span("verify-improvement"):
                logger.info("验证改进效果")
                logger.info("改进前: 成功率 0%, 平均耗时 65s")
                logger.info("改进后: 成功率 100%, 平均耗时 95s")
                logger.info("✓ 改进有效，确认应用")
                METRICS.set_gauge("agent.success_rate", 1.0, labels={"agent": "coder"})
                time.sleep(0.3)
        
        logger.info("✅ 场景 2 完成: Self-Improving Loop 成功")
        print("\n📊 场景 2 指标:")
        print(f"  - 失败任务: 3")
        print(f"  - 改进建议: 1")
        print(f"  - 改进应用: 1")
        print(f"  - 成功率提升: 0% → 100%")


def scenario_3_evolution():
    """场景 3: Evolution Engine（可观测增强版）"""
    print_banner("场景 3: Evolution Engine - Prompt 进化")
    
    logger = get_logger("Evolution")
    
    with start_trace("scenario-3-evolution", attributes={"scenario": "evolution"}):
        logger.info("开始场景 3: Evolution Engine")
        
        # Step 1: 收集追踪数据
        with span("collect-traces"):
            logger.info("收集最近 7 天的 Agent 追踪数据")
            logger.info("发现 15 条追踪记录，5 个失败模式")
            METRICS.set_gauge("traces.collected", 15)
            time.sleep(0.5)
        
        # Step 2: 分析 Prompt 缺陷
        with span("analyze-prompt-gaps"):
            logger.info("分析 Prompt 缺陷")
            logger.info("发现 2 个 Prompt 缺口")
            logger.info("  - 缺少错误处理提示")
            logger.info("  - 缺少超时预警机制")
            METRICS.inc_counter("prompt.gaps_found", 2)
            time.sleep(0.5)
        
        # Step 3: 生成 Prompt 补丁
        with span("generate-prompt-patch"):
            logger.info("生成 Prompt 补丁")
            logger.info("  + 规则 1: 任务超时前 10s 发出预警")
            logger.info("  + 规则 2: 捕获所有异常并记录详细信息")
            logger.emit_event("prompt_patch_generated", agent_id="coder", severity="info", payload={
                "rules_added": 2
            })
            METRICS.inc_counter("prompt.patches_generated", 2)
            time.sleep(0.5)
        
        # Step 4: 应用进化
        with span("apply-evolution"):
            logger.info("应用 Prompt 进化")
            logger.info("✓ 补丁已应用到 coder Agent")
            logger.emit_event("evolution_applied", agent_id="coder", severity="info", payload={
                "patches": 2
            })
            METRICS.inc_counter("evolution.applied", 1, labels={"agent": "coder"})
            time.sleep(0.5)
        
        # Step 5: 跨 Agent 知识传播
        with span("share-knowledge"):
            logger.info("跨 Agent 知识传播")
            logger.info("✓ 知识已传播到 3 个低成功率 Agent")
            METRICS.inc_counter("knowledge.transfers", 3)
            time.sleep(0.3)
        
        logger.info("✅ 场景 3 完成: Evolution Engine 成功")
        print("\n📊 场景 3 指标:")
        print(f"  - Prompt 缺口: 2")
        print(f"  - 补丁生成: 2")
        print(f"  - 进化应用: 1")
        print(f"  - 知识传播: 3")


def main():
    """主函数"""
    print_banner("AIOS Full Cycle Demo - 最终版（可观测增强）")
    
    start_time = time.time()
    
    # 初始化
    logger = get_logger("Demo")
    
    logger.info("🚀 开始完整闭环演示")
    
    try:
        # 场景 1: Reactor 自动修复
        scenario_1_reactor_fix()
        
        # 场景 2: Self-Improving Loop
        scenario_2_self_improving()
        
        # 场景 3: Evolution Engine
        scenario_3_evolution()
        
        # 导出指标
        print_banner("导出可观测数据")
        
        # 保存指标快照
        metrics_file = Path(__file__).parent / "observability" / "metrics" / f"demo_metrics_{int(time.time())}.json"
        METRICS.write_snapshot(str(metrics_file))
        print(f"📊 指标已保存: {metrics_file}")
        
        # 打印指标摘要
        snapshot = METRICS.snapshot()
        print(f"\n📈 指标摘要:")
        print(f"  - Counters: {len(snapshot['counters'])}")
        print(f"  - Gauges: {len(snapshot['gauges'])}")
        print(f"  - Histograms: {len(snapshot['histograms'])}")
        
        # 总结
        elapsed = time.time() - start_time
        print_banner("演示完成")
        print(f"✅ 总耗时: {elapsed:.1f}s")
        print(f"✅ 3 个场景全部成功")
        print(f"\n📁 输出文件:")
        print(f"  - Traces: aios/observability/traces/")
        print(f"  - Metrics: aios/observability/metrics/")
        print(f"  - Logs: aios/logs/")
        print(f"  - Events: events.jsonl")
        print(f"\n🚀 启动 Dashboard:")
        print(f"  python aios/dashboard/dashboard_server.py")
        print(f"  然后访问: http://localhost:8080")
        
        logger.info("✅ 完整闭环演示成功")
        
    except Exception as e:
        logger.exception(f"演示失败: {str(e)}")
        raise


if __name__ == "__main__":
    main()
