"""
手动触发 Self-Improving Loop 测试脚本
模拟 coder-dispatcher Agent 连续失败 3 次后的自动改进
"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from agent_system.self_improving_loop import SelfImprovingLoop

def main():
    print("=" * 60)
    print("  Self-Improving Loop - Manual Trigger Test")
    print("=" * 60)
    
    loop = SelfImprovingLoop()
    
    # 检查 coder-dispatcher 是否应该触发改进
    agent_id = "coder-dispatcher"
    
    print(f"\n[1] 检查 {agent_id} 是否需要改进...")
    should_improve = loop._should_trigger_improvement(agent_id)
    print(f"  结果: {'✓ 需要改进' if should_improve else '✗ 不需要改进'}")
    
    if should_improve:
        print(f"\n[2] 触发改进循环...")
        applied_count = loop._run_improvement_cycle(agent_id)
        print(f"  应用了 {applied_count} 个改进")
        
        print(f"\n[3] 查看改进统计...")
        stats = loop.get_improvement_stats(agent_id)
        print(f"  Agent: {stats.get('agent_id')}")
        print(f"  最后改进时间: {stats.get('last_improvement')}")
        print(f"  冷却剩余时间: {stats.get('cooldown_remaining_hours', 0):.1f}h")
    else:
        print(f"\n[2] 跳过改进（不满足触发条件）")
        print(f"  可能原因：")
        print(f"    - 失败次数不足（需要 ≥3 次）")
        print(f"    - 在冷却期内（6 小时）")
        print(f"    - 没有追踪数据")
    
    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
