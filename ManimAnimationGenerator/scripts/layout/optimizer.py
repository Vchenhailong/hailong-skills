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

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from manim import Mobject, VGroup, Text, MathTex


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
        round_count = 0
        max_rounds = 3  # 最多 3 轮

        for violation in violations:
            while round_count < max_rounds:
                round_count += 1
                strategy = self._select_strategy(violation, current_mobjects)

                if strategy == self.STRATEGY_SCALE:
                    success = self._apply_scale(current_mobjects, violation)
                elif strategy == self.STRATEGY_WRAP:
                    success = self._apply_wrap(current_mobjects, violation)
                else:  # STRATEGY_SPLIT
                    success = self._apply_split(violation, current_mobjects)

                if success:
                    # 记录调整日志
                    self._adjustments.append({
                        "round": round_count,
                        "strategy": strategy,
                        "violation_type": violation["type"],
                        "success": True,
                    })

                    # 重新测量并验证
                    if self._verify_no_violation(current_mobjects, violations):
                        return OptimizationResult(
                            success=True,
                            rounds_executed=round_count,
                            adjustments=self._adjustments,
                        )
                else:
                    # 当前策略失败，尝试下一个策略
                    self._adjustments.append({
                        "round": round_count,
                        "strategy": strategy,
                        "violation_type": violation["type"],
                        "success": False,
                    })

        # 所有轮次执行完毕仍失败
        return OptimizationResult(
            success=False,
            rounds_executed=round_count,
            adjustments=self._adjustments,
            error_message=(
                f"经过 {round_count} 轮自动优化仍无法解决布局问题。\n"
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
            for m in mobjects if hasattr(m, "get_tex_string")
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
        - Text 对象：按中文字符宽度估算，在合适位置插入换行符后重建
        - MathTex 对象：对长公式字符串按字符数阈值拆分，用 \\\\ 插入换行
        - 非文本类 Mobject：跳过（缩放或拆分处理）

        Args:
            mobjects: Mobject 列表
            violation: 违规信息（含 column_width 等布局上下文）

        Returns:
            是否成功应用了至少一次换行
        """
        from manim import MathTex, Text

        # 从 violation 或 column_layout 中获取目标栏宽（单位：Manim 坐标）
        target_width = violation.get("column_width", None)
        if target_width is None:
            # 回退：使用违规对象的实际超宽比例估算目标宽度
            target_width = ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MAX - ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MIN

        wrapped_count = 0
        for i, mobj in enumerate(mobjects):
            if isinstance(mobj, Text):
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
            if '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf':
                # CJK 统一汉字 / 扩展 A 区
                width += 0.6
            elif '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
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
        original_text = text_obj.get_plaintext() if hasattr(text_obj, 'get_plaintext') else str(text_obj.text)

        # 已经不超宽，无需换行
        if text_obj.width <= target_width * 0.95:
            return False

        # 计算每行大约能容纳多少字符
        char_width_estimate = self._estimate_char_width(original_text)
        if char_width_estimate == 0:
            return False

        chars_per_line = max(int(target_width / (char_width_estimate / len(original_text))), 8)

        # 按自然断点分行
        lines = self._split_text_by_lines(original_text, chars_per_line)

        if len(lines) <= 1:
            return False  # 无法进一步拆分

        # 重建 Text 对象（多行版本）
        new_text_str = "\n".join(lines)
        try:
            # 尝试保持原对象的样式属性
            original_font_size = getattr(text_obj, 'font_size', None)
            original_color = text_obj.color if hasattr(text_obj, 'color') else None

            new_text = Text(new_text_str, font_size=original_font_size or text_obj.font_size)
            if original_color is not None:
                new_text.set_color(original_color)

            # 将原对象替换为新对象的内容
            # 由于 Manim 不支持直接替换内部文本，这里采用变通方式：
            # 缩放新文本以匹配原对象的位置信息，并通过 mobject.become() 同步
            text_obj.become(new_text)
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
            for delimiter in ['。', '；', '，', ',', ';', '.', ' ', '\n']:
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

        对长公式按字符数阈值拆分，在合适运算符处插入 \\\\
        （LaTeX 换行符），然后重建 MathTex 对象。

        Args:
            math_obj: 待处理的 MathTex 对象
            target_width: 目标栏宽（Manim 单位）

        Returns:
            是否执行了换行重建
        """
        tex_str = math_obj.get_tex_string()

        # 已经不超宽
        if math_obj.width <= target_width * 0.95:
            return False

        # 长公式阈值（字符数）
        long_threshold = 50

        if len(tex_str) <= long_threshold:
            return False

        # 寻找合适的换行断点（优先在 =、+、-、\\times 等二元运算符之后）
        parts = self._split_tex_by_breakpoints(tex_str, long_threshold)

        if len(parts) <= 1:
            return False

        # 用 LaTeX 换行符拼接
        new_tex_str = " \\\\\n".join(parts)

        try:
            new_math = MathTex(new_tex_str, font_size=math_obj.font_size)
            if hasattr(math_obj, 'color'):
                new_math.set_color(math_obj.color)
            math_obj.become(new_math)
            return True
        except Exception as e:
            logging.warning(f"[_wrap_math_object] 公式换行重建失败: {e}")
            return False

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
        if '\\\\' in tex:
            initial_parts = [p.strip() for p in tex.split('\\\\')]
        else:
            initial_parts = [tex]

        result = []
        for part in initial_parts:
            while len(part) > max_chars:
                chunk = part[:max_chars]
                bp = -1

                # 按优先级寻找断点
                for pattern in ['=', r'\pm', r'\mp', r'\cdot', r'\times', '+', '-', ',']:
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
        """应用拆分策略（调用外部回调）

        当字号缩小和换行均无效时，触发原子拆分回调。

        Args:
            violation: 违规信息
            mobjects: Mobject 列表

        Returns:
            是否成功触发回调
        """
        if self._on_split:
            self._on_split(
                violation_type=violation.get("type", "unknown"),
                mobjects=mobjects,
                suggested_id=violation.get("object_name", "atom"),
            )
            return True
        return False

    def _verify_no_violation(
        self,
        mobjects: List[Mobject],
        original_violations: List[Dict[str, Any]],
    ) -> bool:
        """验证调整后是否消除违规

        重新测量内容尺寸，判断是否仍在允许范围内。

        Args:
            mobjects: 调整后的 Mobject 列表
            original_violations: 原始违规列表（用于判断类型）

        Returns:
            是否无违规
        """
        total_width, total_height = LayoutEngine.measure_content_dims(mobjects)

        for v in original_violations:
            if v["type"] == "WIDTH_OVERFLOW":
                if total_width > ZoneConstants.HORIZONTAL_OVERFLOW_THRESHOLD:
                    return False
            elif v["type"] == "HEIGHT_OVERFLOW":
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
        from scripts.layout.engine import LayoutEngine
        return LayoutEngine.measure_content_dims(mobjs)


# 导入依赖（避免循环导入）
from scripts.layout.engine import LayoutEngine
from scripts.layout.constants import ZoneConstants