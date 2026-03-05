"""
AIOS Fast/Slow Thinking Router

作者: Grok + 小九
日期: 2026-03-05
版本: v1.0
功能: 根据任务复杂度、Evolution Score、当前卦象智能路由模型
"""

from typing import Literal, TypedDict, Dict, Any
import logging
from pathlib import Path
import json
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

ModelType = Literal["fast", "slow"]  # fast=Sonnet 4.6, slow=Opus 4.6 / o1

class TaskIndicators(TypedDict, total=False):
    needs_code: bool
    high_risk: bool
    est_lines: int
    dependencies: int
    requires_reasoning: bool
    task_description: str  # 用于日志

def get_evolution_score() -> float:
    """从 evolution_state.json 获取 Evolution Score"""
    try:
        state_file = project_root / "agent_system" / "evolution_state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                return state.get('evolution_score', 97.58)
        return 97.58
    except Exception as e:
        logger.warning(f"Failed to get Evolution Score: {e}")
        return 97.58

def get_current_hexagram() -> str:
    """从 pattern_history.jsonl 获取当前卦象"""
    try:
        history_file = project_root / "agent_system" / "data" / "pattern_history.jsonl"
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_record = json.loads(lines[-1])
                    return last_record.get('pattern', '未知')
        return '未知'
    except Exception as e:
        logger.warning(f"Failed to get current hexagram: {e}")
        return '未知'

def route_task(
    task_id: str,
    task_description: str,
    indicators: TaskIndicators
) -> ModelType:
    """
    主路由函数 - 核心逻辑
    """
    # === 1. 基础复杂度计算 ===
    complexity = 0.0
    
    words = len(task_description.split())
    complexity += min(words / 150, 0.4)  # 文字量
    
    if indicators.get("needs_code") and indicators.get("est_lines", 0) > 50:
        complexity += 0.35
    
    if indicators.get("high_risk"):
        complexity += 0.4
    
    if indicators.get("dependencies", 0) > 3:
        complexity += 0.2
    
    if indicators.get("requires_reasoning"):
        complexity += 0.3
    
    # === 2. Evolution Score 强干预（你的核心优势）===
    evolution_conf = get_evolution_score()
    if evolution_conf < 0.90:
        complexity += 0.25  # 低置信强制慢模型
    
    # === 3. 坤卦特殊加成（厚德载物 → 更稳健）===
    current_gua = get_current_hexagram()
    gua_bonus = 0.0
    if current_gua == "坤卦":
        gua_bonus = 0.10
        complexity += gua_bonus
        logger.info(f"🌟 坤卦加成激活 (+0.10) - 当前卦象: {current_gua}")
    
    # === 4. 最终决策 ===
    model_choice: ModelType = "slow" if complexity > 0.65 else "fast"
    
    # 日志记录（便于 Heartbeat 和每日报告追踪）
    log_data = {
        "task_id": task_id,
        "complexity_score": round(complexity, 3),
        "evolution_conf": round(evolution_conf, 3),
        "current_gua": current_gua,
        "gua_bonus": gua_bonus,
        "model": model_choice,
        "reason": "复杂/高风险/低置信/坤卦" if model_choice == "slow" else "简单任务"
    }
    logger.info(f"🚦 Router 决策: {model_choice} | {log_data}")
    
    # 记录到 router_decisions.jsonl
    try:
        log_file = project_root / "agents" / "router" / "router_decisions.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "model": model_choice,
            "complexity": round(complexity, 3),
            "evolution_conf": round(evolution_conf, 3),
            "current_gua": current_gua,
            "gua_bonus": gua_bonus
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.warning(f"Failed to log router decision: {e}")
    
    return model_choice

