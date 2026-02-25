#!/usr/bin/env python3
"""测试 Reactor 重试机制"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reactor_auto_trigger import execute_playbook_with_retry, get_timeout

def test_retry_success_on_first_attempt():
    """测试：第一次就成功"""
    playbook = {
        'id': 'test1',
        'name': 'Test Playbook',
        'action': {
            'command': 'echo success',
            'type': 'auto'
        }
    }
    event = {'epoch': 1, 'severity': 'INFO'}
    
    result = execute_playbook_with_retry(playbook, event, max_retries=3)
    
    assert result['status'] == 'success', f"Expected success, got {result['status']}"
    assert result.get('retried') is None, "Should not have retried"
    print("[PASS] test_retry_success_on_first_attempt")

def test_retry_failure():
    """测试：所有重试都失败"""
    playbook = {
        'id': 'test2',
        'name': 'Failing Playbook',
        'action': {
            'command': 'exit 1',  # 总是失败
            'type': 'auto'
        }
    }
    event = {'epoch': 2, 'severity': 'ERR'}
    
    result = execute_playbook_with_retry(playbook, event, max_retries=3)
    
    assert result['status'] == 'failed', f"Expected failed, got {result['status']}"
    assert result.get('retried') == True, "Should have retried"
    assert result.get('total_attempts') == 3, f"Expected 3 attempts, got {result.get('total_attempts')}"
    print("[PASS] test_retry_failure")

def test_dynamic_timeout():
    """测试：动态超时"""
    playbook = {'action': {'timeout': 30}}
    
    # INFO 级别
    event_info = {'severity': 'INFO'}
    timeout_info = get_timeout(playbook, event_info)
    assert timeout_info == 30, f"Expected 30, got {timeout_info}"
    
    # ERR 级别
    event_err = {'severity': 'ERR'}
    timeout_err = get_timeout(playbook, event_err)
    assert timeout_err == 45, f"Expected 45, got {timeout_err}"
    
    # CRIT 级别
    event_crit = {'severity': 'CRIT'}
    timeout_crit = get_timeout(playbook, event_crit)
    assert timeout_crit == 60, f"Expected 60, got {timeout_crit}"
    
    print("[PASS] test_dynamic_timeout")

def test_pending_confirm():
    """测试：需要确认的 playbook 不执行"""
    playbook = {
        'id': 'test3',
        'name': 'Confirm Playbook',
        'action': {
            'command': 'echo test',
            'type': 'confirm'
        }
    }
    event = {'epoch': 3, 'severity': 'WARN'}
    
    result = execute_playbook_with_retry(playbook, event, max_retries=3)
    
    assert result['status'] == 'pending_confirm', f"Expected pending_confirm, got {result['status']}"
    print("[PASS] test_pending_confirm")

if __name__ == '__main__':
    print("Testing Reactor retry mechanism...\n")
    
    try:
        test_retry_success_on_first_attempt()
        test_retry_failure()
        test_dynamic_timeout()
        test_pending_confirm()
        
        print("\n[SUCCESS] All tests passed!")
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
