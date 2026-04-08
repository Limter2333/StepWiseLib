"""
Reality Checker Agent - 现实核查智能体
=====================================

职责:
- 事实核查
- 可行性评估
- 风险识别
- 假设验证
- 数据准确性检查
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.prompt_engine import prompt_manager
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel


class ClaimType(Enum):
    """声明类型"""
    FACT = "fact"
    OPINION = "opinion"
    PREDICTION = "prediction"
    ASSUMPTION = "assumption"


class ConfidenceLevel(Enum):
    """置信级别"""
    HIGH = "high"      # 90%+
    MEDIUM = "medium"  # 60-90%
    LOW = "low"        # <60%


@dataclass
class Claim:
    """声明"""
    id: str
    text: str
    claim_type: ClaimType
    source: Optional[str] = None
    verification_status: str = "pending"  # verified, false, unverified, partial


@dataclass
class RealityCheckResult:
    """核查结果"""
    claim: Claim
    is_verified: bool
    confidence: ConfidenceLevel
    evidence: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    verdict: str = ""
    explanation: str = ""


@dataclass
class FeasibilityResult:
    """可行性评估结果"""
    is_feasible: bool
    confidence: ConfidenceLevel
    timeline_estimate: str = ""
    resource_requirements: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class RealityChecker:
    """现实核查智能体

    【能力】
    - 事实核查
    - 可行性评估
    - 风险识别
    - 假设验证
    - 数据准确性检查
    """

    def __init__(self):
        self.name = "Reality Checker"
        self.specialty = ["事实核查", "风险评估", "可行性分析", "数据验证"]
        self.claims_history: List[Claim] = []

    async def check_fact(
        self,
        statement: str,
        context: Optional[str] = None
    ) -> RealityCheckResult:
        """核查事实

        Args:
            statement: 待核查的声明
            context: 上下文

        Returns:
            RealityCheckResult: 核查结果
        """
        claim = Claim(
            id=f"CLM-{len(self.claims_history) + 1:04d}",
            text=statement,
            claim_type=ClaimType.FACT
        )

        evidence = []
        contradictions = []

        try:
            # 使用LLM进行事实核查
            llm = get_llm()
            system_prompt = """You are a fact-checker. Evaluate the given statement for accuracy.
Provide evidence for or against the claim. Be objective and cite sources when possible."""

            user_prompt = f"""Fact-check this statement:
"{statement}"

Context: {context or 'No additional context provided'}

Respond with:
1. Verification status (verified/unverified/false/partial)
2. Confidence level (high/medium/low)
3. Supporting evidence
4. Contradicting evidence
5. Verdict
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3
            )

            # 解析结果
            result = self._parse_llm_response(response.content, claim)
            self.claims_history.append(claim)
            return result

        except Exception as e:
            error_logger.log(
                error_type="RealityCheckError",
                message=f"Fact check failed: {str(e)}",
                level=ErrorLevel.WARNING
            )

            return RealityCheckResult(
                claim=claim,
                is_verified=False,
                confidence=ConfidenceLevel.LOW,
                verdict="Unable to verify",
                explanation=f"Check failed due to: {str(e)}"
            )

    async def assess_feasibility(
        self,
        requirement: str,
        current_capabilities: Optional[Dict] = None
    ) -> FeasibilityResult:
        """评估可行性

        Args:
            requirement: 需求描述
            current_capabilities: 当前能力/资源

        Returns:
            FeasibilityResult: 可行性评估
        """
        risks = []
        blockers = []
        recommendations = []

        try:
            llm = get_llm()
            system_prompt = """You are a technical feasibility analyst. Evaluate the given requirement
for technical feasibility, considering current resources and constraints."""

            capabilities_str = "\n".join([
                f"- {k}: {v}" for k, v in (current_capabilities or {}).items()
            ])

            user_prompt = f"""Assess feasibility of:
Requirement: {requirement}

Current Capabilities:
{capabilities_str or "Not specified"}

Evaluate:
1. Technical feasibility (1-10)
2. Resource requirements
3. Timeline estimate
4. Key risks
5. Potential blockers
6. Recommendations
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3
            )

            # 解析评估结果
            result = self._parse_feasibility_response(response.content)
            return result

        except Exception as e:
            error_logger.log(
                error_type="FeasibilityError",
                message=f"Feasibility assessment failed: {str(e)}",
                level=ErrorLevel.WARNING
            )

            return FeasibilityResult(
                is_feasible=False,
                confidence=ConfidenceLevel.LOW,
                blockers=[f"Assessment failed: {str(e)}"]
            )

    async def identify_risks(
        self,
        plan: str,
        context: Optional[str] = None
    ) -> List[Dict]:
        """识别风险

        Args:
            plan: 计划/方案描述
            context: 上下文

        Returns:
            List[Dict]: 风险列表
        """
        risks = []

        try:
            llm = get_llm()
            system_prompt = """You are a risk analyst. Identify potential risks in the given plan.
Categorize risks and suggest mitigation strategies."""

            user_prompt = f"""Identify risks in:
Plan: {plan}
Context: {context or 'No additional context'}

For each risk provide:
- Category (technical, resource, external, schedule)
- Impact (high/medium/low)
- Likelihood (high/medium/low)
- Mitigation strategy
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3
            )

            risks = self._parse_risks_response(response.content)

        except Exception as e:
            error_logger.log(
                error_type="RiskAnalysisError",
                message=f"Risk identification failed: {str(e)}",
                level=ErrorLevel.WARNING
            )

        return risks

    async def validate_assumption(
        self,
        assumption: str,
        evidence: Optional[List[str]] = None
    ) -> Dict:
        """验证假设

        Args:
            assumption: 假设描述
            evidence: 支持证据列表

        Returns:
            Dict: 验证结果
        """
        try:
            llm = get_llm()
            system_prompt = """You are a critical thinking analyst. Evaluate assumptions against evidence."""

            evidence_str = "\n".join([f"- {e}" for e in (evidence or [])])

            user_prompt = f"""Validate this assumption:
"{assumption}"

Supporting Evidence:
{evidence_str or "No evidence provided"}

Determine:
1. Is the assumption valid, partially valid, or invalid?
2. What evidence supports or contradicts it?
3. What would need to be true for this assumption to hold?
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3
            )

            return {
                "assumption": assumption,
                "analysis": response.content,
                "is_valid": "valid" in response.content.lower()
            }

        except Exception as e:
            error_logger.log(
                error_type="ValidationError",
                message=f"Assumption validation failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            return {
                "assumption": assumption,
                "is_valid": False,
                "reason": str(e)
            }

    def _parse_llm_response(
        self,
        llm_response: str,
        claim: Claim
    ) -> RealityCheckResult:
        """解析LLM响应"""
        lower_response = llm_response.lower()

        # 判断验证状态
        if "verified" in lower_response and "unverified" not in lower_response:
            is_verified = True
        elif "false" in lower_response:
            is_verified = False
        else:
            is_verified = False

        # 判断置信度
        if "high confidence" in lower_response or "verified" in lower_response:
            confidence = ConfidenceLevel.HIGH
        elif "medium" in lower_response:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        return RealityCheckResult(
            claim=claim,
            is_verified=is_verified,
            confidence=confidence,
            evidence=[],
            contradictions=[],
            verdict="Verified" if is_verified else "Unverified/Falsified",
            explanation=llm_response[:500]
        )

    def _parse_feasibility_response(self, llm_response: str) -> FeasibilityResult:
        """解析可行性评估响应"""
        lower_response = llm_response.lower()

        is_feasible = "feasible" in lower_response or "possible" in lower_response
        confidence = ConfidenceLevel.MEDIUM

        if "not feasible" in lower_response or "impossible" in lower_response:
            is_feasible = False

        if "high confidence" in lower_response:
            confidence = ConfidenceLevel.HIGH
        elif "low confidence" in lower_response:
            confidence = ConfidenceLevel.LOW

        return FeasibilityResult(
            is_feasible=is_feasible,
            confidence=confidence,
            explanation=llm_response[:500]
        )

    def _parse_risks_response(self, llm_response: str) -> List[Dict]:
        """解析风险响应"""
        risks = []

        # 简单解析 - 实际应该用更好的方法
        lines = llm_response.split("\n")
        current_risk = {}

        for line in lines:
            if "-" in line or "*" in line:
                content = line.lstrip("-* ").strip()
                if "risk" in content.lower() or "impact" in content.lower():
                    if current_risk:
                        risks.append(current_risk)
                    current_risk = {"description": content}
                elif current_risk:
                    if "mitigation" not in current_risk:
                        current_risk["mitigation"] = content

        if current_risk:
            risks.append(current_risk)

        return risks

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "claim_types": [c.value for c in ClaimType],
            "confidence_levels": [c.value for c in ConfidenceLevel],
            "verification_methods": ["llm_analysis", "evidence_check", "cross_reference"]
        }


# 全局实例
reality_checker = RealityChecker()
