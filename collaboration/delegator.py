"""
Delegator - Task decomposition, assignment, and result aggregation.

Flow:
1. Receive complex task
2. Decompose into subtasks (with dependency graph)
3. Assign each subtask to best available agent
4. Track progress
5. Aggregate results when all done

Task states: pending → assigned → running → done | failed | timeout
"""

import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

from .registry import AgentRegistry
from .messenger import Messenger, MsgType

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "collaboration"
TASKS_FILE = DATA_DIR / "tasks.jsonl"


@dataclass
class SubTask:
    task_id: str
    parent_id: str  # delegation id
    description: str
    required_caps: list
    assigned_to: str = ""
    status: str = "pending"  # pending | assigned | running | done | failed | timeout
    result: dict = field(default_factory=dict)
    error: str = ""
    created_at: float = 0.0
    started_at: float = 0.0
    finished_at: float = 0.0
    timeout: int = 600  # seconds
    depends_on: list = field(default_factory=list)  # task_ids that must complete first
    priority: int = 5  # 1=highest, 10=lowest

    def is_timed_out(self) -> bool:
        if self.status == "running" and self.started_at:
            return (time.time() - self.started_at) > self.timeout
        return False

    def is_ready(self, completed_ids: set) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in completed_ids for dep in self.depends_on)


@dataclass
class Delegation:
    delegation_id: str
    description: str
    requester: str  # who asked for this
    subtasks: list  # list of SubTask dicts
    status: str = "active"  # active | completed | failed | cancelled
    created_at: float = 0.0
    finished_at: float = 0.0
    aggregated_result: dict = field(default_factory=dict)


class Delegator:
    """Decomposes tasks, assigns to agents, tracks and aggregates."""

    def __init__(self, registry: AgentRegistry, agent_id: str = "orchestrator"):
        self.registry = registry
        self.messenger = Messenger(agent_id)
        self.agent_id = agent_id
        self._delegations: dict[str, Delegation] = {}
        self._tasks: dict[str, SubTask] = {}
        self._load()

    # ── persistence ──

    def _load(self):
        if TASKS_FILE.exists():
            for line in TASKS_FILE.read_text(encoding="utf-8").strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    if d.get("_type") == "delegation":
                        dlg = Delegation(**{k: v for k, v in d.items() if k != "_type"})
                        self._delegations[dlg.delegation_id] = dlg
                    elif d.get("_type") == "subtask":
                        st = SubTask(**{k: v for k, v in d.items() if k != "_type"})
                        self._tasks[st.task_id] = st
                except (json.JSONDecodeError, TypeError):
                    pass

    def _append(self, record: dict):
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TASKS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ── create delegation ──

    def create_delegation(
        self, description: str, subtask_specs: list[dict], requester: str = "user"
    ) -> Delegation:
        """
        Create a delegation with subtasks.

        subtask_specs: [{"description": str, "caps": [...], "depends_on": [...], "timeout": int, "priority": int}]
        """
        dlg_id = uuid.uuid4().hex[:10]
        now = time.time()

        subtasks = []
        for i, spec in enumerate(subtask_specs):
            st = SubTask(
                task_id=f"{dlg_id}_{i}",
                parent_id=dlg_id,
                description=spec["description"],
                required_caps=spec.get("caps", []),
                created_at=now,
                timeout=spec.get("timeout", 600),
                depends_on=spec.get("depends_on", []),
                priority=spec.get("priority", 5),
            )
            self._tasks[st.task_id] = st
            subtasks.append(asdict(st))
            self._append({**asdict(st), "_type": "subtask"})

        dlg = Delegation(
            delegation_id=dlg_id,
            description=description,
            requester=requester,
            subtasks=subtasks,
            created_at=now,
        )
        self._delegations[dlg_id] = dlg
        self._append({**asdict(dlg), "_type": "delegation"})

        return dlg

    # ── assignment ──

    def assign_ready_tasks(self, delegation_id: str) -> list[SubTask]:
        """Find ready subtasks and assign to best available agents."""
        dlg = self._delegations.get(delegation_id)
        if not dlg or dlg.status != "active":
            return []

        completed = {
            tid
            for tid, t in self._tasks.items()
            if t.parent_id == delegation_id and t.status == "done"
        }

        assigned = []
        pending = [
            self._tasks[f"{delegation_id}_{i}"]
            for i in range(len(dlg.subtasks))
            if self._tasks.get(f"{delegation_id}_{i}")
            and self._tasks[f"{delegation_id}_{i}"].status == "pending"
        ]

        # sort by priority
        pending.sort(key=lambda t: t.priority)

        for task in pending:
            if not task.is_ready(completed):
                continue

            agent = self.registry.best_for(task.required_caps)
            if not agent:
                continue

            task.assigned_to = agent.agent_id
            task.status = "assigned"
            task.started_at = time.time()

            # notify agent
            self.messenger.send(
                agent.agent_id,
                MsgType.REQUEST,
                {
                    "action": "execute_task",
                    "task_id": task.task_id,
                    "description": task.description,
                    "delegation_id": delegation_id,
                },
            )

            # update agent load
            self.registry.heartbeat(
                agent.agent_id, load=min(agent.load + 0.3, 1.0), status="busy"
            )
            assigned.append(task)

        return assigned

    # ── progress tracking ──

    def update_task(
        self, task_id: str, status: str, result: dict = None, error: str = ""
    ):
        task = self._tasks.get(task_id)
        if not task:
            return

        task.status = status
        if result:
            task.result = result
        if error:
            task.error = error
        if status in ("done", "failed"):
            task.finished_at = time.time()

        # check if delegation is complete
        dlg = self._delegations.get(task.parent_id)
        if dlg:
            all_tasks = [
                self._tasks[f"{dlg.delegation_id}_{i}"]
                for i in range(len(dlg.subtasks))
                if self._tasks.get(f"{dlg.delegation_id}_{i}")
            ]

            if all(t.status == "done" for t in all_tasks):
                dlg.status = "completed"
                dlg.finished_at = time.time()
                dlg.aggregated_result = self._aggregate(all_tasks)
            elif any(t.status == "failed" for t in all_tasks):
                # check if failed task has no dependents still pending
                failed_ids = {t.task_id for t in all_tasks if t.status == "failed"}
                blocked = [
                    t
                    for t in all_tasks
                    if t.status == "pending"
                    and any(d in failed_ids for d in t.depends_on)
                ]
                if blocked and all(
                    t.status in ("done", "failed")
                    for t in all_tasks
                    if t not in blocked
                ):
                    dlg.status = "failed"
                    dlg.finished_at = time.time()

    def check_timeouts(self) -> list[SubTask]:
        """Find and mark timed-out tasks."""
        timed_out = []
        for task in self._tasks.values():
            if task.is_timed_out():
                task.status = "timeout"
                task.finished_at = time.time()
                task.error = f"Timed out after {task.timeout}s"
                timed_out.append(task)
        return timed_out

    def _aggregate(self, tasks: list[SubTask]) -> dict:
        """Combine results from all subtasks."""
        return {
            "subtask_count": len(tasks),
            "results": {t.task_id: t.result for t in tasks},
            "total_time": max(t.finished_at for t in tasks)
            - min(t.created_at for t in tasks),
        }

    # ── query ──

    def get_delegation(self, delegation_id: str) -> Optional[Delegation]:
        return self._delegations.get(delegation_id)

    def get_status(self, delegation_id: str) -> dict:
        dlg = self._delegations.get(delegation_id)
        if not dlg:
            return {"error": "not found"}

        tasks = [
            self._tasks.get(f"{delegation_id}_{i}") for i in range(len(dlg.subtasks))
        ]
        tasks = [t for t in tasks if t]

        return {
            "delegation_id": delegation_id,
            "status": dlg.status,
            "progress": f"{sum(1 for t in tasks if t.status == 'done')}/{len(tasks)}",
            "subtasks": [
                {
                    "id": t.task_id,
                    "status": t.status,
                    "assigned_to": t.assigned_to,
                    "description": t.description[:60],
                }
                for t in tasks
            ],
        }

    def list_active(self) -> list[dict]:
        return [
            self.get_status(d.delegation_id)
            for d in self._delegations.values()
            if d.status == "active"
        ]


# ── CLI ──


def main():
    import sys

    reg = AgentRegistry()
    dlg = Delegator(reg)

    if len(sys.argv) < 2:
        print("Usage: delegator.py [active|status <id>|timeouts]")
        return

    cmd = sys.argv[1]
    if cmd == "active":
        active = dlg.list_active()
        if not active:
            print("No active delegations.")
        for a in active:
            print(f"  {a['delegation_id']}  {a['progress']}  {a['status']}")
    elif cmd == "status" and len(sys.argv) > 2:
        s = dlg.get_status(sys.argv[2])
        print(json.dumps(s, indent=2, ensure_ascii=False))
    elif cmd == "timeouts":
        to = dlg.check_timeouts()
        print(f"  {len(to)} timed out tasks")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
