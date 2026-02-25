## Examples

### Basic Usage

```python
from aios import AIOS

# Initialize AIOS
system = AIOS()

# Log an event
system.log_event("error", "network", {
    "code": 502,
    "url": "api.example.com",
    "retry_count": 3
})

# Run the self-healing pipeline
result = system.run_pipeline()
print(f"Pipeline result: {result}")

# Check evolution score
score = system.evolution_score()
print(f"Evolution: {score['score']:.2f} ({score['grade']})")
```

### Multi-Agent Task

```python
from aios import AIOS

system = AIOS()

# Delegate a complex task to specialized agents
result = system.handle_task(
    "Analyze this codebase and suggest optimizations",
    auto_create=True
)

print(f"Task routed to: {result['agent_type']}")
print(f"Session key: {result['session_key']}")
```

### CLI Usage

```bash
# Check system health
aios health

# View evolution score
aios score

# Generate daily insight report
aios insight --since 24h --format telegram

# Run morning reflection
aios reflect --since 24h

# Apply learning suggestions
aios apply

# Run full pipeline
python -c "from aios import AIOS; AIOS().run_pipeline()"
```

### Dashboard

```bash
# Start the real-time dashboard
python -m aios.dashboard.server

# Open http://localhost:9091 in your browser
```

---

## 📚 Documentation

- [Quick Start Guide](docs/QUICKSTART.md) *(coming soon)*
- [Architecture Deep Dive](docs/ARCHITECTURE.md) *(coming soon)*
- [API Reference](docs/API.md) *(coming soon)*
- [Deployment Guide](docs/DEPLOYMENT.md) *(coming soon)*
- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

---
