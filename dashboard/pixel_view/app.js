// AIOS Pixel Agents - 主逻辑

class PixelAgents {
    constructor() {
        this.canvas = document.getElementById('office-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.agents = [];
        this.events = [];
        this.ws = null;
        this.sprites = {};
        
        this.init();
    }
    
    async init() {
        console.log('[PixelAgents] 初始化中...');
        
        // 加载数据
        await this.loadAgents();
        await this.loadEvents();
        
        // 绘制场景
        this.drawOffice();
        
        // 连接 WebSocket
        this.connectWebSocket();
        
        // 绑定事件
        this.bindEvents();
        
        // 开始动画循环
        this.animate();
        
        // 自动刷新（每 5 秒）
        setInterval(() => {
            this.loadAgents();
            this.loadEvents();
        }, 5000);
        
        console.log('[PixelAgents] 初始化完成');
    }
    
    async loadAgents() {
        try {
            // 从 AIOS Agent System 读取数据
            const response = await fetch('http://127.0.0.1:9093/api/agents/status');
            const data = await response.json();
            
            console.log('[PixelAgents] Agent 数据:', data);
            
            // 转换为 Pixel Agents 格式
            this.agents = this.convertAgentsData(data);
            
            // 更新侧边栏
            this.updateAgentsList();
            
            console.log(`[PixelAgents] 加载了 ${this.agents.length} 个 Agent`);
        } catch (error) {
            console.error('[PixelAgents] 加载 Agent 失败:', error);
            
            // 使用模拟数据
            this.agents = this.getMockAgents();
            this.updateAgentsList();
        }
    }
    
    async loadEvents() {
        try {
            const response = await fetch('http://127.0.0.1:9093/api/events/recent?limit=10');
            const data = await response.json();
            
            console.log('[PixelAgents] 事件数据:', data);
            
            this.events = data.events || [];
            this.updateEventsList();
            
            console.log(`[PixelAgents] 加载了 ${this.events.length} 个事件`);
        } catch (error) {
            console.error('[PixelAgents] 加载事件失败:', error);
            
            // 使用模拟数据
            this.events = this.getMockEvents();
            this.updateEventsList();
        }
    }
    
    convertAgentsData(data) {
        // 将 AIOS Agent System 数据转换为 Pixel Agents 格式
        const agents = [];
        
        // 预定义位置（更分散）
        const positions = [
            { x: 150, y: 200 },  // analyst
            { x: 400, y: 200 },  // coder
            { x: 250, y: 450 },  // monitor
            { x: 650, y: 450 }   // researcher
        ];
        
        let posIndex = 0;
        
        if (data.active_agents_by_template) {
            for (const [type, agentList] of Object.entries(data.active_agents_by_template)) {
                for (const agent of agentList) {
                    const pos = positions[posIndex % positions.length];
                    agents.push({
                        id: agent.id,
                        type: type,
                        name: agent.name,
                        status: agent.last_active ? 'running' : 'idle',
                        position: pos,
                        current_task: agent.task_description || null,
                        last_active: agent.last_active
                    });
                    posIndex++;
                }
            }
        }
        
        return agents;
    }
    
    getMockAgents() {
        // 模拟数据（用于测试）
        return [
            {
                id: 'coder-699258',
                type: 'coder',
                name: '编码开发专员',
                status: 'running',
                position: { x: 100, y: 150 },
                current_task: '优化 AIOS 架构',
                last_active: Date.now()
            },
            {
                id: 'analyst-688334',
                type: 'analyst',
                name: '数据分析专员',
                status: 'idle',
                position: { x: 300, y: 150 },
                current_task: null,
                last_active: Date.now() - 300000
            },
            {
                id: 'monitor-001',
                type: 'monitor',
                name: '系统监控专员',
                status: 'running',
                position: { x: 500, y: 150 },
                current_task: '监控系统资源',
                last_active: Date.now()
            }
        ];
    }
    
    getMockEvents() {
        return [
            {
                timestamp: Date.now() - 2000,
                type: 'agent.task_started',
                agent_id: 'coder-699258',
                message: '开始分析 AIOS 架构'
            },
            {
                timestamp: Date.now() - 300000,
                type: 'agent.task_completed',
                agent_id: 'analyst-688334',
                message: '完成数据分析报告'
            }
        ];
    }
    
    drawOffice() {
        // 清空画布
        this.ctx.fillStyle = '#0a0a0a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制霓虹网格
        this.ctx.strokeStyle = '#00ff9f';
        this.ctx.lineWidth = 1;
        this.ctx.globalAlpha = 0.3;
        for (let x = 0; x < this.canvas.width; x += 50) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }
        for (let y = 0; y < this.canvas.height; y += 50) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
        this.ctx.globalAlpha = 1.0;
        
        // 绘制区域标签（霓虹灯效果）
        this.ctx.fillStyle = '#00ff9f';
        this.ctx.font = 'bold 16px "Courier New"';
        this.ctx.shadowColor = '#00ff9f';
        this.ctx.shadowBlur = 10;
        this.ctx.fillText('>>> 办公区', 20, 30);
        this.ctx.fillText('>>> 会议室', 20, 330);
        this.ctx.fillText('>>> 监控室', 420, 330);
        this.ctx.shadowBlur = 0;
        
        // 绘制 Agents
        this.drawAgents();
    }
    
    drawAgents() {
        for (const agent of this.agents) {
            this.drawAgent(agent);
        }
    }
    
    drawAgent(agent) {
        const { x, y } = agent.position;
        
        // 霓虹灯颜色
        const colors = {
            coder: '#00ff9f',
            analyst: '#ff9f00',
            monitor: '#9f00ff',
            researcher: '#ff00ff'
        };
        
        const statusColors = {
            idle: '#666',
            running: '#00ff9f',
            degraded: '#ff0066',
            learning: '#ffff00'
        };
        
        const color = colors[agent.type] || '#00ff9f';
        const statusColor = statusColors[agent.status] || '#666';
        
        // 呼吸效果
        let pulse = 1.0;
        if (agent.status === 'running') {
            pulse = 0.8 + Math.sin(Date.now() / 500) * 0.2;
        } else {
            pulse = 0.9 + Math.sin(Date.now() / 1000) * 0.1;
        }
        
        // 霓虹光晕
        this.ctx.shadowColor = color;
        this.ctx.shadowBlur = 20 * pulse;
        
        // 根据类型绘制不同造型
        switch(agent.type) {
            case 'coder':
                this.drawCoder(x, y, color, pulse);
                break;
            case 'analyst':
                this.drawAnalyst(x, y, color, pulse);
                break;
            case 'monitor':
                this.drawMonitor(x, y, color, pulse);
                break;
            case 'researcher':
                this.drawResearcher(x, y, color, pulse);
                break;
            default:
                this.drawDefault(x, y, color, pulse);
        }
        
        // 状态指示器
        this.ctx.shadowColor = statusColor;
        this.ctx.shadowBlur = 25 * pulse;
        this.ctx.fillStyle = statusColor;
        this.ctx.beginPath();
        this.ctx.arc(x + 52, y - 8, 8 * pulse, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 清除阴影
        this.ctx.shadowBlur = 0;
        
        // 名字
        this.ctx.fillStyle = color;
        this.ctx.font = 'bold 12px "Courier New"';
        this.ctx.shadowColor = color;
        this.ctx.shadowBlur = 5;
        this.ctx.fillText(agent.type.toUpperCase(), x - 5, y + 110);
        this.ctx.shadowBlur = 0;
        
        // 任务进度条
        if (agent.status === 'running' && agent.current_task) {
            this.ctx.fillStyle = color;
            this.ctx.globalAlpha = 0.3;
            this.ctx.fillRect(x - 10, y + 95, 80, 4);
            this.ctx.globalAlpha = 1.0;
            
            const progress = (Date.now() % 3000) / 3000;
            this.ctx.fillStyle = color;
            this.ctx.fillRect(x - 10, y + 95, 80 * progress, 4);
        }
    }
    
    drawCoder(x, y, color, pulse) {
        // 轻微漂浮效果
        const float = Math.sin(Date.now() / 1500) * 3;
        y += float;
        
        // Coder: 方形身体 + 眼镜
        this.ctx.fillStyle = color;
        this.ctx.globalAlpha = pulse;
        this.ctx.fillRect(x, y, 60, 90);
        this.ctx.globalAlpha = 1.0;
        
        // 头
        this.ctx.fillStyle = '#f0f0f0';
        this.ctx.fillRect(x + 15, y - 30, 30, 30);
        
        // 眼镜
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(x + 18, y - 20, 10, 8);
        this.ctx.strokeRect(x + 32, y - 20, 10, 8);
        this.ctx.beginPath();
        this.ctx.moveTo(x + 28, y - 16);
        this.ctx.lineTo(x + 32, y - 16);
        this.ctx.stroke();
        
        // 键盘符号
        this.ctx.fillStyle = '#fff';
        this.ctx.font = '16px monospace';
        this.ctx.fillText('</>', x + 15, y + 50);
    }
    
    drawAnalyst(x, y, color, pulse) {
        // 轻微漂浮效果（不同频率）
        const float = Math.sin(Date.now() / 1800 + 1) * 3;
        y += float;
        
        // Analyst: 圆形身体 + 图表
        this.ctx.fillStyle = color;
        this.ctx.globalAlpha = pulse;
        
        // 圆形身体
        this.ctx.beginPath();
        this.ctx.arc(x + 30, y + 45, 30, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.globalAlpha = 1.0;
        
        // 头
        this.ctx.fillStyle = '#f0f0f0';
        this.ctx.beginPath();
        this.ctx.arc(x + 30, y - 15, 15, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 图表符号
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(x + 15, y + 60);
        this.ctx.lineTo(x + 20, y + 50);
        this.ctx.lineTo(x + 30, y + 55);
        this.ctx.lineTo(x + 40, y + 40);
        this.ctx.lineTo(x + 45, y + 45);
        this.ctx.stroke();
    }
    
    drawMonitor(x, y, color, pulse) {
        // 轻微漂浮效果
        const float = Math.sin(Date.now() / 2000 + 2) * 3;
        y += float;
        
        // Monitor: 六边形身体 + 眼睛
        this.ctx.fillStyle = color;
        this.ctx.globalAlpha = pulse;
        
        // 六边形
        this.ctx.beginPath();
        this.ctx.moveTo(x + 30, y);
        this.ctx.lineTo(x + 50, y + 15);
        this.ctx.lineTo(x + 50, y + 60);
        this.ctx.lineTo(x + 30, y + 75);
        this.ctx.lineTo(x + 10, y + 60);
        this.ctx.lineTo(x + 10, y + 15);
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.globalAlpha = 1.0;
        
        // 头
        this.ctx.fillStyle = '#f0f0f0';
        this.ctx.fillRect(x + 15, y - 30, 30, 30);
        
        // 眼睛（警觉）
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x + 20, y - 20, 8, 12);
        this.ctx.fillRect(x + 32, y - 20, 8, 12);
    }
    
    drawResearcher(x, y, color, pulse) {
        // 轻微漂浮效果
        const float = Math.sin(Date.now() / 1700 + 3) * 3;
        y += float;
        
        // Researcher: 三角形身体 + 书本
        this.ctx.fillStyle = color;
        this.ctx.globalAlpha = pulse;
        
        // 三角形
        this.ctx.beginPath();
        this.ctx.moveTo(x + 30, y);
        this.ctx.lineTo(x + 60, y + 90);
        this.ctx.lineTo(x, y + 90);
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.globalAlpha = 1.0;
        
        // 头
        this.ctx.fillStyle = '#f0f0f0';
        this.ctx.fillRect(x + 15, y - 30, 30, 30);
        
        // 书本符号
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(x + 20, y + 40, 20, 15);
        this.ctx.beginPath();
        this.ctx.moveTo(x + 30, y + 40);
        this.ctx.lineTo(x + 30, y + 55);
        this.ctx.stroke();
    }
    
    drawDefault(x, y, color, pulse) {
        // 默认造型
        this.ctx.fillStyle = color;
        this.ctx.globalAlpha = pulse;
        this.ctx.fillRect(x, y, 60, 90);
        this.ctx.globalAlpha = 1.0;
        
        this.ctx.fillStyle = '#f0f0f0';
        this.ctx.fillRect(x + 15, y - 30, 30, 30);
    }
    
    updateAgentsList() {
        const container = document.getElementById('agents-list-content');
        
        if (this.agents.length === 0) {
            container.innerHTML = '<p class="loading">暂无 Agent</p>';
            return;
        }
        
        container.innerHTML = this.agents.map(agent => `
            <div class="agent-item status-${agent.status}" data-agent-id="${agent.id}">
                <div class="agent-name">${agent.name}</div>
                <div class="agent-status">状态: ${this.getStatusText(agent.status)}</div>
                ${agent.current_task ? `<div class="agent-task">任务: ${agent.current_task}</div>` : ''}
            </div>
        `).join('');
    }
    
    updateEventsList() {
        const container = document.getElementById('events-log-content');
        
        if (this.events.length === 0) {
            container.innerHTML = '<p class="loading">暂无事件</p>';
            return;
        }
        
        container.innerHTML = this.events.map(event => {
            const timeAgo = this.getTimeAgo(event.timestamp);
            const eventType = this.getEventType(event.type);
            
            // 生成事件消息（更易读）
            let message = event.message || event.type || '未知事件';
            if (event.payload) {
                if (event.payload.error) message = event.payload.error;
                if (event.payload.cpu_percent) message = `CPU: ${event.payload.cpu_percent}%`;
            }
            
            // 美化事件类型
            if (message === 'reactor.skipped') {
                message = '🔧 Reactor 跳过执行';
            } else if (message.includes('agent.')) {
                message = message.replace('agent.', '🤖 Agent ');
            } else if (message.includes('pipeline.')) {
                message = message.replace('pipeline.', '⚙️ Pipeline ');
            } else if (message.includes('resource.')) {
                message = message.replace('resource.', '📊 资源 ');
            }
            
            return `
                <div class="event-item type-${eventType}">
                    <div class="event-time">${timeAgo}</div>
                    <div class="event-message">${message}</div>
                </div>
            `;
        }).join('');
    }
    
    getStatusText(status) {
        const statusMap = {
            idle: '空闲',
            running: '运行中',
            degraded: '降级',
            learning: '学习中'
        };
        return statusMap[status] || status;
    }
    
    getEventType(type) {
        if (type.includes('error') || type.includes('failed')) return 'error';
        if (type.includes('success') || type.includes('completed')) return 'success';
        if (type.includes('warning')) return 'warning';
        return 'info';
    }
    
    getTimeAgo(timestamp) {
        const seconds = Math.floor((Date.now() - timestamp) / 1000);
        
        if (seconds < 60) return `${seconds}秒前`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时前`;
        return `${Math.floor(seconds / 86400)}天前`;
    }
    
    connectWebSocket() {
        try {
            this.ws = new WebSocket('ws://127.0.0.1:9093/ws');
            
            this.ws.onopen = () => {
                console.log('[PixelAgents] WebSocket 连接成功');
                document.getElementById('connection-status').textContent = '● 已连接';
                document.getElementById('connection-status').className = 'status-connected';
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onerror = (error) => {
                console.error('[PixelAgents] WebSocket 错误:', error);
            };
            
            this.ws.onclose = () => {
                console.log('[PixelAgents] WebSocket 断开，5秒后重连...');
                document.getElementById('connection-status').textContent = '● 未连接';
                document.getElementById('connection-status').className = 'status-disconnected';
                
                setTimeout(() => this.connectWebSocket(), 5000);
            };
        } catch (error) {
            console.error('[PixelAgents] WebSocket 连接失败:', error);
            // WebSocket 不可用，使用 HTTP 轮询
            document.getElementById('connection-status').textContent = '● HTTP 轮询';
            document.getElementById('connection-status').className = 'status-disconnected';
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('[PixelAgents] 收到消息:', data);
        
        // 更新数据
        if (data.agents) {
            this.agents = this.convertAgentsData(data.agents);
            this.updateAgentsList();
            this.drawOffice();
        }
        
        if (data.events) {
            this.events = data.events;
            this.updateEventsList();
        }
    }
    
    bindEvents() {
        // 刷新按钮
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadAgents();
            this.loadEvents();
        });
        
        // Agent 点击
        document.getElementById('agents-list-content').addEventListener('click', (e) => {
            const agentItem = e.target.closest('.agent-item');
            if (agentItem) {
                const agentId = agentItem.dataset.agentId;
                this.showAgentDetails(agentId);
            }
        });
        
        // Canvas 鼠标移动（显示 tooltip）
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) * (this.canvas.width / rect.width);
            const y = (e.clientY - rect.top) * (this.canvas.height / rect.height);
            
            this.handleCanvasHover(x, y);
        });
        
        // Canvas 鼠标离开
        this.canvas.addEventListener('mouseleave', () => {
            this.hideTooltip();
        });
    }
    
    handleCanvasHover(mouseX, mouseY) {
        // 检查鼠标是否在 Agent 上（扩大碰撞区域）
        for (const agent of this.agents) {
            const { x, y } = agent.position;
            if (mouseX >= x - 15 && mouseX <= x + 75 && mouseY >= y - 45 && mouseY <= y + 110) {
                this.showTooltip(agent, mouseX, mouseY);
                return;
            }
        }
        this.hideTooltip();
    }
    
    showTooltip(agent, x, y) {
        const container = document.getElementById('agent-tooltips');
        
        let tooltip = container.querySelector('.tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            container.appendChild(tooltip);
        }
        
        const rect = this.canvas.getBoundingClientRect();
        const canvasX = x / this.canvas.width * rect.width;
        const canvasY = y / this.canvas.height * rect.height;
        
        tooltip.style.left = (canvasX + 10) + 'px';
        tooltip.style.top = (canvasY + 10) + 'px';
        tooltip.style.display = 'block';
        
        tooltip.innerHTML = `
            <strong>${agent.name}</strong><br>
            状态: ${this.getStatusText(agent.status)}<br>
            ${agent.current_task ? `任务: ${agent.current_task}<br>` : ''}
            ${agent.last_active ? `活跃: ${this.getTimeAgo(agent.last_active)}` : '从未活跃'}
        `;
    }
    
    hideTooltip() {
        const container = document.getElementById('agent-tooltips');
        const tooltip = container.querySelector('.tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }
    
    showAgentDetails(agentId) {
        const agent = this.agents.find(a => a.id === agentId);
        if (agent) {
            alert(`Agent 详情:\n\nID: ${agent.id}\n类型: ${agent.type}\n名称: ${agent.name}\n状态: ${this.getStatusText(agent.status)}\n当前任务: ${agent.current_task || '无'}`);
        }
    }
    
    animate() {
        // 动画循环
        this.drawOffice();
        
        // 添加扫描线效果
        this.drawScanlines();
        
        // 添加粒子效果（霓虹光点）
        this.drawParticles();
        
        requestAnimationFrame(() => this.animate());
    }
    
    drawScanlines() {
        // 扫描线效果（赛博朋克风格）
        this.ctx.globalAlpha = 0.05;
        this.ctx.fillStyle = '#00ff9f';
        
        const time = Date.now() / 50;
        const y = (time % this.canvas.height);
        
        this.ctx.fillRect(0, y, this.canvas.width, 2);
        this.ctx.fillRect(0, (y + this.canvas.height / 2) % this.canvas.height, this.canvas.width, 2);
        
        this.ctx.globalAlpha = 1.0;
    }
    
    drawParticles() {
        // 霓虹光点效果
        if (!this.particles) {
            this.particles = [];
            for (let i = 0; i < 20; i++) {
                this.particles.push({
                    x: Math.random() * this.canvas.width,
                    y: Math.random() * this.canvas.height,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    size: Math.random() * 2 + 1,
                    color: ['#00ff9f', '#ff9f00', '#9f00ff', '#ff00ff'][Math.floor(Math.random() * 4)]
                });
            }
        }
        
        this.ctx.globalAlpha = 0.6;
        for (const p of this.particles) {
            // 更新位置
            p.x += p.vx;
            p.y += p.vy;
            
            // 边界反弹
            if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;
            
            // 绘制光点
            this.ctx.fillStyle = p.color;
            this.ctx.shadowColor = p.color;
            this.ctx.shadowBlur = 10;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fill();
        }
        this.ctx.shadowBlur = 0;
        this.ctx.globalAlpha = 1.0;
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.pixelAgents = new PixelAgents();
});
