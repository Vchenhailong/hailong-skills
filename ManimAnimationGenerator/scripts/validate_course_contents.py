#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学内容 JSON 校验与解析脚本

职责：
1. 校验 JSON 结构是否符合 Schema
2. 自动修复不合规的内容（如将含中文的 formula 拆分为 content + formula）
3. 为代码生成阶段提供标准化的数据接口

用法：
    # 校验并修复单个文件
    python scripts/validate_course_contents.py -i outputs/matrix_content.json

    # 仅校验不修改
    python scripts/validate_course_contents.py -i outputs/matrix_content.json --validate-only

    # 批量处理目录下所有 JSON
    python scripts/validate_course_contents.py --batch --dir outputs/
"""

import json
import math
import os
import re
import argparse
from typing import List, Dict, Any, Tuple, Optional

# ============================================================
# 常量定义
# ============================================================

# 合法的原子类型
VALID_ATOM_TYPES = {
    "definition",
    "intuition",
    "operation",
    "counter_intuitive",
    "application",
    "summary",
}

# 合法的内容类型
VALID_CONTENT_TYPES = {"highlight", "content", "formula", "mixed"}

# 合法的布局类型
VALID_LAYOUT_TYPES = {"vertical", "two_column", "three_column", "centered"}

# 颜色映射
COLOR_MAP = {"highlight": "#66DDFF", "content": "#FFFFFF", "formula": "#FFFFFF"}


# ============================================================
# 工具函数
# ============================================================


def has_chinese(text: str) -> bool:
    """检查字符串是否包含中文字符"""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def is_pure_latex_formula(text: str) -> bool:
    """
    判断是否为纯 LaTeX 公式（不含中文，符合数学语法）
    """
    if not text or has_chinese(text):
        return False

    # 包含 LaTeX 命令
    latex_patterns = [
        r"\\begin\{",
        r"\\end\{",
        r"\\frac",
        r"\\sqrt",
        r"\\overline",
        r"\\text\{",
        r"\\vec",
        r"\\neq",
        r"\\Rightarrow",
        r"\\Leftrightarrow",
        r"\\sum",
        r"\\int",
        r"\\alpha",
        r"\\beta",
        r"\\gamma",
        r"\\theta",
        r"\\matrix",
        r"\\begin\{pmatrix\}",
        r"\\begin\{bmatrix\}",
        r"_\{",
        r"\^\{",
        r"\\\[",
        r"\\\]",
    ]
    for pattern in latex_patterns:
        if re.search(pattern, text):
            return True

    # 纯数学表达式（字母、数字、运算符、括号）
    if re.match(r"^[a-zA-Z0-9\s\+\-\*\/\=\_\^\{\}\(\)\[\]\.,;:!?]+$", text):
        return True

    return False


def split_mixed_content(text: str) -> List[Dict[str, str]]:
    """
    将混合了中文和公式的文本拆分为多个元素

    支持：
    - 反斜杠命令: \frac, \sqrt, \begin{pmatrix}...\end{pmatrix}
    - 下标: a_{i}, a_{ij}, a_{i,j}
    - 上标: a^{i}, a^{ij}
    - 内联公式: $...$

    示例：
        输入: "矩阵 a_{ij} 表示第 i 行第 j 列的元素"
        输出: [
            {"text": "矩阵 ", "type": "content"},
            {"text": "a_{ij}", "type": "formula"},
            {"text": " 表示第 i 行第 j 列的元素", "type": "content"}
        ]
    """
    if not text:
        return []

    result = []
    current_pos = 0
    length = len(text)

    while current_pos < length:
        formula_start = -1
        formula_end = -1

        # 剩余文本
        remaining = text[current_pos:]

        # 模式1: \begin{...}...\end{...}
        begin_match = re.search(r"\\begin\{([a-zA-Z*]+)\}", remaining)
        if begin_match:
            formula_start = current_pos + begin_match.start()
            env_name = begin_match.group(1)
            end_pattern = rf"\\end\{{{env_name}\}}"
            end_match = re.search(end_pattern, remaining[begin_match.start() :])
            if end_match:
                formula_end = (
                    formula_start
                    + begin_match.end()
                    + end_match.start()
                    + end_match.end()
                )
                result.append(
                    {"text": text[formula_start:formula_end], "type": "formula"}
                )
                current_pos = formula_end
                continue

        # 模式2: 反斜杠命令（单个命令，可能带参数）
        cmd_match = re.search(r"\\(?:[a-zA-Z]+|.)", remaining)
        if cmd_match:
            formula_start = current_pos + cmd_match.start()
            j = formula_start + cmd_match.end()
            brace_count = 0
            in_brace = False
            while j < length:
                if text[j] == "{":
                    brace_count += 1
                    in_brace = True
                elif text[j] == "}":
                    brace_count -= 1
                    if brace_count == 0 and in_brace:
                        j += 1
                        if j < length and text[j] in "_{}":
                            continue
                        break
                elif text[j] in " \t\n" and brace_count == 0:
                    break
                j += 1
            formula_end = j
            result.append({"text": text[formula_start:formula_end], "type": "formula"})
            current_pos = formula_end
            continue

        # 模式3: 下标 a_{i} 或 a_{ij} 或 a_{i,j}
        sub_match = re.search(r"[a-zA-Z]\_\{[^}]+\}", remaining)
        if sub_match:
            formula_start = current_pos + sub_match.start()
            formula_end = formula_start + sub_match.end()
            result.append({"text": text[formula_start:formula_end], "type": "formula"})
            current_pos = formula_end
            continue

        # 模式4: 上标 a^{i} 或 a^{ij}
        sup_match = re.search(r"[a-zA-Z]\^\{[^}]+\}", remaining)
        if sup_match:
            formula_start = current_pos + sup_match.start()
            formula_end = formula_start + sup_match.end()
            result.append({"text": text[formula_start:formula_end], "type": "formula"})
            current_pos = formula_end
            continue

        # 模式5: 内联公式 $...$
        inline_match = re.search(r"\$[^\$]+\$", remaining)
        if inline_match:
            formula_start = current_pos + inline_match.start()
            formula_end = formula_start + inline_match.end()
            result.append({"text": text[formula_start:formula_end], "type": "formula"})
            current_pos = formula_end
            continue

        # 没有找到公式，剩余全部作为 content
        if current_pos < length:
            result.append({"text": text[current_pos:], "type": "content"})
        break

    # 合并相邻的 content 类型
    merged = []
    for item in result:
        if merged and merged[-1]["type"] == "content" and item["type"] == "content":
            merged[-1]["text"] += item["text"]
        else:
            merged.append(item.copy())

    return merged


# ============================================================
# JSON 校验与修复
# ============================================================


def validate_and_fix_atom(
    atom: Dict[str, Any], fix: bool = True
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    校验并修复单个原子对象

    返回: (是否有效, 错误列表, 修复后的原子)
    """
    errors = []
    fixed_atom = atom.copy() if fix else atom

    # 检查必填字段
    if "id" not in atom:
        errors.append("缺少 id 字段")
    elif not isinstance(atom["id"], str):
        errors.append("id 字段必须是字符串")

    if "type" not in atom:
        errors.append("缺少 type 字段")
    elif atom["type"] not in VALID_ATOM_TYPES:
        errors.append(f"type 值 '{atom['type']}' 不合法，合法值: {VALID_ATOM_TYPES}")

    if "content" not in atom:
        errors.append("缺少 content 字段")
    elif not isinstance(atom["content"], list):
        errors.append("content 字段必须是数组")
    elif len(atom["content"]) == 0:
        errors.append("content 数组不能为空")

    if "duration" not in atom:
        if fix:
            fixed_atom["duration"] = 6.0
        else:
            errors.append("缺少 duration 字段")
    elif not isinstance(atom["duration"], (int, float)):
        errors.append("duration 字段必须是数字")

    # 校验 layout 字段
    if "layout" in atom:
        if atom["layout"] not in VALID_LAYOUT_TYPES:
            errors.append(
                f"layout 值 '{atom['layout']}' 不合法，合法值: {VALID_LAYOUT_TYPES}"
            )

    # ===== duration 校验 =====
    # 规则：min_duration = ceil(len(speech) / 4)，向上取整
    speech = atom.get("speech", "")
    duration = atom.get("duration")
    if speech and duration is not None:
        min_duration = math.ceil(len(speech) / 4.0)  # 语音速度约4字符/秒
        if duration < min_duration:
            if fix:
                fixed_atom["duration"] = min_duration
            else:
                errors.append(
                    f"duration={duration} < 最小值{min_duration} "
                    f"（{len(speech)}字 ÷ 4字符/秒）"
                )

    # 修复 content 数组
    if "content" in atom and isinstance(atom["content"], list) and fix:
        new_content = []
        for item in atom["content"]:
            if not isinstance(item, dict):
                continue

            text = item.get("text", "")
            item_type = item.get("type", "content")

            # 检查 item_type 合法性
            if item_type not in VALID_CONTENT_TYPES:
                item_type = "content"

            # formula 类型检查：包含中文的必须拆分
            if item_type == "formula" and has_chinese(text):
                # 拆分为多个元素
                split_items = split_mixed_content(text)
                if len(split_items) > 1:
                    new_content.extend(split_items)
                else:
                    # 无法拆分，降级为 content
                    new_content.append({"text": text, "type": "content"})
            else:
                new_content.append({"text": text, "type": item_type})
        fixed_atom["content"] = new_content

    # 校验 graphics 字段（仅校验类型和必填字段，不校验 type 的具体枚举值）
    if "graphics" in atom and atom["graphics"] is not None:
        graphics = atom["graphics"]
        if not isinstance(graphics, dict):
            errors.append("graphics 字段必须是对象")
        elif "type" not in graphics:
            errors.append("graphics 缺少 type 字段")

    return len(errors) == 0, errors, fixed_atom


def validate_and_fix_json(
    data: Dict[str, Any], fix: bool = True
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    校验并修复整个 JSON 数据

    返回: (是否有效, 错误列表, 修复后的数据)
    """
    errors = []
    fixed_data = data.copy() if fix else data

    # 检查顶层字段
    if "topic" not in data:
        errors.append("缺少 topic 字段")

    if "version" not in data:
        errors.append("缺少 version 字段")

    if "atoms" not in data:
        errors.append("缺少 atoms 字段")
    elif not isinstance(data["atoms"], list):
        errors.append("atoms 字段必须是数组")
    else:
        fixed_atoms = []
        for i, atom in enumerate(data["atoms"]):
            is_valid, atom_errors, fixed_atom = validate_and_fix_atom(atom, fix)
            if atom_errors:
                for err in atom_errors:
                    errors.append(f"atoms[{i}].{err}")
            if fix:
                fixed_atoms.append(fixed_atom)
        if fix:
            fixed_data["atoms"] = fixed_atoms

    return len(errors) == 0, errors, fixed_data


# ============================================================
# 主入口
# ============================================================


def process_file(
    input_path: str,
    output_path: Optional[str] = None,
    fix: bool = True,
    verbose: bool = True,
) -> bool:
    """
    处理单个 JSON 文件

    返回: 是否处理成功
    """
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件失败 {input_path}: {e}")
        return False

    is_valid, errors, fixed_data = validate_and_fix_json(data, fix)

    if errors:
        print(f"校验失败 {input_path}:")
        for err in errors:
            print(f"  - {err}")
        if not fix:
            return False

    if fix:
        output = output_path or input_path
        try:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(fixed_data, f, ensure_ascii=False, indent=2)
            if verbose:
                print(f"已保存: {output}")
                if errors:
                    print(f"  已修复 {len(errors)} 个问题")
        except Exception as e:
            print(f"保存文件失败 {output}: {e}")
            return False

    return True


def batch_process(directory: str, fix: bool = True) -> None:
    """批量处理目录下的所有 JSON 文件"""
    json_files = [f for f in os.listdir(directory) if f.endswith(".json")]
    for filename in json_files:
        filepath = os.path.join(directory, filename)
        print(f"处理: {filename}")
        process_file(filepath, fix=fix)


def main():
    parser = argparse.ArgumentParser(description="教学内容 JSON 校验与解析工具")
    parser.add_argument("--input", "-i", type=str, help="输入 JSON 文件路径")
    parser.add_argument(
        "--output", "-o", type=str, help="输出 JSON 文件路径（默认覆盖输入）"
    )
    parser.add_argument("--batch", "-b", action="store_true", help="批量处理模式")
    parser.add_argument(
        "--dir", "-d", type=str, default="courses/", help="批量处理时指定的目录"
    )
    parser.add_argument(
        "--validate-only", "-v", action="store_true", help="仅校验，不修复"
    )
    args = parser.parse_args()

    fix = not args.validate_only

    if args.batch:
        batch_process(args.dir, fix)
    elif args.input:
        process_file(args.input, args.output, fix)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
