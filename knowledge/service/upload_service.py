import os
import uuid
import logging
import shutil
from datetime import datetime

from fastapi import UploadFile

from knowledge.core.paths import get_local_base_dir
from knowledge.processor.import_processor.exceptions import FileProcessingError
from knowledge.utils.client.storage_clients import StorageClients
from knowledge.processor.import_processor.main_graph import import_app
from knowledge.utils.task_util import update_task_status, add_running_task, add_done_task, TASK_STATUS_PROCESSING, TASK_STATUS_COMPLETED, TASK_STATUS_FAILED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UpLoadService:
    """
    处理文件上传的逻辑
    """

    def get_base_dir(self):
        return os.path.join(get_local_base_dir(), datetime.now().strftime("%Y%m%d"))


    def run_import_graph(self, task_id: str, import_file_path: str, file_dir: str):
        """
        运行整个图谱流程
        Args:
            task_id:
            import_file_path:
            file_dir:

        Returns:

        """
        # 1. 更新任务状态为processing
        update_task_status(task_id, TASK_STATUS_PROCESSING)

        # 2. 定义运行graph流程的状态
        graph_state = {
            "task_id": task_id,
            "import_file_path": import_file_path,
            "file_dir": file_dir
        }

        # stream:迭代整个graph图状态可以得到每一个节点的事件(节点的名字以及节点操作完state之后的新状态)
        # 3. 运行整个导入图状态
        try:
            for event in import_app.stream(graph_state):

                for key, value in event.items():
                    logger.info(f"当前正在执行的节点--->{key}")

            # 3.1 更新任务为已完成
            update_task_status(task_id, TASK_STATUS_COMPLETED)
        except Exception as e:
            logger.error(f"[{task_id}] 执行导入过程中出现异常 原因{str(e)}")

            # 3.2 更新任务为失败
            update_task_status(task_id, TASK_STATUS_FAILED)

    def process_upload_file(self, file: UploadFile):
        """
        处理文件上传
        1、将上传的文件存储到本地临时目录（中转）
        2、将上传的文件存储到远程minio
        3、将file_dir /import_file_path /task_id 返回
        Args:
            file:

        Returns:

        """
        # 1、生成任务id
        task_id = uuid.uuid4().hex[:8] # 随机 获取前8个随机数
        add_running_task(task_id, "upload_file")

        # 2、生成一个日期目录 并且将日期目录和临时目录拼接在一起
        base_file_dir = self.get_base_dir()

        # 3、构建文档完整归属目录
        file_dir = os.path.join(base_file_dir,task_id)

        # 4、保存文件到临时目录
        import_file_path =self._save_upload_file_to_lcoal(file, file_dir)

        # 5、保存文件到minio中
        self.save_upload_file_to_minio(import_file_path, file.filename)
        add_done_task(task_id, "upload_file")
        # 6、返回图谱的信息
        return task_id, import_file_path, file_dir

    def _save_upload_file_to_lcoal(self, file: UploadFile, file_dir: str) -> str | bytes:
        """
        保存文件目录
        Args:
            file (UploadFile): 文件上传对象
            file_dir: 上传文件的目录

        Returns:

        """

        # 1、创建文件归属目录
        os.makedirs(file_dir, exist_ok=True)

        # 2、构建导入文件的路径
        import_file_path = os.path.join(file_dir, file.filename)

        try:
            # 3、写入文件（不是目录）
            with open(import_file_path, "wb") as f:
                # 不同的操作系统以及不同的python版本都可以分批次写入
                shutil.copyfileobj(file.file, f)
        except IOError as e:
            logger.info(f"上传{file.filename}写入临时目录失败，原因{str(e)}")
            raise FileProcessingError(message=f"{file.filename}写入临时目录失败 原因{str(e)}")

        # 4、返回导入的文件
        return import_file_path

    def save_upload_file_to_minio(self, import_file_path: str, filename: str):
        """

        Args:
            import_file_path: 上传文件的地址
            filename: 上传文件的名字

        Returns:

        """
        # 1、获取minio客户端
        try:
            minio_client = StorageClients.get_minio_client()
        except ConnectionError as e:
            logger.error(f"Minio客户端获取失败，原因：{str(e)}")
            return

        # 2、获取minio的相关信息
        bucket_name = os.getenv("MINIO_BUCKET")
        object_name = f"origin_files/{datetime.now().strftime('%Y%m%d')}/{filename}"

        # 3、上传
        try:
            minio_client.fput_object(bucket_name, object_name, import_file_path)
        except Exception as e:
            logger.error(f"{filename}上传到Minio失败 原因{str(e)}")

