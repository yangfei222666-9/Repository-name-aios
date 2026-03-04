# AIOS v2.0 - 停止所有监控服务

Write-Host "停止AIOS监控服务..."

# 停止Metrics Exporter
$jobIdFile = "aios/observability/.metrics_job_id"
if (Test-Path $jobIdFile) {
    $jobId = Get-Content $jobIdFile
    Stop-Job -Id $jobId -ErrorAction SilentlyContinue
    Remove-Job -Id $jobId -ErrorAction SilentlyContinue
    Remove-Item $jobIdFile
    Write-Host "✓ Metrics Exporter 已停止"
}

# 停止Docker容器
docker stop aios-prometheus aios-grafana 2>$null
docker rm aios-prometheus aios-grafana 2>$null
Write-Host "✓ Prometheus 和 Grafana 已停止"

Write-Host "`n所有服务已停止"
