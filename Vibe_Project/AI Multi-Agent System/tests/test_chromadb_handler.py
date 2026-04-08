"""
ChromaDB Handler单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.vectorstore.chromadb_handler import ChromaDBHandler


class TestChromaDBHandler:
    """ChromaDB处理器测试"""

    def setup_method(self):
        """每个测试前创建处理器"""
        self.handler = ChromaDBHandler(
            persist_directory="G:/claude_code_project/data/chromadb/test",
            collection_name="test_collection"
        )

    def test_initialization(self):
        """测试初始化"""
        assert self.handler is not None
        assert self.handler.collection_name == "test_collection"
        assert self.handler.persist_directory == "G:/claude_code_project/data/chromadb/test"

    def test_get_collection_stats(self):
        """测试获取集合统计"""
        stats = self.handler.get_collection_stats()

        assert "name" in stats
        assert "count" in stats
        assert stats["name"] == "test_collection"

    def test_add_documents(self):
        """测试添加文档"""
        ids = self.handler.add_documents(
            texts=["Test document 1", "Test document 2"],
            metadatas=[
                {"source": "test1.txt"},
                {"source": "test2.txt"}
            ],
            ids=["test_doc_1", "test_doc_2"]
        )

        assert len(ids) == 2
        assert ids == ["test_doc_1", "test_doc_2"]

    def test_similarity_search(self):
        """测试相似性搜索"""
        # 先添加文档
        self.handler.add_documents(
            texts=["Python is a programming language"],
            metadatas=[{"source": "python.txt"}],
            ids=["test_python"]
        )

        # 搜索
        results = self.handler.similarity_search(
            query="programming language",
            k=5
        )

        assert len(results) > 0
        assert "content" in results[0]
        assert "similarity_score" in results[0]

    def test_delete_document(self):
        """测试删除文档"""
        # 先添加文档
        self.handler.add_documents(
            texts=["Document to be deleted"],
            metadatas=[{"source": "delete_test.txt"}],
            ids=["delete_test_doc"]
        )

        # 验证存在
        stats_before = self.handler.get_collection_stats()
        count_before = stats_before["count"]

        # 删除
        success = self.handler.delete_document("delete_test_doc")
        assert success == True

    def test_delete_document_not_found(self):
        """测试删除不存在的文档"""
        success = self.handler.delete_document("nonexistent_doc_12345")
        # ChromaDB delete不会抛出异常，即使ID不存在
        assert success == True

    def test_delete_by_filter(self):
        """测试按过滤条件删除"""
        # 先添加文档
        self.handler.add_documents(
            texts=["Filter test 1", "Filter test 2"],
            metadatas=[
                {"source": "filter_test.txt", "category": "test"},
                {"source": "filter_test.txt", "category": "other"}
            ],
            ids=["filter_doc_1", "filter_doc_2"]
        )

        # 按source过滤删除
        deleted_count = self.handler.delete_by_filter(
            {"source": "filter_test.txt"}
        )

        # 至少删除了2个文档
        assert deleted_count >= 2


class TestChromaDBHandlerEdgeCases:
    """ChromaDB边界情况测试"""

    def setup_method(self):
        """每个测试前创建处理器"""
        self.handler = ChromaDBHandler(
            persist_directory="G:/claude_code_project/data/chromadb/edge_test",
            collection_name="edge_test_collection"
        )

    def test_empty_search(self):
        """测试空查询"""
        results = self.handler.similarity_search(
            query="nonexistent content xyz123",
            k=5
        )
        # 可能返回空结果或低分结果
        assert isinstance(results, list)

    def test_large_k(self):
        """测试大k值"""
        results = self.handler.similarity_search(
            query="test",
            k=100
        )
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
