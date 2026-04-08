"""
Reranker - 重排序模块
=====================

【学习要点】为什么需要Reranker？

1. 向量检索的局限性
   - 基于embedding相似度
   - 可能忽略语义细节
   - 排名不一定最优

2. Reranker的作用
   - 对初步检索结果重新排序
   - 使用更强大的模型（如Cross-Encoder）
   - 提高检索质量

3. 两阶段检索
   - Stage 1: 向量检索（高效，召回候选）
   - Stage 2: Reranker（精确，重排Top-K）

4. 多样性重排序 (MMR)
   - 避免结果过于相似
   - 提升覆盖度
   - 提升用户体验
"""

from typing import List, Dict, Optional, Tuple, Callable
from collections import Counter, defaultdict
import numpy as np
from dataclasses import dataclass
import os

# SSL 修复：禁用 HuggingFace SSL 验证（Windows 证书问题）
os.environ['HF_HUB_DISABLE_SSL'] = 'true'


@dataclass
class RerankResult:
    """重排序结果"""
    index: int          # 原始索引
    score: float        # 重排序分数
    content: str         # 内容
    metadata: Dict       # 元数据


class ScoreNormalizer:
    """分数归一化工具

    【学习要点】为什么需要归一化？
    - 不同 reranker 输出分数范围不同
    - Cross-Encoder: [-1, 1] 或 [0, 1]
    - BM25: 无上界
    - 归一化后便于融合和比较
    """

    @staticmethod
    def min_max(scores: np.ndarray) -> np.ndarray:
        """Min-Max归一化

        公式: (x - min) / (max - min)
        范围: [0, 1]
        """
        min_val = scores.min()
        max_val = scores.max()
        if max_val - min_val < 1e-8:
            return np.ones_like(scores) * 0.5
        return (scores - min_val) / (max_val - min_val)

    @staticmethod
    def z_score(scores: np.ndarray) -> np.ndarray:
        """Z-Score归一化

        公式: (x - mean) / std
        范围: 近似 [-3, 3]
        """
        std = scores.std()
        if std < 1e-8:
            return np.zeros_like(scores)
        return (scores - scores.mean()) / std

    @staticmethod
    def percentile(scores: np.ndarray) -> np.ndarray:
        """百分位归一化

        公式: rank(x) / n
        范围: [0, 1]
        """
        return np.array([
            (scores < s).sum() / len(scores)
            for s in scores
        ])

    @staticmethod
    def rank(scores: np.ndarray) -> np.ndarray:
        """排名归一化

        将分数转换为排名（1=最高），然后归一化
        """
        # argsort ascending, then reverse to get descending rank
        # np.argsort gives indices that would sort ascending
        # so if scores = [1,3,2,5,4], argsort = [0,2,1,4,3]
        # descending order indices = [3,4,1,2,0] (5's index, 4's index, etc.)
        n = len(scores)
        order = np.argsort(scores)
        ranks = np.empty_like(order)
        ranks[order] = np.arange(1, n + 1)  # 1-based rank
        # 最高分排第1名，归一化后值最大
        return ranks / (n + 1)


class BaseReranker:
    """Reranker基类"""

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 5
    ) -> List[RerankResult]:
        """重排序

        Args:
            query: 查询文本
            results: 初步检索结果 [{"content": ..., "metadata": ...}, ...]
            top_k: 返回数量

        Returns:
            重排序后的结果
        """
        raise NotImplementedError


class CrossEncoderReranker(BaseReranker):
    """Cross-Encoder重排序

    【学习要点】Cross-Encoder vs Bi-Encoder

    Bi-Encoder (向量检索):
    - query和doc分别编码
    - 分别生成embedding
    - 计算cosine相似度
    - 速度快，但精度一般

    Cross-Encoder:
    - query和doc一起编码
    - 直接输出相似度分数
    - 精度高，但速度慢
    - 适合重排序少量候选
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu"
    ):
        """
        Args:
            model_name: HuggingFace模型名
            device: cpu/cuda
        """
        self.model_name = model_name
        self.device = device
        self.model = None  # 延迟加载

    def _load_model(self):
        """延迟加载模型"""
        if self.model is None:
            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(self.model_name, device=self.device)
            except ImportError:
                raise ImportError("请安装sentence-transformers: pip install sentence-transformers")

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 5
    ) -> List[RerankResult]:
        """重排序"""
        if not results:
            return []

        self._load_model()

        # 构建query-doc pairs
        pairs = [[query, r["content"]] for r in results]

        # 批量预测分数
        scores = self.model.predict(pairs)

        # 排序
        ranked_indices = np.argsort(scores)[::-1]

        # 构建结果
        reranked = []
        for i, idx in enumerate(ranked_indices[:top_k]):
            reranked.append(RerankResult(
                index=idx,
                score=float(scores[idx]),
                content=results[idx]["content"],
                metadata=results[idx].get("metadata", {})
            ))

        return reranked


class BM25Reranker(BaseReranker):
    """BM25重排序（轻量级备选）

    【学习要点】BM25算法
    - 经典的文本检索算法
    - 基于词频和逆文档频率
    - 对长文档友好
    - 无需机器学习模型
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_lengths = []
        self.avgdl = 0
        self.doc_freqs = {}  # term -> doc frequency
        self.idf = {}

    def fit(self, documents: List[str]):
        """构建索引

        Args:
            documents: 文档列表
        """
        import math
        from collections import Counter

        N = len(documents)
        self.doc_lengths = []

        for doc in documents:
            # 智能分词：检测是否包含中文字符
            if self._contains_chinese(doc):
                # 中文：按字符分词（包含标点和空格）
                terms = self._tokenize_chinese(doc.lower())
            else:
                # 英文：按空格分词
                terms = doc.lower().split()

            self.doc_lengths.append(len(terms))

            # 统计文档频率
            for term in set(terms):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avgdl = sum(self.doc_lengths) / N if N > 0 else 0

        # 计算IDF
        for term, df in self.doc_freqs.items():
            self.idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    def _contains_chinese(self, text: str) -> bool:
        """检测文本是否包含中文"""
        return any('\u4e00' <= char <= '\u9fff' for char in text)

    def _tokenize_chinese(self, text: str) -> List[str]:
        """中文分词（字符级）"""
        import re
        # 按标点、空白字符分割，保留所有字符
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^\s\w]', text)
        # 过滤空字符
        return [t for t in tokens if t.strip()]

    def _score(self, query_terms: List[str], doc_idx: int) -> float:
        """计算单个文档的BM25分数"""
        import math

        doc_len = self.doc_lengths[doc_idx]
        term_freqs = query_terms  # 简化：假设query term都出现

        score = 0.0
        for term in set(query_terms):
            if term not in self.idf:
                continue

            # 简化的TF计算
            tf = 1  # 假设每个term出现1次
            idf = self.idf[term]

            # BM25公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)

            score += idf * numerator / denominator

        return score

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 5
    ) -> List[RerankResult]:
        """重排序"""
        if not results:
            return []

        # 先fit（如果还没fit）
        if not self.doc_lengths:
            self.fit([r["content"] for r in results])

        query_terms = query.lower().split()

        # 计算每个结果的BM25分数
        scores = []
        for i, result in enumerate(results):
            # 重新分词
            doc_terms = result["content"].lower().split()
            score = self._score_with_doc(query_terms, doc_terms)
            scores.append((i, score, result))

        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)

        # 构建结果
        reranked = []
        for i, (idx, score, result) in enumerate(scores[:top_k]):
            reranked.append(RerankResult(
                index=idx,
                score=score,
                content=result["content"],
                metadata=result.get("metadata", {})
            ))

        return reranked

    def _score_with_doc(self, query_terms: List[str], doc_terms: List[str]) -> float:
        """计算query和doc的BM25分数"""
        import math

        doc_len = len(doc_terms)
        doc_tf = Counter(doc_terms)

        score = 0.0
        for term in set(query_terms):
            if term not in self.idf:
                continue

            tf = doc_tf.get(term, 0)
            idf = self.idf[term]

            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / max(self.avgdl, 1))

            score += idf * numerator / denominator

        return score


class HybridReranker(BaseReranker):
    """混合重排序

    结合多种重排序方法
    """

    def __init__(
        self,
        use_cross_encoder: bool = True,
        use_bm25: bool = True,
        cross_encoder_weight: float = 0.7
    ):
        self.use_cross_encoder = use_cross_encoder
        self.use_bm25 = use_bm25
        self.cross_encoder_weight = cross_encoder_weight

        self.cross_encoder = None
        self.bm25 = None

        if use_cross_encoder:
            try:
                self.cross_encoder = CrossEncoderReranker()
            except ImportError:
                self.use_cross_encoder = False

        if use_bm25:
            self.bm25 = BM25Reranker()

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 5
    ) -> List[RerankResult]:
        """混合重排序"""
        if not results:
            return []

        scores = np.zeros(len(results))

        # Cross-Encoder分数
        if self.use_cross_encoder and self.cross_encoder:
            try:
                ce_results = self.cross_encoder.rerank(query, results, top_k=len(results))
                ce_scores = np.array([r.score for r in ce_results])
                # 归一化
                ce_scores = ScoreNormalizer.min_max(ce_scores)
                scores += self.cross_encoder_weight * ce_scores
            except Exception:
                pass

        # BM25分数
        if self.use_bm25 and self.bm25:
            try:
                self.bm25.fit([r["content"] for r in results])
                bm25_results = self.bm25.rerank(query, results, top_k=len(results))
                bm25_scores = np.array([r.score for r in bm25_results])
                # 归一化
                bm25_scores = ScoreNormalizer.min_max(bm25_scores)
                scores += (1 - self.cross_encoder_weight) * bm25_scores
            except Exception:
                pass

        # 排序
        ranked_indices = np.argsort(scores)[::-1]

        # 构建结果
        reranked = []
        for i, idx in enumerate(ranked_indices[:top_k]):
            reranked.append(RerankResult(
                index=idx,
                score=float(scores[idx]),
                content=results[idx]["content"],
                metadata=results[idx].get("metadata", {})
            ))

        return reranked


class MMRReranker(BaseReranker):
    """MMR (Maximal Marginal Relevance) 多样性重排序

    【学习要点】MMR算法
    - 在相关性和多样性之间取得平衡
    - 公式: MMR = λ * Sim(query, doc) - (1-λ) * max_{d' in S} Sim(doc, d')
    - λ 越大越注重相关性，越小越注重多样性

    应用场景：
    - 检索结果去重
    - 推荐系统多样性
    - 文档摘要选择
    """

    def __init__(
        self,
        base_reranker: Optional[BaseReranker] = None,
        lambda_param: float = 0.7,
        embedding_func: Optional[Callable[[str], List[float]]] = None
    ):
        """
        Args:
            base_reranker: 基础相关性 reranker
            lambda_param: 平衡参数 [0, 1]
            embedding_func: 用于计算相似度的embedding函数
        """
        self.base_reranker = base_reranker
        self.lambda_param = lambda_param
        self.embedding_func = embedding_func

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 5
    ) -> List[RerankResult]:
        """MMR重排序"""
        if not results:
            return []

        # 如果没有基础reranker，先用BM25排序
        if self.base_reranker is None:
            bm25 = BM25Reranker()
            bm25.fit([r["content"] for r in results])
            scored_results = bm25.rerank(query, results, top_k=len(results))
        else:
            scored_results = self.base_reranker.rerank(query, results, top_k=len(results))

        # MMR选择
        selected = []
        remaining_indices = list(range(len(results)))

        for _ in range(min(top_k, len(results))):
            if not remaining_indices:
                break

            best_score = float('-inf')
            best_idx = None

            for idx in remaining_indices:
                # 相关性分数
                relevance = scored_results[idx].score if idx < len(scored_results) else 0.0

                # 多样性分数：与已选结果的最大相似度
                diversity = 0.0
                if selected and self.embedding_func is not None:
                    doc_embedding = self.embedding_func(results[idx]["content"])
                    max_sim = 0.0
                    for sel_idx in selected:
                        sel_embedding = self.embedding_func(results[sel_idx]["content"])
                        sim = self._cosine_similarity(doc_embedding, sel_embedding)
                        max_sim = max(max_sim, sim)
                    diversity = max_sim

                # MMR分数
                mmr_score = self.lambda_param * relevance - (1 - self.lambda_param) * diversity

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            if best_idx is not None:
                selected.append(best_idx)
                remaining_indices.remove(best_idx)

        # 构建结果
        reranked = []
        for idx in selected:
            reranked.append(RerankResult(
                index=idx,
                score=best_score,
                content=results[idx]["content"],
                metadata=results[idx].get("metadata", {})
            ))

        return reranked

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 * norm2 < 1e-8:
            return 0.0
        return dot / (norm1 * norm2)


class RRFReranker(BaseReranker):
    """Reciprocal Rank Fusion (RRF) 重排序

    【学习要点】RRF算法
    - 将多个排序列表融合为一个
    - 基于排名的融合，不依赖分数
    - 公式: RRF(d) = Σ 1/(k + rank_i(d))
    - k 是平滑参数，通常设为60

    优点：
    - 简单高效
    - 不需要分数校准
    - 对异常值鲁棒
    """

    def __init__(self, k: int = 60):
        """
        Args:
            k: 平滑参数，越大越注重多样性
        """
        self.k = k

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 5
    ) -> List[RerankResult]:
        """RRF重排序

        注意: RRF通常需要多个排序列表，这里使用单一排序列表
        实际应用中应传入多个不同检索方法的结果
        """
        if not results:
            return []

        # 为每个结果计算RRF分数
        # 由于只有单一排序列表，使用BM25作为基础排序
        bm25 = BM25Reranker()
        bm25.fit([r["content"] for r in results])
        bm25_results = bm25.rerank(query, results, top_k=len(results))

        # 构建RRF分数（这里简化处理，实际多列表会更复杂）
        scores = np.zeros(len(results))
        for rrf_result in bm25_results:
            doc_idx = rrf_result.index
            # 使用排名的倒数作为RRF分数
            rank = doc_idx + 1
            scores[doc_idx] = 1.0 / (self.k + rank)

        # 排序
        ranked_indices = np.argsort(scores)[::-1]

        # 构建结果
        reranked = []
        for idx in ranked_indices[:top_k]:
            reranked.append(RerankResult(
                index=idx,
                score=float(scores[idx]),
                content=results[idx]["content"],
                metadata=results[idx].get("metadata", {})
            ))

        return reranked


# 全局默认reranker
_default_reranker: Optional[HybridReranker] = None


def get_reranker() -> HybridReranker:
    """获取全局reranker实例"""
    global _default_reranker
    if _default_reranker is None:
        _default_reranker = HybridReranker()
    return _default_reranker


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 初始化
reranker = HybridReranker(
    use_cross_encoder=True,
    use_bm25=True,
    cross_encoder_weight=0.7
)

# 2. 初步检索结果（从向量数据库返回）
initial_results = [
    {"content": "Python is a programming language", "metadata": {"source": "doc1"}},
    {"content": "JavaScript is for web development", "metadata": {"source": "doc2"}},
    {"content": "Machine learning uses Python", "metadata": {"source": "doc3"}},
]

# 3. 重排序
query = "What programming language is used for ML?"
reranked = reranker.rerank(query, initial_results, top_k=3)

# 4. 结果
for r in reranked:
    print(f"[{r.score:.3f}] {r.content[:50]}...")
"""
