"""Vercel Serverless 入口。

Vercel 把 api/ 目录下的 .py 文件识别为 Serverless Function，并把同目录的
其他文件一起打进函数包，因此后端代码放在 api/app/ 里即可，无需额外配置。

注意：api/app/ 是 backend/app/ 的部署副本，修改后端后请运行
    python scripts/sync_api_backend.py
重新同步（打包脚本会自动执行）。
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from app.main import app  # noqa: E402,F401
