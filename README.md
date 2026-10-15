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
| `POST /query` | 提交问答（**DAG 轨**：固定 LangGraph RAG） |
| `POST /api/agent/query` | 提交问答（**Agent 轨**：openai-agents 编排，学习用） |
| `GET /stream/{task_id}` | SSE 流式回答（两轨共用） |
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

开发期 Vite 会把 `/query`、`/api/agent/query`、`/stream`、`/history`、`/upload`、`/status` 代理到 `http://127.0.0.1:8000`。

输入框旁可切换 **DAG / Agent**（偏好保存在 localStorage）。

## 双轨架构（DAG 纯知识库 + Agent 智能分流）

```text
入口层             FastAPI 统一进程；前端切换 DAG / Agent
DAG 轨             POST /query → LangGraph：confirm → hybrid+hyde → RRF → rerank → answer
Agent 轨           POST /api/agent/query → openai-agents 决策 KB tools 或 MCP 联网 → 同一套节点
能力层             query_processor 节点两轨复用（联网仅挂在 Agent tool）
```

| 层级 | 本仓库 | 常见生产形态 |
|------|--------|----------------|
| 入口/网关 | `knowledge.api.main` 双 API | API Gateway + 鉴权限流 |
| 编排 | `POST /api/agent/query` + openai-agents | Agent / 工作流按场景选用 |
| 能力 | `query_processor` 节点（两轨复用） | 检索、重排、生成等库或微服务 |
| 观测 | SSE progress / delta / final | tracing + tool span |
| 演进 | 默认 DAG；Agent 轨可选 | 稳定后再切默认入口 |

何时用哪条轨：

- **DAG**：固定走知识库（hybrid + hyde → RRF → rerank → 生成），不含联网旁路
- **Agent**：模型先 `confirm_item`，再决定知识库工具链或 `web_search`（MCP），最后生成

Agent 目录（生产级分层）`knowledge/agent/`：

```text
config.py / errors.py
context/           会话状态
runtime/           模型 + runner
orchestration/     instructions + Agent 工厂
tools/             kb / web / answer
```

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
│   ├── agent/                ← openai-agents 编排轨（config/context/runtime/orchestration/tools）
│   ├── front-agent/          ← Agent Brain React 前端
│   ├── processor/            ← 导入 / 查询 LangGraph 流水线（能力层）
│   ├── service/              ← 业务服务
│   └── schema/               ← 请求/响应模型
```

更细的流水线说明见：

- `knowledge/processor/import_processor/README.md`
- `knowledge/processor/query_processor/README.md`
- `knowledge/front-agent/README.md`
