"""
RAG管道 - 端到端实现
====================

【学习要点】RAG完整流程
1. Document Loading   → 加载文档(PDF/Word/网页)
2. Text Splitting     → 文本分割(chunking)
3. Embedding          → 向量化
4. Vector Storage     → 向量存储
5. Retrieval          → 检索
6. Generation         → 生成回答

【为什么需要管道化？】
- 模块化: 各环节独立可替换
- 可追踪: 每步都可监控
- 可优化: 单独优化每个环节
"""

from typing import List, Dict, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import time

# 导入项目模块
from knowledge.parsers import PDFParser, WordParser, WebParser, ExcelParser, PowerPointParser
from knowledge.chunking.em_splitter import EMSplitter
from knowledge.vectorstore.chromadb_handler import ChromaDBHandler
from knowledge.vectorstore.milvus_handler import MilvusHandler
from core.prompt_engine import prompt_manager, build_rag_prompt
from core.guardrails import guardrails
from core.llm import get_llm
from memory.short_term import short_term_memory, MemoryType
from logs.error_logs.error_logger import error_logger, ErrorLevel
from knowledge.retrieval import get_reranker, HybridReranker
from core.rag_validator import get_query_validator, ValidationLevel


class DocumentType(Enum):
    """支持的文档类型"""
    PDF = "pdf"
    WORD = "docx"
    WEB = "url"
    TEXT = "txt"
    MARKDOWN = "md"
    EXCEL = "xlsx"
    POWERPOINT = "pptx"


@dataclass
class Document:
    """文档对象"""
    id: str
    content: str
    source: str
    doc_type: DocumentType
    metadata: Dict[str, Any]


@dataclass
class Chunk:
    """文本块"""
    id: str
    content: str
    doc_id: str
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    score: float
    doc_id: str
    metadata: Dict[str, Any]


@dataclass
class RAGConfig:
    """RAG配置"""
    # 向量存储选择
    use_milvus: bool = False  # True=Milvus, False=ChromaDB

    # 分割配置
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chunk_size: int = 100

    # 检索配置
    top_k: int = 5
    score_threshold: float = 0.5
    initial_k: int = 20  # 初步检索数量（用于重排序）

    # 混合检索配置
    keyword_weight: float = 0.5  # 关键词检索权重 (0.0-1.0)
    vector_weight: float = 0.5  # 向量检索权重 (0.0-1.0)
    fusion_method: str = "rrf"  # 融合方法: rrf, weighted, concat

    # 重排序配置
    use_reranker: bool = True
    reranker_type: str = "hybrid"  # cross_encoder, bm25, hybrid

    # 生成配置
    max_context_tokens: int = 3000


class RAGPipeline:
    """RAG管道

    【架构】
    Pipeline = Loader + Splitter + Embedder + VectorStore + Retriever + Generator
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()

        # 初始化组件
        self._init_parsers()
        self._init_splitter()
        self._init_vectorstore()
        self._init_embedder()

    def _init_parsers(self):
        """初始化文档解析器"""
        self.parsers = {
            DocumentType.PDF: PDFParser(),
            DocumentType.WORD: WordParser(),
            DocumentType.WEB: WebParser(),
            DocumentType.EXCEL: ExcelParser(),
            DocumentType.POWERPOINT: PowerPointParser(),
        }

    def _init_splitter(self):
        """初始化文本分割器"""
        self.splitter = EMSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            min_chunk_size=self.config.min_chunk_size
        )

    def _init_vectorstore(self):
        """初始化向量存储"""
        if self.config.use_milvus:
            self.vectorstore = MilvusHandler(
                collection_name="rag_knowledge_base"
            )
        else:
            self.vectorstore = ChromaDBHandler(
                persist_directory="G:/claude_code_project/data/chromadb/rag",
                collection_name="rag_knowledge_base"
            )

    def _init_embedder(self):
        """初始化Embedding模型

        【学习要点】Embedding模型
        - 将文本转为向量
        - 语义相似的内容向量也相似
        - 模型选择影响检索质量
        """
        from langchain_huggingface import HuggingFaceEmbeddings
        import os

        # 优先使用本地模型
        local_model_path = "G:/claude_model/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
        if os.path.exists(local_model_path):
            self.embedder = HuggingFaceEmbeddings(
                model_name=local_model_path
            )
        else:
            self.embedder = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

    # ========== 文档加载 ==========

    def load_document(
        self,
        source: str,
        doc_type: Optional[DocumentType] = None
    ) -> Document:
        """加载文档

        Args:
            source: 文件路径或URL
            doc_type: 文档类型（自动检测）

        Returns:
            Document对象
        """
        # 自动检测类型
        if doc_type is None:
            doc_type = self._detect_doc_type(source)

        # 解析文档
        if doc_type == DocumentType.PDF:
            result = self.parsers[DocumentType.PDF].parse(source)
            content = "\n".join([p["text"] for p in result["content"]])
            metadata = {"pages": result["num_pages"]}

        elif doc_type == DocumentType.WORD:
            result = self.parsers[DocumentType.WORD].parse(source)
            content = "\n".join([
                p["text"] for p in result["content"]
                if p.get("type") == "paragraph"
            ])
            metadata = {
                "paragraphs": result["num_paragraphs"],
                "tables": result["num_tables"]
            }

        elif doc_type == DocumentType.WEB:
            result = self.parsers[DocumentType.WEB].parse(source)
            content = result["text"]
            metadata = {"title": result.get("title", "")}

        elif doc_type == DocumentType.EXCEL:
            result = self.parsers[DocumentType.EXCEL].parse(source)
            content = result.content
            metadata = {
                "sheets": result.sheets,
                "sheet_count": len(result.sheets),
                "file_name": result.metadata.get("file_name", "")
            }

        elif doc_type == DocumentType.POWERPOINT:
            result = self.parsers[DocumentType.POWERPOINT].parse(source)
            content = result.content
            metadata = {
                "slides": result.slides,
                "slide_count": len(result.slides),
                "file_name": result.metadata.get("file_name", "")
            }

        else:
            # 纯文本
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
            metadata = {}

        # 生成文档ID
        doc_id = f"doc_{int(time.time() * 1000)}"

        return Document(
            id=doc_id,
            content=content,
            source=source,
            doc_type=doc_type,
            metadata=metadata
        )

    def _detect_doc_type(self, source: str) -> DocumentType:
        """检测文档类型"""
        if source.startswith("http"):
            return DocumentType.WEB

        ext = Path(source).suffix.lower()
        type_map = {
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.WORD,
            ".doc": DocumentType.WORD,
            ".txt": DocumentType.TEXT,
            ".md": DocumentType.MARKDOWN,
            ".xlsx": DocumentType.EXCEL,
            ".xls": DocumentType.EXCEL,
            ".pptx": DocumentType.POWERPOINT
        }

        return type_map.get(ext, DocumentType.TEXT)

    # ========== 文本分割 ==========

    def split_document(self, document: Document) -> List[Chunk]:
        """分割文档为文本块

        【学习要点】分割策略
        - chunk_size: 块大小（太小丢失上下文，太大降低检索精度）
        - overlap: 重叠（保持块之间连续性）
        - 语义分割: 按句子/段落分割，保持语义完整
        """
        texts = self.splitter.split_text(document.content)

        chunks = []
        for i, text in enumerate(texts):
            chunk = Chunk(
                id=f"{document.id}_chunk_{i}",
                content=text,
                doc_id=document.id,
                chunk_index=i,
                metadata={
                    "source": document.source,
                    "doc_type": document.doc_type.value,
                    **document.metadata
                }
            )
            chunks.append(chunk)

        return chunks

    # ========== 向量存储 ==========

    def index_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> Dict:
        """索引文档

        【流程】
        1. 加载文档
        2. 分割文本
        3. 向量化
        4. 存储到向量数据库
        """
        all_chunks = []
        indexed_count = 0

        for doc in documents:
            try:
                # 分割
                chunks = self.split_document(doc)
                all_chunks.extend(chunks)

                # 批量索引
                if len(all_chunks) >= batch_size:
                    self._index_chunks(all_chunks)
                    indexed_count += len(all_chunks)
                    all_chunks = []

            except Exception as e:
                error_logger.log(
                    error_type="IndexError",
                    message=f"Failed to index {doc.source}: {str(e)}",
                    level=ErrorLevel.ERROR,
                    exc_info=e
                )

        # 剩余的块
        if all_chunks:
            self._index_chunks(all_chunks)
            indexed_count += len(all_chunks)

        return {
            "documents_processed": len(documents),
            "chunks_indexed": indexed_count
        }

    def _index_chunks(self, chunks: List[Chunk]):
        """索引文本块"""
        texts = [c.content for c in chunks]
        metadatas = [
            {
                "chunk_id": c.id,
                "doc_id": c.doc_id,
                "chunk_index": c.chunk_index,
                **c.metadata
            }
            for c in chunks
        ]
        ids = [c.id for c in chunks]

        self.vectorstore.add_documents(
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )

    # ========== 检索 ==========

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_dict: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """检索相关文档

        Args:
            query: 查询文本
            top_k: 返回数量
            filter_dict: 过滤条件

        Returns:
            检索结果列表
        """
        top_k = top_k or self.config.top_k

        # Step 1: 初步检索（使用更大的k用于重排序）
        initial_k = self.config.initial_k if self.config.use_reranker else top_k
        results = self.vectorstore.similarity_search(
            query=query,
            k=initial_k,
            filter_dict=filter_dict
        )

        # Step 2: 重排序（如果启用）
        if self.config.use_reranker and results:
            results = self._apply_reranking(query, results)

        # DEBUG: 打印原始 ChromaDB 分数
        if results:
            scores = [r["similarity_score"] for r in results]
            print(f"[RETRIEVE] ChromaDB scores before filtering: min={min(scores):.4f}, max={max(scores):.4f}, threshold={self.config.score_threshold}")

        # 转换结果
        # 注意：ChromaDB L2 distance 值可能很大（如60+），这是embedding向量空间的特点
        # 判断是否有"相关知识"应该看是否有结果返回，而不是绝对阈值
        retrieval_results = []
        for r in results:
            retrieval_results.append(RetrievalResult(
                content=r["content"],
                score=r["similarity_score"],
                doc_id=r["metadata"].get("doc_id", ""),
                metadata=r["metadata"]
            ))

        # 返回top_k
        return retrieval_results[:top_k]

    def _apply_reranking(
        self,
        query: str,
        results: List[Dict]
    ) -> List[Dict]:
        """应用重排序

        Args:
            query: 查询文本
            results: 初步检索结果

        Returns:
            重排序后的结果
        """
        if not results:
            return results

        try:
            reranker = get_reranker()
            reranked = reranker.rerank(query, results, top_k=len(results))

            # 检查 reranker 是否返回了有效分数（不是全 0）
            rerank_scores = [r.score for r in reranked]
            if max(rerank_scores) > 0:
                # Reranker 返回有效分数，更新并排序
                for r in reranked:
                    results[r.index]["similarity_score"] = r.score
                results = [results[r.index] for r in reranked]
                print(f"[RERANK] Used reranker scores: max={max(rerank_scores):.4f}")
            else:
                # Reranker 返回无效分数（全是 0），保留原始 ChromaDB 分数
                print(f"[RERANK] Reranker returned all zeros, keeping original ChromaDB scores")
                # 按原始分数排序
                results.sort(key=lambda x: x["similarity_score"])

        except Exception as e:
            error_logger.log(
                error_type="RerankError",
                message=f"Reranking failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            # 重排序失败时保持原顺序和分数
            print(f"[RERANK] Exception: {str(e)}, keeping original order")

        return results

    # ========== 生成 ==========

    async def generate(
        self,
        query: str,
        retrieval_results: List[RetrievalResult],
        session_id: Optional[str] = None
    ) -> Dict:
        """生成回答

        【流程】
        1. 构建上下文（检索结果）
        2. 构建Prompt
        3. 调用LLM生成

        Returns:
            包含answer和token_usage的字典
        """
        # 构建上下文
        context_parts = []
        for i, r in enumerate(retrieval_results):
            context_parts.append(
                f"[Source {i+1}] (score: {r.score:.2f})\n{r.content}"
            )
        context = "\n\n".join(context_parts)

        # 构建Prompt
        system_prompt, user_prompt = build_rag_prompt(query, context)

        # Token使用量初始化
        token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        # 调用实际LLM生成
        try:
            llm = get_llm()
            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3
            )
            answer = response.content
            # 注意：token记录已在LLMWrapper.generate()中完成，这里不要重复记录
            # 但我们需要获取token usage用于per-session追踪
            if response.usage:
                token_usage = response.usage

        except Exception as e:
            error_logger.log(
                error_type="LLMGenerationError",
                message=f"LLM generation failed: {str(e)}",
                level=ErrorLevel.ERROR
            )
            # 降级：返回上下文+问题
            answer = f"Based on {len(retrieval_results)} relevant sources:\n\n{context}"

        # 保存到短期记忆
        if session_id:
            short_term_memory.add_to_session(
                session_id=session_id,
                content=f"Query: {query}\nResponse: {answer[:500]}...",
                memory_type=MemoryType.INTERMEDIATE_RESULT,
                metadata={"query": query, "sources": len(retrieval_results)}
            )

        return {"answer": answer, "token_usage": token_usage}

    # ========== 端到端RAG ==========

    async def query(
        self,
        question: str,
        session_id: Optional[str] = None,
        use_knowledge: bool = True
    ) -> Dict:
        """完整的RAG查询

        Args:
            question: 用户问题
            session_id: 会话ID
            use_knowledge: 是否使用知识库

        Returns:
            包含答案和来源的字典
        """
        # 0. 输入验证（清洗查询）
        validator = get_query_validator(ValidationLevel.NORMAL)
        validation_result = validator.validate(question)
        if not validation_result.is_valid:
            return {
                "answer": f"Invalid query: {validation_result.error_message}",
                "sources": [],
                "error": True,
                "validation_error": True
            }
        question = validation_result.cleaned_query

        # 0.1 身份类问题检查 - 直接返回Agent介绍，不走RAG
        identity_keywords = ["你是谁", "who are you", "what are you", "你是什么", "你的身份", "你叫什么", "你叫", "叫什么名字", "who am i", "introduce yourself", "你的名字"]
        if any(kw.lower() in question.lower() for kw in identity_keywords):
            return {
                "answer": "你好！我是AI Multi-Agent系统，一个智能助手。我可以帮你：\n1. 查询知识库、回答问题\n2. 进行技术开发和代码编写\n3. 编写文档和测试\n4. 项目管理和任务规划\n有什么我可以帮你的吗？",
                "sources": [],
                "guardrail_passed": True,
                "used_rag": False
            }

        # 0.5. 问候语检查 - 直接返回问候，不走RAG
        greeting_keywords = ["你好", "hi", "hello", "嗨", "您好", "hey", "早上好", "下午好", "晚上好", "hi there", "greetings"]
        if any(kw.lower() in question.lower() for kw in greeting_keywords):
            return {
                "answer": "你好！有什么我可以帮助你的吗？我可以回答问题、编写代码、管理知识库等。",
                "sources": [],
                "guardrail_passed": True,
                "used_rag": False
            }

        # 1. Guardrails检查输入
        guard_result = guardrails.check_input(question)
        if not guard_result.passed:
            return {
                "answer": f"I cannot process this request: {guard_result.message}",
                "sources": [],
                "error": True,
                "guardrail_result": guard_result.model_dump()
            }

        # 2. 检索
        if use_knowledge:
            retrieval_results = self.retrieve(question)
        else:
            retrieval_results = []

        # DEBUG: 打印检索结果分数
        print(f"[DEBUG] retrieval_results count: {len(retrieval_results)}")
        for r in retrieval_results:
            print(f"[DEBUG] score={r.score}, threshold={self.config.score_threshold}")

        # 3. 判断是否有相关知识（用于标记和日志）
        has_relevant_knowledge = False
        if retrieval_results:
            best_score = min(r.score for r in retrieval_results)
            if best_score < 1.0:
                has_relevant_knowledge = True
            elif best_score > 50.0:
                has_relevant_knowledge = False
            else:
                has_relevant_knowledge = best_score < 10.0
            print(f"[DEBUG] has_relevant_knowledge={has_relevant_knowledge}, best_score={best_score:.4f}")
        else:
            print(f"[DEBUG] has_relevant_knowledge={has_relevant_knowledge}, no docs retrieved")

        # 4. 始终调用LLM生成回答（确保token被记录）
        # 只有在有相关知识时才传入检索结果作为上下文
        generate_result = await self.generate(question, retrieval_results if has_relevant_knowledge else [], session_id)
        answer = generate_result["answer"]
        token_usage = generate_result.get("token_usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

        # 4. Guardrails检查输出
        output_result = guardrails.check_output(answer)

        return {
            "answer": answer,
            "sources": [
                {
                    "content": r.content[:200] + "...",
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in retrieval_results
            ],
            "guardrail_passed": output_result.passed,
            "token_usage": token_usage
        }

    # ========== 工具方法 ==========

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "vectorstore": self.vectorstore.get_collection_stats(),
            "config": {
                "chunk_size": self.config.chunk_size,
                "top_k": self.config.top_k,
                "use_milvus": self.config.use_milvus
            }
        }


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 初始化管道
rag = RAGPipeline()

# 2. 索引文档
docs = [
    rag.load_document("document1.pdf"),
    rag.load_document("document2.docx"),
    rag.load_document("https://example.com/article")
]
result = rag.index_documents(docs)
print(f"Indexed: {result}")

# 3. 查询
response = rag.query(
    question="What is the main topic?",
    session_id="user_123"
)

print(f"Answer: {response['answer']}")
print(f"Sources: {len(response['sources'])}")

# 4. 查看统计
stats = rag.get_stats()
"""
