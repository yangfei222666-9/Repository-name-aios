# AIOS 安装清单

> 按顺序完成，确保每一步都成功 ✅

---

## 📋 第一步：环境准备

- [ ] Python 3.12+ 已安装
  ```bash
  python --version
  # 预期: Python 3.12.x
  ```

- [ ] Git 已安装
  ```bash
  git --version
  # 预期: git version 2.x
  ```

- [ ] 至少 4GB RAM 可用
- [ ] 至少 2GB 磁盘空间

---

## 📦 第二步：安装 AIOS

- [ ] 克隆仓库
  ```bash
  git clone https://github.com/your-repo/aios.git
  cd aios
  ```

- [ ] 创建虚拟环境（推荐）
  ```bash
  python -m venv venv
  # Windows: venv\Scripts\activate
  # macOS/Linux: source venv/bin/activate
  ```

- [ ] 安装依赖
  ```bash
  pip install -r requirements.txt
  ```

---

## ⚙️ 第三步：配置系统

- [ ] 复制配置文件
  ```bash
  cp .env.example .env
  ```

- [ ] 编辑 `.env`，设置工作目录
  ```env
  AIOS_WORKSPACE=/path/to/workspace
  ```

- [ ] 初始化系统
  ```bash
  python -m aios.init
  ```

---

## 🚀 第四步：启动核心服务

- [ ] 启动 AIOS
  ```bash
  python -m aios.start
  ```

- [ ] 验证输出
  ```
  [AIOS] 预热组件中...
  [Scheduler] 🚀 启动（最大并发: 5）
  [Reactor] 加载了 18 个 playbook
  [ScoreEngine] 启动中...
  [AIOS] ✅ 组件预热完成
  ```

---

## ✅ 第五步：验证安装

- [ ] 运行健康检查
  ```bash
  python -m aios.healthcheck
  ```

- [ ] 检查 Agent 状态
  ```bash
  python aios/agent_system/check_agent_status.py
  ```

- [ ] 查看 Dashboard（可选）
  ```bash
  python aios/dashboard/app.py
  # 访问: http://localhost:8080
  ```

---

## 🎯 第六步：配置 Agent（可选）

- [ ] 编辑 Agent 配置
  ```bash
  nano aios/agent_system/data/agent_configs.json
  ```

- [ ] 添加角色信息
  ```json
  {
    "agent_coder_001": {
      "type": "coder",
      "role": "Senior Python Developer",
      "goal": "Write clean, maintainable code",
      "backstory": "10+ years experience..."
    }
  }
  ```

---

## 📱 第七步：配置交互入口（可选）

### Telegram
- [ ] 创建 Telegram Bot（@BotFather）
- [ ] 获取 Bot Token
- [ ] 配置 `.env`
  ```env
  TELEGRAM_BOT_TOKEN=your_token
  TELEGRAM_CHAT_ID=your_chat_id
  ```

### Web UI
- [ ] 启动 Dashboard
  ```bash
  python aios/dashboard/app.py
  ```

---

## 🔌 第八步：安装插件（可选）

- [ ] 查看可用插件
  ```bash
  python -m aios.plugins list
  ```

- [ ] 安装插件
  ```bash
  python -m aios.plugins install <plugin_name>
  ```

---

## 🎉 完成！

恭喜！AIOS 已成功安装。

### 下一步：

1. **阅读文档**: [README.md](README.md)
2. **查看示例**: [examples/](examples/)
3. **创建第一个任务**:
   ```python
   from aios.agent_system.auto_dispatcher import AutoDispatcher
   
   dispatcher = AutoDispatcher(Path.cwd())
   dispatcher.enqueue_task({
       "type": "code",
       "message": "写一个 Hello World",
       "priority": "high"
   })
   ```

---

## 🆘 遇到问题？

- **查看日志**: `aios/orchestrator.log`
- **GitHub Issues**: https://github.com/your-repo/aios/issues
- **Discord**: https://discord.gg/aios

---

**✅ 所有步骤完成后，你就可以开始使用 AIOS 了！**
