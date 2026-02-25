"""
AIOS Memory Palace API
可插拔的记忆系统 - 支持文件系统、向量数据库、图数据库
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class MemoryBackend(Enum):
    """记忆后端类型"""
    JSON = "json"           # 文件系统（默认）
    CHROMA = "chroma"       # 向量数据库
    NEO4J = "neo4j"         # 图数据库


class MemoryAPI:
    """统一的记忆API"""
    
    def __init__(self, backend: MemoryBackend = MemoryBackend.JSON, workspace: Optional[Path] = None):
        self.backend = backend
        self.workspace = workspace or Path(__file__).parent.parent.parent / "memory"
        self.workspace.mkdir(exist_ok=True)
        
        # 后端实例
        self._backend_instance = None
        self._init_backend()
    
    def _init_backend(self):
        """初始化后端"""
        if self.backend == MemoryBackend.JSON:
            self._backend_instance = JSONBackend(self.workspace)
        elif self.backend == MemoryBackend.CHROMA:
            # TODO: 实现 Chroma 后端
            raise NotImplementedError("Chroma backend not implemented yet")
        elif self.backend == MemoryBackend.NEO4J:
            # TODO: 实现 Neo4j 后端
            raise NotImplementedError("Neo4j backend not implemented yet")
    
    def store_lesson(self, category: str, pattern: str, lesson: str, **metadata) -> str:
        """存储教训
        
        Args:
            category: 错误类别（encoding/path/permission等）
            pattern: 错误模式
            lesson: 教训内容
            **metadata: 额外元数据（severity/source等）
        
        Returns:
            lesson_id: 教训ID
        """
        lesson_data = {
            "id": f"{category}_{int(datetime.now().timestamp())}",
            "category": category,
            "pattern": pattern,
            "lesson": lesson,
            "timestamp": datetime.now().isoformat(),
            "confidence": "draft",
            **metadata
        }
        
        return self._backend_instance.store(lesson_data)
    
    def find_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """查找相似教训
        
        Args:
            query: 查询文本（错误消息、问题描述等）
            limit: 返回结果数量
        
        Returns:
            相似教训列表
        """
        return self._backend_instance.query(query, limit)
    
    def link(self, entity1: str, entity2: str, relation: str):
        """建立实体关系
        
        Args:
            entity1: 实体1（错误类型、Agent等）
            entity2: 实体2
            relation: 关系类型（causes/fixes/related_to等）
        """
        return self._backend_instance.link(entity1, entity2, relation)
    
    def switch_backend(self, backend: MemoryBackend):
        """切换后端
        
        Args:
            backend: 新的后端类型
        """
        self.backend = backend
        self._init_backend()
    
    async def store_lesson_async(self, category: str, pattern: str, lesson: str, **metadata) -> str:
        """异步存储教训（用于心跳调用）"""
        # TODO: 实现异步版本
        return self.store_lesson(category, pattern, lesson, **metadata)


class JSONBackend:
    """JSON文件后端"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.lessons_file = workspace / "lessons.json"
        self.links_file = workspace / "links.json"
        
        # 加载现有数据
        self.lessons = self._load_lessons()
        self.links = self._load_links()
    
    def _load_lessons(self) -> Dict:
        """加载教训库"""
        if not self.lessons_file.exists():
            return {"lessons": [], "rules_derived": []}
        
        with open(self.lessons_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 兼容旧格式
            if isinstance(data, dict) and 'lessons' in data:
                return data
            return {"lessons": data if isinstance(data, list) else []}
    
    def _load_links(self) -> List:
        """加载关系链接"""
        if not self.links_file.exists():
            return []
        
        with open(self.links_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_lessons(self):
        """保存教训库"""
        with open(self.lessons_file, 'w', encoding='utf-8') as f:
            json.dump(self.lessons, f, indent=2, ensure_ascii=False)
    
    def _save_links(self):
        """保存关系链接"""
        with open(self.links_file, 'w', encoding='utf-8') as f:
            json.dump(self.links, f, indent=2, ensure_ascii=False)
    
    def store(self, lesson_data: Dict) -> str:
        """存储教训"""
        # 检查是否已存在
        lesson_id = lesson_data['id']
        existing = [l for l in self.lessons['lessons'] if l.get('id') == lesson_id]
        
        if existing:
            # 更新现有教训
            idx = self.lessons['lessons'].index(existing[0])
            self.lessons['lessons'][idx] = lesson_data
        else:
            # 添加新教训
            self.lessons['lessons'].append(lesson_data)
        
        self._save_lessons()
        return lesson_id
    
    def query(self, query: str, limit: int = 5) -> List[Dict]:
        """查询相似教训（简单文本匹配）"""
        query_lower = query.lower()
        results = []
        
        for lesson in self.lessons['lessons']:
            # 简单的关键词匹配
            score = 0
            if query_lower in lesson.get('pattern', '').lower():
                score += 2
            if query_lower in lesson.get('lesson', '').lower():
                score += 1
            if query_lower in lesson.get('category', '').lower():
                score += 1
            
            if score > 0:
                results.append({
                    **lesson,
                    'score': score
                })
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def link(self, entity1: str, entity2: str, relation: str):
        """建立关系链接"""
        link = {
            "from": entity1,
            "to": entity2,
            "relation": relation,
            "timestamp": datetime.now().isoformat()
        }
        
        # 检查是否已存在
        existing = [l for l in self.links if 
                   l['from'] == entity1 and l['to'] == entity2 and l['relation'] == relation]
        
        if not existing:
            self.links.append(link)
            self._save_links()


# 全局单例
_memory_instance = None

def get_memory(backend: MemoryBackend = MemoryBackend.JSON) -> MemoryAPI:
    """获取Memory API单例"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MemoryAPI(backend)
    return _memory_instance


# 便捷导出
memory = get_memory()
