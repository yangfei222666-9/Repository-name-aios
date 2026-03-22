# TaijiOS 密钥轮换流程

## 轮换触发条件

- 定期轮换：每 90 天
- 紧急轮换：疑似泄露、人员变动、CI 日志误打印
- 验收轮换：第二阶段演练要求

---

## 轮换步骤

### 1. Telegram Bot Token

```powershell
# 1. 通过 @BotFather 生成新 token
# 2. 注入新 token
$env:TAIJI_TELEGRAM_BOT_TOKEN = "new_token"

# 3. 验证
python aios/agent_system/telegram_notifier.py send \
  --title "Token 轮换验证" --level info --reason-code token_rotation_test

# 4. 确认 audit.jsonl 有 op_result=success 记录
# 5. 废弃旧 token（在 @BotFather revoke）
```

### 2. TaijiOS API Token

```powershell
# 1. 生成新 token（32字节随机）
$newToken = [System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Max 256 }))

# 2. 更新环境变量
$env:TAIJIOS_API_TOKEN = $newToken

# 3. 验证
python aios/aios.py submit --desc "token rotation test" --token $newToken

# 4. 确认 audit.jsonl 有 authorized 记录
# 5. 更新 auth.json（本地，不入库）
```

### 3. OpenClaw / Anthropic API Key

```powershell
# 1. 在 Anthropic Console 生成新 key
# 2. 注入
$env:OPENCLAW_API_KEY = "new_key"
$env:ANTHROPIC_API_KEY = "new_key"

# 3. 验证（smoke test）
python aios/agent_system/scripts/validate_config.py --env prod

# 4. 废弃旧 key（在 Console revoke）
```

---

## 轮换验证

每次轮换后必须验证：

```powershell
# 检查所有 secret 状态
python aios/agent_system/secret_manager.py check

# 配置校验
python aios/agent_system/scripts/validate_config.py --strict

# secret scan（确认无明文）
python aios/agent_system/scripts/secret_scan.py --gate
```

---

## 禁止事项

- 禁止在 git commit / PR / issue 中出现明文 secret
- 禁止在日志、runlog、audit.jsonl 中打印完整 secret（只允许前4位+***）
- 禁止多环境共用同一个 Telegram chat_id
- 禁止轮换后不验证直接上 prod

---

## 紧急泄露处理

1. 立即 revoke 泄露的 secret
2. 按上述步骤生成并注入新 secret
3. 检查 audit.jsonl 确认泄露期间无异常调用
4. 在 audit.jsonl 手动追加一条事件记录：
   ```json
   {"ts": "...", "action": "secret.emergency_rotation", "reason": "suspected_leak", "secret": "token_name"}
   ```
