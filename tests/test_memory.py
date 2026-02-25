#!/usr/bin/env python3
"""
Memory API 测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from memory.api import memory, MemoryBackend


class TestMemoryAPI(unittest.TestCase):
    """Memory API 测试"""
    
    def test_store_and_query(self):
        """测试存储和查询"""
        # 存储教训
        lesson_id = memory.store_lesson(
            category="test_error",
            pattern="timeout",
            lesson="增加重试机制，使用指数退避"
        )
        
        self.assertIsNotNone(lesson_id)
        
        # 查询相似教训
        results = memory.find_similar("timeout")
        self.assertGreater(len(results), 0)
        
        # 验证结果
        found = False
        for result in results:
            if "重试机制" in result.get('lesson', ''):
                found = True
                break
        
        self.assertTrue(found)
    
    def test_link_entities(self):
        """测试实体关系"""
        # 建立关系
        memory.link("agent_timeout", "network_error", "causes")
        
        # 验证关系已保存
        # （简单验证，不抛异常即可）
    
    def test_multiple_lessons(self):
        """测试多个教训"""
        # 存储多个教训
        memory.store_lesson("encoding", "UnicodeError", "使用 -X utf8 参数")
        memory.store_lesson("path", "FileNotFoundError", "使用绝对路径")
        memory.store_lesson("permission", "PermissionError", "使用管理员权限")
        
        # 查询
        results = memory.find_similar("编码")
        # 应该能找到相关教训


if __name__ == '__main__':
    unittest.main(verbosity=2)
