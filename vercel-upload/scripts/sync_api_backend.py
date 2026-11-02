"""把 backend/app 同步到 api/app（Vercel 部署副本）。

Vercel 只把 api/ 目录下的文件打进函数包，所以部署副本放在 api/app/。
修改后端代码后执行：python scripts/sync_api_backend.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "backend" / "app"
DST = ROOT / "api" / "app"

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=IGNORE)
    files = sum(1 for _ in DST.rglob("*.py"))
    print(f"已同步 {SRC} -> {DST}（{files} 个 .py 文件）")


if __name__ == "__main__":
    main()
