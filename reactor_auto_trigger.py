#!/usr/bin/env python3
"""
AIOS Reactor Auto-Trigger
监听事件流，自动触发 Reactor playbooks
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

AIOS_ROOT = Path(__file__).parent
EVENTS_FILE = AIOS_ROOT / "events" / "events.jsonl"
PLAYBOOKS_FILE = AIOS_ROOT / "data" / "playbooks.json"
REACTOR_LOG = AIOS_ROOT / "reactor_log.jsonl"
LAST_CHECK_FILE = AIOS_ROOT / "data" / "reactor_last_check.txt"

def load_playbooks() -> List[Dict]:
    """加载 playbooks"""
    if not PLAYBOOKS_FILE.exists():
        return []
    
    with open(PLAYBOOKS_FILE, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    # 兼容两种格式：数组或单个对象
    if isinstance(data, list):
        playbooks = data
    elif isinstance(data, dict):
        # 如果是单个对象，包装成数组
        playbooks = [data]
    else:
        playbooks = []
    
    return [pb for pb in playbooks if pb.get('enabled', True)]

def load_recent_events(since_minutes: int = 5) -> List[Dict]:
    """加载最近的事件"""
    if not EVENTS_FILE.exists():
        return []
    
    cutoff = datetime.now() - timedelta(minutes=since_minutes)
    events = []
    
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                ts = datetime.fromisoformat(event.get('ts', '2000-01-01'))
                if ts > cutoff:
                    events.append(event)
            except:
                continue
    
    return events

def match_playbook(event: Dict, playbook: Dict) -> bool:
    """判断事件是否匹配 playbook"""
    trigger = playbook.get('trigger', {})
    
    # 检查 severity
    event_severity = event.get('severity', 'INFO')
    if event_severity not in trigger.get('severity', ['WARN', 'ERR', 'CRIT']):
        return False
    
    # 检查 keywords
    keywords = trigger.get('keywords', [])
    event_text = json.dumps(event, ensure_ascii=False).lower()
    
    for keyword in keywords:
        if keyword.lower() in event_text:
            return True
    
    return False

def get_timeout(playbook: Dict, event: Dict) -> int:
    """根据 playbook 类型和事件严重程度动态设置超时"""
    base_timeout = playbook.get('action', {}).get('timeout', 30)
    
    # 严重事件给更多时间
    severity = event.get('severity', 'INFO')
    if severity == 'CRIT':
        return int(base_timeout * 2)
    elif severity == 'ERR':
        return int(base_timeout * 1.5)
    
    return base_timeout

def verify_fix(playbook: Dict, event: Dict) -> bool:
    """
    验证修复是否成功
    
    Args:
        playbook: Playbook 配置
        event: 触发事件
        
    Returns:
        True 如果验证通过，False 否则
    """
    import subprocess
    
    verify_cmd = playbook.get('action', {}).get('verify_command')
    
    if not verify_cmd:
        # 没有验证命令，默认信任 returncode
        return True
    
    try:
        proc = subprocess.run(
            verify_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return proc.returncode == 0
    except Exception as e:
        print(f"   ⚠️ 验证失败: {e}")
        return False

def execute_playbook(playbook: Dict, event: Dict, retry_attempt: int = 0) -> Dict:
    """执行 playbook（单次尝试）"""
    import subprocess
    
    action = playbook.get('action', {})
    command = action.get('command', '')
    action_type = action.get('type', 'auto')
    
    result = {
        'playbook_id': playbook['id'],
        'playbook_name': playbook['name'],
        'event_id': event.get('epoch', 0),
        'timestamp': datetime.now().isoformat(),
        'status': 'pending',
        'verified': False,
        'retry_attempt': retry_attempt
    }
    
    # 如果需要确认，跳过自动执行
    if action_type == 'confirm':
        result['status'] = 'pending_confirm'
        return result
    
    # 动态超时
    timeout = get_timeout(playbook, event)
    
    # 执行命令
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if proc.returncode == 0:
            # 执行成功，进行验证
            result['verified'] = verify_fix(playbook, event)
            result['status'] = 'success' if result['verified'] else 'failed'
            if not result['verified']:
                result['error'] = 'Verification failed'
        else:
            result['status'] = 'failed'
            result['error'] = proc.stderr[:200]
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)[:200]
    
    return result

def execute_playbook_with_retry(playbook: Dict, event: Dict, max_retries: int = 3) -> Dict:
    """执行 playbook（带重试）"""
    retry_delays = [1, 2, 5]  # 指数退避：1s, 2s, 5s
    
    for attempt in range(max_retries):
        result = execute_playbook(playbook, event, retry_attempt=attempt)
        
        if result['status'] == 'success' and result['verified']:
            if attempt > 0:
                result['retried'] = True
                result['total_attempts'] = attempt + 1
            return result
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < max_retries - 1:
            delay = retry_delays[min(attempt, len(retry_delays) - 1)]
            time.sleep(delay)
    
    # 所有重试都失败
    result['retried'] = True
    result['total_attempts'] = max_retries
    return result

def log_reaction(result: Dict):
    """记录 Reactor 执行结果"""
    REACTOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    with open(REACTOR_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False) + '\n')

def update_last_check():
    """更新最后检查时间"""
    LAST_CHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_CHECK_FILE.write_text(datetime.now().isoformat())

def main():
    """主循环"""
    print("🤖 AIOS Reactor Auto-Trigger 启动")
    
    playbooks = load_playbooks()
    print(f"📦 加载了 {len(playbooks)} 个 playbooks")
    
    # 加载最近 5 分钟的事件
    events = load_recent_events(since_minutes=5)
    print(f"📊 检测到 {len(events)} 个最近事件")
    
    # 收集所有匹配的 (event, playbook) 对
    tasks = []
    for event in events:
        for playbook in playbooks:
            if match_playbook(event, playbook):
                tasks.append((event, playbook))
                print(f"✅ 匹配: {playbook['name']} <- {event.get('event', 'unknown')}")
    
    if not tasks:
        print("📈 统计: 无匹配任务")
        print("✅ Reactor 检查完成")
        return
    
    # 并行执行所有任务
    import concurrent.futures
    
    matched = len(tasks)
    executed = 0
    
    print(f"\n🚀 并行执行 {matched} 个任务...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(execute_playbook_with_retry, playbook, event, 3): (event, playbook)
            for event, playbook in tasks
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_task):
            event, playbook = future_to_task[future]
            try:
                result = future.result()
                log_reaction(result)
                
                if result['status'] == 'success':
                    executed += 1
                    retry_info = f" (重试 {result.get('total_attempts', 1)} 次)" if result.get('retried') else ""
                    print(f"   ✓ {playbook['name']}: 执行成功{retry_info}")
                elif result['status'] == 'pending_confirm':
                    print(f"   ⏸ {playbook['name']}: 等待确认")
                else:
                    retry_info = f" (已重试 {result.get('total_attempts', 1)} 次)" if result.get('retried') else ""
                    print(f"   ✗ {playbook['name']}: 执行失败{retry_info}: {result.get('error', 'unknown')}")
            except Exception as e:
                print(f"   ❌ {playbook['name']}: 异常 - {e}")
    
    update_last_check()
    
    print(f"\n📈 统计: 匹配 {matched} 个，执行 {executed} 个")
    print("✅ Reactor 检查完成")

if __name__ == '__main__':
    main()
