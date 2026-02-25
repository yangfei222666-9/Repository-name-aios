"""Smoke tests for AIOS collaboration layer."""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# patch DATA_DIR before imports
TEMP = Path(tempfile.mkdtemp(prefix="collab_test_"))

def setup():
    """Monkey-patch data dirs to temp."""
    import aios.collaboration.registry as reg_mod
    import aios.collaboration.messenger as msg_mod
    import aios.collaboration.delegator as dlg_mod
    import aios.collaboration.consensus as con_mod
    import aios.collaboration.pool as pool_mod

    reg_mod.REGISTRY_FILE = TEMP / "agents.json"
    msg_mod.INBOX_DIR = TEMP / "inboxes"
    dlg_mod.TASKS_FILE = TEMP / "tasks.jsonl"
    con_mod.VOTES_FILE = TEMP / "votes.jsonl"
    pool_mod.POOL_FILE = TEMP / "pool_state.json"

setup()

from aios.collaboration.registry import AgentRegistry, AgentProfile
from aios.collaboration.messenger import Messenger, MsgType
from aios.collaboration.delegator import Delegator
from aios.collaboration.consensus import Consensus, Protocol, cross_check
from aios.collaboration.pool import AgentPool, AgentType

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}")


# ── Registry ──
print("\n📋 Registry")
reg = AgentRegistry(TEMP / "agents.json")

a1 = reg.register(AgentProfile("coder_1", "Coder", ["code", "debug"]))
a2 = reg.register(AgentProfile("researcher_1", "Researcher", ["research", "search"]))
a3 = reg.register(AgentProfile("reviewer_1", "Reviewer", ["code", "review"]))

test("register 3 agents", len(reg.list_all()) == 3)
test("find by capability [code]", len(reg.find_by_capability(["code"])) == 2)
test("find by capability [research]", len(reg.find_by_capability(["research"])) == 1)
test("best_for [code, debug]", reg.best_for(["code", "debug"]).agent_id == "coder_1")
test("best_for [nonexistent] is None", reg.best_for(["nonexistent"]) is None)

reg.heartbeat("coder_1", load=0.5, status="busy")
test("heartbeat updates status", reg.get("coder_1").status == "busy")
test("busy agent excluded from available", len(reg.find_by_capability(["code"], only_available=True)) == 1)

reg.unregister("researcher_1")
test("unregister", len(reg.list_all()) == 2)

# ── Messenger ──
print("\n📨 Messenger")
m_coder = Messenger("coder_1", TEMP / "inboxes")
m_reviewer = Messenger("reviewer_1", TEMP / "inboxes")

msg = m_coder.request("reviewer_1", {"action": "review", "file": "main.py"})
test("send request", msg.msg_id != "")
test("receiver inbox has message", m_reviewer.pending_count() == 1)

received = m_reviewer.receive()
test("receive consumes message", len(received) == 1)
test("message content correct", received[0].payload["file"] == "main.py")
test("inbox empty after receive", m_reviewer.pending_count() == 0)

# response
m_reviewer.respond(msg.msg_id, "coder_1", {"approved": True})
resp = m_coder.receive()
test("response received", len(resp) == 1 and resp[0].reply_to == msg.msg_id)

# broadcast
m_coder.broadcast({"event": "build_complete"})
bc = m_reviewer.receive()
test("broadcast received", len(bc) == 1 and bc[0].payload["event"] == "build_complete")

# ── Delegator ──
print("\n📦 Delegator")
reg2 = AgentRegistry(TEMP / "agents2.json")
reg2.register(AgentProfile("coder_1", "Coder", ["code", "debug"]))
reg2.register(AgentProfile("reviewer_1", "Reviewer", ["code", "review"]))

dlg = Delegator(reg2, "orchestrator")
delegation = dlg.create_delegation(
    "Build feature X",
    [
        {"description": "Write code", "caps": ["code"], "priority": 1},
        {"description": "Review code", "caps": ["review"], "depends_on": [], "priority": 5},
    ]
)
test("create delegation", delegation.delegation_id != "")
test("2 subtasks created", len(delegation.subtasks) == 2)

assigned = dlg.assign_ready_tasks(delegation.delegation_id)
test("assign ready tasks", len(assigned) >= 1)

status = dlg.get_status(delegation.delegation_id)
test("status shows progress", "progress" in status)

# complete tasks
for i in range(len(delegation.subtasks)):
    tid = f"{delegation.delegation_id}_{i}"
    dlg.update_task(tid, "done", result={"ok": True})

d = dlg.get_delegation(delegation.delegation_id)
test("delegation completed", d.status == "completed")
test("aggregated result has results", "results" in d.aggregated_result)

# ── Consensus ──
print("\n🗳️ Consensus")
con = Consensus()
req = con.create_request(
    "Is this code safe to deploy?",
    ["yes", "no"],
    Protocol.MAJORITY,
    min_voters=2,
)
test("create consensus request", req.request_id != "")

con.cast_vote(req, "coder_1", "yes", confidence=0.9, reasoning="Tests pass")
test("first vote, still open", req.status == "open")

con.cast_vote(req, "reviewer_1", "yes", confidence=0.8, reasoning="LGTM")
test("majority reached → decided", req.status == "decided")
test("decision is yes", req.decision == "yes")

result = con.get_result(req)
test("result has tally", result["tally"]["yes"] == 2)

# cross_check convenience
xc = cross_check("2+2=?", {"agent_a": "4", "agent_b": "4", "agent_c": "5"})
test("cross_check majority", xc["decision"] == "4")

# unanimous
req2 = con.create_request("Agree?", ["yes", "no"], Protocol.UNANIMOUS, min_voters=2)
con.cast_vote(req2, "a1", "yes")
con.cast_vote(req2, "a2", "no")
test("unanimous fails on disagreement", req2.decision == "")

# ── Pool ──
print("\n🏊 Pool")
reg3 = AgentRegistry(TEMP / "agents3.json")
pool = AgentPool(reg3)

spec = pool.spawn_spec("code_agent_1", template="coder", agent_type=AgentType.ON_DEMAND)
test("spawn spec generated", spec["agent_id"] == "code_agent_1")
test("spec has model", spec["model"] != "")
test("spec has capabilities", "code" in spec["capabilities"])
test("registered in registry", reg3.get("code_agent_1") is not None)

pool.mark_ready("code_agent_1", session_key="sess_123")
test("mark ready", pool.get("code_agent_1").status == "ready")

pool.mark_busy("code_agent_1")
test("mark busy", pool.get("code_agent_1").status == "busy")
test("task count incremented", pool.get("code_agent_1").task_count == 1)

pool.mark_done("code_agent_1")
test("mark done → ready", pool.get("code_agent_1").status == "ready")

stats = pool.stats()
test("stats correct", stats["total"] == 1 and stats["ready"] == 1)

pool.retire("code_agent_1")
test("retire → stopped", pool.get("code_agent_1").status == "stopped")

# templates
test("4 built-in templates", len(AgentPool.TEMPLATES) == 4)

# ── Summary ──
print(f"\n{'='*40}")
print(f"  ✅ {passed} passed  ❌ {failed} failed")
print(f"{'='*40}")

# cleanup
shutil.rmtree(TEMP, ignore_errors=True)

sys.exit(0 if failed == 0 else 1)
