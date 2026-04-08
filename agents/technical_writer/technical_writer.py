"""
Technical Writer Agent - 技术文档智能体
=====================================

职责:
- 技术文档撰写
- API文档生成
- 用户手册
- 变更日志维护
- 文档翻译
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.prompt_engine import prompt_manager
from core.guardrails import guardrails
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel


class DocType(Enum):
    """文档类型"""
    README = "readme"
    API_DOC = "api_doc"
    USER_GUIDE = "user_guide"
    TECHNICAL_DESIGN = "technical_design"
    CHANGELOG = "changelog"
    ARCHITECTURE = "architecture"
    TUTORIAL = "tutorial"
    FAQ = "faq"


@dataclass
class DocTask:
    """文档任务"""
    id: str
    doc_type: DocType
    title: str
    description: str
    audience: str = "developers"  # developers, users, stakeholders
    language: str = "en"
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class DocResult:
    """文档结果"""
    content: str
    doc_type: str
    title: str
    format: str = "markdown"
    sections: List[str] = field(default_factory=list)
    quality_score: float = 0.0


class TechnicalWriter:
    """技术文档智能体

    【能力】
    - 生成README文档
    - 撰写API文档
    - 编写用户手册
    - 维护变更日志
    - 技术方案文档
    """

    def __init__(self):
        self.name = "Technical Writer"
        self.specialty = ["Markdown", "OpenAPI", "技术写作", "文档结构化"]
        self.current_task: Optional[DocTask] = None

    async def generate_readme(
        self,
        project_name: str,
        description: str,
        features: List[str],
        tech_stack: Optional[List[str]] = None,
        installation: Optional[str] = None,
        usage: Optional[str] = None,
        license: str = "MIT"
    ) -> DocResult:
        """生成README文档

        Args:
            project_name: 项目名称
            description: 项目描述
            features: 功能列表
            tech_stack: 技术栈
            installation: 安装说明
            usage: 使用示例
            license: 许可证

        Returns:
            DocResult: README文档
        """
        guard_result = guardrails.check_input(project_name)
        if not guard_result.passed:
            raise ValueError(f"Input blocked: {guard_result.message}")

        try:
            llm = get_llm()
            system_prompt = """You are a senior technical writer specializing in creating
clear, comprehensive README documentation for software projects."""

            user_prompt = f"""Generate a professional README.md for:

Project Name: {project_name}
Description: {description}
Features: {', '.join(features)}
Tech Stack: {', '.join(tech_stack or [])}
License: {license}

Include all standard sections with proper formatting."""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )

            content = response.content
            sections = self._extract_sections(content)
            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"README generation failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            content = self._generate_placeholder_readme(project_name, description, features)
            sections = ["Title", "Description", "Features", "Installation", "Usage", "License"]
            quality_score = 0.5

        return DocResult(
            content=content,
            doc_type=DocType.README.value,
            title=project_name,
            sections=sections,
            quality_score=quality_score
        )

    async def generate_api_doc(
        self,
        endpoints: List[Dict],
        title: str = "API Documentation",
        auth_method: str = "Bearer Token"
    ) -> DocResult:
        """生成API文档

        Args:
            endpoints: 端点列表，每个包含 method, path, description, params, response
            title: 文档标题
            auth_method: 认证方式

        Returns:
            DocResult: API文档
        """
        try:
            llm = get_llm()
            system_prompt = """You are a technical writer specializing in API documentation.
Generate clear, comprehensive API docs with request/response examples."""

            endpoints_str = "\n".join([
                f"- {ep['method']} {ep['path']}: {ep['description']}"
                for ep in endpoints
            ])

            user_prompt = f"""Generate API documentation in Markdown format:

Title: {title}
Authentication: {auth_method}
Endpoints:
{endpoints_str}

For each endpoint include:
- Method and Path
- Description
- Request Parameters
- Request Body (if applicable)
- Response Codes
- Example Request/Response
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )

            content = response.content
            sections = self._extract_sections(content)
            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"API doc generation failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            content = self._generate_placeholder_api_doc(endpoints, title)
            sections = ["Overview", "Authentication", "Endpoints", "Errors"]
            quality_score = 0.5

        return DocResult(
            content=content,
            doc_type=DocType.API_DOC.value,
            title=title,
            sections=sections,
            quality_score=quality_score
        )

    async def generate_user_guide(
        self,
        product_name: str,
        features: List[str],
        getting_started: Optional[str] = None,
        faq: Optional[List[str]] = None
    ) -> DocResult:
        """生成用户指南

        Args:
            product_name: 产品名称
            features: 功能列表
            getting_started: 快速开始指南
            faq: 常见问题

        Returns:
            DocResult: 用户指南
        """
        try:
            llm = get_llm()
            system_prompt = """You are a technical writer creating user-friendly guides.
Use clear language, step-by-step instructions, and visual aids where possible."""

            user_prompt = f"""Generate a comprehensive user guide for:

Product: {product_name}
Features: {', '.join(features)}

Structure:
1. Introduction
2. Getting Started
3. Feature Walkthrough (for each major feature)
4. FAQ
5. Support Information
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )

            content = response.content
            sections = self._extract_sections(content)
            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"User guide generation failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            content = self._generate_placeholder_user_guide(product_name, features)
            sections = ["Introduction", "Getting Started", "Features", "FAQ"]
            quality_score = 0.5

        return DocResult(
            content=content,
            doc_type=DocType.USER_GUIDE.value,
            title=product_name,
            sections=sections,
            quality_score=quality_score
        )

    async def generate_changelog(
        self,
        version: str,
        changes: List[str],
        date: Optional[str] = None,
        breaking_changes: Optional[List[str]] = None
    ) -> DocResult:
        """生成变更日志

        Args:
            version: 版本号
            changes: 变更列表
            date: 日期
            breaking_changes: 破坏性变更

        Returns:
            DocResult: CHANGELOG条目
        """
        try:
            llm = get_llm()
            system_prompt = """You are a technical writer specializing in changelog documentation.
Follow Keep a Changelog (https://keepachangelog.com/) format."""

            user_prompt = f"""Generate a changelog entry following Keep a Changelog format:

Version: {version}
Date: {date or datetime.now().strftime('%Y-%m-%d')}
Breaking Changes: {', '.join(breaking_changes or ['None'])}
Changes: {', '.join(changes)}

Categories to use:
- Added (new features)
- Changed (changes in existing functionality)
- Deprecated (soon-to-be removed features)
- Removed (removed features)
- Fixed (bug fixes)
- Security (security improvements)
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3
            )

            content = response.content
            sections = ["Added", "Changed", "Fixed", "Security"]
            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"Changelog generation failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            content = self._generate_placeholder_changelog(version, changes)
            sections = ["Added", "Changed", "Fixed"]
            quality_score = 0.5

        return DocResult(
            content=content,
            doc_type=DocType.CHANGELOG.value,
            title=f"Changelog v{version}",
            sections=sections,
            quality_score=quality_score
        )

    async def update_changelog(
        self,
        existing_changelog: str,
        new_version: str,
        changes: List[str]
    ) -> str:
        """更新现有变更日志"""
        try:
            llm = get_llm()
            system_prompt = """You are a technical writer. Given an existing changelog and new changes,
generate an updated changelog following Keep a Changelog format."""

            user_prompt = f"""Update this changelog with new version {new_version}:

Existing Changelog:
{existing_changelog}

New Changes to Add:
{', '.join(changes)}

Return the complete updated changelog.
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )

            return response.content

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"Changelog update failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            return existing_changelog + f"\n\n## {new_version}\n" + "\n".join([f"- {c}" for c in changes])

    def _extract_sections(self, content: str) -> List[str]:
        """提取文档章节"""
        sections = []
        for line in content.split("\n"):
            if line.startswith("#"):
                sections.append(line.replace("#", "").strip())
        return sections

    def _generate_placeholder_readme(
        self,
        project_name: str,
        description: str,
        features: List[str]
    ) -> str:
        """生成占位README"""
        return f"""# {project_name}

{description}

## Features

{chr(10).join([f"- {f}" for f in features])}

## Installation

```bash
pip install {project_name.lower().replace(' ', '-')}
```

## Usage

```python
from {project_name.lower().replace(' ', '_')} import main

main()
```

## License

MIT
"""

    def _generate_placeholder_api_doc(
        self,
        endpoints: List[Dict],
        title: str
    ) -> str:
        """生成占位API文档"""
        lines = [f"# {title}", "", "## Authentication", "", "## Endpoints", ""]

        for ep in endpoints:
            lines.append(f"### {ep['method']} {ep['path']}")
            lines.append(f"**Description:** {ep['description']}")
            lines.append("")

        return "\n".join(lines)

    def _generate_placeholder_user_guide(
        self,
        product_name: str,
        features: List[str]
    ) -> str:
        """生成占位用户指南"""
        return f"""# {product_name} User Guide

## Introduction

Welcome to {product_name}.

## Getting Started

1. Sign up
2. Configure
3. Start using

## Features

{chr(10).join([f"### {f}\nDescription of {f}" for f in features])}

## FAQ

**Q: How do I...?**

**A:** ...
"""

    def _generate_placeholder_changelog(
        self,
        version: str,
        changes: List[str]
    ) -> str:
        """生成占位变更日志"""
        return f"""## [{version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
{chr(10).join([f"- {c}" for c in changes])}
"""

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "doc_types": [d.value for d in DocType],
            "languages": ["en", "zh", "ja"],
            "formats": ["markdown", "html", "pdf"]
        }


# 全局实例
technical_writer = TechnicalWriter()
