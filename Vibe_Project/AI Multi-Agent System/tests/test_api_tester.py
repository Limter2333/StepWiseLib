"""
API Tester Agent Tests
"""

import pytest
from agents.api_tester.api_tester import (
    APITester,
    TestType,
    HTTPMethod,
    APIEndpoint,
    TestCase,
    TestReport
)

# Mark all classes as not test classes to avoid pytest collection warnings
TestType.__test__ = False
HTTPMethod.__test__ = False
APIEndpoint.__test__ = False
TestCase.__test__ = False
TestReport.__test__ = False


class TestTestType:
    """测试API测试类型枚举"""

    def test_type_values(self):
        assert TestType.UNIT.value == "unit"
        assert TestType.INTEGRATION.value == "integration"
        assert TestType.CONTRACT.value == "contract"
        assert TestType.PERFORMANCE.value == "performance"
        assert TestType.SECURITY.value == "security"
        assert TestType.E2E.value == "e2e"

    def test_type_count(self):
        assert len(TestType) == 6


class TestHTTPMethod:
    """测试HTTP方法枚举"""

    def test_method_values(self):
        assert HTTPMethod.GET.value == "GET"
        assert HTTPMethod.POST.value == "POST"
        assert HTTPMethod.PUT.value == "PUT"
        assert HTTPMethod.PATCH.value == "PATCH"
        assert HTTPMethod.DELETE.value == "DELETE"

    def test_method_count(self):
        assert len(HTTPMethod) == 5


class TestAPIEndpoint:
    """测试API端点数据类"""

    def test_endpoint_creation(self):
        endpoint = APIEndpoint(
            method=HTTPMethod.GET,
            path="/api/users",
            description="Get all users"
        )

        assert endpoint.method == HTTPMethod.GET
        assert endpoint.path == "/api/users"
        assert endpoint.expected_status == 200  # default

    def test_endpoint_with_body(self):
        endpoint = APIEndpoint(
            method=HTTPMethod.POST,
            path="/api/users",
            description="Create user",
            params={"page": 1},
            headers={"Authorization": "Bearer token"},
            body={"name": "John"},
            expected_status=201
        )

        assert endpoint.body["name"] == "John"
        assert endpoint.expected_status == 201


class TestCaseData:
    """测试测试用例数据类"""

    def test_case_creation(self):
        endpoint = APIEndpoint(
            method=HTTPMethod.GET,
            path="/api/health",
            description="Health check"
        )
        case = TestCase(
            id="tc_1",
            name="Health check returns 200",
            endpoint=endpoint,
            assertions=["status == 200"],
            expected_result={"status": "ok"}
        )

        assert case.id == "tc_1"
        assert case.name == "Health check returns 200"
        assert case.endpoint.path == "/api/health"
        assert len(case.assertions) == 1


class TestReportData:
    """测试测试报告数据类"""

    def test_report_creation(self):
        report = TestReport()

        assert report.total_tests == 0  # default
        assert report.passed == 0  # default
        assert report.failed == 0  # default
        assert report.results == []  # default

    def test_report_with_results(self):
        report = TestReport(
            total_tests=10,
            passed=8,
            failed=1,
            skipped=1,
            duration_ms=150.5,
            results=[
                {"id": "tc_1", "status": "passed"},
                {"id": "tc_2", "status": "failed"}
            ]
        )

        assert report.total_tests == 10
        assert report.passed == 8
        assert report.failed == 1
        assert report.skipped == 1
        assert report.duration_ms == 150.5
        assert len(report.results) == 2


class TestAPITester:
    """测试API测试智能体"""

    def test_agent_creation(self):
        agent = APITester()
        assert agent.name == "API Tester"

    def test_global_instance_exists(self):
        from agents.api_tester import api_tester
        assert api_tester.name == "API Tester"

    def test_get_capabilities(self):
        agent = APITester()
        caps = agent.get_capabilities()

        assert caps["name"] == "API Tester"
        assert len(caps["test_types"]) > 0
        assert len(caps["http_methods"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
