"""提示词模块单元测试。"""
import pytest
from harness.prompt import (
    PromptTemplate, PromptProvider, ReActPromptProvider,
    SimplePromptProvider, CustomPromptProvider, get_prompt_provider
)


class TestPromptTemplate:
    """PromptTemplate 测试。"""
    
    def test_basic_render(self):
        """测试基本模板渲染。"""
        template = PromptTemplate(template="Hello ${name}, welcome to {place}!")
        result = template.render(name="Alice", place="Wonderland")
        assert result == "Hello Alice, welcome to Wonderland!"
    
    def test_with_default_variables(self):
        """测试带默认变量的模板。"""
        template = PromptTemplate(
            template="${greeting} ${name}!",
            variables={"greeting": "Hi"}
        )
        result = template.render(name="Bob")
        assert result == "Hi Bob!"
    
    def test_override_default_variables(self):
        """测试覆盖默认变量。"""
        template = PromptTemplate(
            template="${greeting} ${name}!",
            variables={"greeting": "Hi"}
        )
        result = template.render(greeting="Hello", name="Bob")
        assert result == "Hello Bob!"


class TestReActPromptProvider:
    """ReActPromptProvider 测试。"""
    
    def test_get_system_prompt(self):
        """测试获取系统提示词。"""
        provider = ReActPromptProvider()
        prompt = provider.get_system_prompt(tool_list="- read_file: 读取文件")
        assert "read_file" in prompt
        assert "<thought>" in prompt
        assert "<action>" in prompt
        assert "<final_answer>" in prompt
    
    def test_get_format_instructions(self):
        """测试获取格式说明。"""
        provider = ReActPromptProvider()
        instructions = provider.get_format_instructions()
        assert "<thought>" in instructions
        assert "<action>" in instructions
    
    def test_get_examples(self):
        """测试获取示例。"""
        provider = ReActPromptProvider()
        examples = provider.get_examples()
        assert "埃菲尔铁塔" in examples
    
    def test_get_environment_info(self):
        """测试获取环境信息。"""
        provider = ReActPromptProvider()
        env_info = provider.get_environment_info()
        assert "operating_system" in env_info
        assert env_info["operating_system"] in ["macOS", "Windows", "Linux", "Unknown"]


class TestSimplePromptProvider:
    """SimplePromptProvider 测试。"""
    
    def test_get_system_prompt(self):
        """测试获取系统提示词。"""
        provider = SimplePromptProvider()
        prompt = provider.get_system_prompt(tool_list="- tool1: 描述")
        assert "tool1" in prompt
    
    def test_get_format_instructions(self):
        """测试获取格式说明。"""
        provider = SimplePromptProvider()
        instructions = provider.get_format_instructions()
        assert isinstance(instructions, str)


class TestCustomPromptProvider:
    """CustomPromptProvider 测试。"""
    
    def test_get_system_prompt(self):
        """测试获取自定义系统提示词。"""
        provider = CustomPromptProvider(
            system_prompt="自定义提示词",
            format_instructions="格式说明",
            examples="示例"
        )
        prompt = provider.get_system_prompt()
        assert prompt == "自定义提示词"
    
    def test_get_format_instructions(self):
        """测试获取格式说明。"""
        provider = CustomPromptProvider(
            system_prompt="提示词",
            format_instructions="格式说明"
        )
        instructions = provider.get_format_instructions()
        assert instructions == "格式说明"
    
    def test_get_examples(self):
        """测试获取示例。"""
        provider = CustomPromptProvider(
            system_prompt="提示词",
            examples="示例"
        )
        examples = provider.get_examples()
        assert examples == "示例"


class TestGetPromptProvider:
    """get_prompt_provider 工厂函数测试。"""
    
    def test_get_react_provider(self):
        """测试获取 ReAct 提供者。"""
        provider = get_prompt_provider("react")
        assert isinstance(provider, ReActPromptProvider)
    
    def test_get_simple_provider(self):
        """测试获取 Simple 提供者。"""
        provider = get_prompt_provider("simple")
        assert isinstance(provider, SimplePromptProvider)
    
    def test_get_custom_provider(self):
        """测试获取 Custom 提供者。"""
        provider = get_prompt_provider(
            "custom",
            system_prompt="自定义",
            format_instructions="格式"
        )
        assert isinstance(provider, CustomPromptProvider)
    
    def test_unknown_provider_raises(self):
        """测试未知提供者类型抛出异常。"""
        with pytest.raises(ValueError, match="未知的提示词提供者类型"):
            get_prompt_provider("unknown")
