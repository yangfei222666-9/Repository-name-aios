# AIOS API Documentation

**Version:** 0.5  
**Last Updated:** 2026-02-24

---

## Table of Contents

1. [Core API](#core-api)
   - [EventBus](#eventbus)
   - [Scheduler](#scheduler)
   - [Reactor](#reactor)
   - [ScoreEngine](#scoreengine)
2. [Agent System](#agent-system)
3. [Memory Palace](#memory-palace)
4. [CLI Commands](#cli-commands)
5. [Configuration](#configuration)
6. [REST API](#rest-api)

---

## Core API

### EventBus

Central event system for component communication.

#### Import

```python
from aios.core import EventBus
```

#### Methods

##### `emit(event_type: str, data: dict) -> str`

Emit an event to the bus.

**Parameters:**
- `event_type` (str): Event type (e.g., "resource.high", "task.failed")
- `data` (dict): Event payload

**Returns:**
- `event_id` (str): Unique event identifier

**Example:**

```python
bus = EventBus()
event_id = bus.emit("resource.high", {
    "resource": "cpu",
    "value": 85,
    "threshold": 80
})
print(f"Event emitted: {event_id}")
```

##### `subscribe(event_type: str, callback: Callable) -> str`

Subscribe to events of a specific type.

**Parameters:**
- `event_type` (str): Event type to listen for (supports wildcards: "resource.*")
- `callback` (Callable): Function to call when event occurs

**Returns:**
- `subscription_id` (str): Unique subscription identifier

**Example:**

```python
def handle_high_cpu(event):
    print(f"High CPU detected: {event['data']['value']}%")

bus.subscribe("resource.high", handle_high_cpu)
```

##### `unsubscribe(subscription_id: str) -> bool`

Unsubscribe from events.

**Parameters:**
- `subscription_id` (str): Subscription ID from `subscribe()`

**Returns:**
- `success` (bool): True if unsubscribed successfully

##### `get_events(event_type: str = None, limit: int = 100) -> List[dict]`

Retrieve historical events.

**Parameters:**
- `event_type` (str, optional): Filter by event type
- `limit` (int): Maximum number of events to return

**Returns:**
- `events` (List[dict]): List of event objects

**Example:**

```python
# Get last 50 resource events
events = bus.get_events("resource.*", limit=50)
for event in events:
    print(f"{event['timestamp']}: {event['type']} - {event['data']}")
```

---

### Scheduler

Decision-making engine that routes events to appropriate handlers.

#### Import

```python
from aios.core import Scheduler
```

#### Methods

##### `schedule(task: dict, priority: str = "P2") -> str`

Schedule a task for execution.

**Parameters:**
- `task` (dict): Task definition
  - `type` (str): Task type (e.g., "reactor.execute", "agent.spawn")
  - `params` (dict): Task parameters
- `priority` (str): Priority level ("P0", "P1", "P2", "P3")

**Returns:**
- `task_id` (str): Unique task identifier

**Example:**

```python
scheduler = Scheduler()
task_id = scheduler.schedule({
    "type": "reactor.execute",
    "params": {
        "playbook_id": "cpu_high_kill_idle",
        "event_id": "evt_123"
    }
}, priority="P1")
```

##### `get_status(task_id: str) -> dict`

Get task execution status.

**Parameters:**
- `task_id` (str): Task ID from `schedule()`

**Returns:**
- `status` (dict): Task status object
  - `state` (str): "pending", "running", "completed", "failed"
  - `progress` (float): 0.0 to 1.0
  - `result` (dict, optional): Task result if completed

**Example:**

```python
status = scheduler.get_status(task_id)
print(f"Task {task_id}: {status['state']} ({status['progress']*100}%)")
```

##### `cancel(task_id: str) -> bool`

Cancel a pending or running task.

**Parameters:**
- `task_id` (str): Task ID to cancel

**Returns:**
- `success` (bool): True if cancelled successfully

---

### Reactor

Automatic remediation engine that executes playbooks.

#### Import

```python
from aios.core import Reactor
```

#### Methods

##### `execute(playbook_id: str, event: dict, dry_run: bool = False) -> dict`

Execute a playbook.

**Parameters:**
- `playbook_id` (str): Playbook identifier
- `event` (dict): Triggering event
- `dry_run` (bool): If True, simulate execution without making changes

**Returns:**
- `result` (dict): Execution result
  - `success` (bool): True if all actions succeeded
  - `actions_executed` (int): Number of actions executed
  - `validation_passed` (bool): True if validation succeeded
  - `error` (str, optional): Error message if failed

**Example:**

```python
reactor = Reactor()
result = reactor.execute("cpu_high_kill_idle", event, dry_run=True)
if result['success']:
    print(f"Playbook executed: {result['actions_executed']} actions")
else:
    print(f"Playbook failed: {result['error']}")
```

##### `match(event: dict) -> List[str]`

Find playbooks that match an event.

**Parameters:**
- `event` (dict): Event to match against

**Returns:**
- `playbook_ids` (List[str]): List of matching playbook IDs

**Example:**

```python
matches = reactor.match({
    "type": "resource.high",
    "data": {"resource": "cpu", "value": 85}
})
print(f"Found {len(matches)} matching playbooks: {matches}")
```

##### `load_playbook(path: str) -> str`

Load a playbook from file.

**Parameters:**
- `path` (str): Path to playbook JSON file

**Returns:**
- `playbook_id` (str): Loaded playbook ID

**Example:**

```python
playbook_id = reactor.load_playbook("playbooks/my_playbook.json")
print(f"Loaded playbook: {playbook_id}")
```

##### `validate_playbook(playbook: dict) -> Tuple[bool, str]`

Validate playbook structure.

**Parameters:**
- `playbook` (dict): Playbook definition

**Returns:**
- `valid` (bool): True if valid
- `error` (str): Error message if invalid

**Example:**

```python
valid, error = reactor.validate_playbook({
    "id": "test",
    "trigger": {"event_type": "test.event"},
    "actions": [{"type": "log", "params": {}}]
})
if not valid:
    print(f"Invalid playbook: {error}")
```

---

### ScoreEngine

Real-time system health scoring.

#### Import

```python
from aios.core import ScoreEngine
```

#### Methods

##### `get_score() -> float`

Get current evolution score.

**Returns:**
- `score` (float): Evolution score (0.0 to 1.0)

**Example:**

```python
engine = ScoreEngine()
score = engine.get_score()
print(f"Evolution Score: {score:.2f}")
```

##### `get_breakdown() -> dict`

Get detailed score breakdown.

**Returns:**
- `breakdown` (dict): Score components
  - `task_success_rate` (float): 0.0 to 1.0
  - `correction_rate` (float): 0.0 to 1.0
  - `uptime` (float): 0.0 to 1.0
  - `learning_rate` (float): 0.0 to 1.0

**Example:**

```python
breakdown = engine.get_breakdown()
print(f"Task Success Rate: {breakdown['task_success_rate']*100}%")
print(f"Correction Rate: {breakdown['correction_rate']*100}%")
```

##### `get_trend(window_hours: int = 24) -> str`

Get score trend over time.

**Parameters:**
- `window_hours` (int): Time window in hours

**Returns:**
- `trend` (str): "improving", "stable", "degrading"

**Example:**

```python
trend = engine.get_trend(window_hours=24)
print(f"24h trend: {trend}")
```

##### `get_history(limit: int = 100) -> List[dict]`

Get historical scores.

**Parameters:**
- `limit` (int): Maximum number of records

**Returns:**
- `history` (List[dict]): Score history
  - `timestamp` (int): Unix timestamp
  - `score` (float): Evolution score
  - `breakdown` (dict): Score components

---

## Agent System

### Agent

Base class for creating custom agents.

#### Import

```python
from aios.agent_system import Agent
```

#### Methods

##### `__init__(agent_id: str, agent_type: str)`

Initialize agent.

**Parameters:**
- `agent_id` (str): Unique agent identifier
- `agent_type` (str): Agent type (e.g., "worker", "monitor")

##### `execute(task: dict) -> dict`

Execute a task (must be implemented by subclass).

**Parameters:**
- `task` (dict): Task definition

**Returns:**
- `result` (dict): Task result

**Example:**

```python
class MyAgent(Agent):
    def __init__(self, agent_id):
        super().__init__(agent_id, "worker")
    
    def execute(self, task):
        # Your logic here
        return {"status": "success", "output": "Task completed"}
```

---

### Dispatcher

Routes tasks to appropriate agents.

#### Import

```python
from aios.agent_system import Dispatcher
```

#### Methods

##### `dispatch(task: dict) -> dict`

Dispatch a task to an agent.

**Parameters:**
- `task` (dict): Task definition
  - `type` (str): Agent type to use
  - `params` (dict): Task parameters

**Returns:**
- `result` (dict): Task result

**Example:**

```python
dispatcher = Dispatcher()
result = dispatcher.dispatch({
    "type": "worker",
    "params": {"file": "data.csv"}
})
```

##### `get_agent_status(agent_id: str) -> dict`

Get agent status.

**Parameters:**
- `agent_id` (str): Agent identifier

**Returns:**
- `status` (dict): Agent status
  - `state` (str): "idle", "running", "blocked", "degraded"
  - `success_rate` (float): 0.0 to 1.0
  - `last_active` (int): Unix timestamp

---

## Memory Palace

Unified memory system for knowledge storage and retrieval.

#### Import

```python
from aios.memory import MemoryPalace
```

#### Methods

##### `store(key: str, value: dict, metadata: dict = None) -> bool`

Store knowledge.

**Parameters:**
- `key` (str): Unique identifier
- `value` (dict): Knowledge content
- `metadata` (dict, optional): Additional metadata

**Returns:**
- `success` (bool): True if stored successfully

**Example:**

```python
mp = MemoryPalace()
mp.store("lesson_001", {
    "category": "error_handling",
    "content": "Always validate input before processing",
    "confidence": 0.9
}, metadata={
    "source": "playbook:validate_input",
    "created_at": 1703260800
})
```

##### `query(query: str, top_k: int = 5) -> List[dict]`

Query knowledge.

**Parameters:**
- `query` (str): Search query
- `top_k` (int): Maximum number of results

**Returns:**
- `results` (List[dict]): Matching knowledge entries

**Example:**

```python
results = mp.query("how to handle errors", top_k=3)
for result in results:
    print(f"Lesson: {result['content']}")
    print(f"Confidence: {result['confidence']}")
```

##### `link(key1: str, key2: str, relation: str) -> bool`

Link related knowledge.

**Parameters:**
- `key1` (str): First knowledge key
- `key2` (str): Second knowledge key
- `relation` (str): Relationship type (e.g., "related_to", "caused_by")

**Returns:**
- `success` (bool): True if linked successfully

**Example:**

```python
mp.link("lesson_001", "lesson_002", "related_to")
```

##### `get(key: str) -> dict`

Retrieve knowledge by key.

**Parameters:**
- `key` (str): Knowledge identifier

**Returns:**
- `value` (dict): Knowledge content (or None if not found)

##### `delete(key: str) -> bool`

Delete knowledge.

**Parameters:**
- `key` (str): Knowledge identifier

**Returns:**
- `success` (bool): True if deleted successfully

---

## CLI Commands

### `aios start`

Start AIOS service.

**Options:**
- `--config PATH`: Path to config file (default: config.json)
- `--log-level LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)
- `--dashboard-port PORT`: Dashboard port (default: 8765)

**Example:**

```bash
aios start --config prod.json --log-level INFO
```

---

### `aios stop`

Stop AIOS service.

**Example:**

```bash
aios stop
```

---

### `aios status`

Show AIOS status.

**Example:**

```bash
aios status
```

**Output:**

```
AIOS v0.5 - Running
Evolution Score: 0.75 (Good)
Active Agents: 3
Pending Tasks: 2
Uptime: 2h 15m
```

---

### `aios event emit`

Emit a custom event.

**Options:**
- `EVENT_TYPE`: Event type
- `--data JSON`: Event data (JSON string)

**Example:**

```bash
aios event emit resource.high --data '{"resource":"cpu","value":85}'
```

---

### `aios playbook list`

List all playbooks.

**Example:**

```bash
aios playbook list
```

**Output:**

```
ID                        Description                    Risk
------------------------  -----------------------------  ------
cpu_high_kill_idle        Kill idle agents on high CPU   low
retry_on_timeout          Retry tasks on timeout         low
restart_failed_service    Restart failed services        medium
```

---

### `aios playbook validate`

Validate a playbook file.

**Options:**
- `PATH`: Path to playbook JSON file

**Example:**

```bash
aios playbook validate playbooks/my_playbook.json
```

**Output:**

```
✓ Playbook is valid
  ID: my_playbook
  Trigger: task.failed
  Actions: 2
  Risk: low
```

---

### `aios memory list`

List stored knowledge.

**Options:**
- `--category CATEGORY`: Filter by category
- `--limit N`: Maximum number of results

**Example:**

```bash
aios memory list --category error_handling --limit 10
```

---

### `aios memory query`

Query knowledge.

**Options:**
- `QUERY`: Search query
- `--top-k N`: Number of results (default: 5)

**Example:**

```bash
aios memory query "how to handle connection timeout" --top-k 3
```

---

### `aios agents list`

List all agents.

**Example:**

```bash
aios agents list
```

**Output:**

```
Agent ID       Type     State    Success Rate  Last Active
-----------    ------   ------   ------------  -----------
agent_001      worker   idle     100%          2s ago
agent_002      worker   running  95%           1s ago
agent_003      monitor  idle     100%          5s ago
```

---

### `aios score show`

Show evolution score.

**Example:**

```bash
aios score show
```

**Output:**

```
Evolution Score: 0.75 (Good)

Breakdown:
- Task Success Rate: 0.85 (85%)
- Correction Rate: 0.70 (70%)
- Uptime: 0.95 (95%)
- Learning Rate: 0.50 (50%)

Trend: Improving ↗
```

---

### `aios logs follow`

Follow live logs.

**Options:**
- `--component NAME`: Filter by component (eventbus, scheduler, reactor)
- `--level LEVEL`: Filter by log level (DEBUG, INFO, WARNING, ERROR)

**Example:**

```bash
aios logs follow --component reactor --level ERROR
```

---

## Configuration

### config.json

Main configuration file.

**Example:**

```json
{
  "environment": "production",
  "log_level": "INFO",
  "data_dir": "data/",
  
  "eventbus": {
    "persist": true,
    "max_events": 10000
  },
  
  "scheduler": {
    "max_concurrent_tasks": 5,
    "default_timeout": 300,
    "retry_policy": {
      "max_retries": 3,
      "backoff_factor": 2
    }
  },
  
  "reactor": {
    "playbooks_dir": "playbooks/",
    "dry_run": false,
    "require_approval": ["high"]
  },
  
  "memory": {
    "enabled": true,
    "backend": "json",
    "path": "memory/"
  },
  
  "dashboard": {
    "enabled": true,
    "port": 8765,
    "auth": {
      "enabled": false,
      "username": "admin",
      "password": "changeme"
    }
  },
  
  "webhooks": {
    "enabled": false,
    "endpoints": []
  }
}
```

---

## REST API

AIOS exposes a REST API for external integrations.

**Base URL:** `http://localhost:8765/api/v1`

### Authentication

If auth is enabled, include API key in header:

```
Authorization: Bearer YOUR_API_KEY
```

---

### `GET /status`

Get system status.

**Response:**

```json
{
  "version": "0.5.0",
  "uptime": 7920,
  "evolution_score": 0.75,
  "active_agents": 3,
  "pending_tasks": 2
}
```

---

### `POST /events`

Emit an event.

**Request:**

```json
{
  "type": "resource.high",
  "data": {
    "resource": "cpu",
    "value": 85
  }
}
```

**Response:**

```json
{
  "event_id": "evt_abc123",
  "timestamp": 1703260800
}
```

---

### `GET /events`

Get events.

**Query Parameters:**
- `type` (optional): Filter by event type
- `limit` (optional): Maximum number of results (default: 100)

**Response:**

```json
{
  "events": [
    {
      "id": "evt_abc123",
      "type": "resource.high",
      "data": {"resource": "cpu", "value": 85},
      "timestamp": 1703260800
    }
  ],
  "total": 1
}
```

---

### `GET /score`

Get evolution score.

**Response:**

```json
{
  "score": 0.75,
  "grade": "good",
  "breakdown": {
    "task_success_rate": 0.85,
    "correction_rate": 0.70,
    "uptime": 0.95,
    "learning_rate": 0.50
  },
  "trend": "improving"
}
```

---

### `GET /agents`

List agents.

**Response:**

```json
{
  "agents": [
    {
      "id": "agent_001",
      "type": "worker",
      "state": "idle",
      "success_rate": 1.0,
      "last_active": 1703260800
    }
  ],
  "total": 1
}
```

---

### `POST /playbooks/execute`

Execute a playbook.

**Request:**

```json
{
  "playbook_id": "cpu_high_kill_idle",
  "event_id": "evt_abc123",
  "dry_run": false
}
```

**Response:**

```json
{
  "success": true,
  "actions_executed": 2,
  "validation_passed": true,
  "execution_time": 1.23
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (invalid API key) |
| 404 | Not Found (resource doesn't exist) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (AIOS not running) |

---

## Rate Limits

- **Free tier:** 100 requests/minute
- **Pro tier:** 1000 requests/minute
- **Enterprise:** Unlimited

---

## SDK Support

Official SDKs:
- **Python:** `pip install aios-sdk`
- **JavaScript:** `npm install aios-sdk`
- **Go:** `go get github.com/aios/sdk-go`

**Example (Python SDK):**

```python
from aios_sdk import AIOSClient

client = AIOSClient(api_key="YOUR_API_KEY")

# Emit event
client.events.emit("resource.high", {"resource": "cpu", "value": 85})

# Get score
score = client.score.get()
print(f"Evolution Score: {score.value}")
```

---

## Support

- **Documentation:** https://docs.aios.dev
- **GitHub Issues:** https://github.com/yangfei222666-9/aios/issues
- **Discord:** https://discord.gg/aios
- **Email:** support@aios.dev

---

**Last Updated:** 2026-02-24  
**Maintainer:** 珊瑚海 (yangfei222666-9)  
**License:** MIT
