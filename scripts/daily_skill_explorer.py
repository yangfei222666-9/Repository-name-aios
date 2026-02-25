"""
每日技能探索与自动安装
自动搜索 ClawdHub 技能，评估价值，自动安装高分技能
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path(r"C:\Users\A\.openclaw\workspace")
STATE_FILE = WORKSPACE / "memory" / "selflearn-state.json"
DAILY_LOG = WORKSPACE / "memory" / f"{datetime.now().strftime('%Y-%m-%d')}.md"

# 搜索关键词（轮换）
SEARCH_KEYWORDS = [
    "notification", "telegram", "alert",
    "backup", "recovery", "archive",
    "log", "analyzer", "monitor",
    "security", "audit", "scanner",
    "performance", "profiler", "optimizer",
    "database", "sql", "connector",
    "github", "git", "cicd",
    "ai", "automation", "productivity"
]

# AIOS 相关关键词（用于评估相关性）
AIOS_KEYWORDS = [
    "notification", "alert", "monitor", "log", "backup",
    "security", "audit", "performance", "profiler",
    "automation", "scheduler", "agent", "event"
]

def load_state():
    """加载状态文件"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    """保存状态文件"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_today_keyword(state):
    """获取今天要搜索的关键词（轮换）"""
    last_keyword_index = state.get("last_keyword_index", -1)
    next_index = (last_keyword_index + 1) % len(SEARCH_KEYWORDS)
    return SEARCH_KEYWORDS[next_index], next_index

def search_skills(keyword):
    """搜索技能"""
    try:
        result = subprocess.run(
            [r"C:\Users\A\AppData\Roaming\npm\clawdhub.cmd", "search", keyword, "--limit", "10"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30,
            shell=True
        )
        
        if result.returncode != 0:
            return None
        
        # 解析输出
        lines = result.stdout.strip().split('\n')
        skills = []
        
        for line in lines:
            if ' v' in line and '(' in line:
                # 格式: skill-name v1.0.0  Description  (3.456)
                parts = line.split('  ')
                if len(parts) >= 2:
                    name_version = parts[0].strip()
                    name = name_version.split(' v')[0]
                    
                    # 提取评分
                    score_str = line.split('(')[-1].split(')')[0]
                    try:
                        score = float(score_str)
                    except:
                        score = 0.0
                    
                    skills.append({
                        "name": name,
                        "score": score,
                        "line": line
                    })
        
        return skills
    
    except Exception as e:
        print(f"搜索失败: {e}")
        return None

def is_aios_related(skill_name):
    """判断技能是否与 AIOS 相关"""
    name_lower = skill_name.lower()
    return any(keyword in name_lower for keyword in AIOS_KEYWORDS)

def is_already_installed(skill_name):
    """检查技能是否已安装"""
    try:
        result = subprocess.run(
            [r"C:\Users\A\AppData\Roaming\npm\clawdhub.cmd", "list"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10,
            shell=True
        )
        
        if result.returncode == 0:
            installed = result.stdout.strip().split('\n')
            for line in installed:
                if skill_name in line:
                    return True
        
        return False
    
    except Exception as e:
        print(f"检查安装状态失败: {e}")
        return False

def install_skill(skill_name):
    """安装技能"""
    try:
        result = subprocess.run(
            [r"C:\Users\A\AppData\Roaming\npm\clawdhub.cmd", "install", skill_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60,
            shell=True
        )
        
        if result.returncode == 0:
            return True, "安装成功"
        else:
            error = result.stderr.strip() if result.stderr else result.stdout.strip()
            return False, error
    
    except Exception as e:
        return False, str(e)

def log_to_daily(message):
    """记录到每日日志"""
    timestamp = datetime.now().strftime("%H:%M")
    
    # 确保文件存在
    if not DAILY_LOG.exists():
        DAILY_LOG.write_text(f"# {datetime.now().strftime('%Y-%m-%d')} 日志\n\n", encoding='utf-8')
    
    # 追加日志
    with open(DAILY_LOG, 'a', encoding='utf-8') as f:
        f.write(f"\n## {timestamp} 技能探索\n{message}\n")

def main():
    """主函数"""
    print("=== 每日技能探索与自动安装 ===\n")
    
    # 加载状态
    state = load_state()
    
    # 获取今天的搜索关键词
    keyword, keyword_index = get_today_keyword(state)
    print(f"今天搜索关键词: {keyword}")
    
    # 搜索技能
    skills = search_skills(keyword)
    
    if skills is None:
        print("搜索失败（可能限流中）")
        log_to_daily(f"**搜索关键词：** {keyword}\n**结果：** 搜索失败（可能限流中）")
        return
    
    print(f"找到 {len(skills)} 个技能\n")
    
    # 筛选高价值技能
    high_value_skills = [
        s for s in skills 
        if s['score'] >= 3.0 and is_aios_related(s['name'])
    ]
    
    print(f"高价值技能（评分≥3.0 且与AIOS相关）: {len(high_value_skills)}")
    
    # 安装统计
    installed_count = 0
    skipped_count = 0
    failed_count = 0
    
    installed_list = []
    skipped_list = []
    failed_list = []
    
    for skill in high_value_skills:
        name = skill['name']
        score = skill['score']
        
        # 检查是否已安装
        if is_already_installed(name):
            print(f"  ⏭️  {name} ({score}) - 已安装")
            skipped_count += 1
            skipped_list.append(f"- {name} ({score}) - 已安装")
            continue
        
        # 尝试安装
        print(f"  📦 安装 {name} ({score})...", end=" ")
        success, message = install_skill(name)
        
        if success:
            print("✅")
            installed_count += 1
            installed_list.append(f"- ✅ {name} ({score})")
        else:
            print(f"❌ {message}")
            failed_count += 1
            failed_list.append(f"- ❌ {name} ({score}) - {message}")
    
    # 生成日志
    log_message = f"""**搜索关键词：** {keyword}
**找到技能：** {len(skills)} 个
**高价值技能：** {len(high_value_skills)} 个（评分≥3.0 且与AIOS相关）

**安装结果：**
- 成功安装：{installed_count} 个
- 已安装跳过：{skipped_count} 个
- 安装失败：{failed_count} 个

"""
    
    if installed_list:
        log_message += "**新安装技能：**\n" + "\n".join(installed_list) + "\n\n"
    
    if skipped_list:
        log_message += "**已安装技能：**\n" + "\n".join(skipped_list) + "\n\n"
    
    if failed_list:
        log_message += "**安装失败：**\n" + "\n".join(failed_list) + "\n\n"
    
    # 记录到日志
    log_to_daily(log_message)
    
    # 更新状态
    state['last_skill_explore'] = datetime.now().strftime('%Y-%m-%d')
    state['last_keyword_index'] = keyword_index
    save_state(state)
    
    # 输出总结
    print(f"\n=== 总结 ===")
    print(f"成功安装: {installed_count} 个")
    print(f"已安装跳过: {skipped_count} 个")
    print(f"安装失败: {failed_count} 个")
    
    if installed_count > 0:
        print(f"\n✨ 今天安装了 {installed_count} 个新技能！")
        return "SKILLS_INSTALLED:" + str(installed_count)
    else:
        return "SKILLS_OK"

if __name__ == "__main__":
    result = main()
    print(f"\n输出: {result}")
