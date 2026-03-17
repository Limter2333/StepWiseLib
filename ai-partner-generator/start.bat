@echo off
echo ========================================
echo AI Partner Generator - 快速启动脚本
echo ========================================
echo.

REM 检查 Java
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Java，请确保已安装 Java 17+
    pause
    exit /b 1
)
echo [✓] Java 已安装

REM 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Node.js，请确保已安装 Node.js 18+
    pause
    exit /b 1
)
echo [✓] Node.js 已安装

echo.
echo ========================================
echo 第一步：启动后端服务
echo ========================================
echo.

cd backend

set /p API_KEY="请输入您的 DashScope API Key: "
if "%API_KEY%"=="" (
    echo [警告] 未输入 API Key，图片生成功能将无法使用
    set API_KEY=your-api-key-here
)

set DASHSCOPE_API_KEY=%API_KEY%

echo 正在启动后端...
start "AI Partner Backend" cmd /k "mvn spring-boot:run"

echo 等待后端启动 (10 秒)...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo 第二步：启动前端服务
echo ========================================
echo.

cd ..\frontend

if not exist "node_modules" (
    echo 首次运行，正在安装依赖...
    call npm install
)

echo 正在启动前端...
start "AI Partner Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo 启动完成！
echo ========================================
echo.
echo 前端地址：http://localhost:3000
echo 后端地址：http://localhost:8080
echo.
echo 按任意键退出此窗口...
pause >nul
