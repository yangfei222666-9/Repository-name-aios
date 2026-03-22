# TaijiOS 配置变更规范

## 配置文件结构

```
aios/config/
  dev.yaml        # 开发环境（入库）
  staging.yaml    # 预发环境（入库）
  prod.yaml       # 生产环境（入库）

aios/agent_system/config/
  notify.example.json   # 通知配置示例（入库）
  auth.example.json     # 鉴权配置示例（入库）
  notify.json           # 通知配置实例（不入库）
  auth.json             # 鉴权配置实例（不入库）
```

---

## 字段分类

### 可直接修改（改完提交即生效）

| 字段类型 | 示例 | 说明 |
|----------|------|------|
| 超时/重试参数 | `agents.timeouts.coder` | 调整后下次启动生效 |
| 功能开关 | `features.auto_recovery` | 布尔值，true/false |
| 阈值参数 | `monitoring.alert_threshold.*` | 数值类 |
| 模型选择 | `models.default` | 字符串，模型 ID |
| 调度参数 | `cron.*.schedule` | cron 表达式 |

### 必须走环境变量（禁止明文入库）

| 字段 | 对应环境变量 |
|------|-------------|
| Telegram Bot Token | `TAIJI_TELEGRAM_BOT_TOKEN` |
| Telegram Chat ID (prod) | `TAIJI_TELEGRAM_CHAT_ID` |
| Telegram Chat ID (staging) | `TAIJI_STAGING_TELEGRAM_CHAT_ID` |
| Telegram Chat ID (dev) | `TAIJI_DEV_TELEGRAM_CHAT_ID` |
| API Token | `TAIJIOS_API_TOKEN` |
| OpenClaw API Key | `OPENCLAW_API_KEY` |

yaml 文件中只保留 `*_env` 引用字段名，不保留明文值。

### 需要演练/审批后才能改

| 字段 | 原因 |
|------|------|
| `notifications.telegram.chat_id_env` | 改错会导致告警发到错误群 |
| `self_improving.auto_apply` | 改为 true 会触发自动代码修改 |
| `queue.max_pending` | 影响任务积压上限 |
| `storage.path` | 改路径会导致历史数据不可访问 |
| 任何 prod 环境的 `*_env` 字段 | 影响生产鉴权/通知链路 |

---

## 变更流程

### 普通参数变更
1. 修改对应环境的 yaml 文件
2. 运行校验：`python scripts/validate_config.py --env <env>`
3. 提交，commit message 格式：`config(<env>): <变更描述>`
4. 示例：`config(prod): 调整 coder 超时从 180s 到 240s`

### 敏感配置变更（token/chat_id）
1. 只修改服务器环境变量，不改 yaml
2. 重启相关服务使新值生效
3. 在 audit.jsonl 手动记录变更时间和原因

### 跨环境结构变更（新增/删除字段）
1. 三个环境 yaml 同步修改
2. 更新 `validate_config.py` 的校验规则
3. 运行全量校验：`python scripts/validate_config.py --strict`
4. 提交前确认 diff 合理

---

## 校验命令

```bash
# 校验所有环境
python aios/agent_system/scripts/validate_config.py

# 只校验 prod
python aios/agent_system/scripts/validate_config.py --env prod

# 严格模式（警告也算失败，CI 用）
python aios/agent_system/scripts/validate_config.py --strict
```

退出码：
- `0` = 全部通过
- `1` = 有错误
- `2` = 有警告（仅 --strict 模式）

---

## 禁止事项

- 禁止在 yaml 文件中写明文 token、密码、chat_id
- 禁止三个环境共用同一个 `chat_id_env`（会导致告警串群）
- 禁止跳过校验直接修改 prod 配置
- 禁止在 notify.json / auth.json 中写真实密钥后提交 git
