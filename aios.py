#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS CLI - 命令行工具
统一管理 AIOS 系统
"""
import sys
import os
import argparse
import subprocess
from pathlib import Path
import json
import time

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# AIOS 根目录
AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))


class AIOSCLI:
    """AIOS 命令行工具"""
    
    def __init__(self):
        self.python = "C:\\Program Files\\Python312\\python.exe"
        self.aios_root = AIOS_ROOT
    
    def status(self):
        """查看 AIOS 状态"""
        print("=" * 60)
        print("AIOS 系统状态")
        print("=" * 60)
        
        # 检查组件状态
        print("\n📦 组件状态:")
        
        components = {
            "EventBus": self.aios_root / "core" / "event_bus.py",
            "Scheduler": self.aios_root / "core" / "production_scheduler.py",
            "Reactor": self.aios_root / "core" / "production_reactor.py",
            "Dashboard": self.aios_root / "dashboard" / "server.py",
        }
        
        for name, path in components.items():
            status = "✅" if path.exists() else "❌"
            print(f"   {status} {name}")
        
        # 检查性能数据
        perf_file = self.aios_root / "data" / "performance_stats.jsonl"
        if perf_file.exists():
            with open(perf_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n📊 性能数据: {len(lines)} 条记录")
        
        # 检查事件数据
        events_file = self.aios_root / "events" / "events.jsonl"
        if events_file.exists():
            with open(events_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"📝 事件数据: {len(lines)} 条记录")
        
        print("\n" + "=" * 60)
    
    def start(self):
        """启动 AIOS 服务"""
        print("🚀 启动 AIOS 服务...")
        
        # 预热组件
        print("\n1. 预热组件...")
        result = subprocess.run(
            [self.python, "-X", "utf8", str(self.aios_root / "warmup.py")],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✅ 组件预热完成")
        else:
            print(f"   ❌ 预热失败: {result.stderr}")
            return
        
        # 启动 Dashboard
        print("\n2. 启动 Dashboard...")
        print("   访问: http://127.0.0.1:9091")
        print("   按 Ctrl+C 停止")
        
        try:
            subprocess.run(
                [self.python, "-X", "utf8", str(self.aios_root / "dashboard" / "server.py")],
                cwd=str(self.aios_root / "dashboard")
            )
        except KeyboardInterrupt:
            print("\n\n✅ Dashboard 已停止")
    
    def stop(self):
        """停止 AIOS 服务"""
        print("🛑 停止 AIOS 服务...")
        
        # 查找并停止 Python 进程
        import psutil
        
        stopped = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'python' in proc.info['name'].lower():
                    if any('aios' in str(arg).lower() for arg in cmdline):
                        proc.terminate()
                        stopped += 1
                        print(f"   ✅ 停止进程 {proc.info['pid']}")
            except:
                pass
        
        if stopped == 0:
            print("   ℹ️ 没有运行中的 AIOS 进程")
        else:
            print(f"\n✅ 已停止 {stopped} 个进程")
    
    def dashboard(self):
        """打开 Dashboard"""
        print("🌐 启动 Dashboard...")
        
        # 启动服务器
        print("   服务器启动中...")
        subprocess.Popen(
            [self.python, "-X", "utf8", str(self.aios_root / "dashboard" / "server.py")],
            cwd=str(self.aios_root / "dashboard")
        )
        
        time.sleep(1)
        
        # 打开浏览器
        import webbrowser
        webbrowser.open("http://127.0.0.1:9091")
        
        print("   ✅ Dashboard 已启动")
        print("   访问: http://127.0.0.1:9091")
        print("   实时推送: 已启用")
        print("\n   按 Ctrl+C 停止服务器")
    
    def analyze(self):
        """性能分析"""
        print("📊 运行性能分析...")
        
        result = subprocess.run(
            [self.python, "-X", "utf8", str(self.aios_root / "analyze_performance.py")],
            cwd=str(self.aios_root)
        )
        
        if result.returncode == 0:
            print("\n✅ 分析完成")
        else:
            print("\n❌ 分析失败")
    
    def test(self):
        """运行测试"""
        print("🧪 运行测试...")
        
        result = subprocess.run(
            [self.python, "-m", "pytest", "tests/", "-v"],
            cwd=str(self.aios_root)
        )
        
        if result.returncode == 0:
            print("\n✅ 所有测试通过")
        else:
            print("\n❌ 测试失败")
    
    def warmup(self):
        """预热组件"""
        print("🔥 预热组件...")
        
        result = subprocess.run(
            [self.python, "-X", "utf8", str(self.aios_root / "warmup.py")],
            cwd=str(self.aios_root)
        )
        
        if result.returncode == 0:
            print("\n✅ 预热完成")
        else:
            print("\n❌ 预热失败")
    
    def heartbeat(self):
        """运行心跳"""
        print("💓 运行心跳...")
        
        result = subprocess.run(
            [self.python, "-X", "utf8", str(self.aios_root / "heartbeat_runner_optimized.py")],
            cwd=str(self.aios_root)
        )
    
    def monitor(self, duration=5):
        """实时监控"""
        print(f"👀 启动实时监控（{duration} 分钟）...")
        
        result = subprocess.run(
            [self.python, "-X", "utf8", str(self.aios_root / "monitor_live.py"),
             "--duration", str(duration)],
            cwd=str(self.aios_root)
        )
    
    def benchmark(self):
        """性能基准测试"""
        print("⚡ 运行性能基准测试...")
        
        result = subprocess.run(
            [self.python, "-X", "utf8", str(self.aios_root / "benchmark_heartbeat.py")],
            cwd=str(self.aios_root)
        )
    
    def demo(self):
        """运行演示"""
        print("🎬 AIOS 演示")
        print("=" * 60)
        print("\n选择演示场景：")
        print("  1. 简单演示（10秒快速体验）")
        print("  2. API 健康检查（真实场景，20秒）")
        print("\n默认运行场景 2（API 健康检查）")
        print("=" * 60)
        
        # 默认运行 API 健康检查
        result = subprocess.run(
            [self.python, "-X", "utf8", str(self.aios_root / "demo_api_health.py")],
            cwd=str(self.aios_root)
        )
        
        if result.returncode == 0:
            print("\n✅ 演示完成")
        else:
            print("\n❌ 演示失败")
    
    def version(self):
        """显示版本信息"""
        print("AIOS CLI v1.0")
        print("AIOS v0.6 (预热版)")
        print(f"路径: {self.aios_root}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AIOS CLI - 统一管理 AIOS 系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  aios status              查看系统状态
  aios demo                运行完整演示（推荐首次使用）
  aios start               启动 AIOS 服务
  aios stop                停止 AIOS 服务
  aios dashboard           打开 Dashboard
  aios analyze             性能分析
  aios test                运行测试
  aios warmup              预热组件
  aios heartbeat           运行心跳
  aios monitor             实时监控（5分钟）
  aios monitor --duration 10  实时监控（10分钟）
  aios benchmark           性能基准测试
  aios version             显示版本信息
        """
    )
    
    parser.add_argument(
        "command",
        choices=["status", "start", "stop", "dashboard", "demo", "analyze", "test",
                 "warmup", "heartbeat", "monitor", "benchmark", "version"],
        help="要执行的命令"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="监控时长（分钟），默认 5"
    )
    
    args = parser.parse_args()
    
    cli = AIOSCLI()
    
    # 执行命令
    if args.command == "status":
        cli.status()
    elif args.command == "demo":
        cli.demo()
    elif args.command == "start":
        cli.start()
    elif args.command == "stop":
        cli.stop()
    elif args.command == "dashboard":
        cli.dashboard()
    elif args.command == "analyze":
        cli.analyze()
    elif args.command == "test":
        cli.test()
    elif args.command == "warmup":
        cli.warmup()
    elif args.command == "heartbeat":
        cli.heartbeat()
    elif args.command == "monitor":
        cli.monitor(args.duration)
    elif args.command == "benchmark":
        cli.benchmark()
    elif args.command == "version":
        cli.version()


if __name__ == "__main__":
    main()
