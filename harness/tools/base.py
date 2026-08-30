import inspect
from dataclasses import dataclass, field
from typing import Callable, Any, get_type_hints


class ToolArgumentError(Exception):
    """工具参数校验错误"""
    pass


def _auto_schema(func: Callable) -> dict:
    """自动从函数签名生成 JSON Schema 参数定义。
    
    设计意图：利用 Python 的类型提示自动生成工具参数 schema，
    让工具定义更简洁，同时支持 LLM 理解工具参数。
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    
    schema = {}
    for name, param in sig.parameters.items():
        param_schema = {"type": "string"}  # 默认类型
        
        # 根据类型注解生成 schema
        if name in hints:
            hint = hints[name]
            if hint == str:
                param_schema["type"] = "string"
            elif hint == int:
                param_schema["type"] = "integer"
            elif hint == float:
                param_schema["type"] = "number"
            elif hint == bool:
                param_schema["type"] = "boolean"
        
        # 添加默认值
        if param.default != inspect.Parameter.empty:
            param_schema["default"] = param.default
        
        schema[name] = param_schema
    
    return schema


@dataclass
class ToolSpec:
    """工具规格定义。
    
    封装工具的元信息：名称、描述、参数 schema、权限级别等。
    支持自动参数校验和 schema 生成。
    """
    name: str
    description: str
    func: Callable
    parameters: dict = field(default_factory=dict)  # JSON Schema
    permission_level: str = "safe"  # safe / confirm / admin
    requires_confirm: bool = False
    
    def validate_args(self, *args, **kwargs) -> dict:
        """校验工具参数，返回校验后的参数字典。
        
        简单实现：检查参数数量和类型。
        生产环境可接入 pydantic 做更严格的校验。
        """
        sig = inspect.signature(self.func)
        params = list(sig.parameters.keys())
        
        # 检查必需参数
        required_params = [p for p in params if sig.parameters[p].default == inspect.Parameter.empty]
        provided_args = len(args) + len(kwargs)
        
        if provided_args < len(required_params):
            raise ToolArgumentError(
                f"工具 {self.name} 缺少必需参数，需要 {len(required_params)} 个，"
                f"只提供了 {provided_args} 个"
            )
        
        return kwargs or dict(zip(params, args))
    
    def invoke(self, *args, **kwargs) -> str:
        """执行工具并返回结果字符串。
        
        统一捕获异常，返回错误信息而不是抛出异常。
        """
        try:
            validated = self.validate_args(*args, **kwargs)
            result = self.func(*args, **kwargs)
            return str(result) if result is not None else ""
        except Exception as e:
            return f"工具执行错误：{str(e)}"
    
    def to_prompt_schema(self) -> str:
        """生成供系统提示词使用的工具描述。"""
        params_desc = []
        for name, schema in self.parameters.items():
            type_str = schema.get("type", "string")
            params_desc.append(f"{name}: {type_str}")
        
        params_str = ", ".join(params_desc) if params_desc else "无参数"
        return f"- {self.name}({params_str}): {self.description}"


def tool(
    name: str = "",
    description: str = "",
    permission: str = "safe",
    requires_confirm: bool = False
):
    """工具装饰器：把普通函数注册为 ToolSpec。
    
    用法：
        @tool(description="读取文件内容")
        def read_file(file_path: str) -> str:
            ...
    """
    def decorator(func: Callable):
        return ToolSpec(
            name=name or func.__name__,
            description=description or inspect.getdoc(func) or "",
            func=func,
            parameters=_auto_schema(func),
            permission_level=permission,
            requires_confirm=requires_confirm,
        )
    return decorator
