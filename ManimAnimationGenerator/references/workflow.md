# 完整工作流程

本文档串联从内容设计到视频发布的全流程，明确各阶段使用的规范和验收清单。

## 阶段一：内容设计

目标：确定教学路径和知识原子。

操作步骤：

1. 遵循 pedagogy_path.md 设计教学路径（覆盖七个阶段）。
2. 查阅 builtin_knowledge.md 确认知识原子及其依赖关系。
3. 如需要，查阅 textbook_sources.md 获取教材引用。
4. 根据学科选择对应的规范文件（physics.md 等）。

输出物：教学路径图、知识原子列表。

验收：人工确认教学路径完整。

## 阶段二：教学路径与内容设计

目标：将知识原子转化为可执行的教学内容文件。

操作步骤：

```
1. 按七阶段规划叙事流，设计每个原子的具体教学内容（定义、直观解释、反直觉澄清等）。
2. 为每个原子分配视觉动作类型。
3. 生成语音文本草案，转义数学符号为自然语言。
4. 自动拆分检查：
   - 检查每个原子的元素数量（> 8 则拆分）
   - 检查预估高度（> 5.5 单位则拆分）
   - 检查预估宽度（> 12 单位则拆分）
   - 重要公式独立成原子
5. 用户逐条确认教学草案。
6. 生成 Markdown 课程文档（人类可读）：
   - 文件名：主题_course.md
   - 内容：按教学阶段组织的自然语言描述
   - **必须包含人工制作时长估算**（每个原子/板块标注预估制作时间，单位：分钟）
   - 无技术字段（type、duration、visual_action 等技术程序字段）
   - 便于用户阅读、校对、讨论
7. 输出独立的 JSON 教学内容文件（机器可读），存放在 courses/ 目录下。
```

输出物：

- Markdown 课程文档：主题\_course.md
- JSON 教学内容文件：courses/主题\_content.json

验收：用户确认教学草案完整，Markdown 文档可读，JSON 文件格式正确，每个原子满足尺寸约束。

示例 JSON：

```json
{
  "topic": "矩阵乘法",
  "version": "1.0",
  "source": "同济高等数学 2.1",
  "prerequisites": ["向量点积", "矩阵基本概念"],
  "atoms": [
    {
      "id": "mat_mul_guess",
      "type": "counter_intuitive",
      "content": "错误猜测：按位相乘",
      "visual_action": "show_wrong_guess",
      "speech": "有人可能会以为矩阵乘法是相同位置直接相乘，但这是错误的。",
      "duration": 6.0
    },
    {
      "id": "mat_mul_definition",
      "type": "definition",
      "content": "(AB)_{ij} = Σ_k A_{ik} B_{kj}",
      "visual_action": "highlight_dot_product",
      "speech": "结果矩阵第 i 行 j 列等于 A 的第 i 行与 B 的第 j 列的点积。",
      "duration": 6.0
    }
  ]
}
```

## 阶段三：代码开发

目标：编写 Manim 动画代码。

操作步骤：

1. 读取阶段二输出的 JSON 教学内容文件（从 courses/ 目录）作为代码生成依据。
2. 参考 layout.md 和 animation.md 确定动画风格。
3. 参考 rendering.md 确定渲染参数。
4. 若内容 > 30 原子或预估时长 > 8 分钟，遵循分场规则拆分场景，每个场景对应独立的 JSON 内容文件和 Python 文件。
5. 编写 Manim 代码（继承 LayoutScene 基类）。

输出物：Python 代码文件（一个或多个）。

验收：使用 verification_checklist.md 逐项自检，全部通过后方可进入渲染。

## 阶段四：渲染与成片验收

目标：生成视频成片并验收。

操作步骤：

1. 渲染每个场景为 MP4（统一分辨率、帧率）。
2. 使用 quality_acceptance.md 验收每个单独场景。
3. 若为多场景，按 rendering.md 中的合并规范使用 FFmpeg 合并。
4. 对合并后的全场视频，再次验收 quality_acceptance.md 中的全场视频专项。

输出物：最终视频成片（MP4）。

验收：

- 单独场景：quality_acceptance.md 中画面与布局、音频与字幕、讲解与知识点全部通过。
- 全场视频：额外通过全场视频专项。

## 阶段五：发布

目标：输出最终视频。

操作步骤：

1. 确认所有验收项通过。
2. 输出最终视频文件。

输出物：发布版视频。

## 文件与阶段对应关系表

```
| 文件 | 所属阶段 | 用途 |
|------|----------|------|
| pedagogy_path.md | 内容设计 | 教学路径规范 |
| builtin_knowledge.md | 内容设计 | 知识原子库 |
| textbook_sources.md | 内容设计 | 教材来源 |
| tts_guide.md | 教学路径与内容设计 | TTS 语音指南 |
| json_schema.md | 内容设计 | JSON 教学内容规范 |
| layout.md | 代码开发 | 布局规范 |
| animation.md | 代码开发 | 动画规范 |
| rendering.md | 代码开发 | 渲染规范 |
| project_structure.md | 代码开发 | 用户项目构建结构 |
| layout_base.py | 代码开发 | 布局底座 |
| tex_tools.py | 代码开发 | LaTeX 工具 |
| validate_course_contents.py | 代码开发 | JSON 校验 |
| split_atom.py | 代码开发 | 原子拆分 |
| verification_checklist.md | 代码开发 | 开发自检清单 |
| quality_acceptance.md | 成片验收 | 成片验收清单 |
| physics.md 等学科文件 | 内容设计/代码开发 | 学科专项规范 |
```

## Markdown 课程文档示例

文件名：matrix_course.md

内容示例：

```
# 矩阵：基础与运算

来源：同济线性代数 第6版 第一章
前置知识：二元一次方程组、向量
制作时长：约 45 分钟

## 激活 — 从方程组引入
> 预估制作时长：8 分钟

我们从熟悉的方程组开始

2x + 3y = 8
4x - y = 3

能否把系数单独提取出来？

系数矩阵 A = [2, 3; 4, -1]

这就是矩阵——系数的矩形表格。

## 直观体验 — 矩阵是空间变换器
> 预估制作时长：12 分钟

矩阵不只是表格。

矩阵 = 空间的变换器。

每个矩阵都代表一种变换规则。

看一个具体例子：缩放变换，放大2倍。

[1, 1] 变成了 [2, 2]。

## 定义 — 矩阵的严格定义
> 预估制作时长：5 分钟

矩阵是由 m 行 n 列数字排列成的矩形数表。

A = [a11, a12, ..., a1n; a21, a22, ..., a2n; ...; am1, am2, ..., amn]

aij 表示第 i 行第 j 列的元素。

## 运算 — 矩阵加法
> 预估制作时长：10 分钟

对应位置元素相加。

[1, 2; 3, 4] + [5, 6; 7, 8] = [6, 8; 10, 12]

## 运算 — 数乘
> 预估制作时长：5 分钟

每个元素乘以常数。

2 * [1, 2; 3, 4] = [2, 4; 6, 8]

## 运算 — 矩阵乘法
> 预估制作时长：15 分钟

Cij = Σ Aik * Bkj

要求：A 的列数 = B 的行数。

## 反直觉 — 乘法不交换
> 预估制作时长：10 分钟

AB != BA

几何解释：先缩放再旋转 != 先旋转再缩放。

## 反直觉 — 为什么没有除法？
> 预估制作时长：8 分钟

原因1：矩阵乘法不满足交换律，除法不唯一。

原因2：不是所有矩阵都可逆。奇异矩阵信息丢失，无法恢复。

原因3：方程可能无解或多解。

替代方案：逆矩阵。

## 应用 — 图像处理

调整亮度：每个像素值乘以系数，图像变亮。

## 总结

矩阵定义 -> 基本运算 -> 乘法（变换复合）

掌握矩阵，就掌握了多维世界的钥匙。

## 思考题

已知 A = [1, 0; 0, 2]，B = [0, 1; 1, 0]

请计算 AB 和 BA，验证它们是否相等。
```

## 快速决策流程图

```
开始
|
内容设计（pedagogy_path.md + builtin_knowledge.md）
|
教学路径与内容设计（用户确认）
|
自动拆分检查（元素数、高度、宽度）
|
生成 Markdown 课程文档（主题_course.md）
|
输出 JSON 教学内容文件（courses/主题_content.json）
|
是否需要拆分？
|- 否 -> 直接编写代码
|- 是 -> 按拆分规则拆分为多个原子 -> 重新输出 JSON
|
编写代码（继承 LayoutScene）
|
开发自检（verification_checklist.md）
|
渲染输出
|
成片验收（quality_acceptance.md）
|
是否多场景？
|- 否 -> 直接发布
|- 是 -> FFmpeg合并 -> 全场专项验收 -> 发布
|
结束
```

## 负向约束（Don't）

> **用途**：当工作流步骤写成这样 → 直接导致返工或事故。Agent 必须避免以下任意一条。
> 对应 SKILL.md 中的 [负向约束速查索引](file:///c:/Users/chenhl/.trae-cn/skills/manimanimationgenerator/SKILL.md#负向约束速查索引dont-quick-reference)。

### W-D1：跳过教学草案 Markdown 用户确认

```python
# ❌ DON'T：直接生成 JSON 和代码，跳过 Markdown 草案
step_json = generate_json(topic)
step_code = generate_code(step_json)  # 无用户确认直接生产

# ✅ DO：必须经过 3 步确认
draft_md = generate_draft_markdown(topic)  # 1. 生成草案
# → 用户审核 Markdown（教学路径/内容/时长）
step_json = update_json_from_draft(draft_md)  # 2. 更新 JSON
# → 用户审核 JSON 细节
step_code = generate_code(step_json)  # 3. 生成代码
```

**画面炸成**：生成内容与用户意图不符 → 返工重做

---

### W-D2：跳过 Gate 3 程序化布局校验

```python
# ❌ DON'T：代码写完直接渲染，跳过 validate_layout()
def construct(self):
    formula = MathTex(r"...")
    self.add(formula)
    self.play(Write(formula))
    self.render()    # 直接渲染，未调用 validate_layout()

# ✅ DO：代码完成后、渲染前必须调用
violations = self.validate_layout(all_mobs)
if violations:
    print("布局违规:", violations)
    return  # 禁止渲染，修复后重试
```

**画面炸成**：布局问题仅在渲染后肉眼可见，修复成本高

---

### W-D3：跳过教学草案时长估算

```python
# ❌ DON'T：每个原子 duration 留默认值 6.0（未按实际内容估算）
atoms = [{"id": "xxx", "duration": 6.0}] * 20  # 全部默认时长

# ✅ DO：每个原子估算人工制作时长，填入 draft_md
atoms_estimated = [
    {"id": "simple_def", "estimated_minutes": 5},    # 简单定义
    {"id": "complex_proof", "estimated_minutes": 15}, # 复杂证明
    {"id": "animation_derivation", "estimated_minutes": 12}  # 动画推导
]
```

**画面炸成**：用户无法估计总制作时长，项目管理失控

---

### W-D4：跨域混用坐标参考系

```python
# ❌ DON'T：混用数学坐标系和像素坐标系
bad_formula = MathTex(r"...").move_to([300, 200, 0])  # 像素坐标
bad_graph = Circle().move_to(axes.c2p(1, 2))          # 数学坐标

# ✅ DO：统一使用数学坐标系（Y轴向上）
all_elements = VGroup(
    MathTex(r"..."),
    Circle()
).move_to(axes.c2p(0, 2))
```

**画面炸成**：公式与图形位置完全不匹配
