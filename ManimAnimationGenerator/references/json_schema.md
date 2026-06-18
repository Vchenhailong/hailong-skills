# JSON 教学内容文件规范

## 1. 强制前提：从 JSON 文件读取

代码生成阶段（工作流阶段三）**必须**从阶段二输出的 JSON 教学内容文件中读取数据，**禁止** AI 自行重写或解释教学内容。

JSON 文件路径示例：courses/主题\_content.json

读取方式：

```python
import json
with open("courses/matrix_content.json", "r", encoding="utf-8") as f:
    content_data = json.load(f)

for atom in content_data["atoms"]:
    for item in atom["content"]:
        # 按 type 字段渲染
```

若 JSON 文件不存在或格式错误，AI **必须报错并终止**，不得继续生成代码。

## 2. JSON Schema 完整定义

### 2.1 顶层结构

| 字段          | 类型   | 必填 | 说明                             |
| ------------- | ------ | ---- | -------------------------------- |
| topic         | string | 是   | 主题名称                         |
| version       | string | 是   | 版本号                           |
| source        | string | 否   | 教材或知识库来源                 |
| prerequisites | array  | 否   | 前置知识列表，每项为 string      |
| atoms         | array  | 是   | 教学原子序列，每个元素为原子对象 |

### 2.2 原子对象结构

| 字段          | 类型   | 必填 | 说明                                                      |
| ------------- | ------ | ---- | --------------------------------------------------------- |
| id            | string | 是   | 原子唯一标识，如 "mat_mul_definition"                     |
| type          | string | 是   | 原子类型（见下方类型说明）                                |
| content       | array  | 是   | 内容数组，至少一个元素                                    |
| layout        | string | 否   | 布局类型：vertical / two_column / three_column / centered |
| tex_template  | string | 否   | LaTeX 模板：默认空（使用拆分），"ctex" 时使用 ctex 模板   |
| graphics      | object | 否   | 图形绘制描述                                              |
| visual_action | string | 否   | 视觉动作类型                                              |
| speech        | string | 否   | 语音文本（无语音时可省略）                                |
| duration      | number | 是   | 预计时长（秒），无字幕默认 2.5（动画0.5s+缓冲2s）         |

**duration 计算规则（强制）**：

`duration` 必须基于 `speech` 字段的字符数按以下公式计算，**禁止随意填写**：

```
字幕驱动：duration = speech_chars / 4.0
无字幕：duration = 2.5（最小值）
```

- 若计算结果 < 3.0 → 取 3.0（最短朗读时长）
- 若计算结果 > 20.0 → 必须**拆分原子**（将当前 atom 拆为多个，每个 duration ≤ 20.0）
- `speech` 为空时 → duration 默认取 2.5

示例：speech = "受力分析是力学的基础方法"（13 字符）→ expected = 13/4 = 3.25 → duration = 4.0

**原子类型说明**：

| type 值           | 含义         | 对应教学阶段 | 说明                             |
| ----------------- | ------------ | ------------ | -------------------------------- |
| definition        | 形式化定义   | 阶段③        | 给出严谨的数学定义或定理表述     |
| intuition         | 直观体验     | 阶段②        | 用动画、生活类比建立感性认识     |
| operation         | 运算示范     | 阶段④        | 展示如何应用规则进行计算或推导   |
| counter_intuitive | 反直觉点澄清 | 阶段⑤        | 先展示错误猜测，再证伪并解释原因 |
| application       | 应用与迁移   | 阶段⑥        | 展示生活或工程案例，体现概念价值 |
| summary           | 总结与回顾   | 阶段⑦        | 梳理核心要点，展示知识网络图     |

**注意事项**：

- 每个教学路径应至少包含 definition、intuition、operation、counter_intuitive、application、summary 各至少一个
- counter_intuitive 类型的原子必须包含证伪步骤（先展示错误，再展示正确）
- 若某概念无常见反直觉点，可省略 counter_intuitive，但需在注释中说明

### 2.3 content 数组元素结构

| 字段 | 类型   | 必填 | 说明                                               |
| ---- | ------ | ---- | -------------------------------------------------- |
| text | string | 是   | 要显示的文本内容，对于 formula 类型为 LaTeX 表达式 |
| type | string | 是   | 内容类型：highlight / content / formula / mixed    |

注：mixed 类型仅在 tex_template 为 "ctex" 时使用，表示中文与公式混合在同一个字符串中。

### 2.4 类型定义与渲染规则

| type      | 含义     | 渲染方式               | 颜色            | 是否支持中文 | 示例 text                |
| --------- | -------- | ---------------------- | --------------- | ------------ | ------------------------ |
| highlight | 强调文本 | Text()                 | #66DDFF（浅蓝） | 支持         | "等比例缩放"             |
| content   | 普通文本 | Text()                 | #FFFFFF（白色） | 支持         | "信息完整保留"           |
| formula   | 数学公式 | MathTex()              | #FFFFFF（白色） | 禁止         | "E = mc^2"               |
| mixed     | 混合内容 | Tex(tex_template=ctex) | #FFFFFF（白色） | 支持         | "矩阵 $a_{ij}$ 表示元素" |

**类型映射规则**（兼容旧格式）：

- type: "text" -> 自动映射为 content
- type: "title" -> 自动映射为 highlight

**禁止行为**：

- 禁止使用 type: "text" 标记公式（应使用 formula）
- 禁止使用 type: "title" 标记普通文本（应使用 content 或 highlight）
- 禁止在 formula 中包含中文字符
- 禁止在 formula 中使用 Tex()（统一使用 MathTex()）

### 2.4.1 中英文混合的处理方式（强制）

**强制要求**：包含中文的 LaTeX 内容**必须**使用 ctex 模板，不得拆分。

- 使用 Tex + ctex 模板，中文和公式写在同一个字符串中
- JSON 中必须声明 `tex_template: "ctex"`
- 环境要求：已安装 ctex 宏包，使用 xelatex 编译器

JSON 示例：

```

{
"id": "mixed*formula",
"type": "definition",
"tex_template": "ctex",
"content": [
{"text": "矩阵 $a*{ij}$ 表示第 $i$ 行第 $j$ 列的元素", "type": "mixed"}
]
}

```

### 2.5 formula 类型的特殊处理

**核心原则**：formula 类型中禁止包含中文字符。

当 type 为 formula 时，AI 必须：

1. **检查是否包含中文**：
   - 若 text 字段中包含中文字符（匹配正则 `[\u4e00-\u9fff]`），**必须报错**，提示使用 mixed 类型 + `tex_template: "ctex"`
   - 正确做法：使用 mixed 类型并指定 `"tex_template": "ctex"`
   - 错误做法：`{"text": "矩阵 a_{ij} 表示第 $i$ 行", "type": "formula"}`

2. **拆分示例**：

输入（错误）：
{"text": "矩阵 a\_{ij} 表示第 i 行第 j 列的元素", "type": "formula"}

输出（正确）：

```json
[
  { "text": "矩阵 ", "type": "content" },
  { "text": "a_{ij}", "type": "formula" },
  { "text": " 表示第 i 行第 j 列的元素", "type": "content" }
]
```

3. **LaTeX 语法验证**：
   - 检查括号匹配
   - 检查反斜杠转义
   - 禁止使用化学专用命令（如 \ce）
   - 禁止使用 \text{} 包裹中文（应直接拆分）

4. **长公式处理**：
   - 预估宽度 > 13.5 单位时，自动拆分为多行（使用 align\* 环境）

5. **纯公式渲染**：
   - 确认无中文后，使用 MathTex(r"text") 渲染（不使用 Tex）

### 2.6 组合渲染示例

输入 JSON：

```json
{
  "content": [
    { "text": "等比例缩放", "type": "highlight" },
    { "text": "：信息完整保留", "type": "content" },
    {
      "text": "\\begin{pmatrix} 2 & 0 \\\\ 0 & 2 \\end{pmatrix}",
      "type": "formula"
    }
  ]
}
```

渲染代码：

```python
def has_chinese(text):
    import re
    return bool(re.search(r'[\u4e00-\u9fff]', text))

items = []
for item in content:
    if item["type"] == "highlight":
        obj = Text(item["text"], color="#66DDFF", font_size=34)
    elif item["type"] == "content":
        obj = Text(item["text"], color=WHITE, font_size=34)
    elif item["type"] == "formula":
        # formula 已确保无中文，直接使用 MathTex
        obj = MathTex(item["text"], font_size=34)
    items.append(obj)

group = VGroup(*items).arrange(DOWN, buff=0.4, center=True)
```

### 2.7 注意事项

- highlight 和 content 类型不能包含 LaTeX 命令
- 如需在普通文本中使用数学符号（如 ≠），直接使用 Unicode 字符，不要用 \neq
- 数学公式中的特殊符号（如 \neq）会在语音生成时自动转义

## 3. 文件组织

- 所有 JSON 教学内容文件放在 `courses/` 目录下
- 命名规则：主题\_content.json（如 matrix_content.json）
- 分场时：主题\_序号\_content.json（如 matrix_01_content.json）

## 4. 验证清单

- [ ] 代码中已添加读取 JSON 教学内容文件的逻辑（json.load()）
- [ ] JSON 文件路径正确（courses/目录）
- [ ] 代码中的公式/文本与 JSON 文件的 content 数组一一对应，无遗漏
- [ ] content 数组中的 formula 类型已正确转换为 MathTex
- [ ] mixed 类型已配合 tex_template: "ctex" 使用
- [ ] 含中文的公式已拆分，无中文混入 formula
- [ ] layout 字段取值正确（vertical / two_column / three_column / centered）
