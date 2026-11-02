@echo off
chcp 65001 >nul
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] 创建虚拟环境...
  python -m venv .venv || goto :error
  call ".venv\Scripts\activate.bat"
  echo [2/3] 安装依赖...
  python -m pip install --upgrade pip
  pip install -r requirements.txt || goto :error
) else (
  call ".venv\Scripts\activate.bat"
)

if not exist ".env" (
  echo [3/3] 生成 .env（未配置大模型 Key，将使用模板引擎）
  copy ".env.example" ".env" >nul
)

echo.
echo 后端启动中：http://127.0.0.1:8000/api/docs
echo.
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
goto :eof

:error
echo.
echo 启动失败，请确认已安装 Python 3.10+ 并加入 PATH。
pause
