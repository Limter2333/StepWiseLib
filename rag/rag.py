import os
from typing import List, Optional

import chromadb
from sentence_transformers import CrossEncoder, SentenceTransformer

# 默认知识文档路径：始终基于当前文件位置解析，避免因运行目录不同而找不到文档
_DEFAULT_DOC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doc.md")


class RAGRetriever:
    """封装向量索引与检索，供 Agent 作为检索工具调用

    RAG 核心思想：不把全部知识硬塞给 LLM，而是先建立文档向量索引，
    收到问题后先检索出最相关的少量片段，再把这些片段交给 LLM 生成回答。
    """

    def __init__(
        self,
        embedding_model_name: str = "shibing624/text2vec-base-chinese",
        rerank_model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        collection_name: str = "default",
    ) -> None:
        # embedding 模型：把文本转成向量（用于相似度检索）
        self.embedding_model_name = embedding_model_name
        # 重排模型名称：CrossEncoder 直接对"问题-片段"对打分，比向量相似度更准
        self.rerank_model_name = rerank_model_name
        # 加载 embedding 模型（模型体积小，启动时直接加载）
        self.embedding_model = SentenceTransformer(embedding_model_name)
        # 重排模型懒加载：首次真正用到 rerank 时才加载，避免每次都耗时初始化
        self._rerank_model = None
        # chromadb 内存版客户端 + 默认集合，用于存储向量索引
        self.collection = chromadb.EphemeralClient().get_or_create_collection(
            name=collection_name
        )

    @property
    def rerank_model(self):
        """懒加载 CrossEncoder 重排模型，只用一次加载并缓存"""
        if self._rerank_model is None:
            self._rerank_model = CrossEncoder(self.rerank_model_name)
        return self._rerank_model

    def index_document(self, doc_file: str) -> int:
        """将文档分片、向量化并写入向量库，返回分片数量

        这是 RAG 的"索引阶段"（离线执行）：文档更新后需要重新执行一次。
        """
        # 1. 分片：把长文档按空行切成多个独立片段
        chunks = self._split_into_chunks(doc_file)
        # 先清空旧索引，保证重复索引时结果一致（临时集合为空时 delete 可能报错，忽略即可）
        try:
            self.collection.delete()
        except Exception:
            pass
        # 2. 向量化 + 入库：每个片段计算 embedding 后写入向量库
        for i, chunk in enumerate(chunks):
            self.collection.add(
                documents=[chunk],          # 原始文本（供最后拼接返回）
                embeddings=[self._embed(chunk)],  # 向量表示（供相似度检索）
                ids=[str(i)],               # 唯一 id
            )
        return len(chunks)

    def retrieve(self, query: str, top_k: int = 5, rerank: bool = True) -> str:
        """检索与 query 最相关的 top_k 条片段，返回拼接好的文本

        RAG 的"召回阶段"（在线执行）：每次 Agent 调用检索工具都会走到这里。
        """
        # 1. 召回：把问题向量化，在向量库中按余弦相似度找出 top_k 个候选片段
        results = self.collection.query(
            query_embeddings=[self._embed(query)],
            n_results=top_k,
        )
        chunks = results["documents"][0]

        # 2. 重排（可选）：用 CrossEncoder 对"问题-片段"逐对打分，按更精准的相关性排序
        if rerank:
            pairs = [(query, chunk) for chunk in chunks]
            scores = self.rerank_model.predict(pairs)
            # 按得分从高到低排序，再截取前 top_k 个
            chunks = [
                chunk
                for chunk, _ in sorted(
                    zip(chunks, scores), key=lambda x: x[1], reverse=True
                )
            ][:top_k]

        # 3. 格式化：给每个片段加序号标记，方便 LLM 在 observation 中引用
        return "\n\n".join(
            f"[片段 {i + 1}]\n{chunk}" for i, chunk in enumerate(chunks)
        )

    @staticmethod
    def _split_into_chunks(doc_file: str) -> List[str]:
        """简单的分片策略：按连续空行（\\n\\n）切分，并丢弃空片段"""
        with open(doc_file, "r", encoding="utf-8") as file:
            content = file.read()
        return [chunk for chunk in content.split("\n\n") if chunk.strip()]

    def _embed(self, text: str) -> List[float]:
        """文本向量化：encode 后归一化，使向量相似度比较结果更稳定"""
        embedding = self.embedding_model.encode(text, normalize_embeddings=True)
        return embedding.tolist()


# 模块级单例：模型加载很耗时，进程内只初始化一次
_retriever: Optional[RAGRetriever] = None


def get_retriever() -> RAGRetriever:
    """懒加载全局检索器，首次调用时加载模型并建立默认文档索引"""
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
        _retriever.index_document(_DEFAULT_DOC_FILE)
    return _retriever


def retrieve(query: str, top_k: int = 5) -> str:
    """从本地知识库中检索与问题最相关的文档片段（例如知识库中哆啦A梦与超级赛亚人的故事、秘密道具等），返回若干片段文本，请据此回答用户问题。

    这是暴露给 Agent 的入口函数：
    - Agent 通过工具调用机制执行 <action>retrieve("...")</action>
    - 返回的片段文本会成为 observation 提供给 LLM 继续推理
    """
    return get_retriever().retrieve(query, top_k=top_k)
