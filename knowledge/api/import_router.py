"""
导入相关路由。可由 main.py 统一挂载，也可本文件单独启动（兼容旧用法）。
"""

import os

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from knowledge.core.deps import get_upload_file_service
from knowledge.core.paths import get_front_page_dir
from knowledge.schema.upload_schema import TaskStatusResponse, UploadResponse
from knowledge.service.upload_service import UpLoadService
from knowledge.utils.task_util import get_task_info


def register_import_routes(app: FastAPI) -> None:
    @app.post("/upload", response_model=UploadResponse)
    def upload_endpoint(
        file: UploadFile,
        background_tasks: BackgroundTasks,
        upload_service: UpLoadService = Depends(get_upload_file_service),
    ):
        task_id, import_file_path, file_dir = upload_service.process_upload_file(file)
        background_tasks.add_task(
            upload_service.run_import_graph, task_id, import_file_path, file_dir
        )
        return UploadResponse(message=f"{file.filename}文件上传成功", task_id=task_id)

    @app.get("/status/{task_id}", response_model=TaskStatusResponse)
    def get_task_status_endpoint(task_id: str):
        task_info = get_task_info(task_id)
        return TaskStatusResponse(**task_info)


def create_app() -> FastAPI:
    """单独以导入服务启动时使用（默认端口 8000）。"""
    app = FastAPI(title="Agent Brain Import", description="Agent Brain 导入服务", version="0.0.1")
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

    register_import_routes(app)

    page_dir = get_front_page_dir()
    if page_dir and os.path.exists(page_dir):
        app.mount("/front", StaticFiles(directory=page_dir))

    return app


if __name__ == "__main__":
    uvicorn.run(app=create_app(), host="0.0.0.0", port=8000, log_level="info")
