# TaijiOS Secret Inventory

最后更新：2026-03-19

## Secret 清单

| Secret 名称 | 环境变量 | 使用模块 | 当前来源 | 目标来源 | 迁移状态 |
|-------------|----------|----------|----------|----------|----------|
| Telegram Bot Token | `TAIJI_TELEGRAM_BOT_TOKEN` | `telegram_notifier.py`, `site_monitor.py`, `debate_policy_engine.py` | 环境变量 | 环境变量 | ✅ 已完成 |
| Telegram Chat ID (prod) | `TAIJI_TELEGRAM_CHAT_ID` | `telegram_notifier.py`, `api_monitor.py` | 环境变量（`api_monitor.py` 已修复明文） | 环境变量 | ✅ 已完成 |
| Telegram Chat ID (staging) | `TAIJI_STAGING_TELEGRAM_CHAT_ID` | `telegram_notifier.py` | 环境变量 | 环境变量 | ✅ 已完成 |
| Telegram Chat ID (dev) | `TAIJI_DEV_TELEGRAM_CHAT_ID` | `telegram_notifier.py` | 环境变量 | 环境变量 | ✅ 已完成 |
| TaijiOS API Token | `TAIJIOS_API_TOKEN` | `auth.py`, `aios.py`, `task_submitter.py`, `runtime_v2/cli.py` | 环境变量 / `auth.json`（不入库） | 环境变量 | ✅ 已完成 |
| OpenClaw API Key | `OPENCLAW_API_KEY` | `prod.yaml` → 模型调用 | 环境变量 | 环境变量 | ✅ 已完成 |
| Anthropic API Key | `ANTHROPIC_API_KEY` | `real_coder.py` | 环境变量 | 环境变量 | ✅ 已完成 |
| OpenAI API Key | `OPENAI_API_KEY` | `diary_llm_enhancer.py`, `embedding_generator.py` | 环境变量 | 环境变量 | ✅ 已完成 |

## 已修复的明文 Secret

| 文件 | 问题 | 修复方式 |
|------|------|----------|
| `api_monitor.py:16` | `TELEGRAM_CHAT_ID = "7986452220"` 硬编码 | 改为 `os.environ.get("TAIJI_TELEGRAM_CHAT_ID")` |

## 不一致的环境变量名（待统一）

以下模块使用旧命名，功能正常但不符合统一规范：

| 模块 | 当前变量名 | 规范变量名 |
|------|-----------|-----------|
| `site_monitor.py` | `TG_BOT_TOKEN`, `TG_CHAT_ID` | `TAIJI_TELEGRAM_BOT_TOKEN`, `TAIJI_TELEGRAM_CHAT_ID` |
| `debate_policy_engine.py` | `TELEGRAM_BOT_TOKEN` | `TAIJI_TELEGRAM_BOT_TOKEN` |

`secret_manager.get_telegram_bot_token()` 已做兼容处理，两种命名均可读取。

## 注入方式

### 本地开发
```powershell
$env:TAIJI_ENV = "dev"
$env:TAIJI_TELEGRAM_BOT_TOKEN = "your_token"
$env:TAIJI_DEV_TELEGRAM_CHAT_ID = "your_dev_chat_id"
$env:TAIJIOS_API_TOKEN = "your_api_token"
$env:OPENCLAW_API_KEY = "your_api_key"
```

### CI（GitHub Actions）
在 repo Settings → Secrets and variables → Actions 中设置：
- `TAIJI_TELEGRAM_BOT_TOKEN`
- `TAIJI_TELEGRAM_CHAT_ID`
- `TAIJIOS_API_TOKEN`
- `OPENCLAW_API_KEY`

### 生产主机
写入系统环境变量或 `.env` 文件（不入库），通过 Task Scheduler 启动时注入。
