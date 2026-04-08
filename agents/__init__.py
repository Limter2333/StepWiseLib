# Agents Module - Complete Agent Employee System
# 13 Agent Employees

# Original 6 Agents
from .dev_agent import dev_agent, DevAgent
from .doc_agent import doc_agent, DocAgent
from .test_agent import test_agent, TestAgent
from .rag_agent import rag_agent, RAGAgent
from .pm_agent import pm_agent, PMAgent
from .conversation_agent import conversation_agent, ConversationAgent

# Additional Agents
from .senior_pm_agent import senior_pm_agent, SeniorPMAgent
from .ops_agent import ops_agent, OpsAgent
from .evaluator_agent import evaluator_agent, EvaluatorAgent

# New 9 Agents (temporary disabled - need class exports)
# from .frontend_developer import frontend_developer, FrontendDeveloper
# from .backend_architect import backend_architect, BackendArchitect
# from .technical_writer import technical_writer, TechnicalWriter
# from .code_reviewer import code_reviewer, CodeReviewer
# from .ui_designer import ui_designer, UIDesigner
# from .product_manager import product_manager, ProductManager
# from .reality_checker import reality_checker, RealityChecker
# from .api_tester import api_tester, APITester
# from .workflow_optimizer import workflow_optimizer, WorkflowOptimizer

# Orchestrator
from .orchestrator.agent_manager import agent_registry, workflow

__all__ = [
    # Original 6
    "dev_agent", "DevAgent",
    "doc_agent", "DocAgent",
    "test_agent", "TestAgent",
    "rag_agent", "RAGAgent",
    "pm_agent", "PMAgent",
    "conversation_agent", "ConversationAgent",
    # Additional 3
    "senior_pm_agent", "SeniorPMAgent",
    "ops_agent", "OpsAgent",
    "evaluator_agent", "EvaluatorAgent",
    # New 9 (disabled - need class exports)
    # "frontend_developer", "FrontendDeveloper",
    # "backend_architect", "BackendArchitect",
    # "technical_writer", "TechnicalWriter",
    # "code_reviewer", "CodeReviewer",
    # "ui_designer", "UIDesigner",
    # "product_manager", "ProductManager",
    # "reality_checker", "RealityChecker",
    # "api_tester", "APITester",
    # "workflow_optimizer", "WorkflowOptimizer",
    # Orchestrator
    "agent_registry",
    "workflow",
]
