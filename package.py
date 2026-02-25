#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS v1.0 打包脚本
创建 AIOS-v1.0-demo.zip（可直接复制运行）
"""
import sys
import os
import zipfile
from pathlib import Path
import shutil

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

AIOS_ROOT = Path(__file__).parent

# 需要打包的文件和目录
INCLUDE_PATTERNS = [
    # 核心文件
    "aios.py",
    "demo_simple.py",
    "demo_api_health.py",
    "README.md",
    "LICENSE",
    
    # 核心目录
    "observability/",
    "agent_system/",
    "dashboard/",
    "core/",
    
    # 配置和文档
    "config.yaml",
    "API.md",
    "TUTORIAL.md",
    
    # 测试
    "tests/",
]

# 排除的文件和目录
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    "*.egg-info",
    "dist",
    "build",
    ".git",
    ".github",
    "data/",  # 不打包数据文件
    "logs/",
    "events.jsonl",
    "*.log",
]

def should_include(path: Path) -> bool:
    """判断是否应该包含该文件"""
    path_str = str(path.relative_to(AIOS_ROOT))
    
    # 检查排除模式
    for pattern in EXCLUDE_PATTERNS:
        if pattern.endswith("/"):
            if pattern[:-1] in path_str.split(os.sep):
                return False
        elif pattern.startswith("*."):
            if path.name.endswith(pattern[1:]):
                return False
        elif pattern in path_str:
            return False
    
    return True

def create_package():
    """创建打包文件"""
    print("=" * 70)
    print("  📦 AIOS v1.0 打包工具")
    print("=" * 70)
    
    # 输出文件
    output_file = AIOS_ROOT / "AIOS-v1.0-demo.zip"
    
    if output_file.exists():
        print(f"\n⚠️  删除旧文件: {output_file.name}")
        output_file.unlink()
    
    print(f"\n📝 创建打包文件: {output_file.name}")
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        file_count = 0
        
        # 遍历所有文件
        for pattern in INCLUDE_PATTERNS:
            pattern_path = AIOS_ROOT / pattern
            
            if pattern.endswith("/"):
                # 目录
                dir_path = AIOS_ROOT / pattern[:-1]
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file() and should_include(file_path):
                            arcname = f"aios/{file_path.relative_to(AIOS_ROOT)}"
                            zf.write(file_path, arcname)
                            file_count += 1
                            if file_count % 10 == 0:
                                print(f"   已打包 {file_count} 个文件...")
            else:
                # 单个文件
                if pattern_path.exists():
                    arcname = f"aios/{pattern}"
                    zf.write(pattern_path, arcname)
                    file_count += 1
        
        # 添加 README（如果不在 INCLUDE_PATTERNS 里）
        if "README.md" not in INCLUDE_PATTERNS:
            readme_path = AIOS_ROOT / "README.md"
            if readme_path.exists():
                zf.write(readme_path, "aios/README.md")
                file_count += 1
        
        print(f"\n✅ 打包完成！共 {file_count} 个文件")
    
    # 显示文件大小
    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"📊 文件大小: {size_mb:.2f} MB")
    print(f"📁 输出路径: {output_file}")
    
    print("\n" + "=" * 70)
    print("  ✅ 打包成功！")
    print("=" * 70)
    
    print("\n💡 使用方法:")
    print("   1. 解压 AIOS-v1.0-demo.zip")
    print("   2. cd aios")
    print("   3. python aios.py demo")
    print("   4. python aios.py dashboard")

if __name__ == "__main__":
    try:
        create_package()
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
