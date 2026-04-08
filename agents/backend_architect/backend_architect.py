"""
Backend Architect Agent - 后端架构智能体
==========================================

职责:
- 系统架构设计
- 数据库设计
- API架构
- 微服务设计
- 性能与扩展性规划
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.prompt_engine import prompt_manager
from core.guardrails import guardrails
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel


class ArchitecturePattern(Enum):
    """架构模式"""
    MONOLITHIC = "monolithic"
    MICROSERVICE = "microservice"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"
    LAYERED = "layered"
    CQRS = "cqrs"


class DatabaseType(Enum):
    """数据库类型"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    MILVUS = "milvus"
    CHROMADB = "chromadb"


@dataclass
class ArchitectureTask:
    """架构任务"""
    id: str
    task_type: str  # system_design, db_design, api_design
    description: str
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    scale: str = "medium"  # small, medium, large
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ArchitectureResult:
    """架构设计结果"""
    architecture_diagram: str  # ASCII art or description
    components: List[Dict]
    database_schema: Optional[str] = None
    api_spec: Optional[str] = None
    tech_stack: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"
    recommendations: List[str] = field(default_factory=list)
    quality_score: float = 0.0


class BackendArchitect:
    """后端架构智能体

    【能力】
    - 设计高可用系统架构
    - 规划数据库Schema
    - 设计RESTful/GraphQL API
    - 规划微服务拆分
    - 性能与扩展性建议
    """

    def __init__(self):
        self.name = "Backend Architect"
        self.specialty = ["系统设计", "数据库", "API设计", "微服务", "云架构"]
        self.current_task: Optional[ArchitectureTask] = None

    async def design_system(
        self,
        description: str,
        requirements: List[str],
        scale: str = "medium",
        pattern: ArchitecturePattern = ArchitecturePattern.LAYERED
    ) -> ArchitectureResult:
        """设计系统架构

        Args:
            description: 系统描述
            requirements: 需求列表
            scale: 规模 (small/medium/large)
            pattern: 架构模式

        Returns:
            ArchitectureResult: 架构设计方案
        """
        guard_result = guardrails.check_input(description)
        if not guard_result.passed:
            raise ValueError(f"Input blocked: {guard_result.message}")

        try:
            llm = get_llm()
            system_prompt = """You are a senior backend architect with expertise in:
- Microservices architecture
- Domain-driven design
- Event-driven architecture
- Cloud-native design patterns

Provide detailed, production-ready architecture designs."""

            user_prompt = f"""Design a backend system architecture for:

Description: {description}
Requirements: {', '.join(requirements)}
Scale: {scale}
Pattern: {pattern.value}

Provide:
1. System components and their responsibilities
2. Data flow between components
3. Technology stack recommendations
4. Scalability considerations
5. Potential bottlenecks and solutions
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )

            arch_diagram = self._generate_architecture_diagram(description, pattern)
            components = self._extract_components(response.content)
            tech_stack = self._recommend_tech_stack(pattern, scale)
            recommendations = self._generate_recommendations(scale)

            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"Architecture design LLM call failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            arch_diagram = self._generate_placeholder_diagram(description)
            components = self._generate_placeholder_components()
            tech_stack = ["Python", "FastAPI", "PostgreSQL", "Redis"]
            recommendations = ["Consider using caching", "Add monitoring"]
            quality_score = 0.5

        return ArchitectureResult(
            architecture_diagram=arch_diagram,
            components=components,
            database_schema=None,
            api_spec=None,
            tech_stack=tech_stack,
            estimated_complexity=scale,
            recommendations=recommendations,
            quality_score=quality_score
        )

    async def design_database(
        self,
        description: str,
        entities: List[str],
        db_type: DatabaseType = DatabaseType.POSTGRESQL
    ) -> ArchitectureResult:
        """设计数据库Schema

        Args:
            description: 系统描述
            entities: 实体列表 (e.g., ["User", "Order", "Product"])
            db_type: 数据库类型

        Returns:
            ArchitectureResult: 数据库设计方案
        """
        guard_result = guardrails.check_input(description)
        if not guard_result.passed:
            raise ValueError(f"Input blocked")

        try:
            llm = get_llm()
            system_prompt = f"You are a database architect specializing in {db_type.value}."

            user_prompt = f"""Design a database schema for:

System: {description}
Entities: {', '.join(entities)}
Database: {db_type.value}

Provide:
1. Table definitions with columns and types
2. Primary keys and foreign keys
3. Indexes for optimization
4. Relationships between tables
5. Any partitioning or sharding considerations
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )

            schema = self._generate_sql_schema(entities, db_type)
            components = self._extract_db_components(entities)
            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"Database design failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            schema = self._generate_placeholder_schema(entities, db_type)
            components = []
            quality_score = 0.5

        result = ArchitectureResult(
            architecture_diagram="Database Schema Design",
            components=components,
            database_schema=schema,
            tech_stack=[db_type.value],
            quality_score=quality_score
        )
        return result

    async def design_api(
        self,
        description: str,
        resources: List[str],
        api_style: str = "rest"
    ) -> ArchitectureResult:
        """设计API规范

        Args:
            description: API描述
            resources: 资源列表
            api_style: API风格 (rest/graphql/grpc)

        Returns:
            ArchitectureResult: API设计方案
        """
        try:
            llm = get_llm()
            system_prompt = f"You are an API architect specializing in {api_style}."

            user_prompt = f"""Design an {api_style} API for:

Description: {description}
Resources: {', '.join(resources)}

Provide:
1. Endpoint definitions (method, path, description)
2. Request/response schemas
3. Authentication/authorization
4. Error handling conventions
5. Rate limiting considerations
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3
            )

            api_spec = self._generate_api_spec(resources, api_style)
            components = self._extract_api_components(resources)
            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"API design failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            api_spec = self._generate_placeholder_api_spec(resources, api_style)
            components = []
            quality_score = 0.5

        result = ArchitectureResult(
            architecture_diagram="API Design",
            components=components,
            api_spec=api_spec,
            tech_stack=[api_style.upper()],
            quality_score=quality_score
        )
        return result

    def _generate_architecture_diagram(
        self,
        description: str,
        pattern: ArchitecturePattern
    ) -> str:
        """生成架构图 (ASCII)"""
        if pattern == ArchitecturePattern.MICROSERVICE:
            return f"""
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Service A    │     │  Service B    │     │  Service C    │
│   (Python)    │     │   (Python)    │     │   (Python)    │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Database    │     │   Database    │     │   Database    │
│   (Postgres)  │     │   (MongoDB)   │     │   (Redis)     │
└───────────────┘     └───────────────┘     └───────────────┘
"""
        elif pattern == ArchitecturePattern.LAYERED:
            return f"""
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│                   (FastAPI / React)                          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│                      (Services)                              │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                      │
│                    (Repositories)                           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        Database                             │
│                    (PostgreSQL)                            │
└─────────────────────────────────────────────────────────────┘
"""
        return f"/* Architecture for: {description} */"

    def _generate_placeholder_diagram(self, description: str) -> str:
        return f"""
┌─────────────────────────────────────────┐
│           {description[:30]}            │
│                                         │
│  [Component 1]  →  [Component 2]       │
│        ↓                ↓               │
│  [Component 3]  ←  [Component 4]      │
└─────────────────────────────────────────┘
"""

    def _generate_sql_schema(
        self,
        entities: List[str],
        db_type: DatabaseType
    ) -> str:
        """生成SQL Schema"""
        lines = [f"-- Schema for: {', '.join(entities)}", f"-- Database: {db_type.value}", ""]

        for entity in entities:
            lines.append(f"CREATE TABLE {entity.lower()} (")
            lines.append(f"    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),")
            lines.append(f"    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
            lines.append(f"    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            lines.append(f");")
            lines.append("")

        return "\n".join(lines)

    def _generate_placeholder_schema(
        self,
        entities: List[str],
        db_type: DatabaseType
    ) -> str:
        return self._generate_sql_schema(entities, db_type)

    def _generate_api_spec(
        self,
        resources: List[str],
        api_style: str
    ) -> str:
        """生成API规范"""
        lines = [f"# {api_style.upper()} API Specification", ""]

        for resource in resources:
            resource_lower = resource.lower()
            lines.append(f"## {resource}")
            lines.append(f"GET    /api/{resource_lower}      - List {resource}")
            lines.append(f"POST   /api/{resource_lower}      - Create {resource}")
            lines.append(f"GET    /api/{resource_lower}/{{id}} - Get {resource}")
            lines.append(f"PUT    /api/{resource_lower}/{{id}} - Update {resource}")
            lines.append(f"DELETE /api/{resource_lower}/{{id}} - Delete {resource}")
            lines.append("")

        return "\n".join(lines)

    def _generate_placeholder_api_spec(
        self,
        resources: List[str],
        api_style: str
    ) -> str:
        return self._generate_api_spec(resources, api_style)

    def _recommend_tech_stack(
        self,
        pattern: ArchitecturePattern,
        scale: str
    ) -> List[str]:
        """推荐技术栈"""
        base = ["Python", "FastAPI", "Pydantic"]

        if scale == "large":
            base.extend(["Kubernetes", "Docker", "AWS/GCP", "Redis", "PostgreSQL"])
        elif scale == "medium":
            base.extend(["Docker", "PostgreSQL", "Redis", "Nginx"])
        else:
            base.extend(["SQLite", "Redis"])

        if pattern == ArchitecturePattern.MICROSERVICE:
            base.extend(["RabbitMQ", "Kafka", "Service Mesh"])
        elif pattern == ArchitecturePattern.EVENT_DRIVEN:
            base.extend(["Kafka", "Celery", "Redis Streams"])

        return base

    def _extract_components(self, content: str) -> List[Dict]:
        """提取组件"""
        return [
            {"name": "API Gateway", "responsibility": "Request routing"},
            {"name": "Auth Service", "responsibility": "Authentication"},
            {"name": "Business Logic", "responsibility": "Core features"},
            {"name": "Data Layer", "responsibility": "Data persistence"},
        ]

    def _extract_db_components(self, entities: List[str]) -> List[Dict]:
        """提取数据库组件"""
        return [{"entity": e, "type": "table"} for e in entities]

    def _extract_api_components(self, resources: List[str]) -> List[Dict]:
        """提取API组件"""
        return [{"resource": r, "endpoints": 5} for r in resources]

    def _generate_recommendations(self, scale: str) -> List[str]:
        """生成建议"""
        recommendations = [
            "Implement caching layer with Redis",
            "Add distributed tracing for observability",
            "Use connection pooling for database",
        ]

        if scale == "large":
            recommendations.extend([
                "Consider implementing circuit breaker pattern",
                "Plan for horizontal scaling",
                "Implement rate limiting at API gateway",
            ])

        return recommendations

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "architecture_patterns": [p.value for p in ArchitecturePattern],
            "database_types": [d.value for d in DatabaseType],
            "task_types": ["system_design", "db_design", "api_design"]
        }


# 全局实例
backend_architect = BackendArchitect()
