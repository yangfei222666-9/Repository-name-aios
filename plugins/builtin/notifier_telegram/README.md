# Telegram Notifier Plugin

Telegram 通知插件，自动发送 AIOS 告警到 Telegram。

## 功能

- 自动监听错误和告警事件
- 支持 Markdown 格式
- 速率限制（防止刷屏）
- 级别过滤（只发送重要通知）

## 配置

### 1. 创建 Telegram Bot

1. 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新 Bot
3. 按提示设置 Bot 名称
4. 获取 Bot Token（类似：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2. 获取 Chat ID

**方法1：使用 @userinfobot**
1. 在 Telegram 中找到 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息
3. 获取你的 Chat ID（数字）

**方法2：使用 API**
1. 先给你的 Bot 发送一条消息
2. 访问：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. 在返回的 JSON 中找到 `chat.id`

### 3. 配置插件

编辑 `config.yaml`：

```yaml
enabled: true
bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
chat_id: "7986452220"
min_severity: warn
rate_limit: 5
```

## 使用

### 加载插件

```bash
python __main__.py plugin load builtin/notifier_telegram
```

### 测试发送

```python
from plugins.manager import get_manager

manager = get_manager()
manager.load("builtin/notifier_telegram")

notifier = manager.get("builtin/notifier_telegram")
notifier.send("测试通知", "warn")
```

### 自动通知

插件会自动监听以下事件：
- `event.*error*` - 所有错误事件
- `event.*failed*` - 所有失败事件
- `alert.*` - 所有告警事件

当事件发生时，自动发送到 Telegram。

## 通知格式

```
⚠️ [WARN] 事件: provider.error
错误: Rate limit exceeded
Provider: openai
```

## 级别说明

| 级别 | 图标 | 说明 |
|------|------|------|
| info | ℹ️ | 信息 |
| warn | ⚠️ | 警告 |
| error | ❌ | 错误 |
| critical | 🚨 | 严重错误 |

## 速率限制

默认每 5 秒最多发送一次通知，防止刷屏。

可以在 `config.yaml` 中调整：

```yaml
rate_limit: 10  # 改为 10 秒
```

## 健康检查

```bash
python __main__.py plugin health builtin/notifier_telegram
```

## 故障排查

### 1. 发送失败

**检查：**
- Bot Token 是否正确
- Chat ID 是否正确
- 是否给 Bot 发送过消息（Bot 需要先收到消息才能主动发送）

### 2. 收不到通知

**检查：**
- 插件是否已加载
- 事件级别是否达到 `min_severity`
- 是否触发了速率限制

### 3. 连接超时

**检查：**
- 网络连接是否正常
- Telegram API 是否可访问

## 示例

### 发送自定义通知

```python
from plugins.manager import get_manager
from plugins.eventbus import get_bus

manager = get_manager()
bus = get_bus()

# 加载插件
manager.load("builtin/notifier_telegram")

# 发布告警事件
bus.publish("alert.high_cpu", {
    "message": "CPU 使用率过高: 95%",
    "severity": "warn"
})
# → 自动发送到 Telegram
```

### 发送错误通知

```python
bus.publish("event.provider.error", {
    "provider": "openai",
    "error": "Rate limit exceeded",
    "severity": "error",
    "data": {
        "error": "Rate limit exceeded",
        "provider": "openai"
    }
})
# → 自动发送到 Telegram
```

## 注意事项

1. **保护 Bot Token** - 不要泄露到公开仓库
2. **速率限制** - Telegram API 有速率限制，不要发送太频繁
3. **消息长度** - 单条消息最长 4096 字符

---

**提示：** 配置完成后，运行 `python -X utf8 demo_quick.py` 测试通知功能。
