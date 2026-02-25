"""
Pool - Agent lifecycle management.

Manages agent spawning, health monitoring, and graceful shutdown.
Bridges to OpenClaw's sessions_spawn for actual sub-agent creation.

Agent types:
- PERSISTENT: long-running specialist (monitor, watcher)
- ON_DEMAND: spawned for a task, cleaned up after
- EPHEMERAL: one-shot, auto-delete session after completion
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

from .registry import AgentRegistry, AgentProfile

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "collaboration"
POOL_FILE = DATA_DIR / "pool_state.json"


class AgentType(str, Enum):
    PERSISTENT = "persistent"
    ON_DEMAND = "on_demand"
    EPHEMERAL = "ephemeral"


@dataclass
class PooledAgent:
    agent_id: str
    agent_type: str
    session_key: str = ""  # OpenClaw session key
    label: str = ""  # OpenClaw session label
    model: str = ""  # model override
    capabilities: list = field(default_factory=list)
    spawned_at: float = 0.0
    last_active: float = 0.0
    task_count: int = 0
    max_tasks: int = 0  # 0 = unlimited
    status: str = "starting"  # starting | ready | busy | stopping | stopped


class AgentPool:
    """Manages a pool of sub-agents with lifecycle control."""

    # default specialist templates
    TEMPLATES = {
        "coder": {
            "capabilities": ["code", "debug", "test"],
            "model": "claude-sonnet-4-5",
            "prompt_prefix": "You are a coding specialist. Focus on writing clean, tested code.",
        },
        "researcher": {
            "capabilities": ["research", "search", "analyze"],
            "model": "claude-sonnet-4-5",
            "prompt_prefix": "You are a research specialist. Find accurate information and cite sources.",
        },
        "reviewer": {
            "capabilities": ["review", "validate", "audit"],
            "model": "claude-sonnet-4-5",
            "prompt_prefix": "You are a code/content reviewer. Be thorough and constructive.",
        },
        "monitor": {
            "capabilities": ["monitor", "alert", "health"],
            "model": "claude-haiku-4-5",
            "prompt_prefix": "You are a monitoring agent. Watch for issues and report concisely.",
        },
    }

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self._pool: dict[str, PooledAgent] = {}
        self._load()

    def _load(self):
        if POOL_FILE.exists():
            try:
                data = json.loads(POOL_FILE.read_text(encoding="utf-8"))
                for d in data:
                    pa = PooledAgent(**d)
                    self._pool[pa.agent_id] = pa
            except (json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        POOL_FILE.parent.mkdir(parents=True, exist_ok=True)
        POOL_FILE.write_text(
            json.dumps(
                [asdict(a) for a in self._pool.values()], ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )

    def spawn_spec(
        self,
        agent_id: str,
        template: str = "",
        agent_type: AgentType = AgentType.ON_DEMAND,
        capabilities: list = None,
        model: str = "",
        max_tasks: int = 0,
    ) -> dict:
        """
        Generate spawn specification (to be executed by orchestrator via sessions_spawn).
        Returns dict with task prompt, model, label for sessions_spawn call.
        """
        tmpl = self.TEMPLATES.get(template, {})
        caps = capabilities or tmpl.get("capabilities", [])
        mdl = model or tmpl.get("model", "")
        prefix = tmpl.get("prompt_prefix", "You are a specialist agent.")

        now = time.time()
        pa = PooledAgent(
            agent_id=agent_id,
            agent_type=agent_type.value,
            capabilities=caps,
            model=mdl,
            spawned_at=now,
            last_active=now,
            max_tasks=max_tasks,
        )
        self._pool[agent_id] = pa

        # register in agent registry
        self.registry.register(
            AgentProfile(
                agent_id=agent_id,
                name=agent_id,
                capabilities=caps,
                status="idle",
            )
        )

        self._save()

        return {
            "agent_id": agent_id,
            "label": f"collab_{agent_id}",
            "model": mdl,
            "task_prefix": prefix,
            "capabilities": caps,
        }

    def mark_ready(self, agent_id: str, session_key: str = ""):
        pa = self._pool.get(agent_id)
        if pa:
            pa.status = "ready"
            pa.session_key = session_key
            self.registry.heartbeat(agent_id, status="idle")
            self._save()

    def mark_busy(self, agent_id: str):
        pa = self._pool.get(agent_id)
        if pa:
            pa.status = "busy"
            pa.task_count += 1
            pa.last_active = time.time()
            self.registry.heartbeat(agent_id, load=0.8, status="busy")
            self._save()

    def mark_done(self, agent_id: str):
        pa = self._pool.get(agent_id)
        if pa:
            if pa.max_tasks and pa.task_count >= pa.max_tasks:
                pa.status = "stopping"
            else:
                pa.status = "ready"
                self.registry.heartbeat(agent_id, load=0.0, status="idle")
            self._save()

    def retire(self, agent_id: str):
        pa = self._pool.get(agent_id)
        if pa:
            pa.status = "stopped"
            self.registry.heartbeat(agent_id, status="offline")
            self._save()

    def remove(self, agent_id: str):
        if agent_id in self._pool:
            del self._pool[agent_id]
            self.registry.unregister(agent_id)
            self._save()

    def get(self, agent_id: str) -> Optional[PooledAgent]:
        return self._pool.get(agent_id)

    def list_active(self) -> list[PooledAgent]:
        return [a for a in self._pool.values() if a.status not in ("stopped",)]

    def list_idle(self) -> list[PooledAgent]:
        return [a for a in self._pool.values() if a.status == "ready"]

    def stats(self) -> dict:
        agents = list(self._pool.values())
        return {
            "total": len(agents),
            "ready": sum(1 for a in agents if a.status == "ready"),
            "busy": sum(1 for a in agents if a.status == "busy"),
            "stopped": sum(1 for a in agents if a.status == "stopped"),
            "total_tasks": sum(a.task_count for a in agents),
        }


# ── CLI ──


def main():
    import sys

    reg = AgentRegistry()
    pool = AgentPool(reg)

    if len(sys.argv) < 2:
        print("Usage: pool.py [list|stats|templates|spawn <id> <template>|retire <id>]")
        return

    cmd = sys.argv[1]
    if cmd == "list":
        agents = pool.list_active()
        if not agents:
            print("No active agents in pool.")
        for a in agents:
            print(
                f"  {a.agent_id:20s}  type={a.agent_type:12s}  status={a.status:10s}  tasks={a.task_count}"
            )
    elif cmd == "stats":
        s = pool.stats()
        print(json.dumps(s, indent=2))
    elif cmd == "templates":
        for name, tmpl in AgentPool.TEMPLATES.items():
            print(f"  {name:15s}  caps={tmpl['capabilities']}  model={tmpl['model']}")
    elif cmd == "spawn" and len(sys.argv) >= 4:
        spec = pool.spawn_spec(sys.argv[2], template=sys.argv[3])
        print(json.dumps(spec, indent=2, ensure_ascii=False))
    elif cmd == "retire" and len(sys.argv) > 2:
        pool.retire(sys.argv[2])
        print(f"Retired {sys.argv[2]}")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
