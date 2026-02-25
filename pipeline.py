#!/usr/bin/env python3
# aios/pipeline.py - AIOS 日常流水线 v0.7
"""
一条龙流水线，心跳调一次全跑完：

  sensors → alerts → reactor → verifier → feedback → evolution → report

每个阶段独立 try/except，一个挂了不影响后续。
输出：结构化报告（可选 telegram 格式推送）。
"""

import json, sys, io, time, subprocess, os
from pathlib import Path
from datetime import datetime

# 强制 UTF-8 环境
os.environ["PYTHONIOENCODING"] = "utf-8"
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

AIOS_ROOT = Path(__file__).resolve().parent
WS = AIOS_ROOT.parent if AIOS_ROOT.name == "aios" else AIOS_ROOT
PYTHON = r"C:\Program Files\Python312\python.exe"

sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(WS / "scripts"))

# ── 阶段执行器 ──


def _run_stage(name, fn):
    """执行一个阶段，返回 (ok, result, elapsed_ms)"""
    t0 = time.time()
    try:
        result = fn()
        elapsed = int((time.time() - t0) * 1000)
        return True, result, elapsed
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        return False, str(e)[:200], elapsed


# ── 各阶段 ──


def stage_sensors():
    """感知扫描"""
    try:
        from core.dispatcher import (
            dispatch as aios_dispatch,
            get_pending_actions,
            clear_actions,
        )

        aios_dispatch(run_sensors=True)
        actions = get_pending_actions()
        count = len(actions)
        high = sum(1 for a in actions if a.get("priority") == "high")
        if actions:
            clear_actions()

        # 检查是否需要生成每日汇总
        try:
            from learning.habits.tracker import check_and_generate_summary

            summary = check_and_generate_summary()
            if summary:
                # 生成了新的汇总
                pass
        except Exception:
            pass

        return {"pending_actions": count, "high_priority": high}
    except ImportError:
        return {"skip": "dispatcher not available"}


def stage_alerts():
    """告警检查"""
    try:
        # 动态导入 alert_fsm
        scripts_path = WS / "scripts"
        if str(scripts_path) not in sys.path:
            sys.path.insert(0, str(scripts_path))
        
        import alert_fsm

        # 运行 alerts 检查规则
        try:
            from scripts_alerts_runner import run_checks, format_summary

            results, notifications = run_checks()
            summary = format_summary(results)
        except:
            results = {}
            notifications = []
            summary = "alerts check skipped"

        # 告警统计
        stats = alert_fsm.stats()
        overdue = alert_fsm.check_sla()

        return {
            "open": stats.get("open", 0),
            "ack": stats.get("ack", 0),
        "overdue": stats.get("overdue", 0),
        "resolved_today": stats.get("resolved_today", 0),
        "notifications": len(notifications),
        "notification_texts": notifications[:3],  # 最多3条
    }
    except Exception as e:
        return {"error": str(e)[:200]}


def stage_reactor():
    """自动响应"""
    from core.reactor import scan_and_react, dashboard_metrics

    results = scan_and_react(mode="auto")
    acted = [r for r in results if r.get("status") not in ("no_match",)]
    success = [r for r in acted if r.get("status") == "success"]
    pending = [r for r in acted if r.get("status") == "pending_confirm"]

    return {
        "total_matched": len(acted),
        "auto_executed": len(success),
        "pending_confirm": len(pending),
        "details": [
            {"pb": r.get("playbook_id"), "status": r.get("status")} for r in acted[:5]
        ],
    }


def stage_verifier():
    """执行后验证（对刚执行的 reaction 验证）"""
    from core.verifier import verify_reaction
    from core.reactor import REACTION_LOG

    if not REACTION_LOG.exists():
        return {"skip": "no reactions to verify"}

    # 读最近的 success reaction（最近 2 分钟内）
    with open(REACTION_LOG, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        return {"skip": "empty reaction log"}

    from datetime import timedelta

    cutoff = (datetime.now() - timedelta(minutes=2)).isoformat()
    recent = []
    for line in lines[-5:]:
        try:
            r = json.loads(line)
            if r.get("status") == "success" and r.get("ts", "") >= cutoff:
                recent.append(r)
        except:
            continue

    if not recent:
        return {"skip": "no recent reactions to verify"}

    verified = 0
    passed = 0
    for r in recent:
        result = verify_reaction(r)
        verified += 1
        if result.get("passed"):
            passed += 1

    return {"verified": verified, "passed": passed, "failed": verified - passed}


def stage_feedback():
    """反馈分析"""
    from core.feedback_loop import analyze_playbook_patterns, generate_suggestions

    patterns = analyze_playbook_patterns(168)
    suggestions = generate_suggestions(168)

    high_priority = [s for s in suggestions if s.get("priority") == "high"]

    return {
        "playbooks_analyzed": len(patterns),
        "suggestions": len(suggestions),
        "high_priority": len(high_priority),
        "high_details": [
            {
                "pb": s.get("playbook_id"),
                "type": s.get("type"),
                "reason": s.get("reason", "")[:60],
            }
            for s in high_priority[:3]
        ],
    }


def stage_evolution():
    """进化评分"""
    from core.evolution import compute_evolution_v2

    result = compute_evolution_v2()
    return {
        "v2_score": result["evolution_v2"],
        "grade": result["grade"],
        "base": result["base_score"],
        "reactor": result["reactor_score"],
    }


def stage_convergence():
    """告警收敛检查"""
    try:
        # 动态导入 alert_fsm
        scripts_path = WS / "scripts"
        if str(scripts_path) not in sys.path:
            sys.path.insert(0, str(scripts_path))
        
        from alert_fsm import record_healthy_window

        suggestions = record_healthy_window()
        return {
            "converge_suggestions": len(suggestions),
            "details": [
                {"id": s.get("alert_id"), "action": s.get("action")}
                for s in suggestions[:3]
            ],
        }
    except Exception as e:
        return {"skip": str(e)[:100]}


def stage_scheduler_summary():
    """调度器状态摘要"""
    try:
        from core.scheduler_v2 import SchedulerV2, Priority

        # 读取最近的调度决策日志
        decision_log = AIOS_ROOT / "data" / "scheduler_decisions.jsonl"
        recent_decisions = []
        if decision_log.exists():
            with open(decision_log, "r", encoding="utf-8") as f:
                lines = f.readlines()
            cutoff = (datetime.now() - __import__("datetime").timedelta(hours=1)).isoformat()
            for line in lines[-50:]:
                try:
                    d = json.loads(line.strip())
                    if d.get("ts", "") >= cutoff:
                        recent_decisions.append(d)
                except:
                    continue

        # 统计优先级分布
        p0 = sum(1 for d in recent_decisions if d.get("priority") == 0)
        p1 = sum(1 for d in recent_decisions if d.get("priority") == 1)
        p2 = sum(1 for d in recent_decisions if d.get("priority", 2) == 2)

        # 读取队列状态（从最近的 pipeline_runs 推断）
        runs_file = AIOS_ROOT / "data" / "pipeline_runs.jsonl"
        last_run_ms = 0
        if runs_file.exists():
            with open(runs_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if lines:
                try:
                    last = json.loads(lines[-1].strip())
                    last_run_ms = last.get("total_ms", 0)
                except:
                    pass

        return {
            "decisions_1h": len(recent_decisions),
            "p0_urgent": p0,
            "p1_high": p1,
            "p2_normal": p2,
            "last_pipeline_ms": last_run_ms,
        }
    except Exception as e:
        return {"skip": str(e)[:200]}


def stage_agent_health():
    """Agent 健康检查"""
    try:
        agent_data = AIOS_ROOT / "agent_system" / "data" / "agents.json"
        if not agent_data.exists():
            return {"skip": "agents.json not found"}

        with open(agent_data, "r", encoding="utf-8") as f:
            data = json.loads(f.read())

        agents = data if isinstance(data, list) else data.get("agents", [])
        total = len(agents)
        active = sum(1 for a in agents if a.get("status") == "active")
        degraded = sum(1 for a in agents if a.get("status") == "degraded")
        failed = sum(1 for a in agents if a.get("status") == "failed")

        # 计算整体成功率
        total_tasks = 0
        success_tasks = 0
        for a in agents:
            stats = a.get("stats", {})
            total_tasks += stats.get("tasks_completed", 0) + stats.get("tasks_failed", 0)
            success_tasks += stats.get("tasks_completed", 0)

        success_rate = (success_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "total": total,
            "active": active,
            "degraded": degraded,
            "failed": failed,
            "overall_success_rate": round(success_rate, 1),
            "total_tasks": total_tasks,
        }
    except Exception as e:
        return {"skip": str(e)[:200]}


# ── 主流水线 ──


def run_pipeline(fmt="default"):
    """执行完整流水线"""
    stages = [
        ("sensors", stage_sensors),
        ("alerts", stage_alerts),
        ("reactor", stage_reactor),
        ("verifier", stage_verifier),
        ("convergence", stage_convergence),
        ("scheduler", stage_scheduler_summary),
        ("agent_health", stage_agent_health),
        ("feedback", stage_feedback),
        ("evolution", stage_evolution),
    ]

    report = {
        "ts": datetime.now().isoformat(),
        "stages": {},
        "total_ms": 0,
        "errors": [],
    }

    total_t0 = time.time()

    for name, fn in stages:
        ok, result, elapsed = _run_stage(name, fn)
        report["stages"][name] = {"ok": ok, "result": result, "ms": elapsed}
        if not ok:
            report["errors"].append(f"{name}: {result}")

    report["total_ms"] = int((time.time() - total_t0) * 1000)

    # 保存报告
    _save_report(report)

    return report


def _save_report(report):
    report_dir = Path(AIOS_ROOT) / "data"
    report_dir.mkdir(parents=True, exist_ok=True)
    log_file = report_dir / "pipeline_runs.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False) + "\n")


# ── 格式化 ──


def format_report(report, fmt="default"):
    """格式化报告"""
    stages = report.get("stages", {})
    errors = report.get("errors", [])
    total_ms = report.get("total_ms", 0)

    if fmt == "telegram":
        return _format_telegram(stages, errors, total_ms)
    else:
        return _format_default(stages, errors, total_ms)


def _format_default(stages, errors, total_ms):
    lines = [f"🔄 AIOS Pipeline — {datetime.now().strftime('%H:%M')} ({total_ms}ms)"]
    lines.append("=" * 40)

    for name, s in stages.items():
        icon = "✅" if s["ok"] else "❌"
        lines.append(f"{icon} {name} ({s['ms']}ms)")
        r = s["result"]
        if isinstance(r, dict):
            for k, v in r.items():
                if k not in ("details", "high_details", "notification_texts", "skip"):
                    lines.append(f"    {k}: {v}")
                elif k == "skip":
                    lines.append(f"    ⏭️ {v}")
        elif isinstance(r, str):
            lines.append(f"    {r[:80]}")

    if errors:
        lines.append(f"\n⚠️ {len(errors)} 个阶段异常:")
        for e in errors:
            lines.append(f"  ❌ {e}")

    return "\n".join(lines)


def _format_telegram(stages, errors, total_ms):
    evo = stages.get("evolution", {}).get("result", {})
    alerts = stages.get("alerts", {}).get("result", {})
    reactor = stages.get("reactor", {}).get("result", {})
    feedback = stages.get("feedback", {}).get("result", {})
    sched = stages.get("scheduler", {}).get("result", {})
    agent_hp = stages.get("agent_health", {}).get("result", {})

    grade = evo.get("grade", "?")
    grade_icon = {"healthy": "🟢", "degraded": "🟡", "critical": "🔴"}.get(grade, "⚪")

    lines = [
        f"🔄 AIOS Pipeline ({total_ms}ms)",
        f"{grade_icon} Evolution v2: {evo.get('v2_score', '?')} ({grade})",
        f"📋 告警: OPEN={alerts.get('open',0)} 超SLA={alerts.get('overdue',0)}",
        f"⚡ 响应: 执行={reactor.get('auto_executed',0)} 待确认={reactor.get('pending_confirm',0)}",
    ]

    # 调度摘要
    if not sched.get("skip"):
        p0 = sched.get("p0_urgent", 0)
        lines.append(f"📅 调度: 决策={sched.get('decisions_1h',0)} P0={p0} P1={sched.get('p1_high',0)}")

    # Agent 健康
    if not agent_hp.get("skip"):
        degraded = agent_hp.get("degraded", 0)
        failed = agent_hp.get("failed", 0)
        agent_icon = "🔴" if failed > 0 else ("🟡" if degraded > 0 else "🟢")
        lines.append(f"{agent_icon} Agents: {agent_hp.get('active',0)}/{agent_hp.get('total',0)}活跃 成功率={agent_hp.get('overall_success_rate',0)}%")

    high = feedback.get("high_priority", 0)
    if high > 0:
        lines.append(f"💡 高优建议: {high} 条")

    if errors:
        lines.append(f"⚠️ 异常: {len(errors)}")

    # 生成 AI 摘要（使用路由器）
    try:
        from core.llm_helper import generate_summary

        summary_data = {
            "evolution_score": evo.get("v2_score", 0),
            "grade": grade,
            "alerts_open": alerts.get("open", 0),
            "reactor_executed": reactor.get("auto_executed", 0),
        }
        ai_summary = generate_summary(summary_data, task_type="summarize_short")
        lines.append(f"\n🤖 {ai_summary}")
    except Exception:
        pass  # 静默失败，不影响报告

    # 阶段耗时
    stage_times = " / ".join(f"{n}:{s.get('ms',0)}" for n, s in stages.items())
    lines.append(f"⏱️ {stage_times}")

    return "\n".join(lines)


# ── CLI ──


def cli():
    if len(sys.argv) < 2:
        fmt = "default"
    else:
        fmt = sys.argv[1]

    if fmt in ("run", "default"):
        report = run_pipeline()
        print(format_report(report, "default"))
    elif fmt == "telegram":
        report = run_pipeline()
        print(format_report(report, "telegram"))
    elif fmt == "history":
        log_file = Path(AIOS_ROOT) / "data" / "pipeline_runs.jsonl"
        if not log_file.exists():
            print("无历史记录")
            return
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        recent = lines[-5:] if len(lines) > 5 else lines
        for line in recent:
            r = json.loads(line.strip())
            ts = r.get("ts", "?")[:16]
            ms = r.get("total_ms", 0)
            errs = len(r.get("errors", []))
            evo = r.get("stages", {}).get("evolution", {}).get("result", {})
            grade = evo.get("grade", "?")
            print(f"  {ts} | {ms}ms | {grade} | errors={errs}")
    else:
        print("用法: python pipeline.py [run|telegram|history]")


if __name__ == "__main__":
    cli()
