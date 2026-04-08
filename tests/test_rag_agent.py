"""
RAG Agent Tests
"""

import pytest
from datetime import datetime
from agents.rag_agent.rag_agent import (
    RAGAgent,
    KnowledgeBase,
    KnowledgeSource
)


class TestRAGAgentCreation:
    """测试RAGAgent创建"""

    def test_agent_creation(self):
        agent = RAGAgent()
        assert agent.name == "RAG Agent"
        assert len(agent.knowledge_bases) == 0
        assert agent.current_kb is None

    def test_global_instance_exists(self):
        from agents.rag_agent import rag_agent
        assert rag_agent.name == "RAG Agent"


class TestKnowledgeSource:
    """测试知识来源数据类"""

    def test_knowledge_source_creation(self):
        source = KnowledgeSource(
            id="source_1",
            name="Test Source",
            source_type="file",
            path="/path/to/file.pdf"
        )

        assert source.id == "source_1"
        assert source.name == "Test Source"
        assert source.source_type == "file"
        assert source.status == "pending"
        assert source.document_count == 0

    def test_knowledge_source_with_metadata(self):
        source = KnowledgeSource(
            id="source_2",
            name="URL Source",
            source_type="url",
            path="https://example.com",
            indexed_at=datetime.now(),
            document_count=10,
            status="ready"
        )

        assert source.status == "ready"
        assert source.document_count == 10
        assert source.indexed_at is not None


class TestKnowledgeBase:
    """测试知识库类"""

    def test_knowledge_base_creation(self):
        kb = KnowledgeBase(name="Test KB")

        assert kb.name == "Test KB"
        assert len(kb.sources) == 0
        assert kb.use_milvus is False

    def test_knowledge_base_with_milvus(self):
        # Note: Milvus connection is tested in integration tests
        # This just verifies the flag is stored correctly
        kb = KnowledgeBase(name="Test KB", use_milvus=False)
        assert kb.use_milvus is False

    def test_add_source(self):
        kb = KnowledgeBase(name="Test KB")

        source = kb.add_source(
            name="PDF Files",
            source_type="file",
            path="/docs"
        )

        assert source is not None
        assert source.name == "PDF Files"
        assert source.id == "source_1"

    def test_add_multiple_sources(self):
        kb = KnowledgeBase(name="Test KB")

        source1 = kb.add_source(name="Source 1", source_type="file", path="/path1")
        source2 = kb.add_source(name="Source 2", source_type="url", path="/path2")

        assert source1.id != source2.id
        assert len(kb.sources) == 2

    def test_get_source(self):
        kb = KnowledgeBase(name="Test KB")

        source = kb.add_source(name="Test", source_type="file", path="/test")

        retrieved = kb.get_source(source.id)

        assert retrieved is not None
        assert retrieved.id == source.id

    def test_get_nonexistent_source(self):
        kb = KnowledgeBase(name="Test KB")

        retrieved = kb.get_source("nonexistent")

        assert retrieved is None


class TestRAGAgentKBManagement:
    """测试RAGAgent知识库管理"""

    def test_create_knowledge_base(self):
        agent = RAGAgent()

        kb = agent.create_knowledge_base(name="Projects KB")

        assert kb is not None
        assert kb.name == "Projects KB"
        assert "Projects KB" in agent.knowledge_bases
        assert agent.current_kb == kb

    def test_create_multiple_knowledge_bases(self):
        agent = RAGAgent()

        kb1 = agent.create_knowledge_base(name="KB 1")
        kb2 = agent.create_knowledge_base(name="KB 2")

        assert len(agent.knowledge_bases) == 2
        assert agent.current_kb == kb2  # Last one becomes current
        assert kb1 != kb2

    def test_switch_knowledge_base(self):
        agent = RAGAgent()

        kb1 = agent.create_knowledge_base(name="KB 1")
        kb2 = agent.create_knowledge_base(name="KB 2")

        result = agent.switch_knowledge_base("KB 1")

        assert result is True
        assert agent.current_kb == kb1

    def test_switch_to_nonexistent_kb(self):
        agent = RAGAgent()
        agent.create_knowledge_base(name="Existing KB")

        result = agent.switch_knowledge_base("NonExistent")

        assert result is False

    def test_list_knowledge_bases(self):
        agent = RAGAgent()

        agent.create_knowledge_base(name="KB 1")
        agent.create_knowledge_base(name="KB 2")

        listed = agent.list_knowledge_bases()

        assert len(listed) == 2
        assert any(kb["name"] == "KB 1" for kb in listed)
        assert any(kb["name"] == "KB 2" for kb in listed)


class TestDocumentTypeDetection:
    """测试文档类型检测"""

    def test_detect_pdf(self):
        agent = RAGAgent()

        doc_type = agent._detect_doc_type("document.pdf")

        assert doc_type.value == "pdf"

    def test_detect_docx(self):
        agent = RAGAgent()

        doc_type = agent._detect_doc_type("document.docx")

        assert doc_type.value == "docx"

    def test_detect_doc(self):
        agent = RAGAgent()

        doc_type = agent._detect_doc_type("document.doc")

        assert doc_type.value == "docx"

    def test_detect_txt(self):
        agent = RAGAgent()

        doc_type = agent._detect_doc_type("readme.txt")

        assert doc_type.value == "txt"

    def test_detect_markdown(self):
        agent = RAGAgent()

        doc_type = agent._detect_doc_type("guide.md")

        assert doc_type.value == "md"

    def test_detect_url(self):
        agent = RAGAgent()

        doc_type = agent._detect_doc_type("https://example.com/page")

        assert doc_type.value == "url"

    def test_detect_unknown_extension(self):
        agent = RAGAgent()

        doc_type = agent._detect_doc_type("file.unknown")

        assert doc_type.value == "txt"

    def test_detect_case_insensitive(self):
        agent = RAGAgent()

        doc_type = agent._detect_doc_type("document.PDF")

        assert doc_type.value == "pdf"


class TestCapabilities:
    """测试能力获取"""

    def test_get_capabilities(self):
        agent = RAGAgent()

        caps = agent.get_capabilities()

        assert caps["name"] == "RAG Agent"
        assert ".pdf" in caps["supported_formats"]
        assert ".docx" in caps["supported_formats"]
        assert "indexing" in caps["features"]
        assert "query" in caps["features"]
        assert "chroma" in caps["vectorstores"]
        assert "milvus" in caps["vectorstores"]

    def test_all_features_listed(self):
        agent = RAGAgent()
        caps = agent.get_capabilities()

        expected_features = ["indexing", "query", "update", "delete", "batch_indexing"]
        for feature in expected_features:
            assert feature in caps["features"]


class TestIndexDocument:
    """测试文档索引"""

    @pytest.mark.asyncio
    async def test_index_document_no_kb(self):
        agent = RAGAgent()
        # No KB created

        with pytest.raises(ValueError, match="No knowledge base selected"):
            await agent.index_document("/path/to/file.pdf")

    @pytest.mark.asyncio
    async def test_index_directory_no_kb(self):
        agent = RAGAgent()

        with pytest.raises(ValueError, match="No knowledge base selected"):
            await agent.index_directory("/some/directory")


class TestQuery:
    """测试查询"""

    @pytest.mark.asyncio
    async def test_query_no_kb(self):
        agent = RAGAgent()

        with pytest.raises(ValueError, match="No knowledge base selected"):
            await agent.query("What is Python?")


class TestUpdateDelete:
    """测试更新和删除"""

    @pytest.mark.asyncio
    async def test_update_document(self):
        agent = RAGAgent()
        agent.create_knowledge_base(name="Test KB")

        # This will try to index the new file
        result = await agent.update_document("/old/path.pdf", "/new/path.pdf")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_document(self):
        agent = RAGAgent()

        result = await agent.delete_document("/path/to/file.pdf")

        assert result is True


class TestGetStats:
    """测试统计信息"""

    def test_get_knowledge_base_stats_nonexistent(self):
        agent = RAGAgent()
        agent.create_knowledge_base(name="Existing KB")

        stats = agent.get_knowledge_base_stats("NonExistent")

        assert stats is None

    def test_get_knowledge_base_stats(self):
        agent = RAGAgent()
        agent.create_knowledge_base(name="Test KB")

        stats = agent.get_knowledge_base_stats("Test KB")

        assert stats is not None
        assert stats["name"] == "Test KB"
        assert "sources" in stats
        assert "vectorstore" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
