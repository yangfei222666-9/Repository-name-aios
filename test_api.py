"""
Test AIOS Python API
"""
from aios import AIOS
import json

print("=== AIOS API Test ===\n")

# 1. Initialize
print("1. Initializing AIOS...")
system = AIOS()
print("   OK AIOS initialized\n")

# 2. Log event
print("2. Logging test event...")
system.log_event("TOOL", "test", {
    "action": "api_test",
    "timestamp": "2026-02-23T18:28:00"
})
print("   OK Event logged\n")

# 3. Load events
print("3. Loading recent events...")
events = system.load_events(days=1)
print(f"   OK Loaded {len(events)} events\n")

# 4. Evolution score
print("4. Checking evolution score...")
score = system.evolution_score()
print(f"   Score: {score.get('score', 'N/A')}")
print(f"   Grade: {score.get('grade', 'N/A')}")
print(f"   OK Evolution score retrieved\n")

# 5. Config
print("5. Loading config...")
config = system.config
print(f"   OK Config loaded ({len(config)} keys)\n")

print("=== All Tests Passed ===")
