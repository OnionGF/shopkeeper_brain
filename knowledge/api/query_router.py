"""
查询相关路由。可由 main.py 统一挂载，也可本文件单独启动（兼容旧用法）。
"""

import asyncio
import os
from typing import Union

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from knowledge.core.deps import get_query_service
from knowledge.core.paths import get_front_agent_dist_dir
from knowledge.schema.query_schema import QueryRequest, QueryResponse, StreamSubmitResponse
from knowledge.service.query_service import QueryService
from knowledge.utils.sse_util import create_sse_queue, sse_generator


def register_query_routes(app: FastAPI) -> None:
    @app.post("/query")
    async def query(
        request: QueryRequest,
        background_tasks: BackgroundTasks,
        service: QueryService = Depends(get_query_service),
    ) -> Union[StreamSubmitResponse, QueryResponse]:
        session_id = request.session_id or service.generate_session_id()
        task_id = service.generate_task_id()

        if request.is_stream:
            create_sse_queue(task_id=task_id)
            background_tasks.add_task(
                service.run_query_graph,
                session_id=session_id,
                task_id=task_id,
                query=request.query,
                is_stream=request.is_stream,
            )
            return StreamSubmitResponse(
                message="查询请求已经提交",
                session_id=session_id,
                task_id=task_id,
            )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            service.run_query_graph,
            session_id,
            task_id,
            request.query,
            request.is_stream,
        )
        answer = service.get_task_result(task_id)
        return QueryResponse(
            message="查询请求已经处理完了",
            session_id=session_id,
            answer=answer,
        )

    @app.get("/stream/{task_id}")
    async def stream(task_id: str, request: Request) -> StreamingResponse:
        return StreamingResponse(
            content=sse_generator(task_id, request),
            media_type="text/event-stream",
        )

    @app.get("/history/{session_id}")
    async def get_history(
        session_id: str,
        limit: int = 50,
        service: QueryService = Depends(get_query_service),
    ):
        try:
            items = service.get_history(session_id, limit)
            return {"session_id": session_id, "items": items}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"history error: {e}")

    @app.delete("/history/{session_id}")
    async def clear_chat_history(
        session_id: str,
        service: QueryService = Depends(get_query_service),
    ):
        count = service.clear_history(session_id)
        return {"message": "History cleared", "deleted_count": count}


def create_app() -> FastAPI:
    """单独以查询服务启动时使用（默认端口 8001）。"""
    app = FastAPI(title="Agent Brain Query", description="Agent Brain 查询服务", version="v1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def hello_world():
        return {"flag": "success"}

    register_query_routes(app)

    agent_dir = get_front_agent_dist_dir()
    if agent_dir and os.path.exists(agent_dir):
        app.mount("/agent", StaticFiles(directory=agent_dir, html=True), name="agent")

    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8001)
