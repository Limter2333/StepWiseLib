"""
混合检索模块 - Hybrid Search
===========================

【功能】
- 关键词搜索
- 向量搜索
- 混合搜索（RRF融合）

【依赖】
- KeywordIndex: 关键词索引
- VectorStore: 向量存储
- RRFResultMerger: 结果融合
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class SearchResult:
    """搜索结果"""
    id: Optional[str] = None
    content: str = ""
    score: float = 0.0
    metadata: Dict[str, Any] = None
    source: Optional[str] = None  # 来源

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.source is None:
            self.source = self.metadata.get("source", "")


class KeywordSearcher:
    """关键词搜索引擎

    【功能】
    - 文档索引
    - BM25排序
    - 关键词匹配
    """

    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.term_doc_freq: Dict[str, int] = {}  # 词项 -> 文档频率
        self.doc_count = 0
        self.N = 0  # 文档总数

    @property
    def N(self):
        return self._N

    @N.setter
    def N(self, value):
        self._N = value

    def index(self, documents: List[Dict[str, Any]]):
        """索引文档

        Args:
            documents: [{"id": "...", "content": "...", "metadata": {...}}]
        """
        for doc in documents:
            doc_id = doc["id"]
            content = doc["content"].lower()
            self.documents[doc_id] = {
                "content": content,
                "metadata": doc.get("metadata", {})
            }

            # 词项统计
            terms = set(content.split())
            for term in terms:
                self.term_doc_freq[term] = self.term_doc_freq.get(term, 0) + 1

        self.doc_count = len(self.documents)
        self.N = self.doc_count

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """搜索

        Args:
            query: 查询词
            top_k: 返回数量

        Returns:
            SearchResult列表
        """
        query_terms = query.lower().split()
        scores: Dict[str, float] = {}

        for doc_id, doc in self.documents.items():
            score = 0.0
            doc_terms = set(doc["content"].split())

            for term in query_terms:
                if term in doc_terms:
                    # BM25 scoring (Okapi formula)
                    tf = doc["content"].lower().split().count(term)
                    df = self.term_doc_freq.get(term, 1)
                    # 使用标准BM25 IDF公式
                    idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
                    score += tf * idf

            if score > 0:
                scores[doc_id] = score

        # 排序
        results = sorted(
            [
                SearchResult(
                    id=doc_id,
                    content=self.documents[doc_id]["content"],
                    score=scores[doc_id],
                    metadata=self.documents[doc_id]["metadata"]
                )
                for doc_id in scores
            ],
            key=lambda x: x.score,
            reverse=True
        )

        return results[:top_k]


class VectorSearcher:
    """向量搜索引擎

    【功能】
    - 向量检索
    - 相似度计算
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.vectors: Dict[str, List[float]] = {}

    def index(self, documents: List[Dict[str, Any]]):
        """索引文档

        Args:
            documents: [{"id": "...", "content": "...", "vector": [...], "metadata": {...}}]
        """
        for doc in documents:
            doc_id = doc["id"]
            self.documents[doc_id] = {
                "content": doc["content"],
                "metadata": doc.get("metadata", {})
            }
            if "vector" in doc:
                self.vectors[doc_id] = doc["vector"]

    def search(self, query_vector: List[float], top_k: int = 10) -> List[SearchResult]:
        """向量搜索

        Args:
            query_vector: 查询向量
            top_k: 返回数量

        Returns:
            SearchResult列表
        """
        scores: Dict[str, float] = {}

        for doc_id, doc_vector in self.vectors.items():
            # 余弦相似度
            dot = sum(a * b for a, b in zip(query_vector, doc_vector))
            norm1 = math.sqrt(sum(a * a for a in query_vector))
            norm2 = math.sqrt(sum(a * a for a in doc_vector))

            if norm1 > 0 and norm2 > 0:
                scores[doc_id] = dot / (norm1 * norm2)
            else:
                scores[doc_id] = 0.0

        # 排序
        results = sorted(
            [
                SearchResult(
                    id=doc_id,
                    content=self.documents[doc_id]["content"],
                    score=scores[doc_id],
                    metadata=self.documents[doc_id]["metadata"]
                )
                for doc_id in scores
            ],
            key=lambda x: x.score,
            reverse=True
        )

        return results[:top_k]


class HybridSearcher:
    """混合搜索引擎

    【功能】
    - 关键词 + 向量融合搜索
    - RRF (Reciprocal Rank Fusion) 算法
    """

    def __init__(self, keyword_weight: float = 0.5, vector_weight: float = 0.5, fusion_method: str = "rrf"):
        self.keyword_searcher = KeywordSearcher()
        self.vector_searcher = VectorSearcher()
        self.keyword_weight = keyword_weight
        self.vector_weight = vector_weight
        self.fusion_method = fusion_method  # "rrf", "weighted", "concat"

    def index(self, documents: List[Dict[str, Any]]):
        """索引文档

        Args:
            documents: [{"id": "...", "content": "...", "vector": [...], "metadata": {...}}]
        """
        # 提取纯文本文档给关键词搜索器
        text_docs = [{"id": d["id"], "content": d["content"], "metadata": d.get("metadata", {})} for d in documents]
        self.keyword_searcher.index(text_docs)

        # 完整文档给向量搜索器
        self.vector_searcher.index(documents)

    def search(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 10,
        rrf_k: int = 60,
        vector_results: Optional[List[SearchResult]] = None
    ) -> List[SearchResult]:
        """混合搜索

        Args:
            query: 文本查询
            query_vector: 向量查询
            top_k: 返回数量
            rrf_k: RRF参数
            vector_results: 外部传入的向量搜索结果

        Returns:
            SearchResult列表
        """
        keyword_results = self.keyword_searcher.search(query, top_k=top_k)

        # 如果没有提供vector_results，使用内部的向量搜索
        if vector_results is None:
            if query_vector:
                vector_results = self.vector_searcher.search(query_vector, top_k=top_k)
            else:
                vector_results = []

        # 根据fusion_method融合结果
        if self.fusion_method == "rrf":
            results = self._rrf_fusion(keyword_results, vector_results, rrf_k, top_k)
        elif self.fusion_method == "weighted":
            results = self._weighted_fusion(keyword_results, vector_results, top_k)
        elif self.fusion_method == "concat":
            results = self._concat_fusion(keyword_results, vector_results, top_k)
        else:
            results = keyword_results

        return results

    def _rrf_fusion(
        self,
        keyword_results: List[SearchResult],
        vector_results: List[SearchResult],
        rrf_k: int,
        top_k: int
    ) -> List[SearchResult]:
        """RRF融合"""
        # 如果没有向量结果，直接返回关键词结果
        if not vector_results:
            return [
                SearchResult(
                    id=r.id,
                    content=r.content,
                    score=r.score,
                    metadata=r.metadata,
                    source="keyword"
                )
                for r in keyword_results[:top_k]
            ]

        keyword_scores = {r.id: (i + 1) for i, r in enumerate(keyword_results)}
        vector_scores = {r.id: (i + 1) for i, r in enumerate(vector_results)}

        all_ids = set(keyword_scores.keys()) | set(vector_scores.keys())
        rrf_scores: Dict[str, float] = {}

        for doc_id in all_ids:
            kw_rank = keyword_scores.get(doc_id, len(keyword_scores) + 1)
            vec_rank = vector_scores.get(doc_id, len(vector_results) + 1)

            rrf = self.keyword_weight / (rrf_k + kw_rank)
            rrf += self.vector_weight / (rrf_k + vec_rank)
            rrf_scores[doc_id] = rrf

        # 构建结果
        id_to_doc = {r.id: r for r in keyword_results + vector_results if r.id}
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids[:top_k]:
            if doc_id in id_to_doc:
                doc = id_to_doc[doc_id]
                results.append(SearchResult(
                    id=doc.id,
                    content=doc.content,
                    score=rrf_scores[doc_id],
                    metadata=doc.metadata,
                    source="hybrid"
                ))
        return results

    def _weighted_fusion(
        self,
        keyword_results: List[SearchResult],
        vector_results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """加权融合"""
        scores: Dict[str, float] = {}

        for r in keyword_results:
            scores[r.id] = self.keyword_weight * r.score

        for r in vector_results:
            if r.id in scores:
                scores[r.id] += self.vector_weight * r.score
            else:
                scores[r.id] = self.vector_weight * r.score

        id_to_doc = {r.id: r for r in keyword_results + vector_results if r.id}
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        return [
            SearchResult(
                id=doc_id,
                content=id_to_doc[doc_id].content,
                score=scores[doc_id],
                metadata=id_to_doc[doc_id].metadata,
                source="hybrid"
            )
            for doc_id in sorted_ids[:top_k] if doc_id in id_to_doc
        ]

    def _concat_fusion(
        self,
        keyword_results: List[SearchResult],
        vector_results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """拼接融合"""
        seen = set()
        results = []

        for r in keyword_results:
            if r.id not in seen:
                results.append(SearchResult(
                    id=r.id,
                    content=r.content,
                    score=r.score,
                    metadata=r.metadata,
                    source="keyword"
                ))
                seen.add(r.id)

        for r in vector_results:
            if r.id not in seen:
                results.append(SearchResult(
                    id=r.id,
                    content=r.content,
                    score=r.score,
                    metadata=r.metadata,
                    source="vector"
                ))
                seen.add(r.id)

        return results[:top_k]
