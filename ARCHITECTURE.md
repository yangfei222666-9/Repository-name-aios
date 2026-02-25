# AIOS Architecture

**Version:** 0.5  
**Last Updated:** 2026-02-24

---

## Overview

AIOS (Autonomous Intelligence Operating System) is a self-healing, self-learning system that monitors, analyzes, and automatically fixes issues in AI agent workflows.

**Core Philosophy:**
- **Observe** → **Decide** → **Act** → **Verify** → **Learn**
- Event-driven architecture (all communication via EventBus)
- Autonomous operation (minimal human intervention)
- Continuous evolution (system improves over time)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         AIOS v0.5                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌───────────┐    ┌─────────┐            │
│  │ EventBus │◄───┤ Scheduler │◄───┤ Reactor │            │
│  │  (心脏)   │    │  (大脑)    │    │ (免疫)   │            │
│  └────┬─────┘    └─────┬─────┘    └────┬────┘            │
│       │                │                │                  │
│       ▼                ▼                ▼                  │
│  ┌─────────────────────────────────────────┐              │
│  │         ScoreEngine (体检报告)           │              │
│  └─────────────────────────────────────────┘              │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────┐              │
│  │      Agent StateMachine (执行层)         │              │
│  └─────────────────────────────────────────┘              │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────┐              │
│  │         Dashboard (监控面板)             │              │
│  └─────────────────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. EventBus (System Heart)

**Purpose:** Central nervous system for all component communication.

**Event Types:**
- `resource.high` - Resource usage alerts (CPU/memory/GPU)
- `task.failed` - Task execution failures
- `agent.degraded` - Agent performance degradation
- `playbook.executed` - Reactor actions
- `score.updated` - Evolution score changes

**Key Features:**
- Async event dispatch
- Topic-based subscription
- Event persistence (events.jsonl)
- Replay capability

**Code Location:** `aios/core/event_bus.py`

---

### 2. Scheduler (System Brain)

**Purpose:** Decision-making engine that analyzes events and triggers appropriate actions.

**Decision Flow:**
```
Event → Analyze → Prioritize → Route → Execute → Verify
```

**Decision Types:**
- **Immediate:** Critical issues (system crash, data loss)
- **Scheduled:** Routine maintenance (cleanup, optimization)
- **Deferred:** Low-priority improvements (refactoring, documentation)

**Key Features:**
- Priority queue (P0/P1/P2/P3)
- Concurrency control (max 3 parallel tasks)
- Timeout handling (default 300s)
- Retry logic (exponential backoff)

**Code Location:** `aios/core/scheduler.py`

---

### 3. Reactor (Immune System)

**Purpose:** Automatic remediation engine that executes fixes based on playbooks.

**Playbook Structure:**
```json
{
  "id": "cpu_high_kill_idle",
  "trigger": {
    "event_type": "resource.high",
    "conditions": {"resource": "cpu", "threshold": 80}
  },
  "actions": [
    {"type": "kill_process", "target": "idle_agents"}
  ],
  "validation": {
    "check": "cpu_below_threshold",
    "threshold": 70
  }
}
```

**Execution Flow:**
```
Trigger Match → Pre-check → Execute → Validate → Report
```

**Key Features:**
- Pattern matching (strict + fuzzy)
- Dry-run mode (test without executing)
- Rollback support (undo failed actions)
- Success rate tracking

**Code Location:** `aios/core/reactor.py`

---

### 4. ScoreEngine (Health Monitor)

**Purpose:** Real-time system health scoring and trend analysis.

**Evolution Score Formula:**
```
Evolution Score = (TSR × 0.4) + (CR × 0.3) + (Uptime × 0.2) + (Learning × 0.1)

Where:
- TSR (Task Success Rate): % of successful tasks
- CR (Correction Rate): % of auto-fixed issues
- Uptime: System availability (0-1)
- Learning: Knowledge accumulation rate
```

**Health Grades:**
- **0.8-1.0:** Excellent (green)
- **0.6-0.8:** Good (yellow)
- **0.4-0.6:** Degraded (orange)
- **0.0-0.4:** Critical (red)

**Key Features:**
- Real-time scoring (updated every event)
- Trend detection (improving/stable/degrading)
- Alert thresholds (auto-notify on degradation)

**Code Location:** `aios/core/score_engine.py`

---

### 5. Agent StateMachine (Execution Layer)

**Purpose:** Manages agent lifecycle and state transitions.

**State Diagram:**
```
idle → running → blocked → degraded → archived
  ↑       ↓         ↓         ↓          ↓
  └───────┴─────────┴─────────┴──────────┘
```

**State Transitions:**
- `idle → running`: Task assigned
- `running → blocked`: Resource exhausted
- `blocked → degraded`: Repeated failures
- `degraded → archived`: Unrecoverable
- `* → idle`: Task completed / reset

**Key Features:**
- Auto-recovery (blocked → idle after cooldown)
- Circuit breaker (3 failures → degraded)
- Load balancing (distribute tasks to idle agents)

**Code Location:** `aios/agent_system/state_machine.py`

---

### 6. Dashboard (Monitoring UI)

**Purpose:** Real-time visualization of system health and metrics.

**Features:**
- **Overview Tab:** Evolution score, event timeline, top issues
- **Agents Tab:** Agent status, success rates, task history
- **Evolution Tab:** Score trends, improvement suggestions
- **Performance Tab:** Response times, throughput, bottlenecks

**Tech Stack:**
- Backend: Python HTTP server (port 8765)
- Frontend: HTML + Vanilla JS
- Updates: WebSocket (real-time) + HTTP polling (fallback)

**Code Location:** `aios/dashboard/`

---

### 7. Memory Palace (Knowledge Base)

**Purpose:** Unified memory system for storing and retrieving knowledge.

**API:**
```python
from aios.memory import MemoryPalace

mp = MemoryPalace()

# Store knowledge
mp.store("lesson_123", {
    "category": "error_handling",
    "content": "Always validate input before processing",
    "confidence": 0.9
})

# Query knowledge
results = mp.query("how to handle errors", top_k=5)

# Link related knowledge
mp.link("lesson_123", "lesson_456", relation="related_to")
```

**Backends:**
- **JSON** (default): File-based storage
- **Chroma**: Vector database (semantic search)
- **Neo4j**: Graph database (relationship queries)

**Code Location:** `aios/memory/`

---

## Data Flow

### 1. Error Detection → Auto-Fix

```
1. Error occurs (e.g., CPU > 80%)
   ↓
2. EventBus emits "resource.high" event
   ↓
3. Scheduler analyzes event → decides to trigger Reactor
   ↓
4. Reactor matches playbook "cpu_high_kill_idle"
   ↓
5. Reactor executes: kill idle agents
   ↓
6. Reactor validates: CPU < 70%?
   ↓
7. ScoreEngine updates Evolution Score
   ↓
8. Dashboard shows real-time update
```

### 2. Knowledge Extraction

```
1. Task fails (e.g., "FileNotFoundError")
   ↓
2. EventBus emits "task.failed" event
   ↓
3. Knowledge Extractor analyzes error pattern
   ↓
4. If pattern repeats ≥3 times → create lesson
   ↓
5. Store lesson in Memory Palace (draft level)
   ↓
6. Next time same error occurs → apply lesson
   ↓
7. If fix succeeds → upgrade lesson (verified)
   ↓
8. After 5 successes → upgrade to hardened
```

### 3. Agent Evolution

```
1. Agent fails task repeatedly (≥3 times in 24h)
   ↓
2. Evolution Engine analyzes failure pattern
   ↓
3. Generate improvement suggestion (e.g., increase timeout)
   ↓
4. If risk=low → auto-apply
   ↓
5. If risk=medium/high → notify human for approval
   ↓
6. Track improvement effectiveness (A/B test)
   ↓
7. If improvement fails → auto-rollback
```

---

## Key Design Decisions

### 1. Event-Driven Architecture

**Why:** Decouples components, enables async processing, simplifies testing.

**Trade-off:** Slightly higher latency (event dispatch overhead) vs. better scalability.

### 2. File-Based Storage (Default)

**Why:** Simple, human-readable, no external dependencies.

**Trade-off:** Limited query performance vs. easy debugging and portability.

### 3. Autonomous by Default

**Why:** Reduces human intervention, enables 24/7 operation.

**Trade-off:** Risk of incorrect auto-fixes vs. faster response times.

**Mitigation:** Risk-based approval (low-risk auto-apply, high-risk require confirmation).

### 4. Gradual Evolution

**Why:** Avoids breaking changes, allows rollback, builds confidence over time.

**Trade-off:** Slower improvement vs. system stability.

---

## Extension Points

### 1. Custom Playbooks

Add new playbooks to `aios/playbooks/`:

```json
{
  "id": "my_custom_fix",
  "trigger": {
    "event_type": "custom.event",
    "conditions": {"key": "value"}
  },
  "actions": [
    {"type": "custom_action", "params": {...}}
  ]
}
```

### 2. Custom Memory Backend

Implement `MemoryBackend` interface:

```python
from aios.memory.backend import MemoryBackend

class MyBackend(MemoryBackend):
    def store(self, key, value, metadata):
        # Your implementation
        pass
    
    def query(self, query, top_k):
        # Your implementation
        pass
```

### 3. Custom Agents

Register new agent types in `aios/agent_system/registry.py`:

```python
from aios.agent_system import AgentRegistry

registry = AgentRegistry()
registry.register("my_agent", MyAgentClass)
```

---

## Performance Characteristics

### Latency

- Event dispatch: <10ms
- Playbook matching: <50ms
- Reactor execution: 100ms-5s (depends on action)
- Score calculation: <20ms

### Throughput

- Events/sec: ~1000 (single-threaded)
- Concurrent tasks: 3 (configurable)
- Agent spawns: 0.3s (with circuit breaker)

### Resource Usage

- Memory: ~50MB (base) + ~10MB per active agent
- CPU: <5% (idle), 10-30% (active)
- Disk: ~1MB/day (events.jsonl)

---

## Security Considerations

### 1. Playbook Validation

- All playbooks are validated before execution
- Dangerous actions (e.g., `rm -rf`) require explicit approval
- Dry-run mode available for testing

### 2. Event Integrity

- Events are signed with SHA-256 hash
- Tampering detection via checksum validation
- Audit log for all critical actions

### 3. Memory Isolation

- Each agent has isolated memory space
- Shared knowledge requires explicit linking
- No cross-agent data leakage

---

## Testing Strategy

### Unit Tests

- Component-level tests (EventBus, Scheduler, Reactor)
- Mock external dependencies
- Coverage target: >80%

### Integration Tests

- End-to-end workflows (error → fix → verify)
- Real playbook execution
- Coverage target: >60%

### Smoke Tests

- Quick sanity checks (<30s)
- Run before every deployment
- Critical path only

### Regression Tests

- Full test suite (5-10min)
- Run nightly
- Catch breaking changes

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest aios/tests/

# Start dashboard
python aios/dashboard/server.py

# Run heartbeat
python aios/heartbeat_runner.py
```

### Production

```bash
# Install as package
pip install aios-framework

# Configure
export AIOS_CONFIG_PATH=/path/to/config.json

# Run as service
systemctl start aios
```

---

## Monitoring

### Key Metrics

- **Evolution Score:** Overall system health (0-1)
- **Task Success Rate:** % of successful tasks
- **Correction Rate:** % of auto-fixed issues
- **Response Time:** Time from error to fix
- **Uptime:** System availability

### Alerts

- Evolution Score < 0.4 → Critical alert
- Task Success Rate < 70% → Warning
- Correction Rate < 50% → Investigation needed

### Logs

- **events.jsonl:** All system events
- **playbook_executions.jsonl:** Reactor actions
- **agent_tasks.jsonl:** Agent execution history

---

## Roadmap

### v0.6 (Production-Ready)

- Priority queue (P0/P1/P2/P3)
- Concurrency control (max N parallel tasks)
- Timeout + retry logic
- Rollback mechanism
- Weight self-learning (simple version)

### v0.7 (Community Edition)

- Plugin system (custom playbooks/agents)
- Multi-user support (role-based access)
- Cloud deployment (Docker + K8s)
- API documentation (OpenAPI spec)

### v0.8 (Enterprise Edition)

- Distributed architecture (multi-node)
- Advanced analytics (ML-based predictions)
- Integration with EvoMap (community knowledge)
- SLA guarantees (99.9% uptime)

---

## FAQ

### Q: How does AIOS differ from traditional monitoring tools?

**A:** Traditional tools alert humans to fix issues. AIOS automatically fixes issues and learns from them.

### Q: Can I use AIOS without OpenClaw?

**A:** Yes! AIOS is a standalone framework. OpenClaw integration is optional.

### Q: What happens if a playbook fails?

**A:** Reactor validates the fix. If validation fails, the action is rolled back and logged for human review.

### Q: How do I contribute?

**A:** See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## References

- [README.md](README.md) - Quick start guide
- [TUTORIAL.md](TUTORIAL.md) - Step-by-step tutorial
- [API.md](API.md) - API documentation
- [CHANGELOG.md](CHANGELOG.md) - Version history

---

**Last Updated:** 2026-02-24  
**Maintainer:** 珊瑚海 (yangfei222666-9)  
**License:** MIT
