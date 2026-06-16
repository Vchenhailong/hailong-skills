#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
布局自动优化器 - 运行时迭代调整机制

职责：
- 当 validate_layout() 发现溢出违规时，自动执行 3 轮递进调整
- 调整策略：①缩小字号 → ②换行 → ③拆分原子
- 返回优化结果（是否成功 + 调整日志）

优化流程：
1. 检测违规类型（WIDTH_OVERFLOW / HEIGHT_OVERFLOW）
2. 按优先级尝试调整方案
3. 每轮调整后重新测量并验证
4. 若 3 轮全部失败，返回失败报告（建议人工干预）
"""

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from manim import Mobject, VGroup, Text, MathTex, Tex, TexTemplate, DOWN

from scripts.layout.engine import LayoutEngine
from scripts.layout.constants import ZoneConstants


# ============================================================
# minipage 路径：em 宽度探针缓存
# ============================================================
#
# 1em 在不同字号下的 Manim 实际宽度不同。
# 用 Tex(r"\rule{1em}{0.5em}", font_size=N) 测一次即可。
# 同一 (manim_width, font_size) 组合的探测结果可复用。
#
# cache key: (manim_width, font_size)
# cache val: em 数量 (float)
_EM_WIDTH_CACHE: Dict[Tuple[float, int], float] = {}


# 跨调用复用的 xelatex + xeCJK 模板（避免每次重建）
# 同时缓存探测成功的状态，避免 LaTeX 首次失败后回退值被永久污染。
_XELATEX_TEMPLATE_CACHE: Optional[TexTemplate] = None


def _get_xelatex_template() -> TexTemplate:
    """获取 xelatex + xeCJK 模板（带中文字体，跨平台）

    缓存为模块级单例，避免每次 wrap 都重建。
    字体优先级（按系统平台自动选择）：
    - Windows: Microsoft YaHei > SimHei > 微软雅黑
    - macOS:   PingFang SC > Hiragino Sans GB > STHeiti
    - Linux:   Noto Sans CJK SC > WenQuanYi Micro Hei > Source Han Sans SC

    若指定字体在当前平台不存在，xeCJK 会回退到系统默认 CJK 字体，
    但渲染尺寸可能与预期不一致，故显式按平台选择。

    ⚠ 一致性约束：
    - 不加 [Scale=X]：CJK 字体必须按 font_size 100% 渲染
    - 若加 [Scale=0.92]，CJK 字符有效尺寸 = font_size × 0.92 < Pango 路径
    - 这会导致 minipage 路径比 Pango 兜底路径"看起来字体更小"，违反一致性
    - 字号与栏宽的协调由 _compute_em_width 负责，字体本身不缩放
    """
    global _XELATEX_TEMPLATE_CACHE
    if _XELATEX_TEMPLATE_CACHE is not None:
        return _XELATEX_TEMPLATE_CACHE
    template = TexTemplate(tex_compiler="xelatex")
    # 不加 [Scale=X]：CJK 字符渲染尺寸严格等于 font_size，与 Pango 一致
    import platform

    system = platform.system()
    if system == "Windows":
        cjk_main = "Microsoft YaHei"
        cjk_sans = "Microsoft YaHei"
    elif system == "Darwin":  # macOS
        cjk_main = "PingFang SC"
        cjk_sans = "PingFang SC"
    else:  # Linux / 其他
        cjk_main = "Noto Sans CJK SC"
        cjk_sans = "Noto Sans CJK SC"
    template.preamble = (
        r"\usepackage{xeCJK}"
        "\n"
        rf"\setCJKmainfont{{{cjk_main}}}"
        "\n"
        rf"\setCJKsansfont{{{cjk_sans}}}"
        "\n"
    )
    _XELATEX_TEMPLATE_CACHE = template
    return template


@dataclass
class OptimizationResult:
    """优化结果"""

    success: bool  # 是否优化成功
    rounds_executed: int  # 执行了几轮调整（0-3）
    adjustments: List[Dict[str, Any]]  # 调整日志
    error_message: Optional[str] = None  # 失败时的错误信息

    @property
    def is_successful(self) -> bool:
        """判断是否成功"""
        return self.success


class LayoutOptimizer:
    """布局自动优化器

    当 validate_layout() 返回违规时，自动执行迭代调整。

    调整策略（按优先级）：
    1. **缩小字号**：字体缩放至可用空间内（最小 24px）
    2. **换行策略**：长文本/公式拆分为多行（使用 align* 环境）
    3. **内容拆分**：将原子拆分为多个独立原子（触发外部回调）

    运行流程：
    ```
    1. 检测违规 → 2. 尝试方案① → 3. 重新测量 → 4. 验证
       ↓（失败）
       尝试方案② → 重新测量 → 验证（失败）
       ↓
       尝试方案③ → 调用拆分回调 → 结束
    ```
    """

    # 字体大小限制
    MIN_FONT_SIZE = 24
    MAX_FONT_SIZE = 34
    SCALE_FACTOR_PER_ROUND = 0.9  # 每轮缩放系数

    # 调整策略枚举
    STRATEGY_SCALE = "scale_font"
    STRATEGY_WRAP = "wrap_content"
    STRATEGY_SPLIT = "split_atom"

    def __init__(
        self,
        on_split_callback: Optional[callable] = None,
    ):
        """初始化优化器

        Args:
            on_split_callback: 当需要拆分原子时调用的回调函数
                签名：callback(violation_type, mobject, suggested_id)
                用于触发外部逻辑（如 JSON 拆分、重新生成代码）
        """
        self._on_split = on_split_callback
        self._adjustments: List[Dict[str, Any]] = []

    def optimize(
        self,
        mobjects: List[Mobject],
        violations: List[Dict[str, Any]],
        column_layout: Optional[Dict] = None,
        max_height: float = 5.5,
    ) -> OptimizationResult:
        """执行自动优化（核心方法）

        Args:
            mobjects: 需要优化的 Mobject 列表（会原地修改）
            violations: validate_layout() 返回的违规列表
            column_layout: 当前栏位布局信息（含 x_min/x_max/width）
            max_height: 允许的最大高度（默认 5.5 单位）

        Returns:
            OptimizationResult 优化结果

        示例::

            violations = scene.validate_layout(all_mobjects)
            if violations:
                optimizer = LayoutOptimizer()
                result = optimizer.optimize(all_mobjects, violations, column_layout)
                if result.success:
                    print(f"优化成功，共执行 {result.rounds_executed} 轮调整")
                else:
                    print(f"优化失败：{result.error_message}")
        """
        self._adjustments = []
        current_mobjects = mobjects
        max_rounds = 3  # 最多 3 轮

        # round_count 放在 for 内部，每个违规独立计数 3 轮，
        # 避免第一个违规耗尽 3 轮后 round_count == 3，
        # 后续违规的 while 条件直接为 False。
        # 此外，单次 _verify_no_violation 通过后不要立即 return，
        # 所有违规都尝试处理后再统一判断 success。
        remaining_violations: List[Dict[str, Any]] = list(violations)
        processed_violations: List[Dict[str, Any]] = []
        all_resolved = True

        for violation in list(remaining_violations):
            round_count = 0
            # 跟踪已尝试过的策略，避免同轮重复使用同一策略（升级到下一策略）
            tried_strategies = set()
            resolved = False
            while round_count < max_rounds:
                round_count += 1
                strategy = self._select_strategy(violation, current_mobjects)
                # 升级策略：若该策略本轮已尝试过但未消除违规，则跳过它选择下一个
                if strategy in tried_strategies:
                    if self.STRATEGY_SPLIT not in tried_strategies:
                        strategy = self.STRATEGY_SPLIT
                    else:
                        # 三种策略都用过了，本违规已无更多方案可走
                        break

                if strategy == self.STRATEGY_SCALE:
                    success = self._apply_scale(current_mobjects, violation)
                elif strategy == self.STRATEGY_WRAP:
                    success = self._apply_wrap(current_mobjects, violation)
                else:  # STRATEGY_SPLIT
                    success = self._apply_split(violation, current_mobjects)

                tried_strategies.add(strategy)

                if success:
                    # 记录调整日志
                    self._adjustments.append(
                        {
                            "round": round_count,
                            "strategy": strategy,
                            "violation_type": violation["type"],
                            "success": True,
                        }
                    )

                    # 重新测量并验证
                    if self._verify_no_violation(current_mobjects, [violation]):
                        resolved = True
                        processed_violations.append(violation)
                        break
                    # 策略成功了但违规未消失 → 清空 tried_strategies 让升级生效
                    tried_strategies.clear()
                else:
                    # 当前策略失败，尝试下一个策略
                    self._adjustments.append(
                        {
                            "round": round_count,
                            "strategy": strategy,
                            "violation_type": violation["type"],
                            "success": False,
                        }
                    )

            if not resolved:
                all_resolved = False
                logging.warning(
                    f"[optimize] 违规 {violation.get('type')} 处理失败，"
                    f"对象 {violation.get('object_name')}"
                )

        if all_resolved and self._verify_no_violation(
            current_mobjects, remaining_violations
        ):
            return OptimizationResult(
                success=True,
                rounds_executed=sum(1 for _ in self._adjustments),
                adjustments=self._adjustments,
            )

        # 所有违规所有轮次执行完毕仍失败
        return OptimizationResult(
            success=False,
            rounds_executed=sum(1 for _ in self._adjustments),
            adjustments=self._adjustments,
            error_message=(
                f"经过自动优化仍无法解决布局问题。\n"
                f"建议：将相关原子拆分为更细粒度的独立原子。"
                f"\n调整日志：{self._format_adjustments()}"
            ),
        )

    def _select_strategy(
        self,
        violation: Dict[str, Any],
        mobjects: List[Mobject],
    ) -> str:
        """选择当前应使用的调整策略

        策略选择逻辑：
        1. 首次遇到 WIDTH_OVERFLOW → 尝试缩小字号
        2. 首次遇到 HEIGHT_OVERFLOW → 尝试换行
        3. 字号已接近下限或换行无效 → 强制拆分

        Args:
            violation: 违规信息（含 type 字段）
            mobjects: 当前 Mobject 列表

        Returns:
            策略名称（STRATEGY_SCALE / STRATEGY_WRAP / STRATEGY_SPLIT）
        """
        violation_type = violation.get("type", "")

        # 检查是否有多行公式（适合换行）
        has_multirow_formulas = any(
            isinstance(m, MathTex) and "\\\\" in m.get_tex_string()
            for m in mobjects
            if hasattr(m, "get_tex_string")
        )

        if violation_type == "WIDTH_OVERFLOW":
            # 宽度溢出：优先缩小字号
            return self.STRATEGY_SCALE
        elif violation_type == "HEIGHT_OVERFLOW":
            # 高度溢出：优先换行（如果有公式）
            return self.STRATEGY_WRAP if has_multirow_formulas else self.STRATEGY_SCALE

        # 默认尝试缩放
        return self.STRATEGY_SCALE

    def _apply_scale(
        self,
        mobjects: List[Mobject],
        violation: Dict[str, Any],
    ) -> bool:
        """应用字体缩小策略

        对所有 Text/MathTex 对象统一缩放到 0.9 倍，直至达到最小字号。

        Args:
            mobjects: Mobject 列表
            violation: 违规信息

        Returns:
            是否成功应用
        """
        scaled_count = 0
        for mobj in mobjects:
            if isinstance(mobj, (Text, MathTex)):
                current_size = getattr(mobj, "font_size", 32)
                if current_size > self.MIN_FONT_SIZE:
                    new_size = max(
                        int(current_size * self.SCALE_FACTOR_PER_ROUND),
                        self.MIN_FONT_SIZE,
                    )
                    mobj.font_size = new_size
                    scaled_count += 1

        return scaled_count > 0

    def _apply_wrap(
        self,
        mobjects: List[Mobject],
        violation: Dict[str, Any],
    ) -> bool:
        """应用换行策略

        对过宽的 Text/MathTex 对象按可用栏宽截断并重建为多行对象。

        处理逻辑：
        - Text 对象：minipage 路径（xelatex）→ 失败回退到 Pango 路径
        - MathTex 对象：对长公式字符串按字符数阈值拆分，用 \\\\ 插入换行
        - 非文本类 Mobject：跳过（缩放或拆分处理）

        与栏位缩放的一致性保证：
        - 换行目标是 column_width（与 place_*_column 内部 scale 算式用同一常量）
        - 换行后内容 width ≤ target * 0.95，place_*_column 再算 scale_factor ≥ 1.0
        - 因此栏位缩放对换行后的内容不再触发，避免双重缩放
        - 若调用方传 use_minipage=False，强制走 Pango 路径

        Args:
            mobjects: Mobject 列表
            violation: 违规信息，含 column_width / use_minipage

        Returns:
            是否成功应用了至少一次换行
        """
        # 从 violation 或 column_layout 中获取目标栏宽（单位：Manim 坐标）
        target_width = violation.get("column_width", None)
        if target_width is None:
            # 回退：使用违规对象的实际超宽比例估算目标宽度
            target_width = (
                ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MAX
                - ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MIN
            )

        # 是否走 minipage 路径：默认通过 LayoutScene.is_minipage_available()
        # 决定；调用方可传 use_minipage=False 强制 Pango
        use_minipage = violation.get("use_minipage", None)
        if use_minipage is None:
            try:
                # 延迟导入避免循环依赖
                from scripts.layout.scene_base import LayoutScene

                use_minipage = LayoutScene.is_minipage_available()
            except Exception:
                use_minipage = False

        wrapped_count = 0
        for i, mobj in enumerate(mobjects):
            if isinstance(mobj, Text):
                if use_minipage:
                    # 先试 minipage（LaTeX 高质量断行）
                    wrapped = _wrap_text_with_minipage(mobj, target_width)
                    if not wrapped:
                        # 失败回退到 Pango 路径
                        wrapped = self._wrap_text_object(mobj, target_width)
                else:
                    wrapped = self._wrap_text_object(mobj, target_width)
                if wrapped:
                    wrapped_count += 1
            elif isinstance(mobj, MathTex):
                wrapped = self._wrap_math_object(mobj, target_width)
                if wrapped:
                    wrapped_count += 1

        return wrapped_count > 0

    @staticmethod
    def _estimate_char_width(text: str) -> float:
        """估算文本的渲染宽度（Manim 单位）

        使用经验系数：西文字符约 0.25-0.35 单位/字，
        中文字符约 0.55-0.65 单位/字。
        返回值用于与 Manim 坐标系的 width 属性比较。

        Args:
            text: 待估算的纯文本字符串

        Returns:
            估算的渲染宽度（Manim 单位）
        """
        width = 0.0
        for ch in text:
            if "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf":
                # CJK 统一汉字 / 扩展 A 区
                width += 0.6
            elif "\u3000" <= ch <= "\u303f" or "\uff00" <= ch <= "\uffef":
                # CJK 符号和标点 / 全角字母数字
                width += 0.6
            else:
                # ASCII 及其他半角字符
                width += 0.3
        return width

    def _wrap_text_object(self, text_obj: Text, target_width: float) -> bool:
        """对 Text 对象执行换行重建

        通过原始文本字符串 + 目标栏宽，估算每行可容纳的字符数，
        在合适位置（优先逗号/句号等自然断点）截断并重建为多行 Text。

        注意：
        - 此方法会原地修改 text_obj 的内容（通过 replace_submobject 或重建）
        - 如果文本本身已经很短（width < target_width * 0.85），不做处理

        Args:
            text_obj: 待处理的 Text 对象
            target_width: 目标栏宽（Manim 单位）

        Returns:
            是否执行了换行重建
        """
        # 修复 Manim v0.20 兼容性：原 hasattr 检查 'get_plaintext' 方法名，
        # 但 Manim 通过 property 装饰器将其实现为 'plaintext' 属性，hasattr
        # 检查的是方法名（不存在），实际访问 plaintext 才返回字符串，导致
        # 跑渲染时触发 AttributeError。
        # 改用 try/except 模式：优先访问 .plaintext 属性，回退到 str(.text)。
        try:
            original_text = text_obj.plaintext
        except AttributeError:
            original_text = str(text_obj.text)

        # 已经不超宽，无需换行
        if text_obj.width <= target_width * 0.95:
            return False

        # 计算每行大约能容纳多少字符
        char_width_estimate = self._estimate_char_width(original_text)
        if char_width_estimate == 0:
            return False

        chars_per_line = max(
            int(target_width / (char_width_estimate / len(original_text))), 8
        )

        # 按自然断点分行
        lines = self._split_text_by_lines(original_text, chars_per_line)

        if len(lines) <= 1:
            return False  # 无法进一步拆分

        # 重建 Text 对象（多行版本）
        new_text_str = "\n".join(lines)
        try:
            # 尝试保持原对象的样式属性
            original_font_size = getattr(text_obj, "font_size", None)
            original_color = text_obj.color if hasattr(text_obj, "color") else None
            # Manim Text 类的 .color 属性（继承自 SVGMobject）默认渲染为
            # 黑色（#000000），即便构造时传 color=WHITE，父级 .color 仍可能
            # 是 #000000（子级 fill_color 才是 #FFFFFF）。这里必须用子级
            # 的真实 fill_color 作为原始颜色，避免重建后 fill 错误变黑。
            sub_fill_color = None
            if text_obj.submobjects:
                try:
                    sub_fill_color = text_obj.submobjects[0].get_fill_color()
                except Exception:
                    sub_fill_color = None
            if sub_fill_color is not None:
                original_color = sub_fill_color
            # 兼容颜色字符串（如 "#FFFFFF" → WHITE）
            try:
                from manim.utils.color import color_to_hex

                if isinstance(original_color, str) and original_color.startswith("#"):
                    original_color = color_to_hex(original_color)
            except Exception:
                pass

            new_text = Text(
                new_text_str,
                font_size=original_font_size or text_obj.font_size,
                color=original_color,
            )
            # 兜底：再次显式 set_color 一次（部分 Manim 版本构造器 color 会被 SVG 路径覆盖）
            if original_color is not None:
                try:
                    new_text.set_color(original_color)
                except Exception:
                    pass

            # 将原对象替换为新对象的内容
            # 由于 Manim 不支持直接替换内部文本，这里采用变通方式：
            # 缩放新文本以匹配原对象的位置信息，并通过 mobject.become() 同步
            text_obj.become(new_text)
            # become() 在 Text 类上不能可靠传递字符的 fill_color
            # （VMobjectFromSVGPath 类型的子对象的 fill 是 SVG 内嵌属性，
            # become 只复制 points/curves，不复制 fill），换行后必须
            # 强制递归把每个子对象的 fill_color 重新设为原色，避免
            # 字符 fill 从 #FFFFFF 退化为 #000000 导致黑底黑字不可见。
            if original_color is not None:
                try:
                    text_obj.set_color(original_color)
                except Exception:
                    pass

                # 递归强制设置所有子对象的 fill_color（双重保险）
                def _force_fill(mob, color):
                    if hasattr(mob, "set_fill"):
                        try:
                            mob.set_fill(color, opacity=1.0)
                        except Exception:
                            pass
                    if hasattr(mob, "submobjects") and mob.submobjects:
                        for sub in mob.submobjects:
                            _force_fill(sub, color)

                _force_fill(text_obj, original_color)
            return True
        except Exception as e:
            logging.warning(f"[_wrap_text_object] 换行重建失败: {e}")
            return False

    @staticmethod
    def _split_text_by_lines(text: str, chars_per_line: int) -> List[str]:
        """将文本按字符数限制拆分为多行

        优先在自然断点（中文句号、逗号、分号、空格）处换行。
        若一行内无自然断点，则强制在 chars_per_line 处截断。

        Args:
            text: 原始文本
            chars_per_line: 每行最大字符数

        Returns:
            行列表
        """
        lines = []
        remaining = text

        while len(remaining) > chars_per_line:
            # 在当前行的范围内寻找最佳断点
            chunk = remaining[:chars_per_line]
            break_point = -1

            # 优先级从高到低：句号 > 分号 > 逗号 > 空格 > 强制截断
            for delimiter in ["。", "；", "，", ",", ";", ".", " ", "\n"]:
                last_pos = chunk.rfind(delimiter)
                if last_pos != -1:
                    break_point = last_pos + 1  # 保留分隔符
                    break

            if break_point == -1:
                break_point = chars_per_line  # 无自然断点，强制截断

            lines.append(remaining[:break_point].strip())
            remaining = remaining[break_point:].strip()

        if remaining:
            lines.append(remaining)

        return lines

    def _wrap_math_object(self, math_obj: MathTex, target_width: float) -> bool:
        """对 MathTex 对象执行换行重建

        策略 1：优先缩小 font_size（每次 -2，下限 18），
        缩到合适即返回（重建最稳定的方式是缩小 font_size，避免拆词）。
        策略 2：缩小到下限仍超宽 → 按公式原子拆分重建（保留 LaTeX 语法完整性）：
           - 优先用原字符串中已存在的 \\\\（手动换行符）拆分
           - 其次按 = \\pm \\mp \\cdot \\times \\quad \\, 等二元运算符拆分
           - 再次按 + - , 单字符运算符拆分（不拆 \\frac / \\sqrt / ^ / _ 内部）
           - 永不拆单个 LaTeX 字符（如 R_1 永远保持完整）
        策略 3：拆分后用 MathTex(part, font_size=...) 重建每行，VGroup.arrange(DOWN) 堆叠，
        重新测量并 scale 适配 target_width。

        直接按 max_chars 硬切会破坏 LaTeX 公式语法（分数/下标/根号被拆到两行），
        所以必须按公式原子拆分。

        Args:
            math_obj: 待处理的 MathTex 对象
            target_width: 目标栏宽（Manim 单位）

        Returns:
            是否执行了换行/缩放重建
        """
        tex_str = math_obj.get_tex_string()

        # 已经不超宽 → 直接返回
        if math_obj.width <= target_width * 0.95:
            return False

        current_font_size = getattr(math_obj, "font_size", 32)
        original_color = math_obj.color if hasattr(math_obj, "color") else None

        # 策略 1：优先缩小 font_size（每次 -2，下限 18）
        shrunk_math = self._shrink_math_font(
            tex_str, current_font_size, target_width, original_color
        )
        if shrunk_math is not None:
            math_obj.become(shrunk_math)
            return True

        # 策略 2：缩小到下限仍超宽 → 按公式原子拆分重建
        parts = self._split_tex_into_atoms(tex_str, target_width, math_obj)

        if len(parts) <= 1:
            # 实在拆不开，最后回退到整体 scale（不破坏结构但缩小）
            scale_factor = (target_width * 0.95) / max(math_obj.width, 0.01)
            if scale_factor < 1.0:
                new_math = MathTex(tex_str, font_size=current_font_size)
                if original_color is not None:
                    new_math.set_color(original_color)
                new_math.scale(scale_factor, about_point=new_math.get_center())
                math_obj.become(new_math)
                return True
            return False

        try:
            # 用 LaTeX 换行符拼接 → Manim 内部 align 到 VGroup
            new_tex_str = " \\\\\n".join(parts)
            new_math = MathTex(new_tex_str, font_size=current_font_size)
            if original_color is not None:
                new_math.set_color(original_color)
            # 重新测量并 scale 适配 target_width
            if new_math.width > target_width * 0.98:
                scale_factor = (target_width * 0.95) / max(new_math.width, 0.01)
                new_math.scale(scale_factor, about_point=new_math.get_center())
            math_obj.become(new_math)
            return True
        except Exception as e:
            logging.warning(f"[_wrap_math_object] 公式换行重建失败: {e}")
            return False

    @staticmethod
    def _shrink_math_font(
        tex_str: str,
        current_font_size: int,
        target_width: float,
        color,
    ) -> "Optional[MathTex]":
        """缩小 MathTex 字号以适配 target_width

        每次 -2，下限 18。返回 None 表示已无法再缩。

        Args:
            tex_str: 原始 LaTeX 字符串
            current_font_size: 当前字号
            target_width: 目标栏宽（Manim 单位）
            color: 颜色（用于重建后保持样式）

        Returns:
            缩小后 MathTex 对象，或 None（已达下限仍超宽）
        """
        MIN_FONT_SIZE = 18
        FONT_STEP = 2

        # 先创建原始字号的 MathTex 测量实际宽度
        try:
            probe = MathTex(tex_str, font_size=current_font_size)
        except Exception:
            return None

        probe_width = probe.width
        if probe_width <= target_width * 0.95:
            return probe  # 当前字号已足够

        # 从当前字号开始逐步缩小
        font_size = current_font_size
        while font_size > MIN_FONT_SIZE:
            font_size -= FONT_STEP
            try:
                candidate = MathTex(tex_str, font_size=font_size)
                if candidate.width <= target_width * 0.95:
                    if color is not None:
                        candidate.set_color(color)
                    return candidate
            except Exception:
                continue

        # 已到下限仍超宽 → 返回最小字号的版本（交给下一步拆分处理）
        try:
            min_math = MathTex(tex_str, font_size=MIN_FONT_SIZE)
            if color is not None:
                min_math.set_color(color)
            return min_math
        except Exception:
            return None

    def _split_tex_into_atoms(
        self,
        tex_str: str,
        target_width: float,
        math_obj: MathTex,
    ) -> List[str]:
        """按 LaTeX 公式原子拆分为多行

        拆分规则（按优先级，**永不破坏语法结构**）：
        1. 已有 \\\\ 手动换行符 → 直接按 \\\\ 拆
        2. 按 = / \\pm / \\mp / \\cdot / \\times / \\quad / \\, / \\; / \\! 拆分
        3. 按 + / - / , 拆分（不拆 \\frac 分子分母、不拆 ^ / _ 下标）
        4. 拆不开时返回单元素列表

        使用 re.split 按 LaTeX 运算符/分隔符拆，
        保留捕获组（括号），拆出的分隔符也作为独立 token 保留。
        优先级：\\quad / \\, / \\; / \\!  →  + - = ,  →  \\\\
        注意：\frac / \sqrt / ^ / _ 必须保持完整

        Args:
            tex_str: 原始 LaTeX 字符串
            target_width: 目标栏宽
            math_obj: 原 MathTex（用于辅助测量单段宽度）

        Returns:
            公式段列表（每段都是完整 LaTeX 子表达式，可独立被 MathTex 解析）
        """
        # 规则 1：已含手动换行符 → 直接按 \\ 拆
        if "\\\\" in tex_str:
            return [p.strip() for p in tex_str.split("\\\\") if p.strip()]

        split_pattern = (
            r"(\\quad|\\,|\\;|\\!|\\ |"
            r"\\pm|\\mp|\\cdot|\\times|\\div|\\cdot|\\leq|\\geq|\\neq|\\approx|\\equiv|"
            r"\\to|\\rightarrow|\\leftarrow|\\Rightarrow|\\Leftarrow|"
            r"[+\-=,:;])"
        )
        tokens = re.split(split_pattern, tex_str)

        # 去除空 token
        tokens = [t.strip() for t in tokens if t and t.strip()]

        # 合并连续的运算符到前一个 token（避免孤立 `+` 行）
        merged: List[str] = []
        buffer = ""
        for tok in tokens:
            if tok in (
                "+",
                "-",
                "=",
                ",",
                ":",
                ";",
                "\\,",
                "\\;",
                "\\!",
                "\\ ",
                "\\quad",
                "\\pm",
                "\\mp",
                "\\cdot",
                "\\times",
                "\\div",
                "\\leq",
                "\\geq",
                "\\neq",
                "\\approx",
                "\\equiv",
                "\\to",
                "\\rightarrow",
                "\\leftarrow",
                "\\Rightarrow",
                "\\Leftarrow",
            ):
                # 运算符：附加到前一个 token（保持语法完整）
                buffer = (buffer + " " + tok).strip() if buffer else tok
            else:
                if buffer:
                    merged.append(buffer)
                    buffer = ""
                merged.append(tok)
        if buffer:
            merged.append(buffer)

        if len(merged) <= 1:
            return [tex_str]  # 实在拆不开

        # 验证拆分后行数：尝试测量每段是否在目标宽度内
        # 至少要有 > 1 段，且合并后总宽度 < 拆分前（否则无意义）
        return merged

    @staticmethod
    def _split_tex_by_breakpoints(tex: str, max_chars: int) -> List[str]:
        """将 LaTeX 公式字符串按断点拆分

        优先在以下位置断开（按优先级排序）：
        1. 已有的 \\\\（手动换行）
        2. = （等号）
        3. \\pm / \\mp / \\cdot / \\times （运算符前后）
        4. + / - （加减号，排除指数中的 +-）
        5. , （逗号）

        Args:
            tex: LaTeX 公式字符串
            max_chars: 每段最大字符数

        Returns:
            公式段列表
        """
        # 先按已有换行分割
        if "\\\\" in tex:
            initial_parts = [p.strip() for p in tex.split("\\\\")]
        else:
            initial_parts = [tex]

        result = []
        for part in initial_parts:
            while len(part) > max_chars:
                chunk = part[:max_chars]
                bp = -1

                # 按优先级寻找断点
                for pattern in [
                    "=",
                    r"\pm",
                    r"\mp",
                    r"\cdot",
                    r"\times",
                    "+",
                    "-",
                    ",",
                ]:
                    # 向右搜索最后一个匹配位置（避免在最开头断开）
                    search_start = max(len(chunk) // 2, 1)
                    pos = chunk.rfind(pattern, search_start)
                    if pos != -1:
                        bp = pos + len(pattern)
                        break

                if bp == -1 or bp < len(chunk) // 3:
                    bp = max_chars  # 强制截断

                result.append(part[:bp].strip())
                part = part[bp:].strip()

            if part:
                result.append(part)

        return result

    def _apply_split(
        self,
        violation: Dict[str, Any],
        mobjects: List[Mobject],
    ) -> bool:
        """触发原子拆分回调（不实际执行拆分）

        拆分动作由外部（JSON 设计阶段 / 工程师）完成，本方法只通知。
        因此**永远返回 False**：违规未在本次 optimize 调用内消除，
        优化循环应停止并把违规抛给上层（人工干预 / 拆分原子）。

        Args:
            violation: 违规信息
            mobjects: Mobject 列表

        Returns:
            恒为 False。回调是否设置不影响此返回值，避免优化循环误判成功。
        """
        if self._on_split:
            self._on_split(
                violation_type=violation.get("type", "unknown"),
                mobjects=mobjects,
                suggested_id=violation.get("object_name", "atom"),
            )
        return False

    def _verify_no_violation(
        self,
        mobjects: List[Mobject],
        original_violations: List[Dict[str, Any]],
    ) -> bool:
        """验证调整后是否消除违规

        重新测量内容尺寸，判断是否仍在允许范围内。

        按违规类型分类处理：
        - 测量类（WIDTH/HEIGHT_OVERFLOW）：使用 measure_content_dims 验证
        - 区域/重叠/越界类：返回 False（需调用方用 validate_layout 重测）
        - 密度/间距/重心类：返回 False（同上）
        - 未知类型：返回 False（保守策略，避免误判通过）

        Args:
            mobjects: 调整后的 Mobject 列表
            original_violations: 原始违规列表（用于判断类型）

        Returns:
            是否无违规
        """
        if not original_violations:
            return True

        # 可在优化器内通过测量验证的违规类型
        MEASURABLE_TYPES = {"WIDTH_OVERFLOW", "HEIGHT_OVERFLOW"}
        # 需调用方用 validate_layout 重新校验的类型（优化器内无法可靠验证）
        REVALIDATE_TYPES = {
            "REGION_OVERFLOW",
            "REGION_INTRUSION",
            "ELEMENT_OVERLAP",
            "SCREEN_OUT_OF_BOUNDS",
            "STACK_OVERFLOW",
            "WIDTH_EXCEEDS_COLUMN",
            "ABNORMAL_SPACING",
            "OVER_DENSE",
            "TOO_SPARSE",
            "CENTER_OFFSET",
        }

        # 收集所有类型；任何未知类型保守返回 False
        all_types = {v.get("type", "") for v in original_violations}
        unknown_types = all_types - MEASURABLE_TYPES - REVALIDATE_TYPES
        if unknown_types:
            logging.debug(
                f"[_verify_no_violation] 未知违规类型 {unknown_types}，"
                "保守返回 False"
            )
            return False

        # 含可重测类型时返回 False，由调用方走 validate_layout 重测
        if all_types & REVALIDATE_TYPES:
            return False

        # 仅含测量类违规时，进行尺寸校验
        total_width, total_height = LayoutEngine.measure_content_dims(mobjects)
        for v in original_violations:
            vtype = v.get("type", "")
            if vtype == "WIDTH_OVERFLOW":
                if total_width > ZoneConstants.HORIZONTAL_OVERFLOW_THRESHOLD:
                    return False
            elif vtype == "HEIGHT_OVERFLOW":
                if total_height > ZoneConstants.VERTICAL_OVERFLOW_THRESHOLD:
                    return False

        return True

    def _format_adjustments(self) -> str:
        """格式化调整日志

        Returns:
            人类可读的日志字符串
        """
        lines = []
        for adj in self._adjustments:
            lines.append(
                f"第{adj['round']}轮：策略={adj['strategy']}, "
                f"类型={adj['violation_type']}, "
                f"{'成功' if adj['success'] else '失败'}"
            )
        return "\n".join(lines)

    @staticmethod
    def measure_content_dims(mobjs: list) -> Tuple[float, float]:
        """测量内容尺寸（委托给 LayoutEngine）"""
        return LayoutEngine.measure_content_dims(mobjs)


# ============================================================
# minipage 路径（complementary to _wrap_text_object）
# ============================================================


def _compute_em_width(manim_width: float, font_size: int) -> float:
    """将 Manim 坐标宽度换算为 LaTeX em 数量

    通过渲染 \\rule{1em}{0.5em} 实测 1em 在 Manim 坐标系中的实际宽度。
    探测结果与 font_size 强相关，缓存复用。

    Args:
        manim_width: 目标 Manim 坐标宽度
        font_size: Tex 字号（pt）

    Returns:
        em 数量（float），如 22.5 表示 minipage 应设 22.5em
    """
    cache_key = (round(manim_width, 3), int(font_size))
    if cache_key in _EM_WIDTH_CACHE:
        return _EM_WIDTH_CACHE[cache_key]

    em_in_manim = _probe_em_in_manim(font_size)
    em_count = manim_width / em_in_manim
    # 留 2% 余量，避免 LaTeX 测量与 Manim 测量有微差
    em_count *= 0.98
    _EM_WIDTH_CACHE[cache_key] = em_count
    return em_count


def _probe_em_in_manim(font_size: int) -> float:
    """探测 1em 在 Manim 坐标系中的实际宽度

    返回值与 font_size 强相关（font_size 决定 \\rule 的渲染尺寸）。
    探测失败时（LaTeX 引擎缺失、模板编译失败等）回退到经验值
    font_size / 50，但**不写入成功缓存**，下次调用会重新探测。
    """
    try:
        from manim import Tex as _TexProbe

        probe = _TexProbe(r"\rule{1em}{0.5em}", font_size=font_size)
        em_in_manim = probe.width
        if em_in_manim <= 0:
            raise ValueError("probe width non-positive")
        return em_in_manim
    except Exception:
        # 经验回退：em 宽度 ≈ font_size / 50 Manim 单位
        # 依据：10pt 下 1em≈0.139 英寸，Manim 1 单位≈1 英寸时的常见比例
        # 不写入 _EM_WIDTH_CACHE，让下次调用有机会重新探测（环境恢复后）
        return max(font_size / 50.0, 0.05)


# LaTeX 特殊字符转义表（仅处理 minipage 文本需要转义的）
_LATEX_SPECIAL_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "^": r"\textasciicircum{}",
    "~": r"\textasciitilde{}",
}


def _escape_text_for_latex(text: str) -> str:
    """转义 LaTeX 特殊字符

    Args:
        text: 原始中文文本（通常无特殊字符，但用户输入可能含）

    Returns:
        转义后的 LaTeX 安全字符串
    """
    result = []
    for ch in text:
        if ch in _LATEX_SPECIAL_ESCAPES:
            result.append(_LATEX_SPECIAL_ESCAPES[ch])
        else:
            result.append(ch)
    return "".join(result)


def _wrap_text_with_minipage(
    text_obj: Text,
    target_manim_width: float,
) -> bool:
    """minipage 路径换行（complementary to _wrap_text_object）

    与 _wrap_text_object 的对比：
    - _wrap_text_object：按字符数估算断行，重建为多行 Text（Pango 渲染）
    - _wrap_text_with_minipage：构建 minipage 交给 LaTeX 处理断行（xelatex 渲染）
    - 优先用 _wrap_text_object（快、无 TeX 编译开销）
    - 仅当 LayoutScene.is_minipage_available() == True 时使用本函数

    工作流程：
    1. 实测目标 Manim 宽度对应的 em 数（探针缓存）
    2. 构建 LaTeX：\\begin{minipage}[t]{Xem}\\raggedright <text>\\end{minipage}
    3. 渲染为 Tex 对象（使用 xelatex + xeCJK 模板）
    4. 颜色保持（同 _wrap_text_object 的 _force_fill 兜底）
    5. text_obj.become(new_tex)

    Args:
        text_obj: 待处理的 Text 对象
        target_manim_width: 目标 Manim 坐标宽度（如 ZoneConstants 计算出的栏宽）

    Returns:
        是否成功执行换行重建
    """
    try:
        original_text = text_obj.plaintext
    except AttributeError:
        original_text = str(text_obj.text)

    if not original_text:
        return False
    if text_obj.width <= target_manim_width * 0.95:
        return False

    font_size = getattr(text_obj, "font_size", 30)

    # 解析原 color（子对象优先，避免父级 .color 退化为 #000000）
    original_color = text_obj.color if hasattr(text_obj, "color") else None
    if text_obj.submobjects:
        try:
            sub_fill = text_obj.submobjects[0].get_fill_color()
            if sub_fill is not None:
                original_color = sub_fill
        except Exception:
            pass

    # 步骤 1: 算 em 宽度
    em_w = _compute_em_width(target_manim_width * 0.95, font_size)

    # 步骤 2: 转义 + 构建 LaTeX
    safe_text = _escape_text_for_latex(original_text)
    latex_src = (
        rf"\begin{{minipage}}[t]{{{em_w:.3f}em}}"
        rf"\raggedright "
        rf"{safe_text}"
        rf"\end{{minipage}}"
    )

    # 步骤 3: 渲染
    try:
        new_text = Tex(
            latex_src,
            font_size=font_size,
            color=original_color,
            tex_template=_get_xelatex_template(),
        )
    except Exception as e:
        logging.warning(f"[_wrap_text_with_minipage] xelatex 渲染失败: {e}")
        return False

    # 步骤 3.5: 一致性检查（渲染后 font_size 必须 ≥ 原值）
    # 渲染后 Tex 的 font_size 必须 ≥ 原值（不允许被 _get_xelatex_template 缩放）
    actual_font_size = getattr(new_text, "font_size", font_size)
    if actual_font_size < font_size * 0.99:
        logging.warning(
            f"[_wrap_text_with_minipage] 渲染后字号 {actual_font_size} "
            f"< 期望 {font_size}，疑似模板缩放"
        )
        return False  # 回退到 Pango 路径

    # 步骤 4: 颜色兜底
    if original_color is not None:
        try:
            new_text.set_color(original_color)
        except Exception:
            pass

        def _force_fill(mob, color):
            if hasattr(mob, "set_fill"):
                try:
                    mob.set_fill(color, opacity=1.0)
                except Exception:
                    pass
            if hasattr(mob, "submobjects") and mob.submobjects:
                for sub in mob.submobjects:
                    _force_fill(sub, color)

        _force_fill(new_text, original_color)

    # 步骤 5: 替换
    text_obj.become(new_text)
    return True
