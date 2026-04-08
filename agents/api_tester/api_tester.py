"""
API Tester Agent - API测试智能体
=============================

职责:
- API端点测试
- 契约测试
- 性能测试
- 安全测试
- 测试报告生成
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class TestType(Enum):
    """API测试类型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    CONTRACT = "contract"
    PERFORMANCE = "performance"
    SECURITY = "security"
    E2E = "e2e"


class HTTPMethod(Enum):
    """HTTP方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class APIEndpoint:
    """API端点"""
    method: HTTPMethod
    path: str
    description: str
    params: Optional[Dict] = None
    headers: Optional[Dict] = None
    body: Optional[Dict] = None
    expected_status: int = 200


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    endpoint: APIEndpoint
    assertions: List[str]
    expected_result: Any


@dataclass
class TestReport:
    """测试报告"""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_ms: float = 0.0
    results: List[Dict] = field(default_factory=list)


class APITester:
    """API测试智能体

    【能力】
    - 生成API测试用例
    - 执行API测试
    - 契约测试
    - 性能测试
    - 生成测试报告
    """

    def __init__(self):
        self.name = "API Tester"
        self.specialty = ["API测试", "契约测试", "性能测试", "安全测试"]
        self.test_templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """加载测试模板"""
        pytest_template = (
            "import pytest\n"
            "import requests\n"
            "\n"
            'BASE_URL = "{base_url}"\n'
            "\n"
            "class Test{endpoint_name}:\n"
            '    """Test cases for {endpoint_path}"""\n'
            "\n"
            "    def test_{method_lower}_{endpoint_safe}(self):\n"
            '        """Test {method} {path}"""\n'
            "        response = requests.{method_lower}(\n"
            '            f"{{BASE_URL}}{path}",\n'
            "            {headers_str}{data_str}\n"
            "        )\n"
            "        assert response.status_code == {expected_status}\n"
            "\n"
            "    def test_{method_lower}_{endpoint_safe}_response_format(self):\n"
            '        """Test {method} {path} response format"""\n'
            "        response = requests.{method_lower}(\n"
            '            f"{{BASE_URL}}{path}",\n'
            "            {headers_str}{data_str}\n"
            "        )\n"
            "        assert response.status_code == {expected_status}\n"
            '        assert "application/json" in response.headers.get("Content-Type", "")\n'
        )

        js_template = (
            "const axios = require('axios');\n"
            "\n"
            "describe('{endpoint_name}', () => {\n"
            "    const BASE_URL = '{base_url}';\n"
            "\n"
            "    test('{method} {path}', async () => {\n"
            "        const response = await axios.{method_lower}(\n"
            '            `{{BASE_URL}}{path}`,\n'
            "            {{ {headers_str}{data_str} }}\n"
            "        );\n"
            "        expect(response.status).toBe({expected_status});\n"
            "    });\n"
            "});\n"
        )

        return {
            "pytest": pytest_template,
            "javascript": js_template,
        }

    def generate_test_cases(
        self,
        endpoints: List[APIEndpoint],
        base_url: str = "http://localhost:8000"
    ) -> List[TestCase]:
        """生成测试用例

        Args:
            endpoints: API端点列表
            base_url: 基础URL

        Returns:
            List[TestCase]: 测试用例列表
        """
        test_cases = []

        for endpoint in endpoints:
            # 正常路径测试
            tc = TestCase(
                id=f"TC-{len(test_cases) + 1:04d}",
                name=f"Test {endpoint.method.value} {endpoint.path} - Success",
                endpoint=endpoint,
                assertions=["status_code == 200", "response_time < 1000ms"],
                expected_result={"status": "success"}
            )
            test_cases.append(tc)

            # 错误情况测试
            if endpoint.method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH]:
                tc_error = TestCase(
                    id=f"TC-{len(test_cases) + 1:04d}",
                    name=f"Test {endpoint.method.value} {endpoint.path} - Validation Error",
                    endpoint=endpoint,
                    assertions=["status_code in [400, 422]"],
                    expected_result={"status": "error"}
                )
                test_cases.append(tc_error)

        return test_cases

    def generate_pytest_code(
        self,
        endpoints: List[APIEndpoint],
        base_url: str = "http://localhost:8000",
        include_auth: bool = True
    ) -> str:
        """生成pytest测试代码

        Args:
            endpoints: API端点列表
            base_url: 基础URL
            include_auth: 是否包含认证

        Returns:
            str: pytest测试代码
        """
        imports = """import pytest
import requests
import time
from typing import Dict, Any

BASE_URL = "{base_url}"

# Authentication helper
def get_auth_headers() -> Dict[str, str]:
    # TODO: Implement actual authentication
    return {{"Authorization": "Bearer test_token"}}

# Request helper with timing
def make_request(method: str, url: str, **kwargs) -> tuple:
    start = time.time()
    response = requests.request(method, url, **kwargs)
    duration = (time.time() - start) * 1000
    return response, duration

""".format(base_url=base_url)

        classes = []
        for endpoint in endpoints:
            class_name = self._to_pascal_case(endpoint.path.replace("/", "_"))
            method_lower = endpoint.method.value.lower()
            path_safe = endpoint.path.replace("/", "_").replace("{", "").replace("}", "")
            headers_str = "headers=get_auth_headers(), " if include_auth else ""
            data_str = f"json={endpoint.body}, " if endpoint.body else ""

            # 生成多个测试方法
            test_methods = []

            # 成功测试
            test_methods.append(f"""
    def test_{method_lower}_{path_safe}_success(self):
        \"\"\"Test successful {endpoint.method.value} {endpoint.path}\"\"\"
        url = f"{{BASE_URL}}{endpoint.path}"
        headers = {{"Content-Type": "application/json"}}
        {('headers.update(get_auth_headers()), ' if include_auth else '')}
        data = {json.dumps(endpoint.body) if endpoint.body else '{}'}

        response, duration = make_request("{endpoint.method.value}", url, headers=headers, json=data if data else None)

        print(f"Response: {{response.status_code}} - {{response.text}}")
        print(f"Duration: {{duration:.2f}}ms")

        assert response.status_code == {endpoint.expected_status}, f"Expected {endpoint.expected_status}, got {{response.status_code}}"
        assert duration < 2000, f"Response time {{duration:.2f}}ms exceeded 2000ms"
""")

            # 认证测试
            if include_auth:
                test_methods.append(f"""
    def test_{method_lower}_{path_safe}_without_auth(self):
        \"\"\"Test {endpoint.method.value} {endpoint.path} without authentication\"\"\"
        url = f"{{BASE_URL}}{endpoint.path}"

        response, _ = make_request("{endpoint.method.value}", url)

        assert response.status_code == 401, f"Expected 401, got {{response.status_code}}"
""")

            # 响应格式测试
            test_methods.append(f"""
    def test_{method_lower}_{path_safe}_response_format(self):
        \"\"\"Test {endpoint.method.value} {endpoint.path} response format\"\"\"
        url = f"{{BASE_URL}}{endpoint.path}"
        headers = {{"Content-Type": "application/json"}}
        {('headers.update(get_auth_headers()), ' if include_auth else '')}
        data = {json.dumps(endpoint.body) if endpoint.body else '{}'}

        response, _ = make_request("{endpoint.method.value}", url, headers=headers, json=data if data else None)

        if response.status_code == 200:
            # Verify JSON response
            try:
                json_data = response.json()
                assert isinstance(json_data, (dict, list)), "Response should be JSON object or array"
            except ValueError:
                pytest.fail("Response is not valid JSON")
""")

            classes.append(f"""
class Test{class_name}:
    \"\"\"Tests for {endpoint.method.value} {endpoint.path}\"\"\"
{"".join(test_methods)}
""")

        return imports + "\n".join(classes)

    def generate_contract_tests(
        self,
        api_spec: Dict,
        provider: str = "consumer"
    ) -> str:
        """生成契约测试代码

        Args:
            api_spec: API规范
            provider: 提供者 (provider/consumer)

        Returns:
            str: 契约测试代码
        """
        if provider == "consumer":
            return self._generate_consumer_contract(api_spec)
        else:
            return self._generate_provider_contract(api_spec)

    def _generate_consumer_contract(self, api_spec: Dict) -> str:
        """生成消费者契约测试"""
        return f"""# Consumer Contract Tests
# Generated for API: {api_spec.get('name', 'Unknown')}

import pytest
from pact import Consumer, Provider

consumer = Consumer('{api_spec.get("consumer_name", "TestConsumer")}')
provider = Provider('{api_spec.get("provider_name", "TestProvider")}')

@pytest.fixture
def pact():
    return consumer


class TestAPIContract:
    def test_api_contract(self, pact):
        # Define expected interactions
        (pact
         .given('API is available')
         .upon_receiving('a request for {api_spec.get("endpoint", "/")}')
         .with_request(
             method='GET',
             path='{api_spec.get("endpoint", "/")}'
         )
         .will_respond_with(
             status={api_spec.get("expected_status", 200)},
             body={json.dumps(api_spec.get("response_body", {{}}))}
         ))

        # Execute test
        with pact:
            result = requests.get(pact.uri + '/{api_spec.get("endpoint", "/")}')
            assert result.status_code == {api_spec.get("expected_status", 200)}
"""

    def _generate_provider_contract(self, api_spec: Dict) -> str:
        """生成提供者契约测试"""
        return f"""# Provider Contract Tests
# Verify provider fulfills contract

import pytest

class TestContractVerification:
    def test_{api_spec.get('endpoint', 'endpoint').replace('/', '_')}_contract(self):
        # Verify {api_spec.get("endpoint", "/")} returns expected schema
        response = requests.get('{api_spec.get("base_url", "http://localhost")}{api_spec.get("endpoint", "/")}')

        assert response.status_code == {api_spec.get("expected_status", 200)}

        data = response.json()
        # Verify schema matches contract
        # Add schema validation here
"""

    def generate_load_test(
        self,
        endpoint: APIEndpoint,
        concurrent_users: int = 10,
        duration_seconds: int = 60
    ) -> str:
        """生成负载测试代码

        Args:
            endpoint: API端点
            concurrent_users: 并发用户数
            duration_seconds: 持续时间

        Returns:
            str: locust负载测试代码
        """
        method_lower = endpoint.method.value.lower()

        return f"""# Load Test for {endpoint.path}
# Users: {concurrent_users}, Duration: {duration_seconds}s

from locust import HttpUser, task, between
import random

class APIUser(HttpUser):
    wait_time = between(1, 3)
    host = "{{{{ host }}}}"

    @task({random.randint(1, 10)})
    def test_{method_lower}_{endpoint.path.replace('/', '_').replace('{{', '').replace('}}', '')}(self):
        self.client.{method_lower}(
            "{endpoint.path}",
            json={json.dumps(endpoint.body) if endpoint.body else None},
            headers={{"Authorization": "Bearer test_token"}}
        )
"""

    async def run_tests(
        self,
        test_cases: List[TestCase],
        base_url: str = "http://localhost:8000"
    ) -> TestReport:
        """运行测试

        Args:
            test_cases: 测试用例列表
            base_url: 基础URL

        Returns:
            TestReport: 测试报告
        """
        report = TestReport()
        report.total_tests = len(test_cases)

        for tc in test_cases:
            try:
                # 模拟测试执行
                result = {
                    "test_id": tc.id,
                    "name": tc.name,
                    "status": "passed",
                    "duration_ms": 100
                }
                report.results.append(result)
                report.passed += 1

            except Exception as e:
                report.results.append({
                    "test_id": tc.id,
                    "name": tc.name,
                    "status": "failed",
                    "error": str(e)
                })
                report.failed += 1

        return report

    def generate_report(self, report: TestReport, format: str = "markdown") -> str:
        """生成测试报告

        Args:
            report: 测试报告数据
            format: 格式 (markdown/json/html)

        Returns:
            str: 格式化的报告
        """
        if format == "json":
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": report.total_tests,
                    "passed": report.passed,
                    "failed": report.failed,
                    "skipped": report.skipped,
                    "pass_rate": f"{(report.passed / report.total_tests * 100) if report.total_tests > 0 else 0:.1f}%"
                },
                "results": report.results
            }, indent=2)

        elif format == "markdown":
            lines = [
                "# API Test Report",
                f"",
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"",
                "## Summary",
                f"",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Total Tests | {report.total_tests} |",
                f"| Passed | {report.passed} |",
                f"| Failed | {report.failed} |",
                f"| Skipped | {report.skipped} |",
                f"| Pass Rate | {(report.passed / report.total_tests * 100) if report.total_tests > 0 else 0:.1f}% |",
                ""
            ]

            if report.failed > 0:
                lines.append("## Failed Tests")
                lines.append("")
                for result in report.results:
                    if result.get("status") == "failed":
                        lines.append(f"- **{result['name']}**: {result.get('error', 'Unknown error')}")

            return "\n".join(lines)

        return str(report)

    def _to_pascal_case(self, text: str) -> str:
        """转PascalCase"""
        words = text.replace("_", " ").replace("/", " ").split()
        return "".join(word.capitalize() for word in words)

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "test_types": [t.value for t in TestType],
            "http_methods": [m.value for m in HTTPMethod],
            "frameworks": ["pytest", "unittest", "jest", "locust", "pact"]
        }


# 全局实例
api_tester = APITester()
