"""
Hexagram State Machine Visualizer - 卦象状态机可视化

基于真实数据生成状态转移图（Mermaid）
"""

from pathlib import Path
from collections import Counter
from hexagram_logger import HEXAGRAM_HISTORY_FILE
import json


def generate_state_machine_diagram(min_transitions: int = 2, output_file: str = None):
    """
    生成卦象状态机图（Mermaid格式）
    
    Args:
        min_transitions: 最小转移次数（过滤低频转移）
        output_file: 输出文件路径（默认：reports/hexagram_state_machine.md）
    """
    if output_file is None:
        output_file = Path(__file__).parent.parent / "reports" / "hexagram_state_machine.md"
    
    # 读取历史数据
    if not HEXAGRAM_HISTORY_FILE.exists():
        print("No hexagram history data found.")
        return None
    
    hexagrams = []
    with open(HEXAGRAM_HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                hexagrams.append(record["hexagram"])
    
    # 统计转移频率
    transitions = []
    for i in range(len(hexagrams) - 1):
        from_hex = hexagrams[i]
        to_hex = hexagrams[i + 1]
        if from_hex != to_hex:  # 跳过自循环
            transitions.append((from_hex, to_hex))
    
    transition_counts = Counter(transitions)
    
    # 过滤低频转移
    filtered_transitions = {
        (from_hex, to_hex): count
        for (from_hex, to_hex), count in transition_counts.items()
        if count >= min_transitions
    }
    
    # 生成 Mermaid 图
    lines = []
    lines.append("# AIOS Hexagram State Machine\n")
    lines.append("**Auto-generated from real system data**\n")
    lines.append("---\n")
    lines.append("## State Transition Diagram\n")
    lines.append("```mermaid")
    lines.append("stateDiagram-v2")
    
    # 添加转移
    for (from_hex, to_hex), count in sorted(filtered_transitions.items(), key=lambda x: -x[1]):
        lines.append(f"    {from_hex} --> {to_hex}: {count}次")
    
    lines.append("```\n")
    
    # 添加统计
    lines.append("## Transition Statistics\n")
    lines.append(f"- Total transitions: {len(transitions)}")
    lines.append(f"- Unique transitions: {len(transition_counts)}")
    lines.append(f"- Filtered transitions (≥{min_transitions}): {len(filtered_transitions)}")
    lines.append(f"- Most common: {transition_counts.most_common(1)[0] if transition_counts else 'N/A'}\n")
    
    # 写入文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return output_file


if __name__ == "__main__":
    print("Generating Hexagram State Machine Diagram...")
    output = generate_state_machine_diagram(min_transitions=1)
    
    if output:
        print(f"✅ Diagram saved: {output}")
    else:
        print("❌ No data available")
