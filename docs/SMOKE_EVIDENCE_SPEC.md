# SMOKE EVIDENCE SPEC v1

## 1. 目的

smoke evidence 的目标是让接收方在 30 秒内完成：
- 快速验收（通过 / 失败 / 证据不完整）
- 失败归因（top_reason_code）
- 复跑指导（next_action）
- 可追溯（evidence_path 与 zip_filename 可定位）

本规范约束的是“证据格式与最小可用信息”，不约束具体实现语言（PowerShell/Bash/Python 均可）。

重要规则：
- INCONCLUSIVE 视为未通过验收，必须补证据或重跑。

---

## 2. 必含字段（最低要求）

每次 smoke 执行结束后，必须在 evidence 中产出以下字段，且随 zip 一起打包。

### 2.1 机器字段名（规范口径，建议用于 JSON / 解析）
- verdict：PASS | FAIL | INCONCLUSIVE
- top_reason_code：见第 3 节标准表；PASS 时必须为 NONE
- next_action：一行最短复跑动作；PASS 时推荐 NONE
- terminal_state：completed | failed | inconclusive
- evidence_path：本次证据目录（推荐相对 zip 根目录）
- zip_filename：统一命名为 smoke_evidence_<ts>.zip（不改名）

### 2.2 文本展示名（smoke_summary.txt 中使用）
- Verdict / Top reason_code / Next action
- terminal_state / evidence_path / zip_filename（建议与机器字段名一致）

### 2.3 对应关系（建议）
- PASS → terminal_state=completed
- FAIL → terminal_state=failed
- INCONCLUSIVE → terminal_state=inconclusive

若证据缺失导致无法判断，一律判为：
- verdict=INCONCLUSIVE
- top_reason_code=EVIDENCE_MISSING

---

## 3. reason_code 标准表（v1）

| top_reason_code | 触发信号（示例关键词） | 解释 | next_action（示例） |
|---|---|---|---|
| NONE | PASS | 通过 | NONE |
| EVIDENCE_MISSING | 缺少日志/结果/关键产物任一类 | 证据不完整，无法验收 | 同分支重跑并回传 zip + 终端截图 |
| INSTALL_SCRIPT_FAIL | install.ps1 / install_macos.sh 失败 | 安装阶段失败 | 重新运行安装脚本后再 smoke |
| DEPENDENCY_MISSING | ModuleNotFoundError / pip install fail | 依赖缺失或安装失败 | 重新 install 依赖后重跑 smoke |
| PYTHON_VERSION_MISMATCH | Python version unsupported | Python 版本不符合要求 | 切换到指定 Python 版本后重跑 |
| PATH_HARDCODED | 出现 C:\ / /Users/ 写死路径 | 跨平台路径硬编码 | 发回文件名+行号，修复后重跑 |
| PERMISSION_DENIED | Permission denied / ExecutionPolicy | 权限不足或策略限制 | 提权/放宽策略后重跑 |
| NETWORK_TIMEOUT | timeout / TLS / connection reset | 网络受限或超时 | 反馈网络限制或改用 fallback 后重跑 |
| SERVICE_NOT_RUNNING | Connection refused / port not listening | 依赖服务未启动 | 启动服务/确认端口后重跑 |

---

## 4. 建议输出文件（随 zip 打包）

smoke 必须额外输出一个“单文件摘要”，用于 30 秒验收落槌。二选一：

### 4.1 smoke_summary.txt（推荐）
- 位置：随 zip 打包（建议放在 regression\evidence 下）
- 固定 6 行键值对（顺序固定）

Verdict: PASS
Top reason_code: NONE
Next action: NONE
terminal_state: completed
zip_filename: smoke_evidence_20260322_153012.zip
evidence_path: regression\evidence

### 4.2 smoke_result.json（可选）
- 位置：zip 根目录
- 字段必须使用 snake_case，值域遵守本规范

---

## 附：接收方 30 秒验收回执格式（建议统一）

Verdict: PASS|FAIL|INCONCLUSIVE
Top reason_code: <xxx>
Next action: <one-line>