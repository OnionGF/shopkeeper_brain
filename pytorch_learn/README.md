# PyTorch 深入学习

基于 [动手学深度学习（D2L）PyTorch 版](https://zh.d2l.ai/) 的本地学习目录。

## 目录说明

| 目录 | 用途 |
|------|------|
| `notebooks/` | 跟课实验（主入口） |
| `notes/` | 概念笔记、公式、踩坑记录 |
| `exercises/` | 课后练习与作业 |
| `src/` | 可复用代码（模型 / 数据集 / 工具） |
| `data/` | 本地数据（不提交） |
| `checkpoints/` | 模型权重（不提交） |

## 环境

```bash
cd pytorch_learn
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

## 学习路线

1. **预备知识** — Tensor、自动求导、线性代数直觉  
2. **线性神经网络** — 线性回归、Softmax、从零实现到简洁实现  
3. **多层感知机** — MLP、过拟合、Dropout、数值稳定性  
4. **深度学习计算** — 层与块、参数管理、自定义层  
5. **卷积神经网络** — Conv、Pooling、LeNet → ResNet  
6. **循环神经网络** — RNN / GRU / LSTM、语言模型  
7. **注意力与 Transformer** — Attention、自注意力、Transformer  
8. **优化与训练技巧** — 优化器、学习率、正则化  

每章对应 `notebooks/0x_*.ipynb` 与 `notes/0x_*.md`，先跑 notebook，再补笔记。

## 建议节奏

- 每天 1 个 notebook，写完至少 3 条笔记（概念 / 代码坑 / 和 RAG 的关联）
- 能跑通后，把通用函数抽到 `src/utils/`
- 练手任务放 `exercises/`，不要和跟课 notebook 混在一起
