@echo off
chcp 65001 >nul
cd /d "%~dp0frontend"

where pnpm >nul 2>nul
if errorlevel 1 (
  echo 未找到 pnpm，请先安装 Node.js 18+ 并执行：npm i -g pnpm
  pause
  exit /b 1
)

if not exist "node_modules" (
  echo 安装前端依赖...
  call pnpm install || goto :error
)

echo.
echo 前端启动中：http://127.0.0.1:5173
echo.
call pnpm dev
goto :eof

:error
echo.
echo 安装失败：若提示 esbuild 构建脚本被忽略，请执行 pnpm approve-builds 后重试。
pause
