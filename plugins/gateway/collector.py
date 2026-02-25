# aios/plugins/gateway/collector.py - 采集 gateway session 的事件 v0.2
"""
从 OpenClaw session 日志提取事件，写入 events.jsonl。
v0.2: 覆盖 TOOL + COMMS + SEC 三层。

支持两种模式：
  1. live: 实时记录（bridge 调用）
  2. batch: 从 session 日志批量导入
"""

import json, time, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.engine import (
    log_tool_event,
    emit,
    load_events,
    LAYER_TOOL,
    LAYER_COMMS,
    LAYER_SEC,
)

# 需要追踪的 tool 名单
TRACKED_TOOLS = {
    "web_fetch",
    "web_search",
    "exec",
    "read",
    "write",
    "edit",
    "browser",
    "image",
    "tts",
    "message",
    "cron",
    "memory_search",
    "memory_get",
}


def record_tool(name: str, ok: bool, ms: int, err: str = None, meta: dict = None):
    """实时记录一次 tool 调用，自动推断 task_context"""
    if name not in TRACKED_TOOLS:
        return None
    if meta is None:
        meta = {}
    if "task_context" not in meta:
        meta["task_context"] = infer_task_context(name, meta)
    return log_tool_event(name=name, ok=ok, ms=ms, err=err, meta=meta)


def record_user_input(msg_len: int, channel: str = "telegram", msg_type: str = "text"):
    """记录用户输入 → COMMS 层"""
    return emit(
        LAYER_COMMS,
        "user_input",
        "ok",
        payload={
            "msg_len": msg_len,
            "channel": channel,
            "msg_type": msg_type,
        },
    )


def record_agent_response(msg_len: int, channel: str = "telegram", latency_ms: int = 0):
    """记录 agent 回复 → COMMS 层"""
    return emit(
        LAYER_COMMS,
        "agent_response",
        "ok",
        latency_ms,
        payload={
            "msg_len": msg_len,
            "channel": channel,
        },
    )


def record_error(source: str, error: str, traceback: str = ""):
    """记录运行时错误 → SEC 层"""
    return emit(
        LAYER_SEC,
        "runtime_error",
        "err",
        payload={
            "source": source,
            "error": error[:300],
            "traceback": traceback[:500],
        },
    )


def infer_task_context(name: str, meta: dict = None) -> str:
    """从 tool 名和 meta 推断任务语义"""
    if name in ("web_fetch", "web_search"):
        return "browsing"
    if name in ("browser", "image"):
        return "browsing"
    if name in ("memory_search", "memory_get"):
        return "recalling"
    if name == "exec":
        cmd = (meta or {}).get("command", "")
        if "git" in cmd:
            return "deploying"
        if "test" in cmd or "pytest" in cmd:
            return "testing"
        return "executing"
    if name in ("write", "edit"):
        return "coding"
    if name == "read":
        return "reading"
    if name in ("message", "tts"):
        return "communicating"
    if name == "cron":
        return "scheduling"
    return "unknown"


def record_session_event(event_type: str, summary: str, data: dict = None):
    """记录 session 级事件（对话开始/结束/错误）"""
    layer = LAYER_COMMS if event_type in ("session_start", "session_end") else LAYER_SEC
    return emit(layer, event_type, "ok", payload=data)


def batch_import(session_log: list) -> dict:
    """
    从 session 历史批量导入事件。
    session_log: [{role, content, tool_calls?, ...}]
    """
    imported = 0
    for msg in session_log:
        # 用户消息 → COMMS
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                emit(
                    LAYER_COMMS,
                    "user_input",
                    "ok",
                    payload={
                        "msg_len": len(content),
                        "source": "batch_import",
                    },
                )
                imported += 1
            continue

        if msg.get("role") != "assistant":
            continue

        # assistant 消息 → COMMS
        content = msg.get("content", "")
        if isinstance(content, str) and content.strip():
            emit(
                LAYER_COMMS,
                "agent_response",
                "ok",
                payload={
                    "msg_len": len(content),
                    "source": "batch_import",
                },
            )
            imported += 1

        # tool 调用 → TOOL
        tool_calls = msg.get("tool_calls", [])
        for tc in tool_calls:
            name = tc.get("function", {}).get("name", tc.get("name", ""))
            if name not in TRACKED_TOOLS:
                continue
            result = tc.get("result", "")
            ok = "error" not in str(result).lower()[:200]
            log_tool_event(name=name, ok=ok, ms=0, meta={"source": "batch_import"})
            imported += 1

    return {"imported": imported}


def daily_summary() -> dict:
    """今日事件摘要：按层 + 按工具 + 按 task_context"""
    events = load_events(days=1)

    by_layer = {}
    by_tool = {}
    by_context = {}

    for e in events:
        # 按层统计
        layer = e.get("layer", e.get("type", "unknown"))
        by_layer[layer] = by_layer.get(layer, 0) + 1

        # 工具层详细统计
        if layer == "TOOL":
            payload = e.get("payload", e.get("data", {}))
            name = payload.get("name", e.get("event", "?"))
            ctx = (payload.get("meta") or {}).get("task_context", "unknown")

            if name not in by_tool:
                by_tool[name] = {"calls": 0, "ok": 0, "fail": 0, "total_ms": 0}
            by_tool[name]["calls"] += 1
            if payload.get("ok", True) and e.get("status", "ok") == "ok":
                by_tool[name]["ok"] += 1
            else:
                by_tool[name]["fail"] += 1
            by_tool[name]["total_ms"] += payload.get("ms", e.get("latency_ms", 0))

            by_context[ctx] = by_context.get(ctx, 0) + 1

    for name, stats in by_tool.items():
        if stats["calls"] > 0:
            stats["avg_ms"] = round(stats["total_ms"] / stats["calls"])

    return {
        "date": time.strftime("%Y-%m-%d"),
        "by_layer": by_layer,
        "tools": by_tool,
        "task_contexts": by_context,
        "total_events": sum(by_layer.values()),
    }


if __name__ == "__main__":
    print(json.dumps(daily_summary(), ensure_ascii=False, indent=2))
