# AIOS 文档清单

本文档列出 AIOS 项目的所有文档及其用途。

---

## 📚 核心文档

### 1. [README.md](README.md)
**用途：** 项目概览、快速开始、核心特性

**内容：**
- AIOS 简介
- 快速开始指南
- 架构概览
- 核心功能（UnifiedRouter、能力矩阵、2 个核心护栏）
- 实际效果数据
- 使用场景

**适合人群：** 所有用户

---

## 🎯 使用指南

### 2. [agent_system/UNIFIED_ROUTER_GUIDE.md](agent_system/UNIFIED_ROUTER_GUIDE.md)
**用途：** UnifiedRouter 完整使用指南

**内容：**
- 核心概念（三档模式、护栏机制）
- 使用方法（基本使用、环境变量配置）
- 配置选项（参数说明、枚举类型）
- 护栏机制详解（解释性、防抖、预算、失败回退）
- 最佳实践（模式选择、参数设置）
- 代码示例（5 个完整示例）
- 故障排查

**适合人群：** 开发者、运维人员

**关键主题：**
- Simple/Full/Auto 三档模式
- 2 个核心护栏（解释性 + 防抖滞回）
- 决策日志分析
- 自定义护栏

### 3. [dashboard/DASHBOARD_GUIDE.md](dashboard/DASHBOARD_GUIDE.md)
**用途：** Dashboard 实时监控工具使用指南

**内容：**
- 启动方法（3 种方式）
- 界面说明（统计指标、决策卡片）
- 决策卡片解读（5 个典型示例）
- 实时监控（WebSocket、HTTP 轮询）
- 数据分析（API 端点、curl 查询、Python 分析）
- 故障排查（5 个常见问题）
- 高级功能（自定义样式、导出报告）

**适合人群：** 开发者、运维人员、数据分析师

**关键主题：**
- 实时决策卡片
- 统计指标分析
- 决策审计
- WebSocket 实时推送

### 4. [agent_system/DEVELOPER_GUIDE.md](agent_system/DEVELOPER_GUIDE.md)
**用途：** 开发者深度指南

**内容：**
- 架构设计（整体架构、设计原则、数据流）
- 核心组件（UnifiedRouter、CapabilityMatcher、Agent Manager、Learning Layer、Self-Healing Pipeline）
- 扩展指南（添加能力、添加模板、添加护栏、自定义决策）
- 贡献指南（代码规范、提交流程、代码审查）
- 测试指南（单元测试、集成测试、端到端测试）
- 性能优化（5 个优化方案）

**适合人群：** 核心开发者、贡献者

**关键主题：**
- 架构设计
- 扩展机制
- 贡献流程
- 性能优化

---

## 📖 参考文档

### 5. [agent_system/README.md](agent_system/README.md)
**用途：** Agent 系统概览

**内容：**
- 架构概览
- 核心模块（Agent 模板库、Agent 管理器、任务路由引擎、协作编排器）
- 数据结构（Agent 配置、任务分类规则）
- 实现计划
- 使用示例
- 配置文件

**适合人群：** 开发者

### 6. [agent_system/TASK_ROUTER.md](agent_system/TASK_ROUTER.md)
**用途：** 任务路由器详细文档（如果存在）

**内容：**
- 路由算法
- 决策树
- 配置选项

**适合人群：** 开发者

### 7. [core/MODEL_ROUTER.md](core/MODEL_ROUTER.md)
**用途：** 模型路由器文档（如果存在）

**内容：**
- 模型选择策略
- 成本优化
- 性能权衡

**适合人群：** 开发者

---

## 🔧 其他文档

### 8. [EXAMPLES.md](EXAMPLES.md)
**用途：** 代码示例和 CLI 使用（如果存在）

**内容：**
- 完整代码示例
- CLI 命令示例
- 常见用例

**适合人群：** 所有用户

### 9. [CHANGELOG.md](CHANGELOG.md)
**用途：** 版本历史和升级指南（如果存在）

**内容：**
- 版本更新记录
- 破坏性变更
- 升级指南

**适合人群：** 所有用户

### 10. [CONTRIBUTING.md](CONTRIBUTING.md)
**用途：** 贡献指南（如果存在）

**内容：**
- 如何贡献
- 代码规范
- PR 流程

**适合人群：** 贡献者

---

## 📊 文档结构

```
aios/
├── README.md                              # 项目概览
├── DOCUMENTATION.md                       # 本文档（文档清单）
├── EXAMPLES.md                            # 代码示例（待创建）
├── CHANGELOG.md                           # 版本历史（待创建）
├── CONTRIBUTING.md                        # 贡献指南（待创建）
├── agent_system/
│   ├── README.md                          # Agent 系统概览
│   ├── UNIFIED_ROUTER_GUIDE.md            # UnifiedRouter 使用指南 ✅
│   ├── DEVELOPER_GUIDE.md                 # 开发者指南 ✅
│   ├── TASK_ROUTER.md                     # 任务路由器文档（已存在）
│   └── README_AUTO.md                     # 自动化文档（已存在）
├── dashboard/
│   ├── README.md                          # Dashboard 简介（已存在）
│   └── DASHBOARD_GUIDE.md                 # Dashboard 使用指南 ✅
├── core/
│   └── MODEL_ROUTER.md                    # 模型路由器文档（已存在）
└── demo/
    └── README.md                          # 演示文档（已存在）
```

---

## 🎯 文档导航

### 我是新用户，想快速了解 AIOS
→ 阅读 [README.md](README.md)

### 我想使用 UnifiedRouter 进行任务路由
→ 阅读 [UNIFIED_ROUTER_GUIDE.md](agent_system/UNIFIED_ROUTER_GUIDE.md)

### 我想监控路由决策
→ 阅读 [DASHBOARD_GUIDE.md](dashboard/DASHBOARD_GUIDE.md)

### 我想扩展 AIOS 功能
→ 阅读 [DEVELOPER_GUIDE.md](agent_system/DEVELOPER_GUIDE.md)

### 我想贡献代码
→ 阅读 [DEVELOPER_GUIDE.md](agent_system/DEVELOPER_GUIDE.md) 的"贡献指南"章节

### 我遇到了问题
→ 查看各指南的"故障排查"章节

---

## 📝 文档更新记录

### 2025-02-22
- ✅ 更新 README.md（反映最新架构）
- ✅ 创建 UNIFIED_ROUTER_GUIDE.md（完整使用指南）
- ✅ 创建 DASHBOARD_GUIDE.md（Dashboard 使用指南）
- ✅ 创建 DEVELOPER_GUIDE.md（开发者指南）
- ✅ 创建 DOCUMENTATION.md（本文档）

### 待完成
- [ ] 创建 EXAMPLES.md（代码示例）
- [ ] 创建 CHANGELOG.md（版本历史）
- [ ] 创建 CONTRIBUTING.md（贡献指南）
- [ ] 更新 agent_system/README.md（反映最新架构）
- [ ] 添加 API 参考文档
- [ ] 添加部署指南

---

## 🔗 相关链接

- **GitHub 仓库**: https://github.com/yangfei222666-9/aios
- **PyPI 包**: https://pypi.org/project/aios-framework/ (即将发布)
- **问题反馈**: https://github.com/yangfei222666-9/aios/issues
- **讨论区**: https://github.com/yangfei222666-9/aios/discussions

---

## 📧 联系方式

- **作者**: [@shh7799](https://t.me/shh7799)
- **邮箱**: yangfei222666-9@github.com (如果有)

---

**最后更新**: 2025-02-22
