"""
模拟卦象演化数据 - 用于测试 Timeline 可视化

生成 3-5 天的模拟数据，展示系统从稳定到高负载再恢复的完整周期。
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add policy to path
sys.path.insert(0, str(Path(__file__).parent.parent / "policy"))
from hexagram_logger import append_hexagram_state

# 模拟系统演化路径（参考珊瑚海的建议）
EVOLUTION_PATH = [
    # Day 1: 稳定期
    ("坤", "坤", "坤", 0.92, 8.5, 0.15),   # 稳定
    ("坤", "坤", "坤", 0.93, 8.2, 0.12),
    ("坤", "坤", "坤", 0.91, 9.1, 0.18),
    
    # Day 2: 协作增强
    ("兑", "坤", "临", 0.89, 10.3, 0.22),  # 协作
    ("兑", "坤", "临", 0.90, 11.2, 0.25),
    ("兑", "兑", "兑", 0.88, 12.5, 0.28),  # 协同愉快
    
    # Day 3: 负载上升
    ("震", "坤", "豫", 0.85, 15.8, 0.35),  # 准备就绪
    ("震", "震", "震", 0.82, 18.3, 0.42),  # 连续冲击
    ("离", "震", "丰", 0.79, 22.1, 0.48),  # 高产出
    
    # Day 4: 高负载期
    ("离", "离", "离", 0.75, 28.5, 0.55),  # 极高负载
    ("离", "坎", "既济", 0.73, 31.2, 0.58), # 任务完成
    ("坎", "离", "未济", 0.70, 35.8, 0.62), # 任务未完成
    
    # Day 5: 风险期
    ("坎", "坎", "坎", 0.68, 42.3, 0.68),  # 深度风险
    ("坎", "坤", "比", 0.71, 38.5, 0.65),  # 协作运行
    ("震", "坤", "豫", 0.74, 32.1, 0.58),  # 准备恢复
    
    # Day 6: 恢复期
    ("坤", "震", "复", 0.78, 25.3, 0.48),  # 系统恢复
    ("坤", "坤", "坤", 0.82, 18.7, 0.35),  # 回归稳定
    ("坤", "坤", "坤", 0.86, 12.5, 0.25),
    
    # Day 7: 稳定期
    ("坤", "坤", "坤", 0.89, 9.8, 0.18),
    ("坤", "坤", "坤", 0.91, 8.3, 0.15),
    ("坤", "坤", "坤", 0.92, 7.9, 0.12),
]


def simulate_hexagram_evolution():
    """
    模拟 7 天的卦象演化数据
    """
    print("Simulating Hexagram Evolution (7 days)...")
    print("=" * 60)
    
    base_time = datetime.now() - timedelta(days=7)
    
    for i, (upper, lower, hexagram, sr, latency, debate) in enumerate(EVOLUTION_PATH):
        # 计算时间戳（每天 3-4 条记录）
        day_offset = i // 3
        hour_offset = (i % 3) * 8  # 每 8 小时一条
        timestamp = base_time + timedelta(days=day_offset, hours=hour_offset)
        
        # 添加随机波动
        sr_jitter = sr + random.uniform(-0.02, 0.02)
        latency_jitter = latency + random.uniform(-1.5, 1.5)
        debate_jitter = debate + random.uniform(-0.03, 0.03)
        
        # 记录到历史文件
        record = append_hexagram_state(
            trigram_upper=upper,
            trigram_lower=lower,
            hexagram=hexagram,
            success_rate=max(0.0, min(1.0, sr_jitter)),
            latency=max(0.0, latency_jitter),
            debate_rate=max(0.0, min(1.0, debate_jitter))
        )
        
        # 修改时间戳（手动覆盖）
        import json
        history_file = Path(__file__).parent.parent / "data" / "hexagram_history.jsonl"
        with open(history_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 修改最后一行的时间戳
        if lines:
            last_record = json.loads(lines[-1])
            last_record["timestamp"] = timestamp.isoformat()
            lines[-1] = json.dumps(last_record, ensure_ascii=False) + "\n"
            
            with open(history_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
        
        print(f"Day {day_offset + 1} | {hexagram:6s} | SR={sr:.2%} | Latency={latency:.1f}s")
    
    print("\n✅ Simulation complete!")
    print(f"   Total records: {len(EVOLUTION_PATH)}")
    print(f"   Time span: 7 days")
    print(f"   Evolution path: 坤 → 临 → 兑 → 豫 → 震 → 丰 → 离 → 既济 → 未济 → 坎 → 比 → 豫 → 复 → 坤")


if __name__ == "__main__":
    simulate_hexagram_evolution()
    
    # 生成报告
    print("\n" + "=" * 60)
    print("Generating Timeline Report...")
    
    from hexagram_timeline import generate_timeline_report, print_timeline_summary
    
    output = generate_timeline_report()
    print(f"✅ Report saved: {output}")
    
    print("\n" + "=" * 60)
    print_timeline_summary()
