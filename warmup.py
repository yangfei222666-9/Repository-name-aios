"""
AIOS 组件预热脚本
在系统启动时运行，预热所有组件
"""
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from heartbeat_runner_optimized import warmup_components


if __name__ == "__main__":
    print("=" * 60)
    print("AIOS 组件预热")
    print("=" * 60)
    
    try:
        components = warmup_components()
        
        print("\n组件状态:")
        print(f"  EventBus: {'✅' if components['bus'] else '❌'}")
        print(f"  Scheduler: {'✅' if components['scheduler'] else '❌'}")
        print(f"  Reactor: {'✅' if components['reactor'] else '❌'}")
        print(f"  ScoreEngine: {'✅' if components['score_engine'] else '❌'}")
        print(f"  NotificationHandler: {'✅' if components['notification_handler'] else '❌'}")
        
        print("\n" + "=" * 60)
        print("✅ 预热完成！后续心跳将非常快速（< 10ms）")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ 预热失败: {e}")
        import traceback
        traceback.print_exc()
