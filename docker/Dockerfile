"""
Dockerfile - 应用镜像构建
=========================

【学习要点】Dockerfile语法

1. FROM - 指定基础镜像
   FROM python:3.11-slim
   # python:3.11-slim = Python 3.11 + 轻量级Linux

2. WORKDIR - 设置工作目录
   WORKDIR /app
   # 类似于 cd /app

3. COPY - 复制文件
   COPY requirements.txt .
   # 复制到当前目录

4. RUN - 执行命令
   RUN pip install -r requirements.txt
   # 构建时安装依赖

5. EXPOSE - 声明端口
   EXPOSE 8000
   # 文档作用，实际由docker run -p映射

6. CMD - 启动命令
   CMD ["uvicorn", "main:app"]
   # 容器启动时执行的命令
"""

# ========== 基础镜像 ==========
FROM python:3.11-slim

# 【学习要点】为什么要slim版本？
# - 完整镜像: ~900MB
# - slim镜像: ~150MB
# - 减少存储空间和拉取时间
# - 生产环境推荐slim

# ========== 设置环境变量 ==========
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# ========== 安装系统依赖 ==========
# 【学习要点】系统依赖 vs Python依赖
# - 系统依赖: apt-get安装，系统级库
# - Python依赖: pip安装，Python库
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 【学习要点】为什么要build-essential？
# - 某些Python包需要编译C扩展
# - chromium: PDF解析可能需要
# - 其他可能需要gcc等编译器

# ========== 设置工作目录 ==========
WORKDIR /app

# ========== 复制依赖文件 ==========
COPY requirements.txt .

# ========== 安装Python依赖 ==========
RUN pip install --no-cache-dir -r requirements.txt

# 【学习要点】pip install的优化
# --no-cache-dir: 不缓存下载的包，减小镜像体积
# -r requirements.txt: 批量安装
# 注意: 顺序很重要，先安装依赖，后复制代码

# ========== 复制应用代码 ==========
COPY . .

# 【学习要点】为什么最后复制代码？
# - Docker层缓存机制
# - 代码经常变，依赖不常变
# - 放在最后可以利用缓存（修改代码不影响依赖安装层）

# ========== 创建数据目录 ==========
RUN mkdir -p /app/data /app/logs

# ========== 暴露端口 ==========
EXPOSE 8000

# ========== 健康检查 ==========
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# 【学习要点】HEALTHCHECK
# - 容器健康状态检查
# - interval: 检查频率
# - timeout: 超时时间
# - retries: 重试次数
# - 帮助Docker管理容器生命周期

# ========== 启动命令 ==========
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 【学习要点】CMD vs ENTRYPOINT
# CMD: 可被docker run覆盖
# ENTRYPOINT: 不可覆盖，作为入口
# 这里用CMD，因为开发时可能需要不同的启动参数
