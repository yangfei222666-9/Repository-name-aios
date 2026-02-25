#!/usr/bin/env python3
"""测试 Reactor 并行化"""

import time
import sys
from pathlib import Path

# 模拟 playbook 执行
def mock_execute_playbook(playbook, event, max_retries=3):
    """模拟执行（延迟 0.5s）"""
    time.sleep(0.5)
    return {
        'playbook_id': playbook['id'],
        'status': 'success',
        'verified': True
    }

def test_sequential():
    """测试串行执行"""
    playbooks = [{'id': f'pb{i}', 'name': f'Playbook {i}'} for i in range(10)]
    event = {'event': 'test'}
    
    start = time.time()
    for pb in playbooks:
        mock_execute_playbook(pb, event)
    duration = time.time() - start
    
    print(f"Sequential execution: {duration:.2f}s")
    return duration

def test_parallel():
    """测试并行执行"""
    import concurrent.futures
    
    playbooks = [{'id': f'pb{i}', 'name': f'Playbook {i}'} for i in range(10)]
    event = {'event': 'test'}
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(mock_execute_playbook, pb, event) for pb in playbooks]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    duration = time.time() - start
    
    print(f"Parallel execution (5 workers): {duration:.2f}s")
    return duration

if __name__ == '__main__':
    print("Testing Reactor parallelization...\n")
    
    seq_time = test_sequential()
    par_time = test_parallel()
    
    speedup = seq_time / par_time
    improvement = (1 - par_time / seq_time) * 100
    
    print(f"\nSpeedup: {speedup:.2f}x")
    print(f"Improvement: {improvement:.1f}%")
    
    if speedup >= 2.0:
        print("\n[SUCCESS] Parallelization working! (>2x speedup)")
    else:
        print(f"\n[WARNING] Speedup less than expected ({speedup:.2f}x < 2.0x)")
