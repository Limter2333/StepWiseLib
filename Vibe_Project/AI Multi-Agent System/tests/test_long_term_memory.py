"""
测试长期记忆模块
"""

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.long_term import LongTermMemory, MemoryCategory


class TestLongTermMemory:
    """长期记忆测试"""

    def setup_method(self):
        """每个测试前创建临时数据库"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.memory = LongTermMemory(
            db_path=self.temp_db.name,
            vectorstore_enabled=False  # 禁用向量存储加快测试
        )

    def teardown_method(self):
        """测试后清理"""
        if hasattr(self, 'memory'):
            self.memory.close()
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_add_memory(self):
        """测试添加记忆"""
        memory_id = self.memory.add(
            content="This is a test memory",
            category=MemoryCategory.KNOWLEDGE,
            tags=["test"]
        )

        assert memory_id is not None
        assert memory_id > 0

    def test_get_memory(self):
        """测试获取记忆"""
        memory_id = self.memory.add(
            content="Test memory content",
            category=MemoryCategory.FACT
        )

        item = self.memory.get(memory_id)

        assert item is not None
        assert item.content == "Test memory content"
        assert item.category == MemoryCategory.FACT

    def test_get_nonexistent_memory(self):
        """测试获取不存在的记忆"""
        item = self.memory.get(9999)
        assert item is None

    def test_update_memory(self):
        """测试更新记忆"""
        memory_id = self.memory.add(
            content="Original content",
            category=MemoryCategory.KNOWLEDGE
        )

        success = self.memory.update(
            memory_id,
            content="Updated content",
            summary="New summary"
        )

        assert success is True

        updated = self.memory.get(memory_id)
        assert updated.content == "Updated content"
        assert updated.summary == "New summary"

    def test_delete_memory_soft(self):
        """测试软删除"""
        memory_id = self.memory.add(
            content="To be deleted",
            category=MemoryCategory.KNOWLEDGE
        )

        success = self.memory.delete(memory_id, soft=True)
        assert success is True

        # 软删除后仍能获取（is_active=0）
        item = self.memory.get(memory_id)
        assert item is None  # 查询默认只返回active的

    def test_search_by_query(self):
        """测试关键词搜索"""
        self.memory.add(
            content="Python programming language",
            category=MemoryCategory.KNOWLEDGE
        )
        self.memory.add(
            content="JavaScript web language",
            category=MemoryCategory.KNOWLEDGE
        )
        self.memory.add(
            content="Machine learning with Python",
            category=MemoryCategory.KNOWLEDGE
        )

        results = self.memory.search(query="Python")

        assert len(results) >= 2
        contents = [r.content for r in results]
        assert any("Python" in c for c in contents)

    def test_search_by_category(self):
        """测试按分类搜索"""
        self.memory.add(content="Fact 1", category=MemoryCategory.FACT)
        self.memory.add(content="Fact 2", category=MemoryCategory.FACT)
        self.memory.add(content="Rule 1", category=MemoryCategory.RULE)

        results = self.memory.search(category=MemoryCategory.FACT)

        assert len(results) == 2
        for r in results:
            assert r.category == MemoryCategory.FACT

    def test_get_by_category(self):
        """测试按分类获取"""
        for i in range(3):
            self.memory.add(
                content=f"Knowledge {i}",
                category=MemoryCategory.KNOWLEDGE
            )
        for i in range(2):
            self.memory.add(
                content=f"Experience {i}",
                category=MemoryCategory.EXPERIENCE
            )

        knowledge_items = self.memory.get_by_category(MemoryCategory.KNOWLEDGE)
        assert len(knowledge_items) >= 3

    def test_increment_access(self):
        """测试访问计数"""
        memory_id = self.memory.add(
            content="Frequently accessed",
            category=MemoryCategory.KNOWLEDGE
        )

        initial = self.memory.get(memory_id)
        initial_count = initial.access_count

        self.memory.increment_access(memory_id)

        updated = self.memory.get(memory_id)
        assert updated.access_count == initial_count + 1

    def test_get_stats(self):
        """测试统计"""
        self.memory.add(content="K1", category=MemoryCategory.KNOWLEDGE)
        self.memory.add(content="K2", category=MemoryCategory.KNOWLEDGE)
        self.memory.add(content="E1", category=MemoryCategory.EXPERIENCE)

        stats = self.memory.get_stats()

        assert stats["total_memories"] >= 3
        assert "knowledge" in stats["by_category"]
        assert stats["by_category"]["knowledge"] >= 2

    def test_add_multiple_memories(self):
        """测试批量添加"""
        for i in range(10):
            self.memory.add(
                content=f"Memory {i}",
                category=MemoryCategory.KNOWLEDGE
            )

        stats = self.memory.get_stats()
        assert stats["total_memories"] >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
