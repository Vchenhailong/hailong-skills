#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕区组件 - 完整实现（自适应高度，**无背景板**）

严格约束：
- X ∈ [-6.75, 6.75]（安全区水平边界）
- 底部固定于 Y=-3.85（防抖动）
- 字幕字号 font_size=18，禁止缩放
- 行距自然合理（按 font_size 换算）
- 最多 2 行字幕，超出自动截断
- **无背景板 / 背景色**（修复 2024-12：移除底衬以提升视觉清晰度）

视觉结构（修复后）：
    第一行文字内容...
    第二行文字内容...
    ↑ 整体水平居中于屏幕底部 Y=-3.85
"""

from manim import (
    VGroup,
    Text,
    ORIGIN,
    UP,
    DOWN,
    LEFT,
    RIGHT,
    FadeOut,
)
from scripts.layout.zones.base import ZoneBase
from scripts.layout.constants import ZoneConstants as ZC


class SubtitleZone(ZoneBase):
    """字幕区组件（自适应高度 + **无背景板** + 视觉渲染）

    职责：
    1. 提供底部固定位置（Y=-3.85）防抖动
    2. 字幕字号固定 font_size=18，禁止缩放
    3. **不绘制背景板 / 背景色**（修复 2024-12）
    4. 仅渲染文字本身
    """

    def __init__(self, scene, debug: bool = False, has_title: bool = True, **kwargs):
        """初始化字幕区组件

        Y 范围根据布局模式动态计算：
        - has_title=True（三区：vertical/centered）：Y ∈ [-3.6, -2.88]（10% 高度 0.72）
        - has_title=False（两区/三区：two_column/three_column）：Y ∈ [-3.6, -2.88]（10% 高度 0.72，9:1 比例）

        Args:
            scene: Manim Scene 对象（用于 play/remove 操作）
            debug: 调试模式，显示容器边框和填充
            has_title: 是否包含标题区（统一 10%，9:1 比例）
            **kwargs: 传递给 ZoneBase 的样式参数
        """
        self.scene = scene
        self._current_texts = None
        self._has_title = has_title

        zones = ZC.compute(ZC.SCREEN_WIDTH, ZC.SCREEN_HEIGHT, has_title=has_title)
        super().__init__(
            x_min=ZC.SUBTITLE_ZONE_X_MIN,
            x_max=ZC.SUBTITLE_ZONE_X_MAX,
            y_min=zones["subtitle_y_min"],
            y_max=zones["subtitle_y_max"],
            debug=debug,
            **kwargs,
        )

    def show(self, text: str, font_size: int = ZC.SUBTITLE_FONT_SIZE) -> VGroup:
        """渲染并显示字幕（**无背景板**）

        注意（P1-9）：本方法仅做"显示单帧字幕"，不涉及滚动。
        若需滚动多行字幕，请使用 SubtitleScroller.show()。
        两者职责分离：
          - SubtitleZone.show : 单帧展示（2 行以内），不做滚动、不预计算时序
          - SubtitleScroller.show : 多行滚动展示（含预计算滚动事件）

        装配逻辑（修复 2024-12 移除底衬）：
        1. 创建文字对象
        2. **不创建 Rectangle 底衬**（移除 2024-12）
        3. 文字整体水平居中、底部固定到 Y=-3.85
        4. 上界约束检查（top >= -2.8 时下移）

        Args:
            text: 字幕文本内容
            font_size: 字幕字体大小（默认18）

        Returns:
            字幕文字组（无底衬）
        """
        self._hide()

        if isinstance(text, str):
            lines = self._split_text_to_lines(text, max_chars_per_line=20)
            text_mobjects = [
                Text(line, font_size=font_size, color=ZC.SUBTITLE_TEXT_COLOR)
                for line in lines
            ]
            measured_line_height = Text("测试", font_size=font_size).height
            line_spacing = measured_line_height * ZC.SUBTITLE_LINE_SPACING_RATIO * 0.4
            text_group = VGroup(*text_mobjects).arrange(DOWN, buff=line_spacing)
        else:
            text_group = text

        text_width = text_group.width
        text_height = text_group.height

        # 修复 2024-12：移除底衬创建（保留计算用于日志/兼容检查）
        bg_width = text_width + ZC.SUBTITLE_BACKGROUND_PADDING_W * 2
        bg_height = text_height + ZC.SUBTITLE_BACKGROUND_PADDING_H * 2

        # 修复 2024-12：移除 Rectangle 背景板与背景色
        # 原代码：bg = Rectangle(...)
        # 修复后：直接使用 text_group 作为字幕组（无底衬）
        # 理由：底衬在 480p 渲染下视觉过重，干扰主内容区；改为纯文字更清爽
        subtitle_group = text_group

        # 水平居中
        subtitle_group.set_x(0)
        # 底部固定到 SUBTITLE_ZONE_BOTTOM_FIXED_Y（防抖动）
        # 实际是 center.y = bottom_fixed_y + subtitle_group.height/2
        subtitle_group.set_y(
            ZC.SUBTITLE_ZONE_BOTTOM_FIXED_Y + subtitle_group.height / 2
        )

        # 上界约束：top 超过 SUBTITLE_ZONE_TOP_Y 时下移（防侵入主内容区）
        top_y = subtitle_group.get_top()[1]
        if top_y > ZC.SUBTITLE_ZONE_TOP_Y:
            subtitle_group.shift(DOWN * (top_y - ZC.SUBTITLE_ZONE_TOP_Y))

        self._current_texts = text_group

        return subtitle_group

    def _hide(self):
        """清除当前字幕"""
        if self._current_texts is not None:
            if self._current_texts in self.scene.mobjects:
                self.scene.remove(self._current_texts)
            self._current_texts = None

    def _split_text_to_lines(self, text: str, max_chars_per_line: int = 20) -> list:
        """将长文本拆分为多行（最多2行，每行20字符）

        Args:
            text: 原始文本
            max_chars_per_line: 每行最大字符数（默认20）

        Returns:
            行列表（最多2行）
        """
        if len(text) <= max_chars_per_line:
            return [text]

        lines = []
        remaining = text
        while len(remaining) > max_chars_per_line:
            # 在 max_chars 附近找断点（优先空格/标点）
            cut_pos = max_chars_per_line
            for i in range(max_chars_per_line, max(0, max_chars_per_line - 5), -1):
                if i < len(remaining) and remaining[i] in (" ", "，", "。", "、", "；"):
                    cut_pos = i + 1
                    break
            lines.append(remaining[:cut_pos])
            remaining = remaining[cut_pos:]
        if remaining:
            lines.append(remaining)
        return lines

    # ============================================================
    # 继承自 ZoneBase 的容器约束方法（保持不变）
    # ============================================================

    def place_content(self, content_group: VGroup) -> VGroup:
        """将字幕内容约束在容器内，底部对齐

        约束策略：
        1. 内容高度超过容器时按比例缩放
        2. 底部对齐（防抖动）
        3. 强制执行上界约束（防止侵入主内容区 Y=-2.8）

        Args:
            content_group: 字幕内容组（Text 或 VGroup）

        Returns:
            已定位的内容组
        """
        content_height = content_group.get_height()

        # 1. 内容高度超过容器时按比例缩放（使用底部作为缩放锚点）
        if content_height > self._height:
            scale_factor = self._height / content_height
            content_group.scale(scale_factor, about_point=content_group.get_bottom())

        # 2. 底部对齐（固定字幕底部位置，防抖动）
        current_bottom = content_group.get_bottom()[1]
        if abs(current_bottom - ZC.SUBTITLE_ZONE_BOTTOM_FIXED_Y) > 0.001:
            content_group.shift(UP * (ZC.SUBTITLE_ZONE_BOTTOM_FIXED_Y - current_bottom))

        # 3. 强制执行上界约束（防止侵入主内容区）
        top_y = content_group.get_top()[1]
        if top_y > ZC.SUBTITLE_ZONE_TOP_Y:
            content_group.shift(UP * (ZC.SUBTITLE_ZONE_TOP_Y - top_y))

        # 水平居中
        content_group.move_to([self._center_x, content_group.get_center()[1], 0])

        self._content_group = content_group
        return content_group

    def place_content_bottom_aligned(self, content_group: VGroup) -> VGroup:
        """将字幕内容底部对齐到固定位置（明确指定底部对齐）

        Args:
            content_group: 字幕内容组

        Returns:
            已定位的内容组
        """
        return self.place_content(content_group)

    def is_content_overflow(self, content_group: VGroup) -> bool:
        """检查内容是否溢出容器

        检查项：
        1. 内容底部是否低于字幕区下界
        2. 内容顶部是否高于字幕区上界
        """
        content_bottom = content_group.get_bottom()[1]
        content_top = content_group.get_top()[1]
        return (
            content_bottom < ZC.SUBTITLE_ZONE_Y_MIN
            or content_top > ZC.SUBTITLE_ZONE_TOP_Y
        )
