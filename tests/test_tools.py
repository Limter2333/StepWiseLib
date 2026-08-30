"""工具层单元测试。"""
import os
import tempfile
import pytest
from harness.tools.base import ToolSpec, ToolArgumentError, tool
from harness.tools.registry import ToolRegistry
from harness.tools.builtin import read_file, write_to_file, run_terminal_command


class TestToolSpec:
    """ToolSpec 测试。"""
    
    def test_tool_decorator(self):
        """测试 @tool 装饰器。"""
        @tool(description="测试工具")
        def test_func(x: str, y: int = 10) -> str:
            """测试函数"""
            return f"{x}-{y}"
        
        assert isinstance(test_func, ToolSpec)
        assert test_func.name == "test_func"
        assert test_func.description == "测试工具"
        assert test_func.parameters.get("x", {}).get("type") == "string"
    
    def test_tool_validate_args(self):
        """测试参数校验。"""
        @tool()
        def add(a: int, b: int) -> int:
            return a + b
        
        # 正常情况
        result = add.validate_args(1, 2)
        assert result == {"a": 1, "b": 2}
        
        # 缺少参数
        with pytest.raises(ToolArgumentError):
            add.validate_args(1)
    
    def test_tool_invoke(self):
        """测试工具调用。"""
        @tool()
        def multiply(x: int, y: int) -> int:
            return x * y
        
        result = multiply.invoke(3, 4)
        assert result == "12"
    
    def test_tool_invoke_error(self):
        """测试工具调用错误处理。"""
        @tool()
        def failing_tool() -> str:
            raise ValueError("测试错误")
        
        result = failing_tool.invoke()
        assert "工具执行错误" in result


class TestToolRegistry:
    """ToolRegistry 测试。"""
    
    def test_register_tool(self):
        """测试工具注册。"""
        registry = ToolRegistry()
        
        @tool()
        def test_tool() -> str:
            return "ok"
        
        registry.register(test_tool)
        assert registry.has("test_tool")
        assert registry.get("test_tool") is test_tool
    
    def test_invoke_tool(self):
        """测试工具调用。"""
        registry = ToolRegistry()
        
        @tool()
        def add(a: int, b: int) -> int:
            return a + b
        
        registry.register(add)
        result = registry.invoke("add", (3, 4))
        assert result == "7"
    
    def test_invoke_unknown_tool(self):
        """测试调用未知工具。"""
        registry = ToolRegistry()
        result = registry.invoke("unknown")
        assert "不存在" in result
    
    def test_list_names(self):
        """测试列出工具名。"""
        registry = ToolRegistry()
        
        @tool()
        def tool1() -> str:
            return "1"
        
        @tool()
        def tool2() -> str:
            return "2"
        
        registry.auto_register(tool1, tool2)
        names = registry.list_names()
        assert "tool1" in names
        assert "tool2" in names


class TestBuiltinTools:
    """内置工具测试。"""
    
    def test_read_file(self, tmp_path):
        """测试读取文件。"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello", encoding="utf-8")
        
        result = read_file.invoke(str(test_file))
        assert result == "hello"
    
    def test_read_file_not_found(self):
        """测试读取不存在的文件。"""
        result = read_file.invoke("/nonexistent/file.txt")
        assert "不存在" in result
    
    def test_write_to_file(self, tmp_path):
        """测试写入文件。"""
        test_file = tmp_path / "test.txt"
        
        result = write_to_file.invoke(str(test_file), "hello")
        assert "成功" in result
        assert test_file.read_text(encoding="utf-8") == "hello"
    
    def test_run_terminal_command(self):
        """测试执行终端命令。"""
        result = run_terminal_command.invoke("echo hello")
        assert "hello" in result
    
    def test_run_dangerous_command(self):
        """测试危险命令拦截。"""
        result = run_terminal_command.invoke("rm -rf /")
        assert "安全限制" in result
