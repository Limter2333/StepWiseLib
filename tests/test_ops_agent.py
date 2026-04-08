"""
Ops Agent 测试
==============

测试运维智能体功能
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ops_agent.ops_agent import (
    OpsAgent,
    ops_agent,
    DeploymentStatus,
    Environment,
    Deployment,
    ServiceHealth
)


class TestOpsAgent:
    """Ops Agent测试"""

    def test_ops_agent_initialization(self):
        """测试Ops Agent初始化"""
        agent = OpsAgent()
        assert agent.name == "Ops Agent"
        assert "Docker" in agent.specialty
        assert "Kubernetes" in agent.specialty

    def test_get_capabilities(self):
        """测试获取Agent能力"""
        caps = ops_agent.get_capabilities()
        assert caps["name"] == "Ops Agent"
        assert caps["type"] == "ops"
        assert "deploy_application" in caps["capabilities"]
        assert "rollback_deployment" in caps["capabilities"]
        assert "check_health" in caps["capabilities"]
        assert "analyze_logs" in caps["capabilities"]
        assert "production" in caps["supported_environments"]
        assert "blue_green" in caps["supported_deployment_types"]

    @pytest.mark.asyncio
    async def test_deploy_to_development(self):
        """测试部署到开发环境"""
        result = await ops_agent.deploy(
            environment="development",
            version="v1.0.0"
        )
        assert result["success"] is True
        assert "deployment_id" in result
        assert result["status"] == "success"
        assert len(result["logs"]) > 0

    @pytest.mark.asyncio
    async def test_deploy_to_staging(self):
        """测试部署到预发布环境"""
        result = await ops_agent.deploy(
            environment="staging",
            version="v1.1.0",
            deployment_type="rolling"
        )
        assert result["success"] is True
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_deploy_to_production(self):
        """测试部署到生产环境"""
        result = await ops_agent.deploy(
            environment="production",
            version="v1.2.0",
            deployment_type="blue_green"
        )
        assert result["success"] is True
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_deployment_history(self):
        """测试获取部署历史"""
        # 先创建一些部署
        await ops_agent.deploy(environment="development", version="v1.0.0")
        await ops_agent.deploy(environment="staging", version="v1.1.0")

        history = ops_agent.get_deployment_history(limit=5)
        assert len(history) >= 2
        assert "id" in history[0]
        assert "environment" in history[0]
        assert "version" in history[0]
        assert "status" in history[0]

    @pytest.mark.asyncio
    async def test_rollback(self):
        """测试回滚"""
        # 先创建部署
        deploy_result = await ops_agent.deploy(
            environment="development",
            version="v1.0.0"
        )
        deployment_id = deploy_result["deployment_id"]

        # 回滚
        rollback_result = await ops_agent.rollback(deployment_id)
        assert rollback_result["success"] is True
        assert rollback_result["rolled_back_version"] == "v1.0.0"

    @pytest.mark.asyncio
    async def test_rollback_nonexistent(self):
        """测试回滚不存在的部署"""
        result = await ops_agent.rollback("nonexistent_deploy_123")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_check_health(self):
        """测试健康检查"""
        health = await ops_agent.check_health("api-service")
        assert health.service_name == "api-service"
        assert health.status in ["healthy", "degraded", "down"]
        assert health.uptime_seconds >= 0
        assert health.response_time_ms >= 0
        assert health.error_rate >= 0

    @pytest.mark.asyncio
    async def test_analyze_logs_no_errors(self):
        """测试分析正常日志"""
        log_content = """
        [INFO] Application started
        [INFO] Database connected
        [INFO] Server listening on port 8080
        [INFO] Health check passed
        """
        result = await ops_agent.analyze_logs(log_content, time_range="1h")

        assert result["summary"]["errors"] == 0
        assert result["time_range"] == "1h"
        assert any("System running normally" in r for r in result["recommendations"])

    @pytest.mark.asyncio
    async def test_analyze_logs_with_errors(self):
        """测试分析错误日志"""
        log_content = """
        [INFO] Application started
        [ERROR] Database connection failed
        [ERROR] Retry attempt 1 failed
        [WARNING] Memory usage high
        [ERROR] Request timeout
        """
        result = await ops_agent.analyze_logs(log_content, time_range="1h")

        assert result["summary"]["errors"] == 3
        assert result["summary"]["warnings"] == 1
        assert len(result["error_patterns"]) == 3
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_logs_high_error_rate(self):
        """测试高错误率日志分析"""
        log_content = """
        [ERROR] Error 1
        [ERROR] Error 2
        [ERROR] Error 3
        [ERROR] Error 4
        [ERROR] Error 5
        [ERROR] Error 6
        [ERROR] Error 7
        [ERROR] Error 8
        [ERROR] Error 9
        [ERROR] Error 10
        [ERROR] Error 11
        """
        result = await ops_agent.analyze_logs(log_content)

        assert result["summary"]["errors"] == 11
        assert any("High error rate detected" in r for r in result["recommendations"])

    @pytest.mark.asyncio
    async def test_deployment_status_tracking(self):
        """测试部署状态追踪"""
        # 初始部署
        result1 = await ops_agent.deploy(environment="staging", version="v1.0.0")
        assert result1["status"] == "success"

        # 部署历史
        history = ops_agent.get_deployment_history()
        statuses = [h["status"] for h in history]

        # 验证至少有成功的部署
        assert "success" in statuses

    def test_environment_enum(self):
        """测试环境枚举"""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"

    def test_deployment_status_enum(self):
        """测试部署状态枚举"""
        assert DeploymentStatus.PENDING.value == "pending"
        assert DeploymentStatus.IN_PROGRESS.value == "in_progress"
        assert DeploymentStatus.SUCCESS.value == "success"
        assert DeploymentStatus.FAILED.value == "failed"
        assert DeploymentStatus.ROLLED_BACK.value == "rolled_back"

    def test_deployment_creation(self):
        """测试部署对象创建"""
        deployment = Deployment(
            id="test_deploy_1",
            environment=Environment.DEVELOPMENT,
            version="v1.0.0"
        )
        assert deployment.id == "test_deploy_1"
        assert deployment.environment == Environment.DEVELOPMENT
        assert deployment.version == "v1.0.0"
        assert deployment.status == DeploymentStatus.PENDING
        assert deployment.created_at is not None

    def test_service_health_creation(self):
        """测试服务健康对象创建"""
        health = ServiceHealth(
            service_name="test-service",
            status="healthy",
            uptime_seconds=3600.0,
            last_check=datetime.now(),
            response_time_ms=50.0,
            error_rate=0.01
        )
        assert health.service_name == "test-service"
        assert health.status == "healthy"
        assert health.uptime_seconds == 3600.0
        assert health.response_time_ms == 50.0
        assert health.error_rate == 0.01


class TestOpsAgentRecommendations:
    """Ops Agent建议生成测试"""

    def test_recommendations_no_issues(self):
        """测试无问题时的建议"""
        agent = OpsAgent()
        recs = agent._generate_recommendations(0, 0)
        assert any("System running normally" in r for r in recs)

    def test_recommendations_some_errors(self):
        """测试一些错误时的建议"""
        agent = OpsAgent()
        recs = agent._generate_recommendations(5, 0)
        assert any("Some errors detected" in r for r in recs)

    def test_recommendations_high_errors(self):
        """测试高错误率时的建议"""
        agent = OpsAgent()
        recs = agent._generate_recommendations(15, 0)
        assert any("High error rate detected" in r for r in recs)

    def test_recommendations_high_warnings(self):
        """测试高警告数时的建议"""
        agent = OpsAgent()
        recs = agent._generate_recommendations(0, 60)
        assert any("High warning count" in r for r in recs)


class TestOpsAgentEdgeCases:
    """Ops Agent边界情况测试"""

    def test_deployment_multiple_types(self):
        """测试不同部署类型"""
        agent = OpsAgent()

        # blue_green部署
        result1 = asyncio.run(agent.deploy("development", "v1.0.0", "blue_green"))
        assert result1["success"] is True

        # canary部署
        result2 = asyncio.run(agent.deploy("staging", "v1.1.0", "canary"))
        assert result2["success"] is True

        # rolling部署
        result3 = asyncio.run(agent.deploy("production", "v1.2.0", "rolling"))
        assert result3["success"] is True

    def test_deployment_invalid_environment(self):
        """测试无效环境"""
        agent = OpsAgent()

        with pytest.raises(ValueError):
            asyncio.run(agent.deploy("invalid_env", "v1.0.0"))

    def test_deployment_history_limit(self):
        """测试部署历史限制"""
        agent = OpsAgent()

        # 创建多个部署
        for i in range(12):
            asyncio.run(agent.deploy("development", f"v1.{i}.0"))

        # 测试limit参数
        history = agent.get_deployment_history(limit=5)
        assert len(history) == 5

        # 测试不带limit参数（默认limit=10）
        history_all = agent.get_deployment_history()
        assert len(history_all) == 10

    def test_rollback_already_rolled_back(self):
        """测试回滚已回滚的部署"""
        agent = OpsAgent()

        # 创建并回滚部署
        result = asyncio.run(agent.deploy("development", "v1.0.0"))
        deploy_id = result["deployment_id"]
        asyncio.run(agent.rollback(deploy_id))

        # 再次回滚应该失败
        result2 = asyncio.run(agent.rollback(deploy_id))
        assert result2["success"] is False

    def test_analyze_logs_empty_content(self):
        """测试分析空日志"""
        agent = OpsAgent()
        result = asyncio.run(agent.analyze_logs(""))
        assert result["summary"]["errors"] == 0
        assert result["summary"]["warnings"] == 0
        assert result["summary"]["info"] == 0

    def test_analyze_logs_only_errors(self):
        """测试只有错误的日志"""
        agent = OpsAgent()
        log_content = "[ERROR]\n" * 100
        result = asyncio.run(agent.analyze_logs(log_content))
        assert result["summary"]["errors"] == 100
        assert any("High error rate detected" in r for r in result["recommendations"])

    def test_analyze_logs_only_warnings(self):
        """测试只有警告的日志"""
        agent = OpsAgent()
        log_content = "[WARNING]\n" * 60
        result = asyncio.run(agent.analyze_logs(log_content))
        assert result["summary"]["warnings"] == 60
        assert any("High warning count" in r for r in result["recommendations"])

    def test_analyze_logs_very_long(self):
        """测试分析超长日志"""
        agent = OpsAgent()
        log_content = "[INFO] Line\n" * 10000
        result = asyncio.run(agent.analyze_logs(log_content))
        assert result["summary"]["info"] == 10000

    def test_analyze_logs_mixed_case(self):
        """测试大小写混合的日志"""
        agent = OpsAgent()
        log_content = "[error] lowercase error\n[ERROR] uppercase error\n[Error] mixed case"
        result = asyncio.run(agent.analyze_logs(log_content))
        # 只有大写的ERROR被计数
        assert result["summary"]["errors"] == 1

    def test_analyze_logs_custom_time_range(self):
        """测试自定义时间范围"""
        agent = OpsAgent()
        result = asyncio.run(agent.analyze_logs("[INFO] test", time_range="24h"))
        assert result["time_range"] == "24h"

    def test_check_health_different_services(self):
        """测试不同服务的健康检查"""
        agent = OpsAgent()

        services = ["api-gateway", "auth-service", "user-service", "payment-service"]
        for service in services:
            health = asyncio.run(agent.check_health(service))
            assert health.service_name == service
            assert health.status in ["healthy", "degraded", "down"]

    def test_deployment_artifacts(self):
        """测试部署产物记录"""
        agent = OpsAgent()
        result = asyncio.run(agent.deploy("development", "v1.0.0"))

        # 查找部署记录
        deployment_id = result["deployment_id"]
        for d in agent.deployments:
            if d.id == deployment_id:
                assert d.artifacts is not None
                assert isinstance(d.artifacts, dict)
                break

    def test_deployment_logs_content(self):
        """测试部署日志内容"""
        agent = OpsAgent()
        result = asyncio.run(agent.deploy("staging", "v1.0.0", "rolling"))

        assert len(result["logs"]) > 0
        assert any("deployment" in log.lower() for log in result["logs"])
        assert any("version" in log.lower() for log in result["logs"])

    def test_service_health_attributes(self):
        """测试服务健康状态的所有属性"""
        health = ServiceHealth(
            service_name="test-service",
            status="degraded",
            uptime_seconds=7200.0,
            last_check=datetime.now(),
            response_time_ms=200.0,
            error_rate=0.05
        )

        assert health.service_name == "test-service"
        assert health.status == "degraded"
        assert health.uptime_seconds == 7200.0
        assert health.last_check is not None
        assert health.response_time_ms == 200.0
        assert health.error_rate == 0.05

    def test_deployment_with_artifacts(self):
        """测试带产物的部署"""
        deployment = Deployment(
            id="deploy_with_artifacts",
            environment=Environment.STAGING,
            version="v2.0.0",
            artifacts={
                "image": "myapp:v2.0.0",
                "config": "staging.yaml",
                "manifest": "k8s-manifest.yaml"
            }
        )

        assert len(deployment.artifacts) == 3
        assert deployment.artifacts["image"] == "myapp:v2.0.0"

    def test_deployment_with_logs(self):
        """测试带日志的部署"""
        deployment = Deployment(
            id="deploy_with_logs",
            environment=Environment.PRODUCTION,
            version="v1.5.0",
            logs=["Step 1: Preparing", "Step 2: Executing", "Step 3: Verifying"]
        )

        assert len(deployment.logs) == 3
        assert deployment.logs[0] == "Step 1: Preparing"

    def test_deployment_status_transitions(self):
        """测试部署状态转换"""
        deployment = Deployment(
            id="status_test",
            environment=Environment.DEVELOPMENT,
            version="v1.0.0"
        )

        # 初始状态
        assert deployment.status == DeploymentStatus.PENDING

        # 转换到进行中
        deployment.status = DeploymentStatus.IN_PROGRESS
        assert deployment.status == DeploymentStatus.IN_PROGRESS

        # 转换到成功
        deployment.status = DeploymentStatus.SUCCESS
        deployment.completed_at = datetime.now()
        assert deployment.status == DeploymentStatus.SUCCESS
        assert deployment.completed_at is not None

    def test_capabilities_specialty_list(self):
        """测试能力列表包含所有专业领域"""
        agent = OpsAgent()
        caps = agent.get_capabilities()

        expected_specialties = ["Docker", "Kubernetes", "CI/CD", "Linux", "Nginx", "Prometheus", "Grafana"]
        for specialty in expected_specialties:
            assert specialty in caps["specialty"]

    def test_capabilities_deployment_types(self):
        """测试支持的部署类型"""
        agent = OpsAgent()
        caps = agent.get_capabilities()

        assert "blue_green" in caps["supported_deployment_types"]
        assert "rolling" in caps["supported_deployment_types"]
        assert "canary" in caps["supported_deployment_types"]

    def test_all_environments_in_capabilities(self):
        """测试所有环境都在能力列表中"""
        agent = OpsAgent()
        caps = agent.get_capabilities()

        envs = caps["supported_environments"]
        assert "development" in envs
        assert "staging" in envs
        assert "production" in envs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
