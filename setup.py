"""
AIOS - Self-Learning AI Agent Framework
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = (
    readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""
)

setup(
    name="aios-framework",
    version="0.5.0",
    author="Shanhuhai",
    author_email="",
    description="Self-healing, self-learning AI operating system with event-driven architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yangfei222666-9/aios",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "watchdog>=3.0.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "websockets>=12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aios=aios.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "aios": [
            "config.yaml",
            "data/*.json",
            "data/*.jsonl",
            "dashboard/templates/*.html",
            "dashboard/static/*.css",
            "dashboard/static/*.js",
        ],
    },
    keywords="ai agent framework self-learning autonomous self-healing event-driven aios",
    project_urls={
        "Documentation": "https://github.com/yangfei222666-9/aios#readme",
        "Bug Reports": "https://github.com/yangfei222666-9/aios/issues",
        "Source": "https://github.com/yangfei222666-9/aios",
        "Changelog": "https://github.com/yangfei222666-9/aios/blob/main/CHANGELOG.md",
    },
)
