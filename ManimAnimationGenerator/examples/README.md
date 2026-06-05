# 示例文件

本目录存放 Skill 自带的示例文件，用于演示 JSON 格式和验证 Skill 功能。

## 文件列表

| 文件 | 说明 |
|------|------|
| matrix_course_example.json | 矩阵主题的 JSON 教学内容示例（符合 json_schema.md 规范） |
| matrix_scene.py | 对应的 Manim 动画代码示例（使用新的 LayoutScene 模块） |
| run_example.sh | 一键运行示例脚本 |

## 使用方法

### 1. 验证 JSON 格式

python scripts/validate_course_contents.py --input examples/matrix_course_example.json

### 2. 运行动画示例

manim -ql examples/matrix_scene.py MatrixScene --disable_caching

### 3. 一键运行

bash examples/run_example.sh matrix_course_example.json

## 示例文件内容说明

### matrix_course_example.json

标准化的教学内容 JSON 文件，严格遵循 `references/json_schema.md`，包含：
- `topic`（主题）、`version`（版本）、`source`（来源）
- `prerequisites`（前置知识）
- `atoms`（教学原子序列），每个原子包含 `id`、`type`、`content`、`layout`、`duration` 等字段
- 不再包含 `global_style` 字段（布局统一由原子级 `layout` 控制）

### matrix_scene.py

对应的 Manim 动画代码：
- 继承自 `scripts.layout.scene_base.LayoutScene`
- 从 `courses/` 目录读取 JSON 文件（示例中读取 `examples/matrix_course_example.json`）
- 根据每个原子的 `layout` 字段自动选择垂直、两栏、三栏或居中布局
- 同步 TTS 语音和字幕，调用 `split_utterance` 确保字幕不超过字幕区容量

### run_example.sh

内容如下：

#!/bin/bash
# 一键运行示例：bash run_example.sh matrix_course_example.json

JSON_FILE=$1
if [ -z "$JSON_FILE" ]; then
    echo "用法: bash run_example.sh <json文件名>"
    exit 1
fi

# 验证 JSON
python scripts/validate_course_contents.py --input "examples/$JSON_FILE"

# 渲染动画（场景类名为 MatrixScene）
manim -ql examples/$(basename "$JSON_FILE" .json)_scene.py MatrixScene --disable_caching

## 注意事项

- 运行前确保已安装所有依赖（见 skill.md）
- 示例中的 `visual_action` 名称需与 `scripts/visual_actions.py` 中的预置名称匹配
- 若 EdgeTTS 发音不自然，建议配置付费 TTS 服务（见 references/tts_guide.md）
- 示例 JSON 中的 `graphics.type` 已使用规范枚举（如 `axes`、`function`、`linear_algebra` 等），旧示例如 `feasible`、`contour` 已移除，请使用规范类型
