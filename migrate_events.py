"""
AIOS v0.6 事件存储迁移脚本
从旧的单文件 events.jsonl 迁移到新的按日期分文件结构
"""
import sys
from pathlib import Path

# 设置 UTF-8 输出
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.event_store import get_event_store


def migrate():
    """执行迁移"""
    workspace = Path(__file__).parent
    old_file = workspace / "data" / "events.jsonl"
    
    if not old_file.exists():
        print("OK 没有找到旧的 events.jsonl，无需迁移")
        return
    
    print(f"[迁移] 开始迁移 {old_file}...")
    store = get_event_store()
    count = store.migrate_from_single_file(old_file)
    
    if count > 0:
        print(f"[迁移] 完成！共迁移 {count} 个事件")
        print(f"[迁移] 新文件位置：{store.base_dir}")
        print(f"[迁移] 旧文件已备份到：{old_file}.bak")
    else:
        print("[迁移] 失败或文件为空")


if __name__ == "__main__":
    migrate()
