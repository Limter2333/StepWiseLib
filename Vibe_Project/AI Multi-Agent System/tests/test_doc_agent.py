"""
Doc Agent Tests
"""

import pytest
from pathlib import Path
from agents.doc_agent.doc_agent import (
    DocAgent,
    DocType
)


class TestDocAgentCreation:
    """测试DocAgent创建"""

    def test_agent_creation(self):
        agent = DocAgent()
        assert agent.name == "Doc Agent"
        assert isinstance(agent.output_dir, Path)

    def test_output_dir_created(self):
        agent = DocAgent()
        assert agent.output_dir.exists()


class TestDocType:
    """测试文档类型枚举"""

    def test_doc_type_values(self):
        assert DocType.README.value == "readme"
        assert DocType.API_DOC.value == "api_doc"
        assert DocType.TECHNICAL_DESIGN.value == "technical_design"
        assert DocType.USER_GUIDE.value == "user_guide"
        assert DocType.CHANGELOG.value == "changelog"
        assert DocType.ARCHITECTURE.value == "architecture"

    def test_doc_type_count(self):
        assert len(DocType) == 6


class TestGenerateReadme:
    """测试README生成"""

    @pytest.mark.asyncio
    async def test_generate_readme_basic(self):
        agent = DocAgent()

        content = await agent.generate_readme(
            project_name="My Project",
            description="A test project",
            features=["Feature 1", "Feature 2"]
        )

        assert "# My Project" in content
        assert "A test project" in content
        assert "- Feature 1" in content
        assert "- Feature 2" in content

    @pytest.mark.asyncio
    async def test_generate_readme_with_tech_stack(self):
        agent = DocAgent()

        content = await agent.generate_readme(
            project_name="API Project",
            description="REST API",
            features=["Fast", "Reliable"],
            tech_stack=["Python", "FastAPI"]
        )

        assert "## Tech Stack" in content
        assert "- Python" in content
        assert "- FastAPI" in content

    @pytest.mark.asyncio
    async def test_generate_readme_with_installation(self):
        agent = DocAgent()

        content = await agent.generate_readme(
            project_name="Install Project",
            description="With installation",
            features=["Easy install"],
            installation="pip install package"
        )

        assert "## Installation" in content
        assert "pip install package" in content

    @pytest.mark.asyncio
    async def test_generate_readme_with_usage(self):
        agent = DocAgent()

        content = await agent.generate_readme(
            project_name="Usage Project",
            description="With usage",
            features=["Feature"],
            usage="python main.py"
        )

        assert "## Usage" in content
        assert "python main.py" in content

    @pytest.mark.asyncio
    async def test_generate_readme_license(self):
        agent = DocAgent()

        content = await agent.generate_readme(
            project_name="Test Project",
            description="Test",
            features=[]
        )

        assert "## License" in content
        assert "MIT" in content


class TestGenerateAPIDoc:
    """测试API文档生成"""

    @pytest.mark.asyncio
    async def test_generate_api_doc_basic(self):
        agent = DocAgent()

        endpoints = [
            {"method": "GET", "path": "/users", "description": "Get users"}
        ]

        content = await agent.generate_api_doc(endpoints=endpoints)

        assert "# API Documentation" in content
        assert "### GET /users" in content
        assert "Get users" in content

    @pytest.mark.asyncio
    async def test_generate_api_doc_with_parameters(self):
        agent = DocAgent()

        endpoints = [
            {
                "method": "GET",
                "path": "/users/{id}",
                "description": "Get user by ID",
                "parameters": [
                    {"name": "id", "type": "integer", "description": "User ID"}
                ]
            }
        ]

        content = await agent.generate_api_doc(endpoints=endpoints)

        assert "id" in content
        assert "integer" in content

    @pytest.mark.asyncio
    async def test_generate_api_doc_with_request_body(self):
        agent = DocAgent()

        endpoints = [
            {
                "method": "POST",
                "path": "/users",
                "description": "Create user",
                "request_body": '{"name": "string"}'
            }
        ]

        content = await agent.generate_api_doc(endpoints=endpoints)

        assert "POST" in content
        assert '{"name": "string"}' in content

    @pytest.mark.asyncio
    async def test_generate_api_doc_with_responses(self):
        agent = DocAgent()

        endpoints = [
            {
                "method": "GET",
                "path": "/status",
                "description": "Check status",
                "responses": {"200": "OK", "500": "Server Error"}
            }
        ]

        content = await agent.generate_api_doc(endpoints=endpoints)

        assert "200" in content
        assert "OK" in content

    @pytest.mark.asyncio
    async def test_generate_api_doc_custom_title(self):
        agent = DocAgent()

        content = await agent.generate_api_doc(
            endpoints=[],
            title="Custom API Title"
        )

        assert "Custom API Title" in content


class TestGenerateTechnicalDesign:
    """测试技术方案文档生成"""

    @pytest.mark.asyncio
    async def test_generate_technical_design_basic(self):
        agent = DocAgent()

        content = await agent.generate_technical_design(
            project_name="TestSystem",
            overview="A test system",
            architecture="Microservices",
            components=[]
        )

        assert "# Technical Design - TestSystem" in content
        assert "## Overview" in content
        assert "A test system" in content
        assert "## Architecture" in content

    @pytest.mark.asyncio
    async def test_generate_technical_design_with_components(self):
        agent = DocAgent()

        components = [
            {
                "name": "AuthService",
                "description": "Authentication service",
                "responsibilities": ["Login", "Logout"]
            }
        ]

        content = await agent.generate_technical_design(
            project_name="System",
            overview="Overview",
            architecture="Arch",
            components=components
        )

        assert "### AuthService" in content
        assert "Authentication service" in content
        assert "- Login" in content
        assert "- Logout" in content

    @pytest.mark.asyncio
    async def test_generate_technical_design_with_dependencies(self):
        agent = DocAgent()

        components = [
            {
                "name": "API",
                "description": "API Layer",
                "responsibilities": ["Handle requests"],
                "dependencies": ["Database", "Cache"]
            }
        ]

        content = await agent.generate_technical_design(
            project_name="System",
            overview="Overview",
            architecture="Arch",
            components=components
        )

        assert "Dependencies:" in content
        assert "Database" in content
        assert "Cache" in content

    @pytest.mark.asyncio
    async def test_generate_technical_design_with_data_flow(self):
        agent = DocAgent()

        content = await agent.generate_technical_design(
            project_name="System",
            overview="Overview",
            architecture="Arch",
            components=[],
            data_flow="Request -> Process -> Response"
        )

        assert "## Data Flow" in content
        assert "Request -> Process -> Response" in content

    @pytest.mark.asyncio
    async def test_generate_technical_design_with_security(self):
        agent = DocAgent()

        content = await agent.generate_technical_design(
            project_name="System",
            overview="Overview",
            architecture="Arch",
            components=[],
            security="JWT Authentication"
        )

        assert "## Security" in content
        assert "JWT Authentication" in content


class TestGenerateUserGuide:
    """测试用户手册生成"""

    @pytest.mark.asyncio
    async def test_generate_user_guide_basic(self):
        agent = DocAgent()

        content = await agent.generate_user_guide(
            product_name="MyApp",
            getting_started="Install and run",
            tutorials=[]
        )

        assert "# MyApp - User Guide" in content
        assert "## Getting Started" in content
        assert "Install and run" in content

    @pytest.mark.asyncio
    async def test_generate_user_guide_with_tutorials(self):
        agent = DocAgent()

        tutorials = [
            {
                "title": "First Steps",
                "description": "Learn the basics",
                "commands": "python start.py"
            }
        ]

        content = await agent.generate_user_guide(
            product_name="MyApp",
            getting_started="Start here",
            tutorials=tutorials
        )

        assert "### 1. First Steps" in content
        assert "Learn the basics" in content
        assert "python start.py" in content

    @pytest.mark.asyncio
    async def test_generate_user_guide_with_faq(self):
        agent = DocAgent()

        faq = [
            {"question": "How to install?", "answer": "Use pip"}
        ]

        content = await agent.generate_user_guide(
            product_name="MyApp",
            getting_started="Start",
            tutorials=[],
            faq=faq
        )

        assert "## FAQ" in content
        assert "How to install?" in content
        assert "Use pip" in content

    @pytest.mark.asyncio
    async def test_generate_user_guide_multiple_tutorials(self):
        agent = DocAgent()

        tutorials = [
            {"title": "Step 1", "description": "First", "commands": "cmd1"},
            {"title": "Step 2", "description": "Second", "commands": "cmd2"}
        ]

        content = await agent.generate_user_guide(
            product_name="App",
            getting_started="Go",
            tutorials=tutorials
        )

        assert "### 1. Step 1" in content
        assert "### 2. Step 2" in content


class TestSaveDocument:
    """测试文档保存"""

    @pytest.mark.asyncio
    async def test_save_document(self):
        agent = DocAgent()

        content = "# Test Document\nTest content"
        path = await agent.save_document(
            content=content,
            filename="test_doc.md"
        )

        assert isinstance(path, str)
        assert "test_doc.md" in path

        # Verify file was written
        from pathlib import Path
        file_path = Path(path)
        assert file_path.exists()

        # Cleanup
        if file_path.exists():
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_save_document_with_doc_type(self):
        agent = DocAgent()

        content = "# API Doc"
        path = await agent.save_document(
            content=content,
            filename="api.md",
            doc_type=DocType.API_DOC
        )

        assert isinstance(path, str)
        from pathlib import Path
        if Path(path).exists():
            Path(path).unlink()


class TestUpdateChangelog:
    """测试变更日志更新"""

    @pytest.mark.asyncio
    async def test_update_changelog_new(self):
        agent = DocAgent()

        path = await agent.update_changelog(
            version="1.0.0",
            changes=["Added feature X", "Fixed bug Y"]
        )

        assert isinstance(path, str)
        assert "CHANGELOG.md" in path

        # Verify content
        from pathlib import Path
        if Path(path).exists():
            content = Path(path).read_text(encoding='utf-8')
            assert "1.0.0" in content
            assert "Added feature X" in content
            # Cleanup
            Path(path).unlink()

    @pytest.mark.asyncio
    async def test_update_changelog_with_date(self):
        agent = DocAgent()

        path = await agent.update_changelog(
            version="2.0.0",
            changes=["Major release"],
            date="2024-01-15"
        )

        assert isinstance(path, str)
        from pathlib import Path
        if Path(path).exists():
            content = Path(path).read_text(encoding='utf-8')
            assert "2.0.0" in content
            assert "2024-01-15" in content
            Path(path).unlink()


class TestCapabilities:
    """测试能力获取"""

    def test_get_capabilities(self):
        agent = DocAgent()

        caps = agent.get_capabilities()

        assert caps["name"] == "Doc Agent"
        assert "readme" in caps["document_types"]
        assert "api_doc" in caps["document_types"]
        assert "markdown" in caps["output_formats"]
        assert "en" in caps["languages"]
        assert "zh" in caps["languages"]

    def test_all_doc_types_in_capabilities(self):
        agent = DocAgent()
        caps = agent.get_capabilities()

        for dt in DocType:
            assert dt.value in caps["document_types"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
