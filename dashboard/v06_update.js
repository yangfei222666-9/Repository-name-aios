// v0.6 Dashboard 数据更新
function updateV06Dashboard(data) {
    if (!data.scheduler_v06 || !data.reactor_v06 || !data.eventstore_v06) {
        console.warn('v0.6 data not available');
        return;
    }

    // 更新 Scheduler 数据
    const sched = data.scheduler_v06;
    updateElement('v06-queue-ready', sched.queue_ready);
    updateElement('v06-queue-retrying', sched.retrying);
    updateElement('v06-concurrency-used', sched.concurrency_used);
    updateElement('v06-concurrency-max', sched.concurrency_max);
    updateElement('v06-running', sched.running);
    updateElement('v06-dlq', sched.dlq);
    updateElement('v06-dlq-new-1h', sched.dlq_new_1h);
    updateElement('v06-exec-p95', sched.exec_p95_ms.toFixed(1));
    updateElement('v06-wait-p95', sched.wait_p95_ms.toFixed(1));
    updateElement('v06-retry-rate', (sched.retry_rate_1h * 100).toFixed(1) + '%');

    // 更新熔断器状态
    const circuit = sched.circuit_breaker;
    const circuitEl = document.getElementById('v06-circuit-status');
    if (circuitEl) {
        circuitEl.textContent = circuit.status.toUpperCase();
        circuitEl.style.color = circuit.status === 'open' ? '#ef4444' : '#10b981';
    }

    // 更新 Reactor 数据
    const reactor = data.reactor_v06;
    updateElement('v06-rules-total', reactor.rules_total);
    updateElement('v06-any-rules', reactor.any_rules);

    // 更新匹配统计
    const match = reactor.match_stats_1h;
    updateElement('v06-match-total', match.total_events);
    updateElement('v06-match-candidates', match.avg_candidates.toFixed(1));
    updateElement('v06-match-hitrate', (match.hit_rate * 100).toFixed(0) + '%');
    updateElement('v06-match-time', match.avg_match_time_ms.toFixed(2));

    // 更新规则类型分布
    const rulesByType = reactor.rules_by_type;
    const rulesByTypeEl = document.getElementById('v06-rules-by-type');
    if (rulesByTypeEl) {
        if (Object.keys(rulesByType).length === 0) {
            rulesByTypeEl.textContent = '全部为 any 规则';
        } else {
            const html = Object.entries(rulesByType)
                .map(([type, count]) => `<span style="margin-right: 10px;">${type}: ${count}</span>`)
                .join('');
            rulesByTypeEl.innerHTML = html;
        }
    }
}

// 辅助函数：安全更新元素
function updateElement(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
    }
}

// 在主更新函数中调用
function updateDashboard(data) {
    // ... 现有更新逻辑 ...
    
    // 添加 v0.6 更新
    updateV06Dashboard(data);
}
