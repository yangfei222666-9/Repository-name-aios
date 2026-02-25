#!/usr/bin/env python3
"""
OpenClaw Event Collector
监听 OpenClaw 会话日志，提取工具调用事件并写入 AIOS events.jsonl
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Paths
WORKSPACE = Path(__file__).parent.parent.parent
SESSION_LOG_DIR = WORKSPACE / ".." / "sessions"
EVENTS_FILE = WORKSPACE / "aios" / "events" / "events.jsonl"

# Ensure events directory exists
EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)


def emit_event(layer: str, event: str, status: str, data: Dict[str, Any]):
    """Emit event to AIOS events.jsonl"""
    record = {
        "ts": datetime.now().isoformat(),
        "epoch": int(time.time()),
        "layer": layer,
        "event": event,
        "status": status,
        "severity": "ERROR" if status == "err" else "INFO",
        "payload": data
    }
    with open(EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_tool_call(log_line: str) -> Optional[Dict[str, Any]]:
    """Parse tool call from session log line"""
    try:
        data = json.loads(log_line)
        if data.get("type") == "tool_use":
            return {
                "tool": data.get("name"),
                "input": data.get("input", {}),
                "timestamp": data.get("timestamp")
            }
        elif data.get("type") == "tool_result":
            return {
                "tool": data.get("tool_name"),
                "success": not data.get("is_error", False),
                "output": data.get("content", ""),
                "timestamp": data.get("timestamp")
            }
    except:
        pass
    return None


def tail_session_logs(session_key: str = "main", interval: int = 5):
    """Tail session logs and emit events"""
    session_dir = SESSION_LOG_DIR / session_key
    if not session_dir.exists():
        print(f"Session directory not found: {session_dir}")
        return

    # Find latest log file
    log_files = sorted(session_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not log_files:
        print(f"No log files found in {session_dir}")
        return

    log_file = log_files[0]
    print(f"Tailing {log_file}")

    # Track last position
    last_pos = log_file.stat().st_size

    while True:
        try:
            current_size = log_file.stat().st_size
            if current_size > last_pos:
                with open(log_file, "r", encoding="utf-8") as f:
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    last_pos = f.tell()

                for line in new_lines:
                    tool_data = parse_tool_call(line.strip())
                    if tool_data:
                        if "success" in tool_data:
                            # Tool result
                            emit_event(
                                layer="TOOL",
                                event=f"tool_{tool_data['tool']}",
                                status="ok" if tool_data["success"] else "err",
                                data={
                                    "tool": tool_data["tool"],
                                    "success": tool_data["success"],
                                    "output_len": len(str(tool_data.get("output", "")))
                                }
                            )
                        else:
                            # Tool call
                            emit_event(
                                layer="TOOL",
                                event=f"tool_call_{tool_data['tool']}",
                                status="ok",
                                data={
                                    "tool": tool_data["tool"],
                                    "input_keys": list(tool_data.get("input", {}).keys())
                                }
                            )

            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    import sys
    session = sys.argv[1] if len(sys.argv) > 1 else "main"
    tail_session_logs(session)
