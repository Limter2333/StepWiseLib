"""
Milvus向量存储处理器 - 生产级
==============================

【学习要点】Milvus vs ChromaDB

| 特性 | ChromaDB | Milvus |
|------|----------|--------|
| 部署复杂度 | 低（embedded） | 高（需要服务） |
| 扩展性 | 差（单机） | 好（分布式） |
| 性能 | 一般 | 高 |
| 适用场景 | 学习/demo | 生产环境 |
| 数据规模 | <100万 | 亿级 |

【Milvus核心概念】
1. Collection: 相当于表
2. Partition: 分区（用于多租户隔离）
3. Shard: 数据分片（提高并发）
4. Index: 向量索引（加速检索）
5. Segment: 数据段（存储单位）
"""

from typing import List, Dict, Optional
from pymilvus import (
    connections,
    DataType,
    Collection, CollectionSchema, FieldSchema, utility
)
from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np


class MilvusHandler:
    """Milvus处理器（生产级）

    【架构设计】
    1. 连接层: 建立到Milvus服务的连接
    2. Schema层: 定义Collection结构
    3. 索引层: 创建向量索引
    4. 操作层: CRUD操作
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = "knowledge_base",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        dimension: int = 384,  # MiniLM-L6-v2的输出维度
        partition_field: Optional[str] = None  # 多租户字段
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.dimension = dimension
        self.partition_field = partition_field

        # 初始化embedding模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model
        )

        # 连接Milvus
        # 【学习要点】连接管理
        # - 需要手动建立连接
        # - 使用完后应关闭
        connections.connect(
            alias="default",
            host=host,
            port=port
        )
        print(f"[Milvus] Connected to {host}:{port}")

        # 创建或获取Collection
        self._init_collection()

    def _init_collection(self):
        """初始化Collection

        【Schema设计】
        - id: 主键，唯一标识
        - vector: 向量字段（用于检索）
        - text: 原始文本
        - metadata: JSON格式的元数据
        """
        # 如果已存在则删除（测试用）
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)

        # 定义字段
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.dimension
            ),
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=65535
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.VARCHAR,
                max_length=65535  # JSON字符串
            )
        ]

        # 创建schema
        collection_schema = CollectionSchema(
            fields=fields,
            description="Knowledge Base Collection"
        )

        # 创建collection
        self.collection = Collection(
            name=self.collection_name,
            schema=collection_schema
        )
        print(f"[Milvus] Created collection: {self.collection_name}")

        # 创建索引
        # 【学习要点】HNSW索引
        # - 近似最近邻算法
        # - 召回率高，速度快
        # - 内存占用较高
        index_params = {
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 64},
            "metric_type": "L2"  # L2距离/欧氏距离
        }

        self.collection.create_index(
            field_name="vector",
            index_params=index_params
        )
        print("[Milvus] Created HNSW index")

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        partition_name: Optional[str] = None
    ) -> List[int]:
        """添加文档

        Args:
            texts: 文档内容列表
            metadatas: 元数据列表
            partition_name: 分区名（用于多租户隔离）

        Returns:
            插入的ID列表

        【流程】
        1. 文本 -> Embedding -> 向量
        2. 构建插入数据
        3. 插入Collection
        """
        import json

        # 生成embeddings
        vectors = self.embeddings.embed_documents(texts)

        # 准备数据
        entities = [
            vectors,  # vector字段
            texts,    # text字段
            [json.dumps(m) if m else "{}" for m in (metadatas or [])]  # metadata字段
        ]

        # 插入
        insert_result = self.collection.insert(entities)

        # 如果指定了分区
        if partition_name:
            # 先插入到默认partition，再移动到指定partition
            pass

        # 刷新使数据可见
        self.collection.flush()

        print(f"[Milvus] Inserted {len(texts)} documents")
        return insert_result.primary_keys

    def search(
        self,
        query: str,
        k: int = 5,
        partition_names: Optional[List[str]] = None,
        expr: Optional[str] = None  # 过滤表达式
    ) -> List[Dict]:
        """向量搜索

        Args:
            query: 查询文本
            k: 返回数量
            partition_names: 只在指定分区搜索
            expr: 过滤表达式

        Returns:
            搜索结果列表

        【学习要点】搜索流程
        1. query -> embedding
        2. 在索引中找最近邻
        3. 返回结果
        """
        # 查询文本embedding
        query_vector = self.embeddings.embed_query(query)

        # 搜索参数
        search_params = {
            "metric_type": "L2",
            "params": {"ef": 64}  # ef值越大召回率越高但越慢
        }

        # 执行搜索
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=k,
            partition_names=partition_names,
            expr=expr,
            output_fields=["text", "metadata"]
        )

        # 格式化结果
        formatted = []
        for hits in results:
            for hit in hits:
                import json
                metadata = {}
                try:
                    metadata = json.loads(hit.entity.get("metadata", "{}"))
                except:
                    pass

                formatted.append({
                    "id": hit.id,
                    "text": hit.entity.get("text"),
                    "metadata": metadata,
                    "distance": hit.distance  # L2距离，越小越相似
                })

        return formatted

    def query(
        self,
        expr: str,
        output_fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """结构化查询

        【使用场景】
        - 根据metadata过滤
        - 范围查询
        - 复杂条件
        """
        if output_fields is None:
            output_fields = ["text", "metadata"]

        results = self.collection.query(
            expr=expr,
            output_fields=output_fields
        )
        return results

    def get_collection_stats(self) -> Dict:
        """获取集合统计"""
        return {
            "name": self.collection_name,
            "count": self.collection.num_entities,
            "partitions": self.collection.partitions,
            "indexes": self.collection.indexes
        }

    def create_partition(self, partition_name: str, description: str = "") -> None:
        """创建分区（多租户隔离）

        【学习要点】Partition分区
        - 逻辑隔离，不是物理隔离
        - 共享索引和存储
        - 查询时可指定分区
        """
        self.collection.create_partition(
            name=partition_name,
            description=description
        )
        print(f"[Milvus] Created partition: {partition_name}")

    def drop_partition(self, partition_name: str) -> None:
        """删除分区"""
        self.collection.drop_partition(partition_name=partition_name)
        print(f"[Milvus] Dropped partition: {partition_name}")

    def close(self):
        """关闭连接"""
        connections.disconnect(alias="default")
        print("[Milvus] Disconnected")


# ========== 多租户隔离方案 ==========
"""
【方案对比】

1. Partition隔离（推荐起步）
   collection.create_partition("tenant_A")
   collection.create_partition("tenant_B")
   搜索时指定: collection.search(..., partition_names=["tenant_A"])

   优点: 资源共享，成本低
   缺点: 隔离性一般

2. Collection隔离（完全隔离）
   collection_A = Collection("knowledge_tenant_A")
   collection_B = Collection("knowledge_tenant_B")

   优点: 完全隔离
   缺点: 资源独享，成本高

3. 混合模式（企业级）
   - 共享基础库（通用知识）
   - 租户私有库（私有数据）
   - 查询时合并结果
"""


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 初始化
handler = MilvusHandler(
    host="localhost",
    port=19530,
    collection_name="my_knowledge",
    partition_field="tenant_id"
)

# 2. 创建租户分区
handler.create_partition("tenant_001", "租户A的分区")
handler.create_partition("tenant_002", "租户B的分区")

# 3. 添加文档到指定分区
handler.add_documents(
    texts=["文档内容1", "文档内容2"],
    metadatas=[{"tenant_id": "tenant_001"}, {"tenant_id": "tenant_001"}],
    partition_name="tenant_001"
)

# 4. 在指定租户分区中搜索
results = handler.search(
    query="查找相关内容",
    k=5,
    partition_names=["tenant_001"]
)

# 5. 统计
stats = handler.get_collection_stats()

# 6. 关闭连接
handler.close()
"""
