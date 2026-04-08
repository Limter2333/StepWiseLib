"""
Frontend Developer Agent - 前端开发智能体
==========================================

职责:
- 前端代码生成 (React, Vue, HTML/CSS)
- 响应式布局设计
- UI组件开发
- 前端性能优化
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from core.prompt_engine import prompt_manager
from core.guardrails import guardrails
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel


class FrontendFramework(Enum):
    """前端框架"""
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    HTML_CSS = "html_css"
    NEXTJS = "nextjs"
    FLUTTER = "flutter"


class TaskType(Enum):
    """前端任务类型"""
    COMPONENT = "component"
    PAGE = "page"
    RESPONSIVE = "responsive"
    ANIMATION = "animation"
    STATE_MANAGEMENT = "state_management"


@dataclass
class FrontendTask:
    """前端任务"""
    id: str
    task_type: TaskType
    description: str
    framework: FrontendFramework
    requirements: List[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.requirements is None:
            self.requirements = []


@dataclass
class FrontendResult:
    """前端结果"""
    code: str
    framework: str
    component_name: str
    css: Optional[str] = None
    tests: Optional[str] = None
    documentation: Optional[str] = None
    quality_score: float = 0.0


class FrontendDeveloper:
    """前端开发智能体

    【能力】
    - 生成React/Vue组件
    - HTML/CSS响应式布局
    - 前端状态管理
    - 动画效果实现
    """

    def __init__(self):
        self.name = "Frontend Developer"
        self.specialty = ["React", "Vue", "HTML/CSS", "JavaScript", "TypeScript"]
        self.current_task: Optional[FrontendTask] = None

    async def generate_component(
        self,
        description: str,
        framework: str = "react",
        props: Optional[Dict] = None,
        styles: Optional[str] = None
    ) -> FrontendResult:
        """生成前端组件

        Args:
            description: 组件描述
            framework: 框架 (react/vue/html_css)
            props: 组件属性
            styles: 样式定义

        Returns:
            FrontendResult: 生成的组件代码
        """
        guard_result = guardrails.check_input(description)
        if not guard_result.passed:
            raise ValueError(f"Input blocked: {guard_result.passed}")

        try:
            llm = get_llm()
            system_prompt = f"You are a senior {framework} developer. Generate clean, production-ready code."
            user_prompt = f"""Generate a {framework} component for:
Description: {description}
Props: {props or {}}
Requirements: {styles or 'Modern, clean design'}

Return only the component code with inline styles or CSS modules.
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )
            code = response.content

            # 生成CSS
            css = self._generate_styles(framework, description)

            # 生成测试
            tests = await self._generate_tests(framework, description)

            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"Frontend LLM call failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            code = self._generate_placeholder_component(framework, description)
            css = self._generate_styles(framework, description)
            tests = "# Tests placeholder"
            quality_score = 0.5

        return FrontendResult(
            code=code,
            framework=framework,
            component_name=self._extract_component_name(description),
            css=css,
            tests=tests,
            documentation=self._generate_docs(description, framework),
            quality_score=quality_score
        )

    async def generate_page(
        self,
        description: str,
        framework: str = "react",
        routing: bool = True
    ) -> FrontendResult:
        """生成完整页面"""
        guard_result = guardrails.check_input(description)
        if not guard_result.passed:
            raise ValueError(f"Input blocked")

        try:
            llm = get_llm()
            system_prompt = f"You are a senior {framework} full-stack developer."
            user_prompt = f"""Generate a complete {framework} page with:
Description: {description}
Routing: {'Enabled' if routing else 'Disabled'}

Include:
- Component structure
- State management
- Event handlers
- Responsive styles
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )
            code = response.content
            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"Page generation failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            code = self._generate_placeholder_page(framework, description)
            quality_score = 0.5

        return FrontendResult(
            code=code,
            framework=framework,
            component_name="Page",
            css=None,
            tests=None,
            documentation=self._generate_docs(description, framework),
            quality_score=quality_score
        )

    async def optimize_performance(
        self,
        code: str,
        framework: str = "react"
    ) -> Dict:
        """前端性能优化"""
        suggestions = []

        # 基础检查
        if "useEffect" in code and "useCallback" not in code:
            suggestions.append("Consider wrapping callbacks in useCallback")

        if code.count("useState") > 10:
            suggestions.append("Consider using useReducer for complex state")

        if "inline styles" in code.lower():
            suggestions.append("Consider extracting styles to CSS modules")

        # 检查重复渲染
        if "console.log" in code:
            suggestions.append("Remove console.log statements in production")

        return {
            "suggestions": suggestions,
            "performance_score": max(0, 100 - len(suggestions) * 10),
            "framework": framework
        }

    def _generate_placeholder_component(self, framework: str, description: str) -> str:
        """生成占位组件"""
        if framework == "react":
            return f"""import React from 'react';
import './{self._to_kebab_case(description)}.css';

export const {self._to_pascal_case(description)} = () => {{
  return (
    <div className="{self._to_kebab_case(description)}">
      <h2>{description}</h2>
      {{/* TODO: Implement component */}}
    </div>
  );
}};
"""
        elif framework == "vue":
            return f"""<template>
  <div class="{self._to_kebab_case(description)}">
    <h2>{{ title }}</h2>
  </div>
</template>

<script>
export default {{
  name: '{self._to_pascal_case(description)}'
}};
</script>
"""
        return f"<!-- {description} -->"

    def _generate_placeholder_page(self, framework: str, description: str) -> str:
        """生成占位页面"""
        return self._generate_placeholder_component(framework, description)

    def _generate_styles(self, framework: str, description: str) -> str:
        """生成样式"""
        return f""".{self._to_kebab_case(description)} {{
  padding: 20px;
  margin: 0 auto;
  max-width: 1200px;
}}

.{self._to_kebab_case(description)} h2 {{
  color: #333;
  font-size: 1.5rem;
}}
"""

    async def _generate_tests(self, framework: str, description: str) -> str:
        """生成测试"""
        if framework == "react":
            return f"""import {{ render, screen }} from '@testing-library/react';
import {{ {self._to_pascal_case(description)} }} from './{self._to_kebab_case(description)}';

describe('{self._to_pascal_case(description)}', () => {{
  test('renders component', () => {{
    render(<{self._to_pascal_case(description)} />);
    expect(screen.getByText('{description}')).toBeInTheDocument();
  }});
}});
"""
        return "# Tests placeholder"

    def _generate_docs(self, description: str, framework: str) -> str:
        """生成文档"""
        return f"""## {description} Component

**Framework:** {framework}

### Usage
```{"jsx" if framework == "react" else "vue"}
<{self._to_pascal_case(description)} />
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| className | string | Custom CSS class |
"""

    def _to_kebab_case(self, text: str) -> str:
        """转kebab-case"""
        return "".join(["-" + c.lower() if c.isupper() else c.lower() for c in text]).lstrip("-")

    def _to_pascal_case(self, text: str) -> str:
        """转PascalCase"""
        words = text.replace("_", " ").split()
        return "".join(word.capitalize() for word in words)

    def _extract_component_name(self, description: str) -> str:
        return self._to_pascal_case(description)

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "supported_frameworks": [f.value for f in FrontendFramework],
            "task_types": [t.value for t in TaskType]
        }


# 全局实例
frontend_developer = FrontendDeveloper()
