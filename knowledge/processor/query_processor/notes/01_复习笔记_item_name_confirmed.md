# 复习笔记：ItemNameConfirmedNode（商品名确认节点）

> 文件：`nodes/item_name_confirmed_node.py`  
> 定位：查询流水线**入口节点**——把用户口语商品名对齐成库内标准名，并决定「继续检索 / 让用户选 / 抱歉」。

---

## 1. 在图谱中的位置

```text
item_name_confirmed_node          ← 入口
        │
        ├─ state 有 answer ──────→ answer_output_node → END
        │
        └─ 无 answer（已确认商品名）
                │
                v
           multi_search（并行）
           ├─ hybrid_vector_search
           ├─ hyde_vector_search
           └─ web_mcp_search
                → join → rrf → rerank → answer_output
```

路由：`route_after_item_confirm` —— `state['answer']` 有值则跳过检索。

---

## 2. 为什么要这个节点（业务动机）

| 问题 | 做法 |
|------|------|
| 用户说法不标准（简称/错写/品类） | LLM 抽取 + 向量对齐到标准名 |
| 下游用 `item_name` **精确过滤** | 必须用库里存的正式名，不能用 LLM 原文 |
| 不确定时硬查会噪音大、幻觉高 | 模糊则 `options` 让用户确认；无关则抱歉 |

一句话：**先对齐标准商品名，再准许三路检索；对齐不上就拦截。**

### 为什么转向量再查，而不是直接等值查？

```text
用户/LLM：「RS12 万用表」
库内标准名：「RS PRO RS-12 数字万用表」
```

等值 `==` 查不到；BGE-M3 混合向量（稠密语义 + 稀疏字面）能找回相近标准名，再按分数分 `confirmed` / `options`。

---

## 3. 整体流程（process）

```text
1. 取 original_query、session_id
2. Mongo 拉最近历史（limit=10 条 ≈ 5 轮），拼成上下文字符串
3. _ItemNameExtractor：LLM 抽 item_names + rewritten_query
4. 仅当 item_names 非空 → _ItemNameAligner 向量对齐
   （闲聊/天气等抽不到名，不拿整句去商品库硬匹配）
5. _decide：写 state（继续检索 or 填 answer）
6. state['history'] = 原始历史列表
```

协作结构（组合，非继承）：

| 类 | 职责 |
|----|------|
| `_ItemNameExtractor` | LLM 抽取 + JSON 清洗解析 |
| `_ItemNameAligner` | 向量检索 + 阈值对齐 + 多候选过滤 |
| `ItemNameConfirmedNode` | 编排 + 三分支决策 |

---

## 4. `_ItemNameExtractor` — LLM 抽取

### 输入 / 输出

- 入：原始问题 + 历史上下文  
- 出：`{ item_names: List[str], rewritten_query: str }`  
- 失败兜底：`item_names=[]`，`rewritten_query=original_query`

### 要点

1. `response_format=True`：尽量约束 JSON  
2. Prompt：系统角色 + `ITEM_NAME_USER_EXTRACT_TEMPLATE`（含历史与当前问）  
3. `_clean_and_parse`：去掉 \`\`\`json 围栏再 `json.loads`（防模型升级/换模型）  
4. 校验类型：`item_names` 必须是字符串列表；`rewritten_query` 必须是字符串  

**查询重写**：把代词/省略补全成可检索问句（结合历史），给下游检索用。

---

## 5. `_ItemNameAligner` — 向量对齐

### 5.1 `_search_vector`

```text
BGE-M3 对每个抽取名生成 dense + sparse
  → 在 item_name_collection（如 kb_item_names_v1）做混合检索
  → TopK=5，输出 item_name + score
```

单条结果形态：

```python
{
  "extracted_name": "LLM抽出的名",
  "matches": [{"score": 0.82, "item_name": "库内标准名"}, ...]
}
```

检索参数（配置可调）：稠密/稀疏权重默认各 0.5，`norm_score=True`。

### 5.2 `_align` — 阈值分桶（面试重点）

配置阈值（`.env` / config）：

| 配置 | 默认 | 含义 |
|------|------|------|
| `item_name_high_confidence` | 0.75 | 高于此 → 高置信 |
| `item_name_mid_confidence` | 0.45 | 中置信下界 → 可进 options |
| `item_name_score_gap` | 0.08 | 头部差距，判断能否唯一定夺 |
| `item_name_max_options` | 3 | options 最多展示几个 |

对每个 `extracted_name` 的 matches（按 score 降序）：

**有高置信 `high`（score > high）：**

1. 若库内名与 LLM 抽出名**字符串完全相等** → 直接 `confirmed`（最准）  
2. 否则若 high 只有 1 个 → `confirmed`  
3. 否则多个高分：  
   - `top1 - top2 >= score_gap` → 只确认 top1  
   - 差距不够 → 多个进 `options`（歧义，让用户选）

**无高置信：**

- 取 mid 区间（`>= mid` 且不在 confirmed/options）→ 进 `options`  
- **低于 mid 不兜底**：避免天气等无关问被弱匹配到商品  

**去重规则：**

- confirmed / options 各自不重复  
- 已在 confirmed 的不再进 options  
- 最后 `dict.fromkeys` 保序去重；options 截断到 max_options  

### 5.3 `_item_name_score_filter`

当 `confirmed` 多于 1 个时：只保留与**最高分**差距 ≤ `score_gap` 的名字，压掉明显偏弱的「多确认」。

---

## 6. `_decide` — 三分支决策

| 条件 | 行为 |
|------|------|
| 有 `confirmed` | `state['item_names']=confirmed`，写 `rewritten_query`，**不写 answer** → 走三路检索 |
| 无 confirmed，仅 1 个 option，且本轮 LLM 确有抽取 | **品类问法放行**：把该 option 提升为 confirmed |
| 多个/模糊 options | `state['answer']=请用户从候选里选` → 短路到答案输出 |
| 都空 | `state['answer']=抱歉，关联不到具体产品` → 短路 |

记忆口诀：**确认了就查；含糊就问；啥都没有就道歉。**

---

## 7. 写入 state 的字段

| 字段 | 何时 |
|------|------|
| `item_names` | 确认成功（标准商品名列表） |
| `rewritten_query` | 确认成功 |
| `answer` | 需用户确认或抱歉时（触发跳过检索） |
| `history` | 始终写回近期消息 |

---

## 8. 面试高频问答

**Q1：这个节点解决什么问题？**  
用户说法与库内标准商品名不一致；下游过滤依赖标准名。本节点完成抽取、对齐、分流。

**Q2：为什么向量对齐而不是精确匹配？**  
简称/错写/语序不同导致等值失败；向量可召回相近标准名，再用阈值决定确认或澄清。

**Q3：confirmed 和 options 怎么划分？**  
高置信（及唯一/分差够大）→ confirmed；中置信或多个难分高分 → options；低分丢弃。

**Q4：为什么闲聊不进向量库？**  
LLM 抽不到 `item_names` 则跳过对齐，避免整句弱匹配到商品名产生误导选项。

**Q5：阈值 0.75 / 0.45 怎么来的？**  
不应拍脑袋。应用压测集（问法 × 抽取名 × 期望标准名）扫阈值曲线选最优（代码 TODO 已点明）。

**Q6：和导入侧「商品名识别」的关系？**  
导入：从文档抽名写入 `kb_item_names`；查询：把用户说法对齐到这张表。一张标准名表，两端共用。

**Q7：单一 option 为何直接放行？**  
品类问法常只有一个中置信候选；有抽取词支撑时可当确认，减少多轮打扰（可配置收紧）。

**Q8：失败怎么降级？**  
LLM/Milvus/Embedding 客户端失败 → 空列表 → 走抱歉或空确认，不拖垮整图。

---

## 9. 易错 / 实现注意

1. pymilvus Hit 字段是 `entity`，不是 `entry`  
2. 分数字段用 `distance`（归一化后当作相似度用）  
3. 库内可能有同名重复记录，options 追加时必须再去重  
4. `_item_name_score_filter` 返回类型注解写成了 `List[Dict]`，实际返回 `List[str]`  
5. 有 `answer` 就短路：别在确认节点里又去检索  

---

## 10. 一句话收束

**历史 + LLM 抽名并改写 →（有名才）BGE-M3 混合检索标准名表 → 阈值分成 confirmed/options → 确认则放行三路检索，否则让用户选或抱歉结束。**
