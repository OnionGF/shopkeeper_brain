# 问器 · Agent 问答前端

豆包式布局的 Vite + React + TypeScript 前端，对接现有查询 API（`/query`、`/stream`、`/history`），将 DAG 节点进度映射为「工具调用」展示。

## 开发

```bash
npm install
npm run dev
```

打开 http://127.0.0.1:5173 ，Vite 会把 `/query`、`/stream`、`/history` 代理到 `http://127.0.0.1:8001`。

需先启动查询服务（仓库根目录）：

```bash
PYTHONPATH=. knowledge/.venv/bin/python knowledge/api/query_router.py
```

## 生产构建

```bash
npm run build
```

产物在 `dist/`，由 `query_router` 挂载到 `/agent`（`html=True`）。旧版 `knowledge/front/chat.html` 仍在 `/front`。
