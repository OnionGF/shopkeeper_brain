# Agent Brain · 问答 / 导入前端

Vite + React + TypeScript。对接统一 API（导入 + 查询同进程）。

## 开发

```bash
# 后端统一入口（一个进程 :8000）
cd ../..   # 仓库根
PYTHONPATH=. knowledge/.venv/bin/python -m knowledge.api.main

# 前端
cd knowledge/front-agent
npm install
npm run dev
```

打开 http://127.0.0.1:5173 ：

- `#/` 问答
- `#/import` 知识库导入（侧栏入口）

Vite 把 `/query`、`/stream`、`/history`、`/upload`、`/status` 代理到 `http://127.0.0.1:8000`。

## 生产构建

```bash
npm run build
```

产物在 `dist/`，由统一入口挂载到 `/agent`。

可选环境变量：`VITE_API_BASE`（默认空，同源相对路径）。
