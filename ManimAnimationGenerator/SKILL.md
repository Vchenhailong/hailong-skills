---
name: ManimAnimationGenerator
description: 专业的 Manim 结构化知识动画生成专家，提供企业级工程化脚手架，严格遵循量化规则，生成可直接运行、布局规范、不溢出、不重叠、步骤清晰、风格统一、适合学习观看的动画代码和MP4视频文件。使用场景：(1) 生成数学、物理等学科的知识动画 (2) 创建结构化的教学内容动画 (3) 制作步骤清晰的推导过程动画
---

# Manim 数理动画生成专家

## ⚠️ MANDATORY READING ORDER（强制阅读顺序）

**Agent 必须按以下顺序阅读 SKILL.md，必须严格执行工作流和验收门禁；后续各节均为基于前置内容的精确展开。**

> 除了系统级依赖外，应用级的所有库安装均需激活虚拟环境，并在虚拟环境内进行，避免与系统环境冲突。
> **跳过前置章节将导致关键约束遗漏，直接引发生产事故。**

```markdown
| 顺序   | 章节                                                              | 说明                             | 不可跳过的原因               |
| ------ | ----------------------------------------------------------------- | -------------------------------- | ---------------------------- |
| **1**  | [核心原则](#核心原则)                                             | 1-8 条，不可违反                 | 所有后续约束均源于此         |
| **2**  | [排版布局绝对遵循红线](#排版布局绝对遵循红线最高优先级--不可违反) | M1-M6 / F1-F7 强制行为/禁止项    | 违反任意一条即触发布局崩坏   |
| **3**  | [依赖与环境](#依赖与环境)                                         | Manim 版本/字体/命令格式         | 版本不匹配直接导致渲染失败   |
| **4**  | [调试模式](#调试模式)                                             | --debug 渲染/布局校验            | 无法定位违规时必须启用       |
| **5**  | [工程化脚手架说明](#工程化脚手架说明)                             | 场景基类/动画模块/工具函数位置   | 使用错误的基类导致继承链断裂 |
| **6**  | [工作流（用户-AI协作）](#工作流用户-ai协作)                       | 7 步流程，用户确认节点           | 跳过确认节点导致返工         |
| **7**  | [验收门禁（5道门禁）](#验收门禁5道门禁)                           | G1 JSON 校验 → G5 成片验收       | 跳门禁直接跳过关键检查点     |
| **8**  | [必须遵循的具体规范](#必须遵循的具体规范)                         | 字幕/字体/LaTeX/颜色等           | 非红线但直接影响成品质量     |
| **9**  | [模板库 + 脚本模板](#模板库--脚本模板)                            | course_template.json / manim.cfg | 使用旧模板导致字段缺失       |
| **10** | [示例与测试](#示例与测试)                                         | 示例命令/测试用例                | 缺少运行验证导致渲染失败     |
```

**其余 references/ 下的参考文档按需加载**，但加载顺序如下（高优先级在前）：

```

workflow.md → pedagogy_path.md → layout.md → json_schema.md →
physics.md → math_latex.md → animation.md → tts_guide.md →
quality_acceptance.md → verification_checklist.md →
rendering.md → textbook_sources.md → project_structure.md →
builtin_knowledge.md

```

## 角色定位

你是专业的 Manim 结构化数理动画生成专家，同时提供**企业级工程化脚手架**。严格遵循数理精确性、动画呈现规范、教学路径设计，旨在解决学习知识无路径、知其然而不知所以然的问题，通过详细、清晰的呈现与详细表述，生成可直接运行、内容正确、布局规范、音画同步、易于理解的动画代码。

## 核心原则

1. 先数理 -> 后坐标 -> 再绘图。禁止硬编码、估算、视觉微调。
   **数理正确性要求**：所有坐标必须由数学公式推导（中点、交点、切点等）；几何关系必须验证（距离、角度、平行、垂直、相切）；物理定律必须体现。
   **坐标参考系要求**：涉及坐标计算的场景必须添加 Axes 或 NumberPlane 作为参考系，使用 axes.c2p() 转换坐标。
   **布局约束要求**：详见「排版布局绝对遵循红线」（MUST M1-M6 / FORBIDDEN F1-F7）。
2. 每步 6 秒（0.5 秒动画 + 5.5 秒语音/缓冲），公式不割裂。
3. 用户必须确认知识图谱（含前置知识）和叙事流后才能生成代码。
4. 支持快速模式（跳过确认）和专家模式（完整协作）。
5. 内容必须基于权威教材或标准知识库，禁止编造。所有知识原子需标注真实来源。
6. 教学必须遵循激活前置知识 -> 直观体验 -> 定义 -> 运算 -> 反直觉澄清 -> 应用 -> 总结的七阶段路径。每个知识点的讲解深度需满足 references/pedagogy_path.md 中的讲解深度规范。
7. 支持将长视频拆分为多个独立场景（分场），并可选择合并为全场视频。
8. 语音生成必须将数学符号（包括 Unicode 和 LaTeX）转义为自然语言读音，具体映射表见 `references/tts_guide.md`。
9. **优先使用专业第三方库**：当技能中未实现特定图元时，必须优先使用以下成熟的第三方库，而非自行实现：
   - **`manim-physics`**：刚体力学（重力、碰撞、弹性）、电磁场、波动
   - **`manim-circuit`**：电路元件（电阻、电感、电容、导线，专业级电路图绘制）
   - **`manim-Astronomy`**：天体运动（行星轨道、恒星、时空网格）
   - **`chanim`**：化学分子结构、反应动画
   - **使用原则**：
     - 检查技能 `scripts/physics_graphics.py` 是否已实现该图元
     - 未实现 → 优先使用上述第三方库
     - 第三方库也无 → 才在技能中新增实现
10. **分层基础设施规则**：`scripts/` 按"基线 / 扩展"两层管理——
    - **基线层**（**默认使用技能版本**；项目可基于实际需要更新复制后的基线文件）：`scripts/layout/`、`scripts/animation/`、`scripts/validation/`、`templates/` 的结构部分
    - **扩展层**（项目可按需补充图元/工具，**可基于实际需要更新复制后的基线文件**）：`scripts/physics_graphics.py`（可追加 `create_*` 函数）、新增 `scripts/project_extensions/` 子目录
    - **基线保护原因**：布局引擎 / 区域定义 / 校验器 / 字幕滚动器是核心约束链，修改会破坏技能的设计契约；扩展层与基线层不冲突，新图元走 VGroup 组装、不硬编码坐标、不绕过 `safe_place()` 即可
    - **同步声明**：`scripts/environment/` 是基线新增（见原则 11），与布局引擎同级保护

11. **CJK 环境自检规则**：渲染前必须调用 `scripts/environment/cjk_checker.py::check_cached()`，由 `LayoutScene.setup()` 钩子自动触发，**不允许**渲染到一半才报错。检测内容包括：
    - LaTeX 引擎可用性（pdflatex / xelatex / lualatex）
    - CJK 宏包可用性（xeCJK / CJKutf8 / ctex / fontspec）
    - 中文字体可用性（Microsoft YaHei / Noto Sans CJK / 思源黑体）
    - 推荐渲染路径：`tex_minipage` / `tex_standard` / `text_pango_only`
    缺失组件时通过 `cjk_installer.install_suggested_commands()` 输出安装建议，**默认仅打印命令不自动执行**（`auto_install=True` 才执行，且 Windows 上拒绝自动安装）。

## 工作流（用户-AI 协作）

遵循 references/workflow.md 定义的四个阶段，具体协作步骤如下：

1. **需求澄清**：根据内置知识树引导用户选择主题节点、深度、参考教材。
2. **知识拆解**：生成知识图谱草案（JSON），包含前置知识、原子序列、来源。用户确认。
3. **教学路径与内容设计**：按七阶段规划叙事流，设计每个原子的具体教学内容（定义、直观解释、反直觉澄清等）。同步生成两个产物：
   - **教学草案 Markdown**（`主题_course.md`）— 纯人类可读，无技术字段，用户逐条审核；每个原子/板块必须标注**人工制作时长估算**（单位：分钟）
   - **课程结构 JSON**（`courses/主题_content.json`）— 机器可读，含类型/播放时长估算/动画动作等程序字段
4. **原子拆分优化**：调用项目中的 `scripts/split_atom.py` 自动检查并拆分超长原子：
   - 元素数量 > 8 时拆分
   - 预估垂直高度 > 5.5 单位时拆分
   - 预估水平宽度 > 12 单位时拆分
   - 重要公式独立成原子
   - 用户确认教学草案（Markdown）后，同步更新对应的 JSON 内容文件（存放在 courses/ 目录）。JSON 必须遵守 `references/json_schema.md` 规范。
5. **分场规划**：若总原子数超过 30 个（或预估视频时长大于 8 分钟），自动拆分为多个场景文件，每个场景包含 15 到 30 个原子，保证独立完整性。每个场景对应独立的 JSON 和 Python 文件。
6. **代码生成**：使用 `scripts/layout/scene_base.py` 中的 `LayoutScene` 基类，为每个场景生成独立 Python 文件，并提供可选的合并脚本（使用 ffmpeg 拼接视频和音频）。
   - **强制规范**：生成的代码必须符合「排版布局绝对遵循红线」全部要求（M1-M6 / F1-F7），使用 `LayoutScene` 基类。
7. **开发自检**：按 `references/verification_checklist.md` 逐项检查每个场景的代码。全部通过后方可进入渲染。
8. **渲染输出**：渲染每个场景为 MP4 文件（统一分辨率、帧率）。
9. **成片验收**：按 `references/quality_acceptance.md` 检查视频成品。若为多场景合并视频，需额外通过全场视频专项。
10. **发布**：所有验收项通过后输出最终视频。

详细流程、阶段划分、决策流程图见 `references/workflow.md`。

## 验收门禁

代码生成和视频输出必须通过5道验收门禁：

### 第一道：教学内容 JSON 格式校验（教学内容生成完成后）

- 运行项目中的 JSON Schema 验证器：`python -m scripts.validation.course_schema_validator --input courses/xxx.json`（或使用便捷脚本 `scripts/validate_course_contents.py`）
- 必须遵循 `references/json_schema.md` 中定义的 Schema
- 通过标准：无错误输出，方可进入下一步

### 第二道：布局排版门禁（教学内容设计完成后、代码生成前）

> 本门禁是「排版布局绝对遵循红线」M5（代码生成前必须通过布局验证渲染）的具体执行节点。

**执行要求**：

- 基于 `templates/layout_test_template.json`，用当前项目真实数据替换后生成验证场景并渲染
- 渲染后检查：无截断/重叠/溢出、字幕滚动正常、单栏/两栏/三栏各自符合区域约束
- **禁止**：直接使用硬编码 Python 验证场景而不基于 JSON 模板和实际数据
- 通过标准：视觉检查（即使不具备视觉能力，也需要估算各区域和区域内容的高宽与位置）无问题 -> 方可进入代码生成阶段
- 未通过 -> 按「红线」第四节的违规处置流程执行

### 第三道：程序化布局校验门禁（代码完成后、渲染前）

> 本门禁是「程序化布局校验」原则的具体执行节点。所有布局问题在渲染前被程序化检测，无需依赖肉眼渲染。

**执行要求**：

- 调用 `scripts/layout/scene_base.py` 中的 `validate_layout()` 方法（9 类违规检测，详见「红线」3.5 节）
- 检查范围：区域溢出、元素重叠、字幕侵入、堆叠溢出、间距异常、填充率、重心偏移
- 重叠判定使用「语义相关性唯一基准」—— 语义相关则通过，语义无关则报告违规
- 支持传入 `allowed_overlap_pairs` 和 `allowed_overlap_patterns` 自定义白名单
- 通过标准：`validate_layout()` 返回空列表（零违规），方可进入数理正确性验证
- 未通过 -> 按「红线」违规处置流程（A/B/C 级）执行

### 第四道：数理正确性检查与验证（代码完成后、渲染前）

- 坐标与坐标上的图像，必须数理验证通过
- 几何关系必须数理验证通过
- 检查物理定律是否体现，且物理数学验证通过
- **通过标准：所有检查项通过，方可进入渲染**

#### G-tts：TTS 节奏对齐校验（代码完成后、渲染前）

> **为什么需要此门禁**：tts_guide.md 与 subtitle_scroller.py 已存在，但 course_template.json 未强制 step 层绑定 TTS 三段对齐。
> Agent 易跳过 TTS 节奏控制，导致音画不同步或字幕与公式原子不对应。

**校验内容**：

| #       | 校验项                           | 判定规则                                                              | 违规后果                            |
| ------- | -------------------------------- | --------------------------------------------------------------------- | ----------------------------------- |
| G-tts-1 | **tts_text 非空**                | 每个教学步骤必须包含 TTS 文案（不可留空）                             | 跳过 TTS 节奏控制，音画脱节         |
| G-tts-2 | **duration 充足**                | `duration >= 3.0 秒`（最小朗读时长）                                  | 时长过短导致语速过快/字幕闪退       |
| G-tts-3 | **highlight_range 匹配公式原子** | `highlight_range` 范围必须覆盖 content 中的 formula 类型项            | 字幕高亮与公式不对应，观感混乱      |
| G-tts-4 | **TTS 文本不含未转义符号**       | `_ ^ { } $ \` 等符号必须在 TTS 前通过 `math_symbols_to_speech()` 映射 | TTS 引擎读出 LaTeX 代码而非自然语言 |

**实现位置**：场景代码中每个 step 对应的字幕生成逻辑处（`subtitle_scroller.py`）。

**通过标准**：tts_text 非空 + duration >= 3s + highlight_range 覆盖公式原子 + 符号已映射，方可进入渲染。

### 第五道：成片验收门禁（渲染后、发布前）

- 执行 `references/quality_acceptance.md` 中的所有检查项。
- 若为多场景合并视频，需额外通过全场视频专项检查。
- 通过标准：所有勾选框为 [x]，方可发布。

## **必须** 遵循的具体规范

- 完整工作流程：`references/workflow.md`
- 用户项目构建结构：`references/project_structure.md`
- 布局规范：`references/layout.md`
- **分栏布局递归闭环**（强制执行）：
  - 流程：分配宽度 → 内容适配 → 计算高度 → 顶部对齐 → 检测溢出 → 必要时拆分 → 重新分配 → 直到通过
  - 调用接口：`ZoneConstants.compute()` → `compute_column_layout()` → `validate_column_fit()`
  - 递归上限：3 次（超过标记需人工干预）
  - 溢出处理优先级：①缩小字号 → ②换行 → ③拆分原子
- **字幕区规范**（扩展）：字体大小↔行高换算、底部固定位置、上界约束、底衬+强调条视觉设计
- 动画规范：`references/animation.md`
- 渲染规范：`references/rendering.md`
- JSON 教学内容规范：`references/json_schema.md`
- 物理学科规范：`references/physics.md`（含第 15 节物理绘图图元规范：力学矢量/电路元件/浮力流体/图层优先级；**含第 8.4 节电路图数理验证规则**；**含 15.1.1 受力点选择规范（强制）：G/N/f/F/T 各类力的作用点选取细则与常见错误对照**）
- LaTeX 公式规范：`references/math_latex.md`
- 验证清单：`references/verification_checklist.md`
- 成片验收清单：`references/quality_acceptance.md`
- 内置知识库：`references/builtin_knowledge.md`
- 教材与知识检索：`references/textbook_sources.md`
- 教学路径设计：`references/pedagogy_path.md`
- TTS 语音指南：`references/tts_guide.md`

### 坐标参考系约束（强制执行）

- 涉及坐标计算的场景必须添加 Axes 或 NumberPlane
- 必须使用 `axes.c2p(x, y)` 转换坐标，禁止硬编码 `[x, y, z]`
- 开发调试阶段保留坐标参考系，最终版本可隐藏

### 枚举值约束（强制执行）

- `atoms[].type` 只能使用：`definition`, `intuition`, `operation`, `counter_intuitive`, `application`, `summary`
- `atoms[].layout` 只能使用：`vertical`, `two_column`, `three_column`, `centered`
- `content[].type` 只能使用：`highlight`, `content`, `formula`, `mixed`
- `graphics.type` 只能使用：`axes`, `function`, `polygon`, `linear_algebra`, `matrix_animation`, `comparison`, `image_effect`, `physics`, `three_d`
- `animation.type` 只能使用：`fade_in`, `typewriter`, `highlight`, `slide_in`, `scale_in`, `bounce`, `blink`

**禁止**：自行增加未定义的枚举值。

## 负向约束速查索引（Don't Quick Reference）

> **说明**：以下各领域详细违禁样例（Don't）归属到对应 reference 文件。每个 Don't 条目均包含**代码反例**和**画面崩坏结果**。
> 负向约束（Don't）记忆强度远高于正向建议（Do），每条均为已知生产事故的根因。

| 领域           | Don't 节位置                                                                              | 核心违禁                                                        |
| -------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **布局排版**   | [layout.md — 附录A](references/layout.md#附录a-负向约束速查dont)                          | 硬编码坐标 / 单元素 shift / 跳过 validate_layout                |
| **LaTeX 公式** | [math_latex.md — 10. LaTeX Don't](references/math_latex.md#10-latex-dont-违禁样例库)      | 中文入 MathTex / 未用 ctex / Text() 渲染数学内容 / 下标缺花括号 |
| **物理图元**   | [physics.md — 16. 物理绘图 Don't](references/physics.md#16-物理绘图负向约束dont)          | 力矢量颜色混乱 / 导线 T 型无圆点 / 浮力物体无轮廓区分           |
| **字幕**       | [verification_checklist.md — 字幕](references/verification_checklist.md#字幕负向约束dont) | 单条超 4 行 / 时长不同步 / 强调条未对齐底衬                     |
| **TTS**        | [tts_guide.md — 负向约束](references/tts_guide.md#负向约束dont)                           | 符号未映射 / LaTeX 分隔符未清除 / highlight_range 越界          |
| **工作流**     | [workflow.md — 负向约束](references/workflow.md#负向约束dont)                             | 跳过 Markdown 确认 / 跳过 Gate 3 校验 / 跳过时长估算            |
| **综合**       | [layout.md — 附录A](references/layout.md#附录a-负向约束速查dont)                          | 跨域混用坐标 / 未配重叠白名单 / 使用废弃路径                    |

> **维护规则**：当发现新的典型失败模式时，在对应 reference 文件末尾追加 Don't 条目，标注"D-新增（日期）：事故描述→代码示例→画面崩坏结果"。

## 排版布局绝对遵循红线（最高优先级 — 不可违反）

> **为什么这是红线**：Manim 的坐标系统和 MObject 定位机制极为敏感。
> 一个 `.next_to()` 的微小偏移、一个未调用的 `safe_place()`、
> 一处硬编码的 `[x, y, z]`，都可能导致元素溢出屏幕、相互重叠、
> 或在分辨率切换时完全错位。**排版崩坏是 Manim 项目最常见、最致命的失败模式。**
>
> **因此，以下规则不是"建议"，而是生成代码的先决条件。**
> **违反任何一条 = 布局不合格 = 禁止进入渲染阶段。**

### 一、MUST — 强制行为（每条必须执行）

| 编号 | 规则                                | 正确做法                                                       | 违反后果                             |
| ---- | ----------------------------------- | -------------------------------------------------------------- | ------------------------------------ |
| M1   | **使用 LayoutScene 基类**           | 所有场景类继承 `scripts/layout/scene_base.py` 的 `LayoutScene` | 无法获得区域划分、安全定位等基础设施 |
| M2   | **仅用 VGroup.arrange() 布局**      | 元素分组后调用 `.arrange(buff=..., direction=...)`             | 手动定位在内容变化时必然错位         |
| M3   | **每次添加元素前调用 safe_place()** | `self.safe_place(mobject, region="content")`                   | 元素可能落入字幕区或溢出边界         |
| M4   | **使用 axes.c2p() 转换所有坐标**    | `pos = axes.c2p(x, y)` 而非 `[x, y, 0]`                        | 数学坐标与屏幕坐标不匹配             |
| M5   | **代码生成前必须通过布局验证**      | 两步验证：先程序化校验(无需渲染) → 再渲染视觉确认              | 跳过任一步 = 布局不合格              |
| M6   | **涉及坐标计算时必须添加参考系**    | 场景中包含 Axes 或 NumberPlane                                 | 无法验证坐标正确性                   |

### 二、FORBIDDEN — 禁止行为（出现即判定为错误）

| 编号 | 禁止项                             | 为什么禁止                                             | 典型崩坏场景                                            |
| ---- | ---------------------------------- | ------------------------------------------------------ | ------------------------------------------------------- |
| F1   | **禁止 .next_to() 用于元素间定位** | 相对位置依赖前驱元素的最终渲染位置，链式累积误差       | A.next_to(B) -> B 移动后 A 跟着跑 -> C/D/E 全部连锁错位 |
| F2   | **禁止 .align_to() 用于对齐**      | 同上，且 align_to 不考虑安全区域                       | 公式与图形"看似对齐"实际重叠                            |
| F3   | **禁止 .shift() 用于单个元素微调** | shift 是绝对偏移，在不同分辨率下位置不同               | 1080p 下完美，4K 下飞出屏幕                             |
| F4   | **禁止硬编码坐标 [x, y, z]**       | 屏幕坐标与数学坐标系无关                               | 函数图像与公式标注完全脱节                              |
| F5   | **禁止估算距离/角度**              | "大约向右 2 个单位" 在不同场景下差异巨大               | 两栏布局左栏侵入右栏区域                                |
| F6   | **禁止视觉微调后的代码**           | "看起来差不多"不等于数学上正确                         | 字幕行高变化时公式被遮挡                                |
| F7   | **禁止跳过程序化校验直接渲染**     | validate_layout() 毫秒级执行，跳过等于放弃自动纠错能力 | 渲染 5 分钟后才发现可提前捕获的问题                     |

> **唯一例外**：`.shift()` 仅允许用于**整体 VGroup 的全局位置调整**（如将整个内容组居中），禁止用于单个子元素的定位修正。

### 三、布局崩坏典型场景黑名单

以下场景是已知的崩坏高发区，生成代码时必须主动规避：

| 崩坏类型             | 触发条件                                | 规避方法                                                                                                                  |
| -------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **元素溢出屏幕**     | 公式过长 / 图形过大 / 字号过大          | 使用 safe_place() 自动缩放；长公式拆分为多行                                                                              |
| **元素相互重叠**     | 多个对象使用相近坐标 / next_to 链式累积 | 必须使用 VGroup.arrange() 统一排列                                                                                        |
| **公式截断**         | MathTex 宽度超出分配区域                | 检测宽度 > 区域宽度时自动缩小字号或拆分                                                                                   |
| **字幕遮挡内容**     | 内容高度超出 content 区上界             | 遵循字幕区扩展规范（见 layout.md）                                                                                        |
| **两栏/三栏越界**    | 单栏内容过多撑破列宽                    | place_two_column/three_column 内置**事前预检**（自动换行/缩放/scale_to_fit）+ **事后校验**（validate_layout + 3轮降级链） |
| **动画期间元素漂移** | 动画目标位置使用了相对定位              | 所有动画起止点均通过 safe_place 计算                                                                                      |
| **分辨率适配失效**   | 硬编码像素值                            | 全部使用 Manim 坐标单位（非像素）                                                                                         |

### 3.5、程序化布局校验（M5 的第一步 — 无需渲染）

> **核心原理**：Manim 的 MObject 在 `__init__` 完成后，其几何属性（width / height / bounding_box）**立即可通过属性访问获取，无需调用 render()**。
> 结合 `ZoneConstants` 中已定义的精确区域边界数值，所有布局问题都可以在代码层面 100% 自动检测。

#### 可计算的 Manim 几何属性（无需渲染）

| 属性                              | 返回值                | 用途                   |
| --------------------------------- | --------------------- | ---------------------- |
| `mobject.width`                   | float                 | 元素宽度（Manim 单位） |
| `mobject.height`                  | float                 | 元素高度（Manim 单位） |
| `mobject.get_left()`              | np.ndarray([x, y, z]) | 左边界坐标             |
| `mobject.get_right()`             | np.ndarray            | 右边界坐标             |
| `mobject.get_top()`               | np.ndarray            | 上边界坐标             |
| `mobject.get_bottom()`            | np.ndarray            | 下边界坐标             |
| `mobject.get_center()`            | np.ndarray            | 中心坐标               |
| `mobject.get_corner(UL/UR/DL/DR)` | np.ndarray            | 四角坐标               |

#### 必须自动检测的 9 类问题（分两层）

**第一层：对象 vs 区域边界（inter-region，4 类）**

| 检测项       | 判定逻辑                                                             | 对应 ZoneConstants                                       | 触发条件示例                   |
| ------------ | -------------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------ |
| **区域溢出** | `obj.get_right()[0] > ZONE_X_MAX` 或 `obj.get_top()[1] > ZONE_Y_MAX` | SAFE_AREA / MAIN_CONTENT / GRAPHICS 各自的 \_MIN / \_MAX | 公式宽 7.0 但单栏区仅 12.0 宽  |
| **区域侵入** | content 底部 Y < SUBTITLE_ZONE_Y_MAX                                 | SUBTITLE_ZONE_Y_MAX = -3.3                               | 内容过多下沉到字幕区           |
| **元素重叠** | 两对象 bounding_box 有交集（X 和 Y 方向均重叠）                      | —                                                        | 两栏左栏公式与右栏图形水平交叉 |
| **屏幕越界** | 超出 SCREEN_WIDTH=15.0 或 SCREEN_HEIGHT=9.0                          | SCREEN\_\*                                               | 绝对定位元素飞出画面           |

**第二层：区域内部内容关系（intra-region，5 类）— 各对象之间的高宽均可计算对比**

| 检测项             | 判定逻辑                                                 | 触发条件示例                                    |
| ------------------ | -------------------------------------------------------- | ----------------------------------------------- |
| **堆叠总高度溢出** | `max(tops) - min(bottoms) > region_avail_height`         | 单栏内 8 条公式堆叠后总高超出区域可用高度       |
| **单对象宽度超限** | `obj.width > region_avail_width * 0.98`                  | 某条 MathTex 公式宽度接近或超过列宽             |
| **相邻间距异常**   | 相邻两对象的 gap < 标准间距×0.3 或 > ×4                  | 元素间过密（拥挤感）或过稀疏（遗漏元素/不紧凑） |
| **填充率异常**     | `Σ(obj.width×obj.height) / region_area > 0.92 或 < 0.05` | 内容过于密集（需拆场景/缩字号）或过于稀疏       |
| **视觉重心偏移**   | 加权中心与区域中心的偏移量超过区域尺寸的 15%(H) / 20%(V) | 内容整体偏左/偏上，未居中                       |

> **所有判定均基于 Manim 原生属性**：`obj.width`、`obj.height`、`obj.get_left/right/top/bottom()`、`obj.get_center()` —
> 这些属性在 MObject 构建完成后立即可用，无需 render()。

#### 重叠白名单机制（ELEMENT_OVERLAP 的例外）

> **唯一判定基准：语义相关性**
>
> **语义无关的两个内容对象 → 绝对禁止重叠（报告 ELEMENT_OVERLAP）**
>
> **语义相关的两个内容对象 → 允许重叠（跳过检测）**
>
> 以下全部规则、模式、代码接口，均为此基准的**实现手段**，而非独立标准。

**一、语义相关性判定总表**

```
| #   | 语义关系               | A 端示例              | B 端示例                     | 重叠是否合法 | 典型场景       |
| --- | ---------------------- | --------------------- | ---------------------------- | ------------ | -------------- |
| R1  | **力作用于物体**       | Arrow(力矢量)         | Polygon(木块/小球)           | ✅ 允许      | 受力分析图     |
| R2  | **电连接**             | Line(导线)            | Rectangle(电阻/电池)         | ✅ 允许      | 电路图         |
| R3  | **场与源的空间贯穿**   | CurvedArrow(场线)     | Dot(电荷)/Circle(磁体)       | ✅ 允许      | 电磁场图       |
| R4  | **物体浸入流体**       | Polygon(木块)         | Polygon(液体填充区)          | ✅ 允许      | 浮力场景       |
| R5  | **标注→被标注对象**    | Tex/MathTex("5m/s")   | 任意被标注目标               | ✅ 允许      | 尺寸/数值标注  |
| R6  | **几何依附**           | DashedLine(辅助高线)  | Triangle(主三角形)           | ✅ 允许      | 几何证明       |
| R7  | **顶点标记**           | Dot(顶点A) / Arc(角α) | Polygon/Triangle(图形本体)   | ✅ 允许      | 几何作图       |
| R8  | **符号标记在线段上**   | Tex("⊥") / VGroup     | Line/Polygon(被标记线段)     | ✅ 允许      | 垂直/平行标记  |
| R9  | **尺寸标注覆盖被测物** | Arrow/Brace(标注箭头) | Line/Segment(被测线段)       | ✅ 允许      | 长度/距离标注  |
| R10 | **曲线与其切线/法线**  | Line(切线)            | FunctionGraph/SinCurve(曲线) | ✅ 允许      | 函数图像       |
| R11 | **坐标轴与其刻度标签** | Tex("x"/"1")          | NumberLine/Axes(轴线)        | ✅ 允许      | 坐标系         |
| --  | **无任何语义关联**     | MathTex(公式A)        | MathTex(公式B)               | ❌ **禁止**  | 两公式互相遮挡 |
| --  | **无任何语义关联**     | 图形X(独立元素)       | 图形Y(无关元素)              | ❌ **禁止**  | 无关元素重叠   |
```

**二、实现方式：两层过滤**

`validate_layout()` 在检测到 bounding_box 重叠时，按以下顺序判断：

```
检测到重叠 (x_overlap > tolerance AND y_overlap > tolerance)
│   tolerance = max(0.05, max(stroke_a, stroke_b) * 0.55)
│   其中 0.05 = Manim 默认 stroke_width=4 points / 72 ≈ 0.056 的安全下限
│        0.55 = stroke 接触约 55% 内视为合法（物理图元间容许边界贴合）
│
├─ 第 1 层：显式对象对白名单 (allowed_overlap_pairs)
│   └─ (obj_a, obj_b) 在列表中? → 跳过 ✅ （人工确认语义相关）
│
└─ 第 2 层：类型模式自动匹配 (allowed_overlap_patterns)
    └─ A和B的类型组合匹配某个模式? → 继续走容差比较（不再一票放行）
    └─ 都不匹配? → 报告 ELEMENT_OVERLAP ❌ （推断为语义无关）
```

**三、内置预定义模式映射表（语义关系 → 类型匹配规则）**

> 每个模式对应上述**一、语义相关性判定总表**中的一行或多行。
> 模式的本质是**用 Manim 类型名来近似推断语义关系**。

| 模式名                        | 对应的语义关系                                | A 端类型匹配                              | B 端类型匹配                            | 推断逻辑                                         |
| ----------------------------- | --------------------------------------------- | ----------------------------------------- | --------------------------------------- | ------------------------------------------------ |
| `physics_scene_catch_all`     | **R1+R2+R3+R4 全覆盖** + 物理场景内任意图元对 | PHYSICS_GRAPHIC_TYPES (19类)              | PHYSICS_GRAPHIC_TYPES (19类)            | 物理绘图中的图元间天然存在空间关系，默认语义相关 |
| `force_arrow_on_object`       | R1 力作用于物体                               | Arrow/Vector/DoubleArrow/CurvedArrow      | **任意**(通配)                          | 箭头类 → 推断为力矢量 → 与接触物体语义相关       |
| `wire_to_component`           | R2 电连接                                     | Line/DashedLine/VMobject                  | **任意**(通配)                          | 连线类 → 推断为导线/场线 → 与连接目标语义相关    |
| `object_submerged_in_liquid`  | R4 浸入流体                                   | Polygon/Rectangle/Circle/Ellipse/VMobject | Polygon(液体)                           | 固体 vs 液体Polygon → 推断为浸入关系             |
| `axis_tick_label`             | R11 坐标轴刻度                                | Tex/MathTex/Integer/DecimalNumber         | NumberLine/Axes/ThreeDAxes              | 文本数字 + 轴线类型 → 推断为刻度标签             |
| `geometry_vertex_point`       | R7 顶点标记                                   | Dot/SmallDot/LabeledDot                   | Polygon/Triangle/Circle/Arc...          | 点 + 多边形 → 推断为顶点重合                     |
| `auxiliary_line_on_figure`    | R6 几何依附                                   | Line/DashedLine/DottedLine                | Polygon/Triangle/Circle/Arc...          | 虚线 + 图形 → 推断为辅助线                       |
| `angle_mark_at_vertex`        | R7 角标记                                     | Arc/RightAngle/Angle/Elbow                | Dot/Polygon/Triangle/Line...            | 弧/直角符号 + 顶点 → 推断为角度标记              |
| `geometry_label_on_figure`    | R5 标注(几何)                                 | Tex/MathTex/Text                          | Polygon/Circle/Arc/Line...              | 文本 + 几何图形 → 推断为顶点/边标签              |
| `perpendicular_parallel_mark` | R8 符号标记                                   | Tex/MathTex/VGroup                        | Line/DashedLine/Polygon...              | ⊥∥文本 + 线段 → 推断为垂直平行标记               |
| `dimension_arrow_on_segment`  | R9 尺寸标注                                   | Arrow/DoubleArrow/Line/Brace              | Line/Segment/Polygon...                 | 箭头/大括号 + 线段 → 推断为长度标注              |
| `curve_annotation`            | R10 曲线标注                                  | Line/DashedLine/Arrow/Vector              | ParametricFunction/FunctionGraph/Arc... | 直线 + 曲线 → 推断为切线/法线                    |
| `label_on_target`             | **R5 标注(通用)**                             | Tex/MathTex/Text/MarkupText               | **任意**(通配)                          | 文本类 → 推断为某对象的标注                      |

> `PHYSICS_GRAPHIC_TYPES` 完整清单（19 类）：Arrow, Vector, DoubleArrow, CurvedArrow, Line, DashedLine, DottedLine, Polygon, Rectangle, Square, RegularPolygon, Circle, Ellipse, Arc, CubicBezier, Dot, SmallDot, LabeledDot, VMobject

**四、推荐策略（按场景选择）**

```python
# ══════════════════════════════════════════
# 策略 A：物理场景 — 语义宽松
# 适用：力学/电磁学/电路/浮力流体/光学等
# 原因：物理图元间几乎都存在空间语义关系(R1-R4)，逐项穷举不可行
# 效果：物理图元间全部放行，仅拦截公式/文本间的无关遮挡
# ══════════════════════════════════════════
PHYSICS_PATTERNS = {
    "physics_scene_catch_all": LayoutScene.ALLOWED_PATTERNS["physics_scene_catch_all"],
    "label_on_target":         LayoutScene.ALLOWED_PATTERNS["label_on_target"],
}
violations = self.validate_layout(
    placed_objects, region="graphics",
    allowed_overlap_patterns=PHYSICS_PATTERNS,
)

# ══════════════════════════════════════════
# 策略 B：数学/几何场景 — 语义严格
# 适用：代数推导/几何证明/函数图像/三角函数等
# 原因：数学元素通常各自独立，仅特定标注/依附关系允许重叠
# 效果：仅 R5-R11 对应的 8 种模式允许重叠，其余全部拦截
# ══════════════════════════════════════════
MATH_PATTERNS = {
    k: v for k, v in LayoutScene.ALLOWED_PATTERNS.items()
    if k in [
        "geometry_vertex_point",       # R7
        "auxiliary_line_on_figure",     # R6
        "angle_mark_at_vertex",         # R7
        "geometry_label_on_figure",     # R5
        "perpendicular_parallel_mark",  # R8
        "dimension_arrow_on_segment",   # R9
        "curve_annotation",             # R10
        "label_on_target",              # R5 通用
    ]
}
violations = self.validate_layout(
    placed_objects, region="graphics",
    allowed_overlap_patterns=MATH_PATTERNS,
)

# ══════════════════════════════════════════
# 策略 C：混合场景 — 分区策略
# 适用：同一画面中同时包含物理图形和数学内容
# 做法：物理区域用策略A，数学区域用策略B
# ══════════════════════════════════════════
MIXED_PATTERNS = {**PHYSICS_PATTERNS, **MATH_PATTERNS}
violations = self.validate_layout(
    placed_objects,
    allowed_overlap_patterns=MIXED_PATTERNS,
)

# ══════════════════════════════════════════
# 策略 D：完全手动 — 最高精度控制
# 适用：自动推断可能误判的复杂场景
# 做法：逐一声明每对语义相关的对象
# ══════════════════════════════════════════
violations = self.validate_layout(
    placed_objects,
    allowed_overlap_pairs=[
        (force_arrow_G, block),      # R1: G作用于木块
        (force_arrow_N, block),      # R1: N作用于木块
        (wire_1, resistor),          # R2: 导线接电阻
        (wire_2, battery),           # R2: 导线接电池
        (wood_block, liquid),         # R4: 木块浸入液体
        (label_A, dot_a),            # R5/R7: 标签A在顶点A处
        (altitude_line, triangle),   # R6: 辅助高线依附三角形
        (tangent_line, curve),       # R10: 切线与曲线
    ],
)
```

#### 校验执行方式：LayoutScene.validate_layout()

在 `scripts/layout/scene_base.py` 的 `LayoutScene` 基类中提供 `validate_layout()` 方法：

```python
def validate_layout(
    self,
    placed_objects: List[Mobject],
    region: str = "content",
    overlap_pairs: List[Tuple[Mobject, Mobject]] = None,
    allowed_overlap_pairs: List[Tuple[Mobject, Mobject]] = None,
    allowed_overlap_patterns: Dict[str, Tuple] = None,
) -> List[Dict]:
    """程序化布局校验（无需渲染），检测 9 类布局问题

    Args:
        placed_objects: 已放置的所有 MObject 列表
        region: 目标区域名称 ("content" / "graphics" / "subtitle" /
                "safe_area" / "screen")
        overlap_pairs: 需要检查重叠的对象对列表。若为 None 则检查所有相邻对。
        allowed_overlap_pairs: 显式允许合法重叠的对象对（力箭头-物体、标注-目标等）
        allowed_overlap_patterns: 按类型模式自动豁免重叠的规则字典。
                传入 LayoutScene.ALLOWED_PATTERNS 启用全部内置预定义模式。

    Returns:
        违规列表，每条包含 {"type", "object_name", "expected", "actual", "detail"}
        type 取值范围:
          第一层(4): REGION_OVERFLOW, REGION_INTRUSION, ELEMENT_OVERLAP,
                     SCREEN_OUT_OF_BOUNDS
          第二层(5): STACK_OVERFLOW, WIDTH_EXCEEDS_COLUMN, ABNORMAL_SPACING,
                     OVER_DENSE / TOO_SPARSE, CENTER_OFFSET
        空列表表示全部通过
    """
```

**调用时机与判定**：

```
场景 construct() 方法中：
    1. 创建所有 MObject
    2. 使用 VGroup.arrange() + safe_place() 布局
    3. 调用 self.validate_layout(all_mobjects)   ← 程序化校验（毫秒级）
       ├─ 返回 [] → 通过 → 进入渲染阶段
       └─ 返回 [违规...] → 打印详细报告 → 禁止渲染 → 修复后重试
    4. （可选）渲染验证视频做最终视觉确认
```

**输出报告格式示例**：

```python
[
    {
        "type": "REGION_OVERFLOW",
        "object_name": "formula_group",
        "region": "main_content_single_col",
        "expected": "width <= 12.0 (MAIN_CONTENT_SINGLE_COL_X_MAX - X_MIN)",
        "actual": "width = 13.47, right_x = 6.74 > X_MAX = 6.0",
        "detail": "第3条公式 MathTex(r'\\int_0^\\infty ...') 过长"
    },
    {
        "type": "ELEMENT_OVERLAP",
        "object_name": "formula_2",
        "region": "--",
        "expected": "no overlap with graphics_obj",
        "actual": "overlap width = 0.83 at Y ∈ [-0.2, 0.5]",
        "detail": "公式右边缘(x=0.33) 与图形左边缘(x=-0.50) 重叠"
    }
]
```

> **程序化校验 vs 渲染视觉检查的关系**：
>
> - 程序化校验是**第一步**（必须执行），捕获所有可量化的溢出/重叠/越界
> - 渲染视觉检查是**第二步**（可选但推荐），捕获程序化难以判断的美观性问题（如间距不均匀、视觉重心偏移等）
> - **禁止跳过第一步直接进入第二步**

### 四、违规处置流程

```
检测到违规（静态分析 / 渲染验证 / 人工审查）
    |
    +-- 违规等级 A（F1-F3: 禁用定位方法）
    |      +-- => 立即停止生成，回退重新设计
    |
    +-- 违规等级 B（F4-F6: 硬编码/估算/微调）
    |      +-- => 标记为"需重构"，禁止渲染
    |
    +-- 违规等级 C（M1-M6 未执行：缺少验证步骤）
    |      +-- => 补充缺失步骤后重新验证
    |
    +-- 违规等级 D（validate_layout() 返回溢出/重叠）
           +-- => 自动 handle_violation() 优化
                  ├─ 优化成功 -> 继续渲染
                  └─ 优化失败 -> 标注"需人工拆分原子"
```

#### 布局自动优化机制（双层防护）

**第一层：事前预检**（`place_two_column()` / `place_three_column()` 放置前自动执行）

在将内容放入栏位之前，`_precheck_mobject()` 逐对象测量实际 width/height，按类型分层处理：

```markdown
| 对象类型         | 超宽时处理                                           | 超高时处理                    |
| ---------------- | ---------------------------------------------------- | ----------------------------- |
| **Text**         | CJK 感知宽度估算 → 自然断点分行 → 重建多行 Text      | 同左（换行后高度自然增加）    |
| **MathTex**      | LaTeX 运算符断点拆分（=/+/-/\\times）→ `\\` 换行重建 | 同左                          |
| **图形 Mobject** | `scale_to_fit()` 到栏宽范围内                        | `scale_to_fit()` 到栏高范围内 |
| **VGroup**       | 递归检查子元素，分别处理                             | 同左                          |
```

**第二层：事后校验 + 3 轮降级链**（`validate_layout()` + `handle_violation()` 放置后执行）

当事前预检仍未能完全解决时（如换行后总高度溢出），触发以下递进调整：

```markdown
| 轮次    | 策略         | 触发条件                | 调整方式                                        |
| ------- | ------------ | ----------------------- | ----------------------------------------------- |
| 第 1 轮 | scale_font   | WIDTH / HEIGHT_OVERFLOW | Text/MathTex font_size ×0.9（下限 24px）        |
| 第 2 轮 | wrap_content | 宽度/高度仍溢出         | Text: CJK 自然断点分行；MathTex: LaTeX 断点拆分 |
| 第 3 轮 | split_atom   | 前 2 轮均失败           | 调用 `_on_atom_split` 回调，建议人工拆分原子    |
```

**使用方式**：

```python
if violations:
    result = self.handle_violation(violations, list(all_mobjects))
    # result.success=True: 优化成功
    # result.success=False: 建议人工拆分原子

# 字体自适应算法
from layout.constants import ZoneConstants
font_size = ZoneConstants.auto_font_size(12.0, 13.5)  # 返回 28

# 运行时实测尺寸
from layout.engine import LayoutEngine
width, height = LayoutEngine.measure_content_dims(texts)
```

### 五、布局规范引用索引

以下文件定义了排版的详细参数和实现方式，本红线章节是强制要求的总纲：

```markdown
| 文件                                  | 内容                                                                                                     | 与红线的关系                                |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `references/layout.md`                | 区域划分、安全边界算法、**分栏布局算法（第10章强制执行）**                                               | 红线的参数来源 + 分栏算法规范               |
| `references/layout_concept.html`      | 布局可视化预览（8种场景 + 动态计算算法说明）                                                             | AI/人类理解布局期望的参考，非代码约束       |
| `scripts/layout/constants.py`         | **ZoneConstants.compute()** 动态计算 + **compute_column_layout()** 分栏 + **validate_column_fit()** 校验 | 程序化布局的核心方法                        |
| `scripts/layout/engine.py`            | 自动布局决策引擎                                                                                         | 实现 M2/M3 的工具                           |
| `scripts/layout/scene_base.py`        | LayoutScene 基类 + **validate_layout()**                                                                 | 实现 M1/M3/M5/M6 的基类 + M5 程序化校验方法 |
| `templates/layout_test_template.json` | 布局验证模板                                                                                             | M5 第二步的输入数据                         |
| `references/json_schema.md`           | atoms[].layout 枚举值约束                                                                                | 布局类型的合法取值                          |
```

## 依赖与环境

- Python >= 3.11
- Manim CE >= 0.17.3
- manim-voiceover[all] >= 0.3.6
- **专业物理/化学/天体动画库**（按需安装，根据场景选择）：
  - `manim-physics`：刚体力学、电磁场、波动（`uv add manim-physics`）
  - `manim-circuit`：专业级电路图元件（`uv add manim-circuit`）
  - `manim-Astronomy`：天体运动轨道（`uv add manim-Astronomy`）
  - `chanim`：化学分子结构（`uv add chanim`）
- 根据实际的系统平台安装系统级依赖（并写入环境变量）：PortAudio、SoX（libsox-fmt-all）、gettext、ffmpeg、TexLive、MiKTeX。TexLive(优先) 或 MiKTeX(备选)
- 云端 TTS 账号（阿里云、豆包、Azure）或 EdgeTTS（备选）
- 详见 `references/tts_guide.md`

渲染时必须添加 --disable_caching 标志。推荐在项目根目录使用 `pyproject.toml` 管理依赖。

**第三方库使用优先级**：

1. 检查技能 `scripts/physics_graphics.py` 是否已实现该图元
2. 未实现 → **优先使用上述第三方库**（更专业、更稳定）
3. 第三方库无 → 才在技能中新增实现（需遵循本规范标准）

## 调试模式

- 开发阶段：设置 `debug=True`，显示坐标参考系（网格、刻度）
- 生产阶段：设置 `debug=False`，隐藏坐标参考系
- 实现：调用 `self.add_coordinate_reference(debug=True)`

## 工程化脚手架说明

本 Skill 提供完整的**企业级工程化脚手架**，用户创建项目后，将以下目录复制到项目根目录：

- `scripts/`：核心基础设施（布局引擎、验证器、动画组件、物理图元）
- `templates/`：JSON 模板和配置文件

**⚠️ 分层基础设施规则（最高优先级）**：

> `scripts/` 按"基线 / 扩展"两层管理（详见核心原则 10）：
>
> - **基线层**：技能版本作为**默认**安装；项目可基于实际需要更新复制后的基线文件（更新后需保持向后兼容：保留 API 入口、保持 LayoutScene 子类可继承）
> - **扩展层**：项目可按需追加 `create_*` / 工具函数；禁止删除基线函数
> - **基线保护原因**：布局引擎 / 区域定义 / 校验器 / 字幕滚动器是核心约束链，整体替换会破坏技能的设计契约
>
> **覆盖与扩展清单**：
>
> | 文件/目录 | 类别 | 规则 |
> |-----------|------|------|
> | `scripts/layout/` | 基线 | 默认使用技能版本；项目可更新复制后的基线文件，但需保持 API 兼容 |
> | `scripts/animation/` | 基线 | 默认使用技能版本；项目可更新复制后的基线文件，但需保持 API 兼容 |
> | `scripts/environment/` | 基线 | CJK 自检 + 引擎探测 + 安装建议（核心原则 11）；项目可更新 |
> | `scripts/validation/` | 基线 | 默认使用技能版本；项目可更新复制后的基线文件，但需保持 API 兼容 |
> | `scripts/physics_graphics.py` | 扩展 | 可追加 `create_*` 图元；禁止删除/重命名已有函数 |
> | `scripts/project_extensions/` | 扩展 | 项目自建（需遵循基线约束：不绕过 `safe_place()`、不硬编码坐标） |
> | `templates/` | 配置 | 可调整内容，保持结构一致 |
>
> **扩展原则**（无论基线还是扩展层，新增内容都必须满足）：
>
> - 不绕过 `safe_place()` / `validate_layout()`
> - 不硬编码绝对坐标（用 `ZoneConstants.compute()` / `c2p()` 派生）
> - 不使用 `.next_to()` / `.align_to()` 触碰元素（除标题整组 `move_to(ORIGIN)` 外）
> - 图元走 VGroup 组装，遵循 `references/physics.md` 量化规则

用户项目的标准目录结构见 `references/project_structure.md`。

## 模板库

- 课程内容 JSON 模板：`templates/course_template.json`
- 布局测试 JSON 模板：`templates/layout_test_template.json`
- 模板使用指南：`templates/README.md`

## 脚本模板

以下脚本需要复制到用户项目的对应目录中，模块化集成。详细说明见 `references/project_structure.md`。

### 核心布局模块（`scripts/layout/`）

- `constants.py`：区域常量定义（映射 layout.md，包含字幕区扩展常量）
- `engine.py`：布局决策引擎（自动选择单栏/两栏/三栏）
- `scene_base.py`：`LayoutScene` 场景基类
- `zones/`：区域容器组件（字幕区、主内容区、图形区）
  - `subtitle_zone.py`：字幕区容器（支持底部固定位置、上界约束）
  - `main_content_zone.py`：主内容区容器（单栏/两栏/三栏布局管理）
  - `graphics_zone.py`：图形区容器（物理图形/数学图形的 safe_place 定位）
  - `base.py`：`ZoneBase` 基类（三个区域容器的公共实现）

### 动画组件（`scripts/animation/`）

- `subtitle_scroller.py`：字幕滚动管理器（预计算滚动系统）

### 环境自检模块（`scripts/environment/`）

> 核心原则 11：CJK / LaTeX 引擎自检与安装建议。所有路径在 `LayoutScene.setup()` 钩子中自动执行，**不允许**渲染到一半才报错。

- `__init__.py`：模块导出（`check` / `check_cached` / `install_suggested_commands`）
- `tex_engine_probe.py`：探测 pdflatex / xelatex / lualatex 可用性 + 版本
- `cjk_checker.py`：综合自检（CJK 宏包 / 中文字体 / 渲染路径推荐），支持结果缓存
- `cjk_installer.py`：按平台提供安装命令建议，**默认仅打印不执行**（`auto_install=True` 时 Linux/macOS 才会执行，Windows 拒绝自动安装）

**使用示例**：

```python
from scripts.environment.cjk_checker import check, RenderPath

report = check(verbose=True)
if report.render_path == RenderPath.TEX_MINIPAGE:
    # 走 minipage 渲染（xelatex + xeCJK + 中文字体齐全）
    scene.use_minipage_path()
elif report.render_path == RenderPath.TEXT_PANGO_ONLY:
    # 走 Text (Pango)，_wrap_text_object 已处理换行
    scene.use_text_fallback()
```

### 字幕区扩展规范（`scripts/layout/constants.py`）

```python
# 字体大小 ↔ 行高换算公式
MANIM_FONT_TO_UNIT_RATIO = 8.0 / 72.0  # ≈ 0.111
SUBTITLE_LINE_HEIGHT_RATIO = 1.15  # 行高系数
line_height = font_size / 72 * MANIM_FONT_TO_UNIT_RATIO * SUBTITLE_LINE_HEIGHT_RATIO

# 字幕区布局约束
SUBTITLE_ZONE_BOTTOM_FIXED_Y = -3.85  # 底部固定位置（防抖动）
SUBTITLE_ZONE_TOP_Y = -2.8  # 上界（防止侵入主内容区）

# 字幕底衬+强调条样式
SUBTITLE_BACKGROUND_COLOR = "#0e1828"  # 深色半透明底衬
SUBTITLE_BACKGROUND_OPACITY = 0.72
SUBTITLE_ACCENT_COLOR = "#ffd166"  # 金色强调条
```

### 预计算字幕滚动系统（`scripts/animation/subtitle_scroller.py`）

**核心设计**：

1. **字体大小 ↔ 行高精确关联**：动态计算行高、滚动距离、底衬大小
2. **预计算滚动时序**：所有滚动事件的触发时间、滚动距离、动画时长提前计算
3. **前驱滚出 = 后继滚入**：联动滚动，速度、间距一致
4. **底部固定位置**：字幕组底部对齐到 `SUBTITLE_ZONE_BOTTOM_FIXED_Y`，防止多行字幕抖动
5. **字幕底衬+左侧强调条**：借鉴 mathVideoMaker 视觉设计

**布局约束**：

- 可见行数固定 2 行，超出自动垂直滚动
- 滚动单位 = `line_height + line_height * SUBTITLE_LINE_SPACING_RATIO`
- 上界约束：字幕组顶部不得超过 `SUBTITLE_ZONE_TOP_Y`

### 验证器（`scripts/validation/`）

- `course_schema_validator.py`：JSON Schema 验证器

### 工具模块

- `tex_tools.py`：LaTeX 解析与符号映射（含 LaTeX→Unicode 转换引擎、P1-P6 违规检测、中文下标规范化、增强版 TTS 映射）
- `subtitle_splitter.py`：语音文本分行
- `subtitle_scroller.py`：字幕滚动管理器（自动处理多行字幕滚动，滚动速度与语音同步，约4字符/秒）
- `split_atom.py`：原子拆分工具
- `visual_actions.py`：预置视觉动作模板（可选）
- `validate_course_contents.py`：JSON 校验与修复的便捷入口

**注意**：`scripts/layout_base.py` 已被废弃，不再使用。布局功能全部迁移至 `scripts/layout/` 模块。

## 示例与测试

见 `examples/README.md`
