#  RAG 系统：Markdown 与 HTML 表格处理指南

在构建高质量的 RAG（检索增强生成）系统时，使用文本切分器直接处理包含表格的文档，是一场极其惨烈的灾难。切分器会无视表格的二维结构，将 `|` 或 `<tr><td>` 暴力斩断，导致下游的大模型（LLM）产生严重的幻觉和语义丢失。



**问题演示**：假设有一个简单的 Markdown 表格：

```markdown
| 功能     | 量程   | 精确度              |
|----------|--------|---------------------|
| 直流电压 | 200mV  | ± (0.5% + 2 digits) |
| 直流电压 | 20V    | ± (0.5% + 2 digits) |
| 交流电压 | 600V   | ± (1.2% + 10 digits)|
```

如果切分器在第 3 行和第 4 行之间切断，下游 LLM 拿到的第二个 Chunk 就变成了：

```
| 直流电压 | 20V    | ± (0.5% + 2 digits) |
| 交流电压 | 600V   | ± (1.2% + 10 digits)|
```

**表头丢失**，LLM 完全不知道 `20V` 是什么含义——是电压？电流？电阻？语义彻底断裂。

针对这一"**世界级痛点**"，工业界常见有 4 个层级的演进式解决方案。

---

## 方案一: 表格隔离保护法

**核心思想**：将表格视为"不可侵犯的原子实体"。

**实现方式**：
在文本进入通用切分器之前，使用正则表达式将标准的 Markdown 表格整个提取出来，作为独立的 Chunk 存放，剩余的正文再送入切分器。

```python
import re

def isolate_tables(md_content: str):
    """将 Markdown 表格从正文中隔离出来"""
    # 匹配标准 Markdown 表格（以 | 开头的连续行）
    table_pattern = re.compile(r'(\n?(?:\|[^\n]+\|\n)+)', re.MULTILINE)

    tables = []
    text_parts = []
    last_end = 0

    for match in table_pattern.finditer(md_content):
        # 收集表格前的正文
        text_parts.append(md_content[last_end:match.start()])
        # 收集表格（作为独立 Chunk）
        tables.append(match.group())
        last_end = match.end()

    # 收集最后一段正文
    text_parts.append(md_content[last_end:])

    return text_parts, tables  # 正文送切分器，表格直接作为独立 Chunk
```

* **优点**：实现简单，能有效保护小型标准表格的完整性。
* **缺点**：
    * 如果表格本身超出了 Embedding 模型的 Token 上限，依然会面临超载报错。
    * 对 HTML 表格（`<table><tr><td>`）无能为力。
    * 只支持标准 Markdown 表格语法（`|` 管道符格式）。

---

## 方案二: 表头续传切分法

**核心思想**：表格可以切，但必须保证每一块"残骸"都拥有完整的身份证。

**实现方式**：
编写专门的表格切分算法。先提取表格的首行（表头），然后按固定行数切分下方的数据行。在组装 Chunk 时，强制将提取出的表头拼接到每一个数据子块的顶部。

```python
def split_table_with_header(table_text: str, max_rows_per_chunk: int = 5):
    """切分表格，并为每个子块续传表头"""
    lines = table_text.strip().split("\n")

    # 前两行：表头 + 分隔线（如 |---|---|）
    header = lines[0]
    separator = lines[1]
    data_rows = lines[2:]

    chunks = []
    for i in range(0, len(data_rows), max_rows_per_chunk):
        batch = data_rows[i:i + max_rows_per_chunk]
        # 每个子块都拼上表头，保证 LLM 能看懂列含义
        chunk = "\n".join([header, separator] + batch)
        chunks.append(chunk)

    return chunks


# 示例
table = """| 功能     | 量程   | 精确度              |
|----------|--------|---------------------|
| 直流电压 | 200mV  | ± (0.5% + 2 digits) |
| 直流电压 | 20V    | ± (0.5% + 2 digits) |
| 交流电压 | 200V   | ± (1.2% + 10 digits)|
| 交流电压 | 600V   | ± (1.2% + 10 digits)|"""

for i, chunk in enumerate(split_table_with_header(table, max_rows_per_chunk=2)):
    print(f"--- Chunk {i + 1} ---")
    print(chunk)
    print()
```

**输出效果**：每个 Chunk 都保留了完整表头：

```
--- Chunk 1 ---
| 功能     | 量程   | 精确度              |
|----------|--------|---------------------|
| 直流电压 | 200mV  | ± (0.5% + 2 digits) |
| 直流电压 | 20V    | ± (0.5% + 2 digits) |

--- Chunk 2 ---
| 功能     | 量程   | 精确度              |
|----------|--------|---------------------|
| 交流电压 | 200V   | ± (1.2% + 10 digits)|
| 交流电压 | 600V   | ± (1.2% + 10 digits)|
```

* **优点**：完美解决了超大表格的容量超载问题，LLM 拿到子块依然能看懂列含义。
* **缺点**：产物依然是二维结构（带有 `|` 管道符）。大部分向量模型（如 BGE-M3）对空间符号的敏感度极差，导致检索命中率依然不理想。

---

##  方案三: 降维转译法

**核心思想**：消灭二维表格，将表格拍平，转译为高信息密度的自然语言。

**实现方式**：
这是目前大厂处理复杂图文文档的核心策略，分为三个阶段：

### 阶段一：矩阵投影

引入 `BeautifulSoup` 等解析器，彻底解析 HTML 表格。针对 `rowspan` 和 `colspan`（跨行跨列），在内存中构建二维数组（2D List），并将合并的单元格内容进行**向下、向右的物理填充**。

**为什么需要矩阵投影？** 以万用表"规格"表格为例，HTML 中"直流电压"设置了 `rowspan="5"`，意味着它占据 5 行。但在 HTML 源码中，第 2~5 行的 `<tr>` 里只有 3 个 `<td>`（而不是 4 个），如果直接逐行解析，数据会全部错位。

```python
| 直流电压 | 200mV  | 0.1mV | ±(0.5%+2) |
|         | 2000mV | 1mV   | ±(0.5%+2) |
|         | 20V    | 0.01V | ±(0.5%+2) |
|         | 200V   | 0.1V  | ±(0.8%+2) |
|         | 600V   | 1V    | ±(0.8%+2) |
```

**矩阵投影**做的事情就是：先在内存里创建一个空的二维数组（5行×4   ），然后遇到 `rowspan="5"` 时，把"直流电压"这个值**物理填充到 5 个格子里**：

~~~python
grid[0][0] = "直流电压"
grid[1][0] = "直流电压"  # 向下填充
grid[2][0] = "直流电压"  # 向下填充
grid[3][0] = "直流电压"  # 向下填充
grid[4][0] = "直流电压"  # 向下填充
```

`colspan` 同理，只不过是**向右填充**。填充完之后，每一行都是完整的 4 个值，后续处理就不会错位了。

## 意图嗅探

填充完矩阵之后，要判断这个表格属于什么类型，因为不同类型的表格转译成自然语言的方式不一样。常见的有两种：

**第一种：左上角空置的交叉表**，比如你文档里电池测试那个表：
```
|          | 良好    | 较弱        | 坏的    |
| 9V电池   | >8.2V  | 7.2至8.2V  | <7.2V  |
| 1.5V电池 | >1.35V | 1.22至1.35V | <1.22V |
```

左上角是空的，说明第一行是列头，第一列是行头，两个维度交叉描述。转译时要把行头和列头都拼进去：`9V电池的良好标准为>8.2V`。

**第二种：无表头的 K-V 表**，比如你文档里技术指标那个表：
```
| 二极管测试     | 测试电流最大值1mA... |
| 短路蜂鸣测试   | 若电阻小于30时...   |
| 输入阻抗      | >1MΩ              |

没有表头行，每一行就是一个键值对。转译方式就简单了：二极管测试：测试电流最大值1mA...。
~~~

所以"意图嗅探"就是**先看表格长什么样，再决定怎么把它转成自然语言**。



```python
from bs4 import BeautifulSoup

def html_table_to_grid(html: str):
    """将 HTML 表格（含 rowspan/colspan）展开为规整的二维数组"""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")

    # 1. 计算表格的实际列数
    num_rows = len(rows)
    num_cols = max(
        sum(int(td.get("colspan", 1)) for td in row.find_all("td"))
        for row in rows
    )

    # 2. 创建空的二维数组
    grid = [[None] * num_cols for _ in range(num_rows)]

    # 3. 遍历每个单元格，处理 rowspan/colspan 的物理填充
    for row_idx, row in enumerate(rows):
        col_idx = 0
        for td in row.find_all("td"):
            # 找到当前行中第一个空位
            while col_idx < num_cols and grid[row_idx][col_idx] is not None:
                col_idx += 1

            rowspan = int(td.get("rowspan", 1))
            colspan = int(td.get("colspan", 1))
            text = td.get_text(strip=True)

            # 向下、向右物理填充
            for r in range(rowspan):
                for c in range(colspan):
                    if row_idx + r < num_rows and col_idx + c < num_cols:
                        grid[row_idx + r][col_idx + c] = text

            col_idx += colspan

    return grid
```

**填充效果**（以"直流电压"为例）：

```
填充前（HTML 源码的实际结构）：
第1行: [直流电压(rowspan=5), 200mV,  0.1mV, ±0.5%(rowspan=3)]
第2行: [                      2000mV, 1mV                     ]  ← 只有2个td
第3行: [                      20V,    0.01V                    ]  ← 只有2个td
第4行: [                      200V,   0.1V,  ±0.8%(rowspan=2) ]
第5行: [                      600V,   1V                       ]  ← 只有2个td

填充后（规整的二维数组）：
第1行: [直流电压, 200mV,  0.1mV, ±0.5%]
第2行: [直流电压, 2000mV, 1mV,   ±0.5%]  ← 直流电压被向下填充
第3行: [直流电压, 20V,    0.01V, ±0.5%]  ← 直流电压和±0.5%都被向下填充
第4行: [直流电压, 200V,   0.1V,  ±0.8%]
第5行: [直流电压, 600V,   1V,    ±0.8%]  ← ±0.8%被向下填充
```

### 阶段二：意图嗅探

矩阵构建完成后，需要判断表格属于什么类型，因为不同类型的转译策略不同：

**类型一：标准表头表**（第一行是列标题）

```
| 功能     | 量程   | 分辨率 | 精确度 |
|----------|--------|--------|--------|
| 直流电压 | 200mV  | 0.1mV  | ±0.5%  |

```

特征：第一行的内容是描述性的列名。转译时用第一行作为 key。

**类型二：左上角空置的交叉表**（行头 + 列头交叉描述）

```
|          | 良好    | 较弱        | 坏的    |
|----------|---------|-------------|---------|
| 9V电池   | >8.2V  | 7.2至8.2V   | <7.2V  |
| 1.5V电池 | >1.35V | 1.22至1.35V | <1.22V |
```

特征：左上角（`grid[0][0]`）为空。转译时需要同时拼接行头和列头。

**类型三：无表头的 K-V 表**（每行就是一个键值对）

```
| 输入阻抗   | >1MΩ           |
| 显示       | 3½位液晶显示    |
| 电池       | 一粒9V电池      |
```

特征：只有两列，没有明显的表头行。转译时直接 `key：value`。

```python
def detect_table_type(grid):
    """嗅探表格类型"""
    if not grid or not grid[0]:
        return "unknown"

    first_cell = (grid[0][0] or "").strip()
    num_cols = len(grid[0])

    # 左上角为空 → 交叉表
    if not first_cell and num_cols > 2:
        return "cross_table"

    # 只有两列且第一行看起来不像表头 → K-V 表
    if num_cols == 2:
        return "kv_table"

    # 默认：标准表头表
    return "header_table"
```



### 阶段三：语义重构

根据表格类型，将每一行数据转译为自然语言：

```python
def linearize(grid, table_type: str):
    """将二维表格转译为一维自然语言"""
    results = []

    if table_type == "header_table":
        headers = grid[0]
        for row in grid[1:]:
            parts = [f"{h}:{v}" for h, v in zip(headers, row) if v]
            results.append("- 【" + "，".join(parts) + "】")

    elif table_type == "cross_table":
        col_headers = grid[0][1:]   # 第一行（去掉左上角空格）作为列头
        for row in grid[1:]:
            row_header = row[0]     # 第一列作为行头
            for col_h, val in zip(col_headers, row[1:]):
                if val:
                    results.append(f"- {row_header}的{col_h}标准为{val}")

    elif table_type == "kv_table":
        for row in grid:
            if row[0] and row[1]:
                results.append(f"- {row[0]}：{row[1]}")

    return "\n".join(results)
```

**转译效果演示**：

```
原始表格（标准表头表）：
| 功能     | 量程   | 分辨率 | 精确度 |
| 直流电压 | 200mV  | 0.1mV  | ±0.5%  |
| 直流电压 | 20V    | 0.01V  | ±0.5%  |

转译结果：
- 【功能:直流电压，量程:200mV，分辨率:0.1mV，精确度:±0.5%】
- 【功能:直流电压，量程:20V，分辨率:0.01V，精确度:±0.5%】

原始表格（交叉表）：
|          | 良好    | 较弱        | 坏的   |
| 9V电池   | >8.2V  | 7.2至8.2V   | <7.2V |

转译结果：
- 9V电池的良好标准为>8.2V
- 9V电池的较弱标准为7.2至8.2V
- 9V电池的坏的标准为<7.2V
```

* **优点**：
    * **绝对安全**：转译成普通句子后，随意被切分也不会丢失语义。
    * **极度精准**：向量模型对自然语言的 Embedding 效果成倍提升，召回率暴增。
* **缺点**：算法实现极其复杂，极度考验开发者对各类"变态排版"的兼容能力。

---

## 方案四: VLM 视觉语言模型降维引擎

**核心思想**：放弃代码解析，把排版解析工作外包给拥有"视觉"的 AI 智能体。

**实现方式**：
针对**多级嵌套表头**、**表内嵌表**、**跨页断裂表**等无法用代码穷举的极端脏数据，引入"动态路由"机制：

### 步骤一：渲染截图

使用 `html2image` 或 `Playwright` 将复杂的 HTML 表格渲染并保存为图片。本质上是在后台启动一个无界面浏览器（headless browser），让浏览器渲染 HTML，然后截图。

```python
from playwright.sync_api import sync_playwright

def html_to_image(html_content: str, output_path: str = "table.png"):
    """将 HTML 表格渲染为图片"""
    # 包装成完整的 HTML 页面，添加样式让表格更清晰
    full_html = f"""
    <html><body style="padding:20px; font-family:Arial;">
    {html_content}
    </body></html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 无界面模式
        page = browser.new_page()
        page.set_content(full_html)                 # 喂入 HTML
        page.screenshot(path=output_path)           # 截图保存
        browser.close()

    return output_path
```

### 步骤二：多模态提取

将截图转为 Base64，喂给视觉语言大模型（VLM），让 AI 用"眼睛"理解表格：

```python
import base64
from openai import OpenAI

def extract_table_with_vlm(image_path: str) -> str:
    """用视觉大模型提取表格内容"""
    # 1. 图片转 Base64
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    # 2. 调用 VLM
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }},
                {"type": "text", "text": """
                    请将图片中的表格转译为一维自然语言描述。
                    要求：每一行数据独立成句，包含所有列信息。
                    格式：- 【列名1:值1，列名2:值2，...】
                """}
            ]
        }]
    )

    return response.choices[0].message.content
```

### 步骤三：Prompt 约束

要求 VLM 输出展平后的一维自然语言键值对描述，确保输出格式统一、可被下游直接使用。

* **优点**：真正的降维打击，通杀世界上所有人类肉眼能看懂的表格。
* **缺点**：推理耗时极长（单图 3-5 秒），API Token 成本高昂。

---

## 最佳实践：智能路由架构

在实际的企业级流水线中，**单一方案永远不是最优解**。最成熟的架构是 **方案三 + 方案四的混合动态路由**：

> 用极低成本、毫秒级响应的**确定性代码（2D 矩阵投影）**去处理 90% 的常规与不规则合并表格；
> 在算法中埋入"复杂度嗅探器"，一旦检测到极度异常的嵌套结构，则立刻路由给 **VLM 视觉引擎**进行重成本兜底。

```python
def smart_route(html_table: str):
    """智能路由：根据表格复杂度选择处理方案"""
    soup = BeautifulSoup(html_table, "html.parser")

    # 复杂度嗅探
    has_nested_table = soup.find("table").find("table") is not None      # 表中嵌表
    has_deep_rowspan = any(
        int(td.get("rowspan", 1)) > 10 for td in soup.find_all("td")
    )  # 超深跨行

    # 路由决策
    if has_nested_table or has_deep_rowspan:
        # 极端复杂 → 方案四：VLM 视觉引擎兜底
        image_path = html_to_image(html_table)
        return extract_table_with_vlm(image_path)
    else:
        # 常规表格 → 方案三：确定性代码处理
        grid = html_table_to_grid(html_table)
        table_type = detect_table_type(grid)
        return linearize(grid, table_type)
```

这才是确保流入下游的数据做到 100% 纯净无损。

---

## 四种方案对比总结

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 方案一：表格隔离保护法 | 小型标准 Markdown 表格 | 实现简单 | 不支持大表格和 HTML 表格 |
| 方案二：表头续传切分法 | 超大标准表格 | 解决容量超载 | 二维结构影响检索质量 |
| 方案三：降维转译法 | 常规及合并单元格表格 | 语义完整，检索精准 | 算法实现复杂 |
| 方案四：VLM 视觉引擎 | 极端嵌套/跨页表格 | 通杀所有表格 | 耗时长，成本高 |


