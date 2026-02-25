# aios/__main__.py - 统一 CLI 入口 (argparse)
from __future__ import annotations
import argparse
import json
import sys
import os

AIOS_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AIOS_ROOT)


def cmd_health(args) -> int:
    from core.engine import load_events
    from core.config import load, get_path
    from learning.baseline import evolution_score

    issues = []

    cfg = load()
    if not cfg:
        issues.append(("FAIL", "config.yaml empty or missing"))
    else:
        issues.append(("PASS", f"config: {len(cfg)} keys"))

    ep = get_path("paths.events")
    if ep and ep.exists():
        events = load_events(days=1)
        issues.append(("PASS", f"events: {len(events)} (24h)"))
    else:
        issues.append(("WARN", "no events yet"))

    from pathlib import Path

    aram = Path(r"C:\Users\A\Desktop\ARAM-Helper\aram_data.json")
    if aram.exists():
        data = json.loads(aram.read_text(encoding="utf-8"))
        issues.append(("PASS", f"aram_data: {len(data)} champions"))
    else:
        issues.append(("WARN", "aram_data.json not found"))

    evo = evolution_score()
    grade = evo.get("grade", "N/A")
    score = evo.get("score", 0)
    if grade in ("healthy", "ok"):
        issues.append(("PASS", f"evolution: {score} ({grade})"))
    elif grade == "N/A":
        issues.append(("WARN", "evolution: no baseline data"))
    else:
        issues.append(("FAIL", f"evolution: {score} ({grade})"))

    for status, msg in issues:
        icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[status]
        print(f"  {icon} {msg}")

    has_fail = any(s == "FAIL" for s, _ in issues)
    has_warn = any(s == "WARN" for s, _ in issues)
    print(f"\nHealth: {'FAIL' if has_fail else 'WARN' if has_warn else 'PASS'}")
    return 1 if has_fail else 0


def _parse_since(since: str) -> int:
    """'24h' -> 1, '7d' -> 7, 'all' -> 365"""
    if since == "all":
        return 365
    if since.endswith("h"):
        return max(1, int(since[:-1]) // 24) or 1
    if since.endswith("d"):
        return int(since[:-1])
    return 1


def cmd_analyze(args) -> int:
    days = _parse_since(args.since)
    from learning.analyze import generate_full_report

    r = generate_full_report(days)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def cmd_report(args) -> int:
    days = _parse_since(args.since)
    from learning.analyze import generate_daily_report

    print(generate_daily_report(days))
    return 0


def cmd_apply(args) -> int:
    if args.dry_run:
        from learning.apply import run

        run(mode="show")
    else:
        from learning.apply import run

        run(mode="auto")
    return 0


def cmd_replay(args) -> int:
    import time

    hours = (
        int(args.since.rstrip("h"))
        if args.since.endswith("h")
        else int(args.since.rstrip("d")) * 24
    )
    from scripts.replay import replay

    now = int(time.time())
    r = replay(now - hours * 3600, now)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def cmd_tickets(args) -> int:
    from learning.tickets import load_tickets, summary

    if args.status == "all":
        for t in load_tickets():
            print(json.dumps(t, ensure_ascii=False))
    elif args.status in ("open", "done", "wontfix"):
        for t in load_tickets(status=args.status):
            print(json.dumps(t, ensure_ascii=False))
    else:
        print(summary())
    return 0


def cmd_score(args) -> int:
    from learning.baseline import evolution_score

    print(json.dumps(evolution_score(), ensure_ascii=False, indent=2))
    return 0


def cmd_gate(args) -> int:
    from learning.baseline import regression_gate

    r = regression_gate()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 1 if r.get("alerts") else 0


def cmd_test(args) -> int:
    import subprocess

    suite = os.path.join(AIOS_ROOT, "scripts", "run_regression_suite.py")
    return subprocess.call([sys.executable, suite])


def cmd_insight(args) -> int:
    from scripts.insight import generate_insight

    compact = args.format == "telegram"
    report = generate_insight(days=_parse_since(args.since), compact=compact)
    print(report)
    if args.save and not compact:
        import time
        from pathlib import Path

        date_str = time.strftime("%Y-%m-%d")
        out_path = Path(AIOS_ROOT) / "learning" / f"insight_{date_str}.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"\n已保存到: {out_path}")
    return 0


def cmd_reflect(args) -> int:
    if args.inject:
        from scripts.reflect import load_today_strategies, format_strategies_for_prompt

        strategies = load_today_strategies()
        if strategies:
            print(format_strategies_for_prompt(strategies))
        else:
            print("今天暂无策略。")
    else:
        from scripts.reflect import analyze_and_reflect, save_strategies

        strategies = analyze_and_reflect(_parse_since(args.since))
        save_strategies(strategies)
        for s in strategies:
            icon = {"critical": "🚨", "high": "⚠️", "medium": "📋", "low": "✅"}.get(
                s["priority"], "📋"
            )
            print(f"  {icon} [{s['rule']}] {s['content']}")
    return 0


def cmd_version(args) -> int:
    from learning.analyze import AIOS_VERSION, _get_git_commit

    print(f"AIOS {AIOS_VERSION} (commit: {_get_git_commit()})")
    return 0


def cmd_plugin(args) -> int:
    from plugins.manager import get_manager

    manager = get_manager()

    if args.plugin_cmd == "list":
        plugins = manager.list()
        if not plugins:
            print("没有已加载的插件")
            return 0

        for meta in plugins:
            # 查找插件实例（可能有 builtin/ 前缀）
            plugin = None
            for key in manager.plugins.keys():
                if key == meta.name or key.endswith(f"/{meta.name}"):
                    plugin = manager.plugins[key]
                    break

            if plugin:
                status_icon = {
                    "loaded": "✓",
                    "running": "▶",
                    "error": "✗",
                    "disabled": "⏸",
                }.get(plugin.status.value, "?")
            else:
                status_icon = "?"
            print(
                f"  {status_icon} {meta.name} v{meta.version} ({meta.plugin_type.value})"
            )
            print(f"     {meta.description}")
        return 0

    elif args.plugin_cmd == "discover":
        plugins = manager.discover()
        if not plugins:
            print("没有发现可用插件")
            return 0

        print(f"发现 {len(plugins)} 个插件:")
        for name in plugins:
            loaded = "✓" if name in manager.plugins else " "
            print(f"  [{loaded}] {name}")
        return 0

    elif args.plugin_cmd == "load":
        if not args.name:
            print("错误: 需要指定插件名称")
            return 1

        if manager.load(args.name):
            print(f"✓ 插件 {args.name} 加载成功")
            return 0
        else:
            print(f"✗ 插件 {args.name} 加载失败")
            return 1

    elif args.plugin_cmd == "unload":
        if not args.name:
            print("错误: 需要指定插件名称")
            return 1

        if manager.unload(args.name):
            print(f"✓ 插件 {args.name} 卸载成功")
            return 0
        else:
            print(f"✗ 插件 {args.name} 卸载失败")
            return 1

    elif args.plugin_cmd == "reload":
        if not args.name:
            print("错误: 需要指定插件名称")
            return 1

        if manager.reload(args.name):
            print(f"✓ 插件 {args.name} 重载成功")
            return 0
        else:
            print(f"✗ 插件 {args.name} 重载失败")
            return 1

    elif args.plugin_cmd == "enable":
        if not args.name:
            print("错误: 需要指定插件名称")
            return 1

        if manager.enable(args.name):
            print(f"✓ 插件 {args.name} 已启用")
            return 0
        else:
            print(f"✗ 插件 {args.name} 启用失败")
            return 1

    elif args.plugin_cmd == "disable":
        if not args.name:
            print("错误: 需要指定插件名称")
            return 1

        if manager.disable(args.name):
            print(f"✓ 插件 {args.name} 已禁用")
            return 0
        else:
            print(f"✗ 插件 {args.name} 禁用失败")
            return 1

    elif args.plugin_cmd == "health":
        if args.name:
            # 单个插件健康检查
            plugin = manager.get(args.name)
            if plugin is None:
                print(f"✗ 插件 {args.name} 不存在")
                return 1

            health = plugin.health_check()
            status = health.get("status", "unknown")
            icon = {"ok": "✓", "warn": "⚠", "error": "✗"}.get(status, "?")
            print(f"  {icon} {args.name}: {status}")
            if "message" in health:
                print(f"     {health['message']}")
            return 0 if status == "ok" else 1
        else:
            # 所有插件健康检查
            results = manager.health_check_all()
            if not results:
                print("没有已加载的插件")
                return 0

            for name, health in results.items():
                status = health.get("status", "unknown")
                icon = {"ok": "✓", "warn": "⚠", "error": "✗"}.get(status, "?")
                print(f"  {icon} {name}: {status}")
                if "message" in health:
                    print(f"     {health['message']}")

            has_error = any(h.get("status") == "error" for h in results.values())
            return 1 if has_error else 0

    return 0


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="aios", description="AIOS — 个人 AI 操作系统")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("health", help="健康检查 (pass/warn/fail)")

    pa = sub.add_parser("analyze", help="跑学习器，生成 suggestions + report")
    pa.add_argument("--since", default="24h", help="时间窗口: 24h, 7d, all")

    pr = sub.add_parser("report", help="输出 daily report")
    pr.add_argument("--since", default="24h", help="时间窗口: 24h, 7d, all")

    pap = sub.add_parser("apply", help="应用 L1 建议 (alias)")
    pap.add_argument("--dry-run", action="store_true", help="只显示不应用")

    prel = sub.add_parser("replay", help="回放验证")
    prel.add_argument("--since", default="24h", help="回放窗口: 24h, 48h")

    pt = sub.add_parser("tickets", help="列出 L2 工单")
    pt.add_argument(
        "--status", default="open", choices=["open", "done", "wontfix", "all"]
    )

    pi = sub.add_parser("insight", help="每日健康简报 (穷人版 ClickHouse)")
    pi.add_argument("--since", default="24h", help="时间窗口: 24h, 7d, all")
    pi.add_argument("--format", default="markdown", choices=["markdown", "telegram"])
    pi.add_argument("--save", action="store_true", help="保存到文件")

    pr2 = sub.add_parser("reflect", help="晨间反思 (自动生成每日策略)")
    pr2.add_argument("--since", default="24h", help="分析窗口: 24h, 7d")
    pr2.add_argument("--inject", action="store_true", help="只输出今日策略")

    sub.add_parser("score", help="evolution_score 进化评分")
    sub.add_parser("gate", help="门禁检测 (退化报警)")
    sub.add_parser("test", help="跑回归测试 (15 cases)")
    sub.add_parser("version", help="版本信息")

    # plugin 子命令
    pp = sub.add_parser("plugin", help="插件管理")
    pp_sub = pp.add_subparsers(dest="plugin_cmd")
    pp_sub.add_parser("list", help="列出已加载插件")
    pp_sub.add_parser("discover", help="发现可用插件")

    pp_load = pp_sub.add_parser("load", help="加载插件")
    pp_load.add_argument("name", nargs="?", help="插件名称")

    pp_unload = pp_sub.add_parser("unload", help="卸载插件")
    pp_unload.add_argument("name", nargs="?", help="插件名称")

    pp_reload = pp_sub.add_parser("reload", help="重载插件")
    pp_reload.add_argument("name", nargs="?", help="插件名称")

    pp_enable = pp_sub.add_parser("enable", help="启用插件")
    pp_enable.add_argument("name", nargs="?", help="插件名称")

    pp_disable = pp_sub.add_parser("disable", help="禁用插件")
    pp_disable.add_argument("name", nargs="?", help="插件名称")

    pp_health = pp_sub.add_parser("health", help="健康检查")
    pp_health.add_argument("name", nargs="?", help="插件名称（可选）")

    args = p.parse_args(argv)

    if not args.cmd:
        p.print_help()
        return 0

    # plugin 子命令特殊处理
    if args.cmd == "plugin":
        if not hasattr(args, "plugin_cmd") or not args.plugin_cmd:
            pp.print_help()
            return 0
        return cmd_plugin(args)

    dispatch = {
        "health": cmd_health,
        "analyze": cmd_analyze,
        "report": cmd_report,
        "insight": cmd_insight,
        "reflect": cmd_reflect,
        "apply": cmd_apply,
        "replay": cmd_replay,
        "tickets": cmd_tickets,
        "score": cmd_score,
        "gate": cmd_gate,
        "test": cmd_test,
        "version": cmd_version,
    }

    return dispatch[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
