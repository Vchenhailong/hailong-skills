# 用户项目构建结构

当用户使用本 Skill 生成教学内容动画时，建议按以下目录结构组织项目文件。

## 推荐目录结构

```
{project_name}/                    # 用户项目根目录
│
├── .venv/
├── references/                         # 规范文档（只读参考，不参与运行）
│   ├── layout.md                       # 布局安全区域规范（字幕区/主内容区/图形区坐标）
│   ├── layout_concept.html             # 布局可视化预览（8种场景 + 高度计算）
│   └── json_schema.md                  # 课程 JSON 结构规范（atom 类型、content 类型等）
│
├── courses/                            # 课程数据（JSON 教学内容文件）
│   ├── linear_programming_scene1.json  # 基础篇：图解法与基本概念（此处仅为示意）
│   └── linear_programming_scene2.json  # 进阶篇：单纯形法与对偶理论（此处仅为示意）
│
├── scenes/                             # 场景渲染入口（业务代码）
│   ├── linear_programming_scene1.py    # 基础篇场景类，继承 LayoutScene（此处仅为示意）
│   └── linear_programming_scene2.py    # 进阶篇场景类，继承 LayoutScene（此处仅为示意）
│
├── scripts/                            # 基础设施模块（核心）
│   │
│   ├── layout/                         # 排版布局引擎
│   │   ├── __init__.py                 # 统一导出（LayoutScene, ZoneConstants 等）
│   │   ├── constants.py                # 区域常量定义，映射 layout.md 规范
│   │   ├── zones/                      # 区域容器组件
│   │   │   ├── __init__.py             # 统一导出三个 Zone 类
│   │   │   ├── base.py                 # ZoneBase 抽象基类（固定宽高、边界约束、clamp、溢出检测）
│   │   │   ├── subtitle_zone.py        # 字幕区容器（14.0 x 1.05 单位，Y ∈ [-3.85, -2.8]，比例规则：两区9:1，三区7:1）
│   │   │   ├── main_content_zone.py    # 主内容区容器（单栏/两栏/三栏动态边界）
│   │   │   └── graphics_zone.py        # 图形区容器（溢出优先缩放，防入字幕区）
│   │   ├── engine.py                   # 布局决策引擎（根据内容数量自动选择单/两/三栏）
│   │   ├── optimizer.py                # 布局优化器（文本换行/缩放/颜色保持、防子对象颜色丢失）
│   │   └── scene_base.py               # LayoutScene 场景基类（聚合所有 Zone，提供高层 API；含 CJK 环境自检钩子）
│   │
│   ├── animation/                      # 动画组件库
│   │   ├── __init__.py                 # 统一导出
│   │   └── subtitle_scroller.py        # 字幕滚动管理器（整行直接翻动，无 FadeIn/FadeOut）
│   │
│   ├── environment/                    # 环境自检与 CJK 配置（v1.1 新增）
│   │   ├── __init__.py                 # 统一导出（check / run_setup / RenderPath 等）
│   │   ├── tex_engine_probe.py         # LaTeX 引擎探测（pdflatex / xelatex / lualatex 可用性 + 版本）
│   │   ├── cjk_checker.py              # CJK 综合自检（宏包 kpsewhich + 中文字体 + 渲染路径决策 + 跨平台盘符并行扫描）
│   │   ├── cjk_installer.py            # 缺失组件自动安装（apt/brew/choco 分平台分发；默认 dry_run）
│   │   └── interactive.py              # 交互层（自动检测失败时 stdin 询问用户指定路径/确认安装；仅 TTY 启用）
│   │
│   ├── validation/                     # 验证器模块
│   │   ├── __init__.py                 # 统一导出
│   │   └── course_schema_validator.py  # JSON Schema 验证器（校验课程文件结构正确性）
│   │
│   ├── physics_graphics.py             # 物理图元工厂（force_arrow / circuit / voltmeter / 斜面等；遵循 physics.md 规范）
│   ├── visual_actions.py               # 视觉动作注册表（highlight_xxx / show_xxx 等高亮动画）
│   ├── validate_layout.py              # 布局校验器（_precheck_mobject / boundary check / overlap detect；CLI 入口）
│   ├── validate_course_contents.py     # 课程内容校验器（CLI 入口，遍历 courses/ 目录跑 JSON Schema 校验）
│   ├── tex_tools.py                    # LaTeX 解析工具（符号映射表、parse_mixed_content）
│   ├── subtitle_splitter.py            # 语音文本拆分行（split_utterance）
│   └── split_atom.py                   # 原子拆分工具
│
├── media/                              # 渲染输出（Manim 自动生成的视频和图像）
│    └── videos/
├── concat_videos.sh                    # 多场景合并脚本（项目根目录，与 scenes/ 平级）
├── manim.config                        # manim 构建的基础配置
├── pyproject.toml                      # 项目配置和依赖管理
├── config.py                           # 全局配置（可选）
└── README.md                           # 项目说明
```

## pyproject.toml 示例

```
[project]
name = "my_math_videos"
version = "0.1.0"
description = "数学教学动画项目"
requires-python = ">=3.11"
dependencies = [
    "manim==0.18.1",
    "manim-voiceover[all]==0.3.6",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.manim]
quality = "high"
resolution = "1080p"
fps = 30
```

## 文件命名规范

```
| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 教学内容 JSON | 主题_content.json | matrix_content.json |
| 单场景代码 | 主题_scene.py | matrix_scene.py |
| 分场代码 | 主题_序号_子标题.py | matrix_01_definition.py |
| 主类名 | PascalCase，与文件名对应 | MatrixDefinition |
| 合并脚本 | concat_videos.sh | concat_videos.sh |
```

## 路径变量建议

在生成的代码中，使用相对路径或可配置变量：

# config.py 示例

```python
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
COURSES_DIR = os.path.join(PROJECT_ROOT, "courses")
SCENES_DIR = os.path.join(PROJECT_ROOT, "scenes")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
```
## 单场景 vs 分场

```
| 场景 | 原子数 | 文件组织 |
|------|--------|----------|
| 单场景 | 小于等于 30 | 1 个 JSON + 1 个 Python 文件 |
| 分场 | 大于 30 | 每个场景独立 JSON + Python 文件 + 合并脚本 |
```

## 与 Skill 目录的关系

用户项目目录独立于 Skill 目录。Skill 提供脚本模板和规范，用户项目存放具体内容。

```
~/skills/ManimAnimationGenerator/
~/my_math_videos/
    ├── courses/
    ├── scenes/
    ├── pyproject.toml
    └── outputs/
```
## 验证清单

- [ ] 教学内容 JSON 放在 courses/ 目录
- [ ] 生成的 Python 代码放在 scenes/ 目录
- [ ] 渲染命令输出到 outputs/ 目录
- [ ] 分场时提供 concat_videos.sh 合并脚本