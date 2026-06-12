#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tex_tools.py - LaTeX 解析与验证工具


import re
from typing import List, Dict, Any, Tuple, Optional
from manim import Text, MathTex  # type: ignore


def validate_latex(expr):
    """检查 LaTeX 表达式是否基本合法（含 P1/P4/P5 及补充规则）"""
    # ---- P6：多行环境定界符（前置） ----
    # 在检查嵌套定界符之前先处理，避免被后续 $...$ 匹配切断
    multi_env_pattern = re.compile(
        r"\\begin\s*\{(align|array|gather|multline)\*?\}.*?\\end\s*\{\1\}",
        re.DOTALL,
    )
    for m in multi_env_pattern.finditer(expr):
        block = m.group()
        if block.startswith("$") or block.endswith("$"):
            return False, (
                "多行环境 \\begin{...}...\\end{...} 必须以 $$...$$ 包裹，" "而非 $...$"
            )

    # ---- P1：嵌套定界符检测 ----
    # 逐字符扫描，识别 $...$ 块，检查块内是否有另一个 $ 字符
    pos = 0
    length = len(expr)
    while pos < length:
        if expr[pos] == "$":
            # 进入 math 模式，寻找结束 $
            inner_start = pos + 1
            j = inner_start
            while j < length:
                if expr[j] == "\\":
                    j += 2  # 跳过转义字符
                    continue
                if expr[j] == "$":
                    # 找到结束 $，检查块内是否有另一个 $
                    inner = expr[inner_start:j]
                    if "$" in inner:
                        return False, (
                            "嵌套定界符：$...$ 内不能包含另一个 $。"
                            " 内部 '$...$' 必须改用 \\( ... \\) 或 \\text{} 包裹"
                        )
                    break
                j += 1
            if j >= length or expr[j] != "$":
                return False, "$...$ 定界符未配对"
            pos = j + 1
            continue
        pos += 1

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

    # 检查 MathTex 中是否有中文（MathTex 阶段，非 Tex 阶段）
    # 注意：Tex 中的 $...$ 数学部分也走同样规则
    if re.search(r"[\u4e00-\u9fff]", expr):
        # 如果中文在 $...$ 内（而非在 \text{} 中），则整个表达式不适合 MathTex
        # 先检查中文是否被 \text{} 包裹
        safe_chinese = True
        for m in re.finditer(r"[\u4e00-\u9fff]", expr):
            ch = m.group()
            # 向前查找最近的 $ 或 \text{
            prefix = expr[: m.start()]
            # 找最近未闭合的 \text{
            text_open = prefix.count(r"\text{") - prefix.count(r"\text{}")
            if text_open == 0:
                safe_chinese = False
                break
        if not safe_chinese:
            return False, "MathTex 中不能包含中文，请使用 Tex 或 \\text{} 包裹"

    # ---- P4：斜杠除法检测 ----
    # 在 math 表达式中，除法必须用 \frac{分子}{分母}，而非斜杠 /
    # 单位形式（m/s, kg/m^3 等）除外：排除 "数字/数字" 或 "单字母/单字母" 的单位模式
    # 提取所有 $...$ 块内容进行检测
    dollar_iter = re.finditer(r"\$([^\$]+)\$", expr)
    for m in dollar_iter:
        block = m.group(1)
        # 排除单位模式：前后都是单字符字母/数字的模式（常见单位）
        # 排除已经用 \frac 表示的
        slash_matches = re.finditer(r"/", block)
        for sm in slash_matches:
            slash_pos = sm.start()
            left = block[:slash_pos].strip()
            right = block[slash_pos + 1 :].strip()
            # 单位判断：左侧或右侧是纯符号（字母、数字、指数），整体是科学计数或单位
            # 常见单位模式：m/s, kg/m^3, N/m^2, J/(kg·K) 等
            if re.match(r"^[a-zA-Zα-ωΑ-Ω0-9\^]+$", left) and re.match(
                r"^[a-zA-Zα-ωΑ-Ω0-9\^]+$", right
            ):
                # 可能是单位，跳过
                continue
            if re.match(r"^\d+(\.\d+)?$", left) and re.match(r"^\d+(\.\d+)?$", right):
                # 科学计数分子/分母，跳过
                continue
            # 纯数学表达式中的斜杠除法：必须提示改为 \frac
            return (
                False,
                f"斜杠除法：数学表达式中除法必须用 \\frac{{}}{{}}，"
                f"不能用 /。块 '.../{right}' 需改为 \\frac{{{left}}}{{{right}}}",
            )

    # ---- P5：表达式碎片化检测 ----
    # 由数学运算符（=, +, -, <, >, \leq, \geq, \to 等）连接的量不得被拆到多个 $...$ 块
    # 策略：提取所有 $...$ 块，检测是否有跨块的二元运算符
    blocks = [m.group(1) for m in re.finditer(r"\$([^\$]+)\$", expr)]
    if len(blocks) > 1:
        # 检查连续块之间是否被运算符连接（而非逗号、分号分隔）
        # 找 $ 符号的位置
        dollar_positions = [m.start() for m in re.finditer(r"\$", expr)]
        # 检查两个相邻 $...$ 之间是否有运算符
        ops = re.compile(
            r"(?<![\\a-zA-Z])(=|\+|-|<|>|<=|>=|\\leq|\\le|\\geq|\\ge|\\to|"
            r"\\rightarrow|\\Rightarrow|\\approx|\\equiv)"
        )
        # 扫描 $ 符号对
        for i in range(0, len(dollar_positions) - 1, 2):
            seg_start = dollar_positions[i + 1]  # 第一个块的结束 $
            seg_end = dollar_positions[i + 2]  # 第二个块的开始 $
            between = expr[seg_start:seg_end]
            # 如果两段之间有运算符但没有分隔符（逗号/分号），则碎片化
            if ops.search(between) and not re.search(r"[，,;]", between):
                return (
                    False,
                    "表达式碎片化：由运算符连接的数学量必须位于同一个 $...$ 内，"
                    "禁止拆分为多个 $...$ 块",
                )

    # ---- 中文下标 \text{} 包裹检测（补充规则 3）----
    # 检查 _ 后的内容是否包含中文且未用 \text{} 包裹
    # 匹配 $...$ 块内的下标格式
    for block in [m.group(1) for m in re.finditer(r"\$([^\$]+)\$", expr)]:
        # 找 _ 后跟 { } 的模式
        sub_pattern = re.compile(r"_(\{[^{}]*\})")
        for sm in sub_pattern.finditer(block):
            subscript_content = sm.group(1)[1:-1]  # 去掉 { }
            if re.search(r"[\u4e00-\u9fff]", subscript_content):
                if not subscript_content.startswith(r"\text"):
                    return (
                        False,
                        f"中文下标未包裹：'$v_{{{subscript_content}}}$'"
                        f" 需改为 '$v_{{\\text{{{subscript_content}}}}}$'",
                    )

    return True, "OK"


def validate_latex_strict(expr):
    """
    严格模式：完整 P1/P4/P5 + 补充规则检测。
    返回 (is_valid, messages)，messages 为字符串列表（含所有违规描述）。
    """
    messages = []
    errors = []

    # ---- P6：多行环境定界符 ----
    multi_env_pattern = re.compile(
        r"\\begin\s*\{(align|array|gather|multline)\*?\}.*?\\end\s*\{\1\}",
        re.DOTALL,
    )
    for m in multi_env_pattern.finditer(expr):
        block = m.group()
        if block.startswith("$") or block.endswith("$"):
            errors.append(
                "P6 多行环境定界符：\\begin{...}...\\end{...}"
                " 必须以 $$...$$ 包裹，而非 $...$"
            )

    # ---- P1：嵌套定界符 ----
    pos = 0
    length = len(expr)
    dollar_stack = []  # 存储嵌套的 $ 位置
    while pos < length:
        if expr[pos] == "$":
            # 检查是否与已开 $ 配对（奇数个 $ 嵌套）
            inner_start = pos + 1
            j = inner_start
            while j < length:
                if expr[j] == "\\":
                    j += 2
                    continue
                if expr[j] == "$":
                    break
                j += 1
            if j < length and expr[j] == "$":
                inner = expr[inner_start:j]
                if "$" in inner:
                    errors.append(
                        "P1 嵌套定界符：$...$ 内不能包含另一个 $。"
                        " 内部 '$' 需改用 \\( ... \\) 或 \\text{} 包裹"
                    )
                    break
            pos = j + 1
            continue
        pos += 1

    # 括号匹配
    if expr.count("{") != expr.count("}"):
        errors.append("花括号不匹配")
    if expr.count("(") != expr.count(")"):
        errors.append("圆括号不匹配")

    # 非法命令
    illegal = [r"\ce", r"\begin{circuitikz}", r"\begin{tikz}"]
    for cmd in illegal:
        if cmd in expr:
            errors.append(f"包含非法命令 {cmd}")

    # ---- P4：斜杠除法 ----
    blocks = [m.group(1) for m in re.finditer(r"\$([^\$]+)\$", expr)]
    for block in blocks:
        slash_matches = list(re.finditer(r"/", block))
        for sm in slash_matches:
            slash_pos = sm.start()
            left = block[:slash_pos].strip()
            right = block[slash_pos + 1 :].strip()
            # 单位/科学计数跳过
            if re.match(r"^[a-zA-Zα-ωΑ-Ω0-9\^]+$", left) and re.match(
                r"^[a-zA-Zα-ωΑ-Ω0-9\^]+$", right
            ):
                continue
            if re.match(r"^\d+(\.\d+)?$", left) and re.match(r"^\d+(\.\d+)?$", right):
                continue
            errors.append(
                f"P4 斜杠除法：'/{right}' 需改为 " f"\\frac{{{left}}}{{{right}}}"
            )

    # ---- P5：表达式碎片化 ----
    if len(blocks) > 1:
        dollar_positions = [m.start() for m in re.finditer(r"\$", expr)]
        ops = re.compile(
            r"(?<![\\a-zA-Z])(=|\+|-|<|>|<=|>=|\\leq|\\le|\\geq|\\ge|"
            r"\\to|\\rightarrow|\\Rightarrow|\\approx|\\equiv)"
        )
        for i in range(0, len(dollar_positions) - 1, 2):
            seg_start = dollar_positions[i + 1]
            seg_end = dollar_positions[i + 2]
            between = expr[seg_start:seg_end]
            if ops.search(between) and not re.search(r"[，,;]", between):
                errors.append(
                    "P5 表达式碎片化：由运算符连接的数学量必须位于"
                    "同一个 $...$ 内，禁止拆分为多个块"
                )
                break

    # ---- 中文下标 ----
    for block in blocks:
        sub_pattern = re.compile(r"_(\{[^{}]*\})")
        for sm in sub_pattern.finditer(block):
            subscript_content = sm.group(1)[1:-1]
            if re.search(r"[\u4e00-\u9fff]", subscript_content):
                if not subscript_content.startswith(r"\text"):
                    errors.append(
                        f"中文下标未包裹：'$v_{{{subscript_content}}}$'"
                        f" 需改为 '$v_{{\\text{{{subscript_content}}}}}$'"
                    )

    is_valid = len(errors) == 0
    messages = errors if errors else ["全部规则通过"]
    return is_valid, messages


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
