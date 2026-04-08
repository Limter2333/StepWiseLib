"""
Doc Agent - 文档智能体
======================

职责:
- 项目文档撰写
- API文档生成
- 技术方案编写
- 用户手册
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from enum import Enum
import os

# 导入核心模块
from core.llm import get_llm
from core.prompt_engine import prompt_manager
from logs.error_logs import error_logger, ErrorLevel


class DocType(Enum):
    """文档类型"""
    README = "readme"
    API_DOC = "api_doc"
    TECHNICAL_DESIGN = "technical_design"
    USER_GUIDE = "user_guide"
    CHANGELOG = "changelog"
    ARCHITECTURE = "architecture"


class DocAgent:
    """文档智能体

    【能力】
    - 根据代码生成文档
    - 撰写技术方案
    - 生成API文档
    - 维护变更日志
    """

    def __init__(self):
        self.name = "Doc Agent"
        self.output_dir = Path("G:/claude_code_project/docs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_doc_with_llm(
        self,
        doc_type: str,
        project_name: str,
        description: str,
        features: str = "",
        tech_stack: str = "",
        audience: str = "developers"
    ) -> str:
        """使用LLM生成文档

        Args:
            doc_type: 文档类型 (README, API_DOC, TECHNICAL_DESIGN, USER_GUIDE)
            project_name: 项目名称
            description: 项目描述
            features: 关键特性
            tech_stack: 技术栈
            audience: 目标受众

        Returns:
            生成的文档内容
        """
        try:
            system_prompt, user_prompt = prompt_manager.render(
                "doc_generation",
                doc_type=doc_type,
                project_name=project_name,
                description=description,
                features=features,
                tech_stack=tech_stack,
                audience=audience
            )

            llm = get_llm()
            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )
            return response.content

        except Exception as e:
            error_logger.log(
                error_type="LLMDocGenerationError",
                message=f"LLM doc generation failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            return "# LLM generation failed, use template-based approach"

    async def generate_readme(
        self,
        project_name: str,
        description: str,
        features: List[str],
        installation: str = "",
        usage: str = "",
        tech_stack: Optional[List[str]] = None
    ) -> str:
        """生成README.md"""
        content = f"""# {project_name}

{description}

## Features

"""
        for feature in features:
            content += f"- {feature}\n"

        if tech_stack:
            content += f"""
## Tech Stack

"""
            for tech in tech_stack:
                content += f"- {tech}\n"

        if installation:
            content += f"""
## Installation

{installation}
"""

        if usage:
            content += f"""
## Usage

{usage}
"""

        content += """
## License

MIT
"""
        return content

    async def generate_api_doc(
        self,
        endpoints: List[Dict],
        title: str = "API Documentation"
    ) -> str:
        """生成API文档"""
        content = f"""# {title}

## Endpoints

"""
        for ep in endpoints:
            content += f"""### {ep.get('method', 'GET')} {ep.get('path', '/')}

**Description:** {ep.get('description', 'No description')}

"""
            if ep.get('parameters'):
                content += "**Parameters:**\n"
                for param in ep['parameters']:
                    content += f"- `{param['name']}` ({param.get('type', 'string')}): {param.get('description', '')}\n"
                content += "\n"

            if ep.get('request_body'):
                content += f"""**Request Body:**
```json
{ep.get('request_body')}
```

"""

            if ep.get('responses'):
                content += "**Responses:**\n"
                for code, resp in ep['responses'].items():
                    content += f"- `{code}`: {resp}\n"
                content += "\n"

        return content

    async def generate_technical_design(
        self,
        project_name: str,
        overview: str,
        architecture: str,
        components: List[Dict],
        data_flow: str = "",
        security: str = ""
    ) -> str:
        """生成技术方案文档"""
        content = f"""# Technical Design - {project_name}

## Overview

{overview}

## Architecture

{architecture}

## Components

"""
        for comp in components:
            content += f"""### {comp.get('name', 'Component')}

**Description:** {comp.get('description', '')}

**Responsibilities:**
"""
            for resp in comp.get('responsibilities', []):
                content += f"- {resp}\n"

            if comp.get('dependencies'):
                content += f"\n**Dependencies:** {', '.join(comp['dependencies'])}\n"

            content += "\n"

        if data_flow:
            content += f"""## Data Flow

{data_flow}

"""

        if security:
            content += f"""## Security

{security}

"""

        return content

    async def generate_user_guide(
        self,
        product_name: str,
        getting_started: str,
        tutorials: List[Dict],
        faq: List[Dict] = None
    ) -> str:
        """生成用户手册"""
        content = f"""# {product_name} - User Guide

## Getting Started

{getting_started}

## Tutorials

"""
        for i, tutorial in enumerate(tutorials, 1):
            content += f"""### {i}. {tutorial.get('title', f'Tutorial {i}')}

{tutorial.get('description', '')}

```
{tutorial.get('commands', '')}
```

"""

        if faq:
            content += """## FAQ

"""
            for q in faq:
                content += f"""### {q.get('question', '')}

{q.get('answer', '')}

"""

        return content

    async def save_document(
        self,
        content: str,
        filename: str,
        doc_type: DocType = DocType.README
    ) -> str:
        """保存文档到文件"""
        file_path = self.output_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(file_path)

    async def update_changelog(
        self,
        version: str,
        changes: List[str],
        date: Optional[str] = None
    ) -> str:
        """生成或更新CHANGELOG"""
        changelog_path = self.output_dir / "CHANGELOG.md"

        # 读取现有内容
        existing = ""
        if changelog_path.exists():
            with open(changelog_path, 'r', encoding='utf-8') as f:
                existing = f.read()

        # 构建新条目
        new_entry = f"""## [{version}] - {date or datetime.now().strftime('%Y-%m-%d')}

"""
        for change in changes:
            new_entry += f"- {change}\n"
        new_entry += "\n"

        # 插入到现有内容后面
        if "# Changelog" in existing:
            content = existing.replace("# Changelog", "# Changelog\n" + new_entry)
        else:
            content = f"# Changelog\n\n{new_entry}\n{existing}"

        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(changelog_path)

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "document_types": [dt.value for dt in DocType],
            "output_formats": ["markdown", "html", "pdf"],
            "languages": ["en", "zh"]
        }


# 全局实例
doc_agent = DocAgent()
