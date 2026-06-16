<img width="640" height="360" alt="image" src="https://github.com/user-attachments/assets/19336ef0-f97c-47f8-98dc-f367d0f7e236" />

# ManimAnimationGenerator 技能包

> 数学/物理知识动画生成专用 Manim 脚手架，遵循「七阶段教学路径」「排版布局绝对红线」「语义相关性唯一基准」三大核心原则。
> 内置**事前预检 + 事后校验**双层布局防护与**受力点选择规范**。

## 技能定位

本技能可通过任意AI模型接收用户的课程知识目标，自动分析内容结构，生成人类可读的教学内容 Markdown 与对应的课程结构 JSON，由AI驱动 `manim` 渲染引擎输出知识点动画视频。

主旨目标3个：
A. 屏蔽编程工作 
B. 解决manim排版炸的问题 
C. 快速、稳定的通过内容驱动AI生成manim视频

决策影响：技能本身已经做了验证与测试，但 LLM 自身能力可能导致鲁棒性降低、对齐度偏离。建议选择第一梯队的模型。

**核心产物**：

- **教学草案 Markdown**（`主题_course.md`）— 纯人类可读，含教学阶段、直观解释、反直觉澄清，每个原子标注人工制作时长（分钟），无技术字段
- **课程结构 JSON**（`courses/主题_content.json`）— 机器可读，含类型/时长/动画动作等程序字段
- **Manim 场景代码**（`.py`）— 渲染用的动画逻辑
- **MP4 视频**（最终输出）

**工作流程**：用户输入任务目标 → AI 全自动生成 Markdown 教学草案 + JSON → 用户逐条审核确认 → 全自动代码生成 → 渲染输出

## 目录结构

```
manimanimationgenerator/
├── SKILL.md                          # 主技能文档（AI 读取的唯一入口）
├── README.md                          # 本文件（包结构总览）
│
├── references/                        # 参考规范（15 个专项文档）
│   ├── animation.md                   # 动画原理与命名规范
│   ├── builtin_knowledge.md           # 内置知识库内容
│   ├── json_schema.md                 # 课程结构 JSON 校验规范（含 duration 计算约束）
│   ├── layout.md                      # 区域布局规范（content/graphics/subtitle）
│   ├── layout_concept.html            # 布局概念可视化说明
│   ├── math_latex.md                  # 数学 LaTeX 规范（MathTex vs Tex）
│   ├── pedagogy_path.md               # 教学路径设计（识记→理解→应用）
│   ├── physics.md                     # 物理绘图图元规范（§15 含 IEC60617/GB-T4728；§15.1.1 受力点选择规范）
│   ├── project_structure.md           # 工程目录结构规范
│   ├── quality_acceptance.md          # 验收标准与质量门禁
│   ├── rendering.md                   # 渲染配置（1080p60/720p30/4k）
│   ├── textbook_sources.md            # 教材知识源覆盖清单
│   ├── tts_guide.md                   # TTS 发音映射（LaTeX+Unicode → 中文）
│   ├── verification_checklist.md     # 验证清单（5道门禁）
│   └── workflow.md                    # 用户-AI 协作工作流
│
├── scripts/                           # 可执行脚本与模块
│   ├── animation/
│   │   └── subtitle_scroller.py       # 字幕滚动管理器（预计算滚动系统 + max_duration 比例缩放）
│   │
│   ├── layout/
│   │   ├── constants.py               # ZoneConstants 布局常量定义
│   │   ├── engine.py                  # 布局引擎入口
│   │   ├── scene_base.py              # LayoutScene 基类（含 validate_layout / _precheck_mobject / place_two_column / place_three_column）
│   │   ├── optimizer.py               # 布局优化器（3轮降级链：scale_font → wrap_content[完整实现] → split_atom）
│   │   └── zones/                     # 三区域容器
│   │       ├── base.py                # ZoneBase 基类
│   │       ├── main_content_zone.py   # 主内容区（文字+公式）
│   │       ├── graphics_zone.py       # 图形区（几何+物理图元）
│   │       └── subtitle_zone.py      # 字幕区（底衬，无装饰条）
│   │
│   ├── validation/
│   │   └── course_schema_validator.py # JSON 结构校验（含 duration 匹配 ±3s 容差）
│   │
│   ├── physics_graphics.py            # 物理图元工厂函数（create_force_arrow / create_car / create_inclined_plane 等）
│   ├── tex_tools.py                   # LaTeX 处理工具（TTS/Unicode/校验/下标）
│   ├── subtitle_splitter.py          # 字幕拆分（max_chars 断行）
│   ├── split_atom.py                  # 公式原子拆分（操作数/操作符解析）
│   ├── visual_actions.py              # 可视化动作定义（fade/slide/highlight...）
│   ├── validate_layout.py             # 布局校验入口脚本
│   └── validate_course_contents.py    # 课程内容校验脚本
│
├── templates/                         # 代码模板与配置
│   ├── course_template.json           # 课程结构 JSON 模板
│   ├── layout_test_template.json      # 布局测试模板
│   └── manim.cfg                      # Manim 全局配置
│
└── examples/                          # 示例
    ├── matrix_course_example.json      # 课程 JSON 示例
    ├── matrix_scene.py                # 对应 Manim 场景代码
    ├── run_example.sh                  # 运行命令示例
    └── run_example_specfication.txt   # 示例规格说明
```

## 核心文件速查

| 任务                                         | 文件                                                                                            |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| AI 读取技能规范                              | `SKILL.md`                                                                                      |
| 布局基类（强制使用）                         | `scripts/layout/scene_base.py` → `LayoutScene`                                                  |
| 事前预检（宽度/高度超限自动调整）            | `scripts/layout/scene_base.py` → `_precheck_mobject()`                                          |
| 双栏布局（内置预检+校验双层防护）            | `scripts/layout/scene_base.py` → `place_two_column()`                                           |
| 三栏布局（三栏均含预检）                     | `scripts/layout/scene_base.py` → `place_three_column()`                                         |
| 布局优化器（3轮降级链）                      | `scripts/layout/optimizer.py` → `LayoutOptimizer`                                               |
| 换行策略（Text CJK 分行 / MathTex 断点拆分） | `scripts/layout/optimizer.py` → `_apply_wrap()` / `_wrap_text_object()` / `_wrap_math_object()` |
| 布局校验（9类违规+语义豁免）                 | `scripts/layout/scene_base.py` → `validate_layout()`（含13种模式自动推断语义相关性）            |
| 重叠白名单（13种模式，语义相关性推断）       | `scripts/layout/scene_base.py` → `ALLOWED_PATTERNS`（零配置自动豁免）                           |
| 物理图元工厂                                 | `scripts/physics_graphics.py` → `create_force_arrow()` / `create_car()` / ...                   |
| 受力点规范                                   | `references/physics.md` → §15.1.1（G/N/f/F/T 作用点速查表 + 错误对照）                          |
| 字幕滚动（预计算+比例缩放）                  | `scripts/animation/subtitle_scroller.py`                                                        |
| 布局常量（区域边界）                         | `scripts/layout/constants.py` → `ZoneConstants`                                                 |
| LaTeX → Unicode 转换                         | `scripts/tex_tools.py` → `latex_to_unicode()`                                                   |
| TTS 发音映射                                 | `scripts/tex_tools.py` → `math_symbols_to_speech()`                                             |

## 核心原则（详见 SKILL.md）

1. **七阶段教学路径** — 每个知识原子按「激活前置知识 → 直观体验 → 定义 → 运算 → 反直觉澄清 → 应用 → 总结」的七阶段叙事流设计，确保教学完整性
2. **排版布局绝对红线** — 所有布局必须使用 LayoutScene 基类 + VGroup.arrange()，禁止硬编码坐标（M1-M6 强制 / F1-F7 禁止）
3. **双层布局防护** — **事前预检**（`_precheck_mobject`：放置前逐对象测量宽高，自动换行/缩放/scale_to_fit）+ **事后校验**（`validate_layout` + 3 轮降级链）
4. **语义相关性唯一基准** — 重叠判定：语义相关 → 允许；语义无关 → 禁止（13 种预定义模式零配置推断）
5. **程序化布局校验** — `validate_layout()` 毫秒级检测 9 类违规（溢出/侵入/重叠/越界/堆叠/列宽/间距/填充率/重心偏移），零渲染依赖
6. **受力分析绘制规范** — 以正确的力学分析结果和规范的工程制图为前提，所有力矢量的作用点必须准确落在受力对象的实际受力点上（详见 physics.md §15.1.1）
7. **5 道验收门禁** — JSON 校验(G1) → 布局预览(G2) → validate_layout 程序化布局(G3) → 数理正确性(G4) → 渲染验证+人工复审(G5)

## 依赖

- Python ≥ 3.10
- Manim (社区版)
- 字体：Source Han Sans / Noto Sans CJK（字幕中文）
