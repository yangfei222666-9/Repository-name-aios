# aios/scripts/daily_report.py - cron 入口：生成报告并输出
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from learning.analyze import generate_daily_report, generate_full_report
from learning.baseline import evolution_score

if __name__ == "__main__":
    fmt = sys.argv[1] if len(sys.argv) > 1 else "text"
    if fmt == "json":
        r = generate_full_report(days=1)
        r["evolution"] = evolution_score()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(generate_daily_report(days=1))
