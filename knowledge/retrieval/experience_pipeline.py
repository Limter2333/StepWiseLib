"""
完美体验管道 - Perfect Experience Pipeline
==========================================

【设计理念】
让用户感受到"懂我"的服务体验：
1. 理解用户真实意图（不仅是字面）
2. 感知情感倾向（积极/消极/中性）
3. 记住对话历史（上下文连贯）
4. 提供个性化响应（因人而异）

【核心流程】
用户查询 → 意图识别 → 知识检索 → 个性化生成 → 情感反馈
"""

from __future__ import annotations

from typing import Dict, List, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import json

# 延迟导入避免循环依赖
if TYPE_CHECKING:
    from .multi_tenant_knowledge import (
        MultiTenantKnowledgeBase,
        SearchResult,
    )
    from .multi_tenant_intent import (
        IntentType,
        Intent,
        Sentiment,
        ConversationContext,
        IntentRecognitionPipeline,
        TaskRouter,
    )

# 运行时导入
def _get_kb():
    from .multi_tenant_knowledge import get_multi_tenant_kb
    return get_multi_tenant_kb()

def _get_intent_recognizer():
    from .multi_tenant_intent import get_intent_recognizer
    return get_intent_recognizer()

def _get_task_router():
    from .multi_tenant_intent import TaskRouter
    return TaskRouter()

# 导出Sentiment供直接模块加载使用
from .multi_tenant_intent import Sentiment


class ResponseStyle(Enum):
    """响应风格"""
    FORMAL = "formal"           # 正式专业
    FRIENDLY = "friendly"      # 友好亲切
    BRIEF = "brief"            # 简洁明了
    DETAILED = "detailed"      # 详细全面


@dataclass
class UserProfile:
    """用户画像"""
    tenant_id: str
    user_id: Optional[str] = None
    preferred_style: "ResponseStyle" = ResponseStyle.FRIENDLY
    language: str = "zh"
    sentiment_history: List["Sentiment"] = field(default_factory=list)


@dataclass
class ExperienceResult:
    """完美体验结果"""
    success: bool
    intent: "Intent"
    search_results: List["SearchResult"]
    response: str
    sentiment: "Sentiment"
    context_updated: bool
    metadata: Dict = field(default_factory=dict)


class PerfectExperiencePipeline:
    """完美体验管道

    【核心价值】
    1. 意图理解 → 知道用户想要什么
    2. 知识检索 → 提供准确答案
    3. 情感感知 → 调整响应方式
    4. 上下文记忆 → 连续对话如流水
    """

    def __init__(
        self,
        knowledge_base: "Optional[MultiTenantKnowledgeBase]" = None,
        intent_recognizer: "Optional[IntentRecognitionPipeline]" = None
    ):
        # 知识库 - 使用延迟导入
        self.kb = knowledge_base or _get_kb()

        # 意图识别器 - 使用延迟导入
        self.intent_recognizer = intent_recognizer or _get_intent_recognizer()

        # 任务路由器 - 使用延迟导入
        self.task_router = _get_task_router()

        # 用户画像存储
        self.user_profiles: Dict[str, UserProfile] = {}

        # 响应模板
        self._init_response_templates()

    def _init_response_templates(self):
        """初始化响应模板"""
        self.templates = {
            # 知识问答类
            IntentType.INQUIRY: {
                ResponseStyle.FRIENDLY: "您好！我帮您找到了相关信息：\n\n{content}\n\n希望对您有帮助~",
                ResponseStyle.FORMAL: "根据检索结果，回复如下：\n\n{content}",
                ResponseStyle.BRIEF: "{content}",
                ResponseStyle.DETAILED: "以下是详细说明：\n\n{content}\n\n如需了解更多，请随时提问。"
            },
            # 任务执行类
            IntentType.TASK_EXECUTION: {
                ResponseStyle.FRIENDLY: "好的，我来帮您处理！\n\n{content}\n\n已完成，请确认结果是否满意~",
                ResponseStyle.FORMAL: "任务已执行，结果如下：\n\n{content}",
                ResponseStyle.BRIEF: "{content}",
                ResponseStyle.DETAILED: "任务执行详情：\n\n{content}\n\n执行状态：成功"
            },
            # 文档管理类
            IntentType.DOCUMENT_MANAGEMENT: {
                ResponseStyle.FRIENDLY: "文档操作已完成！\n\n{content}\n\n需要我帮您做其他的吗~",
                ResponseStyle.FORMAL: "文档管理操作结果：\n\n{content}",
                ResponseStyle.BRIEF: "{content}",
                ResponseStyle.DETAILED: "文档管理详情：\n\n{content}\n\n相关操作已记录。"
            },
            # 闲聊类
            IntentType.CONVERSATION: {
                ResponseStyle.FRIENDLY: "嗨！很高兴和您聊天~\n\n{content}",
                ResponseStyle.FORMAL: "您好，有什么可以帮您的？\n\n{content}",
                ResponseStyle.BRIEF: "{content}",
                ResponseStyle.DETAILED: "您好！\n\n{content}\n\n请问还有其他需要吗？"
            },
            # 问候类
            IntentType.GREETING: {
                ResponseStyle.FRIENDLY: "您好！很高兴见到您！有什么我可以帮您的吗？",
                ResponseStyle.FORMAL: "您好，欢迎使用智能服务系统。",
                ResponseStyle.BRIEF: "您好！",
                ResponseStyle.DETAILED: "您好！欢迎回来！我是您的智能助手，可以为您提供知识问答、任务执行、文档管理等多种服务。请问有什么可以帮助您的？"
            },
            # 感谢类
            IntentType.THANKS: {
                ResponseStyle.FRIENDLY: "不客气！很高兴能帮到您~ 有需要随时找我哦！",
                ResponseStyle.FORMAL: "感谢您的反馈，如有需要请随时联系。",
                ResponseStyle.BRIEF: "不客气！",
                ResponseStyle.DETAILED: "不客气！很高兴能为您提供帮助。如果您有任何其他问题，欢迎随时提问。"
            },
            # 告别类
            IntentType.GOODBYE: {
                ResponseStyle.FRIENDLY: "再见啦！祝您有美好的一天~ 随时欢迎回来！",
                ResponseStyle.FORMAL: "再见，感谢使用本系统。",
                ResponseStyle.BRIEF: "再见！",
                ResponseStyle.DETAILED: "再见！感谢您的使用。如果您需要任何帮助，请随时回来。祝您一切顺利！"
            },
            # 需求澄清类
            IntentType.CLARIFICATION: {
                ResponseStyle.FRIENDLY: "让我进一步了解您的需求：\n\n{content}\n\n请告诉我更多细节，我来帮您~",
                ResponseStyle.FORMAL: "请提供更多细节以便准确响应：\n\n{content}",
                ResponseStyle.BRIEF: "{content}",
                ResponseStyle.DETAILED: "为了更好地帮助您，请提供以下信息：\n\n{content}\n\n您的详细描述将帮助我给出更准确的答案。"
            },
            # 未知类
            IntentType.UNKNOWN: {
                ResponseStyle.FRIENDLY: "抱歉，我不太理解您的意思...\n\n{content}\n\n请您换个方式描述，或者告诉我您想做什么？",
                ResponseStyle.FORMAL: "无法理解当前请求，请重新描述：\n\n{content}",
                ResponseStyle.BRIEF: "{content}",
                ResponseStyle.DETAILED: "抱歉，我未能理解您的问题。\n\n{content}\n\n建议：\n1. 尝试使用不同的词语描述\n2. 明确说明您需要的帮助类型\n3. 如需帮助，可以询问【如何使用】获取操作指南"
            }
        }

    def get_or_create_profile(
        self,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> UserProfile:
        """获取或创建用户画像"""
        profile_key = f"{tenant_id}:{user_id or 'anonymous'}"

        if profile_key not in self.user_profiles:
            self.user_profiles[profile_key] = UserProfile(
                tenant_id=tenant_id,
                user_id=user_id
            )

        return self.user_profiles[profile_key]

    def _format_search_results(
        self,
        results: List["SearchResult"],
        style: "ResponseStyle"
    ) -> str:
        """格式化搜索结果"""
        if not results:
            return "抱歉，暂未找到相关信息。"

        if style == ResponseStyle.BRIEF:
            # 简洁模式：只返回第一条
            return results[0].content[:200] + "..."

        formatted_parts = []
        for i, result in enumerate(results[:3], 1):  # 最多3条
            source = result.metadata.get("source", "未知来源")
            score = result.score

            part = f"【结果{i}】(相关度: {score:.2f})\n"
            part += f"来源: {source}\n"
            part += f"内容: {result.content[:300]}"

            if len(result.content) > 300:
                part += "..."

            formatted_parts.append(part)

        return "\n\n".join(formatted_parts)

    def _generate_response(
        self,
        intent: Intent,
        search_results: List[SearchResult],
        profile: UserProfile
    ) -> str:
        """生成个性化响应"""
        # 获取对应意图的模板
        template_dict = self.templates.get(
            intent.intent_type,
            self.templates[IntentType.UNKNOWN]
        )

        # 根据用户风格选择模板
        template = template_dict.get(
            profile.preferred_style,
            template_dict[ResponseStyle.FRIENDLY]
        )

        # 格式化搜索结果
        content = self._format_search_results(
            search_results,
            profile.preferred_style
        )

        return template.format(content=content)

    def process(
        self,
        query: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 5
    ) -> ExperienceResult:
        """处理用户查询 - 完美体验入口

        Args:
            query: 用户查询
            tenant_id: 租户ID（必须）
            user_id: 用户ID（可选）
            session_id: 会话ID（可选，用于上下文追踪）
            top_k: 返回结果数量

        Returns:
            ExperienceResult: 完美体验结果
        """
        # 1. 获取用户画像
        profile = self.get_or_create_profile(tenant_id, user_id)

        # 2. 如果没有session_id，生成一个
        if not session_id:
            session_id = f"{tenant_id}:{user_id or 'anonymous'}:{hash(query) % 10000}"

        # 3. 意图识别
        intent = self.intent_recognizer.recognize(
            query=query,
            session_id=session_id,
            user_id=user_id
        )

        # 4. 根据意图类型决定下一步
        if intent.intent_type in [IntentType.GREETING, IntentType.GOODBYE,
                                    IntentType.THANKS, IntentType.CHITCHAT]:
            # 这些类型不需要知识检索
            search_results = []
            response = self._generate_response(intent, search_results, profile)

            # 更新情感历史
            sentiment = Sentiment(intent.metadata.get("sentiment", "neutral"))
            profile.sentiment_history.append(sentiment)

            return ExperienceResult(
                success=True,
                intent=intent,
                search_results=[],
                response=response,
                sentiment=sentiment,
                context_updated=True,
                metadata={"intent_type": intent.intent_type.value}
            )

        # 5. 需要知识检索的意图
        if intent.intent_type in [IntentType.INQUIRY, IntentType.DOCUMENT_MANAGEMENT,
                                    IntentType.TASK_EXECUTION]:
            try:
                search_results = self.kb.hybrid_search(
                    tenant_id=tenant_id,
                    query=query,
                    top_k=top_k
                )
            except Exception as e:
                search_results = []
        else:
            search_results = []

        # 6. 生成响应
        response = self._generate_response(intent, search_results, profile)

        # 7. 更新情感历史
        sentiment = Sentiment(intent.metadata.get("sentiment", "neutral"))
        profile.sentiment_history.append(sentiment)

        return ExperienceResult(
            success=True,
            intent=intent,
            search_results=search_results,
            response=response,
            sentiment=sentiment,
            context_updated=True,
            metadata={
                "intent_type": intent.intent_type.value,
                "confidence": intent.confidence,
                "result_count": len(search_results)
            }
        )

    def set_user_style(
        self,
        tenant_id: str,
        user_id: Optional[str],
        style: ResponseStyle
    ):
        """设置用户偏好风格"""
        profile = self.get_or_create_profile(tenant_id, user_id)
        profile.preferred_style = style

    def get_user_history(
        self,
        tenant_id: str,
        user_id: Optional[str]
    ) -> List[Intent]:
        """获取用户对话历史"""
        session_id = f"{tenant_id}:{user_id or 'anonymous'}"
        context = self.intent_recognizer.get_context(session_id)

        if context:
            return context.history

        return []


# 全局实例
_experience_pipeline: Optional[PerfectExperiencePipeline] = None


def get_experience_pipeline() -> PerfectExperiencePipeline:
    """获取完美体验管道实例"""
    global _experience_pipeline
    if _experience_pipeline is None:
        _experience_pipeline = PerfectExperiencePipeline()
    return _experience_pipeline


# ========== 使用示例 ==========
"""
【完美体验流程】

# 1. 获取体验管道
pipeline = get_experience_pipeline()

# 2. 注册租户（首次使用）
kb = get_multi_tenant_kb()
kb.register_tenant("tenant_001", "客户A公司")
kb.add_shared_document(title="产品手册", content="通用产品说明...")
kb.add_private_document("tenant_001", title="内部文档", content="...")

# 3. 处理用户查询
result = pipeline.process(
    query="如何配置产品？",
    tenant_id="tenant_001",
    user_id="user_123",
    session_id="session_001"
)

print(f"意图: {result.intent.intent_type.value}")
print(f"情感: {result.sentiment.value}")
print(f"响应: {result.response}")
print(f"结果数: {len(result.search_results)}")

# 4. 个性化设置
pipeline.set_user_style(
    tenant_id="tenant_001",
    user_id="user_123",
    style=ResponseStyle.FORMAL
)

# 5. 多轮对话
result2 = pipeline.process(
    query="支持哪些格式？",
    tenant_id="tenant_001",
    user_id="user_123",
    session_id="session_001"  # 同一会话，上下文连贯
)

# 6. 获取历史
history = pipeline.get_user_history("tenant_001", "user_123")
print(f"历史对话数: {len(history)}")
"""
