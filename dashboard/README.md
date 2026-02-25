# AIOS Dashboard

实时监控 AIOS 系统状态的 Web 界面。

## 功能

- **系统健康**：最近 1 小时的事件/错误/警告统计
- **Agent 状态**：总数、活跃数、最近任务
- **告警监控**：OPEN/ACK 状态告警
- **待办队列**：pending_actions.jsonl 队列大小
- **事件流**：实时滚动显示最近事件

## 技术栈

- **后端**：FastAPI + WebSocket
- **前端**：原生 HTML/CSS/JS（无依赖）
- **数据源**：复用现有 JSONL 文件
- **端口**：9091

## 启动

```bash
# 安装依赖
pip install fastapi uvicorn websockets

# 启动服务器
cd C:\Users\A\.openclaw\workspace\aios\dashboard
python server.py

# 浏览器访问
http://localhost:9091
```

## 架构

```
┌─────────────┐
│  Browser    │
│  (index.html)│
└──────┬──────┘
       │ WebSocket (实时) / HTTP (降级)
       ↓
┌─────────────┐
│  FastAPI    │
│  (server.py)│
└──────┬──────┘
       │ 读取
       ↓
┌─────────────────────────────┐
│ events.jsonl                │
│ agents.jsonl                │
│ pending_actions.jsonl       │
│ alert_fsm.jsonl             │
└─────────────────────────────┘
```

## WebSocket 协议

**客户端连接后立即收到 snapshot：**
```json
{
  "type": "snapshot",
  "data": {
    "health": {...},
    "agents": {...},
    "actions": [...],
    "alerts": {...},
    "events": [...]
  }
}
```

**之后每 5 秒收到 update：**
```json
{
  "type": "update",
  "data": { ... }
}
```

**WebSocket 断开时自动降级到 HTTP 轮询（10 秒间隔）**

## 优雅降级

1. 优先使用 WebSocket（低延迟、实时推送）
2. WebSocket 失败时自动切换到 HTTP 轮询
3. 断线后自动重连（5 秒间隔）

## 数据刷新

- **WebSocket 模式**：5 秒推送一次
- **HTTP 轮询模式**：10 秒拉取一次
- **事件流**：最近 30 条（snapshot）/ 10 条（update）

## 状态定义

- **healthy**：最近 1 小时错误数 = 0
- **warning**：最近 1 小时错误数 1-10
- **critical**：最近 1 小时错误数 > 10
- **offline**：无法连接

## 扩展

后续可以加：
- 手动触发任务按钮
- 告警确认/关闭操作
- Agent 创建/删除控制
- 策略参数调整界面
- 历史趋势图表（Chart.js）
