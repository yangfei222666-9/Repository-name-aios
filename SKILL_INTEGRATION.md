# AIOS Skill 集成指南

## 概述

AIOS 现在可以自动调用 OpenClaw 的所有 skill 来解决问题。

## 已集成的 Skill（20个）

### 系统监控类
- `system-resource-monitor` - 系统资源监控
- `server-health` - 服务器健康检查
- `monitoring` - 通用监控

### 自动化类
- `automation-workflows` - 自动化工作流
- `windows-ui-automation` - Windows UI 自动化
- `file-organizer-skill` - 文件整理

### 开发工具类
- `github` - GitHub 集成
- `ripgrep` - 快速文本搜索
- `sysadmin-toolbox` - 系统管理工具箱

### 信息收集类
- `ai-news-collectors` - AI 新闻收集
- `news-summary` - 新闻摘要
- `web-monitor` - 网页监控
- `tavily-search` - AI 搜索
- `baidu-search` - 百度搜索

### 任务管理类
- `todoist` - 待办事项管理
- `agent-team-orchestration` - Agent 团队协作

### 实用工具类
- `screenshot` - 截图工具
- `find-skills` - 查找 skill
- `daily-briefing` - 每日简报
- `hz-error-guard` - 错误防护

---

## 使用方法

### 1. 列出所有 Skill

```python
from core.skill_manager import get_skill_manager

manager = get_skill_manager()
skills = manager.list_skills()

for skill in skills:
    print(f"{skill['name']}: {skill['description']}")
```

### 2. 调用 Skill

```python
# 调用系统资源监控
result = manager.call_skill("system-resource-monitor", command="check")

if result["success"]:
    print(result["stdout"])
else:
    print(f"Error: {result['error']}")
```

### 3. 搜索 Skill

```python
# 搜索监控相关的 skill
results = manager.search_skills("monitor")

for result in results:
    print(result['name'])
```

### 4. 自动解决问题

```python
from core.skill_integration import get_skill_integration

integration = get_skill_integration()

# 自动解决资源高占用问题
result = integration.auto_solve("resource_high")

if result["success"]:
    print(f"使用 {result['skill']} 解决了问题")
```

---

## AIOS 自动调用

AIOS 会根据事件类型自动调用合适的 skill：

### 事件 → Skill 映射

| 事件类型 | 自动调用的 Skill |
|---------|----------------|
| `resource.cpu_spike` | system-resource-monitor, server-health |
| `resource.memory_high` | system-resource-monitor, server-health |
| `resource.disk_full` | file-organizer-skill |
| `agent.error` | github |
| `sensor.news` | ai-news-collectors, news-summary |
| `sensor.web_change` | web-monitor |

### 问题类型 → Skill 映射

| 问题类型 | 推荐的 Skill |
|---------|-------------|
| `resource_high` | system-resource-monitor, server-health |
| `disk_full` | file-organizer-skill |
| `code_review` | github |
| `news_update` | ai-news-collectors, news-summary |
| `todo_check` | todoist |
| `screenshot_needed` | screenshot |
| `automation_task` | automation-workflows |
| `ui_automation` | windows-ui-automation |

---

## 集成到 Reactor

在 Reactor 中自动调用 skill：

```python
from core.skill_integration import get_skill_integration

class ProductionReactor:
    def __init__(self):
        self.skill_integration = get_skill_integration()
    
    def execute(self, playbook, event):
        # 获取推荐的 skill
        skills = self.skill_integration.get_skill_for_event(event["type"])
        
        if skills:
            # 尝试用 skill 解决
            result = self.skill_integration.auto_solve(
                problem_type=self._event_to_problem(event["type"]),
                context=event
            )
            
            if result["success"]:
                print(f"✅ Skill {result['skill']} 解决了问题")
                return result
        
        # 否则执行 playbook
        return self._execute_playbook(playbook)
```

---

## 添加新 Skill

### 1. 创建 Skill 目录

```
skills/
└── my-skill/
    ├── SKILL.md          # 说明文档
    ├── skill.py          # 主程序
    └── requirements.txt  # 依赖（可选）
```

### 2. 编写 SKILL.md

```markdown
# My Skill

这是一个示例 skill。

## 使用方法

\`\`\`bash
python skill.py check
\`\`\`
```

### 3. 编写 skill.py

```python
#!/usr/bin/env python3
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: skill.py <command>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        print("✅ Check passed")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 4. 注册到 AIOS

在 `skill_integration.py` 中添加映射：

```python
self.skill_mapping = {
    # ... 现有映射 ...
    "my_problem": ["my-skill"],
}
```

---

## 最佳实践

1. **Skill 应该快速执行** - 超过 30 秒会超时
2. **返回清晰的输出** - stdout 应该包含有用信息
3. **错误处理** - 失败时返回非零退出码
4. **文档完善** - SKILL.md 应该包含使用说明
5. **幂等性** - 多次执行应该产生相同结果

---

## 故障排查

### Skill 找不到

检查 skill 目录是否存在 SKILL.md：

```bash
ls C:\Users\A\.openclaw\workspace\skills\<skill-name>\SKILL.md
```

### Skill 执行失败

查看错误信息：

```python
result = manager.call_skill("my-skill")
print(result["stderr"])
```

### Skill 超时

增加超时时间（修改 skill_manager.py）：

```python
result = subprocess.run(
    cmd,
    timeout=60  # 改为 60 秒
)
```

---

**现在 AIOS 拥有 20 个 skill 的能力！** 🎯
