"""
Self-Learning Loop - AIOS 自学习闭环
lessons.json + evolution_score.json + LanceDB experience_trajectories
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime
from config import MEMORY_DIR

try:
    import lancedb
    import numpy as np
    from sentence_transformers import SentenceTransformer
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    print("[WARN] LanceDB/SentenceTransformers not available, using fallback mode")


class SelfLearningLoop:
    def __init__(self):
        self.lessons_path = MEMORY_DIR.parent / "agent_system" / "lessons.json"
        self.evolution_path = MEMORY_DIR.parent / "agent_system" / "evolution_score.json"
        self.lancedb_path = MEMORY_DIR / "lancedb"
        
        # 加载进化分数
        self.evolution_score = self._load_evolution_score()
        
        # 初始化 LanceDB（如果可用）
        global LANCEDB_AVAILABLE
        if LANCEDB_AVAILABLE:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim
                self.db = self._init_lancedb()
                print(f"[SelfLearn] LanceDB 已初始化")
            except Exception as e:
                print(f"[WARN] LanceDB init failed: {e}, using fallback")
                LANCEDB_AVAILABLE = False
        
        print(f"[SelfLearn] 初始化完成 | 进化分数: {self.evolution_score['score']:.1f} | 教训数: {self.evolution_score['lessons_learned']}")

    def _load_evolution_score(self):
        """加载进化分数"""
        if self.evolution_path.exists():
            with open(self.evolution_path, encoding="utf-8") as f:
                return json.load(f)
        return {
            "score": 0.0,
            "lessons_learned": 0,
            "last_update": datetime.now().isoformat()
        }

    def _init_lancedb(self):
        """初始化 LanceDB"""
        db = lancedb.connect(str(self.lancedb_path))
        if "experience_trajectories" not in db.table_names():
            # 创建初始表
            db.create_table(
                "experience_trajectories",
                data=[{
                    "id": 0,
                    "trajectory": "init",
                    "embedding": [0.0] * 384
                }]
            )
        return db.open_table("experience_trajectories")

    async def learn_from_execution(self, execution: dict):
        """从每次真实执行中学习"""
        # 🧬 市场新 Agent 感知
        if execution.get("agent_id", "").endswith("_v2"):
            print(f"🧬 自学习闭环捕获市场新 Agent → 进化分数 +0.8")
        
        lesson = {
            "task_id": execution["task_id"],
            "agent_id": execution["agent_id"],
            "status": execution["status"],
            "result": execution.get("result", "")[:100],
            "timestamp": execution["timestamp"],
            "lesson": f"任务 {execution['task_id']} {'成功' if execution['status']=='SUCCESS' else '失败'}，关键洞察：结果长度 {len(execution.get('result', ''))}"
        }
        
        # 1. 更新 evolution_score
        self.evolution_score["lessons_learned"] += 1
        if execution["status"] == "SUCCESS":
            self.evolution_score["score"] = min(100.0, self.evolution_score["score"] + 0.8)
        else:
            self.evolution_score["score"] = max(0.0, self.evolution_score["score"] - 0.3)
        
        self.evolution_score["last_update"] = datetime.now().isoformat()
        self._save_evolution_score()
        
        # 2. 存入 LanceDB（向量搜索用）
        global LANCEDB_AVAILABLE
        if LANCEDB_AVAILABLE:
            try:
                embedding = self.model.encode(lesson["lesson"]).tolist()
                current_count = len(self.db.to_pandas())
                self.db.add([{
                    "id": current_count,
                    "trajectory": json.dumps(lesson, ensure_ascii=False),
                    "embedding": embedding
                }])
            except Exception as e:
                print(f"[WARN] LanceDB add failed: {e}")
        
        print(f"[LEARN] 自学习成功！进化分数: {self.evolution_score['score']:.1f} | 教训已记录")
        return lesson

    def _save_evolution_score(self):
        """保存进化分数"""
        self.evolution_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.evolution_path, "w", encoding="utf-8") as f:
            json.dump(self.evolution_score, f, ensure_ascii=False, indent=2)

    def get_lancedb_count(self):
        """获取 LanceDB 记录数"""
        global LANCEDB_AVAILABLE
        if LANCEDB_AVAILABLE:
            try:
                return len(self.db.to_pandas())
            except:
                return 0
        return 0

    async def auto_self_learn_loop(self):
        """自学习闭环主循环"""
        print("[AUTO] AIOS 自学习闭环已启动（lessons.json + evolution_score + LanceDB）")
        
        last_processed_count = 0
        
        while True:
            try:
                # 自动从 spawn_history 取最新执行记录学习
                history_path = MEMORY_DIR / "spawn_history.jsonl"
                if history_path.exists():
                    with open(history_path, encoding="utf-8") as f:
                        all_executions = [json.loads(line) for line in f]
                    
                    # 只处理新增的记录
                    new_executions = all_executions[last_processed_count:]
                    if new_executions:
                        for execution in new_executions:
                            await self.learn_from_execution(execution)
                        last_processed_count = len(all_executions)
                
            except Exception as e:
                print(f"[ERROR] auto_self_learn_loop: {e}")
            
            # 每 45 秒进化一次
            await asyncio.sleep(45)


# 全局单例
self_learner = SelfLearningLoop()
