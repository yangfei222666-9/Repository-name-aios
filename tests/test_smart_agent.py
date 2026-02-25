"""
创建一个测试 Agent，验证学习功能
"""
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from collaboration.smart_pool import SmartAgentPool
from collaboration.registry import AgentRegistry

def main():
    print("=" * 60)
    print("创建测试 Agent")
    print("=" * 60)
    
    # 创建智能池
    registry = AgentRegistry()
    pool = SmartAgentPool(registry)
    
    # 创建一个 coder Agent
    print("\n📝 创建 Agent: smart-coder-001")
    spec = pool.spawn_spec(
        agent_id="smart-coder-001",
        template="coder",
        task_description="编写一个简单的 Python 脚本，读取文件并统计行数"
    )
    
    print(f"\n✅ Agent 创建成功")
    print(f"   ID: smart-coder-001")
    print(f"   模型: {spec.get('model', 'N/A')}")
    print(f"   能力: {spec.get('capabilities', [])}")
    
    print(f"\n📋 增强后的 Prompt:")
    print(spec.get('task', 'N/A'))
    
    print("\n" + "=" * 60)
    print("✅ 完成")
    print("\n💡 提示：")
    print("   - Agent 已创建并注入了历史教训")
    print("   - 如果执行失败，会自动降级重试")
    print("   - 所有结果会记录到学习日志")

if __name__ == "__main__":
    main()
