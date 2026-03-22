# TaijiOS 回滚策略

## 回滚对象

| 对象 | 说明 |
|------|------|
| 代码版本 | git commit / tag |
| 配置版本 | `aios/config/{env}.yaml`，与代码成对回退 |
| 关键脚本 | `agent_system/scripts/`，随代码回退 |

代码和配置**必须成对回退**，禁止只回代码不回配置。

---

## 回滚锚点

上一个通过 `prod-gate` 的 commit，识别方式：

1. commit message 含 `[green]` 或 `[prod-gate]`
2. GitHub Actions `prod-gate` job 绿灯的 commit hash
3. 都找不到时 fallback 到 `HEAD~1`

---

## 触发条件

以下任一情况触发回滚：

- `hourly_s1` 连续 2 轮失败
- 告警链路静默（5 分钟内无响应）
- `/api/system/health` 返回非 200
- 配置校验失败（`validate_config.py --strict` 非零）
- 人工判断当前版本不可用

---

## 执行步骤

### 快速回滚（≤15 分钟目标）

```powershell
# 1. 确认当前状态
git log --oneline -5

# 2. 执行回滚（dry-run 先确认）
.\aios\agent_system\scripts\rollback.ps1 -Env prod -DryRun

# 3. 确认无误后执行
.\aios\agent_system\scripts\rollback.ps1 -Env prod

# 4. 验证
# 查看证据
cat aios\agent_system\data\prod\reports\rollback_latest.json
# 健康检查
curl http://localhost:9092/api/system/health
```

### 指定版本回滚

```powershell
.\aios\agent_system\scripts\rollback.ps1 -TargetCommit abc1234 -Env prod
```

### staging 演练

```powershell
.\aios\agent_system\scripts\rollback.ps1 -Env staging -DryRun
.\aios\agent_system\scripts\rollback.ps1 -Env staging
```

---

## 回滚成功判定

全部满足才算成功：

- [ ] `rollback_latest.json` 中 `result.pass = true`
- [ ] `validate_config.py --env prod` 返回 0
- [ ] `/api/system/health` 返回 200（服务运行时）
- [ ] `audit.jsonl` 有 `rollback.complete` 记录

---

## 证据落盘

每次回滚（含 dry-run）都会生成：

```
aios/agent_system/data/{env}/reports/
  rollback_latest.json      # 最新回滚结果（覆盖）
  rollback_<timestamp>.json # 历史记录（永久保留）
  rollback_latest.md        # 可读摘要

aios/agent_system/data/{env}/audit.jsonl
  # rollback.start + rollback.complete 两条记录
```

---

## 演练流程

每次大版本变更前，在 staging 演练一次：

1. 执行 `rollback.ps1 -Env staging -DryRun`，确认计划正确
2. 执行 `rollback.ps1 -Env staging`，完成实际回滚
3. 验证 `rollback_latest.json` 中 `result.pass = true`
4. 记录演练时间、版本号、验证结果到 `rollback_latest.md`
5. 将 `rollback_latest.json` 作为演练证据归档

---

## 禁止事项

- 禁止只回代码不回配置
- 禁止在 prod 直接执行未经 dry-run 确认的回滚
- 禁止回滚到未通过 `validate_config.py` 的版本
- 禁止跳过健康检查直接宣布回滚成功
- 禁止删除历史 `rollback_<timestamp>.json` 文件

---

## 角色分工

| 角色 | 职责 |
|------|------|
| 操作者 | 执行 `rollback.ps1`，确认证据落盘 |
| 验证者 | 独立验证健康检查和告警链路 |
| 记录者 | 在 audit.jsonl 补充人工备注 |

单人运维时，操作者兼任所有角色，但必须按顺序完成每一步。
