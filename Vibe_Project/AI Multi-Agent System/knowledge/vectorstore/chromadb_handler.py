"""
ChromaDB向量存储处理器
======================

【学习要点】ChromaDB是什么?
- 轻量级向量数据库
- Python原生，使用简单
- 支持embedded模式（不需要单独服务）
- 适合: 学习、demo、小规模生产

【对比】
ChromaDB: 简单易用，单机版，适合学习
Milvus: 分布式，高并发，生产级
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


class ChromaDBHandler:
    """ChromaDB处理器

    【架构】
    ChromaDB = Collection(集合) + Embedding(嵌入) + Vector(向量)

    Collection: 文档集合，类似于表
    Embedding: 将文本转为向量的模型
    Vector: 文档的向量表示
    """

    def __init__(
        self,
        persist_directory: str = "G:/claude_code_project/data/chromadb",
        collection_name: str = "knowledge_base",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        # 初始化embedding函数
        # 【学习要点】Sentence Transformers
        # - 将句子转换为向量
        # - 语义相似的内容向量也相似
        # 支持本地模型路径
        local_model_path = "G:/claude_model/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
        if os.path.exists(local_model_path):
            self.embeddings = HuggingFaceEmbeddings(
                model_name=local_model_path
            )
        else:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model
            )

        # 初始化ChromaDB客户端
        # 【学习要点】持久化存储
        # - 数据保存在本地磁盘
        # - 重启后数据不丢失
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # 使用PersistentClient避免实例冲突
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # 初始化vectorstore
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加文档

        Args:
            texts: 文档内容列表
            metadatas: 元数据列表（如{"source": "pdf", "page": 1}）
            ids: 文档ID列表

        Returns:
            生成的文档ID列表

        【流程】
        1. 文本 -> Embedding模型 -> 向量
        2. 向量 + 元数据 -> 存储到Collection
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]

        # LangChain的Chroma包装器会自动处理embedding
        self.vectorstore.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )

        print(f"[ChromaDB] Added {len(texts)} documents")
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """相似性搜索

        Args:
            query: 查询文本
            k: 返回数量
            filter_dict: 过滤条件

        Returns:
            相似文档列表

        【流程】
        1. 查询文本 -> Embedding -> 向量
        2. 在Collection中找最相似的k个向量
        3. 返回对应的文档
        """
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )

        # 格式化结果
        formatted = []
        for doc, score in results:
            formatted.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": score  # 越低越相似
            })

        return formatted

    def similarity_search_by_vector(
        self,
        vector: List[float],
        k: int = 5
    ) -> List[Dict]:
        """通过向量搜索

        【使用场景】
        - 已有embedding，直接查向量
        - 用于以图搜图等场景
        """
        results = self.vectorstore.similarity_search_by_vector(
            embedding=vector,
            k=k
        )

        return [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in results
        ]

    def get_collection_stats(self) -> Dict:
        """获取集合统计信息

        【学习要点】元数据统计
        - 了解数据分布
        - 监控数据规模
        """
        collection = self.vectorstore._collection
        return {
            "name": self.collection_name,
            "count": collection.count(),
            "persist_directory": self.persist_directory
        }

    def delete_document(self, doc_id: str) -> bool:
        """删除文档

        Args:
            doc_id: 文档ID

        Returns:
            是否删除成功
        """
        try:
            self.vectorstore.delete(ids=[doc_id])
            print(f"[ChromaDB] Deleted document: {doc_id}")
            return True
        except Exception as e:
            print(f"[ChromaDB] Delete failed: {e}")
            return False

    def delete_by_filter(self, filter_dict: Dict) -> int:
        """根据过滤条件删除文档

        Args:
            filter_dict: 过滤条件，如 {"source": "doc.pdf"}

        Returns:
            删除的文档数量
        """
        try:
            # 使用ChromaDB原生的where条件查询
            # 注意：这是一个简化实现，完整实现需要使用ChromaDB的where语法
            results = self.vectorstore._collection.get(
                where=filter_dict,
                limit=1000
            )

            if results and results.get("ids"):
                doc_ids = results["ids"]
                self.vectorstore.delete(ids=doc_ids)
                print(f"[ChromaDB] Deleted {len(doc_ids)} documents by filter")
                return len(doc_ids)

            return 0
        except Exception as e:
            print(f"[ChromaDB] Filter delete failed: {e}")
            return 0

        return {
            "name": self.collection_name,
            "count": collection.count(),
            "persist_directory": self.persist_directory
        }

    def delete_collection(self) -> None:
        """删除集合

        【注意】这是不可逆操作
        """
        self.vectorstore.delete_collection()
        print(f"[ChromaDB] Deleted collection: {self.collection_name}")

    def persist(self) -> None:
        """持久化数据到磁盘

        【学习要点】持久化
        - 数据保存在persist_directory
        - 手动调用或自动触发
        """
        self.client.persist()
        print("[ChromaDB] Data persisted to disk")


# ========== 使用示例 ==========
"""
【学习要点】完整使用流程

# 1. 初始化
handler = ChromaDBHandler(
    persist_directory="data/chromadb",
    collection_name="my_docs"
)

# 2. 添加文档
handler.add_documents(
    texts=[
        "Python是一种编程语言",
        "机器学习是AI的一个分支",
        "深度学习是机器学习的子领域"
    ],
    metadatas=[
        {"source": "doc1", "category": "programming"},
        {"source": "doc2", "category": "ai"},
        {"source": "doc3", "category": "ai"}
    ]
)

# 3. 搜索
results = handler.similarity_search("什么是深度学习?", k=2)

# 4. 查看统计
stats = handler.get_collection_stats()
"""
