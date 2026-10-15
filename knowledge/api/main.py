"""
Agent Brain 统一 API 入口：导入 + 查询同进程分流。

启动：
  PYTHONPATH=. knowledge/.venv/bin/python -m knowledge.api.main
  # 或
  PYTHONPATH=. knowledge/.venv/bin/python knowledge/api/main.py
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from knowledge.api.import_router import register_import_routes
from knowledge.api.query_router import register_query_routes
from knowledge.core.paths import get_front_agent_dist_dir


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Brain", description="Agent Brain 统一 API（导入 + 查询）", version="v1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def health():
        return {"flag": "success", "services": ["import", "query"]}

    # 业务路由分流（路径本身无冲突：/upload|/status vs /query|/stream|/history）
    register_import_routes(app)
    register_query_routes(app)

    agent_dir = get_front_agent_dist_dir()
    if agent_dir and os.path.exists(agent_dir):
        app.mount("/agent", StaticFiles(directory=agent_dir, html=True), name="agent")

    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000, log_level="info")
