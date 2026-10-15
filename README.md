# Agent Brain

知识库 RAG 系统：文档导入（切分 / 向量化 / 入库）+ 问答（混合检索 / 联网 / 流式回答）。

前端为 **Agent Brain**（Vite + React），后端为统一 FastAPI 入口（导入 + 查询同进程）。

## 快速开始

在仓库根目录执行。

### 1. 后端（统一入口，一个进程）

```bash
PYTHONPATH=. knowledge/.venv/bin/python -m knowledge.api.main
```

服务地址：http://127.0.0.1:8000

| 路径 | 说明 |
|------|------|
| `POST /upload` | 上传 PDF / MD |
| `GET /status/{task_id}` | 导入任务进度 |
| `POST /query` | 提交问答 |
| `GET /stream/{task_id}` | SSE 流式回答 |
| `GET/DELETE /history/{session_id}` | 会话历史 |
| `/agent` | React 前端构建产物（需先 `npm run build`） |

依赖：Milvus、MongoDB、MinIO 等按本地环境配置；Python 依赖见 `knowledge/requirements.txt`，虚拟环境建议使用 `knowledge/.venv`。

### 2. 前端

```bash
cd knowledge/front-agent
npm install
npm run dev
```

打开 http://127.0.0.1:5173

- `#/`：问答
- `#/import`：知识库导入（侧栏「知识库导入」也可进入）

开发期 Vite 会把 `/query`、`/stream`、`/history`、`/upload`、`/status` 代理到 `http://127.0.0.1:8000`。

## 日常用法小结

只需启动两个进程：

1. 后端：`python -m knowledge.api.main`（端口 **8000**）
2. 前端：`npm run dev`（端口 **5173**）

不必再分别启动导入服务（旧 8000）和查询服务（旧 8001）。`import_router.py` / `query_router.py` 仍可单独启动以兼容旧方式，日常推荐用 `knowledge.api.main`。

## 生产构建（前端）

```bash
cd knowledge/front-agent
npm run build
```

产物输出到 `knowledge/front-agent/dist`，由统一后端挂载到 http://127.0.0.1:8000/agent/ 。

可选环境变量：`VITE_API_BASE`（默认空，使用同源相对路径）。

## 目录速览

```text
shopkeeper_brain/
├── README.md                 ← 本文件
├── knowledge/
│   ├── api/
│   │   ├── main.py           ← 统一入口（推荐）
│   │   ├── import_router.py  ← 导入路由（可被 main 挂载）
│   │   └── query_router.py   ← 查询路由（可被 main 挂载）
│   ├── front-agent/          ← Agent Brain React 前端
│   ├── processor/            ← 导入 / 查询 LangGraph 流水线
│   ├── service/              ← 业务服务
│   └── schema/               ← 请求/响应模型
```

更细的流水线说明见：

- `knowledge/processor/import_processor/README.md`
- `knowledge/processor/query_processor/README.md`
- `knowledge/front-agent/README.md`
