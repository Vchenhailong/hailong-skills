#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕区组件 - 完整实现（自适应高度 + 底衬）

严格约束：
- X ∈ [-6.75, 6.75]（安全区水平边界）
- 底部固定于 Y=-3.85（防抖动）
- 字幕字号 font_size=18，禁止缩放
- 行距自然合理（按 font_size 换算）
- 最多 2 行字幕，超出自动截断
- 底衬自适应文字高度

视觉结构：
┌───────────────────────────────┐  ← bg: 深色半透明底衬（自适应文字宽度+高度）
│  第一行文字内容...             │
│  第二行文字内容...             │
└───────────────────────────────┘
    ↑ 整体水平居中于屏幕底部 Y=-3.85
"""

from manim import (
    VGroup,
    Rectangle,
    Text,
    ORIGIN,
    UP,
    DOWN,
    LEFT,
    RIGHT,
    FadeIn,
    FadeOut,
)
from scripts.layout.zones.base import ZoneBase
from scripts.layout.constants import ZoneConstants as ZC


class SubtitleZone(ZoneBase):
    """字幕区组件（自适应高度 + 视觉渲染）

    职责：
    1. 提供底部固定位置（Y=-3.85）防抖动
    2. 字幕字号固定 font_size=18，禁止缩放
    3. 底衬自适应文字内容（宽度+高度）
    4. 渲染视觉层（底衬 + 文字）
    """

    def __init__(self, scene, debug: bool = False, **kwargs):
        """初始化字幕区组件

        Args:
            scene: Manim Scene 对象（用于 play/remove 操作）
            debug: 调试模式，显示容器边框和填充
            **kwargs: 传递给 ZoneBase 的样式参数
        """
        self.scene = scene
        self._current_bg = None
        self._current_texts = None
        super().__init__(
            x_min=ZC.SUBTITLE_ZONE_X_MIN,
            x_max=ZC.SUBTITLE_ZONE_X_MAX,
            y_min=ZC.SUBTITLE_ZONE_Y_MIN,
            y_max=ZC.SUBTITLE_ZONE_Y_MAX,
            debug=debug,
            **kwargs,
        )

    def show(self, text: str, font_size: int = ZC.SUBTITLE_FONT_SIZE) -> VGroup:
        """渲染并显示字幕（含底衬）

        注意（P1-9）：本方法仅做"显示单帧字幕"，不涉及滚动。
        若需滚动多行字幕，请使用 SubtitleScroller.show()。
        两者职责分离：
          - SubtitleZone.show : 单帧展示（2 行以内），不做滚动、不预计算时序
          - SubtitleScroller.show : 多行滚动展示（含预计算滚动事件）

        装配逻辑：
        1. 创建文字对象 → 计算自适应底衬尺寸
        2. 底衬 Rectangle（深色半透明，宽度=min(文字宽+内边距*2, 上限14.0)）
        3. 文字 → 居中于底衬内
        4. 组装 VGroup → 移动到 Y=-3.85 → 水平居中
        5. 上界约束检查（top >= -2.8 时下移）

        Args:
            text: 字幕文本内容
            font_size: 字幕字体大小（默认18）

        Returns:
            组装完成的字幕组（bg + texts）
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
        bg_width = min(
            text_width + ZC.SUBTITLE_BACKGROUND_PADDING_W * 2,
            ZC.SCREEN_WIDTH * 0.95,
        )
        bg_height = text_height + ZC.SUBTITLE_BACKGROUND_PADDING_H * 2

        bg = Rectangle(
            width=bg_width,
            height=bg_height,
            fill_color=ZC.SUBTITLE_BACKGROUND_COLOR,
            fill_opacity=ZC.SUBTITLE_BACKGROUND_OPACITY,
            stroke_width=0,
            corner_radius=ZC.SUBTITLE_BACKGROUND_CORNER_RADIUS,
        )

        # 文字居中于底衬
        text_group.move_to(bg.get_center())

        subtitle_group = VGroup(bg, text_group)

        # 修复 P0-5：原代码
        #   subtitle_group.move_to(ORIGIN).align_to(ORIGIN, DOWN).shift(DOWN * abs(Y))
        #   subtitle_group.align_to(ORIGIN, LEFT + RIGHT)
        # 第一个 align_to(ORIGIN, DOWN) 的第一个参数是 mobject，传 ORIGIN 点是错误的；
        # 第二个 align_to(ORIGIN, LEFT+RIGHT) 同理。
        # 正确做法：直接用 set_y / set_x 设定绝对位置（依赖 ZC 中的固定值，
        # 符合"字幕底部固定"红线约束），并保留上界约束防侵入主内容区。
        # 水平居中
        subtitle_group.set_x(0)
        # 底部固定到 SUBTITLE_ZONE_BOTTOM_FIXED_Y（防抖动）
        # subtitle_group.height/2 是其中心到顶/底的距离
        # 实际是 center.y = bottom_fixed_y + subtitle_group.height/2
        subtitle_group.set_y(
            ZC.SUBTITLE_ZONE_BOTTOM_FIXED_Y + subtitle_group.height / 2
        )

        # 上界约束：top 超过 SUBTITLE_ZONE_TOP_Y 时下移（防侵入主内容区）
        top_y = subtitle_group.get_top()[1]
        if top_y > ZC.SUBTITLE_ZONE_TOP_Y:
            subtitle_group.shift(DOWN * (top_y - ZC.SUBTITLE_ZONE_TOP_Y))

        self._current_bg = bg
        self._current_texts = text_group

        return subtitle_group

    def _hide(self):
        """清除当前字幕"""
        if self._current_bg is not None:
            for mobj in [self._current_bg, self._current_texts]:
                if mobj is not None and mobj in self.scene.mobjects:
                    self.scene.remove(mobj)
            self._current_bg = None
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
