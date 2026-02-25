#!/usr/bin/env python3
"""
AIOS 自动知识提取器
从 events.jsonl 和对话中提取知识，自动更新 lessons.json 和 USER.md
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# 配置
WORKSPACE = Path(__file__).parent.parent.parent
AIOS_DIR = WORKSPACE / "aios"
MEMORY_DIR = WORKSPACE / "memory"
LESSONS_FILE = MEMORY_DIR / "lessons.json"
USER_FILE = WORKSPACE / "USER.md"
EVENTS_FILE = AIOS_DIR / "data" / "events.jsonl"

# 知识提取规则
ERROR_PATTERNS = {
    "encoding": ["UnicodeEncodeError", "gbk", "utf-8", "encoding"],
    "path": ["FileNotFoundError", "No such file", "路径", "path"],
    "permission": ["PermissionError", "Access denied", "权限"],
    "timeout": ["TimeoutError", "timeout", "超时"],
    "api": ["API", "rate limit", "401", "403", "429"],
    "memory": ["MemoryError", "out of memory", "内存"],
    "syntax": ["SyntaxError", "IndentationError", "语法"],
}

USER_PREFERENCE_PATTERNS = {
    "喜欢": r"(喜欢|爱用|想要|偏好|习惯用)([^，。！？\n]{3,30})",
    "不喜欢": r"(不喜欢|讨厌|不要|别用|最讨厌)([^，。！？\n]{3,30})",
    "工作习惯": r"(通常|一般|经常|每天|每周)([^，。！？\n]{3,30})",
}


def load_lessons():
    """加载现有教训"""
    if not LESSONS_FILE.exists():
        return []
    
    with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # 兼容旧格式（有 lessons 字段）和新格式（直接是数组）
        if isinstance(data, dict) and 'lessons' in data:
            return data['lessons']
        return data if isinstance(data, list) else []


def save_lessons(lessons):
    """保存教训（保持原有格式）"""
    LESSONS_FILE.parent.mkdir(exist_ok=True)
    
    # 读取原文件以保留其他字段（如 rules_derived）
    existing_data = {}
    if LESSONS_FILE.exists():
        with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    # 更新 lessons 字段
    if isinstance(existing_data, dict):
        existing_data['lessons'] = lessons
        output = existing_data
    else:
        output = {"lessons": lessons}
    
    with open(LESSONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def extract_error_patterns():
    """从 events.jsonl 提取错误模式"""
    if not EVENTS_FILE.exists():
        return []
    
    # 读取最近24小时的事件
    cutoff_time = datetime.now() - timedelta(hours=24)
    recent_errors = []
    
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                event = json.loads(line)
                timestamp = event.get('timestamp', '')
                if not timestamp:
                    continue
                
                event_time = datetime.fromisoformat(timestamp)
                if event_time < cutoff_time:
                    continue
                
                # 只关注错误事件
                if event.get('type') != 'error':
                    continue
                
                recent_errors.append(event)
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
    
    # 分析错误模式
    new_lessons = []
    error_messages = [e.get('message', '') for e in recent_errors]
    
    # 统计错误类型
    error_types = Counter()
    for msg in error_messages:
        for error_type, keywords in ERROR_PATTERNS.items():
            if any(kw in msg for kw in keywords):
                error_types[error_type] += 1
    
    # 生成教训（出现3次以上的错误）
    for error_type, count in error_types.items():
        if count >= 3:
            # 找一个具体的错误消息作为示例
            example = next((msg for msg in error_messages 
                          if any(kw in msg for kw in ERROR_PATTERNS[error_type])), "")
            
            lesson = {
                "category": error_type,
                "pattern": f"重复出现 {count} 次",
                "lesson": generate_lesson_text(error_type, example),
                "confidence": "draft",
                "first_seen": datetime.now().isoformat(),
                "occurrences": count,
                "auto_extracted": True
            }
            new_lessons.append(lesson)
    
    return new_lessons


def generate_lesson_text(error_type, example):
    """根据错误类型生成教训文本"""
    templates = {
        "encoding": "Windows 终端输出中文时用 -X utf8 参数运行 Python",
        "path": "使用绝对路径或 Path 对象，避免路径拼接错误",
        "permission": "需要管理员权限时用 Start-Process -Verb RunAs",
        "timeout": "增加超时时间或添加重试机制",
        "api": "遇到 API 限流时添加延迟和指数退避",
        "memory": "处理大文件时分块读取，避免一次性加载",
        "syntax": "检查代码语法，特别是缩进和括号匹配",
    }
    
    base_lesson = templates.get(error_type, "需要进一步分析")
    
    # 如果有具体示例，添加上下文
    if example and len(example) < 100:
        return f"{base_lesson}（示例：{example[:50]}...）"
    
    return base_lesson


def extract_user_preferences():
    """从最近的对话中提取用户偏好"""
    # 读取最近3天的 memory 文件
    preferences = []
    
    for days_ago in range(3):
        date = datetime.now() - timedelta(days=days_ago)
        memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        
        if not memory_file.exists():
            continue
        
        with open(memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取偏好模式
        for pref_type, pattern in USER_PREFERENCE_PATTERNS.items():
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    trigger = match[0]
                    pref_text = match[1].strip()
                else:
                    continue
                
                # 过滤无效匹配
                if len(pref_text) < 3 or len(pref_text) > 50:
                    continue
                
                # 过滤包含代码/路径的匹配
                if any(x in pref_text for x in ['\\', '/', '()', '==', '->']):
                    continue
                
                full_text = f"{trigger}{pref_text}"
                preferences.append({
                    "type": pref_type,
                    "text": full_text,
                    "date": date.strftime('%Y-%m-%d')
                })
    
    return preferences


def update_user_md(preferences):
    """更新 USER.md 中的偏好"""
    if not preferences or not USER_FILE.exists():
        return {"status": "skip", "reason": "no preferences or USER.md not found"}
    
    with open(USER_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有"偏好"部分
    if "## 偏好" not in content:
        # 在文件末尾添加偏好部分
        new_section = "\n\n## 偏好\n"
        for pref in preferences[:5]:  # 只添加前5个
            new_section += f"- {pref['text']} ({pref['date']})\n"
        
        content += new_section
        
        with open(USER_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"status": "updated", "added": len(preferences[:5])}
    
    return {"status": "skip", "reason": "preferences section already exists"}


def merge_lessons(existing, new_lessons):
    """合并新旧教训，去重"""
    # 创建现有教训的签名集合
    existing_sigs = set()
    for lesson in existing:
        sig = f"{lesson.get('category', '')}:{lesson.get('pattern', '')}"
        existing_sigs.add(sig)
    
    # 只添加新的教训
    added = []
    for new_lesson in new_lessons:
        sig = f"{new_lesson['category']}:{new_lesson['pattern']}"
        if sig not in existing_sigs:
            existing.append(new_lesson)
            added.append(new_lesson)
    
    return existing, added


def main():
    """主函数"""
    print("🧠 AIOS 自动知识提取")
    print("=" * 50)
    
    results = {}
    
    # 1. 提取错误模式
    print("\n🔍 分析错误模式...")
    new_error_lessons = extract_error_patterns()
    
    if new_error_lessons:
        print(f"   ✅ 发现 {len(new_error_lessons)} 个新错误模式")
        for lesson in new_error_lessons:
            print(f"   📌 {lesson['category']}: {lesson['lesson']}")
    else:
        print("   ✅ 无新错误模式")
    
    # 2. 合并到 lessons.json
    print("\n📚 更新教训库...")
    existing_lessons = load_lessons()
    merged_lessons, added = merge_lessons(existing_lessons, new_error_lessons)
    
    if added:
        save_lessons(merged_lessons)
        print(f"   ✅ 添加 {len(added)} 条新教训")
        results['lessons_added'] = len(added)
    else:
        print("   ✅ 无新教训需要添加")
        results['lessons_added'] = 0
    
    # 3. 提取用户偏好
    print("\n👤 提取用户偏好...")
    preferences = extract_user_preferences()
    
    if preferences:
        print(f"   ✅ 发现 {len(preferences)} 个偏好")
        for pref in preferences[:3]:
            print(f"   💡 {pref['type']}: {pref['text'][:30]}...")
    else:
        print("   ✅ 无新偏好")
    
    # 4. 更新 USER.md
    print("\n📝 更新用户档案...")
    update_result = update_user_md(preferences)
    results['user_updated'] = update_result
    
    if update_result['status'] == 'updated':
        print(f"   ✅ 添加 {update_result['added']} 个偏好到 USER.md")
    else:
        print(f"   ℹ️  {update_result.get('reason', 'no update needed')}")
    
    # 5. 保存提取报告
    report_file = AIOS_DIR / "data" / "knowledge_report.json"
    report_file.parent.mkdir(exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "new_lessons": [l['lesson'] for l in added] if added else [],
        "preferences_count": len(preferences)
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 知识提取报告已保存: {report_file.relative_to(WORKSPACE)}")
    
    # 6. 输出心跳格式
    print("\n" + "=" * 50)
    if results['lessons_added'] > 0:
        print(f"KNOWLEDGE_EXTRACTED:{results['lessons_added']}")
    else:
        print("KNOWLEDGE_OK")


if __name__ == "__main__":
    main()
