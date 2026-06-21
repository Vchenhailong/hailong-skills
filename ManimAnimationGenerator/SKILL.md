---
name: ManimAnimationGenerator
description: 专业的 Manim 结构化知识动画生成专家，提供企业级工程化脚手架，严格遵循量化规则，生成可直接运行、布局规范、不溢出、不重叠、步骤清晰、风格统一、适合学习观看的动画代码和MP4视频文件，使用场景：(1) 生成数学、物理等学科的知识动画 (2) 创建结构化的教学内容动画 (3) 制作步骤清晰的推导过程动画
---

# Manim 数理动画生成专家

## MANDATORY READING ORDER（强制阅读顺序）

**Agent 必须按以下顺序阅读。跳过任一章节将导致关键约束遗漏，直接引发生产事故。**

| 顺序  | 章节                    | 不可跳过的原因          |
| ----- | ----------------------- | ----------------------- |
| **1** | 技能目标（A/B/C）       | 决定所有行为的北极星    |
| **2** | 核心原则（1-11条）      | 不可违反的元规则        |
| **3** | 工作流（显式展露）      | 跳过任意步骤 = 返工     |
| **4** | 验收门禁（5道显式门禁） | 跳过任意门禁 = 缺陷视频 |
| **5** | 代码契约                | 技能核心能力的实现入口  |
| **6** | 排版布局红线            | 违反任意一条 = 布局崩坏 |
| **7** | 依赖与环境 / 示例       | 环境不匹配 = 渲染失败   |

## 技能目标（北极星）

本技能通过三个核心目标驱动所有行为决策：

| 目标                       | 说明                                                     | 核心实现                                                                        |
| -------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **A. 屏蔽 manim 编程工作** | 暴露最少 API，AI 只需调用而非编写底层逻辑                | `LayoutScene` 基类（`scripts/layout/scene_base.py`）                            |
| **B. 解决 manim 核心短板** | 自动完成排版布局、内容缩放、动画处理、字幕处理、时长控制 | `safe_place()` / `validate_layout()` / `subtitle_scroller.py` / `ZoneConstants` |
| **C. 内容驱动生成**        | 用户聚焦纯内容，AI 驱动 manim 输出 MP4                   | JSON 教学内容 + Markdown 教学草案 + 代码生成                                    |

**决策原则**：任何行为选择，以最贴近 A/B/C 三目标的方式决定。

## 核心原则

1. **先数理 → 后坐标 → 再绘图**。禁止硬编码、估算、视觉微调。
   - 坐标必须由数学公式推导（中点、交点、切点等）
   - 几何关系必须验证（距离、角度、平行、垂直、相切）
   - 物理定律必须体现
2. **字幕驱动时长**（动画 + 字幕同步）：场景时长由字幕和内容中较长者决定。字幕按 `duration = chars / 4.0` 计算；无字幕时缓冲 2 秒（动画 0.5s + 缓冲 2s = 2.5s 最小值）。
3. **用户确认后才能生成代码**：知识图谱（含前置知识）和叙事流必须经过用户确认。
4. **内容必须基于权威教材或标准知识库**，所有知识原子需标注真实来源。
5. **教学遵循七阶段路径**：激活前置知识 → 直观体验 → 定义 → 运算 → 反直觉澄清 → 应用 → 总结。
6. **长视频自动分场**：总原子数 > 30 或时长 > 8 分钟时，拆分为多个独立场景。
7. **数学符号必须转义为自然语言读音**（映射表见 `scripts/tex_tools.py::math_symbols_to_speech()`）。
8. **优先使用专业第三方库**：manim-physics / manim-circuit / manim-Astronomy / chanim。
9. **分层基础设施规则**：`scripts/layout/` / `scripts/animation/` / `scripts/validation/` 为基线层，`scripts/physics_graphics.py` 和 `scripts/project_extensions/` 为扩展层。基线层修改会破坏设计契约，禁止随意修改。
10. **布局与字幕强制规则**：所有场景必须遵循排版布局红线（M1-M10）和字幕处理规范（由 `subtitle_scroller.py` 处理），禁止绕过。
11. **CJK 环境自检**：渲染前必须调用 `scripts/environment/cjk_checker.py::check_cached()`（由 `LayoutScene.setup()` 自动触发），不允许渲染到一半才报错。

## 工作流（不可跳过）

遵循四个阶段，★ 表示必须等待用户确认的决策节点。

### 阶段一：需求澄清

1. 根据内置知识树引导用户选择主题节点、深度、参考教材。

### 阶段二：知识拆解与教学设计

2. 生成知识图谱草案（JSON），包含前置知识、原子序列、来源。
3. 按七阶段规划叙事流，设计每个原子的具体教学内容（定义、直观解释、反直觉澄清等）。
4. **★ 用户确认①**：教学内容本身（知识图谱 + 叙事流）。

### 阶段三：教学草案输出

5. 生成**教学草案 Markdown**（`主题_course.md`）— 纯人类可读，无技术字段，每个原子/板块必须标注**人工制作时长估算**（单位：分钟）。
6. 生成**课程结构 JSON**（`courses/主题_content.json`）— 机器可读，含类型/播放时长估算/动画动作等程序字段。
7. **★ 用户确认②**：Markdown 教学草案内容。

### 阶段四：原子拆分优化

8. 调用 `scripts/split_atom.py` 自动检查并拆分超长原子：
   - 元素数量 > 8 → 拆分
   - 预估垂直高度 > 5.5 单位 → 拆分
   - 预估水平宽度 > 12 单位 → 拆分
   - 重要公式独立成原子

### 阶段五：分场规划

9. 若总原子数 > 30 或预估视频时长 > 8 分钟，自动拆分为多个场景文件，每个场景包含 15-30 个原子，每个场景对应独立的 JSON 和 Python 文件。
10. **★ 用户确认③**：分场规划结果。

### 阶段六：代码生成

11. 使用 `scripts/layout/scene_base.py` 中的 `LayoutScene` 基类，为每个场景生成独立 Python 文件。
12. **强制规范**：生成的代码必须符合「排版布局红线」全部要求（M1-M6 / F1-F7），必须使用 `LayoutScene` 基类。

### 阶段七：开发自检

13. 按 `references/verification_checklist.md` 逐项检查每个场景的代码（Gate 3 布局校验必须执行）。
14. **★ 用户确认④**：代码开发自检通过。

### 阶段八：渲染与验收

15. 渲染每个场景为 MP4 文件（统一分辨率、帧率）。
16. **Gate 4 数理正确性检查**：坐标/几何关系/物理定律验证。
17. **Gate 5 成片验收**：`references/quality_acceptance.md` 全部检查项通过。
18. **★ 用户确认⑤**：成片验收通过。

### 阶段九：发布

19. 所有验收项通过后，输出最终视频。

> **禁止跳过声明**：以上任意步骤（尤其是 ★ 决策节点）不可跳过。跳过 = 返工。

## 验收门禁（5道门禁不可跳过）

代码生成和视频输出必须依次通过以下 5 道门禁：

### Gate 1：教学内容 JSON 格式校验

- **触发时机**：教学内容 JSON 生成完成后，代码生成前。
- **执行方式**：`python -m scripts.validation.course_schema_validator --input courses/xxx.json`
- **通过标准**：无错误输出。JSON 必须符合 `references/json_schema.md` 定义的 Schema。

### Gate 2：布局排版门禁

- **触发时机**：教学内容设计完成后，代码生成前。
- **执行方式**：
  1. 基于 `templates/layout_test_template.json` 生成验证场景
  2. 渲染场景（`manim -ql ...`）
  3. 视觉检查：无截断/重叠/溢出、字幕滚动正常
- **通过标准**：估算各区域高宽与位置无问题，方可进入代码生成阶段。

### Gate 3：程序化布局校验（强制执行）

- **触发时机**：代码完成后，渲染前。
- **执行方式**：调用 `scripts/layout/scene_base.py` 中 `LayoutScene.validate_layout()` 方法。
- **检测范围**（9 类违规）：
  | 违规类型 | 说明 |
  | --- | --- |
  | REGION_OVERFLOW | 对象超出区域左右边界 |
  | REGION_INTRUSION | 非字幕对象侵入字幕区 |
  | ELEMENT_OVERLAP | 元素两两重叠且无语义相关 |
  | STACK_OVERFLOW | 多元素堆叠总高度超出区域 |
  | WIDTH_EXCEEDS | 单个元素宽度超出列宽 |
  | ABNORMAL_SPACING | 相邻元素间距过密或过稀 |
  | OVER_DENSE / TOO_SPARSE | 区域填充率异常 |
  | CENTER_OFFSET | 区域内容重心严重偏移 |
  | SCREEN_OUTSIDE | 元素超出屏幕边界 |
- **重叠白名单**（语义相关性唯一基准）：使用 `allowed_overlap_patterns=LayoutScene.ALLOWED_PATTERNS` 自动推断 13 种合法重叠（详见「重叠白名单机制」节）。
- **通过标准**：`validate_layout()` 返回空列表。任意违规必须修复后重检。

### Gate 4：数理正确性检查

- **触发时机**：Gate 3 通过后，渲染前。
- **执行方式**：人工/AI 校验。
- **检查范围**：
  - 坐标必须由数学公式推导，无硬编码 `[x, y, z]`
  - 几何关系验证（距离、角度、平行、垂直、相切）
  - 物理定律体现与验证
- **通过标准**：所有检查项通过。

### Gate 5：成片验收

- **触发时机**：渲染完成后，发布前。
- **执行方式**：`references/quality_acceptance.md` 全部检查项通过。
- **多场景额外检查**：全场视频专项（FFmpeg 合并后再次通过验收清单）。
- **通过标准**：所有勾选框为 `[x]`。

> **禁止跳过声明**：以上 Gate 1-5 顺序不可颠倒，不可跳过。跳过任一门禁 = 缺陷视频。

## 代码契约（技能核心能力 → 实现入口）

### 目标 A：屏蔽 manim 编程工作

| 能力                     | 实现入口                                                              |
| ------------------------ | --------------------------------------------------------------------- |
| 场景基类（强制使用）     | `scripts/layout/scene_base.py` → `LayoutScene`                        |
| 区域划分与安全定位       | `LayoutScene.safe_place()`                                            |
| 布局验证（毫秒级）       | `LayoutScene.validate_layout()`                                       |
| 双栏/三栏布局（含预检）  | `LayoutScene.place_two_column()` / `LayoutScene.place_three_column()` |
| 布局优化器（3 轮降级链） | `scripts/layout/optimizer.py` → `LayoutOptimizer`                     |

### 目标 B：解决 manim 核心短板

| 能力                      | 实现入口                                                                        |
| ------------------------- | ------------------------------------------------------------------------------- |
| 排版布局（区域常量）      | `scripts/layout/constants.py` → `ZoneConstants.compute()`                       |
| 分栏递归闭环              | `ZoneConstants.compute()` → `compute_column_layout()` → `validate_column_fit()` |
| 内容缩放（自动换行/断点） | `LayoutScene._precheck_mobject()` / `LayoutOptimizer._apply_wrap()`             |
| 字幕滚动                  | `scripts/animation/subtitle_scroller.py` → `SubtitleScroller`                   |
| 打字机动画                | `scripts/animation/typewriter.py` → `Typewriter` / `typewriter_in()`            |
| 时长控制（JSON 层）       | `references/json_schema.md` → `duration` 字段 / `subtitle_scroller.py` 滚动同步 |
| CJK 环境自检              | `scripts/environment/cjk_checker.py` → `check_cached()`                         |

### 目标 C：内容驱动生成

| 能力              | 实现入口                                            |
| ----------------- | --------------------------------------------------- |
| JSON 教学内容规范 | `references/json_schema.md`                         |
| JSON Schema 校验  | `scripts/validation/course_schema_validator.py`     |
| 原子拆分          | `scripts/split_atom.py`                             |
| TTS 符号映射      | `scripts/tex_tools.py` → `math_symbols_to_speech()` |
| LaTeX 工具        | `scripts/tex_tools.py` → `latex_to_unicode()`       |

### 物理图元

| 能力                 | 实现入口                                                                   |
| -------------------- | -------------------------------------------------------------------------- |
| 内置物理图元工厂     | `scripts/physics_graphics.py` → `create_force_arrow()` / `create_car()` 等 |
| 第三方库（按需引入） | manim-physics / manim-circuit / manim-Astronomy / chanim                   |

## 必须遵循的具体规范

### 1. 参考文档（设计约束与验收规则来源）

| 规范              | 文件                                   |
| ----------------- | -------------------------------------- |
| 完整工作流程      | `references/workflow.md`               |
| 布局规范          | `references/layout.md`                 |
| 动画规范          | `references/animation.md`              |
| 渲染规范          | `references/rendering.md`              |
| 字幕规范          | `references/subtitle_scroller.md`      |
| JSON 教学内容规范 | `references/json_schema.md`            |
| 物理学科规范      | `references/physics.md`                |
| 电路图绘制设计    | `references/netlist.md`                |
| LaTeX 公式规范    | `references/math_latex.md`             |
| 验证清单          | `references/verification_checklist.md` |
| 成片验收清单      | `references/quality_acceptance.md`     |
| 教学路径设计      | `references/pedagogy_path.md`          |
| TTS 语音指南      | `references/tts_guide.md`              |

### 2. 代码实现引用（技能核心能力入口）

| 能力             | 入口文件                                                                                                                                      |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 分栏布局递归闭环 | `scripts/layout/constants.py`（`ZoneConstants.compute()` / `validate_column_fit()`）→ `scripts/layout/engine.py`（`compute_column_layout()`） |
| 字幕区常量       | `scripts/layout/constants.py`（`SUBTITLE_ZONE_*` 常量）                                                                                       |
| 字幕滚动执行     | `scripts/animation/subtitle_scroller.py`                                                                                                      |

## 排版布局红线（最高优先级 — 不可违反）

### MUST — 强制行为

| 编号 | 规则                                | 正确做法                                                               |
| ---- | ----------------------------------- | ---------------------------------------------------------------------- |
| M1   | **使用 LayoutScene 基类**           | 所有场景类继承 `scripts/layout/scene_base.py` 的 `LayoutScene`         |
| M2   | **仅用 VGroup.arrange() 布局**      | 元素分组后调用 `.arrange(buff=..., direction=...)`                     |
| M3   | **每次添加元素前调用 safe_place()** | `self.safe_place(mobject, region="content")`                           |
| M4   | **使用 axes.c2p() 转换所有坐标**    | `pos = axes.c2p(x, y)` 而非 `[x, y, 0]`                                |
| M5   | **代码生成前必须通过布局验证**      | 先 `validate_layout()`（毫秒级）→ 再渲染视觉确认                       |
| M6   | **涉及坐标计算时必须添加参考系**    | 场景中包含 Axes 或 NumberPlane                                         |
| M7   | **图形始终占分栏宽高的 80%**        | 调用 `scale_to_fit_zone()` 将图形缩放至分栏宽高的 80%                  |
| M8   | **字幕必须使用 SubtitleScroller**   | 字幕滚动由 `scripts/animation/subtitle_scroller.py` 处理，禁止手动实现 |
| M9   | **字幕时长按字符数计算**            | `duration = subtitle_chars / 4.0`，场景时长取字幕与内容的最大值        |
| M10  | **字幕每行最多 20 字符**            | 超长文本由 `split_utterance()` 自动拆分                                |

### FORBIDDEN — 禁止行为

| 编号 | 禁止项                                  | 典型崩坏场景                        |
| ---- | --------------------------------------- | ----------------------------------- |
| F1   | **禁止 .next_to() 用于元素间定位**      | 链式累积误差导致全部错位            |
| F2   | **禁止 .align_to() 用于对齐**           | "看似对齐"实际重叠                  |
| F3   | **禁止 .shift() 用于单个元素微调**      | 1080p 下完美，4K 下飞出屏幕         |
| F4   | **禁止硬编码坐标 [x, y, z]**            | 函数图像与公式标注完全脱节          |
| F5   | **禁止估算距离/角度**                   | 两栏布局左栏侵入右栏区域            |
| F6   | **禁止视觉微调后的代码**                | 字幕行高变化时公式被遮挡            |
| F7   | **禁止跳过 validate_layout() 直接渲染** | 渲染 5 分钟后才发现可提前捕获的问题 |

> **唯一例外**：`.shift()` 仅允许用于整体 VGroup 的全局位置调整，禁止用于单个子元素的定位修正。

### 坐标参考系约束

- 涉及坐标计算的场景必须添加 Axes 或 NumberPlane
- 必须使用 `axes.c2p(x, y)` 转换坐标，禁止硬编码 `[x, y, z]`
- 开发调试阶段保留坐标参考系，最终版本可隐藏

### 重叠白名单机制（语义相关性唯一基准）

> **唯一判定基准**：语义相关 → 允许；语义无关 → 禁止。

**13 种预定义合法重叠模式**（详细代码实现见 `scripts/layout/scene_base.py` → `ALLOWED_PATTERNS`）：

| 类别   | 模式名                        | 合法重叠                         |
| ------ | ----------------------------- | -------------------------------- |
| 物理类 | `physics_scene_catch_all`     | 物理图元（19类）之间天然语义相关 |
| 物理类 | `force_arrow_on_object`       | 力矢量 ↔ 受力物体                |
| 物理类 | `wire_to_component`           | 导线 ↔ 电路元件                  |
| 物理类 | `object_submerged_in_liquid`  | 物体 ↔ 液体填充区                |
| 数学类 | `axis_tick_label`             | 坐标轴刻度 ↔ 轴线                |
| 数学类 | `geometry_vertex_point`       | 顶点标记 ↔ 几何图形              |
| 数学类 | `auxiliary_line_on_figure`    | 辅助线 ↔ 主图形                  |
| 数学类 | `angle_mark_at_vertex`        | 角度弧 ↔ 顶点                    |
| 数学类 | `geometry_label_on_figure`    | 标注文本 ↔ 几何图形              |
| 数学类 | `perpendicular_parallel_mark` | ⊥∥ 符号 ↔ 线段                   |
| 数学类 | `dimension_arrow_on_segment`  | 尺寸标注 ↔ 线段                  |
| 数学类 | `curve_annotation`            | 切线/法线 ↔ 曲线                 |
| 通用   | `label_on_target`             | 任意标注文本 ↔ 目标对象          |

> **使用方式**：`self.validate_layout(all_mobjects, allowed_overlap_patterns=LayoutScene.ALLOWED_PATTERNS)`

### 违规处置

| 等级 | 触发条件                   | 处置方式                                                   |
| ---- | -------------------------- | ---------------------------------------------------------- |
| A    | F1-F3 违反                 | 立即停止，回退重新设计                                     |
| B    | F4-F6 违反                 | 标记"需重构"，禁止渲染                                     |
| C    | M1-M6 未执行               | 补充缺失步骤后重新验证                                     |
| D    | validate_layout() 返回违规 | 自动 `handle_violation()` 优化；失败则标注"需人工拆分原子" |

## 负向约束速查索引（Don't Quick Reference）

> 以下各领域详细违禁样例归属对应 reference 文件，每条均为已知生产事故的根因。

| 领域           | Don't 节位置                                    | 核心违禁                                               |
| -------------- | ----------------------------------------------- | ------------------------------------------------------ |
| **布局排版**   | `references/layout.md` — 附录A                  | 硬编码坐标 / 单元素 shift / 跳过 validate_layout       |
| **LaTeX 公式** | `references/math_latex.md` — §10                | 中文入 MathTex / 未用 ctex / 下标缺花括号              |
| **物理图元**   | `references/physics.md` — §16                   | 力矢量颜色混乱 / 导线 T 型无圆点 / 浮力物体无轮廓区分  |
| **字幕**       | `references/verification_checklist.md` — 字幕节 | 时长不同步 / 单行超过 20 字 / 字幕侵入内容区           |
| **TTS**        | `references/tts_guide.md` — 负向约束            | 符号未映射 / LaTeX 分隔符未清除 / highlight_range 越界 |
| **工作流**     | `references/workflow.md` — 负向约束             | 跳过 Markdown 确认 / 跳过 Gate 3 校验 / 跳过时长估算   |
| **综合**       | `references/layout.md` — 附录A                  | 跨域混用坐标 / 未配重叠白名单                          |

## 枚举值约束（强制执行）

- `atoms[].type`：只能使用 `definition`, `intuition`, `operation`, `counter_intuitive`, `application`, `summary`
- `atoms[].layout`：只能使用 `vertical`, `two_column`, `three_column`, `centered`
- `content[].type`：只能使用 `highlight`, `content`, `formula`, `mixed`
- `graphics.type`：只能使用 `axes`, `function`, `polygon`, `linear_algebra`, `matrix_animation`, `comparison`, `image_effect`, `physics`, `three_d`
- `animation.type`：只能使用 `fade_in`, `typewriter`, `highlight`, `slide_in`, `scale_in`, `bounce`, `blink`

**禁止**：自行增加未定义的枚举值。

## 依赖与环境

- Python >= 3.11
- Manim CE >= 0.17.3
- manim-voiceover[all] >= 0.3.6
- **专业物理/化学/天体动画库**（按需安装）：
  - `manim-physics`：刚体力学、电磁场、波动
  - `manim-circuit`：专业级电路图元件
  - `manim-Astronomy`：天体运动轨道
  - `chanim`：化学分子结构
- 系统级依赖：PortAudio、SoX、gettext、ffmpeg、TexLive/MiKTeX
- 云端 TTS 账号（阿里云/豆包/Azure）或 EdgeTTS（备选）
- 渲染必须添加 `--disable_caching` 标志

## 调试模式

- 开发阶段：设置 `debug=True`，显示坐标参考系（网格、刻度）
- 生产阶段：设置 `debug=False`，隐藏坐标参考系
- 调用方式：`self.add_coordinate_reference(debug=True)`
- 布局边界可视化：`self.draw_zone_boundaries(layout_mode="two_column")`

## 字幕处理规范

| 规则                   | 取值                                  | 常量                                       |
| ---------------------- | ------------------------------------- | ------------------------------------------ |
| 每行最大字符数         | **20 字符**                           | `ZoneConstants.SUBTITLE_CHARS_PER_LINE`    |
| 字幕区同时显示最大行数 | **2 行**                              | `ZoneConstants.SUBTITLE_VISIBLE_LINES_MAX` |
| 语音朗读速度           | **4 字符/秒**                         | `ZoneConstants.SUBTITLE_SPEECH_RATE`       |
| 单原子 duration 计算   | **`duration = subtitle_chars / 4.0`** | `ZoneConstants.SUBTITLE_DURATION_FORMULA`  |
| 字幕区底部固定 Y       | **-3.85**                             | `SUBTITLE_ZONE_BOTTOM_FIXED_Y`             |
| 字幕区顶部上界 Y       | **-2.8**                              | `SUBTITLE_ZONE_TOP_Y`                      |

## 示例与测试

见 `examples/README.md`
