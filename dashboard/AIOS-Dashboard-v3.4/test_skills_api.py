"""测试 Skills API"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入 server
from server import RealDataHandler

# 创建实例
handler = RealDataHandler(None, None, None)

# 测试
result = handler.get_skills_list()
print(f"Skills count: {len(result['skills'])}")

if result['skills']:
    print("\nFirst 5 skills:")
    for skill in result['skills'][:5]:
        print(f"  - {skill['name']}: {skill['description'][:50]}...")
else:
    print("\n[ERROR] No skills found!")
    
    # 调试
    skills_dir = Path("C:/Users/A/.openclaw/workspace/skills")
    print(f"\nSkills dir: {skills_dir}")
    print(f"Exists: {skills_dir.exists()}")
    
    if skills_dir.exists():
        dirs = list(skills_dir.iterdir())
        print(f"Total dirs: {len(dirs)}")
        
        # 检查第一个
        if dirs:
            first = dirs[0]
            print(f"\nFirst dir: {first.name}")
            skill_md = first / "SKILL.md"
            print(f"SKILL.md exists: {skill_md.exists()}")
            
            if skill_md.exists():
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read()[:200]
                    print(f"Content preview:\n{content}")
