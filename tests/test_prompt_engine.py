"""
测试Prompt工程模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prompt_engine import (
    PromptTemplate, PromptManager, prompt_manager
)


class TestPromptTemplate:
    """Prompt模板测试"""

    def test_template_creation(self):
        """测试模板创建"""
        template = PromptTemplate(
            name="test_template",
            description="A test template",
            system_prompt="You are a {{role}}",
            user_template="Tell me about {{topic}}"
        )

        assert template.name == "test_template"
        assert "{{role}}" in template.system_prompt

    def test_template_render(self):
        """测试模板渲染"""
        template = PromptTemplate(
            name="test",
            description="A test template",
            system_prompt="You are a {{role}}",
            user_template="Tell me about {{topic}}"
        )

        system, user = template.render(role="assistant", topic="Python")

        assert system == "You are a assistant"
        assert user == "Tell me about Python"

    def test_template_with_context(self):
        """测试带上下文的模板"""
        template = PromptTemplate(
            name="test",
            description="A test template with context",
            system_prompt="Context: {{context}}",
            user_template="Question: {{question}}"
        )

        system, user = template.render(
            context="Python is a programming language",
            question="What is Python?"
        )

        assert "Python is a programming language" in system
        assert "What is Python?" in user

    def test_template_unmatched_variables(self):
        """测试未匹配的变量"""
        template = PromptTemplate(
            name="test",
            description="A test template with unmatched variables",
            system_prompt="Hello {{name}}",
            user_template=""
        )

        # 未提供的变量应该被移除
        system, _ = template.render(name="World", age="30")
        assert system == "Hello World"
        assert "{{age}}" not in system


class TestPromptManager:
    """Prompt管理器测试"""

    def setup_method(self):
        """每个测试前创建新的manager"""
        self.manager = PromptManager()

    def test_get_template(self):
        """测试获取内置模板"""
        template = self.manager.get_template("rag_qa")

        assert template is not None
        assert template.name == "rag_qa"

    def test_get_nonexistent_template(self):
        """测试获取不存在的模板"""
        template = self.manager.get_template("nonexistent")
        assert template is None

    def test_register_template(self):
        """测试注册模板"""
        template = PromptTemplate(
            name="custom_template",
            description="A custom template",
            system_prompt="Custom system",
            user_template="Custom user"
        )

        self.manager.register_template(template)
        retrieved = self.manager.get_template("custom_template")

        assert retrieved is not None
        assert retrieved.description == "A custom template"

    def test_render(self):
        """测试渲染"""
        system, user = self.manager.render(
            "rag_qa",
            question="What is AI?",
            context="AI stands for Artificial Intelligence."
        )

        assert "AI stands" in system or "What is AI?" in user

    def test_add_example(self):
        """测试添加示例"""
        self.manager.add_example(
            "rag_qa",
            input_text="What is 2+2?",
            output_text="2+2 equals 4."
        )

        template = self.manager.get_template("rag_qa")
        assert len(template.examples) > 0

    def test_list_templates(self):
        """测试列出模板"""
        templates = self.manager.list_templates()

        assert len(templates) >= 4  # 至少有内置的4个
        names = [t["name"] for t in templates]
        assert "rag_qa" in names
        assert "agent_task" in names


class TestBuildPromptFunctions:
    """便捷函数测试"""

    def test_build_rag_prompt(self):
        """测试RAG Prompt构建"""
        from core.prompt_engine import build_rag_prompt

        system, user = build_rag_prompt(
            question="What is machine learning?",
            context="ML is a subset of AI."
        )

        assert "machine learning" in user.lower()
        assert "ML is a subset" in user or "context" in user.lower()

    def test_build_agent_prompt(self):
        """测试Agent Prompt构建"""
        from core.prompt_engine import build_agent_prompt

        system, user = build_agent_prompt(
            task="Write a function",
            agent_role="Developer",
            agent_specialty="Python",
            capabilities=["Coding", "Testing"]
        )

        assert "Developer" in system
        assert "Write a function" in user


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
