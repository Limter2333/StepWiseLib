# 🚀 Sheven_space - Spring AI 项目部署指南

> **Just dance with agent.** 💃  
> 这里是 StepWiseLib 的核心 Java 项目，让我们一起与 AI 共舞！

---

## 📦 项目概述

**Sheven_space** 是一个基于 Spring Boot 3.5.8 + Spring AI Alibaba 的 AI 应用项目。

### 核心技术栈
- ☕ **Java 17**
- 🍃 **Spring Boot 3.5.8**
- 🤖 **Spring AI Alibaba** (通义千问集成)
- 💬 **DashScope API** (Qwen3-Max 模型)
- 🏗️ **Maven** 构建工具

---

## ⚙️ 配置流程

### 1️⃣ 环境变量配置

项目根目录包含 `.env` 文件，存储所有敏感配置信息：

```bash
# .env文件内容示例
DASHSCOPE_API_KEY=your_api_key_here      # 通义千问 API Key
DASHSCOPE_MODEL=qwen3-max-2026-01-23     # 使用的 AI 模型
DASHSCOPE_TEMPERATURE=0.7                # 温度参数 (0.0-1.0)
DASHSCOPE_MAX_TOKENS=2000                # 最大输出 token 数
DASHSCOPE_TOP_P=0.9                      # 核采样参数
DASHSCOPE_ENABLE_SEARCH=false            # 是否启用联网搜索
```

### 2️⃣ application.yml 配置

[`src/main/resources/application.yml`](src/main/resources/application.yml) 引用环境变量：

```yaml
server:
  port: 8088                              # 服务端口
  servlet:
    encoding:
      charset: UTF-8
      enabled: true
      force: true

spring:
  application:
    name: spring-ai-playground
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}       # 从 .env 读取
      chat:
        options:
          model: ${DASHSCOPE_MODEL}
          temperature: ${DASHSCOPE_TEMPERATURE}
          max-tokens: ${DASHSCOPE_MAX_TOKENS}
          top-p: ${DASHSCOPE_TOP_P}
          enable-search: ${DASHSCOPE_ENABLE_SEARCH}
```

---

## 🔧 参数调整指南

### 🌡️ 温度参数 (Temperature)
- **范围**: 0.0 - 1.0
- **默认值**: 0.7
- **说明**: 
  - 越低 (如 0.2) → 回答更保守、确定性更高
  - 越高 (如 0.9) → 回答更有创造性、随机性更强
- **调整建议**: 
  ```bash
  # 需要更稳定的回答
  DASHSCOPE_TEMPERATURE=0.3
  
  # 需要更有创意的回答
  DASHSCOPE_TEMPERATURE=0.9
  ```

### 📏 最大 Token 数 (Max Tokens)
- **默认值**: 2000
- **说明**: 限制 AI 单次回复的最大长度
- **调整建议**:
  ```bash
  # 简短回复
  DASHSCOPE_MAX_TOKENS=500
  
  # 详细长文
  DASHSCOPE_MAX_TOKENS=4000
  ```

### 🎯 核采样参数 (Top P)
- **范围**: 0.0 - 1.0
- **默认值**: 0.9
- **说明**: 控制词汇选择的多样性
- **调整建议**:
  ```bash
  # 更聚焦的回答
  DASHSCOPE_TOP_P=0.5
  
  # 更多样化的表达
  DASHSCOPE_TOP_P=0.95
  ```

### 🔍 联网搜索 (Enable Search)
- **默认值**: false
- **说明**: 是否启用实时联网搜索获取最新信息
- **调整建议**:
  ```bash
  # 启用联网搜索 (获取最新信息)
  DASHSCOPE_ENABLE_SEARCH=true
  
  # 禁用联网搜索 (仅使用训练数据)
  DASHSCOPE_ENABLE_SEARCH=false
  ```

### 🌐 更换 AI 模型
- **当前模型**: `qwen3-max-2026-01-23`
- **可选模型**:
  ```bash
  # 通义千问系列
  DASHSCOPE_MODEL=qwen-max              # 最强性能
  DASHSCOPE_MODEL=qwen-plus             # 平衡性能和成本
  DASHSCOPE_MODEL=qwen-turbo            # 最快速度
  DASHSCOPE_MODEL=qwen3-max-2026-01-23  # 最新版本
  ```

---

## 🚀 部署与启动

### 方式一：Maven 直接运行（开发环境推荐）

```bash
# 进入项目目录
cd Sheven_space

# 启动项目
mvn spring-boot:run
```

### 方式二：打包后运行（生产环境推荐）

#### Step 1: 编译打包
```bash
# 清理并打包
mvn clean package

# 或者跳过测试打包
mvn clean package -DskipTests
```

#### Step 2: 运行 JAR
```bash
# 生成的 JAR 位于 target/ 目录
java -jar target/Sheven_space-1.0.0.jar
```

### 方式三：IDE 启动（开发调试）

**IntelliJ IDEA:**
1. 打开项目
2. 找到主启动类（通常带有 `@SpringBootApplication` 注解）
3. 点击运行按钮或按 `Shift + F10`

**VS Code:**
1. 安装 Java Extension Pack
2. 打开项目
3. 运行 `Java: Run Application` 命令

---

## ✅ 验证启动成功

启动后，观察控制台输出：

```
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /
 =========|_|==============|___/=/_/_/_/
 :: Spring Boot ::                (v3.5.8)

... (省略日志)

o.s.b.w.embedded.tomcat.TomcatWebServer  : Tomcat started on port(s): 8088 (http)
...
Started spring-ai-playground in X.XXX seconds
```

看到 `Tomcat started on port(s): 8088` 表示启动成功！

访问：`http://localhost:8088`

---

## 🛠️ 常见问题排查

### ❌ 问题 1: API Key 无效
**现象**: 调用 AI 接口时报错
**解决**: 检查 `.env` 文件中的 `DASHSCOPE_API_KEY` 是否正确

### ❌ 问题 2: 端口被占用
**现象**: `Port 8088 was already in use`
**解决**: 
```bash
# 方法 1: 修改 application.yml 中的端口号
server:
  port: 8089  # 改为其他端口

# 方法 2: 关闭占用 8088 端口的进程
# Windows:
netstat -ano | findstr :8088
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8088
kill -9 <PID>
```

### ❌ 问题 3: Maven 依赖下载失败
**现象**: `Could not resolve dependencies`
**解决**:
```bash
# 清理 Maven 缓存
mvn dependency:purge-local-repository

# 强制更新依赖
mvn -U clean install
```

### ❌ 问题 4: Java 版本不匹配
**现象**: `Unsupported class file major version`
**解决**: 确保使用 JDK 17
```bash
# 检查 Java 版本
java -version

# 设置 JAVA_HOME (Windows)
set JAVA_HOME=C:\Program Files\Java\jdk-17

# 设置 JAVA_HOME (Linux/Mac)
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
```

---

## 📝 最佳实践

### 🔒 安全建议
1. **永远不要**将 `.env` 文件提交到 Git
2. 使用 `.gitignore` 忽略敏感文件
3. 为不同环境创建不同的 `.env` 文件：
   ```bash
   .env.development    # 开发环境
   .env.test          # 测试环境
   .env.production    # 生产环境
   ```

### ⚡ 性能优化
1. **连接池配置**: 根据并发量调整数据库连接池大小
2. **线程池配置**: 优化 Spring 应用的线程池参数
3. **JVM 参数**: 根据服务器配置调整堆内存大小
   ```bash
   java -Xms512m -Xmx2g -jar target/Sheven_space-1.0.0.jar
   ```

### 📊 监控建议
1. 启用 Spring Boot Actuator 进行健康检查
2. 配置日志级别进行问题追踪
3. 使用 APM 工具监控应用性能

---

## 📞 获取帮助

如果你遇到问题：
- 📖 查看 [Spring AI Alibaba 官方文档](https://java2ai.com/)
- 🐛 在项目中提 Issue
- 💬 联系项目维护者

---

<div align="center">

**Sheven_space** · Made with 💖 and ☕  
*让我们一起在 AI 的海洋里快乐遨游！* 🌊🤖

[返回主项目](../README.md)

</div>
