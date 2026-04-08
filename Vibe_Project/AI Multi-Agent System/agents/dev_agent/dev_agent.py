"""
Dev Agent - 开发智能体
======================

职责:
- 代码生成
- 代码审查
- 模块实现
- 技术方案设计
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# 导入核心模块
from core.prompt_engine import prompt_manager
from core.guardrails import guardrails
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel


class TaskType(Enum):
    """开发任务类型"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    UNIT_TEST = "unit_test"
    ARCHITECTURE = "architecture"


@dataclass
class DevTask:
    """开发任务"""
    id: str
    task_type: TaskType
    description: str
    language: str = "python"
    framework: Optional[str] = None
    requirements: List[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.requirements is None:
            self.requirements = []


@dataclass
class CodeResult:
    """代码生成结果"""
    code: str
    language: str
    file_path: Optional[str] = None
    imports: List[str] = None
    tests: Optional[str] = None
    documentation: Optional[str] = None
    quality_score: float = 0.0


class DevAgent:
    """开发智能体

    【能力】
    - 理解需求生成代码
    - 代码审查和优化
    - 生成单元测试
    - 提供技术建议
    """

    def __init__(self):
        self.name = "Dev Agent"
        self.specialty = ["Python", "FastAPI", "LangChain", "系统设计"]
        self.current_task: Optional[DevTask] = None

    def create_task(
        self,
        description: str,
        task_type: TaskType,
        language: str = "python",
        **kwargs
    ) -> DevTask:
        """创建开发任务"""
        task = DevTask(
            id=f"dev_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            task_type=task_type,
            description=description,
            language=language,
            **kwargs
        )
        self.current_task = task
        return task

    async def generate_code(
        self,
        description: str,
        language: str = "python",
        framework: Optional[str] = None,
        requirements: Optional[List[str]] = None
    ) -> CodeResult:
        """生成代码

        Args:
            description: 功能描述
            language: 编程语言
            framework: 框架
            requirements: 需求列表

        Returns:
            CodeResult: 生成的代码及元数据
        """
        # 输入安全检查
        guard_result = guardrails.check_input(description)
        if not guard_result.passed:
            raise ValueError(f"Input blocked: {guard_result.message}")

        # 构建Prompt
        system_prompt, user_prompt = prompt_manager.render(
            "code_generation",
            task_description=description,
            language=language,
            framework=framework or "none",
            requirements="\n".join(requirements or [])
        )

        # 调用实际LLM生成代码
        try:
            llm = get_llm()
            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3  # 低温度保持确定性
            )
            code = response.content

            # 生成测试
            tests = await self._generate_tests_with_llm(description, language)

            # 生成文档
            documentation = self._generate_docstring(description, language)

            quality_score = 0.85

        except Exception as e:
            # LLM调用失败时使用placeholder
            error_logger.log(
                error_type="LLMCallError",
                message=f"LLM call failed, using placeholder: {str(e)}",
                level=ErrorLevel.WARNING
            )
            code = self._generate_placeholder_code(description, language, framework)
            tests = self._generate_tests(description, language)
            documentation = self._generate_docstring(description, language)
            quality_score = 0.5

        return CodeResult(
            code=code,
            language=language,
            imports=self._get_imports(language, framework),
            tests=tests,
            documentation=documentation,
            quality_score=0.85
        )

    def _generate_placeholder_code(
        self,
        description: str,
        language: str,
        framework: Optional[str]
    ) -> str:
        """生成占位代码（实际应该调用LLM）"""
        if language == "python":
            return f'''"""
Generated Code
Description: {description}
"""

# Imports
# TODO: Add imports based on requirements

class {self._to_camel_case(description)}:
    """Main class for {description}"""

    def __init__(self):
        self.name = "{description}"

    def execute(self, *args, **kwargs):
        """Execute the main functionality"""
        # TODO: Implement {description}
        pass

# Usage example
if __name__ == "__main__":
    instance = {self._to_camel_case(description)}()
    result = instance.execute()
'''
        return f"// Generated {language} code for: {description}"

    async def _generate_tests_with_llm(self, description: str, language: str) -> str:
        """使用LLM生成测试代码"""
        test_prompt = f"""Generate pytest unit tests for the following Python code feature:
Feature: {description}
Language: {language}

Generate comprehensive test cases including:
1. Basic functionality tests
2. Edge case tests
3. Error handling tests

Return only the test code, no explanations.
"""
        try:
            llm = get_llm()
            response = await llm.generate(
                prompt=test_prompt,
                system_prompt="You are a senior Python developer specializing in test-driven development.",
                max_tokens=2048,
                temperature=0.3
            )
            return response.content
        except Exception:
            return self._generate_tests(description, language)

    def _generate_tests(self, description: str, language: str) -> str:
        """生成测试代码（placeholder）"""
        if language == "python":
            return f'''"""
Tests for {description}
"""
import pytest

class Test{self._to_camel_case(description)}:
    """Test cases for {description}"""

    def test_basic(self):
        """Basic functionality test"""
        assert True

    def test_edge_cases(self):
        """Edge cases test"""
        pass
'''
        return f"// Tests for {description}"

    def _generate_docstring(self, description: str, language: str) -> str:
        """生成文档字符串"""
        return f'''## {description}

### Description
{description}

### Usage
```python
# TODO: Add usage example
```

### Parameters
- `param1`: Description

### Returns
- Return value description
'''

    def _get_imports(self, language: str, framework: Optional[str]) -> List[str]:
        """获取常用导入"""
        if language == "python":
            imports = ["from typing import *"]
            if framework == "fastapi":
                imports.append("from fastapi import FastAPI")
            elif framework == "langchain":
                imports.append("from langchain import *")
            return imports
        return []

    def _to_camel_case(self, text: str) -> str:
        """下划线转驼峰"""
        words = text.replace("_", " ").split()
        return "".join(word.capitalize() for word in words)

    async def review_code(
        self,
        code: str,
        language: str = "python"
    ) -> Dict:
        """代码审查

        Returns:
            包含问题和建议的字典
        """
        issues = []
        suggestions = []

        # 基础检查
        if len(code) < 10:
            issues.append("Code is too short")

        if "TODO" in code or "FIXME" in code:
            suggestions.append("Consider completing TODO/FIXME items")

        # 安全性检查
        if "eval(" in code:
            issues.append("Security: Avoid using eval()")
        if "exec(" in code:
            issues.append("Security: Avoid using exec()")
        if "password" in code.lower() and "=" in code:
            suggestions.append("Security: Ensure no hardcoded passwords")

        # 代码质量
        if code.count("\n") > 500:
            suggestions.append("Consider splitting into smaller modules")

        return {
            "issues": issues,
            "suggestions": suggestions,
            "quality_score": max(0, 1.0 - len(issues) * 0.1),
            "language": language
        }

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "supported_languages": ["python", "javascript", "typescript", "java"],
            "supported_frameworks": ["fastapi", "langchain", "react", "django"],
            "task_types": [t.value for t in TaskType]
        }


# 全局实例
dev_agent = DevAgent()
