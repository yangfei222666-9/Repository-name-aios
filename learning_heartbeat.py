"""
AIOS 自学习心跳任务
每天运行一次，分析数据并生成学习报告
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.learning_workflow import get_learning_workflow


def run_learning_heartbeat():
    """运行学习心跳"""
    workflow = get_learning_workflow()
    
    # 生成学习报告
    report = workflow.generate_learning_report()
    
    # 保存报告
    report_file = workflow.learning_dir / f"report_{Path(__file__).parent.parent.name}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 报告已保存: {report_file}")
    
    # 检查是否有重要建议
    recommendations = workflow.get_playbook_recommendations()
    
    if any(r["action"] == "disable" for r in recommendations):
        print("\n⚠️  发现低效 Playbook，建议禁用")
        return "LEARNING_SUGGESTIONS"
    
    return "LEARNING_OK"


if __name__ == "__main__":
    result = run_learning_heartbeat()
    print(f"\n{result}")
