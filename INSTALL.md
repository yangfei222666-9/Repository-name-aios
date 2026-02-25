# AIOS 安装指南

> **AIOS** - AI Operating System  
> 一个自我进化的 AI Agent 系统

---

## 📋 安装清单（Checklist）

- [ ] 1. 安装 Python 3.12+
- [ ] 2. 克隆 AIOS 仓库
- [ ] 3. 安装依赖
- [ ] 4. 配置环境变量
- [ ] 5. 初始化系统
- [ ] 6. 启动核心服务
- [ ] 7. 验证安装

---

## 🚀 快速开始（5分钟）

### 1. 环境要求

- **Python**: 3.12 或更高
- **操作系统**: Windows 11 / macOS / Linux
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 2GB 可用空间

### 2. 安装步骤

```bash
# 克隆仓库
git clone https://github.com/your-repo/aios.git
cd aios

# 安装依赖
pip install -r requirements.txt

# 初始化系统
python -m aios.init

# 启动核心服务
python -m aios.start
```

### 3. 验证安装

```bash
# 运行健康检查
python -m aios.healthcheck

# 预期输出：
# ✅ EventBus: OK
# ✅ Scheduler: OK
# ✅ Reactor: OK
# ✅ ScoreEngine: OK
# ✅ AIOS is ready!
```

---

## 📦 详细安装步骤

### Step 1: 安装 Python 3.12+

**Windows:**
```bash
# 下载并安装 Python 3.12
# https://www.python.org/downloads/

# 验证安装
python --version
# 输出: Python 3.12.x
```

**macOS:**
```bash
# 使用 Homebrew
brew install python@3.12

# 验证安装
python3 --version
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv

# 验证安装
python3.12 --version
```

---

### Step 2: 克隆仓库

```bash
# HTTPS
git clone https://github.com/your-repo/aios.git

# 或 SSH
git clone git@github.com:your-repo/aios.git

# 进入目录
cd aios
```

---

### Step 3: 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

**依赖列表（requirements.txt）:**
```
psutil>=5.9.0
pydantic>=2.0.0
```

---

### Step 4: 配置环境变量

创建 `.env` 文件：

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
nano .env  # 或使用你喜欢的编辑器
```

**必需配置：**
```env
# AIOS 工作目录
AIOS_WORKSPACE=C:\Users\A\.openclaw\workspace

# 日志级别
AIOS_LOG_LEVEL=INFO

# 心跳间隔（秒）
AIOS_HEARTBEAT_INTERVAL=30
```

**可选配置：**
```env
# Telegram 通知（可选）
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# OpenAI API（可选）
OPENAI_API_KEY=your_api_key
```

---

### Step 5: 初始化系统

```bash
# 运行初始化脚本
python -m aios.init

# 这会创建：
# - aios/data/events/        # 事件存储
# - aios/agent_system/data/  # Agent 数据
# - memory/                  # 记忆文件
# - aios/orchestrator.log    # 日志文件
```

---

### Step 6: 启动核心服务

```bash
# 启动 AIOS
python -m aios.start

# 预期输出：
# [AIOS] 预热组件中...
# [Scheduler] 🚀 启动（最大并发: 5）
# [Reactor] 加载了 18 个 playbook
# [ScoreEngine] 启动中...
# [AIOS] ✅ 组件预热完成 (1ms)
```

---

### Step 7: 验证安装

```bash
# 运行健康检查
python -m aios.healthcheck

# 检查 Agent 状态
python aios/agent_system/check_agent_status.py

# 查看 Dashboard
# 打开浏览器访问: http://localhost:8080
```

---

## 🎯 核心组件说明

### 1. EventBus（事件总线）
- **作用**: 系统心脏，所有事件通过这里流转
- **配置**: 无需配置，自动启动
- **验证**: 检查 `aios/data/events/` 目录

### 2. Scheduler（任务调度）
- **作用**: 决策大脑，管理任务优先级和执行
- **配置**: `aios/agent_system/data/agent_configs.json`
- **验证**: 检查 `aios/agent_system/task_queue.jsonl`

### 3. Reactor（自动修复）
- **作用**: 免疫系统，自动响应错误和异常
- **配置**: `aios/reactor/playbooks/`
- **验证**: 触发一个错误，看是否自动修复

### 4. ScoreEngine（评分引擎）
- **作用**: 体检报告，实时计算系统健康度
- **配置**: 无需配置
- **验证**: 查看 Evolution Score

### 5. Agent System（Agent 管理）
- **作用**: 执行层，管理所有 AI Agent
- **配置**: `aios/agent_system/data/agent_configs.json`
- **验证**: 运行 `check_agent_status.py`

---

## 🔧 常见问题

### Q1: Python 版本不对怎么办？
```bash
# 检查版本
python --version

# 如果低于 3.12，请升级
# Windows: 重新下载安装
# macOS: brew upgrade python
# Linux: apt install python3.12
```

### Q2: 依赖安装失败？
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像（中国用户）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q3: 启动失败？
```bash
# 检查日志
cat aios/orchestrator.log

# 检查端口占用
# Windows:
netstat -ano | findstr :8080
# macOS/Linux:
lsof -i :8080
```

### Q4: Agent 创建失败？
```bash
# 检查配置
cat aios/agent_system/data/agent_configs.json

# 检查日志
cat aios/agent_system/dispatcher.log
```

---

## 🎨 可选组件

### Dashboard（可视化）
```bash
# 启动 Dashboard
python aios/dashboard/app.py

# 访问: http://localhost:8080
```

### Telegram 通知
```bash
# 配置 .env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# 测试通知
python -m aios.test_telegram
```

### 插件系统
```bash
# 查看已安装插件
python -m aios.plugins list

# 安装插件
python -m aios.plugins install <plugin_name>
```

---

## 📚 下一步

安装完成后，你可以：

1. **阅读文档**: [README.md](README.md)
2. **查看示例**: [examples/](examples/)
3. **配置 Agent**: [AGENT_CONFIG.md](AGENT_CONFIG.md)
4. **加入社区**: [Discord](https://discord.gg/aios)

---

## 🆘 获取帮助

- **文档**: https://aios.readthedocs.io
- **GitHub Issues**: https://github.com/your-repo/aios/issues
- **Discord**: https://discord.gg/aios
- **Email**: support@aios.dev

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)
