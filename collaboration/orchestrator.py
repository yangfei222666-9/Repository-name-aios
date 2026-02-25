"""
Real Orchestrator v2 - 多 Agent 协作编排器（生产级）

v2 新增：
- 降级判定：部分成功为一等公民，degraded 状态 + confidence 降级
- 失败策略：重试 + 指数退避 + 熔断窗口 + 失败分类
- 执行 SLA：最小成功集 + 最大失败容忍 + 总体超时

用法（由小九在主会话中调用）：
1. orchestrator.create_plan(task, subtasks, sla) → 创建计划
2. orchestrator.get_ready_tasks(plan) → 获取可执行任务
3. orchestrator.build_spawn_args(subtask) → 生成 spawn 参数
4. orchestrator.mark_done/mark_failed → 更新状态
5. orchestrator.evaluate(plan) → SLA 判定（继续/降级/中止）
6. orchestrator.build_report(plan) → 生成降级感知报告
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "collaboration"
PLANS_FILE = DATA_DIR / "plans.json"
FAILURE_LOG = DATA_DIR / "failure_log.jsonl"


# ── 失败分类 ──


class FailureType:
    GATEWAY_502 = "gateway_502"
    TIMEOUT = "timeout"
    PARSE_ERROR = "parse_error"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    UNKNOWN = "unknown"

    @staticmethod
    def classify(error: str) -> str:
        """从错误文本自动分类"""
        e = error.lower()
        if "502" in e or "bad gateway" in e:
            return FailureType.GATEWAY_502
        if "timeout" in e or "timed out" in e:
            return FailureType.TIMEOUT
        if "429" in e or "rate limit" in e:
            return FailureType.RATE_LIMIT
        if "401" in e or "403" in e or "auth" in e:
            return FailureType.AUTH_ERROR
        if "json" in e or "parse" in e or "decode" in e:
            return FailureType.PARSE_ERROR
        return FailureType.UNKNOWN


# ── 重试策略 ──


@dataclass
class RetryPolicy:
    """指数退避重试策略"""

    max_retries: int = 3
    base_delay: float = 2.0  # 秒
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    # 熔断：同一 failure_type 在窗口内超过阈值则熔断
    circuit_breaker_threshold: int = 5
    circuit_breaker_window: float = 300.0  # 5 分钟

    def delay_for_attempt(self, attempt: int) -> float:
        """第 N 次重试的等待时间"""
        delay = self.base_delay * (self.backoff_factor**attempt)
        return min(delay, self.max_delay)


# ── 执行 SLA ──


@dataclass
class ExecutionSLA:
    """执行服务等级协议"""

    # 最小成功集：这些角色必须成功，否则整体失败
    required_roles: list = field(default_factory=lambda: ["coder", "reviewer"])
    # 最大允许失败数
    max_failures: int = 1
    # 总体超时（秒）
    total_timeout: float = 180.0
    # confidence 降级规则
    full_confidence: float = 1.0  # 全部成功
    degraded_confidence: float = 0.7  # 部分成功
    min_confidence: float = 0.3  # 最低可接受


# ── 子任务 ──


@dataclass
class SubTaskSpec:
    """子任务规格"""

    id: str
    description: str
    prompt: str
    role: str = "general"
    model: str = ""
    timeout: int = 120
    depends_on: list = field(default_factory=list)
    # 执行状态
    session_label: str = ""
    status: str = "pending"  # pending / spawned / done / failed
    result: str = ""
    spawned_at: float = 0.0
    finished_at: float = 0.0
    # v2: 失败详情
    failure_type: str = ""
    retry_count: int = 0
    error_message: str = ""


# ── 计划 ──


@dataclass
class Plan:
    """执行计划"""

    plan_id: str
    task: str
    subtasks: list = field(default_factory=list)
    status: str = "draft"  # draft / executing / done / degraded / failed / aborted
    created_at: float = 0.0
    finished_at: float = 0.0
    consensus_result: dict = field(default_factory=dict)
    final_report: str = ""
    # v2: 降级信息
    degraded: bool = False
    failed_agents: list = field(default_factory=list)
    confidence: float = 1.0
    sla: dict = field(default_factory=dict)


# ── 熔断器 ──


class CircuitBreaker:
    """简单的滑动窗口熔断器"""

    def __init__(self):
        self._failures: list[dict] = []  # {"type": str, "ts": float}

    def record_failure(self, failure_type: str):
        self._failures.append({"type": failure_type, "ts": time.time()})

    def is_tripped(
        self, failure_type: str, threshold: int = 5, window: float = 300.0
    ) -> bool:
        """检查某类失败是否触发熔断"""
        cutoff = time.time() - window
        recent = [
            f for f in self._failures if f["type"] == failure_type and f["ts"] > cutoff
        ]
        return len(recent) >= threshold

    def clear_old(self, window: float = 600.0):
        cutoff = time.time() - window
        self._failures = [f for f in self._failures if f["ts"] > cutoff]


# ── 编排器 ──


class Orchestrator:
    """生产级多 Agent 编排器"""

    ROLE_PREFIXES = {
        "coder": "你是一个编码专家。专注于写出干净、可测试的代码。直接给出结果，不要废话。",
        "researcher": "你是一个研究专家。搜索准确信息，给出有依据的分析。直接给出结果，不要废话。",
        "reviewer": "你是一个审查专家。仔细检查代码/内容的质量、安全性和性能。直接给出结果，不要废话。",
        "general": "你是一个专业助手。直接完成任务，给出结果，不要废话。",
    }

    DEFAULT_RETRY = RetryPolicy()
    DEFAULT_SLA = ExecutionSLA()

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._plans: dict[str, Plan] = {}
        self._breaker = CircuitBreaker()
        self._load()

    # ── 持久化 ──

    def _load(self):
        if PLANS_FILE.exists():
            try:
                data = json.loads(PLANS_FILE.read_text(encoding="utf-8"))
                for d in data:
                    self._plans[d["plan_id"]] = Plan(**d)
            except (json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        PLANS_FILE.write_text(
            json.dumps(
                [asdict(p) for p in self._plans.values()], ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )

    def _log_failure(
        self,
        plan_id: str,
        task_id: str,
        failure_type: str,
        error: str,
        retry_count: int,
    ):
        """追加失败日志"""
        FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.time(),
            "plan_id": plan_id,
            "task_id": task_id,
            "failure_type": failure_type,
            "error": error[:500],
            "retry_count": retry_count,
        }
        with open(FAILURE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ── 创建计划 ──

    def create_plan(
        self, plan_id: str, task: str, subtasks: list[dict], sla: Optional[dict] = None
    ) -> Plan:
        """
        创建执行计划。

        subtasks: [{"id": "t1", "description": "...", "prompt": "...",
                     "role": "coder", "model": "", "timeout": 120,
                     "depends_on": []}]
        sla: {"required_roles": [...], "max_failures": 1, "total_timeout": 180}
        """
        specs = []
        for st in subtasks:
            spec = SubTaskSpec(
                id=st["id"],
                description=st["description"],
                prompt=st.get("prompt", st["description"]),
                role=st.get("role", "general"),
                model=st.get("model", ""),
                timeout=st.get("timeout", 120),
                depends_on=st.get("depends_on", []),
            )
            specs.append(asdict(spec))

        plan = Plan(
            plan_id=plan_id,
            task=task,
            subtasks=specs,
            created_at=time.time(),
            sla=sla or asdict(self.DEFAULT_SLA),
        )
        self._plans[plan_id] = plan
        self._save()
        return plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        return self._plans.get(plan_id)

    # ── 任务调度 ──

    def get_ready_tasks(self, plan: Plan) -> list[dict]:
        """获取所有依赖已满足且未执行的子任务"""
        done_ids = {st["id"] for st in plan.subtasks if st["status"] == "done"}
        ready = []
        for st in plan.subtasks:
            if st["status"] != "pending":
                continue
            deps_met = all(d in done_ids for d in st["depends_on"])
            if deps_met:
                ready.append(st)
        return ready

    def build_spawn_args(self, subtask: dict) -> dict:
        """为一个子任务生成 sessions_spawn 调用参数"""
        role = subtask.get("role", "general")
        prefix = self.ROLE_PREFIXES.get(role, self.ROLE_PREFIXES["general"])
        full_prompt = f"{prefix}\n\n任务：{subtask['prompt']}"

        label = f"collab_{subtask['id']}"
        args = {
            "task": full_prompt,
            "label": label,
            "runTimeoutSeconds": subtask.get("timeout", 120),
        }
        if subtask.get("model"):
            args["model"] = subtask["model"]
        return args

    # ── 状态更新 ──

    def mark_spawned(self, plan_id: str, task_id: str, label: str):
        plan = self._plans.get(plan_id)
        if not plan:
            return
        for st in plan.subtasks:
            if st["id"] == task_id:
                st["status"] = "spawned"
                st["session_label"] = label
                st["spawned_at"] = time.time()
                break
        plan.status = "executing"
        self._save()

    def mark_done(self, plan_id: str, task_id: str, result: str):
        plan = self._plans.get(plan_id)
        if not plan:
            return
        for st in plan.subtasks:
            if st["id"] == task_id:
                st["status"] = "done"
                st["result"] = result
                st["finished_at"] = time.time()
                break
        self._evaluate_completion(plan)
        self._save()

    def mark_failed(
        self, plan_id: str, task_id: str, error: str, retry: bool = False
    ) -> dict:
        """
        标记任务失败。

        返回: {"action": "retry"|"circuit_break"|"degrade"|"abort",
               "failure_type": str, "retry_delay": float}
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return {"action": "abort", "failure_type": "unknown"}

        failure_type = FailureType.classify(error)
        result = {"failure_type": failure_type, "retry_delay": 0.0}

        for st in plan.subtasks:
            if st["id"] != task_id:
                continue

            st["retry_count"] = st.get("retry_count", 0) + 1
            st["failure_type"] = failure_type
            st["error_message"] = error[:500]

            # 记录失败
            self._breaker.record_failure(failure_type)
            self._log_failure(plan_id, task_id, failure_type, error, st["retry_count"])

            # 判定：熔断？
            if self._breaker.is_tripped(
                failure_type,
                self.DEFAULT_RETRY.circuit_breaker_threshold,
                self.DEFAULT_RETRY.circuit_breaker_window,
            ):
                st["status"] = "failed"
                st["result"] = f"CIRCUIT_BREAK: {failure_type} ({error[:200]})"
                st["finished_at"] = time.time()
                result["action"] = "circuit_break"
                break

            # 判定：还能重试？
            if st["retry_count"] <= self.DEFAULT_RETRY.max_retries:
                st["status"] = "pending"  # 重置为 pending，等待重新 spawn
                delay = self.DEFAULT_RETRY.delay_for_attempt(st["retry_count"])
                result["action"] = "retry"
                result["retry_delay"] = delay
                break

            # 重试耗尽
            st["status"] = "failed"
            st["result"] = (
                f"EXHAUSTED: {failure_type} after {st['retry_count']} retries ({error[:200]})"
            )
            st["finished_at"] = time.time()
            result["action"] = "degrade"
            break

        self._evaluate_completion(plan)
        self._save()
        return result

    # ── SLA 判定 ──

    def evaluate(self, plan_id: str) -> dict:
        """
        评估计划状态，返回判定结果。

        返回: {
            "verdict": "continue"|"done"|"degraded"|"abort",
            "confidence": float,
            "degraded": bool,
            "failed_agents": [str],
            "reason": str
        }
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return {"verdict": "abort", "reason": "plan not found"}

        sla = plan.sla or asdict(self.DEFAULT_SLA)
        total = len(plan.subtasks)
        done_tasks = [st for st in plan.subtasks if st["status"] == "done"]
        failed_tasks = [st for st in plan.subtasks if st["status"] == "failed"]
        running_tasks = [st for st in plan.subtasks if st["status"] == "spawned"]
        pending_tasks = [st for st in plan.subtasks if st["status"] == "pending"]

        done_roles = {st["role"] for st in done_tasks}
        failed_roles = {st["role"] for st in failed_tasks}
        failed_ids = [st["id"] for st in failed_tasks]
        required = set(sla.get("required_roles", ["coder", "reviewer"]))
        max_fail = sla.get("max_failures", 1)

        # 超时检查
        elapsed = time.time() - plan.created_at
        total_timeout = sla.get("total_timeout", 180.0)
        if elapsed > total_timeout and (running_tasks or pending_tasks):
            return {
                "verdict": "abort",
                "confidence": sla.get("min_confidence", 0.3),
                "degraded": True,
                "failed_agents": failed_ids,
                "reason": f"总体超时 ({elapsed:.0f}s > {total_timeout:.0f}s)",
            }

        # 还有任务在跑或等待
        if running_tasks or pending_tasks:
            return {
                "verdict": "continue",
                "confidence": sla.get("full_confidence", 1.0),
                "degraded": False,
                "failed_agents": failed_ids,
                "reason": f"进行中: {len(done_tasks)}/{total} 完成, "
                f"{len(running_tasks)} 运行中, {len(pending_tasks)} 等待",
            }

        # 全部结束，判定结果
        # 必需角色是否全部成功？
        missing_required = required - done_roles
        if missing_required:
            return {
                "verdict": "abort",
                "confidence": sla.get("min_confidence", 0.3),
                "degraded": True,
                "failed_agents": failed_ids,
                "reason": f"必需角色缺失: {missing_required}",
            }

        # 失败数是否超限？
        if len(failed_tasks) > max_fail:
            return {
                "verdict": "abort",
                "confidence": sla.get("min_confidence", 0.3),
                "degraded": True,
                "failed_agents": failed_ids,
                "reason": f"失败数超限: {len(failed_tasks)} > {max_fail}",
            }

        # 全部成功
        if not failed_tasks:
            return {
                "verdict": "done",
                "confidence": sla.get("full_confidence", 1.0),
                "degraded": False,
                "failed_agents": [],
                "reason": "全部成功",
            }

        # 部分成功（降级交付）
        confidence = sla.get("degraded_confidence", 0.7)
        # 按失败比例进一步降低 confidence
        fail_ratio = len(failed_tasks) / total
        confidence = max(confidence * (1 - fail_ratio), sla.get("min_confidence", 0.3))

        fail_details = [
            st["id"] + "(" + st.get("failure_type", "?") + ")" for st in failed_tasks
        ]
        return {
            "verdict": "degraded",
            "confidence": round(confidence, 2),
            "degraded": True,
            "failed_agents": failed_ids,
            "reason": f"部分成功: {len(done_tasks)}/{total}, 失败: {fail_details}",
        }

    def _evaluate_completion(self, plan: Plan):
        """内部：检查计划是否可以结束"""
        all_terminal = all(st["status"] in ("done", "failed") for st in plan.subtasks)
        if not all_terminal:
            return

        failed = [st for st in plan.subtasks if st["status"] == "failed"]
        if not failed:
            plan.status = "done"
            plan.degraded = False
            plan.confidence = 1.0
            plan.failed_agents = []
        else:
            # 用 evaluate 判定
            verdict = self.evaluate(plan.plan_id)
            if verdict["verdict"] == "abort":
                plan.status = "failed"
            else:
                plan.status = "degraded"
            plan.degraded = verdict["degraded"]
            plan.confidence = verdict["confidence"]
            plan.failed_agents = verdict["failed_agents"]

        plan.finished_at = time.time()

    # ── 查询 ──

    def get_status(self, plan_id: str) -> dict:
        plan = self._plans.get(plan_id)
        if not plan:
            return {"error": "plan not found"}

        total = len(plan.subtasks)
        done = sum(1 for st in plan.subtasks if st["status"] == "done")
        failed = sum(1 for st in plan.subtasks if st["status"] == "failed")
        spawned = sum(1 for st in plan.subtasks if st["status"] == "spawned")

        return {
            "plan_id": plan_id,
            "task": plan.task,
            "status": plan.status,
            "progress": f"{done}/{total}",
            "done": done,
            "failed": failed,
            "running": spawned,
            "pending": total - done - failed - spawned,
            "degraded": plan.degraded,
            "confidence": plan.confidence,
            "failed_agents": plan.failed_agents,
            "subtasks": [
                {
                    "id": st["id"],
                    "role": st["role"],
                    "status": st["status"],
                    "failure_type": st.get("failure_type", ""),
                    "retry_count": st.get("retry_count", 0),
                    "description": st["description"][:60],
                }
                for st in plan.subtasks
            ],
        }

    # ── 降级感知报告 ──

    def build_report(self, plan_id: str) -> str:
        """生成降级感知的汇总报告"""
        plan = self._plans.get(plan_id)
        if not plan:
            return "Plan not found"

        verdict = self.evaluate(plan_id)
        status_emoji = {
            "done": "✅",
            "degraded": "⚠️",
            "failed": "❌",
            "abort": "🛑",
        }
        emoji = status_emoji.get(verdict["verdict"], "❓")

        lines = [
            f"{emoji} 协作任务报告",
            f"任务: {plan.task}",
            f"状态: {plan.status}  置信度: {verdict['confidence']:.0%}",
        ]

        if verdict["degraded"]:
            lines.append(f"⚠️ 降级交付: {verdict['reason']}")
            lines.append(f"   失败 Agent: {verdict['failed_agents']}")

        lines.append("")

        for st in plan.subtasks:
            st_emoji = {
                "done": "✅",
                "failed": "❌",
                "spawned": "⏳",
                "pending": "⏸️",
            }.get(st["status"], "?")
            elapsed = ""
            if st.get("spawned_at") and st.get("finished_at"):
                elapsed = f" ({st['finished_at'] - st['spawned_at']:.1f}s)"

            lines.append(f"{st_emoji} {st['id']} [{st['role']}]{elapsed}")
            lines.append(f"   {st['description']}")

            if st["status"] == "done" and st.get("result"):
                preview = st["result"][:500]
                lines.append(f"   结果: {preview}")
            elif st["status"] == "failed":
                ft = st.get("failure_type", "unknown")
                rc = st.get("retry_count", 0)
                err = st.get("error_message", st.get("result", ""))[:200]
                lines.append(f"   失败类型: {ft} | 重试: {rc}次")
                lines.append(f"   错误: {err}")

            lines.append("")

        if plan.consensus_result:
            lines.append(
                f"🗳️ 共识: {json.dumps(plan.consensus_result, ensure_ascii=False)}"
            )

        # SLA 摘要
        sla = plan.sla or {}
        if sla:
            lines.append("")
            lines.append("📊 SLA 摘要:")
            lines.append(f"   必需角色: {sla.get('required_roles', [])}")
            lines.append(f"   最大容忍失败: {sla.get('max_failures', 1)}")
            lines.append(f"   总超时: {sla.get('total_timeout', 180)}s")

        return "\n".join(lines)

    # ── 重试辅助 ──

    def should_retry(self, plan_id: str, task_id: str) -> dict:
        """检查某个失败任务是否应该重试"""
        plan = self._plans.get(plan_id)
        if not plan:
            return {"retry": False, "reason": "plan not found"}

        for st in plan.subtasks:
            if st["id"] != task_id:
                continue

            if st["status"] != "pending":
                return {"retry": False, "reason": f"status is {st['status']}"}

            ft = st.get("failure_type", "")
            rc = st.get("retry_count", 0)

            # 熔断检查
            if self._breaker.is_tripped(ft):
                return {
                    "retry": False,
                    "reason": f"circuit breaker tripped for {ft}",
                }

            # 重试次数检查
            if rc > self.DEFAULT_RETRY.max_retries:
                return {
                    "retry": False,
                    "reason": f"max retries exceeded ({rc})",
                }

            delay = self.DEFAULT_RETRY.delay_for_attempt(rc)
            return {
                "retry": True,
                "attempt": rc,
                "delay": delay,
                "failure_type": ft,
            }

        return {"retry": False, "reason": "task not found"}


# ── CLI ──


def main():
    import sys

    orch = Orchestrator()

    if len(sys.argv) < 2:
        print(
            "Usage: orchestrator.py [plans|status <id>|evaluate <id>|report <id>|failures]"
        )
        return

    cmd = sys.argv[1]
    if cmd == "plans":
        for pid, p in orch._plans.items():
            print(
                f"  {pid}  status={p.status}  degraded={p.degraded}  "
                f"confidence={p.confidence:.0%}"
            )
    elif cmd == "status" and len(sys.argv) > 2:
        s = orch.get_status(sys.argv[2])
        print(json.dumps(s, indent=2, ensure_ascii=False))
    elif cmd == "evaluate" and len(sys.argv) > 2:
        v = orch.evaluate(sys.argv[2])
        print(json.dumps(v, indent=2, ensure_ascii=False))
    elif cmd == "report" and len(sys.argv) > 2:
        print(orch.build_report(sys.argv[2]))
    elif cmd == "failures":
        if FAILURE_LOG.exists():
            for line in FAILURE_LOG.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    print(f"  {line}")
        else:
            print("  No failures logged.")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
