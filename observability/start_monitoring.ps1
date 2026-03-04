# AIOS v2.0 - 一键启动脚本
# 启动所有监控和测试服务

Write-Host "=" * 60
Write-Host "AIOS v2.0 - 监控和压测环境启动"
Write-Host "=" * 60

# 检查依赖
Write-Host "`n[1/5] 检查依赖..."
$deps = @("fastapi", "uvicorn", "prometheus-client", "locust", "psutil")
foreach ($dep in $deps) {
    $installed = & "C:\Program Files\Python312\python.exe" -c "import $dep" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ $dep 未安装，正在安装..."
        & "C:\Program Files\Python312\python.exe" -m pip install $dep -q
    } else {
        Write-Host "  ✓ $dep"
    }
}

# 启动Metrics Exporter
Write-Host "`n[2/5] 启动Metrics Exporter (端口9090)..."
$metricsJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\A\.openclaw\workspace"
    & "C:\Program Files\Python312\python.exe" aios/observability/metrics_exporter.py
}
Write-Host "  ✓ Metrics Exporter 已启动 (Job ID: $($metricsJob.Id))"
Write-Host "  访问: http://localhost:9090/metrics"
Write-Host "  统计: http://localhost:9090/stats"

# 等待服务启动
Start-Sleep -Seconds 3

# 启动Prometheus (Docker)
Write-Host "`n[3/5] 启动Prometheus (端口9091)..."
$prometheusRunning = docker ps --filter "name=aios-prometheus" --format "{{.Names}}"
if ($prometheusRunning -eq "aios-prometheus") {
    Write-Host "  ⚠ Prometheus 已在运行，跳过"
} else {
    docker run -d --name aios-prometheus `
        -p 9091:9090 `
        -v "${PWD}/aios/observability/prometheus.yml:/etc/prometheus/prometheus.yml" `
        prom/prometheus
    Write-Host "  ✓ Prometheus 已启动"
    Write-Host "  访问: http://localhost:9091"
}

# 启动Grafana (Docker)
Write-Host "`n[4/5] 启动Grafana (端口3000)..."
$grafanaRunning = docker ps --filter "name=aios-grafana" --format "{{.Names}}"
if ($grafanaRunning -eq "aios-grafana") {
    Write-Host "  ⚠ Grafana 已在运行，跳过"
} else {
    docker run -d --name aios-grafana `
        -p 3000:3000 `
        grafana/grafana
    Write-Host "  ✓ Grafana 已启动"
    Write-Host "  访问: http://localhost:3000 (admin/admin)"
}

# 显示下一步操作
Write-Host "`n[5/5] 环境就绪！"
Write-Host "=" * 60
Write-Host "`n下一步操作："
Write-Host "1. 打开 Grafana: http://localhost:3000"
Write-Host "   - 添加数据源: Prometheus (http://host.docker.internal:9091)"
Write-Host "   - 导入仪表盘: aios/observability/grafana_dashboard.json"
Write-Host ""
Write-Host "2. 启动12小时压力测试:"
Write-Host "   cd aios/observability"
Write-Host "   locust -f stress_test.py --host=http://localhost:9090 \"
Write-Host "          --users 5 --spawn-rate 5 --run-time 12h \"
Write-Host "          --html report_12h.html"
Write-Host ""
Write-Host "3. 监控指标:"
Write-Host "   - Grafana仪表盘: http://localhost:3000"
Write-Host "   - Prometheus查询: http://localhost:9091"
Write-Host "   - 实时统计: http://localhost:9090/stats"
Write-Host ""
Write-Host "4. 停止所有服务:"
Write-Host "   .\stop_monitoring.ps1"
Write-Host "=" * 60

# 保存Job ID供后续停止
$metricsJob.Id | Out-File -FilePath "aios/observability/.metrics_job_id" -Encoding utf8
