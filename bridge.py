# aios/bridge.py - 桥接层 v0.2：5层事件架构
"""
所有外部调用通过 bridge 进入 AIOS 事件总线。
v0.2: 使用 emit() + trace_span，覆盖 KERNEL/COMMS/TOOL/MEM/SEC 全部 5 层。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.engine import (
    emit,
    trace_span,
    log_tool_event,
    log_kernel,
    log_comms,
    log_mem,
    log_sec,
    LAYER_KERNEL,
    LAYER_COMMS,
    LAYER_TOOL,
    LAYER_MEM,
    LAYER_SEC,
)

# ══════════════════════════════════════════════
#  KERNEL 层 — 循环、调度、token、上下文
# ══════════════════════════════════════════════


def on_loop_start(loop_id: int = 0):
    """一次完整思考-行动循环开始"""
    return log_kernel("loop_start", loop_id=loop_id)


def on_loop_end(loop_id: int = 0, latency_ms: int = 0):
    """一次循环结束"""
    return log_kernel("loop_end", latency_ms=latency_ms, loop_id=loop_id)


def on_token_usage(input_tokens: int, output_tokens: int, model: str = ""):
    """记录 token 消耗（成本追踪）"""
    total = input_tokens + output_tokens
    return log_kernel(
        "token_usage",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total,
        model=model,
    )


def on_context_prune(tokens_before: int, tokens_after: int, strategy: str = "truncate"):
    """上下文裁剪事件"""
    return log_kernel(
        "context_prune",
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        pruned=tokens_before - tokens_after,
        strategy=strategy,
    )


def on_shutdown(reason: str = "user"):
    """系统关闭"""
    return log_kernel("shutdown", reason=reason)


# ══════════════════════════════════════════════
#  COMMS 层 — 用户输入、计划、反思、输出
# ══════════════════════════════════════════════


def on_user_input(msg_len: int, channel: str = "telegram", msg_type: str = "text"):
    """接收到用户指令"""
    return log_comms("user_input", msg_len=msg_len, channel=channel, msg_type=msg_type)


def on_plan_generated(steps: int, summary: str = ""):
    """生成执行计划 / CoT"""
    return log_comms("plan_generated", steps=steps, summary=summary[:200])


def on_reflection(trigger: str, outcome: str = ""):
    """触发自我反思"""
    return log_comms("reflection", trigger=trigger, outcome=outcome[:200])


def on_agent_response(msg_len: int, channel: str = "telegram", latency_ms: int = 0):
    """Agent 回复发出"""
    return log_comms(
        "agent_response", latency_ms=latency_ms, msg_len=msg_len, channel=channel
    )


# ══════════════════════════════════════════════
#  TOOL 层 — 工具调用（保持 v0.1 兼容）
# ══════════════════════════════════════════════


def on_executor_run(
    intent: str, tool: str, ok: bool, result: str = "", elapsed_ms: int = 0
):
    """autolearn executor 执行后调用"""
    return log_tool_event(
        name=tool,
        ok=ok,
        ms=elapsed_ms,
        err=result[:500] if not ok else None,
        meta={"intent": intent},
    )


def on_tool_not_found(tool_name: str, query: str = ""):
    """请求了不存在的工具（幻觉监测）"""
    return emit(
        LAYER_TOOL,
        "tool_not_found",
        "err",
        payload={
            "name": tool_name,
            "query": query[:200],
        },
    )


# ══════════════════════════════════════════════
#  MEM 层 — 记忆检索、存储、未命中
# ══════════════════════════════════════════════


def on_memory_recall(source: str, query: str, hit_count: int, latency_ms: int = 0):
    """成功检索到记忆/教训"""
    return log_mem(
        "memory_recall",
        latency_ms=latency_ms,
        source=source,
        query=query[:100],
        hit_count=hit_count,
    )


def on_memory_store(source: str, topic: str, lesson_id: str = ""):
    """写入一条新记忆/教训"""
    return log_mem(
        "memory_store", source=source, topic=topic[:100], lesson_id=lesson_id
    )


def on_memory_miss(source: str, query: str):
    """检索记忆但无结果（知识盲区）"""
    return log_mem("memory_miss", source=source, query=query[:100])


# ══════════════════════════════════════════════
#  SEC 层 — 异常、安全、工单
# ══════════════════════════════════════════════


def on_runtime_error(source: str, error: str, traceback: str = ""):
    """Python 运行时错误"""
    return log_sec(
        "runtime_error",
        status="err",
        source=source,
        error=error[:300],
        traceback=traceback[:500],
    )


def on_hallucination_detected(context: str, detail: str = ""):
    """检测到幻觉（后续步骤推翻前序结论）"""
    return log_sec(
        "hallucination_detected",
        status="err",
        context=context[:200],
        detail=detail[:300],
    )


def on_ticket_created(ticket_id: str, title: str, level: str = "L2"):
    """自动生成工单"""
    return log_sec(
        "ticket_created", ticket_id=ticket_id, title=title[:200], level=level
    )


def on_http_error(source: str, url: str, status_code: int, detail: str = ""):
    """HTTP 错误（502/401/404 等）"""
    return log_sec(
        "http_error",
        status="err",
        source=source,
        url=url[:200],
        status_code=status_code,
        detail=detail[:200],
    )


def on_circuit_breaker(sig: str, tripped: bool):
    """熔断器状态变化"""
    if tripped:
        return log_sec("circuit_breaker_tripped", status="err", sig=sig)


# ══════════════════════════════════════════════
#  v0.1 兼容层 — 旧接口映射到新架构
# ══════════════════════════════════════════════


def on_match(
    query: str, matched_title: str, matched_id: str, score: float, match_type: str
):
    """matcher 匹配后调用 → MEM 层"""
    return log_mem(
        "match",
        source="aram.matcher",
        query=query[:100],
        matched=matched_title,
        matched_id=matched_id,
        score=score,
        match_type=match_type,
    )


def on_correction(query: str, wrong_title: str, correct_title: str, correct_id: str):
    """用户纠正后调用 → MEM 层"""
    return log_mem(
        "correction",
        status="err",
        source="aram.matcher",
        query=query[:100],
        wrong=wrong_title,
        correct=correct_title,
        correct_id=correct_id,
    )


def on_confirm(query: str, matched_title: str, matched_id: str):
    """用户确认后调用 → MEM 层"""
    return log_mem(
        "confirm",
        source="aram.matcher",
        query=query[:100],
        matched=matched_title,
        matched_id=matched_id,
    )


def on_retest(level: str, passed: int, failed: int):
    """autolearn retest 后调用"""
    ok = failed == 0
    layer = LAYER_TOOL if ok else LAYER_SEC
    return emit(
        layer,
        "retest",
        "ok" if ok else "err",
        payload={
            "level": level,
            "passed": passed,
            "failed": failed,
        },
    )


def on_lesson(title: str, category: str, status: str):
    """教训沉淀后调用 → MEM 层"""
    return log_mem(
        "lesson_update",
        source="autolearn",
        title=title[:100],
        category=category,
        lesson_status=status,
    )


def on_health(source: str, ok: bool, checks: dict):
    """健康检查结果 → KERNEL 层"""
    return log_kernel(
        "health_check", status="ok" if ok else "err", source=source, checks=checks
    )


def on_deploy(source: str, action: str, detail: str = ""):
    """版本/配置变更 → KERNEL 层"""
    return log_kernel("deploy", source=source, action=action, detail=detail[:500])
