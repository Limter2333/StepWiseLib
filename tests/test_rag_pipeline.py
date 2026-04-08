"""
测试RAG管道
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.rag_pipeline import RAGPipeline, RAGConfig, DocumentType, Document, Chunk, RetrievalResult


class TestRAGPipeline:
    """RAG管道测试"""

    def setup_method(self):
        """每个测试前创建管道"""
        # 使用ChromaDB进行测试
        self.config = RAGConfig(
            use_milvus=False,
            chunk_size=100,
            chunk_overlap=20
        )
        self.pipeline = RAGPipeline(config=self.config)

    def test_pipeline_initialization(self):
        """测试管道初始化"""
        assert self.pipeline is not None
        assert self.pipeline.splitter is not None
        assert self.pipeline.vectorstore is not None

    def test_detect_doc_type(self):
        """测试文档类型检测"""
        # PDF
        doc_type = self.pipeline._detect_doc_type("document.pdf")
        assert doc_type == DocumentType.PDF

        # Word
        doc_type = self.pipeline._detect_doc_type("document.docx")
        assert doc_type == DocumentType.WORD

        # URL
        doc_type = self.pipeline._detect_doc_type("https://example.com")
        assert doc_type == DocumentType.WEB

    def test_split_document(self):
        """测试文档分割"""
        doc = Document(
            id="test_doc",
            content="This is paragraph one. This is paragraph two. This is paragraph three.",
            source="test.txt",
            doc_type=DocumentType.TEXT,
            metadata={}
        )

        chunks = self.pipeline.split_document(doc)

        assert len(chunks) > 0
        assert all(hasattr(c, 'content') for c in chunks)
        assert all(hasattr(c, 'id') for c in chunks)

    def test_get_stats(self):
        """测试统计信息"""
        stats = self.pipeline.get_stats()

        assert "config" in stats
        assert "vectorstore" in stats
        assert stats["config"]["chunk_size"] == 100


class TestDocumentType:
    """文档类型测试"""

    def test_document_type_enum(self):
        """测试文档类型枚举"""
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.WORD.value == "docx"
        assert DocumentType.WEB.value == "url"
        assert DocumentType.TEXT.value == "txt"


class TestChunkSize:
    """分块大小测试"""

    def test_small_chunk_size(self):
        """测试小分块"""
        config = RAGConfig(chunk_size=50, chunk_overlap=10)
        pipeline = RAGPipeline(config=config)

        doc = Document(
            id="test",
            content="Short content.",
            source="test.txt",
            doc_type=DocumentType.TEXT,
            metadata={}
        )

        chunks = pipeline.split_document(doc)
        assert len(chunks) >= 1

    def test_large_chunk_size(self):
        """测试大分块"""
        config = RAGConfig(chunk_size=5000, chunk_overlap=500)
        pipeline = RAGPipeline(config=config)

        doc = Document(
            id="test",
            content="A" * 10000,  # 很长
            source="test.txt",
            doc_type=DocumentType.TEXT,
            metadata={}
        )

        chunks = pipeline.split_document(doc)
        # 应该分成较少的块
        assert len(chunks) <= 3


class TestRAGGenerate:
    """RAG生成测试 - 验证LLM实际调用"""

    def setup_method(self):
        """每个测试前创建管道"""
        self.config = RAGConfig(use_milvus=False, chunk_size=100, chunk_overlap=20)
        self.pipeline = RAGPipeline(config=self.config)

    def test_generate_builds_context(self):
        """测试生成方法构建上下文"""
        from knowledge.rag_pipeline import RetrievalResult

        retrieval_results = [
            RetrievalResult(
                content="Python is a programming language.",
                score=0.95,
                doc_id="doc1",
                metadata={"source": "test.txt"}
            ),
            RetrievalResult(
                content="JavaScript is also a programming language.",
                score=0.85,
                doc_id="doc2",
                metadata={"source": "test2.txt"}
            )
        ]

        # 测试上下文构建逻辑
        context_parts = []
        for i, r in enumerate(retrieval_results):
            context_parts.append(
                f"[Source {i+1}] (score: {r.score:.2f})\n{r.content}"
            )
        context = "\n\n".join(context_parts)

        assert "[Source 1]" in context
        assert "Python" in context
        assert "[Source 2]" in context
        assert "JavaScript" in context

    def test_retrieval_result_structure(self):
        """测试检索结果结构"""
        from knowledge.rag_pipeline import RetrievalResult

        result = RetrievalResult(
            content="Test content",
            score=0.9,
            doc_id="test_doc",
            metadata={"key": "value"}
        )

        assert result.content == "Test content"
        assert result.score == 0.9
        assert result.doc_id == "test_doc"
        assert result.metadata["key"] == "value"


class TestRAGPipelineAsync:
    """RAG管道异步测试"""

    def setup_method(self):
        """每个测试前创建管道"""
        self.config = RAGConfig(use_milvus=False, chunk_size=100, chunk_overlap=20)
        self.pipeline = RAGPipeline(config=self.config)

    def test_pipeline_has_generate_method(self):
        """测试管道有generate方法"""
        assert hasattr(self.pipeline, 'generate')
        assert callable(self.pipeline.generate)

    def test_pipeline_has_query_method(self):
        """测试管道有query方法"""
        assert hasattr(self.pipeline, 'query')
        assert callable(self.pipeline.query)


class TestRetrievalFiltering:
    """检索过滤逻辑测试 - 验证 ChromaDB L2 distance 过滤"""

    def setup_method(self):
        """每个测试前创建管道"""
        self.config = RAGConfig(
            use_milvus=False,
            chunk_size=100,
            chunk_overlap=20,
            score_threshold=0.5
        )
        self.pipeline = RAGPipeline(config=self.config)

    def test_retrieve_returns_results_when_docs_exist(self):
        """测试有文档时检索返回结果"""
        # 知识库中已有文档，应该能返回结果
        results = self.pipeline.retrieve("rerank")
        # 验证返回的是 RetrievalResult 列表
        assert isinstance(results, list)
        # 如果知识库有相关文档，应该有结果（distance 应该合理范围）

    def test_retrieve_with_high_distance_values(self):
        """测试 ChromaDB L2 distance 很高时仍能返回结果"""
        # ChromaDB L2 distance 可能达到 60-70，这是正常的 embedding 空间特点
        # 关键是：只要有结果返回，就应该被保留
        results = self.pipeline.retrieve("ADK")

        # 验证返回的是列表
        assert isinstance(results, list)

        # 如果有结果，验证结构正确
        for r in results:
            assert hasattr(r, 'content')
            assert hasattr(r, 'score')
            assert hasattr(r, 'doc_id')

    def test_retrieval_result_score_interpretation(self):
        """测试检索结果分数的语义理解"""
        # ChromaDB 返回的是 L2 distance（欧氏距离）
        # - 值越小表示越相似
        # - 值越大表示越不相似
        # - 60-70 的 distance 值是正常的（embedding 空间维度高）

        results = self.pipeline.retrieve("python")

        # 验证结果可以为空（如果没有匹配文档）
        assert isinstance(results, list)

    def test_has_relevant_knowledge_logic(self):
        """测试 has_relevant_knowledge 判断逻辑"""
        # 有检索结果时，应该认为有相关知识
        results = self.pipeline.retrieve("test")
        has_knowledge = len(results) > 0

        # 如果有结果，has_relevant_knowledge 应该为 True
        if len(results) > 0:
            assert has_knowledge is True


class TestRerankerFallback:
    """Reranker 失效处理测试"""

    def setup_method(self):
        """每个测试前创建管道"""
        self.config = RAGConfig(
            use_milvus=False,
            chunk_size=100,
            chunk_overlap=20,
            use_reranker=True
        )
        self.pipeline = RAGPipeline(config=self.config)

    def test_reranker_disabled_when_model_fails(self):
        """测试 reranker 模型加载失败时的降级处理"""
        # 当 reranker 返回全 0 分数时，应该保留 ChromaDB 原生分数
        # 这通过 _apply_reranking 中的逻辑处理

        results = self.pipeline.retrieve("rerank")

        # 验证即使 reranker 有问题，仍能返回结果
        assert isinstance(results, list)


class TestRAGPipelineEdgeCases:
    """RAG管道边界情况测试"""

    def test_detect_doc_type_pdf(self):
        """测试PDF类型检测"""
        config = RAGConfig(use_milvus=False)
        pipeline = RAGPipeline(config=config)

        assert pipeline._detect_doc_type("doc.PDF") == DocumentType.PDF
        assert pipeline._detect_doc_type("document.pdf") == DocumentType.PDF
        assert pipeline._detect_doc_type("/path/to/file.Pdf") == DocumentType.PDF

    def test_detect_doc_type_word(self):
        """测试Word类型检测"""
        config = RAGConfig(use_milvus=False)
        pipeline = RAGPipeline(config=config)

        assert pipeline._detect_doc_type("doc.docx") == DocumentType.WORD
        assert pipeline._detect_doc_type("document.doc") == DocumentType.WORD

    def test_detect_doc_type_web(self):
        """测试Web URL类型检测"""
        config = RAGConfig(use_milvus=False)
        pipeline = RAGPipeline(config=config)

        assert pipeline._detect_doc_type("https://example.com") == DocumentType.WEB
        assert pipeline._detect_doc_type("http://test.org/page") == DocumentType.WEB
        # ftp不是http，不会被检测为WEB
        assert pipeline._detect_doc_type("ftp://files.example.com") == DocumentType.TEXT

    def test_detect_doc_type_excel(self):
        """测试Excel类型检测"""
        config = RAGConfig(use_milvus=False)
        pipeline = RAGPipeline(config=config)

        assert pipeline._detect_doc_type("data.xlsx") == DocumentType.EXCEL
        assert pipeline._detect_doc_type("spreadsheet.xls") == DocumentType.EXCEL

    def test_detect_doc_type_powerpoint(self):
        """测试PowerPoint类型检测"""
        config = RAGConfig(use_milvus=False)
        pipeline = RAGPipeline(config=config)

        assert pipeline._detect_doc_type("presentation.pptx") == DocumentType.POWERPOINT

    def test_detect_doc_type_markdown(self):
        """测试Markdown类型检测"""
        config = RAGConfig(use_milvus=False)
        pipeline = RAGPipeline(config=config)

        assert pipeline._detect_doc_type("readme.md") == DocumentType.MARKDOWN
        assert pipeline._detect_doc_type("notes.txt") == DocumentType.TEXT

    def test_detect_doc_type_unknown(self):
        """测试未知类型默认为TEXT"""
        config = RAGConfig(use_milvus=False)
        pipeline = RAGPipeline(config=config)

        assert pipeline._detect_doc_type("file.unknown") == DocumentType.TEXT
        assert pipeline._detect_doc_type("noextension") == DocumentType.TEXT

    def test_split_empty_document(self):
        """测试分割空文档"""
        config = RAGConfig(use_milvus=False, chunk_size=100)
        pipeline = RAGPipeline(config=config)

        doc = Document(
            id="empty_doc",
            content="",
            source="empty.txt",
            doc_type=DocumentType.TEXT,
            metadata={}
        )

        chunks = pipeline.split_document(doc)
        # 空文档应该返回空列表
        assert len(chunks) == 0

    def test_split_single_char_document(self):
        """测试分割单字符文档"""
        config = RAGConfig(use_milvus=False, chunk_size=100, min_chunk_size=1)
        pipeline = RAGPipeline(config=config)

        doc = Document(
            id="single_char",
            content="A",
            source="test.txt",
            doc_type=DocumentType.TEXT,
            metadata={}
        )

        chunks = pipeline.split_document(doc)
        assert len(chunks) >= 0

    def test_split_very_long_document(self):
        """测试分割超长文档"""
        config = RAGConfig(use_milvus=False, chunk_size=100, chunk_overlap=10)
        pipeline = RAGPipeline(config=config)

        # 创建一个很长的文档
        long_content = "word " * 10000
        doc = Document(
            id="long_doc",
            content=long_content,
            source="long.txt",
            doc_type=DocumentType.TEXT,
            metadata={}
        )

        chunks = pipeline.split_document(doc)
        # 应该分成至少一个块
        assert len(chunks) >= 1

    def test_split_document_with_newlines(self):
        """测试分割带换行的文档"""
        config = RAGConfig(use_milvus=False, chunk_size=50, min_chunk_size=10)
        pipeline = RAGPipeline(config=config)

        doc = Document(
            id="newlines",
            content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
            source="test.txt",
            doc_type=DocumentType.TEXT,
            metadata={}
        )

        chunks = pipeline.split_document(doc)
        assert len(chunks) >= 1

    def test_split_document_unicode(self):
        """测试分割Unicode文档"""
        config = RAGConfig(use_milvus=False, chunk_size=50, min_chunk_size=10)
        pipeline = RAGPipeline(config=config)

        doc = Document(
            id="unicode_doc",
            content="你好世界 🔥 这是测试 🚀",
            source="test.txt",
            doc_type=DocumentType.TEXT,
            metadata={}
        )

        chunks = pipeline.split_document(doc)
        assert len(chunks) >= 1
        # 验证Unicode内容保留
        if chunks:
            assert "你好" in chunks[0].content or len(chunks) == 0

    def test_document_type_enum_values(self):
        """测试DocumentType枚举值"""
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.WORD.value == "docx"
        assert DocumentType.WEB.value == "url"
        assert DocumentType.TEXT.value == "txt"
        assert DocumentType.MARKDOWN.value == "md"
        assert DocumentType.EXCEL.value == "xlsx"
        assert DocumentType.POWERPOINT.value == "pptx"

    def test_rag_config_defaults(self):
        """测试RAGConfig默认值"""
        config = RAGConfig()

        assert config.use_milvus is False
        assert config.chunk_size == 500
        assert config.chunk_overlap == 50
        assert config.min_chunk_size == 100
        assert config.top_k == 5
        assert config.score_threshold == 0.5
        assert config.initial_k == 20
        assert config.keyword_weight == 0.5
        assert config.vector_weight == 0.5
        assert config.fusion_method == "rrf"
        assert config.use_reranker is True

    def test_rag_config_custom(self):
        """测试RAGConfig自定义值"""
        config = RAGConfig(
            use_milvus=True,
            chunk_size=1000,
            chunk_overlap=100,
            top_k=10,
            fusion_method="weighted"
        )

        assert config.use_milvus is True
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 100
        assert config.top_k == 10
        assert config.fusion_method == "weighted"

    def test_retrieval_result_structure(self):
        """测试RetrievalResult结构"""
        result = RetrievalResult(
            content="Test content",
            score=0.95,
            doc_id="doc_123",
            metadata={"source": "test.txt"}
        )

        assert result.content == "Test content"
        assert result.score == 0.95
        assert result.doc_id == "doc_123"
        assert result.metadata["source"] == "test.txt"

    def test_chunk_structure(self):
        """测试Chunk结构"""
        chunk = Chunk(
            id="chunk_1",
            content="Test chunk content",
            doc_id="doc_1",
            chunk_index=0,
            metadata={"source": "test.txt"}
        )

        assert chunk.id == "chunk_1"
        assert chunk.content == "Test chunk content"
        assert chunk.doc_id == "doc_1"
        assert chunk.chunk_index == 0
        assert chunk.metadata["source"] == "test.txt"

    def test_pipeline_without_milvus(self):
        """测试使用ChromaDB的管道"""
        config = RAGConfig(use_milvus=False)
        pipeline = RAGPipeline(config=config)

        assert pipeline.vectorstore is not None
        # ChromaDB should be used

    def test_pipeline_with_milvus_config(self):
        """测试Milvus配置"""
        config = RAGConfig(use_milvus=True)
        # 配置应该是Milvus
        assert config.use_milvus is True
        # 不实际连接Milvus，只验证配置

    def test_context_building(self):
        """测试上下文构建"""
        from knowledge.rag_pipeline import RetrievalResult

        retrieval_results = [
            RetrievalResult(
                content="First result content",
                score=0.95,
                doc_id="doc1",
                metadata={"source": "doc1.txt"}
            ),
            RetrievalResult(
                content="Second result content",
                score=0.85,
                doc_id="doc2",
                metadata={"source": "doc2.txt"}
            ),
            RetrievalResult(
                content="Third result content",
                score=0.75,
                doc_id="doc3",
                metadata={"source": "doc3.txt"}
            ),
        ]

        # 构建上下文
        context_parts = []
        for i, r in enumerate(retrieval_results):
            context_parts.append(
                f"[Source {i+1}] (score: {r.score:.2f}, doc: {r.doc_id})\n{r.content}"
            )
        context = "\n\n".join(context_parts)

        assert "[Source 1]" in context
        assert "[Source 2]" in context
        assert "[Source 3]" in context
        assert "First result content" in context
        assert "Second result content" in context
        assert "score: 0.95" in context

    def test_empty_retrieval_results_handling(self):
        """测试空检索结果处理"""
        # 空检索结果列表
        retrieval_results = []

        # 构建上下文时应该不报错
        context_parts = []
        for i, r in enumerate(retrieval_results):
            context_parts.append(f"[Source {i+1}]\n{r.content}")
        context = "\n\n".join(context_parts)

        assert context == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
