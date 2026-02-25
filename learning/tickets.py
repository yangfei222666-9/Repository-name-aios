# aios/learning/tickets.py - L2 工单队列
"""
L2 建议不自动应用，变成工单追踪。
tickets.jsonl: {id, ts, suggestion, evidence, status, owner}
status: open | done | wontfix
"""

import json, time, sys, hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import get_path
from core.engine import append_jsonl

LEARNING_DIR = Path(__file__).resolve().parent
TICKETS_FILE = get_path("paths.tickets") or (LEARNING_DIR / "tickets.jsonl")


def _gen_id(suggestion: dict) -> str:
    raw = f"{suggestion.get('name','')}-{suggestion.get('action','')}-{suggestion.get('reason','')}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]


def load_tickets(status: str = None) -> list:
    if not TICKETS_FILE.exists():
        return []
    out = []
    for line in TICKETS_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            t = json.loads(line)
            if status and t.get("status") != status:
                continue
            out.append(t)
        except Exception:
            pass
    return out


def _save_all(tickets: list):
    TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TICKETS_FILE.open("w", encoding="utf-8") as f:
        for t in tickets:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")


def ingest(suggestions: list) -> dict:
    """从 tool_suggestions 导入，去重（同 id 不重复创建）"""
    existing = load_tickets()
    existing_ids = {t["id"] for t in existing}
    created = 0

    for s in suggestions:
        if s.get("level") != "L2":
            continue
        tid = _gen_id(s)
        if tid in existing_ids:
            continue
        ticket = {
            "id": tid,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "suggestion": {
                "name": s.get("name", ""),
                "action": s.get("action", ""),
                "reason": s.get("reason", ""),
                "confidence": s.get("confidence", 0),
            },
            "evidence": s.get("evidence", {}),
            "status": "open",
            "owner": "human",
        }
        existing.append(ticket)
        existing_ids.add(tid)
        created += 1

    _save_all(existing)
    return {
        "created": created,
        "total": len(existing),
        "open": sum(1 for t in existing if t["status"] == "open"),
    }


def update_status(ticket_id: str, status: str) -> bool:
    tickets = load_tickets()
    for t in tickets:
        if t["id"] == ticket_id:
            t["status"] = status
            t["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            _save_all(tickets)
            return True
    return False


def summary() -> str:
    tickets = load_tickets()
    if not tickets:
        return "No tickets."
    open_t = [t for t in tickets if t["status"] == "open"]
    done_t = [t for t in tickets if t["status"] == "done"]
    wontfix_t = [t for t in tickets if t["status"] == "wontfix"]

    lines = [
        f"Tickets: {len(open_t)} open, {len(done_t)} done, {len(wontfix_t)} wontfix"
    ]
    for t in open_t:
        s = t["suggestion"]
        lines.append(f"  [{t['id']}] {s['name']}: {s['action']} ({s['reason']})")
    return "\n".join(lines)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "list"
    if action == "list":
        print(summary())
    elif action == "open":
        for t in load_tickets("open"):
            print(json.dumps(t, ensure_ascii=False))
    elif action == "close" and len(sys.argv) >= 3:
        ok = update_status(sys.argv[2], "done")
        print(f"{'closed' if ok else 'not found'}: {sys.argv[2]}")
    elif action == "wontfix" and len(sys.argv) >= 3:
        ok = update_status(sys.argv[2], "wontfix")
        print(f"{'wontfix' if ok else 'not found'}: {sys.argv[2]}")
    else:
        print("Usage: tickets.py [list|open|close <id>|wontfix <id>]")
