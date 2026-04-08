# Agent Employee System - 智能体员工系统

## Overview

This document defines all AI agent employees in the Multi-Agent System. Each agent is a specialized employee with defined responsibilities, capabilities, and collaboration patterns.

---

## Agent Employees

### 1. Dev Agent (开发工程师)

**Agent ID:** `dev`
**Class:** `DevAgent`
**File:** `agents/dev_agent/dev_agent.py`

**Responsibilities:**
- Code generation from requirements
- Code review and optimization
- Module implementation
- Technical design
- Bug diagnosis and fixes

**Specialties:** Python, FastAPI, LangChain, System Design

**Capabilities:**
```
- generate_code(description, language)
- review_code(code)
- fix_bug(description)
- refactor_code(code, target_style)
- suggest_architecture(requirements)
```

**Task Types Handled:**
- `CODE_GENERATION`
- `CODE_REVIEW`
- `BUG_FIX`
- `REFACTOR`
- `ARCHITECTURE`

**Usage Example:**
```python
from agents.dev_agent import dev_agent
result = await dev_agent.generate_code(
    description="Write a hello world function",
    language="python"
)
```

---

### 2. Test Agent (测试工程师)

**Agent ID:** `test`
**Class:** `TestAgent`
**File:** `agents/test_agent/test_agent.py`

**Responsibilities:**
- Unit test generation
- Integration test design
- Regression test suites
- Test report generation
- Code coverage analysis

**Specialties:** pytest, unittest, coverage.py, test design patterns

**Capabilities:**
```
- generate_unit_tests(code, language)
- generate_integration_tests(components)
- analyze_coverage(test_results)
- generate_test_report()
- create_regression_suite(changes)
```

**Test Types Handled:**
- `UNIT` - Unit tests
- `INTEGRATION` - Integration tests
- `E2E` - End-to-end tests
- `PERFORMANCE` - Performance tests
- `SECURITY` - Security tests

**Usage Example:**
```python
from agents.test_agent import test_agent
result = await test_agent.generate_unit_tests(
    code="def add(a, b): return a + b",
    language="python"
)
```

---

### 3. Doc Agent (文档工程师)

**Agent ID:** `doc`
**Class:** `DocAgent`
**File:** `agents/doc_agent/doc_agent.py`

**Responsibilities:**
- Project documentation creation
- API documentation generation
- Technical design documents
- User manuals
- Changelog maintenance

**Specialties:** Markdown, OpenAPI/Swagger, technical writing

**Capabilities:**
```
- generate_readme(project_name, description, features)
- generate_api_doc(endpoints)
- generate_technical_design(architecture)
- generate_user_guide(features)
- update_changelog(changes)
```

**Doc Types Handled:**
- `README` - Project README
- `API_DOC` - API documentation
- `TECHNICAL_DESIGN` - Technical design doc
- `USER_GUIDE` - User manual
- `CHANGELOG` - Change log
- `ARCHITECTURE` - Architecture diagram/spec

**Usage Example:**
```python
from agents.doc_agent import doc_agent
result = await doc_agent.generate_readme(
    project_name="MyProject",
    description="A test project",
    features=["Feature 1", "Feature 2"]
)
```

---

### 4. RAG Agent (知识库工程师)

**Agent ID:** `rag`
**Class:** `RAGAgent`
**File:** `agents/rag_agent/rag_agent.py`

**Responsibilities:**
- Knowledge base management
- Document indexing
- Semantic search
- Context-aware retrieval
- Vector store administration

**Specialties:** ChromaDB, embeddings, semantic search, LangChain

**Capabilities:**
```
- query(question, session_id, use_knowledge)
- add_document(content, metadata)
- create_knowledge_base(name, documents)
- search_knowledge(query, top_k)
- index_documents(documents)
```

**Usage Example:**
```python
from agents.rag_agent import rag_agent
result = await rag_agent.query(
    question="What is RAG?",
    session_id="session_123",
    use_knowledge=True
)
```

---

### 5. PM Agent (项目经理)

**Agent ID:** `pm`
**Class:** `PMAgent`
**File:** `agents/pm_agent/pm_agent.py`

**Responsibilities:**
- Project progress tracking
- Milestone management
- Risk identification
- Report generation
- Task coordination

**Specialties:** Project management, agile methodologies, risk analysis

**Capabilities:**
```
- create_task(title, description, priority)
- update_task_progress(task_id, progress)
- get_progress()
- identify_risks()
- generate_report()
- manage_milestone()
```

**Task Status:**
- `PENDING`
- `IN_PROGRESS`
- `COMPLETED`
- `BLOCKED`
- `CANCELLED`

**Usage Example:**
```python
from agents.pm_agent import pm_agent
result = pm_agent.create_task(
    title="Implement login feature",
    description="Add OAuth2 login",
    priority="high"
)
```

---

### 6. Ops Agent (运维工程师)

**Agent ID:** `ops`
**Class:** `OpsAgent`
**File:** `agents/ops_agent/ops_agent.py`

**Responsibilities:**
- Deployment automation
- Monitoring management
- Log analysis
- Infrastructure configuration
- Alert response
- Rollback operations

**Specialties:** Docker, Kubernetes, CI/CD, Linux, Nginx, Prometheus, Grafana

**Capabilities:**
```
- deploy(environment, version, deployment_type)
- rollback(deployment_id)
- check_health(service_name)
- analyze_logs(log_content, time_range)
- configure_infrastructure()
- scale_service(service_name, replicas)
```

**Deployment Types:**
- `blue_green` - Blue-green deployment
- `rolling` - Rolling update
- `canary` - Canary release

**Environments:**
- `development`
- `staging`
- `production`

**Usage Example:**
```python
from agents.ops_agent import ops_agent
result = await ops_agent.deploy(
    environment="production",
    version="v1.2.3",
    deployment_type="rolling"
)
```

---

### 7. Conversation Agent (对话工程师)

**Agent ID:** `conversation`
**Class:** `ConversationAgent`
**File:** `agents/conversation_agent/conversation_agent.py`

**Responsibilities:**
- User conversation management
- Session state maintenance
- Context preservation
- Intent detection
- Response generation

**Specialties:** Conversation design, context management, intent classification

**Capabilities:**
```
- send_message(session_id, message, role)
- get_conversation_history(session_id, limit)
- summarize_conversation(session_id)
- detect_intent(message)
- create_session(user_id)
```

**Usage Example:**
```python
from agents.conversation_agent import conversation_agent
result = await conversation_agent.send_message(
    session_id="session_123",
    message="Hello!",
    role=MessageRole.USER
)
```

---

## Agent Orchestration

### Task Router

The `TaskRouter` automatically routes tasks to the appropriate agent based on task description analysis.

**File:** `agents/orchestrator/task_router.py`

```python
from agents.orchestrator.task_router import task_router

result = await task_router.execute_task(
    "Write a hello world function in Python"
)
# Automatically routes to Dev Agent

result = await task_router.execute_task(
    "Generate unit tests for my code"
)
# Automatically routes to Test Agent
```

### Task Type Mapping

| Task Keywords | Agent | Task Type |
|--------------|-------|-----------|
| code, implement, function, 开发 | dev | CODE |
| test, verify, 验证 | test | TEST |
| doc, readme, 文档 | doc | DOCUMENT |
| knowledge, search, 知识 | rag | KNOWLEDGE |
| project, task, milestone, 项目 | pm | PROJECT |
| deploy, infrastructure, 部署 | ops | OPS |
| chat, message, 对话 | conversation | CONVERSATION |

---

## Agent Collaboration

### Multi-Agent Workflows

**Code Development Flow:**
```
User Request → Dev Agent (generate code)
                    ↓
              Test Agent (generate tests)
                    ↓
              Doc Agent (generate docs)
                    ↓
                 PM Agent (track task)
```

**Deployment Flow:**
```
Deploy Request → Ops Agent (deploy)
                      ↓
              Monitoring (health check)
                      ↓
              Ops Agent (rollback if needed)
```

**RAG Query Flow:**
```
User Query → Conversation Agent (route)
                  ↓
            RAG Agent (retrieve + generate)
                  ↓
            Conversation Agent (format response)
```

---

## Result Validation

All agent outputs pass through `ResultValidator` to ensure quality:

```python
from agents.orchestrator.result_validator import validate_agent_result

validation = validate_agent_result("dev_agent", {"code": generated_code})
# Returns: is_valid, quality, score, issues, suggestions
```

**Validation Criteria:**
- Output completeness
- Format correctness
- Quality score threshold
- Issue detection

---

## API Endpoints

| Endpoint | Method | Agent | Description |
|----------|--------|-------|-------------|
| `/api/agents/dev/generate` | POST | Dev | Generate code |
| `/api/agents/dev/review` | POST | Dev | Review code |
| `/api/agents/test/generate-unit-tests` | POST | Test | Generate tests |
| `/api/agents/doc/generate-readme` | POST | Doc | Generate README |
| `/api/agents/doc/generate-api-doc` | POST | Doc | Generate API docs |
| `/api/agents/route` | POST | Router | Auto-route task |
| `/api/agents/status` | GET | All | List agent status |
| `/api/tasks/` | CRUD | PM | Manage tasks |

---

## Adding New Agents

To add a new agent:

1. Create agent module: `agents/<agent_name>/<agent_name>.py`
2. Define agent class with `get_capabilities()` method
3. Register in `TaskRouter.agents` dict
4. Add API routes in `api/routes/agents.py`
5. Update this document

**Template:**

```python
class NewAgent:
    def __init__(self):
        self.name = "New Agent"

    def get_capabilities(self) -> Dict:
        return {
            "name": self.name,
            "type": "new",
            "capabilities": [...]
        }
```
