"""
测试Reranker模块
"""

import pytest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.retrieval import (
    BM25Reranker,
    CrossEncoderReranker,
    HybridReranker,
    MMRReranker,
    RRFReranker,
    ScoreNormalizer,
    RerankResult
)


class TestBM25Reranker:
    """BM25 Reranker测试"""

    def setup_method(self):
        """每个测试前创建reranker"""
        self.reranker = BM25Reranker(k1=1.5, b=0.75)

    def test_fit(self):
        """测试索引构建"""
        documents = [
            "Python is a programming language",
            "JavaScript is for web development",
            "Machine learning uses Python and data"
        ]

        self.reranker.fit(documents)

        assert len(self.reranker.doc_lengths) == 3
        assert self.reranker.avgdl > 0
        assert len(self.reranker.idf) > 0

    def test_rerank_basic(self):
        """测试基本重排序"""
        documents = [
            "Python is a programming language",
            "JavaScript is for web development",
            "Machine learning uses Python"
        ]

        self.reranker.fit(documents)

        results = [
            {"content": doc, "metadata": {"index": i}}
            for i, doc in enumerate(documents)
        ]

        query = "What language is used for ML?"
        reranked = self.reranker.rerank(query, results, top_k=3)

        assert len(reranked) == 3
        # ML相关的内容应该有更高分数
        scores = [r.score for r in reranked]
        assert scores == sorted(scores, reverse=True)

    def test_rerank_empty(self):
        """测试空结果"""
        reranked = self.reranker.rerank("query", [], top_k=5)
        assert len(reranked) == 0

    def test_rerank_top_k(self):
        """测试top_k限制"""
        documents = ["doc" + str(i) for i in range(10)]
        self.reranker.fit(documents)

        results = [{"content": doc} for doc in documents]
        reranked = self.reranker.rerank("query", results, top_k=3)

        assert len(reranked) == 3

    def test_score_attributes(self):
        """测试结果属性"""
        documents = ["Python programming", "Web development"]
        self.reranker.fit(documents)

        results = [{"content": doc, "metadata": {"source": "test"}} for doc in documents]
        reranked = self.reranker.rerank("Python", results, top_k=2)

        for r in reranked:
            assert hasattr(r, 'index')
            assert hasattr(r, 'score')
            assert hasattr(r, 'content')
            assert hasattr(r, 'metadata')

    def test_chinese_tokenization(self):
        """测试中文分词"""
        documents = ["Python编程语言", "JavaScript网页开发", "机器学习用Python"]
        reranker = BM25Reranker()
        reranker.fit(documents)

        assert len(reranker.doc_lengths) == 3
        assert reranker.avgdl > 0


class TestCrossEncoderReranker:
    """CrossEncoder Reranker测试"""

    def test_initialization(self):
        """测试初始化"""
        reranker = CrossEncoderReranker(
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
            device="cpu"
        )
        assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert reranker.device == "cpu"
        assert reranker.model is None  # 延迟加载

    def test_rerank_empty(self):
        """测试空结果"""
        reranker = CrossEncoderReranker()
        # 空结果应该直接返回空列表，不触发模型加载
        reranked = reranker.rerank("query", [], top_k=5)
        assert len(reranked) == 0

    def test_rerank_empty_handles_model_not_loaded(self):
        """测试空结果不会触发模型加载"""
        reranker = CrossEncoderReranker()
        assert reranker.model is None  # 确认模型未加载
        reranked = reranker.rerank("query", [], top_k=5)
        assert reranker.model is None  # 确认调用后仍未加载
        assert len(reranked) == 0


class TestHybridReranker:
    """混合重排序测试"""

    def test_initialization(self):
        """测试初始化"""
        reranker = HybridReranker(
            use_cross_encoder=False,  # 禁用cross-encoder避免加载模型
            use_bm25=True,
            cross_encoder_weight=0.7
        )
        assert reranker.use_cross_encoder is False
        assert reranker.use_bm25 is True
        assert reranker.cross_encoder_weight == 0.7
        assert reranker.bm25 is not None

    def test_rerank_with_bm25_only(self):
        """只用BM25的重排序"""
        reranker = HybridReranker(use_cross_encoder=False, use_bm25=True)

        results = [
            {"content": "Python is great", "metadata": {}},
            {"content": "JavaScript is for web", "metadata": {}},
            {"content": "Machine learning uses Python", "metadata": {}}
        ]

        reranked = reranker.rerank("Python programming", results, top_k=3)
        assert len(reranked) == 3
        # Python相关的内容应该排在前面
        assert "Python" in reranked[0].content

    def test_rerank_empty(self):
        """测试空结果"""
        reranker = HybridReranker(use_cross_encoder=False)
        reranked = reranker.rerank("query", [], top_k=5)
        assert len(reranked) == 0

    def test_rerank_top_k(self):
        """测试top_k限制"""
        reranker = HybridReranker(use_cross_encoder=False)

        results = [
            {"content": f"Document {i}", "metadata": {}}
            for i in range(10)
        ]

        reranked = reranker.rerank("query", results, top_k=3)
        assert len(reranked) == 3


class TestMMRReranker:
    """MMR多样性重排序测试"""

    def test_initialization(self):
        """测试初始化"""
        reranker = MMRReranker(lambda_param=0.7)
        assert reranker.lambda_param == 0.7
        assert reranker.base_reranker is None

    def test_rerank_basic(self):
        """测试基本MMR重排序"""
        reranker = MMRReranker(lambda_param=0.5)

        results = [
            {"content": "Python programming language", "metadata": {"id": "1"}},
            {"content": "JavaScript for web development", "metadata": {"id": "2"}},
            {"content": "Python machine learning", "metadata": {"id": "3"}},
            {"content": "Web design principles", "metadata": {"id": "4"}}
        ]

        reranked = reranker.rerank("Python", results, top_k=3)
        assert len(reranked) == 3
        # 验证结果有正确的属性
        for r in reranked:
            assert hasattr(r, 'index')
            assert hasattr(r, 'score')
            assert hasattr(r, 'content')

    def test_rerank_empty(self):
        """测试空结果"""
        reranker = MMRReranker()
        reranked = reranker.rerank("query", [], top_k=5)
        assert len(reranked) == 0

    def test_rerank_with_lambda(self):
        """测试不同lambda参数"""
        # lambda=1.0 只看相关性
        reranker_rel = MMRReranker(lambda_param=1.0, base_reranker=BM25Reranker())
        # lambda=0.0 只看多样性
        reranker_div = MMRReranker(lambda_param=0.0, base_reranker=BM25Reranker())

        results = [
            {"content": "Python is great", "metadata": {}},
            {"content": "Python tutorials", "metadata": {}},
            {"content": "JavaScript web", "metadata": {}}
        ]

        reranked_rel = reranker_rel.rerank("Python", results, top_k=2)
        reranked_div = reranker_div.rerank("Python", results, top_k=2)

        # 两种设置都应该返回结果
        assert len(reranked_rel) == 2
        assert len(reranked_div) == 2

    def test_cosine_similarity(self):
        """测试余弦相似度计算"""
        reranker = MMRReranker()

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]

        # 相同向量相似度为1
        sim_same = reranker._cosine_similarity(vec1, vec2)
        assert abs(sim_same - 1.0) < 1e-6

        # 正交向量相似度为0
        sim_orth = reranker._cosine_similarity(vec1, vec3)
        assert abs(sim_orth) < 1e-6


class TestRRFReranker:
    """RRF重排序测试"""

    def test_initialization(self):
        """测试初始化"""
        reranker = RRFReranker(k=60)
        assert reranker.k == 60

    def test_rerank_basic(self):
        """测试基本RRF重排序"""
        reranker = RRFReranker(k=60)

        results = [
            {"content": "Python is great", "metadata": {}},
            {"content": "JavaScript is for web", "metadata": {}},
            {"content": "Machine learning uses Python", "metadata": {}}
        ]

        reranked = reranker.rerank("Python", results, top_k=3)
        assert len(reranked) == 3

    def test_rerank_empty(self):
        """测试空结果"""
        reranker = RRFReranker()
        reranked = reranker.rerank("query", [], top_k=5)
        assert len(reranked) == 0

    def test_rerank_top_k(self):
        """测试top_k限制"""
        reranker = RRFReranker()

        results = [
            {"content": f"Document {i}", "metadata": {}}
            for i in range(10)
        ]

        reranked = reranker.rerank("query", results, top_k=5)
        assert len(reranked) == 5

    def test_different_k_values(self):
        """测试不同的k值"""
        results = [
            {"content": "doc1", "metadata": {}},
            {"content": "doc2", "metadata": {}}
        ]

        reranker_k_small = RRFReranker(k=10)
        reranker_k_large = RRFReranker(k=100)

        reranked_small = reranker_k_small.rerank("query", results, top_k=2)
        reranked_large = reranker_k_large.rerank("query", results, top_k=2)

        # 两种k值都应该返回结果
        assert len(reranked_small) == 2
        assert len(reranked_large) == 2


class TestScoreNormalizer:
    """分数归一化工具测试"""

    def test_min_max_normalization(self):
        """测试Min-Max归一化"""
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = ScoreNormalizer.min_max(scores)

        assert normalized.min() == 0.0
        assert normalized.max() == 1.0
        assert abs(normalized[2] - 0.5) < 1e-6

    def test_min_max_constant(self):
        """测试常量数组归一化"""
        scores = np.array([1.0, 1.0, 1.0])
        normalized = ScoreNormalizer.min_max(scores)

        # 常量应该归一化为0.5
        assert all(abs(x - 0.5) < 1e-6 for x in normalized)

    def test_z_score_normalization(self):
        """测试Z-Score归一化"""
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = ScoreNormalizer.z_score(scores)

        # 均值应该接近0，标准差应该接近1
        assert abs(normalized.mean()) < 1e-6
        assert abs(normalized.std() - 1.0) < 1e-6

    def test_z_score_constant(self):
        """测试常量数组Z-Score"""
        scores = np.array([1.0, 1.0, 1.0])
        normalized = ScoreNormalizer.z_score(scores)

        # 常量应该归一化为0
        assert all(abs(x) < 1e-6 for x in normalized)

    def test_percentile_normalization(self):
        """测试百分位归一化"""
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = ScoreNormalizer.percentile(scores)

        # 每个值的百分位应该是 (小于它的数量) / n
        assert abs(normalized[0] - 0.0) < 1e-6  # 最小的值
        assert abs(normalized[4] - 0.8) < 1e-6  # 最大的值

    def test_rank_normalization(self):
        """测试排名归一化"""
        scores = np.array([1.0, 3.0, 2.0, 5.0, 4.0])
        normalized = ScoreNormalizer.rank(scores)

        # 排名归一化后，最大值排名最高
        max_idx = np.argmax(scores)
        assert normalized[max_idx] > normalized.min()


class TestRerankResult:
    """RerankResult数据类测试"""

    def test_creation(self):
        """测试创建"""
        result = RerankResult(
            index=0,
            score=0.95,
            content="Test content",
            metadata={"source": "test"}
        )

        assert result.index == 0
        assert result.score == 0.95
        assert result.content == "Test content"
        assert result.metadata["source"] == "test"

    def test_equality(self):
        """测试相等性"""
        result1 = RerankResult(index=0, score=0.9, content="test", metadata={})
        result2 = RerankResult(index=0, score=0.9, content="test", metadata={})

        assert result1.index == result2.index
        assert result1.score == result2.score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
