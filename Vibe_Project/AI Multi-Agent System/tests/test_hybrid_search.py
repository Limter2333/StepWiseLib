"""
测试混合检索模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.retrieval.hybrid_search import (
    KeywordSearcher,
    VectorSearcher,
    HybridSearcher,
    SearchResult
)


class TestKeywordSearcher:
    """关键词搜索引擎测试"""

    def setup_method(self):
        """每个测试前创建searcher"""
        self.searcher = KeywordSearcher()

    def test_index(self):
        """测试索引"""
        documents = [
            {"id": "1", "content": "Python is great", "metadata": {"source": "a"}},
            {"id": "2", "content": "JavaScript is great", "metadata": {"source": "b"}},
        ]
        self.searcher.index(documents)

        assert len(self.searcher.documents) == 2
        assert self.searcher.N == 2

    def test_search_basic(self):
        """测试基本搜索"""
        documents = [
            {"id": "1", "content": "Python programming language", "metadata": {}},
            {"id": "2", "content": "JavaScript web development", "metadata": {}},
            {"id": "3", "content": "Machine learning with Python", "metadata": {}},
        ]
        self.searcher.index(documents)

        results = self.searcher.search("Python", top_k=3)

        assert len(results) <= 3
        # 包含Python的文档应该排名更高
        assert all("python" in r.content.lower() for r in results)

    def test_search_empty(self):
        """测试空结果"""
        documents = [
            {"id": "1", "content": "Python is great", "metadata": {}},
        ]
        self.searcher.index(documents)

        results = self.searcher.search("nonexistent term xyz", top_k=5)
        assert len(results) == 0

    def test_search_top_k(self):
        """测试top_k限制"""
        documents = [
            {"id": str(i), "content": f"Document {i} with python", "metadata": {}}
            for i in range(20)
        ]
        self.searcher.index(documents)

        results = self.searcher.search("python", top_k=5)
        assert len(results) == 5


class TestVectorSearcher:
    """向量搜索引擎测试"""

    def setup_method(self):
        """每个测试前创建searcher"""
        self.searcher = VectorSearcher(dimension=4)

    def test_index(self):
        """测试索引"""
        documents = [
            {"id": "1", "content": "Python is great", "vector": [0.1, 0.2, 0.3, 0.4]},
            {"id": "2", "content": "JavaScript is great", "vector": [0.5, 0.6, 0.7, 0.8]}
        ]
        self.searcher.index(documents)

        assert len(self.searcher.documents) == 2
        assert len(self.searcher.vectors) == 2

    def test_search_with_vectors(self):
        """测试向量搜索"""
        documents = [
            {"id": "1", "content": "Python is great", "vector": [1.0, 0.0, 0.0, 0.0]},
            {"id": "2", "content": "JavaScript is great", "vector": [0.0, 1.0, 0.0, 0.0]},
            {"id": "3", "content": "ML uses Python", "vector": [0.8, 0.1, 0.1, 0.0]}
        ]
        self.searcher.index(documents)

        query_vector = [0.9, 0.1, 0.0, 0.0]
        results = self.searcher.search(query_vector, top_k=3)

        assert len(results) == 3
        # 验证结果包含所有文档
        result_ids = [r.id for r in results]
        assert "1" in result_ids
        assert "2" in result_ids
        assert "3" in result_ids
        # 验证分数是降序排列
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_empty_vectors(self):
        """测试无向量的文档"""
        documents = [
            {"id": "1", "content": "Python is great"}
        ]
        self.searcher.index(documents)

        results = self.searcher.search([0.1, 0.2, 0.3, 0.4], top_k=10)

        # 没有向量数据的文档不返回（因为没有vector可比较）
        assert len(results) == 0

    def test_search_top_k_limit(self):
        """测试top_k限制"""
        documents = [
            {"id": f"doc{i}", "content": f"Doc {i}", "vector": [0.1 * i] * 4}
            for i in range(10)
        ]
        self.searcher.index(documents)

        results = self.searcher.search([0.5, 0.5, 0.5, 0.5], top_k=3)

        assert len(results) == 3


class TestHybridSearcher:
    """混合搜索引擎测试"""

    def setup_method(self):
        """每个测试前创建searcher"""
        self.searcher = HybridSearcher(
            vector_weight=0.5,
            fusion_method="rrf"
        )

    def test_initialization(self):
        """测试初始化"""
        assert self.searcher.vector_weight == 0.5
        assert self.searcher.keyword_weight == 0.5
        assert self.searcher.fusion_method == "rrf"

    def test_search_without_vector(self):
        """测试只有关键词检索"""
        documents = [
            {"id": "1", "content": "Python is great", "metadata": {}},
            {"id": "2", "content": "JavaScript is great", "metadata": {}},
        ]
        self.searcher.index(documents)

        results = self.searcher.search("Python", top_k=5)

        assert len(results) <= 2
        assert all(r.source == "keyword" for r in results)

    def test_rrf_fusion(self):
        """测试RRF融合"""
        self.searcher.fusion_method = "rrf"
        self.searcher.index([
            {"id": "1", "content": "Python programming", "metadata": {}},
            {"id": "2", "content": "JavaScript programming", "metadata": {}},
        ])

        # 模拟向量结果（与关键词结果略有不同顺序）
        vector_results = [
            SearchResult(content="JavaScript programming", score=0.9, source="vector", metadata={}),
            SearchResult(content="Python programming", score=0.8, source="vector", metadata={}),
        ]

        results = self.searcher.search(
            "Python",
            vector_results=vector_results,
            top_k=5
        )

        assert len(results) >= 1
        # 结果应该有hybrid标记
        assert all(r.source == "hybrid" for r in results)

    def test_weighted_fusion(self):
        """测试加权融合"""
        self.searcher.fusion_method = "weighted"
        self.searcher.index([
            {"id": "1", "content": "Python programming", "metadata": {}},
            {"id": "2", "content": "JavaScript programming", "metadata": {}},
        ])

        vector_results = [
            SearchResult(content="Python programming", score=0.9, source="vector", metadata={}),
        ]

        results = self.searcher.search(
            "Python",
            vector_results=vector_results,
            top_k=5
        )

        assert len(results) >= 1

    def test_concat_fusion(self):
        """测试拼接融合"""
        self.searcher.fusion_method = "concat"
        self.searcher.index([
            {"id": "1", "content": "Python programming", "metadata": {}},
            {"id": "2", "content": "JavaScript programming", "metadata": {}},
        ])

        vector_results = [
            SearchResult(content="Python programming", score=0.9, source="vector", metadata={}),
        ]

        results = self.searcher.search(
            "Python",
            vector_results=vector_results,
            top_k=5
        )

        assert len(results) >= 1


class TestSearchResult:
    """SearchResult数据类测试"""

    def test_creation(self):
        """测试创建"""
        result = SearchResult(
            content="Test content",
            score=0.95,
            source="vector",
            metadata={"key": "value"}
        )

        assert result.content == "Test content"
        assert result.score == 0.95
        assert result.source == "vector"
        assert result.metadata["key"] == "value"


class TestHybridSearchEdgeCases:
    """混合检索边界情况测试"""

    def test_keyword_index_empty_list(self):
        """测试索引空文档列表"""
        searcher = KeywordSearcher()
        searcher.index([])
        assert searcher.doc_count == 0
        assert searcher.N == 0

    def test_keyword_search_no_index(self):
        """测试未索引就搜索"""
        searcher = KeywordSearcher()
        results = searcher.search("python", top_k=5)
        assert len(results) == 0

    def test_keyword_search_special_characters(self):
        """测试包含特殊字符的搜索"""
        searcher = KeywordSearcher()
        searcher.index([
            {"id": "1", "content": "Python <script>alert('xss')</script>", "metadata": {}},
            {"id": "2", "content": "JavaScript & SQL injection", "metadata": {}},
        ])
        results = searcher.search("Python", top_k=5)
        assert len(results) >= 1
        assert "python" in results[0].content.lower()

    def test_keyword_search_chinese_content(self):
        """测试中文内容搜索（边界情况：无空格分隔）"""
        searcher = KeywordSearcher()
        searcher.index([
            {"id": "1", "content": "Python编程语言", "metadata": {}},
            {"id": "2", "content": "JavaScript网页开发", "metadata": {}},
            {"id": "3", "content": "Python", "metadata": {}},
        ])
        # 英文词应该能匹配
        results = searcher.search("Python", top_k=5)
        # 只有完全匹配的"Python"会返回
        assert len(results) == 1

    def test_keyword_search_unicode(self):
        """测试Unicode内容"""
        searcher = KeywordSearcher()
        searcher.index([
            {"id": "1", "content": "你好 世界", "metadata": {}},  # 有空格分隔
            {"id": "2", "content": "Hello World", "metadata": {}},
        ])
        results = searcher.search("你好", top_k=5)
        assert len(results) == 1

    def test_keyword_search_very_long_query(self):
        """测试超长查询"""
        searcher = KeywordSearcher()
        searcher.index([
            {"id": "1", "content": "Python programming", "metadata": {}},
        ])
        long_query = "Python " * 1000
        results = searcher.search(long_query, top_k=5)
        # 应该返回结果，因为包含Python
        assert len(results) >= 1

    def test_keyword_search_case_insensitive(self):
        """测试大小写不敏感"""
        searcher = KeywordSearcher()
        searcher.index([
            {"id": "1", "content": "PYTHON programming language", "metadata": {}},
            {"id": "2", "content": "python is great", "metadata": {}},
        ])
        results = searcher.search("Python", top_k=5)
        assert len(results) == 2

    def test_keyword_search_duplicate_terms(self):
        """测试查询中重复词项"""
        searcher = KeywordSearcher()
        searcher.index([
            {"id": "1", "content": "Python Python Python", "metadata": {}},
        ])
        results = searcher.search("Python Python Python", top_k=5)
        assert len(results) == 1

    def test_vector_search_zero_vector(self):
        """测试零向量搜索"""
        searcher = VectorSearcher(dimension=3)
        searcher.index([
            {"id": "1", "content": "Doc1", "vector": [1.0, 0.0, 0.0]},
            {"id": "2", "content": "Doc2", "vector": [0.0, 1.0, 0.0]},
        ])
        results = searcher.search([0.0, 0.0, 0.0], top_k=5)
        # 零向量与所有向量相似度都是0
        assert all(r.score == 0.0 for r in results)

    def test_vector_search_dimension_mismatch(self):
        """测试向量维度不匹配"""
        searcher = VectorSearcher(dimension=3)
        searcher.index([
            {"id": "1", "content": "Doc1", "vector": [1.0, 0.0, 0.0]},
        ])
        # 查询向量维度不同
        results = searcher.search([1.0, 0.0], top_k=5)
        # 应该有处理逻辑
        assert isinstance(results, list)

    def test_vector_search_empty_index(self):
        """测试空索引的向量搜索"""
        searcher = VectorSearcher(dimension=3)
        results = searcher.search([1.0, 2.0, 3.0], top_k=5)
        assert len(results) == 0

    def test_hybrid_search_empty_documents(self):
        """测试空文档列表索引"""
        searcher = HybridSearcher()
        searcher.index([])
        results = searcher.search("python", top_k=5)
        assert len(results) == 0

    def test_hybrid_search_no_vector_no_query(self):
        """测试无向量结果时使用关键词"""
        searcher = HybridSearcher(fusion_method="rrf")
        searcher.index([
            {"id": "1", "content": "Python programming", "metadata": {}},
            {"id": "2", "content": "JavaScript web", "metadata": {}},
        ])
        # 不传vector_results，只传文本查询
        results = searcher.search("Python", vector_results=[], top_k=5)
        assert len(results) >= 1
        assert results[0].source in ["keyword", "hybrid"]

    def test_hybrid_search_rrf_with_empty_keyword(self):
        """测试RRF融合只有向量结果"""
        searcher = HybridSearcher(fusion_method="rrf")
        searcher.index([
            {"id": "1", "content": "Python programming", "metadata": {}},
        ])

        vector_results = [
            SearchResult(id="1", content="Python programming", score=0.9, source="vector", metadata={}),
        ]

        results = searcher.search("Python", vector_results=vector_results, top_k=5)
        assert len(results) >= 1

    def test_hybrid_search_weighted_with_empty_keyword(self):
        """测试加权融合只有向量结果"""
        searcher = HybridSearcher(fusion_method="weighted")
        searcher.index([
            {"id": "1", "content": "Python programming", "metadata": {}},
        ])

        vector_results = [
            SearchResult(id="1", content="Python programming", score=0.9, source="vector", metadata={}),
        ]

        results = searcher.search("Python", vector_results=vector_results, top_k=5)
        assert len(results) >= 1

    def test_hybrid_search_concat_with_empty_keyword(self):
        """测试拼接融合只有向量结果"""
        searcher = HybridSearcher(fusion_method="concat")
        searcher.index([
            {"id": "1", "content": "Python programming", "metadata": {}},
        ])

        vector_results = [
            SearchResult(id="1", content="Python programming", score=0.9, source="vector", metadata={}),
        ]

        results = searcher.search("Python", vector_results=vector_results, top_k=5)
        assert len(results) >= 1

    def test_hybrid_search_unknown_fusion_method(self):
        """测试未知融合方法"""
        searcher = HybridSearcher(fusion_method="unknown")
        searcher.index([
            {"id": "1", "content": "Python", "metadata": {}},
        ])
        results = searcher.search("Python", top_k=5)
        # 应该回退到关键词搜索
        assert len(results) >= 1

    def test_hybrid_search_zero_weights(self):
        """测试零权重"""
        searcher = HybridSearcher(keyword_weight=0.0, vector_weight=0.0, fusion_method="rrf")
        searcher.index([
            {"id": "1", "content": "Python", "metadata": {}},
        ])
        results = searcher.search("Python", top_k=5)
        # 零权重也应该返回结果
        assert isinstance(results, list)

    def test_hybrid_search_all_weights_to_vector(self):
        """测试全给向量权重"""
        searcher = HybridSearcher(keyword_weight=0.0, vector_weight=1.0, fusion_method="weighted")
        searcher.index([
            {"id": "1", "content": "Python", "metadata": {}},
        ])

        vector_results = [
            SearchResult(id="1", content="Python", score=0.9, source="vector", metadata={}),
        ]

        results = searcher.search("Python", vector_results=vector_results, top_k=5)
        assert len(results) >= 1

    def test_hybrid_search_very_large_top_k(self):
        """测试过大的top_k"""
        searcher = HybridSearcher()
        searcher.index([
            {"id": "1", "content": "Python", "metadata": {}},
        ])
        results = searcher.search("Python", top_k=1000)
        # 最多返回所有文档
        assert len(results) <= 1

    def test_search_result_default_values(self):
        """测试SearchResult默认值"""
        result = SearchResult()
        assert result.id is None
        assert result.content == ""
        assert result.score == 0.0
        assert result.metadata == {}
        # source默认为空字符串（从metadata获取）
        assert result.source == ""

    def test_search_result_source_from_metadata(self):
        """测试source从metadata获取"""
        result = SearchResult(
            content="test",
            metadata={"source": "document.txt"}
        )
        assert result.source == "document.txt"

    def test_keyword_search_multiple_terms(self):
        """测试多个词项搜索"""
        searcher = KeywordSearcher()
        searcher.index([
            {"id": "1", "content": "Python programming language", "metadata": {}},
            {"id": "2", "content": "JavaScript programming language", "metadata": {}},
            {"id": "3", "content": "Python machine learning", "metadata": {}},
        ])
        results = searcher.search("Python language", top_k=5)
        assert len(results) >= 1
        # 应该按得分排序
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_vector_search_orthogonal_vectors(self):
        """测试正交向量"""
        searcher = VectorSearcher(dimension=3)
        searcher.index([
            {"id": "1", "content": "X axis", "vector": [1.0, 0.0, 0.0]},
            {"id": "2", "content": "Y axis", "vector": [0.0, 1.0, 0.0]},
            {"id": "3", "content": "Z axis", "vector": [0.0, 0.0, 1.0]},
        ])
        query = [1.0, 0.0, 0.0]
        results = searcher.search(query, top_k=3)
        # X axis应该排第一
        assert results[0].id == "1"
        assert abs(results[0].score - 1.0) < 1e-6

    def test_hybrid_search_different_weights_rrf(self):
        """测试RRF不同权重"""
        searcher1 = HybridSearcher(keyword_weight=1.0, vector_weight=0.0, fusion_method="rrf")
        searcher2 = HybridSearcher(keyword_weight=0.0, vector_weight=1.0, fusion_method="rrf")

        docs = [
            {"id": "1", "content": "Python programming", "metadata": {}},
            {"id": "2", "content": "JavaScript web", "metadata": {}},
        ]

        searcher1.index(docs)
        searcher2.index(docs)

        vector_results = [
            SearchResult(id="1", content="Python programming", score=0.9, source="vector", metadata={}),
            SearchResult(id="2", content="JavaScript web", score=0.8, source="vector", metadata={}),
        ]

        results1 = searcher1.search("Python", vector_results=vector_results, top_k=5)
        results2 = searcher2.search("Python", vector_results=vector_results, top_k=5)

        # 两种权重都应该返回结果
        assert len(results1) >= 1
        assert len(results2) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
