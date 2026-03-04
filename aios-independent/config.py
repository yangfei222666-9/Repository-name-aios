"""
AIOS Independent - 配置文件
"""
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR.parent / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

# Telegram 配置（从环境变量读取，或使用默认值）
import os
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your_token_here")
