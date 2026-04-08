"""
Test Agent Tests
"""

import pytest
from datetime import datetime
from agents.test_agent.test_agent import (
    TestAgent,
    CaseItem,
    TestBundle,
    SummaryReport,
    TestKind
)


class TestTestAgentCreation:
    """测试TestAgent创建"""

    def test_agent_creation(self):
        agent = TestAgent()
        assert agent.name == "Test Agent"
        assert len(agent.test_templates) > 0

    def test_global_instance_exists(self):
        from agents.test_agent import test_agent
        assert test_agent.name == "Test Agent"


class TestTestKind:
    """测试测试类型枚举"""

    def test_test_type_values(self):
        assert TestKind.UNIT.value == "unit"
        assert TestKind.INTEGRATION.value == "integration"
        assert TestKind.E2E.value == "e2e"
        assert TestKind.PERFORMANCE.value == "performance"
        assert TestKind.SECURITY.value == "security"

    def test_test_type_count(self):
        assert len(TestKind) == 5


class TestTestCase:
    """测试测试用例数据类"""

    def test_test_case_creation(self):
        tc = CaseItem(
            id="tc_1",
            name="Test Addition",
            description="Test adding two numbers",
            test_type=TestKind.UNIT,
            code="assert add(1, 2) == 3",
            expected_result="3"
        )

        assert tc.id == "tc_1"
        assert tc.name == "Test Addition"
        assert tc.test_type == TestKind.UNIT
        assert tc.priority == 1  # default

    def test_test_case_with_priority(self):
        tc = CaseItem(
            id="tc_2",
            name="Critical Test",
            description="Test critical path",
            test_type=TestKind.UNIT,
            code="assert True",
            expected_result="True",
            priority=5
        )

        assert tc.priority == 5


class TestTestSuite:
    """测试测试套件数据类"""

    def test_test_suite_creation(self):
        suite = TestBundle(
            name="Unit Tests",
            test_cases=[]
        )

        assert suite.name == "Unit Tests"
        assert suite.coverage == 0.0
        assert suite.passed == 0
        assert suite.failed == 0

    def test_test_suite_with_cases(self):
        tc = CaseItem(
            id="tc_1",
            name="Test 1",
            description="Test",
            test_type=TestKind.UNIT,
            code="assert 1",
            expected_result="1"
        )

        suite = TestBundle(
            name="Suite",
            test_cases=[tc],
            coverage=80.0,
            passed=1,
            failed=0
        )

        assert len(suite.test_cases) == 1
        assert suite.coverage == 80.0


class TestTestReport:
    """测试测试报告类"""

    def test_report_creation(self):
        report = SummaryReport()

        assert len(report.suites) == 0
        assert report.total_tests == 0
        assert report.passed_tests == 0
        assert report.failed_tests == 0

    def test_report_add_suite(self):
        report = SummaryReport()

        tc = CaseItem(
            id="tc_1",
            name="Test 1",
            description="Test",
            test_type=TestKind.UNIT,
            code="assert 1",
            expected_result="1"
        )

        suite = TestBundle(
            name="Unit Tests",
            test_cases=[tc],
            passed=1,
            failed=0
        )

        report.add_suite(suite)

        assert len(report.suites) == 1
        assert report.total_tests == 1
        assert report.passed_tests == 1

    def test_report_pass_rate_zero(self):
        report = SummaryReport()

        assert report.pass_rate == 0.0

    def test_report_pass_rate(self):
        report = SummaryReport()

        suite = TestBundle(
            name="Tests",
            test_cases=[CaseItem(id="1", name="T1", description="", test_type=TestKind.UNIT, code="", expected_result=""),
                        CaseItem(id="2", name="T2", description="", test_type=TestKind.UNIT, code="", expected_result="")],
            passed=1,
            failed=1
        )
        report.add_suite(suite)

        assert report.pass_rate == 50.0

    def test_to_markdown(self):
        report = SummaryReport()
        suite = TestBundle(
            name="Unit Tests",
            test_cases=[
                CaseItem(id="tc_1", name="Test One", description="First test",
                        test_type=TestKind.UNIT, code="assert 1", expected_result="1")
            ],
            coverage=100.0,
            passed=1,
            failed=0
        )
        report.add_suite(suite)

        md = report.to_markdown()

        assert "# Test Report" in md
        assert "Unit Tests" in md
        assert "Passed" in md
        assert "Test One" in md

    def test_to_json(self):
        report = SummaryReport()

        report.to_json()  # Should not raise

        import json
        data = json.loads(report.to_json())

        assert "timestamp" in data
        assert "summary" in data


class TestTestAgentTemplates:
    """测试测试模板"""

    def test_load_templates(self):
        agent = TestAgent()

        assert "python_unittest" in agent.test_templates
        assert "pytest" in agent.test_templates
        assert "api_test" in agent.test_templates

    def test_template_contains_placeholders(self):
        agent = TestAgent()

        template = agent.test_templates["pytest"]

        assert "{module_name}" in template
        assert "{class_name}" in template
        assert "{method}" in template


class TestGenerateUnitTests:
    """测试单元测试生成"""

    @pytest.mark.asyncio
    async def test_generate_unit_tests_basic(self):
        agent = TestAgent()

        tests = await agent.generate_unit_tests(
            module_name="my_module",
            class_name="MyClass",
            methods=["method1", "method2"]
        )

        assert len(tests) == 2
        assert "my_module" in tests[0]
        assert "MyClass" in tests[0]

    @pytest.mark.asyncio
    async def test_generate_unit_tests_custom_framework(self):
        agent = TestAgent()

        tests = await agent.generate_unit_tests(
            module_name="mod",
            class_name="Cls",
            methods=["do_it"],
            framework="python_unittest"
        )

        assert len(tests) == 1
        assert "unittest" in tests[0]

    @pytest.mark.asyncio
    async def test_generate_unit_tests_empty_methods(self):
        agent = TestAgent()

        tests = await agent.generate_unit_tests(
            module_name="mod",
            class_name="Cls",
            methods=[]
        )

        assert len(tests) == 0


class TestGenerateIntegrationTests:
    """测试集成测试生成"""

    @pytest.mark.asyncio
    async def test_generate_integration_tests(self):
        agent = TestAgent()

        interactions = [
            {"from": "AuthService", "to": "UserDB", "method": "get_user", "params": {"id": 1}}
        ]

        test_cases = await agent.generate_integration_tests(
            components=["AuthService", "UserDB"],
            interactions=interactions
        )

        assert len(test_cases) == 1
        assert test_cases[0].name == "Test AuthService -> UserDB"
        assert test_cases[0].test_type == TestKind.INTEGRATION

    @pytest.mark.asyncio
    async def test_generate_integration_tests_multiple(self):
        agent = TestAgent()

        interactions = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"}
        ]

        test_cases = await agent.generate_integration_tests(
            components=["A", "B", "C"],
            interactions=interactions
        )

        assert len(test_cases) == 2


class TestRunTests:
    """测试测试运行"""

    @pytest.mark.asyncio
    async def test_run_tests(self):
        agent = TestAgent()

        tc = CaseItem(
            id="tc_1",
            name="Test 1",
            description="Test",
            test_type=TestKind.UNIT,
            code="assert True",
            expected_result="True"
        )

        suite = TestBundle(name="Test Suite", test_cases=[tc])

        report = await agent.run_tests(suite)

        assert report is not None
        assert report.total_tests == 1
        assert report.passed_tests == 1  # Simplified assumes all pass


class TestGenerateTestReport:
    """测试测试报告生成"""

    @pytest.mark.asyncio
    async def test_generate_test_report_markdown(self):
        agent = TestAgent()

        test_results = {
            "Unit Tests": {"coverage": 80.0, "passed": 8, "failed": 2}
        }

        report = await agent.generate_test_report(test_results, format="markdown")

        assert "# Test Report" in report or "Test Report" in report
        assert "Unit Tests" in report

    @pytest.mark.asyncio
    async def test_generate_test_report_json(self):
        agent = TestAgent()

        test_results = {
            "Unit Tests": {"coverage": 100.0, "passed": 10, "failed": 0}
        }

        report = await agent.generate_test_report(test_results, format="json")

        import json
        data = json.loads(report)
        assert "summary" in data


class TestGenerateLoadTest:
    """测试压力测试生成"""

    @pytest.mark.asyncio
    async def test_generate_load_test(self):
        agent = TestAgent()

        script = await agent.generate_load_test(
            endpoint="/api/users",
            concurrent_users=100,
            duration_seconds=60
        )

        assert "/api/users" in script
        assert "100" in script or "concurrent_users" in script


class TestCapabilities:
    """测试能力获取"""

    def test_get_capabilities(self):
        agent = TestAgent()

        caps = agent.get_capabilities()

        assert caps["name"] == "Test Agent"
        assert "unit" in caps["supported_test_types"]
        assert "integration" in caps["supported_test_types"]
        assert "pytest" in caps["supported_frameworks"]
        assert "unittest" in caps["supported_frameworks"]
        assert "markdown" in caps["report_formats"]
        assert "json" in caps["report_formats"]

    def test_all_test_types_supported(self):
        agent = TestAgent()
        caps = agent.get_capabilities()

        for tt in TestKind:
            assert tt.value in caps["supported_test_types"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
