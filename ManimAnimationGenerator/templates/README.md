# 课程内容 JSON 模板使用指南

## 用途

本模板用于指导 AI 生成标准化的教学内容 JSON 文件。JSON 文件作为阶段二「教学路径与内容设计」的输出物，供阶段三「代码生成」使用。

## 设计原则

### 1. 内容与表现分离

- JSON 只描述讲什么，不描述怎么画
- 视觉动作通过 visual_action 名称引用，具体实现由代码生成阶段映射到内置动画模板

### 2. 公式与文本分离

- formula 类型禁止包含中文字符
- 中文文本必须使用 content 或 highlight 类型
- 混合内容（中文+公式）必须使用 mixed 类型配合 `tex_template: "ctex"`，不得拆分

### 3. 教学路径完整性

- 一个完整课程应覆盖所有原子类型（缺一不可）：

| 类型              | 含义       | 对应教学阶段 |
| ----------------- | ---------- | ------------ |
| definition        | 形式化定义 | 阶段③        |
| intuition         | 直观体验   | 阶段②        |
| operation         | 运算示范   | 阶段④        |
| counter_intuitive | 反直觉澄清 | 阶段⑤        |
| application       | 应用案例   | 阶段⑥        |
| summary           | 总结回顾   | 阶段⑦        |

### 4. 布局类型说明（atoms[].layout 字段）

| layout 值        | 含义                             | 适用场景                     |
| ---------------- | -------------------------------- | ---------------------------- |
| vertical（默认） | 垂直排列（单栏）                 | 定义、定理、多行推导         |
| two_column       | 两栏布局（主内容区左，图形区右） | 图文对照讲解                 |
| three_column     | 三栏布局（左概念+中公式+右图形） | 复杂运算演示                 |
| centered         | 单独居中                         | 大矩阵、大公式、纯标题过渡页 |

### 5. 最大化匹配

- visual_action 优先使用预置名称，实现精确匹配
- 无预置时，AI 根据 name 和 params 动态生成

## 中文与公式混合处理规则（强制）

核心原则：formula 类型禁止包含中文字符。

### 正确做法：拆分

将混合内容拆分为多个 content 元素：

输入（错误）：
{"text": "矩阵 a\_{ij} 表示第 i 行第 j 列的元素", "type": "formula"}

输出（正确）：
[
{"text": "矩阵 ", "type": "content"},
{"text": "a_{ij}", "type": "formula"},
{"text": " 表示第 i 行第 j 列的元素", "type": "content"}
]

### 常见混合模式拆分示例

| 原始文本                | 拆分结果                                                                                                                    |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 点 A(2,5)               | [{"text": "点 A", "type": "content"}, {"text": "(2,5)", "type": "formula"}]                                                 |
| 矩阵 A = [[1,0],[0,1]]  | [{"text": "矩阵 ", "type": "content"}, {"text": "A = \\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}", "type": "formula"}] |
| 公式 E = mc² 是质能方程 | [{"text": "公式 ", "type": "content"}, {"text": "E = mc^2", "type": "formula"}, {"text": " 是质能方程", "type": "content"}] |
| 矩阵乘法：C = A × B     | [{"text": "矩阵乘法：", "type": "content"}, {"text": "C = A \\times B", "type": "formula"}]                                 |

### 必选方案：mixed 类型 + ctex 模板（强制）

当原子内容包含中文时，必须使用 ctex 模板：

```json
{
  "tex_template": "ctex",
  "content": [
    { "text": "矩阵 $a_{ij}$ 表示第 $i$ 行第 $j$ 列的元素", "type": "mixed" }
  ]
}
```

## 预置 visual_action 名称

| 名称                  | 用途           | 参数示例                                                     |
| --------------------- | -------------- | ------------------------------------------------------------ |
| show_equations        | 展示方程组     | {"equations": ["2x+3y=8", "4x-y=3"], "extract_matrix": true} |
| highlight_matrix_cell | 高亮矩阵单元格 | {"row": 0, "col": 0, "color": "#66DDFF"}                     |
| show_definition       | 展示定义       | {"title": "矩阵定义"}                                        |
| show_intuition        | 展示直观解释   | {"type": "geometric"}                                        |
| show_operation        | 展示运算过程   | {"steps": ["step1", "step2"]}                                |
| show_counter_example  | 展示反直觉例子 | {"wrong": "按位乘", "correct": "行列点积"}                   |
| show_application      | 展示应用案例   | {"case": "image_rotation"}                                   |
| show_summary          | 展示总结       | {"keywords": ["定义", "运算", "应用"]}                       |

## 验证与修复

生成 JSON 后，运行验证脚本：

```bash
# 校验并自动修复
python scripts/validate_course_contents.py --input courses/xxx.json

# 仅校验不修改
python scripts/validate_course_contents.py --input courses/xxx.json --validate-only
```

脚本会自动：

- 检查 JSON 结构是否符合 Schema
- 检测并拆分 formula 中的中文字符
- 补全缺失的默认值（如 duration）
- 验证 layout 字段枚举值是否正确

## 配置文件

- manim.cfg - Manim 渲染配置，使用前复制到项目根目录

## 示例 JSON

见 `examples/matrix_course_example.json`
