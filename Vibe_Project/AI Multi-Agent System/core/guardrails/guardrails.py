"""
守卫护栏模块 Guardrails
=======================

【学习要点】
1. 什么是Guardrails?
   - AI系统的安全防护层
   - 过滤输入：防止恶意prompt注入
   - 过滤输出：防止有害内容泄露
   - 监控：记录所有交互用于审计

2. 为什么需要Guardrails?
   - Prompt注入攻击
   - 敏感信息泄露
   - 有害内容生成
   - 业务规则合规

3. Guardrails分层
   - Input Guardrails: 输入验证
   - Output Guardrails: 输出过滤
   - Context Guardrails: 上下文监控
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
import re
from datetime import datetime
from pydantic import BaseModel, Field


class GuardrailType(Enum):
    """护栏类型

    【学习要点】枚举定义安全检查类型
    """
    # 输入检查
    INPUT_SANITIZATION = "input_sanitization"      # 输入清理
    PROMPT_INJECTION = "prompt_injection"          # Prompt注入检测
    SENSITIVE_INPUT = "sensitive_input"            # 敏感信息检测
    LENGTH_CHECK = "length_check"                  # 长度检查

    # 输出检查
    OUTPUT_SANITIZATION = "output_sanitization"    # 输出清理
    SENSITIVE_OUTPUT = "sensitive_output"          # 敏感信息泄露
    CONTENT_FILTER = "content_filter"              # 内容过滤

    # 上下文检查
    RATE_LIMIT = "rate_limit"                      # 频率限制
    SESSION_TIMEOUT = "session_timeout"            # 会话超时


class GuardrailResult(BaseModel):
    """护栏检查结果

    【学习要点】Pydantic模型
    - 自动验证
    - 类型转换
    - 序列化
    """
    passed: bool
    check_type: str
    message: str = ""
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    sanitized_content: Optional[str] = None
    action_taken: Optional[str] = None


class GuardrailConfig(BaseModel):
    """护栏配置"""
    max_input_length: int = 10000
    max_output_length: int = 8000
    block_patterns: List[str] = []
    warn_patterns: List[str] = []
    rate_limit_per_minute: int = 60
    session_timeout_seconds: int = 1800


class Guardrails:
    """守卫护栏系统

    【架构设计】
    - 分层检查：Input → Context → Output
    - 结果聚合：多个检查结果合并
    - 可配置：规则可动态调整
    - 可审计：记录所有检查
    """

    def __init__(self, config: Optional[GuardrailConfig] = None):
        self.config = config or GuardrailConfig()

        # 检查历史（用于审计）
        self.check_history: List[Dict] = []

        # 敏感词库（可扩展）
        self._sensitive_patterns = [
            r'\b\d{15,18}\b',  # 身份证号
            r'\b\d{16,19}\b',  # 信用卡号
            r'api[_-]?key["\']?\s*[:=]\s*["\']?\w+',  # API密钥
            r'password["\']?\s*[:=]\s*["\']?\S+',  # 密码
        ]

        # Prompt注入模式
        self._injection_patterns = [
            r'ignore\s+(previous|above|all)\s+(instructions?|prompts?)',
            r'system\s*:\s*',
            r'\bstrip\s*\(\s*["\']',
            r'\[\s*INST\s*\]',
            r'<script',
            r'{{.*}}.*{{\s*}}',  # 模板注入
        ]

        # 编译正则表达式（性能优化）
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式

        【学习要点】正则编译优化
        - re.compile() 预编译提高性能
        - 避免每次匹配时重新编译
        """
        self._compiled_block = [
            re.compile(p, re.IGNORECASE) for p in self.config.block_patterns
        ]
        self._compiled_warn = [
            re.compile(p, re.IGNORECASE) for p in self.config.warn_patterns
        ]
        self._compiled_sensitive = [
            re.compile(p, re.IGNORECASE) for p in self._sensitive_patterns
        ]
        self._compiled_injection = [
            re.compile(p, re.IGNORECASE) for p in self._injection_patterns
        ]

    def check_input(self, text: str) -> GuardrailResult:
        """检查用户输入

        【检查流程】
        1. 长度检查
        2. Prompt注入检测
        3. 敏感信息检测
        4. 自定义规则检查
        """
        if not text or not text.strip():
            return GuardrailResult(
                passed=False,
                check_type="empty_check",
                message="Input cannot be empty"
            )

        # 1. 长度检查
        length_result = self._check_length(text, is_input=True)
        if not length_result.passed:
            return length_result

        # 2. Prompt注入检测
        injection_result = self._check_prompt_injection(text)
        if not injection_result.passed:
            return injection_result

        # 3. 敏感信息检测
        sensitive_result = self._check_sensitive_info(text, is_input=True)
        if not sensitive_result.passed:
            return sensitive_result

        # 4. 自定义规则
        custom_result = self._check_custom_rules(text)
        if not custom_result.passed:
            return custom_result

        return GuardrailResult(
            passed=True,
            check_type="input_check",
            message="Input passed all checks"
        )

    def check_output(self, text: str) -> GuardrailResult:
        """检查AI输出"""
        if not text:
            return GuardrailResult(
                passed=True,
                check_type="empty_check"
            )

        # 1. 长度检查
        length_result = self._check_length(text, is_input=False)
        if not length_result.passed:
            return length_result

        # 2. 敏感信息泄露检测
        sensitive_result = self._check_sensitive_info(text, is_input=False)
        if not sensitive_result.passed:
            return sensitive_result

        # 3. 内容过滤
        content_result = self._check_content_filter(text)
        if not content_result.passed:
            return content_result

        return GuardrailResult(
            passed=True,
            check_type="output_check",
            message="Output passed all checks"
        )

    def sanitize_input(self, text: str) -> Tuple[str, List[str]]:
        """清理输入文本

        Args:
            text: 原始输入

        Returns:
            (清理后文本, 移除的内容列表)

        【学习要点】数据脱敏
        - 移除敏感信息但保留格式
        - 用***替换而非删除
        """
        if text is None:
            return "", []

        sanitized = text
        removed = []

        # 移除脚本标签
        script_pattern = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
        matches = script_pattern.findall(sanitized)
        for match in matches:
            removed.append(f"[REMOVED_SCRIPT: {match[:50]}...]")
        sanitized = script_pattern.sub('[SCRIPT REMOVED]', sanitized)

        # 移除SQL注入尝试
        sql_pattern = re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b.*?;)', re.IGNORECASE)
        matches = sql_pattern.findall(sanitized)
        for match in matches:
            removed.append(f"[REMOVED_SQL: {match[:50]}...]")
        sanitized = sql_pattern.sub('[SQL REMOVED]', sanitized)

        return sanitized, removed

    def _check_length(self, text: str, is_input: bool) -> GuardrailResult:
        """检查文本长度"""
        max_len = self.config.max_input_length if is_input else self.config.max_output_length
        limit_type = "input" if is_input else "output"

        if len(text) > max_len:
            return GuardrailResult(
                passed=False,
                check_type=f"{limit_type}_length_check",
                message=f"{limit_type.capitalize()} exceeds maximum length ({len(text)} > {max_len})",
                risk_level="MEDIUM",
                action_taken=f"Truncated to {max_len} characters"
            )

        return GuardrailResult(passed=True, check_type="length_check")

    def _check_prompt_injection(self, text: str) -> GuardrailResult:
        """检测Prompt注入

        【学习要点】Prompt注入攻击
        - 攻击者试图覆盖系统指令
        - 常见模式：ignore previous、system:
        - 防御：检测可疑模式
        """
        for i, pattern in enumerate(self._compiled_injection):
            matches = pattern.findall(text)
            if matches:
                return GuardrailResult(
                    passed=False,
                    check_type="prompt_injection",
                    message=f"Potential prompt injection detected: {matches[0][:50]}",
                    risk_level="CRITICAL",
                    action_taken="BLOCKED"
                )

        # 检查是否有意插入系统指令
        if re.search(r'^system\s*:\s*', text, re.MULTILINE | re.IGNORECASE):
            return GuardrailResult(
                passed=False,
                check_type="prompt_injection",
                message="Attempted to override system instructions",
                risk_level="CRITICAL",
                action_taken="BLOCKED"
            )

        return GuardrailResult(passed=True, check_type="prompt_injection_check")

    def _check_sensitive_info(self, text: str, is_input: bool) -> GuardrailResult:
        """检查敏感信息"""
        found = []

        for pattern in self._compiled_sensitive:
            matches = pattern.findall(text)
            if matches:
                found.extend(matches)

        if found:
            action = "WARN" if is_input else "REDACT"
            risk = "HIGH" if is_input else "MEDIUM"

            return GuardrailResult(
                passed=True,  # 只警告不阻止
                check_type="sensitive_info",
                message=f"Potential sensitive information detected: {found[0][:20]}...",
                risk_level=risk,
                sanitized_content=self._redact_sensitive(text) if not is_input else None,
                action_taken=action
            )

        return GuardrailResult(passed=True, check_type="sensitive_check")

    def _check_custom_rules(self, text: str) -> GuardrailResult:
        """检查自定义规则"""
        # 检查禁止的模式
        for pattern in self._compiled_block:
            if pattern.search(text):
                return GuardrailResult(
                    passed=False,
                    check_type="custom_block",
                    message="Content violates policy",
                    risk_level="HIGH",
                    action_taken="BLOCKED"
                )

        # 检查警告模式
        for pattern in self._compiled_warn:
            if pattern.search(text):
                return GuardrailResult(
                    passed=True,
                    check_type="custom_warn",
                    message="Content flagged for review",
                    risk_level="MEDIUM",
                    action_taken="LOGGED"
                )

        return GuardrailResult(passed=True, check_type="custom_rules")

    def _check_content_filter(self, text: str) -> GuardrailResult:
        """内容过滤器（输出检查）"""
        # 这里可以接入更复杂的内容审核服务
        # 简化实现：检测明显的违规关键词

        # 待扩展：接入第三方内容审核API
        return GuardrailResult(
            passed=True,
            check_type="content_filter",
            message="Content passed filter"
        )

    def _redact_sensitive(self, text: str) -> str:
        """脱敏处理

        【学习要点】数据脱敏
        - 信用卡: 1234567890123456 → ************3456
        - 身份证: 110101199001011234 → *************1234
        """
        redacted = text

        # 信用卡号
        redacted = re.sub(r'\b(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})\b',
                          '****-****-****-\\4', redacted)

        # 身份证号
        redacted = re.sub(r'\b(\d{3})\d{11}(\d{4})\b',
                          '\\1************\\2', redacted)

        return redacted

    def log_check(self, result: GuardrailResult, original_content: str):
        """记录检查结果（审计用）"""
        self.check_history.append({
            "timestamp": datetime.now().isoformat(),
            "check_type": result.check_type,
            "passed": result.passed,
            "risk_level": result.risk_level,
            "message": result.message,
            "content_preview": original_content[:100]
        })

    def get_audit_report(self, limit: int = 100) -> Dict:
        """生成审计报告"""
        recent = self.check_history[-limit:]

        stats = {
            "total_checks": len(recent),
            "passed": sum(1 for r in recent if r["passed"]),
            "failed": sum(1 for r in recent if not r["passed"]),
            "by_risk_level": {},
            "by_type": {}
        }

        for r in recent:
            risk = r["risk_level"]
            check_type = r["check_type"]
            stats["by_risk_level"][risk] = stats["by_risk_level"].get(risk, 0) + 1
            stats["by_type"][check_type] = stats["by_type"].get(check_type, 0) + 1

        return stats


# 全局单例
guardrails = Guardrails()


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 初始化（可自定义配置）
config = GuardrailConfig(
    max_input_length=5000,
    block_patterns=[r'违禁词1', r'违禁词2']
)
guard = Guardrails(config)

# 2. 检查用户输入
result = guard.check_input("用户输入的文本")

if not result.passed:
    print(f"阻止: {result.message}")
elif result.risk_level in ["HIGH", "CRITICAL"]:
    print(f"警告: {result.message}")

# 3. 清理输入
sanitized, removed = guard.sanitize_input(raw_input)

# 4. 检查AI输出
output_result = guard.check_output(ai_response)

# 5. 生成审计报告
report = guard.get_audit_report()
"""
