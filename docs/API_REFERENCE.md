# API Reference - AI Multi-Agent System

## Base URL
```
http://localhost:8000
```

---

## Health Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/health/` | GET | Basic health check |
| `/health/ping` | GET | Ping check |
| `/health/uptime` | GET | Uptime statistics |
| `/health/ready` | GET | Readiness check |
| `/health/stats` | GET | System statistics |

---

## Chat Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/chat/chat` | POST | Send chat message |
| `/api/chat/chat/stream` | POST | Stream chat response |
| `/api/chat/sessions` | POST | Create session |
| `/api/chat/sessions` | GET | List sessions |
| `/api/chat/sessions/{id}` | GET | Get session |
| `/api/chat/sessions/{id}/history` | GET | Get history |
| `/api/chat/sessions/{id}/summary` | GET | Get summary |
| `/api/chat/sessions/{id}` | DELETE | Delete session |
| `/api/chat/sessions/{id}/token-usage` | GET | Token usage |
| `/api/chat/intent/detect` | POST | Detect intent |
| `/api/chat/token-usage` | GET | Token usage stats |
| `/api/chat/token-usage/reset` | POST | Reset token usage |

---

## RAG Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/rag/documents` | POST | Upload document |
| `/api/rag/documents` | GET | List documents |
| `/api/rag/query` | POST | Query knowledge base |
| `/api/rag/stats` | GET | RAG statistics |
| `/api/rag/multihop` | POST | Multi-hop reasoning |
| `/api/rag/multihop/decompose` | POST | Decompose question |
| `/api/rag/cache/stats` | GET | Cache statistics |
| `/api/rag/cache/clear` | POST | Clear cache |
| `/api/rag/documents/{id}` | GET | Get document |
| `/api/rag/documents/{id}` | DELETE | Delete document |

---

## Agent Endpoints

### Status & Routing
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/agents/status` | GET | All agent status |
| `/api/agents/route` | POST | Route task to agent |
| `/api/agents/context/set` | POST | Set context |
| `/api/agents/context/get` | GET | Get context |
| `/api/agents/context/delete` | DELETE | Delete context |
| `/api/agents/context/keys` | GET | List context keys |
| `/api/agents/context/all` | GET | Get all contexts |
| `/api/agents/context/clear` | DELETE | Clear contexts |
| `/api/agents/context/stats` | GET | Context statistics |

### Dev Agent
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/agents/dev/generate` | POST | Generate code |
| `/api/agents/dev/review` | POST | Review code |

### Doc Agent
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/agents/doc/generate-readme` | POST | Generate README |
| `/api/agents/doc/generate-api-doc` | POST | Generate API doc |

### Test Agent
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/agents/test/generate-unit-tests` | POST | Generate unit tests |

### PM Agent
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/agents/pm/create-task` | POST | Create task |
| `/api/agents/pm/tasks` | GET | List tasks |
| `/api/agents/pm/report` | GET | PM report |

### Senior PM Agent
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/agents/senior-pm/report` | GET | Senior PM report |
| `/api/agents/senior-pm/sprint` | POST | Create sprint |
| `/api/agents/senior-pm/stakeholder` | POST | Add stakeholder |
| `/api/agents/senior-pm/risk` | POST | Report risk |
| `/api/agents/senior-pm/strategy` | POST | Create strategy |

### RAG Agent
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/agents/rag/create-kb` | POST | Create knowledge base |
| `/api/agents/rag/knowledge-bases` | GET | List knowledge bases |

### Collaboration
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/agents/collaborate/submit` | POST | Submit task |
| `/api/agents/collaborate/report` | GET | Collaboration report |
| `/api/agents/collaborate/{task_id}` | GET | Get task result |

---

## Monitoring Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/monitoring/usage/total` | GET | Total usage |
| `/api/monitoring/usage/endpoints` | GET | Per-endpoint usage |
| `/api/monitoring/usage/session/{id}` | GET | Session usage |
| `/api/monitoring/usage/record` | POST | Record usage |
| `/api/monitoring/usage/clear` | POST | Clear usage |
| `/api/monitoring/cost/estimate` | GET | Cost estimate |
| `/api/monitoring/metrics` | GET | Prometheus metrics |

---

## MCP Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/mcp/context/add` | POST | Add context |
| `/api/mcp/context/stats` | GET | Context stats |
| `/api/mcp/context/segments` | GET | List segments |
| `/api/mcp/context/content` | GET | Get content |
| `/api/mcp/context/clear` | POST | Clear context |
| `/api/mcp/context/compress` | POST | Compress context |

---

## WebSocket

| Endpoint | Description |
|---------|-------------|
| `/ws` | WebSocket connection for real-time updates |

---

## Task Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/tasks/` | GET | List tasks |
| `/api/tasks/` | POST | Create task |
| `/api/tasks/{id}` | GET | Get task |
| `/api/tasks/{id}` | PUT | Update task |
| `/api/tasks/{id}` | DELETE | Delete task |

---

## Request/Response Examples

### Chat Request
```json
POST /api/chat/chat
{
    "message": "Hello, how can you help me?",
    "session_id": "optional-session-id",
    "use_knowledge": true
}
```

### Chat Response
```json
{
    "response": "Hello! I can help you with...",
    "sources": ["doc1.pdf", "doc2.txt"],
    "tokens_used": 150,
    "session_id": "sess_123"
}
```

### Intent Detection
```json
POST /api/chat/intent/detect
{
    "message": "Write a function to add numbers"
}
```

### Response
```json
{
    "intent": "code_generation",
    "entities": {"language": "python"},
    "confidence": 0.95,
    "suggested_action": "route_to_dev"
}
```

---

## Error Responses

| Status Code | Description |
|------------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing auth |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource missing |
| 429 | Too Many Requests - Rate limited |
| 500 | Internal Server Error |

```json
{
    "error": "error_type",
    "message": "Human readable message",
    "details": {}
}
```

---

## Rate Limits

| Tier | Requests/Minute | Requests/Hour |
|------|----------------|---------------|
| Default | 60 | 1000 |
| Premium | 300 | 10000 |

---

**Last Updated:** 2026-04-09
