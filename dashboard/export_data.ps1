# AIOS Dashboard Data Export Script
param([string]$OutputPath = "C:\Users\A\.openclaw\workspace\aios\dashboard\export_data.json")

$ErrorActionPreference = "Stop"
$baseDir = "C:\Users\A\.openclaw\workspace\aios\agent_system"

Write-Host "=== AIOS Data Export ===" -ForegroundColor Cyan

$exportData = [ordered]@{}
$exportData.timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$exportData.version = "1.0"

# Agents
$agentsFile = Join-Path $baseDir "agents.json"
if (Test-Path $agentsFile) {
    Write-Host "[1/6] agents.json..." -ForegroundColor Yellow
    $exportData.agents = Get-Content $agentsFile -Raw | ConvertFrom-Json
    Write-Host "  OK" -ForegroundColor Green
}

# Tasks
$queueFile = Join-Path $baseDir "task_queue.jsonl"
if (Test-Path $queueFile) {
    Write-Host "[2/6] task_queue.jsonl..." -ForegroundColor Yellow
    $tasks = @()
    Get-Content $queueFile | ForEach-Object {
        if ($_.Trim()) { $tasks += ($_ | ConvertFrom-Json) }
    }
    $exportData.tasks = $tasks
    Write-Host "  OK ($($tasks.Count) tasks)" -ForegroundColor Green
}

# Events
$eventsFile = Join-Path $baseDir "events.jsonl"
if (Test-Path $eventsFile) {
    Write-Host "[3/6] events.jsonl..." -ForegroundColor Yellow
    $events = @()
    Get-Content $eventsFile -Tail 1000 | ForEach-Object {
        if ($_.Trim()) { $events += ($_ | ConvertFrom-Json) }
    }
    $exportData.events = $events
    Write-Host "  OK ($($events.Count) events)" -ForegroundColor Green
}

# Lessons
$lessonsFile = Join-Path $baseDir "lessons.json"
if (Test-Path $lessonsFile) {
    Write-Host "[4/6] lessons.json..." -ForegroundColor Yellow
    $exportData.lessons = Get-Content $lessonsFile -Raw | ConvertFrom-Json
    Write-Host "  OK" -ForegroundColor Green
}

# Alerts
$alertsFile = Join-Path $baseDir "alerts.jsonl"
if (Test-Path $alertsFile) {
    Write-Host "[5/6] alerts.jsonl..." -ForegroundColor Yellow
    $alerts = @()
    Get-Content $alertsFile | ForEach-Object {
        if ($_.Trim()) { $alerts += ($_ | ConvertFrom-Json) }
    }
    $exportData.alerts = $alerts
    Write-Host "  OK ($($alerts.Count) alerts)" -ForegroundColor Green
}

# System State
$stateFile = Join-Path $baseDir "system_state.json"
if (Test-Path $stateFile) {
    Write-Host "[6/6] system_state.json..." -ForegroundColor Yellow
    $exportData.system_state = Get-Content $stateFile -Raw | ConvertFrom-Json
    Write-Host "  OK" -ForegroundColor Green
}

Write-Host "`nWriting to $OutputPath..." -ForegroundColor Cyan
$exportData | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputPath -Encoding UTF8

$fileSize = (Get-Item $OutputPath).Length / 1KB
Write-Host "Done! ($([math]::Round($fileSize, 2)) KB)" -ForegroundColor Green
