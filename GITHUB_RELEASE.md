# AIOS v1.0 - 首个公开版本 🚀

**让 AI 系统自己运行、自己看、自己进化！**

---

## ✨ 亮点

- 🎯 **零依赖** - 只需要 Python 3.8+，无需 pip install
- 📊 **完整可观测** - Tracer + Metrics + Logger 三件套
- 🔧 **真实场景** - API 健康检查完整闭环演示
- 🌐 **实时监控** - Dashboard 支持 SSE 实时推送
- ⚡ **高性能** - 心跳延迟 ~3ms，Agent 创建 0.3s

---

## 🚀 快速开始

```bash
# 1. 下载并解压
unzip AIOS-v1.0-demo.zip
cd aios

# 2. 运行演示（20秒）
python aios.py demo

# 3. 启动 Dashboard
python aios.py dashboard
```

**就这么简单！** 🎉

---

## 📦 下载

- **AIOS-v1.0-demo.zip** (0.77 MB)
- 316 个文件
- 零依赖，解压即用

---

## 📖 文档

- [README.md](README.md) - 完整文档
- [RELEASE_NOTES.md](RELEASE_NOTES.md) - 发布说明
- [API.md](API.md) - API 参考

---

## 🎯 使用场景

### 场景 1: API 健康检查

```python
from observability import span, METRICS, get_logger

logger = get_logger("APIMonitor")

with span("health-check"):
    # 检查 API 健康状态
    is_healthy = check_api()
    
    if not is_healthy:
        # 自动修复
        auto_fix_api()
        
    METRICS.inc_counter("api.checks", 1)
```

---

## 🔮 未来计划

- v1.1: 更多真实场景、完整 WebSocket 支持
- v2.0: Agent 市场、多租户支持

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 许可证

MIT License

---

**感谢使用 AIOS！** 🙏
