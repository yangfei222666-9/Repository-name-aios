# 太极OS (TaijiOS) - macOS 配置指南

**版本：** v1.0  
**日期：** 2026-03-12  
**平台：** macOS (Intel / Apple Silicon)

---

## 系统要求

### 硬件
- **CPU:** Intel Core i5+ 或 Apple Silicon (M1/M2/M3)
- **RAM:** 8GB+ (推荐 16GB+)
- **存储:** 20GB+ 可用空间
- **GPU:** 
  - Apple Silicon: 内置 GPU (支持 MPS 加速)
  - Intel: 可选 AMD/NVIDIA GPU

### 软件
- **操作系统:** macOS 11.0 (Big Sur) 或更高版本
- **Python:** 3.12+ (通过 Homebrew 安装)
- **Git:** 最新版本
- **Homebrew:** 包管理器

---

## 快速安装

### 方法 1: 自动安装（推荐）

```bash
# 1. 解压备份文件到目标目录
cd ~/Documents
unzip TaijiOS_Backup.zip
cd TaijiOS_Backup/aios

# 2. 运行自动安装脚本
chmod +x install_macos.sh
./install_macos.sh
```

安装脚本会自动完成：
- ✅ 检查系统要求
- ✅ 安装 Homebrew（如果未安装）
- ✅ 安装 Python 3.12
- ✅ 安装 Git
- ✅ 安装所有依赖
- ✅ 验证安装
- ✅ 创建启动脚本
- ✅ 下载预训练模型（可选）

### 方法 2: 手动安装

```bash
# 1. 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 Python 3.12
brew install python@3.12

# 3. 安装 Git
brew install git

# 4. 升级 pip
python3.12 -m pip install --upgrade pip

# 5. 安装依赖
cd ~/Documents/TaijiOS_Backup/aios
python3.12 -m pip install -r requirements-macos.txt

# 6. 验证安装
python3.12 -c "import torch; import sentence_transformers; import lancedb; print('✅ 安装成功')"
```

---

## 启动服务

### 一键启动所有服务

```bash
cd ~/Documents/TaijiOS_Backup/aios
./start_all.sh
```

这会启动：
- Memory Server (端口 7788)
- Dashboard (端口 8888)

### 单独启动服务

```bash
# Memory Server
./start_memory_server.sh

# Dashboard
./start_dashboard.sh

# Heartbeat
./run_heartbeat.sh
```

### 访问 Dashboard

打开浏览器访问：
- **Dashboard v3.4:** http://127.0.0.1:8888
- **Dashboard v4.0:** http://127.0.0.1:8889 (如果已启动)

---

## 核心依赖说明

### PyTorch (macOS 优化)

在 macOS 上，PyTorch 会自动使用最佳后端：

- **Apple Silicon (M1/M2/M3):** 使用 MPS (Metal Performance Shaders) 加速
- **Intel Mac:** 使用 CPU 或外置 GPU

验证 MPS 支持：
```bash
python3.12 -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

### Sentence Transformers

首次运行时会自动下载模型（约 80MB）：
```bash
python3.12 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### LanceDB

向量数据库，用于 Memory 检索。macOS 上使用预编译版本，无需额外配置。

---

## 常用命令

### 运行 AIOS

```bash
cd ~/Documents/TaijiOS_Backup/aios/agent_system
python3.12 aios.py
```

### 运行 Heartbeat

```bash
cd ~/Documents/TaijiOS_Backup/aios/agent_system
python3.12 heartbeat_v5.py
```

### 运行 Memory Server

```bash
cd ~/Documents/TaijiOS_Backup/aios/agent_system
python3.12 memory_server.py
```

### 运行 Dashboard

```bash
cd ~/Documents/TaijiOS_Backup/aios/dashboard/AIOS-Dashboard-v3.4
python3.12 server.py
```

### 运行测试

```bash
cd ~/Documents/TaijiOS_Backup/aios/agent_system
python3.12 -m pytest tests/
```

---

## 项目结构

```
TaijiOS_Backup/
├── aios/
│   ├── agent_system/          # 核心 Agent 系统
│   │   ├── core/              # 核心模块
│   │   ├── agents/            # Agent 定义
│   │   ├── memory/            # 记忆系统
│   │   ├── data/              # 数据存储
│   │   ├── docs/              # 文档
│   │   ├── scripts/           # 脚本
│   │   └── tests/             # 测试
│   ├── dashboard/             # Dashboard
│   ├── docs/                  # 项目文档
│   ├── install_macos.sh       # macOS 安装脚本
│   ├── requirements-macos.txt # macOS 依赖
│   ├── start_all.sh           # 一键启动脚本
│   ├── start_memory_server.sh # Memory Server 启动脚本
│   ├── start_dashboard.sh     # Dashboard 启动脚本
│   └── run_heartbeat.sh       # Heartbeat 启动脚本
├── MEMORY.md                  # 长期记忆
├── SOUL.md                    # 系统灵魂
├── USER.md                    # 用户信息
└── memory/                    # 日常记忆
```

---

## 常见问题

### 1. Homebrew 安装失败

**问题：** Homebrew 安装过程中网络错误

**解决：**
```bash
# 使用国内镜像
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python 3.12 安装失败

**问题：** `brew install python@3.12` 失败

**解决：**
```bash
# 更新 Homebrew
brew update

# 重试安装
brew install python@3.12

# 或使用 pyenv
brew install pyenv
pyenv install 3.12.0
pyenv global 3.12.0
```

### 3. PyTorch 安装慢

**问题：** PyTorch 下载速度慢

**解决：**
```bash
# 使用清华镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 重新安装
python3.12 -m pip install torch torchvision torchaudio
```

### 4. MPS 不可用

**问题：** `torch.backends.mps.is_available()` 返回 False

**原因：**
- 使用 Intel Mac（MPS 仅支持 Apple Silicon）
- macOS 版本过低（需要 macOS 12.3+）

**解决：**
- Apple Silicon: 升级到 macOS 12.3+
- Intel Mac: 使用 CPU 模式（性能仍然可接受）

### 5. 权限问题

**问题：** `Permission denied` 错误

**解决：**
```bash
# 给脚本添加执行权限
chmod +x install_macos.sh
chmod +x start_all.sh
chmod +x start_memory_server.sh
chmod +x start_dashboard.sh
chmod +x run_heartbeat.sh

# 或使用 sudo（不推荐）
sudo python3.12 -m pip install -r requirements-macos.txt
```

### 6. 端口被占用

**问题：** `Address already in use` 错误

**解决：**
```bash
# 查找占用端口的进程
lsof -i :7788  # Memory Server
lsof -i :8888  # Dashboard

# 杀死进程
kill -9 <PID>

# 或修改配置文件中的端口
```

---

## 性能优化

### 1. 使用 Apple Silicon GPU 加速

在 Apple Silicon Mac 上，PyTorch 会自动使用 MPS 加速：

```python
import torch

# 检查 MPS 是否可用
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("使用 MPS 加速")
else:
    device = torch.device("cpu")
    print("使用 CPU")
```

### 2. 预加载模型

在 `memory_server.py` 启动时预加载常用模型：

```python
from sentence_transformers import SentenceTransformer

# 预加载模型
model = SentenceTransformer('all-MiniLM-L6-v2')
```

### 3. 使用虚拟环境（可选）

```bash
# 创建虚拟环境
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements-macos.txt
```

### 4. 配置 Homebrew 镜像（加速下载）

```bash
# 配置清华镜像
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"

# 写入配置文件
echo 'export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"' >> ~/.zshrc
echo 'export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"' >> ~/.zshrc
echo 'export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"' >> ~/.zshrc
```

---

## 开发工作流

### 1. 每日启动

```bash
# 1. 启动所有服务
cd ~/Documents/TaijiOS_Backup/aios
./start_all.sh

# 2. 访问 Dashboard
open http://127.0.0.1:8888

# 3. 运行 Heartbeat（可选）
./run_heartbeat.sh
```

### 2. 开发新功能

```bash
# 1. 创建新分支
git checkout -b feature/new-feature

# 2. 编写代码
# ...

# 3. 运行测试
cd agent_system
python3.12 -m pytest tests/

# 4. 提交代码
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 3. 调试

```bash
# 使用 Python 调试器
python3.12 -m pdb <script.py>

# 或使用 VS Code / PyCharm
```

---

## IDE 配置

### VS Code（推荐）

**安装扩展：**
- Python (Microsoft)
- Pylance (Microsoft)
- Python Debugger (Microsoft)
- GitLens (Eric Amodio)

**配置文件（`.vscode/settings.json`）：**
```json
{
  "python.defaultInterpreterPath": "/opt/homebrew/bin/python3.12",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.encoding": "utf8"
}
```

**调试配置（`.vscode/launch.json`）：**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    },
    {
      "name": "AIOS: Heartbeat",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/agent_system/heartbeat_v5.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/agent_system"
    }
  ]
}
```

### PyCharm（备选）

**配置 Python 解释器：**
1. PyCharm → Preferences → Project → Python Interpreter
2. 选择 `/opt/homebrew/bin/python3.12` (Apple Silicon)
   或 `/usr/local/bin/python3.12` (Intel)

**配置编码：**
1. PyCharm → Preferences → Editor → File Encodings
2. 设置 Project Encoding 为 UTF-8

---

## 系统服务（可选）

### 使用 launchd 自动启动

创建 `~/Library/LaunchAgents/com.taijios.memoryserver.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taijios.memoryserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/python3.12</string>
        <string>/Users/YOUR_USERNAME/Documents/TaijiOS_Backup/aios/agent_system/memory_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/taijios-memoryserver.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/taijios-memoryserver.error.log</string>
</dict>
</plist>
```

加载服务：
```bash
launchctl load ~/Library/LaunchAgents/com.taijios.memoryserver.plist
```

---

## 备份与恢复

### 备份

```bash
cd ~/Documents/TaijiOS_Backup/aios/agent_system
python3.12 backup.py
```

备份文件保存在 `aios/backups/YYYY-MM-DD/`

### 恢复

```bash
cd ~/Documents/TaijiOS_Backup/aios/agent_system
python3.12 restore.py --backup-dir ../backups/2026-03-12
```

---

## 下一步

1. **阅读核心文档：**
   - `ARCHITECTURE.md` - 系统架构
   - `HEARTBEAT.md` - 心跳机制
   - `MEMORY.md` - 记忆系统

2. **运行示例：**
   - `demo.py` - 基础示例
   - `demo_full_cycle_v2.py` - 完整流程

3. **探索 Agent 系统：**
   - `agent_system/agents/` - Agent 定义
   - `agent_system/core/` - 核心模块

4. **参与开发：**
   - 阅读 `CONTRIBUTING.md`
   - 查看 GitHub Issues
   - 提交 Pull Request

---

## 联系方式

- **项目维护者：** 珊瑚海 (@shh7799)
- **AI 助手：** 小九 🐾
- **项目地址：** ~/Documents/TaijiOS_Backup/aios

---

## 附录：Apple Silicon vs Intel 对比

| 特性 | Apple Silicon (M1/M2/M3) | Intel Mac |
|------|--------------------------|-----------|
| GPU 加速 | ✅ MPS (Metal) | ❌ CPU only |
| 性能 | 🚀 高 | 🐢 中等 |
| 功耗 | 🔋 低 | ⚡ 高 |
| 兼容性 | ✅ 原生支持 | ✅ 完全支持 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**建议：** 如果可能，优先使用 Apple Silicon Mac 以获得最佳性能。

---

**最后更新：** 2026-03-12  
**文档版本：** v1.0  
**作者：** 小九 🐾
