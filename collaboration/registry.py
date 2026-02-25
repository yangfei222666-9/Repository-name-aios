"""
Agent Registry - Registration, discovery, capability matching.

Each agent declares:
- id, name, capabilities (tags)
- status (idle/busy/offline)
- load (0.0~1.0)
- max_concurrent tasks
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "collaboration"
REGISTRY_FILE = DATA_DIR / "agents.json"


@dataclass
class AgentProfile:
    agent_id: str
    name: str
    capabilities: list  # e.g. ["code", "research", "monitor", "review"]
    status: str = "idle"  # idle | busy | offline
    load: float = 0.0  # 0.0 ~ 1.0
    max_concurrent: int = 1
    last_heartbeat: float = 0.0
    metadata: dict = field(default_factory=dict)

    def is_available(self) -> bool:
        return self.status == "idle" and self.load < 0.9

    def can_handle(self, required_caps: list) -> bool:
        return all(c in self.capabilities for c in required_caps)

    def staleness_seconds(self) -> float:
        return (
            time.time() - self.last_heartbeat if self.last_heartbeat else float("inf")
        )


class AgentRegistry:
    """Thread-safe agent registry backed by JSON file."""

    STALE_THRESHOLD = 300  # 5 min without heartbeat → mark offline

    def __init__(self, registry_path: Optional[Path] = None):
        self.path = registry_path or REGISTRY_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._agents: dict[str, AgentProfile] = {}
        self._load()

    # ── persistence ──

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                for d in data:
                    ap = AgentProfile(**d)
                    self._agents[ap.agent_id] = ap
            except (json.JSONDecodeError, TypeError):
                self._agents = {}

    def _save(self):
        self.path.write_text(
            json.dumps(
                [asdict(a) for a in self._agents.values()], ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )

    # ── CRUD ──

    def register(self, profile: AgentProfile) -> AgentProfile:
        profile.last_heartbeat = time.time()
        self._agents[profile.agent_id] = profile
        self._save()
        return profile

    def unregister(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            self._save()
            return True
        return False

    def get(self, agent_id: str) -> Optional[AgentProfile]:
        return self._agents.get(agent_id)

    def list_all(self) -> list[AgentProfile]:
        return list(self._agents.values())

    # ── heartbeat ──

    def heartbeat(self, agent_id: str, load: float = 0.0, status: str = "idle"):
        agent = self._agents.get(agent_id)
        if agent:
            agent.last_heartbeat = time.time()
            agent.load = load
            agent.status = status
            self._save()

    def sweep_stale(self):
        """Mark agents with no recent heartbeat as offline."""
        now = time.time()
        changed = False
        for agent in self._agents.values():
            if (
                agent.status != "offline"
                and (now - agent.last_heartbeat) > self.STALE_THRESHOLD
            ):
                agent.status = "offline"
                changed = True
        if changed:
            self._save()

    # ── discovery ──

    def find_by_capability(
        self, caps: list, only_available: bool = True
    ) -> list[AgentProfile]:
        """Find agents that have ALL required capabilities."""
        self.sweep_stale()
        results = []
        for agent in self._agents.values():
            if agent.can_handle(caps):
                if only_available and not agent.is_available():
                    continue
                results.append(agent)
        # prefer lower load
        results.sort(key=lambda a: a.load)
        return results

    def best_for(self, caps: list) -> Optional[AgentProfile]:
        """Return the single best available agent for given capabilities."""
        candidates = self.find_by_capability(caps, only_available=True)
        return candidates[0] if candidates else None


# ── CLI ──


def main():
    import sys

    reg = AgentRegistry()

    if len(sys.argv) < 2:
        print("Usage: registry.py [list|get <id>|remove <id>]")
        return

    cmd = sys.argv[1]
    if cmd == "list":
        agents = reg.list_all()
        if not agents:
            print("No agents registered.")
        for a in agents:
            print(
                f"  {a.agent_id:20s}  status={a.status:8s}  load={a.load:.1f}  caps={a.capabilities}"
            )
    elif cmd == "get" and len(sys.argv) > 2:
        a = reg.get(sys.argv[2])
        print(json.dumps(asdict(a), indent=2, ensure_ascii=False) if a else "Not found")
    elif cmd == "remove" and len(sys.argv) > 2:
        ok = reg.unregister(sys.argv[2])
        print("Removed" if ok else "Not found")
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
