# aios/plugins/aram/data_adapter.py - 数据适配层
"""
读写 ARAM 数据，隔离文件路径细节。
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.config import get_path

ARAM_DATA = Path(r"C:\Users\A\Desktop\ARAM-Helper\aram_data.json")
ALIAS_FILE = get_path("paths.alias")

_cache = {}


def load_champions() -> dict:
    """加载英雄数据 {id: {name, title, items, ...}}"""
    if "champs" in _cache:
        return _cache["champs"]
    if not ARAM_DATA.exists():
        return {}
    data = json.loads(ARAM_DATA.read_text(encoding="utf-8"))
    _cache["champs"] = data
    return data


def load_aliases() -> dict:
    """加载 learned aliases"""
    if not ALIAS_FILE or not ALIAS_FILE.exists():
        return {}
    try:
        return json.loads(ALIAS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_aliases(aliases: dict):
    """保存 learned aliases"""
    if not ALIAS_FILE:
        return
    ALIAS_FILE.parent.mkdir(exist_ok=True)
    ALIAS_FILE.write_text(
        json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def champion_count() -> int:
    return len(load_champions())


def get_champion(cid: str) -> dict:
    return load_champions().get(cid, {})
