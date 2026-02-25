"""
AIOS Dashboard 启动脚本
自动检测端口占用并切换到可用端口

使用方法：
python -X utf8 aios/start_dashboard.py
"""
import sys
from pathlib import Path

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from dashboard.server import run_server

if __name__ == "__main__":
    print("=" * 60)
    print("AIOS v0.5 Dashboard")
    print("=" * 60)
    print("")
    
    # 启动服务器（自动端口检测）
    run_server(auto_port=True)
