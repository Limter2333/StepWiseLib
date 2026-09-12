from typing import Optional
from .base import ToolSpec, ToolArgumentError


class ToolRegistry:
    """工具注册表，管理所有可用工具。
    
    设计意图：提供统一的工具注册、发现、调用接口，
    让 AgentRunner 不需要关心工具的具体实现细节。
    """
    
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
    
    def register(self, spec: ToolSpec) -> None:
        """注册一个工具。
        
        如果工具名已存在，会覆盖旧的定义。
        """
        if spec.name in self._tools:
            print(f"⚠️ 警告：工具 '{spec.name}' 已存在，将被覆盖")
        self._tools[spec.name] = spec
    
    def auto_register(self, *specs: ToolSpec) -> None:
        """批量注册工具。"""
        for spec in specs:
            self.register(spec)
    
    def get(self, name: str) -> Optional[ToolSpec]:
        """获取工具规格，不存在返回 None。"""
        return self._tools.get(name)
    
    def has(self, name: str) -> bool:
        """检查工具是否存在。"""
        return name in self._tools
    
    def list_names(self) -> list[str]:
        """返回所有已注册的工具名。"""
        return list(self._tools.keys())
    
    def invoke(self, name: str, args: tuple = (), kwargs: dict = None) -> str:
        """调用指定工具。
        
        Args:
            name: 工具名
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            工具执行结果字符串
            
        Raises:
            KeyError: 工具不存在
            ToolArgumentError: 参数校验失败
        """
        if name not in self._tools:
            available = ", ".join(self._tools.keys())
            return f"工具 '{name}' 不存在。可用工具：{available}"
        
        spec = self._tools[name]
        return spec.invoke(*args, **(kwargs or {}))
    
    def to_prompt_list(self) -> str:
        """生成供系统提示词使用的工具列表。"""
        if not self._tools:
            return "暂无可用工具"
        
        lines = [spec.to_prompt_schema() for spec in self._tools.values()]
        return "\n".join(lines)
