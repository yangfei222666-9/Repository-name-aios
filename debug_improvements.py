"""
调试 Self-Improving Loop - 查看改进建议
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent_system.analyze_failures import FailureAnalyzer

def main():
    print("=" * 60)
    print("  Failure Analysis - Debug")
    print("=" * 60)
    
    analyzer = FailureAnalyzer()
    
    # 分析最近 1 天的失败
    report = analyzer.analyze(days=1, min_occurrences=1)
    
    print(f"\n[1] 失败模式统计")
    print(f"  总失败模式: {len(report.get('patterns', []))}")
    
    for pattern in report.get('patterns', [])[:5]:
        print(f"\n  模式: {pattern.get('signature')}")
        print(f"    出现次数: {pattern.get('count')}")
        print(f"    影响 Agent: {pattern.get('affected_agents', [])}")
    
    print(f"\n[2] 改进建议")
    print(f"  总建议数: {len(report.get('improvements', []))}")
    
    for imp in report.get('improvements', [])[:5]:
        print(f"\n  建议: {imp.get('description')}")
        print(f"    风险: {imp.get('risk')}")
        print(f"    影响 Agent: {imp.get('affected_agents', [])}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
