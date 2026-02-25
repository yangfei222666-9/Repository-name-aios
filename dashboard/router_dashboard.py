#!/usr/bin/env python3
"""
AIOS Dashboard - 决策卡片展示
实时显示 Router 的每次决策
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from pathlib import Path
from datetime import datetime
import uvicorn

app = FastAPI()

# 读取决策日志
def get_recent_decisions(limit: int = 20):
    """获取最近的决策记录"""
    decisions_file = Path("aios/data/router_decisions.jsonl")
    
    if not decisions_file.exists():
        return []
    
    decisions = []
    with open(decisions_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[-limit:]:
            try:
                decisions.append(json.loads(line))
            except:
                pass
    
    return list(reversed(decisions))  # 最新的在前


@app.get("/")
async def get_dashboard():
    """Dashboard 主页"""
    html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIOS Router Dashboard - 决策卡片</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 28px;
            color: #2d3748;
            margin-bottom: 8px;
        }
        
        .header p {
            color: #718096;
            font-size: 14px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
        
        .stat-card h3 {
            font-size: 14px;
            color: #718096;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #2d3748;
        }
        
        .decisions {
            display: grid;
            gap: 16px;
        }
        
        .decision-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .decision-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
        
        .decision-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .decision-title {
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
        }
        
        .decision-time {
            font-size: 12px;
            color: #a0aec0;
        }
        
        .decision-body {
            display: grid;
            gap: 12px;
        }
        
        .decision-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .decision-label {
            font-size: 12px;
            font-weight: 600;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            min-width: 80px;
        }
        
        .decision-value {
            font-size: 14px;
            color: #2d3748;
            font-weight: 500;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge-agent {
            background: #667eea;
            color: white;
        }
        
        .badge-model {
            background: #48bb78;
            color: white;
        }
        
        .badge-thinking {
            background: #ed8936;
            color: white;
        }
        
        .badge-mode {
            background: #4299e1;
            color: white;
        }
        
        .confidence-bar {
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #38a169);
            transition: width 0.3s;
        }
        
        .reason-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 4px;
        }
        
        .reason-tag {
            padding: 4px 10px;
            background: #edf2f7;
            color: #4a5568;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .input-snapshot {
            background: #f7fafc;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            font-size: 12px;
            color: #4a5568;
            font-family: 'Courier New', monospace;
        }
        
        .input-snapshot-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: #2d3748;
        }
        
        .input-snapshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 8px;
        }
        
        .input-snapshot-item {
            display: flex;
            justify-content: space-between;
        }
        
        .input-snapshot-key {
            color: #718096;
        }
        
        .input-snapshot-value {
            font-weight: 600;
            color: #2d3748;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .decision-card.new {
            animation: slideIn 0.3s ease-out;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 AIOS Router Dashboard</h1>
            <p>实时决策监控 - 每次路由决策可见、可追溯</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>总决策数</h3>
                <div class="value" id="total-decisions">0</div>
            </div>
            <div class="stat-card">
                <h3>平均置信度</h3>
                <div class="value" id="avg-confidence">0.00</div>
            </div>
            <div class="stat-card">
                <h3>Opus 使用率</h3>
                <div class="value" id="opus-rate">0%</div>
            </div>
            <div class="stat-card">
                <h3>Sticky 命中率</h3>
                <div class="value" id="sticky-rate">0%</div>
            </div>
        </div>
        
        <div class="decisions" id="decisions-container">
            <!-- 决策卡片将动态插入这里 -->
        </div>
    </div>
    
    <script>
        // 加载决策数据
        async function loadDecisions() {
            try {
                const response = await fetch('/api/decisions');
                const decisions = await response.json();
                
                renderDecisions(decisions);
                updateStats(decisions);
            } catch (error) {
                console.error('加载决策失败:', error);
            }
        }
        
        function renderDecisions(decisions) {
            const container = document.getElementById('decisions-container');
            container.innerHTML = '';
            
            decisions.forEach(decision => {
                const card = createDecisionCard(decision);
                container.appendChild(card);
            });
        }
        
        function createDecisionCard(decision) {
            const card = document.createElement('div');
            card.className = 'decision-card';
            
            // 兼容新旧格式：新格式用 decision，旧格式用 plan
            const plan = decision.decision || decision.plan;
            const snapshot = plan.input_snapshot || {};
            const timestamp = new Date(decision.timestamp).toLocaleString('zh-CN');
            // 兼容字段名：新格式 agent，旧格式 agent_type
            const agentName = plan.agent || plan.agent_type || 'unknown';
            const thinkingLevel = plan.thinking || plan.thinking_level || 'off';
            const executionMode = plan.execution_mode || 'apply';
            const reasonCodes = plan.reason_codes || [];
            const confidence = plan.confidence || 0;
            
            card.innerHTML = `
                <div class="decision-header">
                    <div class="decision-title">任务 ${snapshot.task_id || '-'}</div>
                    <div class="decision-time">${timestamp}</div>
                </div>
                
                <div class="decision-body">
                    <div class="decision-row">
                        <div class="decision-label">决策</div>
                        <div class="decision-value">
                            <span class="badge badge-agent">${agentName}</span>
                            <span class="badge badge-model">${plan.model}</span>
                            <span class="badge badge-thinking">thinking=${thinkingLevel}</span>
                            <span class="badge badge-mode">${executionMode}</span>
                        </div>
                    </div>
                    
                    <div class="decision-row">
                        <div class="decision-label">原因</div>
                        <div class="reason-tags">
                            ${reasonCodes.map(code => `<span class="reason-tag">${code}</span>`).join('')}
                        </div>
                    </div>
                    
                    <div class="decision-row">
                        <div class="decision-label">置信度</div>
                        <div style="flex: 1;">
                            <div class="decision-value">${(confidence * 100).toFixed(0)}%</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${confidence * 100}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="input-snapshot">
                        <div class="input-snapshot-title">📊 输入快照</div>
                        <div class="input-snapshot-grid">
                            <div class="input-snapshot-item">
                                <span class="input-snapshot-key">任务类型:</span>
                                <span class="input-snapshot-value">${snapshot.task_type || '-'}</span>
                            </div>
                            <div class="input-snapshot-item">
                                <span class="input-snapshot-key">复杂度:</span>
                                <span class="input-snapshot-value">${snapshot.complexity || '-'}/10</span>
                            </div>
                            <div class="input-snapshot-item">
                                <span class="input-snapshot-key">风险:</span>
                                <span class="input-snapshot-value">${snapshot.risk_level || '-'}</span>
                            </div>
                            <div class="input-snapshot-item">
                                <span class="input-snapshot-key">错误率:</span>
                                <span class="input-snapshot-value">${((snapshot.error_rate || 0) * 100).toFixed(1)}%</span>
                            </div>
                            <div class="input-snapshot-item">
                                <span class="input-snapshot-key">性能下降:</span>
                                <span class="input-snapshot-value">${((snapshot.performance_drop || 0) * 100).toFixed(1)}%</span>
                            </div>
                            <div class="input-snapshot-item">
                                <span class="input-snapshot-key">CPU:</span>
                                <span class="input-snapshot-value">${((snapshot.cpu_usage || 0) * 100).toFixed(0)}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            return card;
        }
        
        function updateStats(decisions) {
            // 总决策数
            document.getElementById('total-decisions').textContent = decisions.length;
            
            // 平均置信度
            if (decisions.length > 0) {
                const avgConfidence = decisions.reduce((sum, d) => {
                    const plan = d.decision || d.plan || {};
                    return sum + (plan.confidence || 0);
                }, 0) / decisions.length;
                document.getElementById('avg-confidence').textContent = avgConfidence.toFixed(2);
            }
            
            // Opus 使用率
            const opusCount = decisions.filter(d => {
                const plan = d.decision || d.plan || {};
                return (plan.model || '').includes('opus');
            }).length;
            const opusRate = decisions.length > 0 ? (opusCount / decisions.length * 100).toFixed(0) : 0;
            document.getElementById('opus-rate').textContent = opusRate + '%';
            
            // Sticky 命中率
            const stickyCount = decisions.filter(d => {
                const plan = d.decision || d.plan || {};
                return (plan.reason_codes || []).includes('sticky_applied');
            }).length;
            const stickyRate = decisions.length > 0 ? (stickyCount / decisions.length * 100).toFixed(0) : 0;
            document.getElementById('sticky-rate').textContent = stickyRate + '%';
        }
        
        // 初始加载
        loadDecisions();
        
        // 每 5 秒刷新
        setInterval(loadDecisions, 5000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)


@app.get("/api/decisions")
async def get_decisions():
    """API: 获取决策列表"""
    decisions = get_recent_decisions(limit=20)
    return decisions


if __name__ == "__main__":
    print("=" * 80)
    print("🎯 AIOS Router Dashboard 启动中...")
    print("=" * 80)
    print("\n访问地址: http://localhost:9092")
    print("实时监控 Router 的每次决策\n")
    
    uvicorn.run(app, host="0.0.0.0", port=9092, log_level="info")
