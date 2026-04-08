"""
Prompt工程模块 Prompt Engine
===========================

【学习要点】
1. 什么是Prompt Engineering?
   - 设计有效的提示词来引导LLM
   - 包括: 指令、上下文、案例、输出格式

2. Prompt的组成部分
   - System Prompt: 定义AI角色和行为
   - Context: 外部知识/检索结果
   - Few-shot Examples: 案例学习
   - User Input: 用户问题
   - Output Format: 输出格式要求

3. 为什么需要Prompt模板?
   - 标准化: 统一格式
   - 可复用: 模板化
   - 可追踪: 版本管理
   - 可优化: A/B测试
"""

from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import json
import re


class PromptTemplate(BaseModel):
    """Prompt模板

    【模板结构】
    - name: 模板名称
    - description: 用途描述
    - system_prompt: 系统级指令
    - user_template: 用户输入模板
    - examples: Few-shot案例
    - output_format: 输出格式要求
    - variables: 变量定义
    """
    name: str
    description: str
    version: str = "1.0"
    system_prompt: str = ""
    user_template: str = ""
    examples: List[Dict[str, str]] = []  # [{"input": "...", "output": "..."}]
    output_format: Optional[str] = None
    variables: Dict[str, str] = {}  # 变量名 -> 描述
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def render(self, **kwargs) -> tuple[str, str]:
        """渲染模板

        Returns:
            (system_prompt, full_user_prompt)
        """
        # 替换变量
        system = self._render_string(self.system_prompt, kwargs)
        user = self._render_string(self.user_template, kwargs)

        # 添加Few-shot示例
        if self.examples:
            user = self._add_few_shot(user, kwargs)

        # 添加输出格式要求
        if self.output_format:
            user += f"\n\n## Output Format\n{self.output_format}"

        return system, user

    def _render_string(self, template: str, context: Dict) -> str:
        """渲染字符串模板

        【学习要点】模板渲染
        - 占位符: {{variable}}
        - 条件: {{#if var}}...{{/if}}
        - 循环: {{#each items}}...{{/each}}
        """
        result = template

        # 简单变量替换 {{variable}}
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # 清理未替换的变量
        result = re.sub(r'\{\{[^}]+\}\}', '', result)

        return result.strip()

    def _add_few_shot(self, user_prompt: str, context: Dict) -> str:
        """添加Few-shot示例"""
        examples_text = "\n\n## Examples\n"

        for i, example in enumerate(self.examples):
            inp = self._render_string(example.get("input", ""), context)
            out = self._render_string(example.get("output", ""), context)
            examples_text += f"Example {i+1}:\nInput: {inp}\nOutput: {out}\n\n"

        return user_prompt + examples_text


class PromptManager:
    """Prompt管理器

    【功能】
    - 模板存储和加载
    - 模板版本管理
    - 动态模板生成
    - 模板组合和继承
    """

    # 内置模板
    DEFAULT_TEMPLATES = {
        "rag_qa": {
            "name": "rag_qa",
            "description": "RAG问答模板",
            "system_prompt": """You are a knowledgeable AI assistant with access to a comprehensive knowledge base.
Your task is to provide detailed, thorough answers based SOLELY on the provided context.

CRITICAL INSTRUCTIONS:
- Draw information from ALL provided context snippets — do not ignore any relevant details
- Expand fully on each concept mentioned in the context — do not truncate or summarize prematurely
- When multiple sources contain relevant information, synthesize them into a comprehensive answer
- Use the context verbatim when citing specific facts, data, or definitions
- Structure your answer with clear sections and bullet points where appropriate
- Do NOT say "the context mentions" or similar — integrate the information naturally
- If the context contains partial information, explain what IS provided fully
- Aim for completeness over brevity — you have context to draw from, use it""",
            "user_template": """## Knowledge Base Context
{{context}}

## User Question
{{question}}

## Your Task
Based ONLY on the knowledge base context above, provide a comprehensive and detailed answer. Extract every relevant detail from the context and present it in a well-organized format. Do not leave any valuable information unused.""",
            "output_format": """## Answer Structure
- Main explanation (detailed, with all relevant facts)
- Supporting details from context
- Any related information that expands on the topic

## Formatting Requirements
- Use markdown headers and bullet points for readability
- Bold key terms when first introduced
- Provide complete explanations, not summaries"""
        },

        "code_generation": {
            "name": "code_generation",
            "description": "代码生成模板",
            "system_prompt": """You are an expert software engineer specializing in code generation.
You generate clean, efficient, well-structured, and production-ready code.

Your code generation principles:
1. Follow best practices and design patterns
2. Write self-documenting code with clear variable/function names
3. Include proper error handling
4. Add type hints for better IDE support
5. Consider security implications
6. Optimize for readability and maintainability""",
            "user_template": """## Code Generation Request

### Feature Description
{{task_description}}

### Programming Language
{{language}}

### Framework (if any)
{{framework}}

### Requirements
{{requirements}}

## Output Format
Generate complete, working code following these requirements.
Return ONLY the code itself, properly formatted with markdown code blocks.
Do NOT include explanations, comments about the code, or any text outside the code block.""",
            "output_format": """## Code Output
```{{language}}
[Your generated code here]
```

## Quality Checklist
- [ ] Code compiles/runs without errors
- [ ] All imports are correct
- [ ] Error handling is included
- [ ] Type hints are provided
- [ ] Code follows language conventions"""
        },

        "agent_task": {
            "name": "agent_task",
            "description": "Agent任务执行模板",
            "system_prompt": """You are {{agent_role}}, an AI agent specialized in {{agent_specialty}}.
Your capabilities include: {{capabilities}}

Always follow these principles:
1. Think step by step
2. Request clarification when needed
3. Report progress regularly
4. Escalate issues when necessary""",
            "user_template": """## Task
{{task_description}}

## Available Tools
{{available_tools}}

## Constraints
{{constraints}}

Execute the task and report your results.""",
            "output_format": """## Result
[Your response here]

## Evidence
[Supporting information]

## Next Steps
[If applicable]"""
        },

        "document_analysis": {
            "name": "document_analysis",
            "description": "文档分析模板",
            "system_prompt": """You are an expert document analyst.
Analyze the provided document and extract key information.""",
            "user_template": """## Document
{{document_content}}

## Analysis Task
{{analysis_type}}

Provide a thorough analysis.""",
            "examples": [
                {
                    "input": "Document: The company revenue was $1M in Q1.\nAnalysis: Key metrics",
                    "output": "Key Metrics:\n- Revenue: $1M\n- Period: Q1"
                }
            ]
        },

        "code_review": {
            "name": "code_review",
            "description": "代码审查模板",
            "system_prompt": """You are a senior code reviewer.
Review the provided code for:
- Correctness
- Performance
- Security
- Code quality""",
            "user_template": """## Code
```{language}}
{{code}}
```

## Review Focus
{{review_focus}}

Provide detailed feedback.""",
            "output_format": """## Issues Found
[List any issues]

## Suggestions
[Improvement recommendations]

## Rating
[1-5 scale]"""
        },

        "test_generation": {
            "name": "test_generation",
            "description": "测试代码生成模板",
            "system_prompt": """You are an expert software engineer specializing in test-driven development.
You generate comprehensive, high-quality test cases that cover:
1. Happy path (basic functionality)
2. Edge cases and boundary conditions
3. Error handling and exception cases
4. Performance considerations

Your tests follow pytest conventions and best practices.""",
            "user_template": """## Generate Tests For

### Feature/Code Description
{{description}}

### Programming Language
{{language}}

### Framework
{{framework}}

### Existing Code (if available)
```{language}}
{{code}}
```

## Requirements
Generate pytest unit tests covering:
1. Basic functionality tests
2. Edge case tests (empty input, null values, boundary values)
3. Error handling tests
4. Integration points

Return ONLY the test code in a markdown code block.""",
            "output_format": """## Test Output
```{language}}
[Your pytest test code here]
```

## Quality Checklist
- [ ] Tests are independent and can run in any order
- [ ] Proper fixtures are used
- [ ] Descriptive test names follow pytest conventions
- [ ] Both positive and negative cases covered
- [ ] Edge cases included"""
        },

        "doc_generation": {
            "name": "doc_generation",
            "description": "文档生成模板",
            "system_prompt": """You are an expert technical documentation writer.
You generate comprehensive, well-structured documentation that:
1. Uses clear headings and structure
2. Includes practical examples
3. Explains concepts thoroughly
4. Follows documentation best practices
5. Supports both Chinese and English audiences""",
            "user_template": """## Documentation Generation Request

### Document Type
{{doc_type}}

### Project/Subject Name
{{project_name}}

### Description
{{description}}

### Key Features/Components
{{features}}

### Tech Stack (if applicable)
{{tech_stack}}

### Target Audience
{{audience}}

## Requirements
Generate a comprehensive {{doc_type}} document following these requirements.
Use markdown format with proper headings, lists, and code blocks where appropriate.""",
            "output_format": """## Document Output
[Your generated documentation in markdown format]

## Quality Checklist
- [ ] Clear title and introduction
- [ ] Logical structure with proper headings
- [ ] Includes code examples where relevant
- [ ] Comprehensive coverage of topics
- [ ] Easy to navigate and read"""
        },

        "intent_classification": {
            "name": "intent_classification",
            "description": "意图分类模板",
            "system_prompt": """You are an expert intent classification system.
Classify the user message into one of the following intent categories:
- question: User is asking a question (what, how, why, when, where)
- request: User is requesting something to be done (create, generate, build)
- update: User wants to modify or update something
- delete: User wants to remove something
- greeting: User is greeting or making small talk
- thanks: User is expressing gratitude
- farewell: User is saying goodbye
- feedback: User is providing feedback or suggestions
- complaint: User is complaining about something
- general: None of the above

Return ONLY the intent category name, nothing else.""",
            "user_template": """## User Message
{{message}}

## Context (if any)
{{context}}

Classify the intent of this message.""",
            "output_format": """## Intent
[One word only: question, request, update, delete, greeting, thanks, farewell, feedback, complaint, or general]"""
        }
    }

    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir
        self.templates: Dict[str, PromptTemplate] = {}

        # 加载内置模板
        for name, config in self.DEFAULT_TEMPLATES.items():
            self.templates[name] = PromptTemplate(**config)

        # 加载自定义模板
        if templates_dir:
            self._load_custom_templates()

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(name)

    def register_template(self, template: PromptTemplate):
        """注册模板"""
        self.templates[template.name] = template
        print(f"[PromptEngine] Registered template: {template.name}")

    def render(
        self,
        template_name: str,
        **context
    ) -> tuple[str, str]:
        """渲染模板"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        return template.render(**context)

    def add_example(
        self,
        template_name: str,
        input_text: str,
        output_text: str
    ):
        """为模板添加示例"""
        template = self.get_template(template_name)
        if template:
            template.examples.append({
                "input": input_text,
                "output": output_text
            })

    def create_from_string(
        self,
        name: str,
        description: str,
        system_prompt: str,
        user_template: str,
        **kwargs
    ) -> PromptTemplate:
        """从字符串创建模板

        【使用场景】
        - 动态创建简单模板
        - 无需定义类
        """
        template = PromptTemplate(
            name=name,
            description=description,
            system_prompt=system_prompt,
            user_template=user_template,
            **kwargs
        )
        self.register_template(template)
        return template

    def _load_custom_templates(self):
        """加载自定义模板"""
        if not self.templates_dir:
            return

        templates_path = Path(self.templates_dir)
        if not templates_path.exists():
            return

        for file in templates_path.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    template = PromptTemplate(**config)
                    self.register_template(template)
            except Exception as e:
                print(f"[PromptEngine] Failed to load {file}: {e}")

    def list_templates(self) -> List[Dict]:
        """列出所有模板"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "version": t.version,
                "has_examples": len(t.examples) > 0
            }
            for t in self.templates.values()
        ]

    def save_template(self, name: str, path: str):
        """保存模板到文件"""
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template not found: {name}")

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(template.model_dump(), f, ensure_ascii=False, indent=2)


# 便捷函数
def build_rag_prompt(question: str, context: str) -> tuple[str, str]:
    """构建RAG问答Prompt

    【学习要点】简化接口
    - 封装常用操作
    - 一行调用
    """
    manager = PromptManager()
    return manager.render(
        "rag_qa",
        question=question,
        context=context
    )


def build_agent_prompt(
    task: str,
    agent_role: str,
    agent_specialty: str,
    capabilities: List[str]
) -> tuple[str, str]:
    """构建Agent任务Prompt"""
    manager = PromptManager()
    return manager.render(
        "agent_task",
        task_description=task,
        agent_role=agent_role,
        agent_specialty=agent_specialty,
        capabilities=", ".join(capabilities),
        available_tools="See documentation",
        constraints="Complete within time limits"
    )


# 全局实例
prompt_manager = PromptManager()
