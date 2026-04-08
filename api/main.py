"""
FastAPI 主入口
==============

【学习要点】
1. FastAPI核心概念
   - 异步: async/await
   - 路径参数: /items/{item_id}
   - 查询参数: /items?skip=0&limit=10
   - 请求体: Pydantic模型验证

2. 为什么要用FastAPI?
   - 高性能: 异步非阻塞
   - 自动文档: /docs 自动生成Swagger UI
   - 类型安全: Pydantic数据验证
   - 简单易用: 装饰器语法
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from contextlib import asynccontextmanager
import sys
import os
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from logs.error_logs.error_logger import error_logger, ErrorLevel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理

    【学习要点】 lifespan上下文管理器
    - 启动时: 执行初始化
    - 关闭时: 执行清理
    """
    print(f"[Startup] {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"[Startup] Debug mode: {settings.DEBUG}")

    # 初始化向量数据库连接
    try:
        from knowledge.vectorstore.chromadb_handler import ChromaDBHandler
        vectorstore = ChromaDBHandler()
        stats = vectorstore.get_collection_stats()
        print(f"[Startup] VectorDB initialized: {stats['name']} ({stats['count']} docs)")
    except Exception as e:
        print(f"[Startup] VectorDB init warning: {e}")

    # 初始化Agent调度器
    try:
        from agents.orchestrator.task_router import task_router
        agents = task_router.list_agents()
        print(f"[Startup] Agent scheduler ready: {len(agents)} agents loaded")
    except Exception as e:
        print(f"[Startup] Agent scheduler init warning: {e}")

    # 预热RAG管道
    try:
        from knowledge.rag_pipeline import RAGPipeline
        rag = RAGPipeline()
        print("[Startup] RAG pipeline ready")
    except Exception as e:
        print(f"[Startup] RAG pipeline init warning: {e}")

    yield

    # 清理
    print("[Shutdown] Cleaning up...")
    # 清理MCP中间件的session缓存
    from core.mcp_middleware import MCPContextMiddleware
    MCPContextMiddleware.clear_all()
    print("[Shutdown] MCP sessions cleared")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-Agent AI System with RAG and Memory",
    lifespan=lifespan,
    redirect_slashes=True
)

# CORS中间件 - 生产环境应通过CORS_ORIGINS环境变量限制
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Session-ID", "X-API-Key"],
)

# Request ID 中间件 - 为每个请求添加唯一ID用于追踪
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """为每个请求添加唯一ID，用于日志追踪"""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# MCP上下文中间件
from core.mcp_middleware import MCPContextMiddleware
app.add_middleware(MCPContextMiddleware, max_tokens=4000)

# 限流中间件
from core.rate_limit_middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)


# ========== 路由导入 ==========
from api.routes import rag, chat, agents, health, mcp, websocket, monitoring, tasks


# ========== 路由注册 ==========
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(mcp.router, prefix="/api/mcp", tags=["MCP"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(tasks.router, tags=["Tasks"])
app.include_router(websocket.router, tags=["WebSocket"])

# 挂载静态文件 - 修复路径问题
web_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
if os.path.exists(web_path):
    # 只挂载 /src/pages 路径，避免与API路由冲突
    pages_path = os.path.join(web_path, "src", "pages")
    if os.path.exists(pages_path):
        app.mount("/src/pages", StaticFiles(directory=pages_path, html=True), name="pages")


# ========== 根路由 ==========
@app.get("/")
async def root():
    """根路径"""
    web_index = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index.html")
    if os.path.exists(web_index):
        return FileResponse(web_index)
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/planB")
async def planB():
    """Plan B UI"""
    planB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planB.html")
    if os.path.exists(planB_path):
        return FileResponse(planB_path)
    raise HTTPException(status_code=404, detail="Plan B not found")


@app.get("/planC")
async def planC():
    """Plan C UI - Stealth Wealth Luxury Tech"""
    planC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planC.html")
    if os.path.exists(planC_path):
        return FileResponse(planC_path)
    raise HTTPException(status_code=404, detail="Plan C not found")


@app.get("/planD")
async def planD():
    """Plan D UI - Stealth Wealth Theme + Editorial Layout"""
    planD_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planD.html")
    if os.path.exists(planD_path):
        return FileResponse(planD_path)
    raise HTTPException(status_code=404, detail="Plan D not found")


@app.get("/planE")
async def planE():
    """Plan E UI - Brutalist Tech (Raw Power)"""
    planE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planE.html")
    if os.path.exists(planE_path):
        return FileResponse(planE_path)
    raise HTTPException(status_code=404, detail="Plan E not found")


@app.get("/planF")
async def planF():
    """Plan F UI - Organic Futurism (Flowing Curves, Natural Gradients)"""
    planF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planF.html")
    if os.path.exists(planF_path):
        return FileResponse(planF_path)
    raise HTTPException(status_code=404, detail="Plan F not found")


@app.get("/planG")
async def planG():
    """Plan G UI - Retro Terminal (80s CRT Green Screen)"""
    planG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planG.html")
    if os.path.exists(planG_path):
        return FileResponse(planG_path)
    raise HTTPException(status_code=404, detail="Plan G not found")


@app.get("/planH")
async def planH():
    """Plan H UI - Glass Morphism (Frosted Glass, Translucent Layers)"""
    planH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planH.html")
    if os.path.exists(planH_path):
        return FileResponse(planH_path)
    raise HTTPException(status_code=404, detail="Plan H not found")


@app.get("/planI")
async def planI():
    """Plan I UI - Neo-Brutalist (Bold Type, High Contrast, Raw Geometry)"""
    planI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planI.html")
    if os.path.exists(planI_path):
        return FileResponse(planI_path)
    raise HTTPException(status_code=404, detail="Plan I not found")


@app.get("/planJ")
async def planJ():
    """Plan J UI - Midnight Corporate (Deep Navy + Gold Executive)"""
    planJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planJ.html")
    if os.path.exists(planJ_path):
        return FileResponse(planJ_path)
    raise HTTPException(status_code=404, detail="Plan J not found")


@app.get("/planK")
async def planK():
    """Plan K UI - Sakura Ethereal (Japanese Wabi-Sabi, Falling Petals)"""
    planK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planK.html")
    if os.path.exists(planK_path):
        return FileResponse(planK_path)
    raise HTTPException(status_code=404, detail="Plan K not found")


@app.get("/planL")
async def planL():
    """Plan L UI - Cyberpunk Noir (Neon Glitch, Hacking Interface)"""
    planL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planL.html")
    if os.path.exists(planL_path):
        return FileResponse(planL_path)
    raise HTTPException(status_code=404, detail="Plan L not found")


@app.get("/planM")
async def planM():
    """Plan M UI - Art Deco Glamour (Gold Geometric, Jazz Age)"""
    planM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planM.html")
    if os.path.exists(planM_path):
        return FileResponse(planM_path)
    raise HTTPException(status_code=404, detail="Plan M not found")


@app.get("/planN")
async def planN():
    """Plan N UI - Nordic Minimal (Scandinavian, Form Follows Function)"""
    planN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planN.html")
    if os.path.exists(planN_path):
        return FileResponse(planN_path)
    raise HTTPException(status_code=404, detail="Plan N not found")


@app.get("/planO")
async def planO():
    """Plan O UI - Vaporwave Dreams (90s Internet, Chrome Gradients)"""
    planO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planO.html")
    if os.path.exists(planO_path):
        return FileResponse(planO_path)
    raise HTTPException(status_code=404, detail="Plan O not found")


@app.get("/planP")
async def planP():
    """Plan P UI - Bauhaus Digital (Geometric, Form Follows Function)"""
    planP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planP.html")
    if os.path.exists(planP_path):
        return FileResponse(planP_path)
    raise HTTPException(status_code=404, detail="Plan P not found")


@app.get("/planQ")
async def planQ():
    """Plan Q UI - Synthwave Sunset (Retro Futurism, Neon Grid)"""
    planQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planQ.html")
    if os.path.exists(planQ_path):
        return FileResponse(planQ_path)
    raise HTTPException(status_code=404, detail="Plan Q not found")


@app.get("/planR")
async def planR():
    """Plan R UI - Glitch Core (Digital Corruption, Error Aesthetics)"""
    planR_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planR.html")
    if os.path.exists(planR_path):
        return FileResponse(planR_path)
    raise HTTPException(status_code=404, detail="Plan R not found")


@app.get("/planS")
async def planS():
    """Plan S UI - Soft Glam (Soft Gradients, Pastel Palette, Gentle Motion)"""
    planS_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planS.html")
    if os.path.exists(planS_path):
        return FileResponse(planS_path)
    raise HTTPException(status_code=404, detail="Plan S not found")


@app.get("/planT")
async def planT():
    """Plan T UI - Kinetic Concrete (Motion-Driven, Dynamic Typography)"""
    planT_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planT.html")
    if os.path.exists(planT_path):
        return FileResponse(planT_path)
    raise HTTPException(status_code=404, detail="Plan T not found")


@app.get("/planU")
async def planU():
    """Plan U UI - Dark Atelier (High Fashion, Editorial Minimal)"""
    planU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planU.html")
    if os.path.exists(planU_path):
        return FileResponse(planU_path)
    raise HTTPException(status_code=404, detail="Plan U not found")


@app.get("/planV")
async def planV():
    """Plan V UI - Vapor Spirit (Ethereal Vaporwave, Soft Glow)"""
    planV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planV.html")
    if os.path.exists(planV_path):
        return FileResponse(planV_path)
    raise HTTPException(status_code=404, detail="Plan V not found")


@app.get("/planW")
async def planW():
    """Plan W UI - Noir Circuit (Circuit Traces, Tech Noird)"""
    planW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planW.html")
    if os.path.exists(planW_path):
        return FileResponse(planW_path)
    raise HTTPException(status_code=404, detail="Plan W not found")


@app.get("/planX")
async def planX():
    """Plan X UI - Space Cosmic (Deep Space, Nebula, Star Particles)"""
    planX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planX.html")
    if os.path.exists(planX_path):
        return FileResponse(planX_path)
    raise HTTPException(status_code=404, detail="Plan X not found")


@app.get("/planY")
async def planY():
    """Plan Y UI - Paper Cutout (Layered Paper, Craft Art, Soft Shadows)"""
    planY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planY.html")
    if os.path.exists(planY_path):
        return FileResponse(planY_path)
    raise HTTPException(status_code=404, detail="Plan Y not found")


@app.get("/planZ")
async def planZ():
    """Plan Z UI - Glitch Core (Digital Corruption, RGB Split, Error Aesthetics)"""
    planZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planZ.html")
    if os.path.exists(planZ_path):
        return FileResponse(planZ_path)
    raise HTTPException(status_code=404, detail="Plan Z not found")


@app.get("/planAA")
async def planAA():
    """Plan AA UI - Soft Glam (Soft Gradients, Rose Gold, Luxury Pastels)"""
    planAA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAA.html")
    if os.path.exists(planAA_path):
        return FileResponse(planAA_path)
    raise HTTPException(status_code=404, detail="Plan AA not found")


@app.get("/planAB")
async def planAB():
    """Plan AB UI - Kinetic Concrete (Motion-Driven, Dynamic Typography, Bold Impact)"""
    planAB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAB.html")
    if os.path.exists(planAB_path):
        return FileResponse(planAB_path)
    raise HTTPException(status_code=404, detail="Plan AB not found")


@app.get("/planAC")
async def planAC():
    """Plan AC UI - Dark Atelier (High Fashion, Editorial Minimal, Art Gallery)"""
    planAC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAC.html")
    if os.path.exists(planAC_path):
        return FileResponse(planAC_path)
    raise HTTPException(status_code=404, detail="Plan AC not found")


@app.get("/planAD")
async def planAD():
    """Plan AD UI - Vapor Spirit (Ethereal Vaporwave, Pink Mist, Dreamy Glow)"""
    planAD_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAD.html")
    if os.path.exists(planAD_path):
        return FileResponse(planAD_path)
    raise HTTPException(status_code=404, detail="Plan AD not found")


@app.get("/planAE")
async def planAE():
    """Plan AE UI - Noir Circuit (Circuit Traces, Cyber Noir, Neon Pulse)"""
    planAE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAE.html")
    if os.path.exists(planAE_path):
        return FileResponse(planAE_path)
    raise HTTPException(status_code=404, detail="Plan AE not found")


@app.get("/planAF")
async def planAF():
    """Plan AF UI - Pixel Nostalgia (8-bit, Retro Games, NES Colors)"""
    planAF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAF.html")
    if os.path.exists(planAF_path):
        return FileResponse(planAF_path)
    raise HTTPException(status_code=404, detail="Plan AF not found")


@app.get("/planAG")
async def planAG():
    """Plan AG UI - Liquid Glass (Flowing Glass, Organic Curves, Water Dynamics)"""
    planAG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAG.html")
    if os.path.exists(planAG_path):
        return FileResponse(planAG_path)
    raise HTTPException(status_code=404, detail="Plan AG not found")


@app.get("/planAH")
async def planAH():
    """Plan AH UI - Aurora Borealis (Northern Lights, Flowing Colors, Ice Crystal)"""
    planAH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAH.html")
    if os.path.exists(planAH_path):
        return FileResponse(planAH_path)
    raise HTTPException(status_code=404, detail="Plan AH not found")


@app.get("/planAI")
async def planAI():
    """Plan AI UI - Bauhaus Revival (Geometric, Primary Colors, Functionalism)"""
    planAI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAI.html")
    if os.path.exists(planAI_path):
        return FileResponse(planAI_path)
    raise HTTPException(status_code=404, detail="Plan AI not found")


@app.get("/planAJ")
async def planAJ():
    """Plan AJ UI - Holographic Future (Iridescent, Rainbow, Metallic Sheen)"""
    planAJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAJ.html")
    if os.path.exists(planAJ_path):
        return FileResponse(planAJ_path)
    raise HTTPException(status_code=404, detail="Plan AJ not found")


@app.get("/planAK")
async def planAK():
    """Plan AK UI - Ancient Temple (Chinese Classical, Ink Wash, Temple Patterns)"""
    planAK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAK.html")
    if os.path.exists(planAK_path):
        return FileResponse(planAK_path)
    raise HTTPException(status_code=404, detail="Plan AK not found")


@app.get("/planAL")
async def planAL():
    """Plan AL UI - Art Nouveau Organic (Curves, Vine Patterns, Natural Growth)"""
    planAL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAL.html")
    if os.path.exists(planAL_path):
        return FileResponse(planAL_path)
    raise HTTPException(status_code=404, detail="Plan AL not found")


@app.get("/planAM")
async def planAM():
    """Plan AM UI - Dystopian Tech (Rust, Surveillance, Authoritarian)"""
    planAM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAM.html")
    if os.path.exists(planAM_path):
        return FileResponse(planAM_path)
    raise HTTPException(status_code=404, detail="Plan AM not found")


@app.get("/planAN")
async def planAN():
    """Plan AN UI - Sakura Dream (Japanese Cherry Blossoms, Spring Romance)"""
    planAN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAN.html")
    if os.path.exists(planAN_path):
        return FileResponse(planAN_path)
    raise HTTPException(status_code=404, detail="Plan AN not found")


@app.get("/planAO")
async def planAO():
    """Plan AO UI - Jungle Safari (Wild Forest, Animal Prints, Expedition)"""
    planAO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAO.html")
    if os.path.exists(planAO_path):
        return FileResponse(planAO_path)
    raise HTTPException(status_code=404, detail="Plan AO not found")


@app.get("/planAP")
async def planAP():
    """Plan AP UI - Midnight Gothic (Dark Rose, Gothic Type, Blood Red)"""
    planAP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAP.html")
    if os.path.exists(planAP_path):
        return FileResponse(planAP_path)
    raise HTTPException(status_code=404, detail="Plan AP not found")


@app.get("/planAQ")
async def planAQ():
    """Plan AQ UI - Retro Diner (50s Americana, Neon Signs, Chrome)"""
    planAQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAQ.html")
    if os.path.exists(planAQ_path):
        return FileResponse(planAQ_path)
    raise HTTPException(status_code=404, detail="Plan AQ not found")


@app.get("/planAR")
async def planAR():
    """Plan AR UI - Minimal Zen Garden (Japanese Raked Sand, Stone, Moss)"""
    planAR_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAR.html")
    if os.path.exists(planAR_path):
        return FileResponse(planAR_path)
    raise HTTPException(status_code=404, detail="Plan AR not found")


@app.get("/planAS")
async def planAS():
    """Plan AS UI - Bioluminescent Ocean (Deep Sea Glow, Glowing Creatures)"""
    planAS_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAS.html")
    if os.path.exists(planAS_path):
        return FileResponse(planAS_path)
    raise HTTPException(status_code=404, detail="Plan AS not found")


@app.get("/planAT")
async def planAT():
    """Plan AT UI - Moroccan Mosaic (Geometric Tiles, Islamic Patterns, Lanterns)"""
    planAT_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAT.html")
    if os.path.exists(planAT_path):
        return FileResponse(planAT_path)
    raise HTTPException(status_code=404, detail="Plan AT not found")


@app.get("/planAU")
async def planAU():
    """Plan AU UI - Matrix Digital (Code Rain, Cyberpunk, Green Terminal)"""
    planAU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAU.html")
    if os.path.exists(planAU_path):
        return FileResponse(planAU_path)
    raise HTTPException(status_code=404, detail="Plan AU not found")


@app.get("/planAV")
async def planAV():
    """Plan AV UI - Renaissance Portrait (Classical Oil, Gold Frames, Museum)"""
    planAV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAV.html")
    if os.path.exists(planAV_path):
        return FileResponse(planAV_path)
    raise HTTPException(status_code=404, detail="Plan AV not found")


@app.get("/planAW")
async def planAW():
    """Plan AW UI - Nordic Frost (Ice Crystal, Cold Tones, Minimal Geometry)"""
    planAW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAW.html")
    if os.path.exists(planAW_path):
        return FileResponse(planAW_path)
    raise HTTPException(status_code=404, detail="Plan AW not found")


@app.get("/planAX")
async def planAX():
    """Plan AX UI - Inca Gold (Ancient Gold, Sun Temple, Mystic Patterns)"""
    planAX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAX.html")
    if os.path.exists(planAX_path):
        return FileResponse(planAX_path)
    raise HTTPException(status_code=404, detail="Plan AX not found")


@app.get("/planAY")
async def planAY():
    """Plan AY UI - Abstract Expressionism (Bold Strokes, Splatter Art, Gallery Feel)"""
    planAY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAY.html")
    if os.path.exists(planAY_path):
        return FileResponse(planAY_path)
    raise HTTPException(status_code=404, detail="Plan AY not found")


@app.get("/planAZ")
async def planAZ():
    """Plan AZ UI - Cyberpunk Neon (Neon Lights, Rainy Streets, High Tech Low Life)"""
    planAZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planAZ.html")
    if os.path.exists(planAZ_path):
        return FileResponse(planAZ_path)
    raise HTTPException(status_code=404, detail="Plan AZ not found")


@app.get("/planBA")
async def planBA():
    """Plan BA UI - Botanical Illustration (Scientific Drawing, Aged Paper, Fine Lines)"""
    planBA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBA.html")
    if os.path.exists(planBA_path):
        return FileResponse(planBA_path)
    raise HTTPException(status_code=404, detail="Plan BA not found")


@app.get("/planBB")
async def planBB():
    """Plan BB UI - Constructivist (Russian Constructivism, Geometric, Revolutionary)"""
    planBB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBB.html")
    if os.path.exists(planBB_path):
        return FileResponse(planBB_path)
    raise HTTPException(status_code=404, detail="Plan BB not found")


@app.get("/planBC")
async def planBC():
    """Plan BC UI - Terracotta Warrior (Ancient China, Bronze, Imperial)"""
    planBC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBC.html")
    if os.path.exists(planBC_path):
        return FileResponse(planBC_path)
    raise HTTPException(status_code=404, detail="Plan BC not found")


@app.get("/planBD")
async def planBD():
    """Plan BD UI - Vaporwave Sunset (90s Internet, Pink Purple, Retro Future)"""
    planBD_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBD.html")
    if os.path.exists(planBD_path):
        return FileResponse(planBD_path)
    raise HTTPException(status_code=404, detail="Plan BD not found")


@app.get("/planBE")
async def planBE():
    """Plan BE UI - De Stijl (Primary Colors, Black Grid, Mondrian Modern)"""
    planBE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBE.html")
    if os.path.exists(planBE_path):
        return FileResponse(planBE_path)
    raise HTTPException(status_code=404, detail="Plan BE not found")


@app.get("/planBF")
async def planBF():
    """Plan BF UI - Isometric Minimal (2.5D Isometric, Geometric, 3D Blocks)"""
    planBF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBF.html")
    if os.path.exists(planBF_path):
        return FileResponse(planBF_path)
    raise HTTPException(status_code=404, detail="Plan BF not found")


@app.get("/planBG")
async def planBG():
    """Plan BG UI - Moroccan Night (Night Bazaar, Lantern Glow, Deep Purple)"""
    planBG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBG.html")
    if os.path.exists(planBG_path):
        return FileResponse(planBG_path)
    raise HTTPException(status_code=404, detail="Plan BG not found")


@app.get("/planBH")
async def planBH():
    """Plan BH UI - Nordic Midsummer (Golden Sun, White Night, Wildflowers)"""
    planBH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBH.html")
    if os.path.exists(planBH_path):
        return FileResponse(planBH_path)
    raise HTTPException(status_code=404, detail="Plan BH not found")


@app.get("/planBI")
async def planBI():
    """Plan BI UI - Edwardian Elegance (1900s Grace, Lace, Rose Garden)"""
    planBI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBI.html")
    if os.path.exists(planBI_path):
        return FileResponse(planBI_path)
    raise HTTPException(status_code=404, detail="Plan BI not found")


@app.get("/planBJ")
async def planBJ():
    """Plan BJ UI - Retro Arcade (80s Arcade, Neon Lights, Game Cabinet)"""
    planBJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBJ.html")
    if os.path.exists(planBJ_path):
        return FileResponse(planBJ_path)
    raise HTTPException(status_code=404, detail="Plan BJ not found")


@app.get("/planBK")
async def planBK():
    """Plan BK UI - Art Deco Glamour (Jazz Age, Gold Geometry, Empire State)"""
    planBK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBK.html")
    if os.path.exists(planBK_path):
        return FileResponse(planBK_path)
    raise HTTPException(status_code=404, detail="Plan BK not found")


@app.get("/planBL")
async def planBL():
    """Plan BL UI - Ancient Egyptian (Pyramid, Hieroglyphs, Desert Dusk)"""
    planBL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBL.html")
    if os.path.exists(planBL_path):
        return FileResponse(planBL_path)
    raise HTTPException(status_code=404, detail="Plan BL not found")


@app.get("/planBM")
async def planBM():
    """Plan BM UI - Kawaii Tech (Pink Tech, Cute Electronics, Soft Neon)"""
    planBM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBM.html")
    if os.path.exists(planBM_path):
        return FileResponse(planBM_path)
    raise HTTPException(status_code=404, detail="Plan BM not found")


@app.get("/planBN")
async def planBN():
    """Plan BN UI - Victorian Steampunk (Industrial Revolution, Gears, Copper Pipes)"""
    planBN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBN.html")
    if os.path.exists(planBN_path):
        return FileResponse(planBN_path)
    raise HTTPException(status_code=404, detail="Plan BN not found")


@app.get("/planBO")
async def planBO():
    """Plan BO UI - Prehistoric Earth (Dino Era, Fossils, Volcanic Landscapes)"""
    planBO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBO.html")
    if os.path.exists(planBO_path):
        return FileResponse(planBO_path)
    raise HTTPException(status_code=404, detail="Plan BO not found")


@app.get("/planBP")
async def planBP():
    """Plan BP UI - Art Nouveau Floral (Lily, Vine, Organic Curves)"""
    planBP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBP.html")
    if os.path.exists(planBP_path):
        return FileResponse(planBP_path)
    raise HTTPException(status_code=404, detail="Plan BP not found")


@app.get("/planBQ")
async def planBQ():
    """Plan BQ UI - Synthwave Horizon (Neon Horizon, Palm Silhouettes, Retro Future)"""
    planBQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBQ.html")
    if os.path.exists(planBQ_path):
        return FileResponse(planBQ_path)
    raise HTTPException(status_code=404, detail="Plan BQ not found")


@app.get("/planBR")
async def planBR():
    """Plan BR UI - Silk Road (Desert Caravans, Jade, Sand Dunes)"""
    planBR_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBR.html")
    if os.path.exists(planBR_path):
        return FileResponse(planBR_path)
    raise HTTPException(status_code=404, detail="Plan BR not found")


@app.get("/planBS")
async def planBS():
    """Plan BS UI - Retro Diner 50s (Checkerboard, Chrome, Red Booth)"""
    planBS_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBS.html")
    if os.path.exists(planBS_path):
        return FileResponse(planBS_path)
    raise HTTPException(status_code=404, detail="Plan BS not found")


@app.get("/planBT")
async def planBT():
    """Plan BT UI - Midnight Jazz (Jazz Bar, Smoke, Saxophone Silhouettes)"""
    planBT_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBT.html")
    if os.path.exists(planBT_path):
        return FileResponse(planBT_path)
    raise HTTPException(status_code=404, detail="Plan BT not found")


@app.get("/planBU")
async def planBU():
    """Plan BU UI - Nordic Wood (Scandinavian, Wood Textures, Nature Minimal)"""
    planBU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBU.html")
    if os.path.exists(planBU_path):
        return FileResponse(planBU_path)
    raise HTTPException(status_code=404, detail="Plan BU not found")


@app.get("/planBV")
async def planBV():
    """Plan BV UI - Baroque Opulence (Luxury Gold, Scrollwork, Royal Purple)"""
    planBV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBV.html")
    if os.path.exists(planBV_path):
        return FileResponse(planBV_path)
    raise HTTPException(status_code=404, detail="Plan BV not found")


@app.get("/planBW")
async def planBW():
    """Plan BW UI - Ancient Greek (Classical Columns, Mythology, Marble)"""
    planBW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBW.html")
    if os.path.exists(planBW_path):
        return FileResponse(planBW_path)
    raise HTTPException(status_code=404, detail="Plan BW not found")


@app.get("/planBX")
async def planBX():
    """Plan BX UI - Retro TV Static (CRT TV, Static Noise, Distortion)"""
    planBX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBX.html")
    if os.path.exists(planBX_path):
        return FileResponse(planBX_path)
    raise HTTPException(status_code=404, detail="Plan BX not found")


@app.get("/planBY")
async def planBY():
    """Plan BY UI - Submarine Depth (Deep Sea, Instruments, Naval)"""
    planBY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBY.html")
    if os.path.exists(planBY_path):
        return FileResponse(planBY_path)
    raise HTTPException(status_code=404, detail="Plan BY not found")


@app.get("/planBZ")
async def planBZ():
    """Plan BZ UI - Martian Colony (Red Planet, Terraforming, Survival)"""
    planBZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planBZ.html")
    if os.path.exists(planBZ_path):
        return FileResponse(planBZ_path)
    raise HTTPException(status_code=404, detail="Plan BZ not found")


@app.get("/planCA")
async def planCA():
    """Plan CA UI - Parisian Boutique (French Fashion, Elegant Pink, Stone Textures)"""
    planCA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCA.html")
    if os.path.exists(planCA_path):
        return FileResponse(planCA_path)
    raise HTTPException(status_code=404, detail="Plan CA not found")


@app.get("/planCB")
async def planCB():
    """Plan CB UI - Woodland Craft (Wood Art, Forest Green, Warm Light)"""
    planCB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCB.html")
    if os.path.exists(planCB_path):
        return FileResponse(planCB_path)
    raise HTTPException(status_code=404, detail="Plan CB not found")


@app.get("/planCC")
async def planCC():
    """Plan CC UI - Art Moderne (1930s Streamline, Ocean Liner, Cinema)"""
    planCC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCC.html")
    if os.path.exists(planCC_path):
        return FileResponse(planCC_path)
    raise HTTPException(status_code=404, detail="Plan CC not found")


@app.get("/planCD")
async def planCD():
    """Plan CD UI - Jungle Canopy (Tropical Rainforest, Dappled Light, Hanging Vines)"""
    planCD_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCD.html")
    if os.path.exists(planCD_path):
        return FileResponse(planCD_path)
    raise HTTPException(status_code=404, detail="Plan CD not found")


@app.get("/planCE")
async def planCE():
    """Plan CE UI - Space Station (ISS, Instrument Panels, Zero Gravity)"""
    planCE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCE.html")
    if os.path.exists(planCE_path):
        return FileResponse(planCE_path)
    raise HTTPException(status_code=404, detail="Plan CE not found")


@app.get("/planCF")
async def planCF():
    """Plan CF UI - Japanese Woodblock (Hokusai Waves, Sakura, Ukiyo-e)"""
    planCF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCF.html")
    if os.path.exists(planCF_path):
        return FileResponse(planCF_path)
    raise HTTPException(status_code=404, detail="Plan CF not found")


@app.get("/planCG")
async def planCG():
    """Plan CG UI - Alpine Chalet (Mountain Cabin, Wood Panels, Snow)"""
    planCG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCG.html")
    if os.path.exists(planCG_path):
        return FileResponse(planCG_path)
    raise HTTPException(status_code=404, detail="Plan CG not found")


@app.get("/planCH")
async def planCH():
    """Plan CH UI - Cyberpunk Corporate (Corporate Dystopia, Neon Skyscrapers)"""
    planCH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCH.html")
    if os.path.exists(planCH_path):
        return FileResponse(planCH_path)
    raise HTTPException(status_code=404, detail="Plan CH not found")


@app.get("/planCI")
async def planCI():
    """Plan CI UI - Desert Oasis (Golden Sand, Palm Trees, Blue Water)"""
    planCI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCI.html")
    if os.path.exists(planCI_path):
        return FileResponse(planCI_path)
    raise HTTPException(status_code=404, detail="Plan CI not found")


@app.get("/planCJ")
async def planCJ():
    """Plan CJ UI - Bioluminescent Forest (Night Forest, Glowing Mushrooms)"""
    planCJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCJ.html")
    if os.path.exists(planCJ_path):
        return FileResponse(planCJ_path)
    raise HTTPException(status_code=404, detail="Plan CJ not found")


@app.get("/planCK")
async def planCK():
    """Plan CK UI - Retro Polaroid (Instant Photos, Soft Tones, Paper Frames)"""
    planCK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCK.html")
    if os.path.exists(planCK_path):
        return FileResponse(planCK_path)
    raise HTTPException(status_code=404, detail="Plan CK not found")


@app.get("/planCL")
async def planCL():
    """Plan CL UI - Art Space Minimal (White Cube Gallery, Art Collection)"""
    planCL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCL.html")
    if os.path.exists(planCL_path):
        return FileResponse(planCL_path)
    raise HTTPException(status_code=404, detail="Plan CL not found")


@app.get("/planCM")
async def planCM():
    """Plan CM UI - Neon Noir (Rainy Neon, Detective Mystery, Future Crime)"""
    planCM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCM.html")
    if os.path.exists(planCM_path):
        return FileResponse(planCM_path)
    raise HTTPException(status_code=404, detail="Plan CM not found")


@app.get("/planCN")
async def planCN():
    """Plan CN UI - Highland Mist (Scottish Highlands, Whisky, Castle Silhouettes)"""
    planCN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCN.html")
    if os.path.exists(planCN_path):
        return FileResponse(planCN_path)
    raise HTTPException(status_code=404, detail="Plan CN not found")


@app.get("/planCO")
async def planCO():
    """Plan CO UI - Miami Vice Sunset (80s Sunshine, Pastel Sky, Neon Palms)"""
    planCO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCO.html")
    if os.path.exists(planCO_path):
        return FileResponse(planCO_path)
    raise HTTPException(status_code=404, detail="Plan CO not found")


@app.get("/planCP")
async def planCP():
    """Plan CP UI - Zen Garden Minimal (Raked Sand, Stone, Moss, Japanese Garden)"""
    planCP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCP.html")
    if os.path.exists(planCP_path):
        return FileResponse(planCP_path)
    raise HTTPException(status_code=404, detail="Plan CP not found")


@app.get("/planCQ")
async def planCQ():
    """Plan CQ UI - Sahara Dunes (Golden Sand, Caravan, Desert Oasis)"""
    planCQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCQ.html")
    if os.path.exists(planCQ_path):
        return FileResponse(planCQ_path)
    raise HTTPException(status_code=404, detail="Plan CQ not found")


@app.get("/planCR")
async def planCR():
    """Plan CR UI - Venetian Carnival (Masquerade, Gold Masks, Feathers)"""
    planCR_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCR.html")
    if os.path.exists(planCR_path):
        return FileResponse(planCR_path)
    raise HTTPException(status_code=404, detail="Plan CR not found")


@app.get("/planCS")
async def planCS():
    """Plan CS UI - Swiss Poster (Grid System, Helvetica, Swiss Minimal)"""
    planCS_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCS.html")
    if os.path.exists(planCS_path):
        return FileResponse(planCS_path)
    raise HTTPException(status_code=404, detail="Plan CS not found")


@app.get("/planCT")
async def planCT():
    """Plan CT UI - Victorian Library (Mahogany, Leather, Brass Accents)"""
    planCT_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCT.html")
    if os.path.exists(planCT_path):
        return FileResponse(planCT_path)
    raise HTTPException(status_code=404, detail="Plan CT not found")


@app.get("/planCU")
async def planCU():
    """Plan CU UI - Tokyo Underground (Neon Signs, Metro Map, Night Station)"""
    planCU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCU.html")
    if os.path.exists(planCU_path):
        return FileResponse(planCU_path)
    raise HTTPException(status_code=404, detail="Plan CU not found")


@app.get("/planCV")
async def planCV():
    """Plan CV UI - Parisian Art Nouveau (Belle Époque, Ironwork, Salon)"""
    planCV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCV.html")
    if os.path.exists(planCV_path):
        return FileResponse(planCV_path)
    raise HTTPException(status_code=404, detail="Plan CV not found")


@app.get("/planCW")
async def planCW():
    """Plan CW UI - Nordic Winter (Snow, Cabin, Aurora, Hygge)"""
    planCW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCW.html")
    if os.path.exists(planCW_path):
        return FileResponse(planCW_path)
    raise HTTPException(status_code=404, detail="Plan CW not found")


@app.get("/planCX")
async def planCX():
    """Plan CX UI - Aztec Revival (Sun Stone, Turquoise, Gold, Pyramid)"""
    planCX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCX.html")
    if os.path.exists(planCX_path):
        return FileResponse(planCX_path)
    raise HTTPException(status_code=404, detail="Plan CX not found")


@app.get("/planCY")
async def planCY():
    """Plan CY UI - Brazilian Carnival (Rainbow, Feathers, Samba, Rio)"""
    planCY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCY.html")
    if os.path.exists(planCY_path):
        return FileResponse(planCY_path)
    raise HTTPException(status_code=404, detail="Plan CY not found")


@app.get("/planCZ")
async def planCZ():
    """Plan CZ UI - Bauhaus Print (Letterpress, Geometric, Red Accents)"""
    planCZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planCZ.html")
    if os.path.exists(planCZ_path):
        return FileResponse(planCZ_path)
    raise HTTPException(status_code=404, detail="Plan CZ not found")


@app.get("/planDA")
async def planDA():
    """Plan DA UI - Brutalist Architecture (Concrete, Monumental, Raw)"""
    planDA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDA.html")
    if os.path.exists(planDA_path):
        return FileResponse(planDA_path)
    raise HTTPException(status_code=404, detail="Plan DA not found")


@app.get("/planDB")
async def planDB():
    """Plan DB UI - Art Deco Cinema (Velvet, Gold Leaf, Hollywood Glamour)"""
    planDB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDB.html")
    if os.path.exists(planDB_path):
        return FileResponse(planDB_path)
    raise HTTPException(status_code=404, detail="Plan DB not found")


@app.get("/planDC")
async def planDC():
    """Plan DC UI - Irish Pub (Stout, Wood, Fireplace, Shamrock)"""
    planDC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDC.html")
    if os.path.exists(planDC_path):
        return FileResponse(planDC_path)
    raise HTTPException(status_code=404, detail="Plan DC not found")


@app.get("/planDD")
async def planDD():
    """Plan DD UI - Holographic Minimal (Iridescent, Rainbow, Transparent Layers)"""
    planDD_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDD.html")
    if os.path.exists(planDD_path):
        return FileResponse(planDD_path)
    raise HTTPException(status_code=404, detail="Plan DD not found")


@app.get("/planDE")
async def planDE():
    """Plan DE UI - Vaporwave Sunset (90s Internet, Roman Statues, Grid Horizon)"""
    planDE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDE.html")
    if os.path.exists(planDE_path):
        return FileResponse(planDE_path)
    raise HTTPException(status_code=404, detail="Plan DE not found")


@app.get("/planDF")
async def planDF():
    """Plan DF UI - Kawaii Grunge (Pastel Pink, Ripped Black, Sticker Overlays)"""
    planDF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDF.html")
    if os.path.exists(planDF_path):
        return FileResponse(planDF_path)
    raise HTTPException(status_code=404, detail="Plan DF not found")


@app.get("/planDG")
async def planDG():
    """Plan DG UI - Memphis Design (80s Italy, Geometric Shapes, Bright Colors)"""
    planDG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDG.html")
    if os.path.exists(planDG_path):
        return FileResponse(planDG_path)
    raise HTTPException(status_code=404, detail="Plan DG not found")


@app.get("/planDH")
async def planDH():
    """Plan DH UI - Desert Mirage (Western, Cactus, Sunset, Tumbleweed)"""
    planDH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDH.html")
    if os.path.exists(planDH_path):
        return FileResponse(planDH_path)
    raise HTTPException(status_code=404, detail="Plan DH not found")


@app.get("/planDI")
async def planDI():
    """Plan DI UI - Nordic Midsummer (Sunshine, Flower Crowns, Midsummer Pole)"""
    planDI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDI.html")
    if os.path.exists(planDI_path):
        return FileResponse(planDI_path)
    raise HTTPException(status_code=404, detail="Plan DI not found")


@app.get("/planDJ")
async def planDJ():
    """Plan DJ UI - Art Nouveau Botanical (Lilies, Vines, Botanical Illustrations)"""
    planDJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDJ.html")
    if os.path.exists(planDJ_path):
        return FileResponse(planDJ_path)
    raise HTTPException(status_code=404, detail="Plan DJ not found")


@app.get("/planDK")
async def planDK():
    """Plan DK UI - Bauhaus Color Block (Primary Colors, Geometric, Modernist)"""
    planDK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDK.html")
    if os.path.exists(planDK_path):
        return FileResponse(planDK_path)
    raise HTTPException(status_code=404, detail="Plan DK not found")


@app.get("/planDL")
async def planDL():
    """Plan DL UI - Moroccan Tiles (Zellige, Geometric, Lantern Glow)"""
    planDL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDL.html")
    if os.path.exists(planDL_path):
        return FileResponse(planDL_path)
    raise HTTPException(status_code=404, detail="Plan DL not found")


@app.get("/planDM")
async def planDM():
    """Plan DM UI - Brutalist Noir (Film Noir + Brutalist Architecture)"""
    planDM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDM.html")
    if os.path.exists(planDM_path):
        return FileResponse(planDM_path)
    raise HTTPException(status_code=404, detail="Plan DM not found")


@app.get("/planDN")
async def planDN():
    """Plan DN UI - Tokyo Pop (Manga, Bubblegum, Action Lines)"""
    planDN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDN.html")
    if os.path.exists(planDN_path):
        return FileResponse(planDN_path)
    raise HTTPException(status_code=404, detail="Plan DN not found")


@app.get("/planDO")
async def planDO():
    """Plan DO UI - Swiss International (Modernist, Grid, Helvetica)"""
    planDO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDO.html")
    if os.path.exists(planDO_path):
        return FileResponse(planDO_path)
    raise HTTPException(status_code=404, detail="Plan DO not found")


@app.get("/planDP")
async def planDP():
    """Plan DP UI - Renaissance Digital (Oil Painting, Gold Frames, Perspective)"""
    planDP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDP.html")
    if os.path.exists(planDP_path):
        return FileResponse(planDP_path)
    raise HTTPException(status_code=404, detail="Plan DP not found")


@app.get("/planDQ")
async def planDQ():
    """Plan DQ UI - Glitch Noir (Digital Corruption + Cyberpunk Detective)"""
    planDQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDQ.html")
    if os.path.exists(planDQ_path):
        return FileResponse(planDQ_path)
    raise HTTPException(status_code=404, detail="Plan DQ not found")


@app.get("/planDR")
async def planDR():
    """Plan DR UI - Botanical Illustration (Scientific Drawing, Fine Lines, Aged Paper)"""
    planDR_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDR.html")
    if os.path.exists(planDR_path):
        return FileResponse(planDR_path)
    raise HTTPException(status_code=404, detail="Plan DR not found")


@app.get("/planDS")
async def planDS():
    """Plan DS UI - Minimalist Japanese (Wabi-Sabi, Ma, Generous Margins)"""
    planDS_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDS.html")
    if os.path.exists(planDS_path):
        return FileResponse(planDS_path)
    raise HTTPException(status_code=404, detail="Plan DS not found")


@app.get("/planDT")
async def planDT():
    """Plan DT UI - Synthwave Highway (80s Neon, Highway, Palm Trees)"""
    planDT_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDT.html")
    if os.path.exists(planDT_path):
        return FileResponse(planDT_path)
    raise HTTPException(status_code=404, detail="Plan DT not found")


@app.get("/planDU")
async def planDU():
    """Plan DU UI - Retro Arcade 80s (Pixel, Neon, Arcade Cabinet)"""
    planDU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDU.html")
    if os.path.exists(planDU_path):
        return FileResponse(planDU_path)
    raise HTTPException(status_code=404, detail="Plan DU not found")


@app.get("/planDV")
async def planDV():
    """Plan DV UI - Vaporwave Aesthetic (80s Internet, Greek Statues, Grid)"""
    planDV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDV.html")
    if os.path.exists(planDV_path):
        return FileResponse(planDV_path)
    raise HTTPException(status_code=404, detail="Plan DV not found")


@app.get("/planDW")
async def planDW():
    """Plan DW UI - Brutalist Tech Minimal (Terminal Green, Matrix, Hex Grid)"""
    planDW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDW.html")
    if os.path.exists(planDW_path):
        return FileResponse(planDW_path)
    raise HTTPException(status_code=404, detail="Plan DW not found")


@app.get("/planDX")
async def planDX():
    """Plan DX UI - Art Nouveau Whiplash (Gold, Lilies, Curved Lines)"""
    planDX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDX.html")
    if os.path.exists(planDX_path):
        return FileResponse(planDX_path)
    raise HTTPException(status_code=404, detail="Plan DX not found")


@app.get("/planDY")
async def planDY():
    """Plan DY UI - Kawaii Deco (Rose Gold, Geometric, Feminine Glamour)"""
    planDY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDY.html")
    if os.path.exists(planDY_path):
        return FileResponse(planDY_path)
    raise HTTPException(status_code=404, detail="Plan DY not found")


@app.get("/planDZ")
async def planDZ():
    """Plan DZ UI - Brutalist Corporate (Corporate Blue, Concrete, Power)"""
    planDZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planDZ.html")
    if os.path.exists(planDZ_path):
        return FileResponse(planDZ_path)
    raise HTTPException(status_code=404, detail="Plan DZ not found")


@app.get("/planEA")
async def planEA():
    """Plan EA UI - Scandinavian Midsummer (Flowers, Sunshine, Nordic Nature)"""
    planEA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEA.html")
    if os.path.exists(planEA_path):
        return FileResponse(planEA_path)
    raise HTTPException(status_code=404, detail="Plan EA not found")


@app.get("/planEB")
async def planEB():
    """Plan EB UI - Vaporwave Chrome (Chrome, Retrowave, Synth)"""
    planEB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEB.html")
    if os.path.exists(planEB_path):
        return FileResponse(planEB_path)
    raise HTTPException(status_code=404, detail="Plan EB not found")


@app.get("/planEC")
async def planEC():
    """Plan EC UI - Art Deco Luxe (Gold, Jazz Age, Empire State)"""
    planEC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEC.html")
    if os.path.exists(planEC_path):
        return FileResponse(planEC_path)
    raise HTTPException(status_code=404, detail="Plan EC not found")


@app.get("/planED")
async def planED():
    """Plan ED UI - Noir Circuit (Circuit Traces, Neon Glow, Dark Tech)"""
    planED_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planED.html")
    if os.path.exists(planED_path):
        return FileResponse(planED_path)
    raise HTTPException(status_code=404, detail="Plan ED not found")


@app.get("/planEE")
async def planEE():
    """Plan EE UI - Botanical Sci-Fi (Alien Plants, Bioluminescent, Space Garden)"""
    planEE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEE.html")
    if os.path.exists(planEE_path):
        return FileResponse(planEE_path)
    raise HTTPException(status_code=404, detail="Plan EE not found")


@app.get("/planEF")
async def planEF():
    """Plan EF UI - Victorian Steampunk (Gears, Brass, Victorian Industrial)"""
    planEF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEF.html")
    if os.path.exists(planEF_path):
        return FileResponse(planEF_path)
    raise HTTPException(status_code=404, detail="Plan EF not found")


@app.get("/planEG")
async def planEG():
    """Plan EG UI - Brutalist Paper (Paper Texture, Typewriter, Bureaucracy)"""
    planEG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEG.html")
    if os.path.exists(planEG_path):
        return FileResponse(planEG_path)
    raise HTTPException(status_code=404, detail="Plan EG not found")


@app.get("/planEH")
async def planEH():
    """Plan EH UI - Nordic Forest (Pine Trees, Moss, Midnight, Tranquil)"""
    planEH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEH.html")
    if os.path.exists(planEH_path):
        return FileResponse(planEH_path)
    raise HTTPException(status_code=404, detail="Plan EH not found")


@app.get("/planEI")
async def planEI():
    """Plan EI UI - Vaporwave Y2K (2000s, Chrome, Translucent, IE Browser)"""
    planEI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEI.html")
    if os.path.exists(planEI_path):
        return FileResponse(planEI_path)
    raise HTTPException(status_code=404, detail="Plan EI not found")


@app.get("/planEJ")
async def planEJ():
    """Plan EJ UI - Art Nouveau Mystical (Celestial, Zodiac, Stars, Mystical)"""
    planEJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEJ.html")
    if os.path.exists(planEJ_path):
        return FileResponse(planEJ_path)
    raise HTTPException(status_code=404, detail="Plan EJ not found")


@app.get("/planEK")
async def planEK():
    """Plan EK UI - Noir Photography (Black White, Film Grain, Street Photography)"""
    planEK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEK.html")
    if os.path.exists(planEK_path):
        return FileResponse(planEK_path)
    raise HTTPException(status_code=404, detail="Plan EK not found")


@app.get("/planEL")
async def planEL():
    """Plan EL UI - Kawaii Minimal (Soft Pastels, Rounded, Cozy Minimal)"""
    planEL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEL.html")
    if os.path.exists(planEL_path):
        return FileResponse(planEL_path)
    raise HTTPException(status_code=404, detail="Plan EL not found")


@app.get("/planEM")
async def planEM():
    """Plan EM UI - Swiss Modern (Modern Swiss, Red Accents, Precision Grid)"""
    planEM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEM.html")
    if os.path.exists(planEM_path):
        return FileResponse(planEM_path)
    raise HTTPException(status_code=404, detail="Plan EM not found")


@app.get("/planEN")
async def planEN():
    """Plan EN UI - Ancient Egyptian Revival (Pyramids, Hieroglyphs, Scarab, Lapis)"""
    planEN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEN.html")
    if os.path.exists(planEN_path):
        return FileResponse(planEN_path)
    raise HTTPException(status_code=404, detail="Plan EN not found")


@app.get("/planEO")
async def planEO():
    """Plan EO UI - Retro Terminal Green (CRT, Phosphor Green, Command Line)"""
    planEO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEO.html")
    if os.path.exists(planEO_path):
        return FileResponse(planEO_path)
    raise HTTPException(status_code=404, detail="Plan EO not found")


@app.get("/planEP")
async def planEP():
    """Plan EP UI - Kawaii Pastel Grunge (Soft Pastels, Grunge Textures)"""
    planEP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEP.html")
    if os.path.exists(planEP_path):
        return FileResponse(planEP_path)
    raise HTTPException(status_code=404, detail="Plan EP not found")


@app.get("/planEQ")
async def planEQ():
    """Plan EQ UI - Brutalist Neon (Neon Lights, Concrete, Power)"""
    planEQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEQ.html")
    if os.path.exists(planEQ_path):
        return FileResponse(planEQ_path)
    raise HTTPException(status_code=404, detail="Plan EQ not found")


@app.get("/planER")
async def planER():
    """Plan ER UI - Vaporwave Minimal (Pastel, Simplified, Geometric)"""
    planER_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planER.html")
    if os.path.exists(planER_path):
        return FileResponse(planER_path)
    raise HTTPException(status_code=404, detail="Plan ER not found")


@app.get("/planES")
async def planES():
    """Plan ES UI - Medieval Manuscript (Parchment, Illuminated, Gothic)"""
    planES_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planES.html")
    if os.path.exists(planES_path):
        return FileResponse(planES_path)
    raise HTTPException(status_code=404, detail="Plan ES not found")


@app.get("/planET")
async def planET():
    """Plan ET UI - Art Deco Linear (Linear Patterns, Stepped Forms, Gold)"""
    planET_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planET.html")
    if os.path.exists(planET_path):
        return FileResponse(planET_path)
    raise HTTPException(status_code=404, detail="Plan ET not found")


@app.get("/planEU")
async def planEU():
    """Plan EU UI - Glitch Minimal (Minimal + Digital Glitch, Subtle)"""
    planEU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEU.html")
    if os.path.exists(planEU_path):
        return FileResponse(planEU_path)
    raise HTTPException(status_code=404, detail="Plan EU not found")


@app.get("/planEV")
async def planEV():
    """Plan EV UI - Nordic Paper (Nordic Design, Paper Texture, Clean)"""
    planEV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEV.html")
    if os.path.exists(planEV_path):
        return FileResponse(planEV_path)
    raise HTTPException(status_code=404, detail="Plan EV not found")


@app.get("/planEW")
async def planEW():
    """Plan EW UI - Retro Diner 50s (Checkerboard, Chrome, Neon Signs)"""
    planEW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEW.html")
    if os.path.exists(planEW_path):
        return FileResponse(planEW_path)
    raise HTTPException(status_code=404, detail="Plan EW not found")


@app.get("/planEX")
async def planEX():
    """Plan EX UI - Cyberpunk Glitch (Cyberpunk + Digital Corruption)"""
    planEX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEX.html")
    if os.path.exists(planEX_path):
        return FileResponse(planEX_path)
    raise HTTPException(status_code=404, detail="Plan EX not found")


@app.get("/planEY")
async def planEY():
    """Plan EY UI - Steampunk Minimal (Gears, Steam, Brass)"""
    planEY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEY.html")
    if os.path.exists(planEY_path):
        return FileResponse(planEY_path)
    raise HTTPException(status_code=404, detail="Plan EY not found")


@app.get("/planEZ")
async def planEZ():
    """Plan EZ UI - Noir Corporate (Dark Elegance, Corporate Mystery)"""
    planEZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planEZ.html")
    if os.path.exists(planEZ_path):
        return FileResponse(planEZ_path)
    raise HTTPException(status_code=404, detail="Plan EZ not found")


@app.get("/planFA")
async def planFA():
    """Plan FA UI - Brutalist Brutalism (Raw Concrete, Maximum Brutality)"""
    planFA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFA.html")
    if os.path.exists(planFA_path):
        return FileResponse(planFA_path)
    raise HTTPException(status_code=404, detail="Plan FA not found")


@app.get("/planFB")
async def planFB():
    """Plan FB UI - Vaporwave Dark (Retrowave, Neon on Dark)"""
    planFB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFB.html")
    if os.path.exists(planFB_path):
        return FileResponse(planFB_path)
    raise HTTPException(status_code=404, detail="Plan FB not found")


@app.get("/planFC")
async def planFC():
    """Plan FC UI - Kawaii Tech (Cute, Pastel, Playful)"""
    planFC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFC.html")
    if os.path.exists(planFC_path):
        return FileResponse(planFC_path)
    raise HTTPException(status_code=404, detail="Plan FC not found")


@app.get("/planFD")
async def planFD():
    """Plan FD UI - Swiss Brutalist (Swiss Design + Brutalism)"""
    planFD_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFD.html")
    if os.path.exists(planFD_path):
        return FileResponse(planFD_path)
    raise HTTPException(status_code=404, detail="Plan FD not found")


@app.get("/planFE")
async def planFE():
    """Plan FE UI - Art Nouveau Space (Organic Cosmos, Starlight Vines)"""
    planFE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFE.html")
    if os.path.exists(planFE_path):
        return FileResponse(planFE_path)
    raise HTTPException(status_code=404, detail="Plan FE not found")


@app.get("/planFF")
async def planFF():
    """Plan FF UI - Noir Minimal (Film Noir + Minimal)"""
    planFF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFF.html")
    if os.path.exists(planFF_path):
        return FileResponse(planFF_path)
    raise HTTPException(status_code=404, detail="Plan FF not found")


@app.get("/planFG")
async def planFG():
    """Plan FG UI - Memphis Minimal (Simplified Memphis, Geometric Playfulness)"""
    planFG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFG.html")
    if os.path.exists(planFG_path):
        return FileResponse(planFG_path)
    raise HTTPException(status_code=404, detail="Plan FG not found")


@app.get("/planFH")
async def planFH():
    """Plan FH UI - Glitch Art (RGB Split, Digital Corruption as Art)"""
    planFH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFH.html")
    if os.path.exists(planFH_path):
        return FileResponse(planFH_path)
    raise HTTPException(status_code=404, detail="Plan FH not found")


@app.get("/planFI")
async def planFI():
    """Plan FI UI - Art Deco Luxe (Geometric Luxury, Gilded Details)"""
    planFI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFI.html")
    if os.path.exists(planFI_path):
        return FileResponse(planFI_path)
    raise HTTPException(status_code=404, detail="Plan FI not found")


@app.get("/planFJ")
async def planFJ():
    """Plan FJ UI - Isometric Minimal (2.5D Isometric, Geometric Architecture)"""
    planFJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFJ.html")
    if os.path.exists(planFJ_path):
        return FileResponse(planFJ_path)
    raise HTTPException(status_code=404, detail="Plan FJ not found")


@app.get("/planFK")
async def planFK():
    """Plan FK UI - Retro Diner 50s (1950s American Diner, Neon Chrome)"""
    planFK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFK.html")
    if os.path.exists(planFK_path):
        return FileResponse(planFK_path)
    raise HTTPException(status_code=404, detail="Plan FK not found")


@app.get("/planFL")
async def planFL():
    """Plan FL UI - Nordic Paper (Scandinavian Design, Handmade Paper Texture)"""
    planFL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFL.html")
    if os.path.exists(planFL_path):
        return FileResponse(planFL_path)
    raise HTTPException(status_code=404, detail="Plan FL not found")


@app.get("/planFM")
async def planFM():
    """Plan FM UI - Kawaii Pastel Grunge (Soft Pastels + Hard Grunge)"""
    planFM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFM.html")
    if os.path.exists(planFM_path):
        return FileResponse(planFM_path)
    raise HTTPException(status_code=404, detail="Plan FM not found")


@app.get("/planFN")
async def planFN():
    """Plan FN UI - Brutalist Neon (Brutalist Frame + Neon Glow)"""
    planFN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFN.html")
    if os.path.exists(planFN_path):
        return FileResponse(planFN_path)
    raise HTTPException(status_code=404, detail="Plan FN not found")


@app.get("/planFO")
async def planFO():
    """Plan FO UI - Retro Terminal Green (Classic Green Screen, Phosphor Glow)"""
    planFO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFO.html")
    if os.path.exists(planFO_path):
        return FileResponse(planFO_path)
    raise HTTPException(status_code=404, detail="Plan FO not found")


@app.get("/planFP")
async def planFP():
    """Plan FP UI - Vaporwave Minimal (Simplified Vaporwave, Soft Gradients)"""
    planFP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFP.html")
    if os.path.exists(planFP_path):
        return FileResponse(planFP_path)
    raise HTTPException(status_code=404, detail="Plan FP not found")


@app.get("/planFQ")
async def planFQ():
    """Plan FQ UI - Medieval Manuscript (Parchment, Gothic Fonts, Illuminated)"""
    planFQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFQ.html")
    if os.path.exists(planFQ_path):
        return FileResponse(planFQ_path)
    raise HTTPException(status_code=404, detail="Plan FQ not found")


@app.get("/planFR")
async def planFR():
    """Plan FR UI - Art Deco Linear (Geometric Lines, Repetitive Patterns)"""
    planFR_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFR.html")
    if os.path.exists(planFR_path):
        return FileResponse(planFR_path)
    raise HTTPException(status_code=404, detail="Plan FR not found")


@app.get("/planFS")
async def planFS():
    """Plan FS UI - Glitch Minimal (Minimal Layout + Glitch Effects)"""
    planFS_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFS.html")
    if os.path.exists(planFS_path):
        return FileResponse(planFS_path)
    raise HTTPException(status_code=404, detail="Plan FS not found")


@app.get("/planFT")
async def planFT():
    """Plan FT UI - Glassmorphism Light (Frosted Glass, Soft Gradients)"""
    planFT_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFT.html")
    if os.path.exists(planFT_path):
        return FileResponse(planFT_path)
    raise HTTPException(status_code=404, detail="Plan FT not found")


@app.get("/planFU")
async def planFU():
    """Plan FU UI - Bauhaus Modern (Basic Design School, Geometric Primary)"""
    planFU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFU.html")
    if os.path.exists(planFU_path):
        return FileResponse(planFU_path)
    raise HTTPException(status_code=404, detail="Plan FU not found")


@app.get("/planFV")
async def planFV():
    """Plan FV UI - Synthwave Sunset (80s Sunset Gradient, Perspective Grid)"""
    planFV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFV.html")
    if os.path.exists(planFV_path):
        return FileResponse(planFV_path)
    raise HTTPException(status_code=404, detail="Plan FV not found")


@app.get("/planFW")
async def planFW():
    """Plan FW UI - Paper Cutout (Layered Paper, Shadow Depth)"""
    planFW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFW.html")
    if os.path.exists(planFW_path):
        return FileResponse(planFW_path)
    raise HTTPException(status_code=404, detail="Plan FW not found")


@app.get("/planFX")
async def planFX():
    """Plan FX UI - Dot Matrix (LED Display, Pixelated)"""
    planFX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFX.html")
    if os.path.exists(planFX_path):
        return FileResponse(planFX_path)
    raise HTTPException(status_code=404, detail="Plan FX not found")


@app.get("/planFY")
async def planFY():
    """Plan FY UI - Sticker Art (Doodle Stickers, Hand-drawn Feel)"""
    planFY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFY.html")
    if os.path.exists(planFY_path):
        return FileResponse(planFY_path)
    raise HTTPException(status_code=404, detail="Plan FY not found")


@app.get("/planFZ")
async def planFZ():
    """Plan FZ UI - Infographic Dark (Data Visualization, Dark Charts)"""
    planFZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planFZ.html")
    if os.path.exists(planFZ_path):
        return FileResponse(planFZ_path)
    raise HTTPException(status_code=404, detail="Plan FZ not found")


@app.get("/planGA")
async def planGA():
    """Plan GA UI - Blueprint Technical (Engineering Blueprint, Grid Lines)"""
    planGA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGA.html")
    if os.path.exists(planGA_path):
        return FileResponse(planGA_path)
    raise HTTPException(status_code=404, detail="Plan GA not found")


@app.get("/planGB")
async def planGB():
    """Plan GB UI - Comic Book Pop (Comic Book Aesthetic, Halftone Dots)"""
    planGB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGB.html")
    if os.path.exists(planGB_path):
        return FileResponse(planGB_path)
    raise HTTPException(status_code=404, detail="Plan GB not found")


@app.get("/planGC")
async def planGC():
    """Plan GC UI - Cyber Luxe (Luxury Materials + Digital Elements)"""
    planGC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGC.html")
    if os.path.exists(planGC_path):
        return FileResponse(planGC_path)
    raise HTTPException(status_code=404, detail="Plan GC not found")


@app.get("/planGD")
async def planGD():
    """Plan GD UI - Brutalist Paper (Brutalism + Paper Texture)"""
    planGD_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGD.html")
    if os.path.exists(planGD_path):
        return FileResponse(planGD_path)
    raise HTTPException(status_code=404, detail="Plan GD not found")


@app.get("/planGE")
async def planGE():
    """Plan GE UI - Vaporwave Pastel (Soft Vaporwave, Pastel Colors)"""
    planGE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGE.html")
    if os.path.exists(planGE_path):
        return FileResponse(planGE_path)
    raise HTTPException(status_code=404, detail="Plan GE not found")


@app.get("/planGF")
async def planGF():
    """Plan GF UI - Moss & Stone (Natural Textures, Stone, Moss)"""
    planGF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGF.html")
    if os.path.exists(planGF_path):
        return FileResponse(planGF_path)
    raise HTTPException(status_code=404, detail="Plan GF not found")


@app.get("/planGG")
async def planGG():
    """Plan GG UI - Terminal Hacker (Hacker Terminal Aesthetic, Matrix Rain)"""
    planGG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGG.html")
    if os.path.exists(planGG_path):
        return FileResponse(planGG_path)
    raise HTTPException(status_code=404, detail="Plan GG not found")


@app.get("/planGH")
async def planGH():
    """Plan GH UI - Ceramic Craft (Porcelain Texture, Glaze Shine)"""
    planGH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGH.html")
    if os.path.exists(planGH_path):
        return FileResponse(planGH_path)
    raise HTTPException(status_code=404, detail="Plan GH not found")


@app.get("/planGI")
async def planGI():
    """Plan GI UI - Neon Noir (Neon + Film Noir, Night City)"""
    planGI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGI.html")
    if os.path.exists(planGI_path):
        return FileResponse(planGI_path)
    raise HTTPException(status_code=404, detail="Plan GI not found")


@app.get("/planGJ")
async def planGJ():
    """Plan GJ UI - Woodtype Industrial (Vintage Woodtype, Industrial Feel)"""
    planGJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGJ.html")
    if os.path.exists(planGJ_path):
        return FileResponse(planGJ_path)
    raise HTTPException(status_code=404, detail="Plan GJ not found")


@app.get("/planGK")
async def planGK():
    """Plan GK UI - Botanical Scientific (Botanical Illustration, Scientific Charts)"""
    planGK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGK.html")
    if os.path.exists(planGK_path):
        return FileResponse(planGK_path)
    raise HTTPException(status_code=404, detail="Plan GK not found")


@app.get("/planGL")
async def planGL():
    """Plan GL UI - Holographic Future (Rainbow Holographic, Futuristic)"""
    planGL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGL.html")
    if os.path.exists(planGL_path):
        return FileResponse(planGL_path)
    raise HTTPException(status_code=404, detail="Plan GL not found")


@app.get("/planGM")
async def planGM():
    """Plan GM UI - Minimalist Luxury (Minimalism + Luxury Materials)"""
    planGM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGM.html")
    if os.path.exists(planGM_path):
        return FileResponse(planGM_path)
    raise HTTPException(status_code=404, detail="Plan GM not found")


@app.get("/planGN")
async def planGN():
    """Plan GN UI - Retro Arcade (80s Arcade Games, Pixel Art)"""
    planGN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGN.html")
    if os.path.exists(planGN_path):
        return FileResponse(planGN_path)
    raise HTTPException(status_code=404, detail="Plan GN not found")


@app.get("/planGO")
async def planGO():
    """Plan GO UI - Japanese Minimal (Japanese Aesthetics, Wabi-Sabi)"""
    planGO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGO.html")
    if os.path.exists(planGO_path):
        return FileResponse(planGO_path)
    raise HTTPException(status_code=404, detail="Plan GO not found")


@app.get("/planGP")
async def planGP():
    """Plan GP UI - Brutalist Brutalism Dark (Dark Brutalism, Concrete)"""
    planGP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGP.html")
    if os.path.exists(planGP_path):
        return FileResponse(planGP_path)
    raise HTTPException(status_code=404, detail="Plan GP not found")


@app.get("/planGQ")
async def planGQ():
    """Plan GQ UI - Sci-Fi Scanner (Holographic Scanning, Sci-Fi Interface)"""
    planGQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGQ.html")
    if os.path.exists(planGQ_path):
        return FileResponse(planGQ_path)
    raise HTTPException(status_code=404, detail="Plan GQ not found")


@app.get("/planGR")
async def planGR():
    """Plan GR UI - Elegant Art Nouveau (Flowing Curves, Floral Patterns)"""
    planGR_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGR.html")
    if os.path.exists(planGR_path):
        return FileResponse(planGR_path)
    raise HTTPException(status_code=404, detail="Plan GR not found")


@app.get("/planGS")
async def planGS():
    """Plan GS UI - Corporate Memphis (Flat People, Bright Colors)"""
    planGS_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGS.html")
    if os.path.exists(planGS_path):
        return FileResponse(planGS_path)
    raise HTTPException(status_code=404, detail="Plan GS not found")


@app.get("/planGT")
async def planGT():
    """Plan GT UI - Neon Genesis (EVA Style, Minimalist Cosmos)"""
    planGT_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGT.html")
    if os.path.exists(planGT_path):
        return FileResponse(planGT_path)
    raise HTTPException(status_code=404, detail="Plan GT not found")


@app.get("/planGU")
async def planGU():
    """Plan GU UI - Vintage Botanical (19th Century Botanical, Sepia)"""
    planGU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGU.html")
    if os.path.exists(planGU_path):
        return FileResponse(planGU_path)
    raise HTTPException(status_code=404, detail="Plan GU not found")


@app.get("/planGV")
async def planGV():
    """Plan GV UI - Bauhaus Geometric (Basic Geometry, Primary Colors)"""
    planGV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGV.html")
    if os.path.exists(planGV_path):
        return FileResponse(planGV_path)
    raise HTTPException(status_code=404, detail="Plan GV not found")


@app.get("/planGW")
async def planGW():
    """Plan GW UI - Ethereal Minimal (Translucent, Ethereal, Feathery)"""
    planGW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGW.html")
    if os.path.exists(planGW_path):
        return FileResponse(planGW_path)
    raise HTTPException(status_code=404, detail="Plan GW not found")


@app.get("/planGX")
async def planGX():
    """Plan GX UI - Punk Industrial (Rivets, Leather, Rebellious)"""
    planGX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGX.html")
    if os.path.exists(planGX_path):
        return FileResponse(planGX_path)
    raise HTTPException(status_code=404, detail="Plan GX not found")


@app.get("/planGY")
async def planGY():
    """Plan GY UI - Coastal Minimal (Ocean Vibes, Sand, Fresh)"""
    planGY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGY.html")
    if os.path.exists(planGY_path):
        return FileResponse(planGY_path)
    raise HTTPException(status_code=404, detail="Plan GY not found")


@app.get("/planGZ")
async def planGZ():
    """Plan GZ UI - Mystical Dark (Magic, Starlight, Ancient)"""
    planGZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planGZ.html")
    if os.path.exists(planGZ_path):
        return FileResponse(planGZ_path)
    raise HTTPException(status_code=404, detail="Plan GZ not found")


@app.get("/planHA")
async def planHA():
    """Plan HA UI - Retro Space Age (60s Space Race, Atomic Patterns)"""
    planHA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHA.html")
    if os.path.exists(planHA_path):
        return FileResponse(planHA_path)
    raise HTTPException(status_code=404, detail="Plan HA not found")


@app.get("/planHB")
async def planHB():
    """Plan HB UI - Terracotta Warm (Earth Tones, Clay, Warm)"""
    planHB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHB.html")
    if os.path.exists(planHB_path):
        return FileResponse(planHB_path)
    raise HTTPException(status_code=404, detail="Plan HB not found")


@app.get("/planHC")
async def planHC():
    """Plan HC UI - Frosted Glass Dark (Dark Frosted Glass, Blue Tones)"""
    planHC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHC.html")
    if os.path.exists(planHC_path):
        return FileResponse(planHC_path)
    raise HTTPException(status_code=404, detail="Plan HC not found")


@app.get("/planHD")
async def planHD():
    """Plan HD UI - Brutalist Nature (Brutalism + Nature, Raw Power)"""
    planHD_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHD.html")
    if os.path.exists(planHD_path):
        return FileResponse(planHD_path)
    raise HTTPException(status_code=404, detail="Plan HD not found")


@app.get("/planHE")
async def planHE():
    """Plan HE UI - Vaporwave Elegant (Elegant Vaporwave, Luxe Gradients)"""
    planHE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHE.html")
    if os.path.exists(planHE_path):
        return FileResponse(planHE_path)
    raise HTTPException(status_code=404, detail="Plan HE not found")


@app.get("/planHF")
async def planHF():
    """Plan HF UI - Retro Diner Modern (Modern 50s Diner, Vibrant)"""
    planHF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHF.html")
    if os.path.exists(planHF_path):
        return FileResponse(planHF_path)
    raise HTTPException(status_code=404, detail="Plan HF not found")


@app.get("/planHG")
async def planHG():
    """Plan HG UI - Neon Aqua (Bright Cyan, Glowing Water)"""
    planHG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHG.html")
    if os.path.exists(planHG_path):
        return FileResponse(planHG_path)
    raise HTTPException(status_code=404, detail="Plan HG not found")


@app.get("/planHI")
async def planHI():
    """Plan HI UI - Brutalist Warm (Brutalism + Warm Tones)"""
    planHI_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHI.html")
    if os.path.exists(planHI_path):
        return FileResponse(planHI_path)
    raise HTTPException(status_code=404, detail="Plan HI not found")


@app.get("/planHJ")
async def planHJ():
    """Plan HJ UI - Vintage Sci-Fi (50-60s Sci-Fi Aesthetic)"""
    planHJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHJ.html")
    if os.path.exists(planHJ_path):
        return FileResponse(planHJ_path)
    raise HTTPException(status_code=404, detail="Plan HJ not found")


@app.get("/planHK")
async def planHK():
    """Plan HK UI - Marble Luxe (White Marble, Gold Lines)"""
    planHK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHK.html")
    if os.path.exists(planHK_path):
        return FileResponse(planHK_path)
    raise HTTPException(status_code=404, detail="Plan HK not found")


@app.get("/planHL")
async def planHL():
    """Plan HL UI - Ink Wash Minimal (Chinese Ink Painting)"""
    planHL_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHL.html")
    if os.path.exists(planHL_path):
        return FileResponse(planHL_path)
    raise HTTPException(status_code=404, detail="Plan HL not found")


@app.get("/planHM")
async def planHM():
    """Plan HM UI - Neon Sunset (Pink-Orange Gradient, 80s Neon)"""
    planHM_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHM.html")
    if os.path.exists(planHM_path):
        return FileResponse(planHM_path)
    raise HTTPException(status_code=404, detail="Plan HM not found")


@app.get("/planHN")
async def planHN():
    """Plan HN UI - Minimal Geometric (Pure Geometry, Basic Colors)"""
    planHN_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHN.html")
    if os.path.exists(planHN_path):
        return FileResponse(planHN_path)
    raise HTTPException(status_code=404, detail="Plan HN not found")


@app.get("/planHO")
async def planHO():
    """Plan HO UI - Vintage Modern (Retro + Modern Minimal)"""
    planHO_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHO.html")
    if os.path.exists(planHO_path):
        return FileResponse(planHO_path)
    raise HTTPException(status_code=404, detail="Plan HO not found")


@app.get("/planHP")
async def planHP():
    """Plan HP UI - Abstract Organic (Flowing Shapes, Natural Curves)"""
    planHP_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHP.html")
    if os.path.exists(planHP_path):
        return FileResponse(planHP_path)
    raise HTTPException(status_code=404, detail="Plan HP not found")


@app.get("/planHQ")
async def planHQ():
    """Plan HQ UI - Crystal Ice (Crystal Texture, Ice Patterns)"""
    planHQ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHQ.html")
    if os.path.exists(planHQ_path):
        return FileResponse(planHQ_path)
    raise HTTPException(status_code=404, detail="Plan HQ not found")


@app.get("/planHR")
async def planHR():
    """Plan HR UI - Neon Sunset (Warm Neon, Sunset Gradients)"""
    planHR_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHR.html")
    if os.path.exists(planHR_path):
        return FileResponse(planHR_path)
    raise HTTPException(status_code=404, detail="Plan HR not found")


@app.get("/planHS")
async def planHS():
    """Plan HS UI - Steampunk Industrial (Gears, Brass, Victorian)"""
    planHS_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHS.html")
    if os.path.exists(planHS_path):
        return FileResponse(planHS_path)
    raise HTTPException(status_code=404, detail="Plan HS not found")


@app.get("/planHT")
async def planHT():
    """Plan HT UI - Paper Craft (Paper Texture, Origami Elements)"""
    planHT_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHT.html")
    if os.path.exists(planHT_path):
        return FileResponse(planHT_path)
    raise HTTPException(status_code=404, detail="Plan HT not found")


@app.get("/planHU")
async def planHU():
    """Plan HU UI - Liquid Glass (Glassmorphism, Flowing Texture)"""
    planHU_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHU.html")
    if os.path.exists(planHU_path):
        return FileResponse(planHU_path)
    raise HTTPException(status_code=404, detail="Plan HU not found")


@app.get("/planHV")
async def planHV():
    """Plan HV UI - Neon Noir (Dark Background, Neon Lights, Cinematic)"""
    planHV_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHV.html")
    if os.path.exists(planHV_path):
        return FileResponse(planHV_path)
    raise HTTPException(status_code=404, detail="Plan HV not found")


@app.get("/planHW")
async def planHW():
    """Plan HW UI - Bioluminescent (Deep Sea, Organic Fluorescence)"""
    planHW_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHW.html")
    if os.path.exists(planHW_path):
        return FileResponse(planHW_path)
    raise HTTPException(status_code=404, detail="Plan HW not found")


@app.get("/planHX")
async def planHX():
    """Plan HX UI - Geometric Memphis (80s Postmodern, Geometric Patterns)"""
    planHX_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHX.html")
    if os.path.exists(planHX_path):
        return FileResponse(planHX_path)
    raise HTTPException(status_code=404, detail="Plan HX not found")


@app.get("/planHY")
async def planHY():
    """Plan HY UI - Ambient Dark (Deep Darkness, Subtle Gradients)"""
    planHY_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHY.html")
    if os.path.exists(planHY_path):
        return FileResponse(planHY_path)
    raise HTTPException(status_code=404, detail="Plan HY not found")


@app.get("/planHZ")
async def planHZ():
    """Plan HZ UI - Botanical Minimal (Minimal Layout, Plant Elements)"""
    planHZ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planHZ.html")
    if os.path.exists(planHZ_path):
        return FileResponse(planHZ_path)
    raise HTTPException(status_code=404, detail="Plan HZ not found")


@app.get("/planIA")
async def planIA():
    """Plan IA UI - Synthwave Horizon (Retro Futuristic, Grid Horizon)"""
    planIA_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIA.html")
    if os.path.exists(planIA_path):
        return FileResponse(planIA_path)
    raise HTTPException(status_code=404, detail="Plan IA not found")


@app.get("/planIB")
async def planIB():
    """Plan IB UI - Desert Mirage (Sand Dunes, Golden Sunset)"""
    planIB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIB.html")
    if os.path.exists(planIB_path):
        return FileResponse(planIB_path)
    raise HTTPException(status_code=404, detail="Plan IB not found")


@app.get("/planIC")
async def planIC():
    """Plan IC UI - Arctic Frost (Ice Crystals, Aurora Borealis)"""
    planIC_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIC.html")
    if os.path.exists(planIC_path):
        return FileResponse(planIC_path)
    raise HTTPException(status_code=404, detail="Plan IC not found")


@app.get("/planID")
async def planID():
    """Plan ID UI - Neon Genesis (Evangelion Style, Sci-Fi Orange)"""
    planID_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planID.html")
    if os.path.exists(planID_path):
        return FileResponse(planID_path)
    raise HTTPException(status_code=404, detail="Plan ID not found")


@app.get("/planIE")
async def planIE():
    """Plan IE UI - Gradient Mesh (Flowing Gradients, Mesh Nodes)"""
    planIE_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIE.html")
    if os.path.exists(planIE_path):
        return FileResponse(planIE_path)
    raise HTTPException(status_code=404, detail="Plan IE not found")


@app.get("/planIF")
async def planIF():
    """Plan IF UI - Sakura Storm (Japanese Cherry Blossoms, Pink Storm)"""
    planIF_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIF.html")
    if os.path.exists(planIF_path):
        return FileResponse(planIF_path)
    raise HTTPException(status_code=404, detail="Plan IF not found")


@app.get("/planIG")
async def planIG():
    """Plan IG UI - Brutalist Swiss (International Style, Bold Grid)"""
    planIG_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIG.html")
    if os.path.exists(planIG_path):
        return FileResponse(planIG_path)
    raise HTTPException(status_code=404, detail="Plan IG not found")


@app.get("/planIH")
async def planIH():
    """Plan IH UI - Holographic Tech (Rainbow Hologram, Floating Projection)"""
    planIH_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIH.html")
    if os.path.exists(planIH_path):
        return FileResponse(planIH_path)
    raise HTTPException(status_code=404, detail="Plan IH not found")


@app.get("/planII")
async def planII():
    """Plan II UI - Retro Terminal (CRT Screen, Phosphor Green)"""
    planII_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planII.html")
    if os.path.exists(planII_path):
        return FileResponse(planII_path)
    raise HTTPException(status_code=404, detail="Plan II not found")


@app.get("/planIJ")
async def planIJ():
    """Plan IJ UI - Watercolor Wash (Soft Pigments, Artistic Paper)"""
    planIJ_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIJ.html")
    if os.path.exists(planIJ_path):
        return FileResponse(planIJ_path)
    raise HTTPException(status_code=404, detail="Plan IJ not found")


@app.get("/planIK")
async def planIK():
    """Plan IK UI - Cyber Minimal (Minimalism + Cyberpunk Elements)"""
    planIK_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "index_planIK.html")
    if os.path.exists(planIK_path):
        return FileResponse(planIK_path)
    raise HTTPException(status_code=404, detail="Plan IK not found")


# ========== 全局异常处理 ==========
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理

    【学习要点】异常处理
    - 统一错误响应格式
    - 记录错误日志
    - 避免敏感信息泄露
    """
    request_id = getattr(request.state, "request_id", "unknown")

    error_id = error_logger.log(
        error_type=type(exc).__name__,
        message=str(exc),
        level=ErrorLevel.ERROR,
        context={
            "path": str(request.url),
            "method": request.method,
            "request_id": request_id
        },
        exc_info=exc
    )

    return {
        "error": True,
        "message": "Internal server error",
        "error_id": error_id,
        "request_id": request_id
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
