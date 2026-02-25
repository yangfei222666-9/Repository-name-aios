"""
AIOS v0.6 事件清理脚本
自动归档和清理旧事件
"""
from pathlib import Path
from core.event_store import get_event_store


def cleanup():
    """执行清理"""
    print("🧹 开始清理旧事件...")
    store = get_event_store()
    stats = store.cleanup()
    
    print(f"\n📊 清理统计：")
    print(f"  - 归档文件数：{stats['archived']}")
    print(f"  - 删除文件数：{stats['deleted']}")
    print(f"  - 节省空间：{stats['saved_bytes'] / 1024 / 1024:.2f} MB")
    
    if stats['archived'] == 0 and stats['deleted'] == 0:
        print("✅ 无需清理")
    else:
        print("✅ 清理完成！")


if __name__ == "__main__":
    cleanup()
