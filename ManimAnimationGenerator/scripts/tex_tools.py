#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tex_tools.py - LaTeX 解析与验证工具


import re
from typing import List, Dict, Any, Tuple, Optional
from manim import Text, MathTex  # type: ignore


def validate_latex(expr):
    """检查 LaTeX 表达式是否基本合法"""
    # 检查花括号匹配
    if expr.count("{") != expr.count("}"):
        return False, "花括号不匹配"

    # 检查括号匹配
    if expr.count("(") != expr.count(")"):
        return False, "圆括号不匹配"

    # 检查常见非法命令
    illegal = [r"\ce", r"\begin{circuitikz}", r"\begin{tikz}"]
    for cmd in illegal:
        if cmd in expr:
            return False, f"包含非法命令 {cmd}"

    # 检查 MathTex 中是否有中文
    if re.search(r"[\u4e00-\u9fff]", expr):
        return False, "MathTex 中不能包含中文，请使用 Tex"

    return True, "OK"


def split_long_formula(expr, max_width=12):
    """如果公式预估宽度超过 max_width，返回建议的 align* 换行版本"""
    est_width = len(expr) * 0.6
    if est_width <= max_width:
        return expr

    # 简单分割：在 + 或 - 处分割
    parts = re.split(r"(?<=[+\-=])", expr)
    if len(parts) <= 1:
        parts = re.split(r"(?<=\\)", expr)

    wrapped = r"\begin{align*} " + " \\\\ ".join(parts) + r" \end{align*}"
    return wrapped


def math_symbols_to_speech(text):
    """将数学符号（LaTeX 和 Unicode）转换为自然语言读音"""
    mapping = {
        # ========== Unicode 数学符号 ==========
        "≠": "不等于",
        "≤": "小于等于",
        "≥": "大于等于",
        "≈": "约等于",
        "≡": "恒等于",
        "×": "乘以",
        "÷": "除以",
        "·": "点乘",
        "±": "正负",
        "√": "根号",
        "∞": "无穷大",
        "∠": "角",
        "⊥": "垂直于",
        "∥": "平行于",
        "△": "三角形",
        "□": "正方形",
        "○": "圆",
        "°": "度",
        "∵": "因为",
        "∴": "所以",
        "∈": "属于",
        "∉": "不属于",
        "⊂": "包含于",
        "⊃": "包含",
        "⊆": "子集于",
        "⊇": "超集于",
        "∪": "并集",
        "∩": "交集",
        "∅": "空集",
        "∀": "对于任意",
        "∃": "存在",
        "→": "趋向于",
        "⇒": "推出",
        "⇔": "等价于",
        # 希腊字母
        "α": "阿尔法",
        "β": "贝塔",
        "γ": "伽马",
        "δ": "德尔塔",
        "ε": "艾普西龙",
        "ζ": "泽塔",
        "η": "伊塔",
        "θ": "西塔",
        "ι": "约塔",
        "κ": "卡帕",
        "λ": "兰姆达",
        "μ": "缪",
        "ν": "纽",
        "ξ": "克西",
        "π": "派",
        "ρ": "柔",
        "σ": "西格玛",
        "τ": "陶",
        "υ": "宇普西龙",
        "φ": "斐",
        "χ": "凯",
        "ψ": "普西",
        "ω": "欧米伽",
        # ========== LaTeX 关系与逻辑符号 ==========
        "\\neq": "不等于",
        "\\ne": "不等于",
        "\\leq": "小于等于",
        "\\le": "小于等于",
        "\\geq": "大于等于",
        "\\ge": "大于等于",
        "\\approx": "约等于",
        "\\equiv": "恒等于",
        "\\to": "趋向于",
        "\\rightarrow": "趋向于",
        "\\Rightarrow": "推出",
        "\\Leftrightarrow": "等价于",
        "\\because": "因为",
        "\\therefore": "所以",
        "\\forall": "对于任意",
        "\\exists": "存在",
        # ========== LaTeX 运算符号 ==========
        "\\times": "乘以",
        "\\cdot": "点乘",
        "\\div": "除以",
        "\\pm": "正负",
        "\\mp": "负正",
        "\\sqrt": "根号",
        "\\sum": "求和",
        "\\int": "积分",
        "\\prod": "连乘",
        "\\lim": "极限",
        "\\partial": "偏导",
        # ========== LaTeX 几何与集合符号 ==========
        "\\angle": "角",
        "\\perp": "垂直于",
        "\\parallel": "平行于",
        "\\triangle": "三角形",
        "\\odot": "圆",
        "\\circ": "度",
        "\\in": "属于",
        "\\notin": "不属于",
        "\\subset": "包含于",
        "\\supset": "包含",
        "\\subseteq": "子集于",
        "\\supseteq": "超集于",
        "\\cup": "并集",
        "\\cap": "交集",
        "\\emptyset": "空集",
        "\\infty": "无穷大",
        # ========== LaTeX 希腊字母 ==========
        "\\alpha": "阿尔法",
        "\\beta": "贝塔",
        "\\gamma": "伽马",
        "\\delta": "德尔塔",
        "\\epsilon": "艾普西龙",
        "\\zeta": "泽塔",
        "\\eta": "伊塔",
        "\\theta": "西塔",
        "\\iota": "约塔",
        "\\kappa": "卡帕",
        "\\lambda": "兰姆达",
        "\\mu": "缪",
        "\\nu": "纽",
        "\\xi": "克西",
        "\\pi": "派",
        "\\rho": "柔",
        "\\sigma": "西格玛",
        "\\tau": "陶",
        "\\upsilon": "宇普西龙",
        "\\phi": "斐",
        "\\chi": "凯",
        "\\psi": "普西",
        "\\omega": "欧米伽",
    }
    for symbol, replacement in mapping.items():
        text = text.replace(symbol, replacement)
    return text


def is_math_only(expr):
    """判断是否纯数学公式（无中文）"""
    return not re.search(r"[\u4e00-\u9fff]", expr)


def choose_tex_class(expr):
    """根据表达式内容自动选择 MathTex 或 Tex"""
    if is_math_only(expr):
        return "MathTex"
    else:
        return "Tex"


# ============================================================
# 中文与公式混排自动拆分
# ============================================================


def has_chinese(text: str) -> bool:
    """检查字符串是否包含中文字符"""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def has_latex(text: str) -> bool:
    """检查是否包含 LaTeX 命令（含 \\ 换行符）"""
    return bool(re.search(r"\\(?:[a-zA-Z]+|.)", text))


def split_mixed_string(text: str) -> List[tuple]:
    """
    将混合字符串拆分为 (text, type) 对

    输入: "矩阵 a_{ij} 表示第 i 行第 j 列的元素"
    输出: [
        ("矩阵 ", "content"),
        ("a_{ij}", "formula"),
        (" 表示第 i 行第 j 列的元素", "content")
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

        # 模式1: \begin{...} ... \end{...}
        begin_match = re.search(r"\\begin\{[a-zA-Z*]+\}", text[current_pos:])
        if begin_match:
            formula_start = current_pos + begin_match.start()
            env_name = re.search(
                r"\\begin\{([a-zA-Z*]+)\}", text[formula_start:]
            ).group(1)
            end_pattern = rf"\\end\{{{env_name}\}}"
            end_match = re.search(end_pattern, text[formula_start:])
            if end_match:
                formula_end = formula_start + end_match.end()
                result.append((text[formula_start:formula_end], "formula"))
                current_pos = formula_end
                continue

        # 模式2: 反斜杠命令（含 \\\\、\\neq、\\div、\\vec 等）
        cmd_match = re.search(r"\\(?:[a-zA-Z]+|.)", text[current_pos:])
        if cmd_match:
            formula_start = current_pos + cmd_match.start()
            j = formula_start + cmd_match.end()
            brace_count = 0
            while j < length:
                if text[j] == "{":
                    brace_count += 1
                elif text[j] == "}":
                    brace_count -= 1
                    if brace_count == 0 and j + 1 < length and text[j + 1] not in "_{}":
                        j += 1
                        break
                j += 1
            formula_end = j
            result.append((text[formula_start:formula_end], "formula"))
            current_pos = formula_end
            continue

        # 模式3: 下标 a_{i}
        sub_match = re.search(r"[a-zA-Z]_\{[^}]+\}", text[current_pos:])
        if sub_match:
            formula_start = current_pos + sub_match.start()
            formula_end = formula_start + sub_match.end()
            result.append((text[formula_start:formula_end], "formula"))
            current_pos = formula_end
            continue

        # 模式4: 上标 a^{i}
        sup_match = re.search(r"[a-zA-Z]\^\{[^}]+\}", text[current_pos:])
        if sup_match:
            formula_start = current_pos + sup_match.start()
            formula_end = formula_start + sup_match.end()
            result.append((text[formula_start:formula_end], "formula"))
            current_pos = formula_end
            continue

        # 没有找到公式，剩余全部作为 content
        if current_pos < length:
            result.append((text[current_pos:], "content"))
        break

    # 合并相邻的 content 类型
    merged = []
    for seg_text, seg_type in result:
        if merged and merged[-1][1] == seg_type == "content":
            merged[-1] = (merged[-1][0] + seg_text, seg_type)
        else:
            merged.append((seg_text, seg_type))

    return merged


def parse_mixed_content(
    content_list: List[Dict[str, Any]],
    font_size: int = 34,
    color_emphasis: str = "#66DDFF",
    color_text: str = "#FFFFFF",
) -> List:
    """
    解析 content 列表，自动处理中文与公式混排

    支持两种模式：
    1. 标准模式：content 已按规范拆分（type 为 content/highlight/formula）
    2. 智能模式：检测 formula 中的中文，自动拆分

    返回 Mobject 列表（用于 Manim 动画）
    """
    from manim import Text, MathTex, VGroup

    result_mobs = []

    for item in content_list:
        text = item.get("text", "")
        item_type = item.get("type", "content")

        if item_type == "formula":
            if has_chinese(text):
                split_items = split_mixed_string(text)
                for sub_text, sub_type in split_items:
                    mobj = _create_simple_mobject(
                        sub_text, sub_type, font_size, color_emphasis, color_text
                    )
                    result_mobs.append(mobj)
            else:
                mobj = MathTex(text, font_size=font_size, color=color_text)
                result_mobs.append(mobj)
        elif item_type == "highlight":
            if has_chinese(text):
                if has_latex(text):
                    split_items = split_mixed_string(text)
                    for sub_text, sub_type in split_items:
                        mobj = _create_simple_mobject(
                            sub_text, sub_type, font_size, color_emphasis, color_text
                        )
                        result_mobs.append(mobj)
                else:
                    result_mobs.append(
                        Text(text, font_size=font_size, color=color_emphasis)
                    )
            else:
                result_mobs.append(
                    MathTex(text, font_size=font_size, color=color_emphasis)
                )
        else:
            if has_latex(text):
                split_items = split_mixed_string(text)
                for sub_text, sub_type in split_items:
                    mobj = _create_simple_mobject(
                        sub_text, sub_type, font_size, color_emphasis, color_text
                    )
                    result_mobs.append(mobj)
            elif has_chinese(text) or not re.search(r"[a-zA-Z0-9\^_{}]", text):
                result_mobs.append(Text(text, font_size=font_size, color=color_text))
            else:
                result_mobs.append(MathTex(text, font_size=font_size, color=color_text))

    return result_mobs


def _create_simple_mobject(
    text: str, item_type: str, font_size: int, color_emphasis: str, color_text: str
):
    """创建单个简单 Mobject（不含公式拆分逻辑）"""

    if item_type == "formula":
        # 关键：formula 类型禁止包含中文
        if has_chinese(text):
            # 如果走到这里，说明之前的拆分逻辑有遗漏，强制降级为 Text
            return Text(text, font_size=font_size, color=color_text)
        return MathTex(text, font_size=font_size, color=color_text)
    elif item_type == "highlight":
        if has_chinese(text):
            return Text(text, font_size=font_size, color=color_emphasis)
        else:
            return MathTex(text, font_size=font_size, color=color_emphasis)
    else:
        return Text(text, font_size=font_size, color=color_text)


def fix_mixed_formula_in_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    在 JSON 预处理阶段拆分包含中文的 formula
    用于 validate_course_contents.py 中
    """
    if "atoms" not in data:
        return data

    fixed_data = data.copy()
    fixed_atoms = []

    for atom in fixed_data.get("atoms", []):
        if "content" not in atom:
            fixed_atoms.append(atom)
            continue

        new_content = []
        for item in atom.get("content", []):
            if not isinstance(item, dict):
                new_content.append(item)
                continue

            text = item.get("text", "")
            item_type = item.get("type", "content")

            if item_type == "formula" and has_chinese(text):
                split_items = split_mixed_string(text)
                for sub_text, sub_type in split_items:
                    new_content.append({"text": sub_text, "type": sub_type})
            else:
                new_content.append(item)

        fixed_atom = atom.copy()
        fixed_atom["content"] = new_content
        fixed_atoms.append(fixed_atom)

    fixed_data["atoms"] = fixed_atoms
    return fixed_data
