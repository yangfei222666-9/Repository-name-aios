# AIOS v0.5 鎬ц兘娣卞害鍒嗘瀽鑴氭湰
# PowerShell 鐗堟湰

$ErrorActionPreference = "Stop"
$workspace = "C:\Users\A\.openclaw\workspace\aios"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "AIOS v0.5 鎬ц兘娣卞害鍒嗘瀽" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# 鍔犺浇 JSON 鏁版嵁
function Load-JsonLines {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        return @()
    }
    
    $data = @()
    Get-Content $Path -Encoding UTF8 | ForEach-Object {
        if ($_.Trim()) {
            try {
                $data += ($_ | ConvertFrom-Json)
            } catch {
                Write-Warning "JSON 瑙ｆ瀽閿欒: $_"
            }
        }
    }
    return $data
}

Write-Host "`n[1/5] 鍔犺浇浜嬩欢鏁版嵁..." -ForegroundColor Yellow

# 鍔犺浇鎵€鏈変簨浠?$events = @()
$events += Load-JsonLines "$workspace\events.jsonl"
$events += Load-JsonLines "$workspace\events\events.jsonl"
$events += Load-JsonLines "$workspace\data\events.jsonl"

$reactorLogs = Load-JsonLines "$workspace\reactor_log.jsonl"
$executionLogs = Load-JsonLines "$workspace\events\execution_log.jsonl"

Write-Host "  - 浜嬩欢鎬绘暟: $($events.Count)"
Write-Host "  - Reactor 鏃ュ織: $($reactorLogs.Count)"
Write-Host "  - 鎵ц鏃ュ織: $($executionLogs.Count)"

Write-Host "`n[2/5] 鍒嗘瀽浜嬩欢..." -ForegroundColor Yellow

# 缁熻鏁版嵁
$stats = @{
    total_events = $events.Count
    by_layer = @{}
    by_event_type = @{}
    by_status = @{}
    latency_by_event = @{}
    errors = @()
    cpu_spikes = @()
}

foreach ($event in $events) {
    # 鎸夊眰缁熻
    $layer = if ($event.layer) { $event.layer } else { "UNKNOWN" }
    if (-not $stats.by_layer.ContainsKey($layer)) {
        $stats.by_layer[$layer] = 0
    }
    $stats.by_layer[$layer]++
    
    # 鎸変簨浠剁被鍨嬬粺璁?    $eventType = if ($event.event) { $event.event } elseif ($event.type) { $event.type } else { "unknown" }
    if (-not $stats.by_event_type.ContainsKey($eventType)) {
        $stats.by_event_type[$eventType] = 0
    }
    $stats.by_event_type[$eventType]++
    
    # 鎸夌姸鎬佺粺璁?    $status = if ($event.status) { $event.status } else { "unknown" }
    if (-not $stats.by_status.ContainsKey($status)) {
        $stats.by_status[$status] = 0
    }
    $stats.by_status[$status]++
    
    # 寤惰繜缁熻
    if ($event.latency_ms) {
        if (-not $stats.latency_by_event.ContainsKey($eventType)) {
            $stats.latency_by_event[$eventType] = @()
        }
        $stats.latency_by_event[$eventType] += $event.latency_ms
    }
    
    # 閿欒鏀堕泦
    if ($status -in @('err', 'error')) {
        $stats.errors += @{
            timestamp = if ($event.ts) { $event.ts } else { $event.timestamp }
            layer = $layer
            event = $eventType
            payload = $event.payload
        }
    }
    
    # CPU 宄板€?    if ($eventType -in @('cpu_high', 'resource.cpu_spike')) {
        $cpuPercent = $event.payload.cpu_percent
        $stats.cpu_spikes += @{
            timestamp = if ($event.ts) { $event.ts } else { $event.timestamp }
            cpu_percent = $cpuPercent
        }
    }
}

Write-Host "  - 鎬讳簨浠? $($stats.total_events)"
Write-Host "  - 閿欒鏁? $($stats.errors.Count)"
Write-Host "  - CPU 宄板€? $($stats.cpu_spikes.Count)"

Write-Host "`n[3/5] 鍒嗘瀽 Reactor 鎬ц兘..." -ForegroundColor Yellow

$reactorStats = @{
    total = $reactorLogs.Count
    success = 0
    failed = 0
    by_playbook = @{}
}

foreach ($log in $reactorLogs) {
    $playbookId = if ($log.playbook_id) { $log.playbook_id } else { "unknown" }
    
    if (-not $reactorStats.by_playbook.ContainsKey($playbookId)) {
        $reactorStats.by_playbook[$playbookId] = @{ success = 0; failed = 0 }
    }
    
    if ($log.status -eq 'success') {
        $reactorStats.success++
        $reactorStats.by_playbook[$playbookId].success++
    } elseif ($log.status -eq 'failed') {
        $reactorStats.failed++
        $reactorStats.by_playbook[$playbookId].failed++
    }
}

$reactorSuccessRate = if ($reactorStats.total -gt 0) { 
    [math]::Round($reactorStats.success / $reactorStats.total * 100, 2) 
} else { 0 }

Write-Host "  - Reactor 鎬绘墽琛? $($reactorStats.total)"
Write-Host "  - 鎴愬姛鐜? $reactorSuccessRate%"

Write-Host "`n[4/5] 鍒嗘瀽鎵ц鏃ュ織..." -ForegroundColor Yellow

$executionStates = @{}
foreach ($log in $executionLogs) {
    $state = if ($log.terminal_state) { $log.terminal_state } else { "UNKNOWN" }
    if (-not $executionStates.ContainsKey($state)) {
        $executionStates[$state] = 0
    }
    $executionStates[$state]++
}

Write-Host "  - 鎵ц鐘舵€佺被鍨? $($executionStates.Count)"

Write-Host "`n[5/5] 鐢熸垚鎶ュ憡..." -ForegroundColor Yellow

# 鐢熸垚鎶ュ憡
$reportPath = "$workspace\reports\performance_deep_analysis.md"
$vizPath = "$workspace\reports\performance_visualization.json"

# 纭繚鐩綍瀛樺湪
New-Item -ItemType Directory -Force -Path "$workspace\reports" | Out-Null

# 鐢熸垚鍙鍖栨暟鎹?$errorRate = if ($stats.total_events -gt 0) { 
    [math]::Round($stats.by_status['err'] / $stats.total_events * 100, 2) 
} else { 0 }

$vizData = @{
    summary = @{
        total_events = $stats.total_events
        error_rate = $errorRate
        reactor_success_rate = $reactorSuccessRate
        cpu_spike_count = $stats.cpu_spikes.Count
    }
    events_by_layer = $stats.by_layer
    events_by_type = $stats.by_event_type
    reactor_performance = $reactorStats
    execution_states = $executionStates
    top_errors = $stats.errors | Select-Object -First 10
    cpu_spikes = $stats.cpu_spikes
}

$vizData | ConvertTo-Json -Depth 10 | Out-File -FilePath $vizPath -Encoding UTF8

# 鐢熸垚 Markdown 鎶ュ憡
$report = @"
# AIOS v0.5 鎬ц兘娣卞害鍒嗘瀽鎶ュ憡

**鐢熸垚鏃堕棿**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

---

## 馃搳 鎵ц鎽樿

- **鎬讳簨浠舵暟**: $($stats.total_events)
- **閿欒鐜?*: $errorRate%
- **Reactor 鎴愬姛鐜?*: $reactorSuccessRate%
- **CPU 宄板€兼鏁?*: $($stats.cpu_spikes.Count)

## 馃搱 浜嬩欢鍒嗗竷鍒嗘瀽

### 鎸夊眰绾х粺璁?
"@

# 鎸夊眰绾ф帓搴?$stats.by_layer.GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object {
    $percentage = [math]::Round($_.Value / $stats.total_events * 100, 1)
    $report += "- **$($_.Key)**: $($_.Value) ($percentage%)`n"
}

$report += @"

### 鎸変簨浠剁被鍨嬬粺璁★紙Top 15锛?
"@

# 鎸変簨浠剁被鍨嬫帓搴?$stats.by_event_type.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 15 | ForEach-Object {
    $percentage = [math]::Round($_.Value / $stats.total_events * 100, 1)
    $report += "- **$($_.Key)**: $($_.Value) ($percentage%)`n"
}

$report += @"

## 鈿?鎬ц兘鎸囨爣

### 寤惰繜鍒嗗竷锛圱op 10 鎱簨浠讹級

"@

# 璁＄畻寤惰繜缁熻
$latencyStats = @()
foreach ($eventType in $stats.latency_by_event.Keys) {
    $latencies = $stats.latency_by_event[$eventType]
    if ($latencies.Count -gt 0) {
        $sorted = $latencies | Sort-Object
        $p95Index = [math]::Floor($sorted.Count * 0.95)
        $p99Index = [math]::Floor($sorted.Count * 0.99)
        
        $latencyStats += @{
            event_type = $eventType
            count = $latencies.Count
            min = ($sorted | Measure-Object -Minimum).Minimum
            max = ($sorted | Measure-Object -Maximum).Maximum
            mean = [math]::Round(($sorted | Measure-Object -Average).Average, 1)
            median = $sorted[[math]::Floor($sorted.Count / 2)]
            p95 = $sorted[$p95Index]
            p99 = $sorted[$p99Index]
        }
    }
}

$latencyStats | Sort-Object -Property p95 -Descending | Select-Object -First 10 | ForEach-Object {
    $report += @"

**$($_.event_type)**
- 璋冪敤娆℃暟: $($_.count)
- 骞冲潎寤惰繜: $($_.mean)ms
- 涓綅鏁? $($_.median)ms
- P95: $($_.p95)ms
- P99: $($_.p99)ms
- 鏈€澶у€? $($_.max)ms

"@
}

# CPU 宄板€煎垎鏋?if ($stats.cpu_spikes.Count -gt 0) {
    $cpuValues = $stats.cpu_spikes | Where-Object { $_.cpu_percent } | ForEach-Object { $_.cpu_percent }
    if ($cpuValues.Count -gt 0) {
        $avgCpu = [math]::Round(($cpuValues | Measure-Object -Average).Average, 1)
        $maxCpu = [math]::Round(($cpuValues | Measure-Object -Maximum).Maximum, 1)
        $minCpu = [math]::Round(($cpuValues | Measure-Object -Minimum).Minimum, 1)
        
        $report += @"

## 馃敟 CPU 宄板€煎垎鏋?
- **宄板€兼鏁?*: $($cpuValues.Count)
- **骞冲潎 CPU**: $avgCpu%
- **鏈€楂?CPU**: $maxCpu%
- **鏈€浣?CPU**: $minCpu%

"@
    }
}

$report += @"

## 馃幆 Reactor 鎵ц鏁堢巼

- **鎬绘墽琛屾鏁?*: $($reactorStats.total)
- **鎴愬姛娆℃暟**: $($reactorStats.success)
- **澶辫触娆℃暟**: $($reactorStats.failed)
- **鎴愬姛鐜?*: $reactorSuccessRate%

### Playbook 鎬ц兘

"@

foreach ($playbook in $reactorStats.by_playbook.Keys) {
    $pbStats = $reactorStats.by_playbook[$playbook]
    $total = $pbStats.success + $pbStats.failed
    $successRate = if ($total -gt 0) { [math]::Round($pbStats.success / $total * 100, 1) } else { 0 }
    $icon = if ($successRate -ge 80) { "鉁? } elseif ($successRate -ge 50) { "鈿狅笍" } else { "鉂? }
    
    $report += "$icon **$playbook**: $($pbStats.success)/$total ($successRate%)`n"
}

# 鎵ц鐘舵€佸垎鏋?if ($executionStates.Count -gt 0) {
    $totalExec = ($executionStates.Values | Measure-Object -Sum).Sum
    
    $report += @"

## 馃攧 鎵ц鐘舵€佸垎鏋?
"@
    
    $executionStates.GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object {
        $percentage = [math]::Round($_.Value / $totalExec * 100, 1)
        $report += "- **$($_.Key)**: $($_.Value) ($percentage%)`n"
    }
}

# 閿欒鍒嗘瀽
if ($stats.errors.Count -gt 0) {
    $report += @"

## 鉂?閿欒鍒嗘瀽

- **鎬婚敊璇暟**: $($stats.errors.Count)
- **閿欒鐜?*: $errorRate%

### 鏈€杩戠殑閿欒锛圱op 5锛?
"@
    
    $stats.errors | Select-Object -Last 5 | ForEach-Object {
        $report += @"

**$($_.event)** @ $($_.timestamp)
- Layer: $($_.layer)

"@
        if ($_.payload.error) {
            $report += "- Error: $($_.payload.error)`n"
        }
        if ($_.payload.detail) {
            $report += "- Detail: $($_.payload.detail)`n"
        }
    }
}

# 浼樺寲寤鸿
$report += @"

## 馃挕 浼樺寲寤鸿

"@

$recommendations = @()

# 1. 閿欒鐜囧垎鏋?if ($errorRate -gt 10) {
    $recommendations += "馃敶 閿欒鐜囪繃楂?($errorRate%)锛岄渶瑕佸姞寮洪敊璇鐞嗗拰閲嶈瘯鏈哄埗"
} elseif ($errorRate -gt 5) {
    $recommendations += "馃煛 閿欒鐜囧亸楂?($errorRate%)锛屽缓璁紭鍖栭敊璇仮澶嶇瓥鐣?
}

# 2. Reactor 鎴愬姛鐜?if ($reactorStats.total -gt 0 -and $reactorSuccessRate -lt 80) {
    $recommendations += "馃敶 Reactor 鎴愬姛鐜囪繃浣?($reactorSuccessRate%)锛岄渶瑕佷慨澶嶅け璐ョ殑 Playbook"
}

# 3. CPU 宄板€?if ($stats.cpu_spikes.Count -gt 5) {
    $recommendations += "鈿狅笍 妫€娴嬪埌 $($stats.cpu_spikes.Count) 娆?CPU 宄板€硷紝寤鸿浼樺寲璧勬簮瀵嗛泦鍨嬫搷浣?
}

# 4. 鎱簨浠?$slowEvents = $latencyStats | Where-Object { $_.p95 -gt 1000 }
if ($slowEvents.Count -gt 0) {
    $recommendations += "馃悓 鍙戠幇 $($slowEvents.Count) 绉嶆參浜嬩欢锛圥95 > 1s锛夛紝闇€瑕佹€ц兘浼樺寲"
    $slowEvents | Sort-Object -Property p95 -Descending | Select-Object -First 3 | ForEach-Object {
        $recommendations += "   - $($_.event_type): P95 = $([math]::Round($_.p95, 0))ms"
    }
}

# 5. NOOP 姣斾緥
if ($executionStates.Count -gt 0) {
    $totalExec = ($executionStates.Values | Measure-Object -Sum).Sum
    $noopCount = 0
    if ($executionStates.ContainsKey('NOOP_DEDUP')) { $noopCount += $executionStates['NOOP_DEDUP'] }
    if ($executionStates.ContainsKey('NOOP_ALREADY_RUNNING')) { $noopCount += $executionStates['NOOP_ALREADY_RUNNING'] }
    
    if ($totalExec -gt 0) {
        $noopRate = [math]::Round($noopCount / $totalExec * 100, 1)
        if ($noopRate -gt 40) {
            $recommendations += "馃攧 NOOP 姣斾緥杩囬珮 ($noopRate%)锛屽缓璁紭鍖栧幓閲嶇瓥鐣?
        }
    }
}

# 6. 涓婁笅鏂囦慨鍓?$contextPrunes = if ($stats.by_event_type.ContainsKey('context_prune')) { $stats.by_event_type['context_prune'] } else { 0 }
if ($contextPrunes -gt 10) {
    $recommendations += "馃捑 棰戠箒鐨勪笂涓嬫枃淇壀 ($contextPrunes 娆?锛岃€冭檻澧炲姞涓婁笅鏂囩獥鍙ｆ垨浼樺寲鍐呭瓨绠＄悊"
}

# 7. 宸ュ叿璋冪敤
$toolExecs = if ($stats.by_event_type.ContainsKey('tool_exec')) { $stats.by_event_type['tool_exec'] } else { 0 }
if ($toolExecs -gt 50) {
    $recommendations += "馃敡 宸ュ叿璋冪敤棰戠箒 ($toolExecs 娆?锛岃€冭檻鎵归噺鎿嶄綔鎴栫紦瀛樼粨鏋?
}

# 8. 缃戠粶閿欒
$networkErrors = $stats.errors | Where-Object { $_.event -like '*network*' }
if ($networkErrors.Count -gt 3) {
    $recommendations += "馃寪 缃戠粶閿欒棰戠箒 ($($networkErrors.Count) 娆?锛屽缓璁寮洪噸璇曟満鍒跺拰瓒呮椂閰嶇疆"
}

# 9. 鏂矾鍣?$circuitBreaker = if ($stats.by_event_type.ContainsKey('circuit_breaker_tripped')) { $stats.by_event_type['circuit_breaker_tripped'] } else { 0 }
$deadloopBreaker = if ($stats.by_event_type.ContainsKey('deadloop_breaker_tripped')) { $stats.by_event_type['deadloop_breaker_tripped'] } else { 0 }
if ($circuitBreaker + $deadloopBreaker -gt 0) {
    $recommendations += "馃毃 鏂矾鍣ㄨЕ鍙?$($circuitBreaker + $deadloopBreaker) 娆★紝绯荤粺瀛樺湪绋冲畾鎬ч棶棰?
}

# 10. Agent 閿欒
$agentErrors = $events | Where-Object { $_.type -eq 'agent.error' }
if ($agentErrors.Count -gt 0) {
    $recommendations += "馃 Agent 鎵ц澶辫触 $($agentErrors.Count) 娆★紝闇€瑕佹敼杩涗换鍔″鐞嗛€昏緫"
}

# 閫氱敤寤鸿
if ($recommendations.Count -eq 0) {
    $recommendations += "鉁?绯荤粺鏁翠綋杩愯鑹ソ锛岀户缁繚鎸?
}

$recommendations += "馃搳 寤鸿瀹氭湡鐩戞帶鍏抽敭鎸囨爣锛氶敊璇巼銆丳95寤惰繜銆丆PU浣跨敤鐜囥€丷eactor鎴愬姛鐜?
$recommendations += "馃攳 寤鸿瀹炴柦鍒嗗竷寮忚拷韪紝鏇村ソ鍦扮悊瑙ｈ姹傞摼璺?
$recommendations += "鈿?鑰冭檻瀹炴柦鎬ц兘棰勭畻锛屼负鍏抽敭鎿嶄綔璁剧疆寤惰繜闃堝€?
$recommendations += "馃敀 寤鸿澧炲姞鏇村鐨勫畨鍏ㄦ鏌ョ偣鍜岀啍鏂満鍒?
$recommendations += "馃搱 鑰冭檻瀹炴柦鑷€傚簲闄愭祦锛屾牴鎹郴缁熻礋杞藉姩鎬佽皟鏁?

for ($i = 0; $i -lt $recommendations.Count; $i++) {
    $report += "$($i + 1). $($recommendations[$i])`n"
}

$report += @"

## 馃搸 闄勫綍

- **鍙鍖栨暟鎹?*: `performance_visualization.json`
- **鍒嗘瀽鑴氭湰**: `scripts/Analyze-Performance.ps1`
- **鏁版嵁婧?*: events.jsonl, reactor_log.jsonl, execution_log.jsonl

---
*鏈姤鍛婄敱 AIOS 鎬ц兘鍒嗘瀽宸ュ叿鑷姩鐢熸垚*
"@

# 鍐欏叆鎶ュ憡
$report | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "`n鉁?鎶ュ憡宸茬敓鎴? $reportPath" -ForegroundColor Green
Write-Host "鉁?鍙鍖栨暟鎹凡淇濆瓨: $vizPath" -ForegroundColor Green

Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "鍒嗘瀽瀹屾垚锛? -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

# 鏄剧ず鎽樿
Write-Host "`n馃搳 鍒嗘瀽鎽樿:" -ForegroundColor Yellow
Write-Host "  - 鎬讳簨浠舵暟: $($stats.total_events)"
Write-Host "  - 閿欒鐜? $errorRate%"
Write-Host "  - Reactor 鎴愬姛鐜? $reactorSuccessRate%"
Write-Host "  - CPU 宄板€? $($stats.cpu_spikes.Count) 娆?
Write-Host "  - 浼樺寲寤鸿: $($recommendations.Count) 鏉?
