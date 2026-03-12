@echo off
chcp 65001 >nul
echo ========================================
echo   ShuiQi - 字段映射 Agent 服务
echo ========================================
echo.

REM 检查 JAVA_HOME
if "%JAVA_HOME%"=="" (
    echo [错误] 未设置 JAVA_HOME 环境变量
    echo 请确保已安装 JDK 17 并设置 JAVA_HOME
    pause
    exit /b 1
)

echo [信息] Java 版本:
java -version
echo.

REM 检查 .env 文件
if not exist ".env" (
    echo [警告] 未找到 .env 文件
    echo 正在从 .env.example 复制配置...
    copy .env.example .env
    echo.
    echo [重要] 请编辑 .env 文件，配置以下必需参数:
    echo   - DASHSCOPE_API_KEY (通义千问 API Key)
    echo   - DB_USERNAME (数据库用户名)
    echo   - DB_PASSWORD (数据库密码)
    echo.
    pause
)

REM 检查 JAR 文件
if not exist "target\ShuiQi-1.0.0.jar" (
    echo [错误] 未找到可执行 JAR 文件
    echo 请先运行：mvn clean package -DskipTests
    pause
    exit /b 1
)

echo [信息] 启动 ShuiQi 应用...
echo 服务端口：http://localhost:8689
echo API 文档：http://localhost:8689/api/field-mapping/health
echo.

java -Xms512m -Xmx2g -jar target\ShuiQi-1.0.0.jar

pause
