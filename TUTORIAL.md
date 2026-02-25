# AIOS Tutorial - From Zero to Hero

**Version:** 0.5  
**Estimated Time:** 30-45 minutes  
**Prerequisites:** Python 3.8+, basic command line knowledge

---

## What You'll Build

By the end of this tutorial, you'll have:
- ✅ A working AIOS instance monitoring your system
- ✅ Custom playbooks that auto-fix common issues
- ✅ A dashboard showing real-time health metrics
- ✅ An agent that learns from mistakes

---

## Part 1: Installation (5 min)

### Step 1: Install AIOS

```bash
# Option A: Install from PyPI (recommended)
pip install aios-framework

# Option B: Install from source
git clone https://github.com/yangfei222666-9/aios.git
cd aios
pip install -e .
```

### Step 2: Verify Installation

```bash
python -c "import aios; print(aios.__version__)"
# Expected output: 0.5.0
```

### Step 3: Create Workspace

```bash
mkdir my-aios-project
cd my-aios-project
aios init
```

This creates:
```
my-aios-project/
├── config.json          # Configuration
├── playbooks/           # Custom playbooks
├── data/                # Events and logs
└── memory/              # Knowledge base
```

---

## Part 2: First Run (10 min)

### Step 1: Start AIOS

```bash
aios start
```

You should see:
```
[INFO] EventBus initialized
[INFO] Scheduler started
[INFO] Reactor loaded 5 playbooks
[INFO] Dashboard running on http://localhost:8765
[INFO] AIOS v0.5 ready!
```

### Step 2: Open Dashboard

Visit http://localhost:8765 in your browser.

You'll see:
- **Evolution Score:** 1.0 (perfect, because nothing has happened yet)
- **Event Timeline:** Empty
- **Active Agents:** 0

### Step 3: Trigger Your First Event

Open a new terminal and run:

```bash
# Simulate high CPU usage
aios event emit resource.high --data '{"resource":"cpu","value":85}'
```

Watch the dashboard:
1. Event appears in timeline
2. Scheduler analyzes it
3. Reactor matches playbook "cpu_high_alert"
4. Action executed: Log warning
5. Evolution Score updates

---

## Part 3: Create Your First Playbook (10 min)

### Step 1: Understand the Problem

Let's say you have a script that occasionally fails with "Connection timeout". You want AIOS to automatically retry it.

### Step 2: Create Playbook File

Create `playbooks/retry_on_timeout.json`:

```json
{
  "id": "retry_on_timeout",
  "description": "Auto-retry tasks that fail with connection timeout",
  "trigger": {
    "event_type": "task.failed",
    "conditions": {
      "error_message": ".*Connection timeout.*"
    }
  },
  "actions": [
    {
      "type": "retry_task",
      "params": {
        "max_retries": 3,
        "delay_seconds": 5
      }
    }
  ],
  "validation": {
    "check": "task_succeeded",
    "timeout_seconds": 30
  },
  "risk_level": "low"
}
```

### Step 3: Reload Playbooks

```bash
aios reload
```

Output:
```
[INFO] Loaded 6 playbooks (1 new)
[INFO] Playbook 'retry_on_timeout' registered
```

### Step 4: Test It

```bash
# Simulate a timeout error
aios event emit task.failed --data '{
  "task_id": "test_123",
  "error_message": "Connection timeout after 30s"
}'
```

Watch the dashboard:
1. Event: `task.failed`
2. Playbook matched: `retry_on_timeout`
3. Action: Retry task (attempt 1/3)
4. Result: Success (or retry again)

---

## Part 4: Add Memory (10 min)

### Step 1: Enable Memory Palace

Edit `config.json`:

```json
{
  "memory": {
    "enabled": true,
    "backend": "json",
    "path": "memory/"
  }
}
```

### Step 2: Store Knowledge

```python
from aios.memory import MemoryPalace

mp = MemoryPalace()

# Store a lesson learned
mp.store("lesson_timeout", {
    "category": "network",
    "content": "Connection timeouts often resolve with retry + exponential backoff",
    "confidence": 0.9,
    "source": "playbook:retry_on_timeout",
    "verified_count": 0
})
```

### Step 3: Query Knowledge

```python
# Later, when a similar error occurs
results = mp.query("how to handle connection timeout", top_k=3)

for result in results:
    print(f"Lesson: {result['content']}")
    print(f"Confidence: {result['confidence']}")
```

### Step 4: Automatic Learning

AIOS automatically extracts lessons from repeated errors:

```bash
# After 3+ similar errors, AIOS creates a lesson
aios event emit task.failed --data '{"error_message": "Connection timeout"}'
aios event emit task.failed --data '{"error_message": "Connection timeout"}'
aios event emit task.failed --data '{"error_message": "Connection timeout"}'

# Check memory
aios memory list
```

Output:
```
[INFO] Found 1 new lesson:
  - lesson_auto_001: "Connection timeout" → retry with backoff
  - Confidence: 0.7 (draft)
  - Verified: 0 times
```

---

## Part 5: Agent System (10 min)

### Step 1: Create an Agent

```python
from aios.agent_system import Agent, AgentRegistry

class MyAgent(Agent):
    def __init__(self, agent_id):
        super().__init__(agent_id, agent_type="worker")
    
    def execute(self, task):
        # Your task logic here
        print(f"Executing task: {task['name']}")
        return {"status": "success"}

# Register agent
registry = AgentRegistry()
registry.register("worker", MyAgent)
```

### Step 2: Dispatch Tasks

```python
from aios.agent_system import Dispatcher

dispatcher = Dispatcher()

# Dispatch a task
task = {
    "name": "process_data",
    "type": "worker",
    "params": {"file": "data.csv"}
}

result = dispatcher.dispatch(task)
print(result)  # {"status": "success"}
```

### Step 3: Monitor Agent Health

```bash
aios agents list
```

Output:
```
Agent ID       Type     State    Success Rate  Last Active
-----------    ------   ------   ------------  -----------
agent_001      worker   idle     100%          2s ago
agent_002      worker   running  95%           1s ago
```

### Step 4: Auto-Recovery

If an agent fails repeatedly, AIOS automatically:
1. Marks it as `degraded`
2. Routes new tasks to healthy agents
3. Attempts recovery after cooldown
4. Archives if unrecoverable

---

## Part 6: Evolution & Learning (5 min)

### Step 1: Track Evolution Score

```bash
aios score show
```

Output:
```
Evolution Score: 0.75 (Good)

Breakdown:
- Task Success Rate: 0.85 (85%)
- Correction Rate: 0.70 (70%)
- Uptime: 0.95 (95%)
- Learning Rate: 0.50 (50%)

Trend: Improving ↗
```

### Step 2: View Improvement Suggestions

```bash
aios evolve suggest
```

Output:
```
[INFO] Found 3 improvement opportunities:

1. Increase timeout for "fetch_data" task
   - Current: 30s
   - Suggested: 60s
   - Reason: 15% of failures are timeouts
   - Risk: Low

2. Add retry logic to "send_email" task
   - Current: No retry
   - Suggested: 3 retries with 5s delay
   - Reason: 20% of failures are transient
   - Risk: Low

3. Optimize "process_large_file" memory usage
   - Current: 2GB peak
   - Suggested: Stream processing
   - Reason: Causing OOM errors
   - Risk: Medium (requires code change)
```

### Step 3: Auto-Apply Low-Risk Improvements

```bash
aios evolve apply --risk low
```

Output:
```
[INFO] Applied 2 improvements:
  ✓ Increased timeout for "fetch_data" (30s → 60s)
  ✓ Added retry logic to "send_email" (3 retries)

[INFO] Skipped 1 medium-risk improvement (requires approval)
```

---

## Part 7: Production Deployment (5 min)

### Step 1: Configure for Production

Edit `config.json`:

```json
{
  "environment": "production",
  "log_level": "INFO",
  "dashboard": {
    "enabled": true,
    "port": 8765,
    "auth": {
      "enabled": true,
      "username": "admin",
      "password": "your-secure-password"
    }
  },
  "scheduler": {
    "max_concurrent_tasks": 5,
    "default_timeout": 300
  },
  "reactor": {
    "dry_run": false,
    "require_approval": ["high"]
  }
}
```

### Step 2: Run as Service

**Linux (systemd):**

Create `/etc/systemd/system/aios.service`:

```ini
[Unit]
Description=AIOS Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/my-aios-project
ExecStart=/usr/bin/python -m aios start
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable aios
sudo systemctl start aios
sudo systemctl status aios
```

**Windows (Task Scheduler):**

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "python" -Argument "-m aios start" -WorkingDirectory "C:\path\to\my-aios-project"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "AIOS" -Action $action -Trigger $trigger -RunLevel Highest
```

### Step 3: Monitor Logs

```bash
# View live logs
aios logs follow

# View specific component
aios logs follow --component reactor

# View errors only
aios logs follow --level error
```

---

## Part 8: Advanced Topics

### Custom Event Types

```python
from aios.core import EventBus

bus = EventBus()

# Define custom event
bus.emit("custom.deployment", {
    "service": "api-server",
    "version": "v2.0.1",
    "status": "success"
})
```

### Custom Actions

```python
from aios.core.reactor import Action

class CustomAction(Action):
    def execute(self, params):
        # Your custom logic
        print(f"Executing custom action with {params}")
        return {"status": "success"}

# Register action
from aios.core.reactor import ActionRegistry
ActionRegistry.register("custom_action", CustomAction)
```

### Webhooks

```python
# config.json
{
  "webhooks": {
    "enabled": true,
    "endpoints": [
      {
        "url": "https://your-server.com/webhook",
        "events": ["task.failed", "agent.degraded"],
        "method": "POST"
      }
    ]
  }
}
```

---

## Troubleshooting

### Issue: Dashboard not loading

**Solution:**
```bash
# Check if port is in use
netstat -an | grep 8765

# Try different port
aios start --dashboard-port 8766
```

### Issue: Playbook not triggering

**Solution:**
```bash
# Check playbook syntax
aios playbook validate playbooks/my_playbook.json

# Enable debug logging
aios start --log-level DEBUG
```

### Issue: High memory usage

**Solution:**
```bash
# Check event log size
du -h data/events.jsonl

# Rotate logs
aios logs rotate --keep-days 7
```

---

## Next Steps

1. **Read [ARCHITECTURE.md](ARCHITECTURE.md)** - Understand system internals
2. **Read [API.md](API.md)** - Explore programmatic API
3. **Join Discord** - Get help from the community
4. **Contribute** - See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Example Projects

### 1. Web Scraper Monitor

Auto-restart scrapers that fail with rate limits:

```json
{
  "id": "restart_rate_limited_scraper",
  "trigger": {
    "event_type": "task.failed",
    "conditions": {"error_message": ".*429.*"}
  },
  "actions": [
    {"type": "wait", "params": {"seconds": 60}},
    {"type": "retry_task", "params": {"max_retries": 1}}
  ]
}
```

### 2. Database Backup Monitor

Alert if backup fails:

```json
{
  "id": "backup_failure_alert",
  "trigger": {
    "event_type": "task.failed",
    "conditions": {"task_name": "daily_backup"}
  },
  "actions": [
    {"type": "send_notification", "params": {
      "channel": "slack",
      "message": "⚠️ Database backup failed!"
    }}
  ]
}
```

### 3. CI/CD Pipeline Monitor

Auto-retry flaky tests:

```json
{
  "id": "retry_flaky_tests",
  "trigger": {
    "event_type": "test.failed",
    "conditions": {"flaky": true}
  },
  "actions": [
    {"type": "retry_task", "params": {"max_retries": 2}}
  ]
}
```

---

## Resources

- **Documentation:** https://docs.aios.dev
- **GitHub:** https://github.com/yangfei222666-9/aios
- **Discord:** https://discord.gg/aios
- **Examples:** https://github.com/yangfei222666-9/aios-examples

---

**Congratulations!** 🎉 You've built a self-healing, self-learning system. Now go break things and watch AIOS fix them automatically!

---

**Last Updated:** 2026-02-24  
**Maintainer:** 珊瑚海 (yangfei222666-9)  
**License:** MIT
