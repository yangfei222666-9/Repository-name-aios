# aios/scripts/log_event.py - CLI wrapper for core/engine
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import log_event, load_events, count_by_type

if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="log_event")
    p.add_argument("type", help="event type")
    p.add_argument("source", help="source module")
    p.add_argument("summary", help="summary")
    p.add_argument("--data", default=None, help="JSON data")
    args = p.parse_args()

    data = json.loads(args.data) if args.data else None
    ev = log_event(args.type, args.source, args.summary, data)
    print(json.dumps(ev, ensure_ascii=False))
