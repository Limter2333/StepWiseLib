# AI Multi-Agent System

面向客户的AI产品，支持多智能体协作、RAG知识库、记忆管理系统。

## 项目概述

### 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 框架 | LangChain + LangGraph | 智能体编排 |
| RAG | ChromaDB + Milvus | 向量数据库 |
| 文档解析 | PyPDF2 + python-docx + crawl4ai | PDF/Word/网页 |
| API | FastAPI | 服务框架 |
| 前端 | 原生HTML/CSS/JS | Liquid Glass风格 |
| 部署 | Docker | 容器化 |

### 智能体团队 (18个)

| 智能体 | 职责 |
|--------|------|
| **Orchestrator** | 核心调度、任务路由 |
| **Dev Agent** | 技术开发、代码生成 |
| **Test Agent** | 测试验证、单元测试生成 |
| **Doc Agent** | 文档生成、API文档 |
| **RAG Agent** | 知识库构建、语义检索 |
| **PM Agent** | 项目管理、任务跟踪 |
| **Senior PM Agent** | 战略规划、干系人管理 |
| **Conversation Agent** | 对话交互、意图识别 |
| **Ops Agent** | 运维部署、监控日志 |
| **Backend Architect** | 系统设计、数据库设计 |
| **Frontend Developer** | 前端开发、响应式布局 |
| **Code Reviewer** | 代码审查、安全扫描 |
| **UI Designer** | 组件设计、设计系统 |
| **Technical Writer** | 技术文档、用户手册 |
| **Product Manager** | 需求分析、用户故事 |
| **Reality Checker** | 事实核查、可行性评估 |
| **API Tester** | 端点测试、契约测试 |
| **Workflow Optimizer** | 流程优化、瓶颈识别 |

---

## 快速开始

### 方式一：Docker部署（推荐）

#### 1. 安装Docker Desktop

**Windows:**
1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 运行安装程序（需要WSL2支持）
3. 启动Docker Desktop
4. 等待任务栏图标显示"Docker Desktop is running"

**验证安装:**
```bash
docker --version
docker-compose --version
```

#### 2. 启动所有服务

```bash
# 进入docker目录
cd G:/claude_code_project/docker

# 启动所有服务（Milvus + Redis + API）
docker-compose up -d

# 查看服务状态
docker-compose ps
```

#### 3. 访问服务

| 服务 | 地址 |
|------|------|
| API文档 | http://localhost:8000/docs |
| Milvus Attu (可视化) | http://localhost:3000 |
| Redis Commander | http://localhost:8081 |

#### 4. 停止服务

```bash
docker-compose down
```

---

### 方式二：本地开发

#### 1. 创建虚拟环境

```bash
cd G:/claude_code_project

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

#### 4. 运行应用

```bash
# 启动API服务
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 或运行demo
python demo.py
```

#### 5. 访问文档

- API文档: http://localhost:8000/docs
- 替代文档: http://localhost:8000/redoc

---

## 核心功能

### P0 - 必须交付
- [x] **单元测试** - 1428个测试用例，98%通过率
- [x] **LLM实际调用** - MiniMax Provider正常工作
- [x] **API端点** - 98个REST端点

### P1 - 应该交付
- [x] **重排序模块** - BM25/CrossEncoder/Hybrid/MMR/RRF多策略
- [x] **混合检索** - RRF/Weighted/Concat融合
- [x] **意图识别** - 44个测试，精准分类

### P2 - 可选交付
- [x] **14种文档格式** - PDF/Word/Excel/PPT/HTML/Markdown等
- [x] **Agent协作** - 共享上下文、任务编排
- [x] **监控指标** - Prometheus格式导出

---

## 高级特性

### 安全与稳定
- [x] **Guardrails** - 输入输出安全检查、XSS/SQL防护
- [x] **限流器** - 令牌桶 + 滑动窗口、IP/API Key追踪
- [x] **熔断器** - CLOSED/OPEN/HALF_OPEN状态机
- [x] **重试策略** - 指数退避 + 抖动
- [x] **JWT认证** - Bearer Token、创建/验证/过期处理
- [x] **密钥管理** - 加密存储、密钥轮换、审计日志
- [x] **客户端配额** - 日/月/年周期、白名单豁免

### RAG知识增强
- [x] **多跳推理** - 问题分解、链式/并行/树形推理
- [x] **查询缓存** - 内存+持久化多级存储、TTL过期
- [x] **输入验证** - 查询/文档/Chunk三级验证
- [x] **流式美化** - Markdown识别、代码块缓冲

### 监控与告警
- [x] **智能告警** - 阈值聚合、冷却抑制、多渠道分发
- [x] **Webhook通知** - 异步投递、HMAC签名、指数重试
- [x] **事件通知** - EventBus发布订阅、WebSocket集成
- [x] **使用统计** - Token消耗、延迟百分位、成本估算
- [x] **审计日志** - JSON结构化日志、敏感操作记录

### 前端体验
- [x] **Liquid Glass UI** - 玻璃态界面、流畅动画
- [x] **骨架屏** - shimmer动画、优雅加载
- [x] **Toast通知** - 4种类型、自动消失
- [x] **API演示** - 在线测试、完整文档

---

## 项目结构

```
ai-agent-system/
├── agents/                      # 18个AI Agent
│   ├── dev_agent/              # 代码开发
│   ├── test_agent/             # 测试生成
│   ├── doc_agent/              # 文档生成
│   ├── rag_agent/             # 知识库
│   ├── pm_agent/              # 项目管理
│   ├── conversation_agent/    # 对话
│   ├── ops_agent/             # 运维
│   ├── backend_architect/    # 架构设计
│   ├── frontend_developer/     # 前端开发
│   ├── code_reviewer/         # 代码审查
│   ├── ui_designer/           # UI设计
│   ├── technical_writer/      # 技术写作
│   ├── product_manager/       # 产品经理
│   ├── reality_checker/       # 现实核查
│   ├── api_tester/            # API测试
│   ├── workflow_optimizer/    # 流程优化
│   ├── senior_pm_agent/       # 高级PM
│   └── orchestrator/          # 任务路由
├── api/                        # FastAPI服务
│   └── routes/                # API路由 (98端点)
├── core/                       # 核心模块
│   ├── guardrails.py         # 安全防护
│   ├── token_manager.py      # Token管理
│   ├── rate_limiter.py       # 限流控制
│   ├── circuit_breaker.py    # 熔断器
│   ├── retry_policy.py       # 重试策略
│   ├── response_cache.py     # RAG缓存
│   ├── rag_validator.py      # RAG验证
│   ├── stream_beautifier.py  # 流式美化
│   ├── client_quota.py       # 配额管理
│   ├── key_manager.py        # 密钥管理
│   ├── smart_alert.py       # 智能告警
│   ├── webhook.py            # Webhook
│   └── event_system.py       # 事件通知
├── knowledge/                  # 知识库
│   ├── parsers/             # 14种文档解析器
│   ├── vectorstore/         # 向量存储
│   ├── retrieval/            # 检索模块
│   │   ├── reranker.py    # 重排序
│   │   ├── hybrid_search.py # 混合检索
│   │   └── multi_tenant_intent.py # 意图识别
│   ├── rag_pipeline.py     # RAG管道
│   └── multihop_reasoner.py # 多跳推理
├── web/                       # 前端UI
│   └── index.html          # Liquid Glass界面
├── docker/                    # Docker配置
├── tests/                     # 测试用例 (63文件, 1428测试)
├── docs/                      # 文档
└── README.md                 # 本文件
```

---

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块
pytest tests/test_reranker.py -v
pytest tests/test_hybrid_search.py -v
pytest tests/test_intent_recognition.py -v

# 运行Agent测试
pytest tests/test_dev_agent.py tests/test_test_agent.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

**测试结果: 1420 passed, 8 skipped, 1 warning**

---

## API文档

完整API文档: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

### 主要端点

| 分类 | 端点数 | 示例 |
|------|--------|------|
| Chat | 12 | POST /api/chat/chat |
| RAG | 10 | POST /api/rag/query |
| Agent | 40+ | POST /api/agents/route |
| Monitoring | 10+ | GET /api/monitoring/metrics |
| MCP | 6 | POST /api/mcp/context/add |

---

## 配置说明

### 环境变量 (.env)

```bash
# LLM配置
LLM_PROVIDER=minimax
ANTHROPIC_API_KEY=your_api_key_here

# 向量数据库
CHROMA_PERSIST_DIR=./data/chromadb

# RAG配置
RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.5
```

---

## 开发指南

### 添加新Agent

1. 创建Agent目录: `agents/<agent_name>/`
2. 实现Agent类:
```python
class NewAgent:
    def __init__(self):
        self.name = "New Agent"
        self.specialty = ["..."]
    
    def get_capabilities(self):
        return {"name": self.name, ...}
```

3. 注册到TaskRouter `agents/orchestrator/task_router.py`
4. 添加API路由 `api/routes/agents.py`
5. 编写测试 `tests/test_<agent_name>.py`

### 添加新文档解析器

1. 继承BaseParser:
```python
class NewParser(BaseParser):
    def parse(self, file_path) -> List[Document]:
        # 实现解析逻辑
        pass
```

2. 注册到 `knowledge/parsers/__init__.py`

---

## 项目统计

| 指标 | 数值 |
|------|------|
| 代码文件 | 600+ |
| 测试文件 | 63 |
| 测试用例 | 1428 |
| API端点 | 98 |
| Agent数量 | 18 |
| 文档格式 | 14种 |
| 代码覆盖率 | ~85% |

---

## 文档

- [产品规范](PRODUCT.md) - 产品愿景与约束
- [Agent系统](AGENTS.md) - Agent员工定义
- [API参考](docs/API_REFERENCE.md) - 完整API文档
- [项目总结](PROJECT_SUMMARY.md) - 开发演进
- [开发日志](DEVELOPMENT_LOG.md) - 每日进度

---

## 许可证

MIT License

---

## 致谢

- [LangChain](https://langchain.com/) - Agent框架
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [FastAPI](https://fastapi.tiangolo.com/) - API框架
- [MiniMax](https://www.minimax.io/) - LLM Provider
