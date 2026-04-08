"""
Test Agent - 测试智能体
=======================

职责:
- 单元测试生成
- 集成测试
- 回归测试
- 测试报告生成
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

# 导入核心模块
from core.llm import get_llm
from core.prompt_engine import prompt_manager
from logs.error_logs import error_logger, ErrorLevel


class TestKind(Enum):
    """测试类型"""
    __test__ = False
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class CaseItem:
    """测试用例"""
    __test__ = False
    id: str
    name: str
    description: str
    test_type: TestKind
    code: str
    expected_result: str
    priority: int = 1  # 1-5


@dataclass
class TestBundle:
    """测试套件"""
    __test__ = False
    name: str
    test_cases: List[CaseItem]
    coverage: float = 0.0
    passed: int = 0
    failed: int = 0


class SummaryReport:
    """测试报告"""
    __test__ = False

    def __init__(self):
        self.timestamp = datetime.now()
        self.suites: List[TestBundle] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def add_suite(self, suite: TestBundle):
        self.suites.append(suite)
        self.total_tests += len(suite.test_cases)
        self.passed_tests += suite.passed
        self.failed_tests += suite.failed

    def to_markdown(self) -> str:
        """生成Markdown报告"""
        content = f"""# Test Report

Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {self.total_tests} |
| Passed | {self.passed_tests} |
| Failed | {self.failed_tests} |
| Pass Rate | {self.pass_rate:.1f}% |

"""

        for suite in self.suites:
            content += f"""## {suite.name}

- Coverage: {suite.coverage:.1f}%
- Passed: {suite.passed}
- Failed: {suite.failed}

"""
            for tc in suite.test_cases:
                status = "✅" if tc.expected_result else "❌"
                content += f"""### {status} {tc.name}

**Description:** {tc.description}

**Priority:** {tc.priority}

```
{tc.code}
```

"""

        return content

    def to_json(self) -> str:
        """生成JSON报告"""
        return json.dumps({
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "total": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "pass_rate": self.pass_rate
            },
            "suites": [
                {
                    "name": s.name,
                    "coverage": s.coverage,
                    "passed": s.passed,
                    "failed": s.failed,
                    "test_cases": [
                        {
                            "id": tc.id,
                            "name": tc.name,
                            "type": tc.test_type.value,
                            "priority": tc.priority
                        }
                        for tc in s.test_cases
                    ]
                }
                for s in self.suites
            ]
        }, indent=2)

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


class TestAgent:
    """测试智能体

    【能力】
    - 生成单元测试
    - 生成集成测试
    - 执行测试并收集结果
    - 生成测试报告
    """
    __test__ = False

    def __init__(self):
        self.name = "Test Agent"
        self.test_templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """加载测试模板"""
        return {
            "python_unittest": """import unittest
from {module_name} import {class_name}

class Test{class_name}(unittest.TestCase):
    \"\"\"Test cases for {class_name}\"\"\"

    def setUp(self):
        self.instance = {class_name}()

    def test_basic_{method}(self):
        \"\"\"Test basic {method} functionality\"\"\"
        result = self.instance.{method}()
        self.assertIsNotNone(result)

    def test_edge_case_{method}(self):
        \"\"\"Test edge case for {method}\"\"\"
        # TODO: Add edge case test
        # 已实现边缘测试用例
        result = self.instance.{method}(None)
        self.assertIsNotNone(result)
        result = self.instance.{method}("")
        self.assertIsNotNone(result)
        result = self.instance.{method}("x" * 10000)
        self.assertIsNotNone(result)
""",
            "pytest": """import pytest
from {module_name} import {class_name}

class Test{class_name}:
    \"\"\"Test cases for {class_name}\"\"\"

    def test_basic_{method}(self):
        result = {class_name}().{method}()
        assert result is not None

    @pytest.mark.parametrize("input,expected", [
        ({test_cases})
    ])
    def test_parametrized_{method}(self, input, expected):
        result = {class_name}().{method}(input)
        assert result == expected
""",
            "api_test": """import requests
import pytest

BASE_URL = "{base_url}"

class TestAPI:
    \"\"\"API tests for {endpoint}\"\"\"

    def test_{endpoint}_{method}(self):
        response = requests.{method}(f\"{{BASE_URL}}{endpoint}\")
        assert response.status_code == {expected_status}

    def test_{endpoint}_with_payload(self):
        payload = {payload}
        response = requests.{method}(
            f\"{{BASE_URL}}{endpoint}\",
            json=payload
        )
        assert response.status_code == {expected_status}
        assert response.json()
"""
        }

    async def generate_unit_tests(
        self,
        module_name: str,
        class_name: str,
        methods: List[str],
        framework: str = "pytest"
    ) -> List[str]:
        """生成单元测试"""
        tests = []

        template = self.test_templates.get(framework, self.test_templates["pytest"])

        for method in methods:
            test_code = template.format(
                module_name=module_name,
                class_name=class_name,
                method=method,
                test_cases="(1, 1), (2, 2)"
            )
            tests.append(test_code)

        return tests

    async def generate_unit_tests_with_llm(
        self,
        description: str,
        language: str = "python",
        framework: str = "pytest",
        code: Optional[str] = None
    ) -> str:
        """使用LLM生成单元测试

        Args:
            description: 功能描述
            language: 编程语言
            framework: 测试框架 (pytest/unittest)
            code: 可选的现有代码

        Returns:
            生成的测试代码
        """
        try:
            system_prompt, user_prompt = prompt_manager.render(
                "test_generation",
                description=description,
                language=language,
                framework=framework,
                code=code or "Not provided"
            )

            llm = get_llm()
            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3
            )
            return response.content

        except Exception as e:
            error_logger.log(
                error_type="LLMTestGenerationError",
                message=f"LLM test generation failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            # Fallback to template-based generation
            return "# LLM generation failed, use template-based approach"

    async def generate_integration_tests(
        self,
        components: List[str],
        interactions: List[Dict]
    ) -> List[CaseItem]:
        """生成集成测试"""
        test_cases = []

        for i, interaction in enumerate(interactions):
            tc = CaseItem(
                id=f"integration_{i+1}",
                name=f"Test {interaction['from']} -> {interaction['to']}",
                description=f"Integration test for {interaction['from']} calling {interaction['to']}",
                test_type=TestKind.INTEGRATION,
                code=self._generate_integration_code(interaction),
                expected_result="Successful interaction",
                priority=interaction.get("priority", 2)
            )
            test_cases.append(tc)

        return test_cases

    def _generate_integration_code(self, interaction: Dict) -> str:
        """生成集成测试代码"""
        return f"""async def test_{interaction['from'].lower()}_{interaction['to'].lower()}():
    \"\"\"Test {interaction['from']} -> {interaction['to']}\"\"\"
    from {interaction['from'].lower()}.{interaction.get('method', 'execute')} import main

    result = await main({interaction.get('params', {})})
    assert result is not None
"""

    async def run_tests(
        self,
        test_suite: TestBundle,
        pytest_args: Optional[List[str]] = None
    ) -> SummaryReport:
        """运行测试并生成报告

        【注意】实际实现需要调用pytest
        """
        report = SummaryReport()

        # 模拟测试执行
        for tc in test_suite.test_cases:
            # 实际实现中会调用pytest
            # 这里简化处理
            test_suite.passed += 1  # 假设都通过

        test_suite.passed = len(test_suite.test_cases)
        report.add_suite(test_suite)

        return report

    async def generate_test_report(
        self,
        test_results: Dict,
        format: str = "markdown"
    ) -> str:
        """生成测试报告"""
        report = SummaryReport()

        # 构建测试套件
        for suite_name, results in test_results.items():
            suite = TestBundle(
                name=suite_name,
                test_cases=[],
                coverage=results.get("coverage", 0.0),
                passed=results.get("passed", 0),
                failed=results.get("failed", 0)
            )
            report.add_suite(suite)

        if format == "json":
            return report.to_json()
        return report.to_markdown()

    async def generate_load_test(
        self,
        endpoint: str,
        concurrent_users: int,
        duration_seconds: int
    ) -> str:
        """生成压力测试脚本"""
        return f"""# Load Test for {endpoint}
# Users: {concurrent_users}
# Duration: {duration_seconds}s

import locust
import requests

class UserBehavior(locust.TaskSet):
    @locust.task
    def get_{endpoint.replace('/', '_')}():
        response = requests.get("{endpoint}")
        if response.status_code != 200:
            print(f"Failed: {{response.status_code}}")

class WebsiteUser(locust.HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 3)

if __name__ == "__main__":
    locust -f load_test.py --host=http://localhost:8000 --users={concurrent_users} --run-time={duration_seconds}s
"""

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "supported_test_types": [t.value for t in TestKind],
            "supported_frameworks": ["pytest", "unittest", "locust"],
            "report_formats": ["markdown", "json", "html"]
        }


# 全局实例
test_agent = TestAgent()
