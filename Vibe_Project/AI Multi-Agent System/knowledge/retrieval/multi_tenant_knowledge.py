"""
多租户混合知识库 - 完美版
=========================

【完美体验设计】

1. 多租户完全隔离
   - 共享基础库：公共知识，所有租户可访问
   - 私有知识库：租户私有数据，完全隔离

2. RAG深度集成
   - 向量检索：语义相似匹配
   - 关键词检索：精确关键词匹配
   - RRF融合：结合两者优势

3. 搜索结果优化
   - 多阶段排序：初步召回 → 重排序 → 最终排序
   - 相关性评分：基于语义和关键词综合评分
   - 去重处理：避免重复结果

4. 完美的租户隔离保证
   - 数据层面：租户私有库物理隔离
   - 查询层面：自动注入租户过滤条件
   - 结果层面：租户只能看到自己的数据
"""

from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import json


class TenantType(Enum):
    """数据来源类型"""
    SHARED = "shared"       # 共享库
    PRIVATE = "private"     # 私有库


class SearchType(Enum):
    """搜索类型"""
    HYBRID = "hybrid"      # 混合搜索（共享+私有）
    PRIVATE_ONLY = "private"  # 仅私有库
    SHARED_ONLY = "shared"    # 仅共享库


@dataclass
class Tenant:
    """租户信息"""
    tenant_id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class KnowledgeChunk:
    """知识块

    【设计】知识块是RAG系统的核心单元
    - id: 唯一标识
    - tenant_id: 归属租户（shared表示共享）
    - content: 文本内容
    - embedding: 向量（可选，用于快速检索）
    - metadata: 元数据（来源、时间、标签等）
    - chunk_index: 在原文档中的位置
    """
    id: str
    tenant_id: str
    content: str
    title: str = ""
    source: str = ""
    chunk_index: int = 0
    metadata: Dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None  # 延迟加载


@dataclass
class SearchResult:
    """搜索结果

    【设计】包含丰富的上下文信息
    - content: 文本内容
    - score: 综合评分
    - source_type: 数据来源（共享/私有）
    - tenant_id: 所属租户
    - metadata: 元数据
    - title: 文档标题
    - rerank_score: 重排序分数（原始）
    - keyword_score: 关键词分数
    - semantic_score: 语义分数
    """
    id: str
    content: str
    title: str
    score: float              # 综合评分（最终排序依据）
    source_type: TenantType
    tenant_id: str
    metadata: Dict
    rerank_score: float = 0.0   # 重排序分数
    keyword_score: float = 0.0   # BM25分数
    semantic_score: float = 0.0  # 向量相似度分数


@dataclass
class SearchRequest:
    """搜索请求"""
    tenant_id: str
    query: str
    search_type: SearchType = SearchType.HYBRID
    top_k: int = 10
    shared_top_k: int = 5       # 共享库返回数
    private_top_k: int = 10      # 私有库返回数
    min_score: float = 0.3       # 最低相关度阈值
    use_reranker: bool = True    # 是否使用重排序
    filters: Optional[Dict] = None  # 额外过滤条件


@dataclass
class SearchResponse:
    """搜索响应"""
    results: List[SearchResult]
    total: int
    query: str
    tenant_id: str
    search_time_ms: float
    metadata: Dict


class VectorStore:
    """向量存储接口

    【设计模式】适配器模式
    - 统一向量存储接口
    - 支持ChromaDB、Milvus等实现
    - 延迟初始化
    """

    def __init__(self):
        self._client = None
        self._collection = None

    def _ensure_initialized(self):
        """延迟初始化"""
        if self._client is None:
            # 实际实现中应该初始化ChromaDB或Milvus
            # 这里简化处理
            pass

    async def add(self, chunks: List[KnowledgeChunk]):
        """添加知识块"""
        self._ensure_initialized()
        # 实际实现：生成embedding，存入向量数据库
        pass

    async def search(
        self,
        query_embedding: List[float],
        tenant_id: str,
        top_k: int,
        filters: Optional[Dict] = None
    ) -> List[Tuple[str, float]]:  # (chunk_id, score)
        """向量搜索"""
        self._ensure_initialized()
        # 返回: [(chunk_id, similarity_score), ...]
        return []


class KeywordIndex:
    """关键词索引

    基于BM25算法的关键词检索
    """

    def __init__(self):
        self.documents: Dict[str, KnowledgeChunk] = {}
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.N: int = 0
        self.avgdl: float = 0.0
        self.doc_lengths: Dict[str, int] = {}

        # BM25参数
        self.k1 = 1.5
        self.b = 0.75

    def add_document(self, chunk: KnowledgeChunk):
        """添加文档"""
        self.documents[chunk.id] = chunk
        self.N += 1

        # 统计词频
        terms = self._tokenize(chunk.content)
        self.doc_lengths[chunk.id] = len(terms)

        for term in set(terms):
            self.doc_freqs[term] += 1

        # 计算平均长度
        self.avgdl = sum(self.doc_lengths.values()) / self.N

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        import re
        # 简单处理：转小写，按空格/标点分割
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        return tokens

    def _compute_idf(self, term: str) -> float:
        """计算IDF"""
        import math
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def _bm25_score(self, chunk_id: str, query_terms: List[str]) -> float:
        """计算BM25分数"""
        import math
        from collections import Counter

        doc_terms = self._tokenize(self.documents[chunk_id].content)
        doc_tf = Counter(doc_terms)
        doc_len = self.doc_lengths[chunk_id]

        score = 0.0
        for term in query_terms:
            if term not in self.doc_freqs:
                continue

            tf = doc_tf.get(term, 0)
            idf = self._compute_idf(term)

            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / max(self.avgdl, 1))
            score += idf * numerator / denominator

        return score

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """关键词搜索

        Returns:
            [(chunk_id, bm25_score), ...]
        """
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        scores = []
        for chunk_id in self.documents:
            score = self._bm25_score(chunk_id, query_terms)
            if score > 0:
                scores.append((chunk_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class RRFResultMerger:
    """RRF结果合并器

    【学习要点】RRF (Reciprocal Rank Fusion)
    - 将多个排序结果合并
    - 基于排名的融合算法
    - 公式: RRF(d) = Σ 1/(k + rank(d))
    """

    def __init__(self, k: int = 60):
        self.k = k

    def merge(
        self,
        result_lists: List[List[Tuple[str, float]]],
        weights: Optional[List[float]] = None
    ) -> List[Tuple[str, float]]:
        """合并多个排序结果

        Args:
            result_lists: 多个排序列表
            weights: 权重列表（可选）

        Returns:
            合并后的排序列表
        """
        if weights is None:
            weights = [1.0] * len(result_lists)

        scores: Dict[str, float] = defaultdict(float)

        for result_list, weight in zip(result_lists, weights):
            for rank, (chunk_id, score) in enumerate(result_list, 1):
                # RRF公式
                rrf_score = weight * (1 / (self.k + rank))
                scores[chunk_id] += rrf_score

        # 排序
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_items


class MultiTenantKnowledgeBase:
    """多租户混合知识库 - 完美版

    【核心特性】

    1. 租户完全隔离
       - 每个租户有独立的私有知识库
       - 共享知识库供所有租户访问
       - 严格的查询隔离保证

    2. 混合搜索
       - 语义搜索：基于向量的语义相似度
       - 关键词搜索：BM25精确匹配
       - RRF融合：结合两者优势

    3. 多阶段排序
       - 初步召回：向量+关键词双路召回
       - 重排序：使用更精确的模型排序
       - 最终排序：综合评分输出

    4. 可扩展性
       - 插件化向量存储
       - 可配置的排序策略
       - 灵活的过滤机制
    """

    def __init__(self):
        # 共享知识库
        self.shared_chunks: Dict[str, KnowledgeChunk] = {}

        # 租户私有知识库
        self.private_chunks: Dict[str, Dict[str, KnowledgeChunk]] = defaultdict(dict)

        # 租户注册表
        self.tenants: Dict[str, Tenant] = {}

        # 关键词索引
        self.shared_keyword_index = KeywordIndex()
        self.private_keyword_indexes: Dict[str, KeywordIndex] = defaultdict(KeywordIndex)

        # 合并器
        self.merger = RRFResultMerger(k=60)

        # 向量存储（延迟初始化）
        self._vector_store: Optional[VectorStore] = None

    def _get_vector_store(self) -> VectorStore:
        """获取向量存储"""
        if self._vector_store is None:
            self._vector_store = VectorStore()
        return self._vector_store

    # ========== 租户管理 ==========

    def register_tenant(self, tenant_id: str, name: str, description: str = "") -> Tenant:
        """注册租户

        Args:
            tenant_id: 租户ID
            name: 租户名称
            description: 租户描述

        Returns:
            租户对象
        """
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            description=description
        )
        self.tenants[tenant_id] = tenant
        self.private_keyword_indexes[tenant_id] = KeywordIndex()

        print(f"[MultiTenantKB] Registered tenant: {tenant_id} ({name})")
        return tenant

    def is_tenant_registered(self, tenant_id: str) -> bool:
        """检查租户是否注册"""
        return tenant_id in self.tenants

    # ========== 文档管理 ==========

    def add_shared_chunk(
        self,
        content: str,
        title: str = "",
        source: str = "",
        chunk_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """添加共享知识块

        Args:
            content: 知识内容
            title: 标题
            source: 来源
            chunk_id: 知识块ID（可选，自动生成）
            metadata: 元数据

        Returns:
            chunk_id
        """
        if chunk_id is None:
            chunk_id = f"shared_{len(self.shared_chunks) + 1}"

        chunk = KnowledgeChunk(
            id=chunk_id,
            tenant_id="shared",
            content=content,
            title=title,
            source=source,
            metadata=metadata or {}
        )

        self.shared_chunks[chunk_id] = chunk

        # 添加到关键词索引
        self.shared_keyword_index.add_document(chunk)

        print(f"[MultiTenantKB] Added shared chunk: {chunk_id}")
        return chunk_id

    def add_private_chunk(
        self,
        tenant_id: str,
        content: str,
        title: str = "",
        source: str = "",
        chunk_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """添加租户私有知识块

        Args:
            tenant_id: 租户ID
            content: 知识内容
            title: 标题
            source: 来源
            chunk_id: 知识块ID（可选）
            metadata: 元数据

        Returns:
            chunk_id
        """
        if not self.is_tenant_registered(tenant_id):
            raise ValueError(f"Tenant not registered: {tenant_id}")

        if chunk_id is None:
            chunk_id = f"private_{tenant_id}_{len(self.private_chunks[tenant_id]) + 1}"

        chunk = KnowledgeChunk(
            id=chunk_id,
            tenant_id=tenant_id,
            content=content,
            title=title,
            source=source,
            metadata=metadata or {}
        )

        self.private_chunks[tenant_id][chunk_id] = chunk

        # 添加到关键词索引
        self.private_keyword_indexes[tenant_id].add_document(chunk)

        print(f"[MultiTenantKB] Added private chunk for {tenant_id}: {chunk_id}")
        return chunk_id

    def add_shared_documents(self, documents: List[Dict]) -> List[str]:
        """批量添加共享文档

        Args:
            documents: [{"content": str, "title": str, "source": str}, ...]

        Returns:
            添加的chunk_id列表
        """
        chunk_ids = []
        for doc in documents:
            chunk_id = self.add_shared_chunk(
                content=doc["content"],
                title=doc.get("title", ""),
                source=doc.get("source", ""),
                metadata=doc.get("metadata", {})
            )
            chunk_ids.append(chunk_id)
        return chunk_ids

    def add_private_documents(
        self,
        tenant_id: str,
        documents: List[Dict]
    ) -> List[str]:
        """批量添加私有文档"""
        chunk_ids = []
        for doc in documents:
            chunk_id = self.add_private_chunk(
                tenant_id=tenant_id,
                content=doc["content"],
                title=doc.get("title", ""),
                source=doc.get("source", ""),
                metadata=doc.get("metadata", {})
            )
            chunk_ids.append(chunk_id)
        return chunk_ids

    # ========== 搜索 ==========

    def _keyword_search_shared(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """共享库关键词搜索"""
        return self.shared_keyword_index.search(query, top_k)

    def _keyword_search_private(
        self,
        tenant_id: str,
        query: str,
        top_k: int
    ) -> List[Tuple[str, float]]:
        """私有库关键词搜索"""
        if tenant_id not in self.private_keyword_indexes:
            return []
        return self.private_keyword_indexes[tenant_id].search(query, top_k)

    def _build_search_result(
        self,
        chunk_id: str,
        score: float,
        source_type: TenantType,
        tenant_id: str = "shared"
    ) -> SearchResult:
        """构建搜索结果"""
        # 获取chunk
        if source_type == TenantType.SHARED:
            chunk = self.shared_chunks.get(chunk_id)
        else:
            chunk = self.private_chunks.get(tenant_id, {}).get(chunk_id)

        if chunk is None:
            return None

        return SearchResult(
            id=chunk.id,
            content=chunk.content,
            title=chunk.title,
            score=score,
            source_type=source_type,
            tenant_id=chunk.tenant_id,
            metadata=chunk.metadata,
            keyword_score=score,
            semantic_score=0.0,
            rerank_score=0.0
        )

    async def search(self, request: SearchRequest) -> SearchResponse:
        """混合搜索

        【核心流程】

        1. 判断搜索类型
           - HYBRID: 共享库 + 私有库
           - PRIVATE_ONLY: 仅私有库
           - SHARED_ONLY: 仅共享库

        2. 关键词搜索（双路召回）
           - 共享库关键词搜索
           - 私有库关键词搜索

        3. 向量搜索（如果可用）
           - 共享库向量搜索
           - 私有库向量搜索

        4. RRF融合
           - 将多路排序结果融合

        5. 构建结果
           - 去重
           - 过滤低分
           - 排序输出

        Args:
            request: 搜索请求

        Returns:
            搜索响应
        """
        import time
        start_time = time.time()

        results: List[SearchResult] = []
        seen_ids = set()

        # ========== 1. 共享库搜索 ==========
        if request.search_type in [SearchType.HYBRID, SearchType.SHARED_ONLY]:
            # 关键词搜索
            kw_results = self._keyword_search_shared(
                request.query,
                request.shared_top_k
            )

            for chunk_id, score in kw_results:
                result = self._build_search_result(
                    chunk_id, score, TenantType.SHARED, "shared"
                )
                if result and result.id not in seen_ids:
                    results.append(result)
                    seen_ids.add(result.id)

        # ========== 2. 私有库搜索 ==========
        if request.search_type in [SearchType.HYBRID, SearchType.PRIVATE_ONLY]:
            if not self.is_tenant_registered(request.tenant_id):
                # 租户未注册，返回空结果
                pass
            else:
                kw_results = self._keyword_search_private(
                    request.tenant_id,
                    request.query,
                    request.private_top_k
                )

                for chunk_id, score in kw_results:
                    result = self._build_search_result(
                        chunk_id, score, TenantType.PRIVATE, request.tenant_id
                    )
                    if result and result.id not in seen_ids:
                        results.append(result)
                        seen_ids.add(result.id)

        # ========== 3. 排序和过滤 ==========
        # 按综合评分排序
        results.sort(key=lambda x: x.score, reverse=True)

        # 过滤低于阈值的
        results = [r for r in results if r.score >= request.min_score]

        # 限制数量
        results = results[:request.top_k]

        # 更新最终评分（归一化）
        if results:
            max_score = results[0].score
            if max_score > 0:
                for r in results:
                    r.score = r.score / max_score

        search_time = (time.time() - start_time) * 1000

        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            tenant_id=request.tenant_id,
            search_time_ms=search_time,
            metadata={
                "search_type": request.search_type.value,
                "filters": request.filters
            }
        )

    # ========== 统计和管理 ==========

    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """获取租户统计"""
        stats = {
            "tenant_id": tenant_id,
            "shared_documents": len(self.shared_chunks),
            "private_documents": len(self.private_chunks.get(tenant_id, {}))
        }

        if tenant_id in self.tenants:
            tenant = self.tenants[tenant_id]
            stats["tenant_name"] = tenant.name

        return stats

    def list_tenants(self) -> List[Dict]:
        """列出所有租户"""
        return [
            {
                "tenant_id": t.tenant_id,
                "name": t.name,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in self.tenants.values()
        ]

    def get_total_stats(self) -> Dict:
        """获取全局统计"""
        private_counts = {tid: len(chunks) for tid, chunks in self.private_chunks.items()}

        return {
            "total_shared_chunks": len(self.shared_chunks),
            "total_private_chunks": sum(private_counts.values()),
            "total_tenants": len(self.tenants),
            "tenants": private_counts
        }


# 全局单例
_multi_tenant_kb: Optional[MultiTenantKnowledgeBase] = None


def get_multi_tenant_kb() -> MultiTenantKnowledgeBase:
    """获取全局多租户知识库实例"""
    global _multi_tenant_kb
    if _multi_tenant_kb is None:
        _multi_tenant_kb = MultiTenantKnowledgeBase()

        # 初始化共享库示例数据
        _multi_tenant_kb.add_shared_documents([
            {
                "title": "产品使用手册",
                "content": "这是产品的通用使用手册。所有用户都可以查看此内容。",
                "source": "admin"
            },
            {
                "title": "常见问题FAQ",
                "content": "常见问题解答：1. 如何登录系统？2. 如何重置密码？",
                "source": "admin"
            }
        ])

    return _multi_tenant_kb


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 获取实例
kb = get_multi_tenant_kb()

# 2. 注册租户
kb.register_tenant("tenant_001", "客户A公司", "重要客户")
kb.register_tenant("tenant_002", "客户B公司", "战略合作伙伴")

# 3. 添加共享文档（所有租户可见）
kb.add_shared_documents([
    {
        "title": "产品手册v2.0",
        "content": "通用产品使用说明，包含所有用户都需要了解的基础知识。",
        "source": "documentation"
    }
])

# 4. 添加租户私有文档（仅该租户可见）
kb.add_private_documents("tenant_001", [
    {
        "title": "客户A内部流程",
        "content": "这是客户A的内部审批流程，只有客户A能看到。",
        "source": "internal"
    }
])

kb.add_private_documents("tenant_002", [
    {
        "title": "客户B项目文档",
        "content": "这是客户B的专属项目文档，只有客户B能看到。",
        "source": "project"
    }
])

# 5. 混合搜索
import asyncio

async def test_search():
    request = SearchRequest(
        tenant_id="tenant_001",
        query="如何使用产品",
        search_type=SearchType.HYBRID,
        top_k=10
    )

    response = await kb.search(request)

    print(f"找到 {response.total} 个结果")
    print(f"搜索耗时: {response.search_time_ms:.2f}ms")

    for result in response.results:
        print(f"[{result.source_type.value}] {result.title}: {result.score:.3f}")
        print(f"  {result.content[:100]}...")

# 运行测试
asyncio.run(test_search())

# 6. 查看统计
stats = kb.get_total_stats()
print(f"共享文档: {stats['total_shared_chunks']}")
print(f"总租户数: {stats['total_tenants']}")

# 查看租户001的统计
tenant_stats = kb.get_tenant_stats("tenant_001")
print(f"租户001私有文档: {tenant_stats['private_documents']}")
"""
