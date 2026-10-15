import os

# 项目根目录（knowledge/）
KNOWLEDGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 本地文件存储基础目录
LOCAL_BASE_DIR = os.path.join(KNOWLEDGE_ROOT, "temp_data")

# Agent Brain React 前端构建产物
FRONT_AGENT_DIST_DIR = os.path.join(KNOWLEDGE_ROOT, "front-agent", "dist")


def get_local_base_dir() -> str:
    """获取本地文件存储基础目录"""
    return LOCAL_BASE_DIR


def get_front_agent_dist_dir() -> str:
    """获取 Agent Brain 前端 dist 目录"""
    return FRONT_AGENT_DIST_DIR
