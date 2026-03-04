# AIOS v2.0 - 监控和压测环境

完整的Prometheus + Grafana + Locust压测环境

## 快速开始

### 1. 一键启动所有服务

```powershell
cd C:\Users\A\.openclaw\workspace\aios\observability
.\start_monitoring.ps1
```

这会启动：
- Metrics Exporter (端口9090) - 统一指标导出
- Prometheus (端口9091) - 指标采集
- Grafana (端口3000) - 可视化仪表盘

### 2. 配置Grafana

1. 打开 http://localhost:3000
2. 登录 (admin/admin)
3. 添加数据源:
   - Type: Prometheus
   - URL: http://host.docker.internal:9091
   - Save & Test
4. 导入仪表盘:
   - Dashboards → Import
   - 上传 `grafana_dashboard.json`

### 3. 验证环境

```powershell
python verify_environment.py
```

应该看到所有测试通过 ✓

### 4. 启动12小时压力测试

```powershell
locust -f stress_test.py --host=http://localhost:9090 `
       --users 5 --spawn-rate 5 --run-time 12h `
       --html report_12h.html
```

或者使用Ramp-up版本（前30分钟从1→5用户）：

```powershell
locust -f stress_test.py --host=http://localhost:9090 `
       --users 5 --spawn-rate 0.0028 --run-time 12h `
       --html report_12h.html
```

### 5. 监控测试进度

- **Grafana仪表盘**: http://localhost:3000
- **Prometheus查询**: http://localhost:9091
- **实时统计**: http://localhost:9090/stats
- **Locust Web UI**: http://localhost:8089 (如果启动了Web模式)

### 6. 停止所有服务

```powershell
.\stop_monitoring.ps1
```

---

## 核心指标（SLO）

测试结束后检查以下5个指标：

| 指标 | 目标 | 告警阈值 | Prometheus查询 |
|------|------|----------|----------------|
| P95 Latency | ≤ 6s | > 8s | `histogram_quantile(0.95, sum(rate(task_latency_seconds_bucket[5m])) by (le))` |
| Success Rate | ≥ 95% | < 90% | `100 * sum(rate(task_success_total[5m])) / sum(rate(task_total[5m]))` |
| Queue Backlog | ≤ 50 | > 200 | `queue_size_gauge` |
| Memory Growth | ≤ 10%/12h | > 15%/h | `process_resident_memory_bytes` |
| Agent Spawn Rate | ≤ 120/h | > 150/h | `rate(agent_spawn_per_hour_total[1h])` |

---

## 文件说明

```
aios/observability/
├── metrics_exporter.py      # 统一指标导出服务
├── prometheus.yml           # Prometheus配置
├── grafana_dashboard.json   # Grafana仪表盘
├── stress_test.py           # Locust压力测试脚本
├── verify_environment.py    # 环境验证脚本
├── start_monitoring.ps1     # 一键启动脚本
├── stop_monitoring.ps1      # 一键停止脚本
└── README.md                # 本文件
```

---

## 故障排查

### Metrics Exporter无法启动

```powershell
# 检查端口占用
netstat -ano | findstr :9090

# 手动启动（查看错误）
python metrics_exporter.py
```

### Prometheus无法连接

```powershell
# 检查Docker容器
docker ps -a | findstr prometheus

# 查看日志
docker logs aios-prometheus
```

### Grafana无法访问

```powershell
# 检查Docker容器
docker ps -a | findstr grafana

# 重启容器
docker restart aios-grafana
```

### 压测任务不执行

1. 检查 `task_queue.jsonl` 是否有任务写入
2. 检查 Heartbeat 是否正常运行
3. 查看 `metrics_exporter.py` 日志

---

## 下一步

测试完成后：

1. 查看 `report_12h.html` - Locust生成的详细报告
2. 导出Grafana截图 - 5个核心指标的趋势图
3. 分析是否达到Phase 4标准：
   - ✓ Success Rate ≥ 95%
   - ✓ P95 Latency ≤ 6s
   - ✓ Memory Growth ≤ 10%
   - ✓ Queue Backlog ≤ 50
   - ✓ Agent Spawn Rate ≤ 120/h

如果全部达标 → 进入Phase 4（生产部署）

---

*最后更新: 2026-03-05*  
*版本: v2.0*
