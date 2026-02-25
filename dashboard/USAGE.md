# AIOS Dashboard 使用文档

## 快速开始

### 访问 Dashboard
浏览器打开：http://localhost:9091

### 开机自启
已配置自动启动，重启电脑后自动运行。

### 手动控制
- **启动**：双击 `C:\Users\A\.openclaw\workspace\aios\dashboard\start_dashboard.bat`
- **停止**：双击 `C:\Users\A\.openclaw\workspace\aios\dashboard\stop_dashboard.bat`

---

## 功能说明

### 1. 系统健康
显示最近 1 小时的系统状态：
- **事件数**：所有事件总数
- **错误数**：ERROR 级别事件
- **警告数**：WARN 级别事件
- **状态徽章**：
  - 🟢 健康：0 错误
  - 🟡 警告：1-10 错误
  - 🔴 严重：>10 错误
  - ⚫ 离线：无法连接

### 2. 智能体状态
- **总数**：所有 Agent 数量（包括已归档）
- **活跃**：最近 1 小时有活动的 Agent

### 3. 告警监控
- **待处理**：OPEN 状态的告警
- **已确认**：ACK 状态的告警
- **手动触发按钮**：
  - **运行流水线**：手动触发 AIOS Pipeline（sensors → alerts → reactor → verifier）
  - **处理队列**：手动触发 Agent 任务队列处理

### 4. 待办任务
显示 `pending_actions.jsonl` 队列大小。

### 5. 告警详情
显示最近 10 条告警的详细信息：
- **规则名称**：触发告警的规则
- **状态**：待处理 / 已确认 / 已解决
- **消息**：告警详情
- **操作按钮**：
  - **确认**：将 OPEN 状态改为 ACK（已确认但未解决）
  - **解决**：将 OPEN/ACK 状态改为 RESOLVED（已解决）

### 6. 事件流
实时滚动显示最近 30 条事件：
- **时间戳**：事件发生时间
- **层级标签**：KERNEL / COMMS / TOOL / MEM / SEC
- **消息内容**：事件详情
- **颜色标识**：
  - 🔵 INFO：蓝色
  - 🟡 WARN：橙色
  - 🔴 ERROR：红色

---

## 实时更新机制

### WebSocket 模式（优先）
- 连接成功后每 5 秒推送一次更新
- 状态指示器显示 🟢 已连接
- 低延迟，实时性好

### HTTP 轮询模式（降级）
- WebSocket 断开时自动切换
- 每 10 秒拉取一次数据
- 状态指示器显示 🔴 已断开
- 自动尝试重连（5 秒间隔）

---

## 操作流程

### 处理告警
1. 在"告警详情"区域查看告警信息
2. 点击"确认"按钮 → 告警状态变为"已确认"
3. 处理完问题后，点击"解决"按钮 → 告警状态变为"已解决"
4. 页面自动刷新，显示最新状态

### 手动触发任务
1. 点击"运行流水线"或"处理队列"按钮
2. 等待 Toast 提示（右上角弹窗）
3. 成功：显示绿色提示 + 自动刷新数据
4. 失败：显示红色提示 + 错误信息

---

## 数据来源

Dashboard 从以下 JSONL 文件读取数据：
- `C:\Users\A\.openclaw\workspace\aios\events.jsonl` - 事件日志
- `C:\Users\A\.openclaw\workspace\aios\agent_system\agents.jsonl` - Agent 状态
- `C:\Users\A\.openclaw\workspace\aios\pending_actions.jsonl` - 待办队列
- `C:\Users\A\.openclaw\workspace\aios\alert_fsm.jsonl` - 告警状态

所有操作（确认/解决告警）会直接修改对应的 JSONL 文件。

---

## 故障排查

### Dashboard 无法访问
1. 检查服务器是否运行：
   ```powershell
   netstat -ano | findstr :9091
   ```
2. 如果没有输出，手动启动：
   ```
   C:\Users\A\.openclaw\workspace\aios\dashboard\start_dashboard.bat
   ```

### WebSocket 连接失败
1. 刷新浏览器（Ctrl+F5 强制刷新）
2. 清除浏览器缓存
3. 检查防火墙是否阻止 localhost 连接

### 数据不更新
1. 检查 JSONL 文件是否存在
2. 检查文件权限（是否可读）
3. 查看浏览器控制台（F12）是否有错误

### 端口被占用
如果 9091 端口被占用：
1. 找到占用进程：
   ```powershell
   netstat -ano | findstr :9091
   ```
2. 关闭进程：
   ```powershell
   taskkill /F /PID <进程ID>
   ```

---

## 技术细节

### 架构
```
浏览器 (WebSocket) ←→ FastAPI 服务器 ←→ JSONL 文件
         ↓ (降级)
    HTTP 轮询 (10秒)
```

### API 端点
- `GET /` - Dashboard UI
- `GET /api/snapshot` - 完整数据快照（HTTP 轮询用）
- `WebSocket /ws` - 实时推送
- `POST /api/alerts/{id}/ack` - 确认告警
- `POST /api/alerts/{id}/resolve` - 解决告警
- `POST /api/trigger/pipeline` - 触发 AIOS Pipeline
- `POST /api/trigger/agent_queue` - 触发 Agent 队列

### 技术栈
- 后端：FastAPI + WebSocket + uvicorn
- 前端：原生 HTML/CSS/JS（无依赖）
- 数据：JSONL 文件（纯文本，易于调试）

---

## 安全说明

- Dashboard 仅监听 `127.0.0.1`（本地回环），外部网络无法访问
- 没有身份验证机制（仅限本机使用）
- 所有操作直接修改本地文件，无需担心远程攻击

---

## 未来扩展

当前版本（v2.0）已实现核心功能，后续可选扩展：
- Agent 创建/删除控制
- 历史趋势图表（Chart.js）
- 配置参数调整界面
- 日志搜索和过滤
- 导出报告功能

---

## 联系支持

如有问题，联系小九（Telegram: @shh7799）
