"""
Backend Architect Agent Tests
"""

import pytest
from agents.backend_architect.backend_architect import (
    BackendArchitect,
    ArchitecturePattern,
    DatabaseType,
    ArchitectureTask,
    ArchitectureResult
)


class TestArchitecturePattern:
    """测试架构模式枚举"""

    def test_pattern_values(self):
        assert ArchitecturePattern.MONOLITHIC.value == "monolithic"
        assert ArchitecturePattern.MICROSERVICE.value == "microservice"
        assert ArchitecturePattern.SERVERLESS.value == "serverless"
        assert ArchitecturePattern.EVENT_DRIVEN.value == "event_driven"
        assert ArchitecturePattern.LAYERED.value == "layered"
        assert ArchitecturePattern.CQRS.value == "cqrs"

    def test_pattern_count(self):
        assert len(ArchitecturePattern) == 6


class TestDatabaseType:
    """测试数据库类型枚举"""

    def test_db_type_values(self):
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.MYSQL.value == "mysql"
        assert DatabaseType.MONGODB.value == "mongodb"
        assert DatabaseType.REDIS.value == "redis"
        assert DatabaseType.MILVUS.value == "milvus"
        assert DatabaseType.CHROMADB.value == "chromadb"

    def test_db_type_count(self):
        assert len(DatabaseType) == 6


class TestArchitectureTask:
    """测试架构任务数据类"""

    def test_task_creation(self):
        task = ArchitectureTask(
            id="arch_1",
            task_type="system_design",
            description="Design a scalable API system"
        )

        assert task.id == "arch_1"
        assert task.task_type == "system_design"
        assert task.description == "Design a scalable API system"
        assert task.scale == "medium"  # default
        assert task.created_at is not None

    def test_task_with_requirements(self):
        task = ArchitectureTask(
            id="arch_2",
            task_type="db_design",
            description="Design database schema",
            requirements=["ACID compliance", "Horizontal scaling"],
            constraints=["Max 100GB storage"]
        )

        assert len(task.requirements) == 2
        assert len(task.constraints) == 1
        assert "ACID compliance" in task.requirements

    def test_task_default_scale(self):
        task = ArchitectureTask(
            id="arch_3",
            task_type="api_design",
            description="API design"
        )

        assert task.scale == "medium"


class TestArchitectureResult:
    """测试架构设计结果数据类"""

    def test_result_creation(self):
        result = ArchitectureResult(
            architecture_diagram="+---+\n|API|\n+---+",
            components=[{"name": "API Gateway", "type": "gateway"}]
        )

        assert result.architecture_diagram is not None
        assert len(result.components) == 1
        assert result.estimated_complexity == "medium"  # default

    def test_result_with_full_data(self):
        result = ArchitectureResult(
            architecture_diagram="diagram",
            components=[{"name": "Auth"}],
            database_schema="CREATE TABLE users...",
            api_spec="GET /users",
            tech_stack=["Python", "PostgreSQL"],
            estimated_complexity="high",
            recommendations=["Use caching"],
            quality_score=85.5
        )

        assert result.database_schema is not None
        assert result.api_spec is not None
        assert len(result.tech_stack) == 2
        assert result.quality_score == 85.5


class TestBackendArchitect:
    """测试后端架构智能体"""

    def test_agent_creation(self):
        agent = BackendArchitect()
        assert agent.name == "Backend Architect"

    def test_global_instance_exists(self):
        from agents.backend_architect import backend_architect
        assert backend_architect.name == "Backend Architect"

    def test_get_capabilities(self):
        agent = BackendArchitect()
        caps = agent.get_capabilities()

        assert caps["name"] == "Backend Architect"
        assert "system_design" in caps["task_types"]
        assert "db_design" in caps["task_types"]
        assert "api_design" in caps["task_types"]
        assert len(caps["architecture_patterns"]) > 0
        assert len(caps["database_types"]) > 0


class TestArchitectTaskScale:
    """测试架构任务规模选项"""

    def test_scale_options(self):
        task_small = ArchitectureTask(
            id="s1", task_type="api", description="d", scale="small"
        )
        task_medium = ArchitectureTask(
            id="s2", task_type="api", description="d", scale="medium"
        )
        task_large = ArchitectureTask(
            id="s3", task_type="api", description="d", scale="large"
        )

        assert task_small.scale == "small"
        assert task_medium.scale == "medium"
        assert task_large.scale == "large"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
