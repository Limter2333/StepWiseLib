"""
Reality Checker Agent Tests
"""

import pytest
from agents.reality_checker.reality_checker import (
    RealityChecker,
    ClaimType,
    ConfidenceLevel,
    Claim,
    RealityCheckResult,
    FeasibilityResult
)


class TestClaimType:
    """测试声明类型枚举"""

    def test_claim_type_values(self):
        assert ClaimType.FACT.value == "fact"
        assert ClaimType.OPINION.value == "opinion"
        assert ClaimType.PREDICTION.value == "prediction"
        assert ClaimType.ASSUMPTION.value == "assumption"

    def test_claim_type_count(self):
        assert len(ClaimType) == 4


class TestConfidenceLevel:
    """测试置信级别枚举"""

    def test_confidence_values(self):
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"

    def test_confidence_count(self):
        assert len(ConfidenceLevel) == 3


class TestClaim:
    """测试声明数据类"""

    def test_claim_creation(self):
        claim = Claim(
            id="claim_1",
            text="The earth is round",
            claim_type=ClaimType.FACT
        )

        assert claim.id == "claim_1"
        assert claim.text == "The earth is round"
        assert claim.claim_type == ClaimType.FACT
        assert claim.verification_status == "pending"  # default

    def test_claim_with_source(self):
        claim = Claim(
            id="claim_2",
            text="AI will replace jobs",
            claim_type=ClaimType.PREDICTION,
            source="TechReport 2026",
            verification_status="unverified"
        )

        assert claim.source == "TechReport 2026"
        assert claim.verification_status == "unverified"


class TestRealityCheckResult:
    """测试核查结果数据类"""

    def test_result_creation(self):
        claim = Claim(
            id="c1",
            text="Test claim",
            claim_type=ClaimType.FACT
        )
        result = RealityCheckResult(
            claim=claim,
            is_verified=True,
            confidence=ConfidenceLevel.HIGH,
            verdict="Confirmed"
        )

        assert result.is_verified is True
        assert result.confidence == ConfidenceLevel.HIGH
        assert result.evidence == []  # default
        assert result.contradictions == []  # default

    def test_result_with_evidence(self):
        claim = Claim(
            id="c1",
            text="Water boils at 100C",
            claim_type=ClaimType.FACT
        )
        result = RealityCheckResult(
            claim=claim,
            is_verified=True,
            confidence=ConfidenceLevel.HIGH,
            evidence=["Scientific study 1", "Standard definition"],
            contradictions=[],
            verdict="True",
            explanation="Standard atmospheric pressure"
        )

        assert len(result.evidence) == 2
        assert result.verdict == "True"


class TestFeasibilityResult:
    """测试可行性评估结果数据类"""

    def test_result_creation(self):
        result = FeasibilityResult(
            is_feasible=True,
            confidence=ConfidenceLevel.MEDIUM
        )

        assert result.is_feasible is True
        assert result.confidence == ConfidenceLevel.MEDIUM

    def test_result_with_full_data(self):
        result = FeasibilityResult(
            is_feasible=False,
            confidence=ConfidenceLevel.LOW,
            timeline_estimate="6 months",
            resource_requirements=["GPU cluster", "10 engineers"],
            risks=["Budget overrun", "Timeline slip"],
            blockers=["Insufficient compute", "Missing expertise"],
            recommendations=["Reduce scope", "Hire more devs"]
        )

        assert result.timeline_estimate == "6 months"
        assert len(result.resource_requirements) == 2
        assert len(result.risks) == 2
        assert len(result.blockers) == 2
        assert len(result.recommendations) == 2


class TestRealityChecker:
    """测试现实核查智能体"""

    def test_agent_creation(self):
        agent = RealityChecker()
        assert agent.name == "Reality Checker"

    def test_global_instance_exists(self):
        from agents.reality_checker import reality_checker
        assert reality_checker.name == "Reality Checker"

    def test_get_capabilities(self):
        agent = RealityChecker()
        caps = agent.get_capabilities()

        assert caps["name"] == "Reality Checker"
        assert len(caps["claim_types"]) > 0
        assert len(caps["confidence_levels"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
