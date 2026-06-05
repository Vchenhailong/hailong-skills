#!/bin/bash
# 一键运行示例脚本
# 用法: bash run_example.sh [json文件名]

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 默认 JSON 文件名
JSON_FILE="${1:-matrix_course_example.json}"
JSON_PATH="$SCRIPT_DIR/$JSON_FILE"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Manim 动画生成示例${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查 JSON 文件是否存在
if [ ! -f "$JSON_PATH" ]; then
    echo -e "${RED}错误: JSON 文件不存在: $JSON_PATH${NC}"
    exit 1
fi
echo -e "${GREEN}使用 JSON: $JSON_FILE${NC}"

# 1. 验证 JSON 格式
echo -e "${YELLOW}[1/3] 验证 JSON 格式...${NC}"
python "$PROJECT_ROOT/scripts/validate_course_contents.py" --input "$JSON_PATH" --validate-only
if [ $? -ne 0 ]; then
    echo -e "${RED}JSON 验证失败，尝试自动修复...${NC}"
    python "$PROJECT_ROOT/scripts/validate_course_contents.py" --input "$JSON_PATH"
fi

# 2. 渲染动画
echo -e "${YELLOW}[2/3] 渲染动画...${NC}"
SCENE_NAME="MatrixScene"
python -m manim -pql "$SCRIPT_DIR/matrix_scene.py" "$SCENE_NAME" --disable_caching

# 3. 完成
echo -e "${GREEN}[3/3] 完成！${NC}"
echo -e "${GREEN}视频已生成并自动播放${NC}"
