"""
RAG Agent - 知识库智能体
========================

职责:
- 知识库构建
- 文档索引
- 知识检索
- 知识更新与维护
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os

# 导入项目模块
from knowledge.rag_pipeline import RAGPipeline, Document, DocumentType
from knowledge.vectorstore.chromadb_handler import ChromaDBHandler
from knowledge.vectorstore.milvus_handler import MilvusHandler
from logs.error_logs import error_logger, ErrorLevel


@dataclass
class KnowledgeSource:
    """知识来源"""
    id: str
    name: str
    source_type: str  # file, url, database
    path: str
    indexed_at: Optional[datetime] = None
    document_count: int = 0
    status: str = "pending"  # pending, indexing, ready, error


class KnowledgeBase:
    """知识库"""

    def __init__(self, name: str, use_milvus: bool = False):
        self.name = name
        self.sources: Dict[str, KnowledgeSource] = {}
        self.use_milvus = use_milvus

        # 初始化RAG管道
        from knowledge.rag_pipeline import RAGConfig
        config = RAGConfig(use_milvus=use_milvus)
        self.pipeline = RAGPipeline(config=config)

    def add_source(
        self,
        name: str,
        source_type: str,
        path: str
    ) -> KnowledgeSource:
        """添加知识来源"""
        source = KnowledgeSource(
            id=f"source_{len(self.sources) + 1}",
            name=name,
            source_type=source_type,
            path=path
        )
        self.sources[source.id] = source
        return source

    def get_source(self, source_id: str) -> Optional[KnowledgeSource]:
        """获取知识来源"""
        return self.sources.get(source_id)


class RAGAgent:
    """RAG智能体

    【能力】
    - 管理多个知识库
    - 索引文档
    - 回答问题
    - 知识更新
    """

    def __init__(self):
        self.name = "RAG Agent"
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}
        self.current_kb: Optional[KnowledgeBase] = None

    def create_knowledge_base(
        self,
        name: str,
        use_milvus: bool = False
    ) -> KnowledgeBase:
        """创建知识库"""
        kb = KnowledgeBase(name=name, use_milvus=use_milvus)
        self.knowledge_bases[name] = kb
        self.current_kb = kb  # Always set new KB as current

        return kb

    def switch_knowledge_base(self, name: str) -> bool:
        """切换当前知识库"""
        if name in self.knowledge_bases:
            self.current_kb = self.knowledge_bases[name]
            return True
        return False

    async def index_document(
        self,
        file_path: str,
        source_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """索引文档

        Args:
            file_path: 文件路径
            source_name: 来源名称
            metadata: 额外元数据

        Returns:
            索引结果
        """
        if self.current_kb is None:
            raise ValueError("No knowledge base selected")

        try:
            # 检测文档类型
            doc_type = self._detect_doc_type(file_path)

            # 加载文档
            document = self.current_kb.pipeline.load_document(file_path, doc_type)

            # 添加来源
            if source_name:
                source = self.current_kb.add_source(
                    name=source_name,
                    source_type=doc_type.value,
                    path=file_path
                )
                document.metadata["source_id"] = source.id
                source.status = "indexing"

            # 索引
            result = self.current_kb.pipeline.index_documents([document])

            # 更新来源状态
            if source_name:
                source.status = "ready"
                source.indexed_at = datetime.now()
                source.document_count = result["chunks_indexed"]

            return {
                "success": True,
                "document_id": document.id,
                "chunks_indexed": result["chunks_indexed"],
                "source": source_name
            }

        except Exception as e:
            error_logger.log(
                error_type="IndexError",
                message=f"Failed to index {file_path}: {str(e)}",
                level=ErrorLevel.ERROR,
                exc_info=e
            )
            return {
                "success": False,
                "error": str(e)
            }

    async def index_directory(
        self,
        directory_path: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = True
    ) -> Dict:
        """批量索引目录中的文档

        Args:
            directory_path: 目录路径
            extensions: 要索引的文件扩展名
            recursive: 是否递归子目录
        """
        if self.current_kb is None:
            raise ValueError("No knowledge base selected")

        extensions = extensions or [".pdf", ".docx", ".txt", ".md", ".html"]
        indexed_count = 0
        failed_count = 0
        errors = []

        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    result = await self.index_document(file_path, source_name=file)

                    if result["success"]:
                        indexed_count += 1
                    else:
                        failed_count += 1
                        errors.append({"file": file_path, "error": result.get("error")})

            if not recursive:
                break

        return {
            "indexed": indexed_count,
            "failed": failed_count,
            "errors": errors
        }

    async def query(
        self,
        question: str,
        top_k: int = 5,
        use_rag: bool = True
    ) -> Dict:
        """查询知识库

        Args:
            question: 问题
            top_k: 返回数量
            use_rag: 是否使用RAG
        """
        if self.current_kb is None:
            raise ValueError("No knowledge base selected")

        try:
            result = self.current_kb.pipeline.query(
                question=question,
                use_knowledge=use_rag
            )

            return {
                "success": True,
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
                "source_count": len(result["sources"])
            }

        except Exception as e:
            error_logger.log(
                error_type="QueryError",
                message=f"Failed to query: {str(e)}",
                level=ErrorLevel.ERROR,
                exc_info=e
            )
            return {
                "success": False,
                "error": str(e)
            }

    async def update_document(
        self,
        old_file_path: str,
        new_file_path: str
    ) -> bool:
        """更新文档"""
        # 实际实现需要删除旧文档的索引，然后索引新文档
        # 这里简化处理
        await self.index_document(new_file_path)
        return True

    async def delete_document(self, file_path: str) -> bool:
        """删除文档索引"""
        # 需要实现向量存储的删除功能
        return True

    def get_knowledge_base_stats(self, name: str) -> Optional[Dict]:
        """获取知识库统计"""
        if name not in self.knowledge_bases:
            return None

        kb = self.knowledge_bases[name]
        stats = kb.pipeline.get_stats()

        return {
            "name": name,
            "sources": len(kb.sources),
            "vectorstore": stats["vectorstore"],
            "config": stats["config"]
        }

    def list_knowledge_bases(self) -> List[Dict]:
        """列出所有知识库"""
        return [
            {
                "name": name,
                "is_current": kb == self.current_kb,
                "sources_count": len(kb.sources)
            }
            for name, kb in self.knowledge_bases.items()
        ]

    def _detect_doc_type(self, file_path: str) -> DocumentType:
        """检测文档类型"""
        ext = Path(file_path).suffix.lower()

        type_map = {
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.WORD,
            ".doc": DocumentType.WORD,
            ".txt": DocumentType.TEXT,
            ".md": DocumentType.MARKDOWN,
        }

        if ext.startswith("."):
            return type_map.get(ext, DocumentType.TEXT)

        # URL检测
        if "://" in file_path:
            return DocumentType.WEB

        return DocumentType.TEXT

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "supported_formats": [".pdf", ".docx", ".txt", ".md", ".html", ".url"],
            "features": [
                "indexing",
                "query",
                "update",
                "delete",
                "batch_indexing"
            ],
            "vectorstores": ["chroma", "milvus"]
        }


# 全局实例
rag_agent = RAGAgent()
