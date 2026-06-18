# 用户项目构建结构

当用户使用本 Skill 生成教学内容动画时，建议按以下目录结构组织项目文件。

## 推荐目录结构

```
{project_name}/                    # 用户项目根目录
│
├── .venv/
├── references/                    # 规范文档（只读参考，不参与运行）
├── courses/                       # 课程数据（JSON 教学内容文件）
│   ├── *.json                    # 每场景一个 JSON 文件
├── scenes/                        # 场景渲染入口（业务代码）
│   ├── *.py                      # 每场景一个 Python 文件，继承 LayoutScene
├── scripts/                       # 基础设施模块（核心）
│   ├── layout/                   # 排版布局引擎
│   │   ├── constants.py          # 区域常量定义
│   │   ├── engine.py             # 布局决策引擎
│   │   ├── optimizer.py          # 布局优化器
│   │   ├── scene_base.py        # LayoutScene 基类
│   │   └── zones/               # 区域容器（base / main_content / graphics / subtitle）
│   ├── animation/                # 动画组件库
│   │   └── subtitle_scroller.py # 字幕滚动管理器
│   ├── environment/             # 环境自检与 CJK 配置
│   │   ├── tex_engine_probe.py # LaTeX 引擎探测
│   │   ├── cjk_checker.py     # CJK 综合自检
│   │   ├── cjk_installer.py   # 缺失组件自动安装
│   │   └── interactive.py     # 交互层
│   ├── validation/              # 验证器模块
│   │   └── course_schema_validator.py # JSON Schema 验证器
│   ├── physics_graphics.py      # 物理图元工厂
│   ├── visual_actions.py        # 视觉动作注册表
│   ├── validate_layout.py       # 布局校验器
│   ├── validate_course_contents.py # 课程内容校验器
│   ├── tex_tools.py            # LaTeX 解析工具
│   ├── subtitle_splitter.py    # 语音文本拆分器
│   └── split_atom.py           # 原子拆分工具
├── media/videos/               # 渲染输出目录
├── concat_videos.sh            # 多场景合并脚本
├── manim.config                # manim 基础配置
├── pyproject.toml               # 项目配置和依赖管理
├── config.py                    # 全局配置（可选）
└── README.md                    # 项目说明
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

| 类型          | 命名规则                 | 示例                    |
| ------------- | ------------------------ | ----------------------- |
| 教学内容 JSON | 主题_content.json       | matrix_content.json     |
| 单场景代码    | 主题_scene.py           | matrix_scene.py         |
| 分场代码      | 主题*序号*子标题.py      | matrix_01_definition.py |
| 主类名        | PascalCase，与文件名对应 | MatrixDefinition        |
| 合并脚本      | concat_videos.sh         | concat_videos.sh        |

## 路径变量建议

在生成的代码中，建议使用相对路径或可配置变量。路径规范定义示例见 `examples/` 目录下各示例项目的 `config.py` 文件。

## 单场景 vs 分场

| 场景   | 原子数 | 文件组织                                 |
| ------ | ------ | ---------------------------------------- |
| 单场景 | ≤ 30   | 1 个 JSON + 1 个 Python 文件             |
| 分场   | > 30   | 每场景独立 JSON + Python 文件 + 合并脚本 |

## 与 Skill 目录的关系

用户项目目录独立于 Skill 目录。Skill 提供脚本模板和规范，用户项目存放具体内容。

```
~/skills/ManimAnimationGenerator/   # Skill 目录（模板和规范）
~/my_math_videos/                   # 用户项目目录
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
