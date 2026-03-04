# AIOS v2.0 架构设计

## 核心定位
**AIOS：一个能自愈的 AI Agent 运行时系统**  
*Self-healing runtime for autonomous AI agents*

---

## 系统架构图

```mermaid
graph TB
    subgraph "Core Agents (8个)"
        CD[coder-dispatcher<br/>代码生成任务分发]
        AD[analyst-dispatcher<br/>数据分析任务分发]
        MD[monitor-dispatcher<br/>系统健康监控分发]
        TQP[task-queue-processor<br/>队列消费引擎]
        TS[task-scheduler<br/>定时任务调度]
        MR[model-router<br/>LLM路由+负载均衡]
        AF[auto-fixer<br/>自愈逻辑核心]
        DM[dependency-manager<br/>依赖解析+版本锁定]
    end
    
    subgraph "Auxiliary Agents (10个)"
        subgraph "Analysis (6个)"
            PA[pattern-analyzer]
            TA[trend-analyzer]
            AA[anomaly-analyzer]
            CA[cost-analyzer]
            QA[quality-analyzer]
            RA[resource-analyzer]
        end
        
        subgraph "Learning (3个)"
            LS[LowSuccess_Agent]
            EL[experience-learner]
            SL[strategy-learner]
        end
        
        subgraph "Skill-based (1个)"
            SE[skill-executor]
        end
    end
    
    subgraph "Runtime Services (无状态微服务)"
        NM[notification-manager<br/>通知推送]
        DP[data-pipeline<br/>数据ETL]
        WD[workflow-designer<br/>工作流编排]
        CM[context-manager<br/>上下文管理]
        TD[task-decomposer<br/>任务拆解]
        UI[user-intent-classifier<br/>意图识别]
    end
    
    subgraph "Observability Stack"
        PROM[Prometheus<br/>指标采集]
        GRAF[Grafana<br/>可视化仪表盘]
        OTEL[OpenTelemetry<br/>链路追踪]
    end
    
    subgraph "Data Layer"
        TQ[(task_queue.jsonl)]
        TE[(task_executions.jsonl)]
        AL[(agents.json)]
        EL_DB[(experience_library.jsonl)]
        LANCE[(LanceDB<br/>向量检索)]
    end
    
    subgraph "Insight Layer (差异化卖点)"
        ES[Evolution Score<br/>系统健康度]
        YJ[易经卦象<br/>系统洞察报告]
    end
    
    %% 核心流程
    User[用户/Heartbeat] --> TQP
    TQP --> TQ
    TQP --> CD
    TQP --> AD
    TQP --> MD
    
    CD --> MR
    AD --> MR
    MD --> MR
    
    MR --> TE
    TE --> AF
    AF --> LS
    LS --> EL_DB
    
    %% 监控流程
    TQP --> PROM
    CD --> PROM
    AD --> PROM
    MD --> PROM
    AF --> PROM
    
    PROM --> GRAF
    PROM --> AF
    
    %% 洞察层
    TE --> PA
    PA --> ES
    ES --> YJ
    YJ --> NM
    
    %% 依赖管理
    CD --> DM
    AD --> DM
    MD --> DM
```

---

## 核心指标（SLO）

### 1. 任务延迟（P95 Latency）
- **目标：** ≤ 6s
- **告警：** > 8s
- **Prometheus指标：** `task_latency_p95_seconds{quantile="0.95"}`

### 2. 成功率（Success Rate）
- **目标：** ≥ 95%
- **告警：** < 90%
- **Prometheus指标：** `task_success_rate_percent`

### 3. 队列积压（Queue Backlog）
- **目标：** ≤ 50
- **告警：** > 200
- **Prometheus指标：** `queue_size_gauge{queue="main"}`

### 4. 内存增长（Memory Growth）
- **目标：** ≤ 10% / 12h
- **告警：** > 15% / h
- **Prometheus指标：** `process_resident_memory_bytes`

### 5. Agent生成速率（Spawn Rate）
- **目标：** ≤ 120 / h
- **告警：** > 150 / h
- **Prometheus指标：** `agent_spawn_per_hour_total`

---

## 架构收缩对比

| 维度 | v1.0 (当前) | v2.0 (目标) | 改善 |
|------|-------------|-------------|------|
| 核心Agent | 45个 | 8个 | -82% |
| 辅助Agent | 0个 | 10个 | 职责清晰 |
| Runtime Services | 0个 | 6个 | 解耦 |
| 协调开销 | 高 | 低 | -70% |
| 内存泄漏风险 | 高 | 低 | -80% |
| 上下文污染 | 严重 | 可控 | -90% |

---

## Phase 1 执行清单（7天）

### Day 1-2: 目录重构
```
aios/
├── agents/
│   ├── core/              # 8个核心Agent
│   │   ├── coder_dispatcher.py
│   │   ├── analyst_dispatcher.py
│   │   ├── monitor_dispatcher.py
│   │   ├── task_queue_processor.py
│   │   ├── task_scheduler.py
│   │   ├── model_router.py
│   │   ├── auto_fixer.py
│   │   └── dependency_manager.py
│   ├── auxiliary/         # 10个辅助Agent
│   │   ├── analysis/      # 6个
│   │   ├── learning/      # 3个
│   │   └── skill/         # 1个
│   └── base.py            # 统一基类
├── services/
│   └── runtime/           # 6个无状态服务
│       ├── notification_manager.py
│       ├── data_pipeline.py
│       ├── workflow_designer.py
│       ├── context_manager.py
│       ├── task_decomposer.py
│       └── user_intent_classifier.py
├── observability/
│   ├── prometheus.yml
│   ├── grafana.json
│   └── otel_config.yaml
└── tests/
    └── stress_test.py
```

### Day 3-4: 统一Agent基类
- 减少重复代码80%
- 标准化生命周期管理
- 统一错误处理

### Day 5: 服务化迁移
- Docker Compose部署runtime services
- 健康检查 + 自动重启

### Day 6-7: 小压力测试
- 每分钟1个任务
- 持续1小时
- 验证稳定性

---

## 12小时压力测试方案

### 负载配置
- **Ramp-up:** 前30分钟从1→5任务/分钟
- **稳定期:** 5任务/分钟 × 11.5小时
- **总任务量:** ~3,450个任务

### 退出条件（任一失败即失败）
1. `success_rate ≥ 95%`
2. `memory_growth ≤ 10%`
3. `p95_latency ≤ 6s`
4. `queue_backlog ≤ 50`
5. `agent_spawn_per_hour ≤ 120`

### 监控面板
- 实时Grafana仪表盘
- 自动告警（Telegram推送）
- 压测报告自动生成

---

## 差异化卖点

### 1. 自愈能力（Auto-Fixer）
- 失败任务自动重生（75%成功率）
- LanceDB向量检索历史成功策略
- Bootstrapped Regeneration（sirius启发）

### 2. 易经洞察层（Evolution Score）
- 64卦智慧决策系统
- 每日系统健康度报告
- 人类可读的系统洞察

### 3. 生产级可观测性
- Prometheus + Grafana + OpenTelemetry
- 5大核心SLO指标
- 自动告警 + 自动修复

---

## 下一步行动

1. ✅ 架构图（已完成）
2. ⏳ 8个核心Agent代码框架
3. ⏳ Prometheus + Grafana配置
4. ⏳ 压力测试脚本

**预计完成时间：** 7天内完成Phase 1，进入12小时压测

---

*最后更新：2026-03-05 00:11*  
*版本：v2.0-alpha*
