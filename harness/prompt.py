import abc
import platform
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PromptTemplate:
    """提示词模板，支持变量替换。"""
    template: str
    variables: dict[str, str] = field(default_factory=dict)
    
    def render(self, **kwargs) -> str:
        """渲染模板，替换变量。
        
        支持 ${variable} 和 {variable} 两种格式。
        """
        merged = {**self.variables, **kwargs}
        result = self.template
        
        for key, value in merged.items():
            result = result.replace(f"${{{key}}}", str(value))
            result = result.replace(f"{{{key}}}", str(value))
        
        return result


class PromptProvider(abc.ABC):
    """提示词提供者抽象基类。
    
    设计意图：将提示词模板与 Agent 核心循环解耦，
    支持不同的提示词策略（ReAct、Plan-and-Execute 等）。
    """
    
    @abc.abstractmethod
    def get_system_prompt(self, **kwargs) -> str:
        """获取系统提示词。
        
        Args:
            **kwargs: 动态变量，如 tool_list、file_list 等
            
        Returns:
            渲染后的系统提示词
        """
        pass
    
    @abc.abstractmethod
    def get_format_instructions(self) -> str:
        """获取输出格式说明。"""
        pass
    
    @abc.abstractmethod
    def get_examples(self) -> str:
        """获取示例。"""
        pass
    
    def get_environment_info(self) -> dict[str, str]:
        """获取环境信息。"""
        os_map = {
            "Darwin": "macOS",
            "Windows": "Windows",
            "Linux": "Linux"
        }
        return {
            "operating_system": os_map.get(platform.system(), "Unknown"),
        }


class ReActPromptProvider(PromptProvider):
    """ReAct 模式提示词提供者。"""
    
    def __init__(self, custom_template: Optional[PromptTemplate] = None):
        """初始化。
        
        Args:
            custom_template: 自定义模板（可选）
        """
        self._template = custom_template or self._default_template()
    
    def get_system_prompt(self, **kwargs) -> str:
        """获取 ReAct 系统提示词。"""
        env_info = self.get_environment_info()
        merged = {**env_info, **kwargs}
        return self._template.render(**merged)
    
    def get_format_instructions(self) -> str:
        """获取格式说明。"""
        return """所有步骤请严格使用以下 XML 标签格式输出：
- <question> 用户问题
- <thought> 思考
- <action> 采取的工具操作
- <observation> 工具或环境返回的结果
- <final_answer> 最终答案

关键规则：
- 每次回答都必须包括 <thought>，然后是 <action> 或 <final_answer>
- 输出 <action> 后立即停止生成，等待真实的 <observation>
- 工具参数中的文件路径请使用绝对路径
- 如果参数包含多行，请使用 \\n 表示换行"""
    
    def get_examples(self) -> str:
        """获取示例。"""
        return """例子 1:

<question>埃菲尔铁塔有多高？</question>
<thought>我需要找到埃菲尔铁塔的高度。可以使用搜索工具。</thought>
<action>get_height("埃菲尔铁塔")</action>
<observation>埃菲尔铁塔的高度约为330米（包含天线）。</observation>
<thought>搜索结果显示了高度。我已经得到答案了。</thought>
<final_answer>埃菲尔铁塔的高度约为330米。</final_answer>

例子 2:

<question>帮我找一个简单的番茄炒蛋食谱，并看看家里的冰箱里有没有西红柿。</question>
<thought>这个任务分两步。第一步，找到番茄炒蛋的食谱。第二步，检查冰箱里是否有西红柿。我先用 find_recipe 工具找食谱。</thought>
<action>find_recipe(dish="番茄炒蛋")</action>
<observation>简单的番茄炒蛋食谱：将2个鸡蛋打散，2个番茄切块。热油，先炒鸡蛋，盛出。再热油，炒番茄至软烂，加入鸡蛋，放盐调味即可。</observation>
<thought>好的，我已经有食谱了。食谱需要西红柿。现在我需要用 check_fridge 工具看看冰箱里有没有西红柿。</thought>
<action>check_fridge(item="西红柿")</action>
<observation>冰箱检查结果：有3个西红柿。</observation>
<thought>我找到了食谱，并且确认了冰箱里有西红柿。可以回答问题了。</thought>
<final_answer>简单的番茄炒蛋食谱是：鸡蛋打散，番茄切块。先炒鸡蛋，再炒番茄，混合后加盐调味。冰箱里有3个西红柿。</final_answer>"""
    
    def _default_template(self) -> PromptTemplate:
        """获取默认模板。"""
        return PromptTemplate(
            template="""你需要解决一个问题。为此，你需要将问题分解为多个步骤。对于每个步骤，首先使用 <thought> 思考要做什么，然后使用可用工具之一决定一个 <action>。接着，你将根据你的行动从环境/工具中收到一个 <observation>。持续这个思考和行动的过程，直到你有足够的信息来提供 <final_answer>。

{format_instructions}

---

{examples}

---

本次任务可用工具：
{tool_list}

---

环境信息：
操作系统：{operating_system}"""
        )


class SimplePromptProvider(PromptProvider):
    """简单提示词提供者，用于不需要复杂推理的场景。"""
    
    def get_system_prompt(self, **kwargs) -> str:
        """获取简单系统提示词。"""
        tool_list = kwargs.get("tool_list", "无")
        return f"""你是一个智能助手，可以帮助用户完成任务。

可用工具：
{tool_list}

请根据用户问题，选择合适的工具或直接给出答案。"""
    
    def get_format_instructions(self) -> str:
        """获取格式说明。"""
        return "直接输出你的回答，不需要特殊格式。"
    
    def get_examples(self) -> str:
        """获取示例。"""
        return ""


class CustomPromptProvider(PromptProvider):
    """自定义提示词提供者。"""
    
    def __init__(self, system_prompt: str, format_instructions: str = "", examples: str = ""):
        """初始化。
        
        Args:
            system_prompt: 系统提示词
            format_instructions: 格式说明
            examples: 示例
        """
        self._system_prompt = system_prompt
        self._format_instructions = format_instructions
        self._examples = examples
    
    def get_system_prompt(self, **kwargs) -> str:
        """获取自定义系统提示词。"""
        return self._system_prompt
    
    def get_format_instructions(self) -> str:
        """获取格式说明。"""
        return self._format_instructions
    
    def get_examples(self) -> str:
        """获取示例。"""
        return self._examples


def get_prompt_provider(provider_type: str = "react", **kwargs) -> PromptProvider:
    """工厂函数：获取提示词提供者。
    
    Args:
        provider_type: 提供者类型 ("react", "simple", "custom")
        **kwargs: 传递给提供者的参数
        
    Returns:
        PromptProvider 实例
    """
    if provider_type == "react":
        return ReActPromptProvider(**kwargs)
    elif provider_type == "simple":
        return SimplePromptProvider(**kwargs)
    elif provider_type == "custom":
        return CustomPromptProvider(**kwargs)
    else:
        raise ValueError(f"未知的提示词提供者类型：{provider_type}")
