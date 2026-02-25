"""
AIOS initialization wizard
"""
import os
import sys
from pathlib import Path
import yaml


def init_aios():
    """Initialize AIOS workspace"""
    print("🧠 AIOS Initialization Wizard")
    print("=" * 50)
    
    # 1. Choose workspace location
    default_workspace = Path.home() / ".aios"
    workspace = input(f"\nWorkspace location [{default_workspace}]: ").strip()
    if not workspace:
        workspace = default_workspace
    else:
        workspace = Path(workspace)
    
    workspace.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created workspace: {workspace}")
    
    # 2. Create directory structure
    dirs = ["events", "learning", "data", "reports", "plugins"]
    for d in dirs:
        (workspace / d).mkdir(exist_ok=True)
    print(f"✓ Created {len(dirs)} directories")
    
    # 3. Create config.yaml
    config = {
        "paths": {
            "workspace": str(workspace),
            "events": str(workspace / "events" / "events.jsonl"),
            "learning": str(workspace / "learning"),
            "data": str(workspace / "data"),
        },
        "sensors": {
            "file_watcher": {"enabled": True, "cooldown_minutes": 10},
            "process_monitor": {"enabled": True, "cooldown_minutes": 5},
            "system_health": {"enabled": True, "cooldown_minutes": 30},
            "network_probe": {"enabled": True, "cooldown_minutes": 10},
        },
        "reactor": {
            "auto_execute": True,
            "require_confirm_for_high_risk": True,
        },
        "evolution": {
            "baseline_window_days": 7,
            "alert_on_degradation": True,
        },
    }
    
    config_path = workspace / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    print(f"✓ Created config: {config_path}")
    
    # 4. Create initial event
    events_file = workspace / "events" / "events.jsonl"
    import json
    import time
    event = {
        "ts": int(time.time()),
        "layer": "KERNEL",
        "category": "init",
        "data": {"message": "AIOS initialized"},
    }
    with open(events_file, "w") as f:
        f.write(json.dumps(event) + "\n")
    print(f"✓ Created events file: {events_file}")
    
    # 5. Success message
    print("\n" + "=" * 50)
    print("✅ AIOS initialized successfully!")
    print("\nNext steps:")
    print(f"  1. cd {workspace}")
    print("  2. aios health          # Check system health")
    print("  3. aios dashboard       # Start web dashboard")
    print("  4. python -c 'from aios import AIOS; AIOS().run_pipeline()'")
    print("\nDocumentation: https://github.com/yangfei222666-9/aios")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(init_aios())
