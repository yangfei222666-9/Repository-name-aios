# AIOS v2.0 - Docker Compose 快速启动指南

## 前置条件
- Docker Desktop 已安装并运行
- 当前目录：`C:\Users\A\.openclaw\workspace\aios`

## 一键启动（Phase 4 测试结束后）

```powershell
# 1. 停止当前测试环境
docker stop aios-prometheus aios-grafana
docker rm aios-prometheus aios-grafana
Stop-Job -Name * -ErrorAction SilentlyContinue

# 2. 启动 Docker Compose 全家桶
cd C:\Users\A\.openclaw\workspace\aios
docker compose up -d

# 3. 验证服务状态
docker compose ps
docker compose logs -f aios-metrics
```

## 服务访问

- **AIOS Metrics**: http://localhost:9090
  - `/health` - 健康检查
  - `/metrics` - Prometheus 指标
  - `/stats` - 统计数据

- **Prometheus**: http://localhost:9091
  - 查询和分析指标

- **Grafana**: http://localhost:3000
  - 默认账号：admin/admin
  - 自动加载 AIOS 仪表盘

## 常用命令

```powershell
# 查看日志
docker compose logs -f aios-metrics
docker compose logs -f prometheus
docker compose logs -f grafana

# 重启服务
docker compose restart aios-metrics

# 停止所有服务
docker compose down

# 停止并删除数据卷
docker compose down -v

# 查看资源使用
docker stats
```

## 健康检查

```powershell
# 检查 AIOS Metrics
Invoke-WebRequest http://localhost:9090/health

# 检查 Prometheus
Invoke-WebRequest http://localhost:9091/-/healthy

# 检查 Grafana
Invoke-WebRequest http://localhost:3000/api/health
```

## 故障排查

### 服务无法启动
```powershell
# 查看详细日志
docker compose logs aios-metrics

# 检查端口占用
netstat -ano | findstr "9090"
netstat -ano | findstr "9091"
netstat -ano | findstr "3000"
```

### 数据持久化
- Prometheus 数据：`prometheus_data` 卷
- Grafana 数据：`grafana_data` 卷

### 重置环境
```powershell
docker compose down -v
docker compose up -d
```

## 生产部署建议

1. **环境变量配置**
   - 创建 `.env` 文件
   - 配置敏感信息（密码、Token）

2. **资源限制**
   - 添加 CPU/内存限制
   - 配置日志轮转

3. **监控告警**
   - 配置 Prometheus AlertManager
   - 集成 Telegram/钉钉通知

4. **备份策略**
   - 定期备份数据卷
   - 导出 Grafana 仪表盘配置

## Phase 5 升级路径

Phase 4 通过后，我们将提供：
- `docker-compose.prod.yml` - 生产级配置
- Kubernetes Deployment YAML
- 自动扩缩容配置（HPA）
- 完整的 CI/CD 流程
