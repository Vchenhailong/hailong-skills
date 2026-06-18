#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形区容器 - 固定宽度，溢出优先缩放

严格遵循 references/layout.md：
- 两栏模式：X ∈ [1.85, 6.75]，Y ∈ [-2.5, 3.11]
- 第 4.5 节：右侧图形区溢出时优先缩放，而非拆分
- layout.md 第 7.1 节：坐标轴标签不得进入字幕区

默认缩放规则（physics.md / layout.md）：
- 图形大小固定为图形区的 80%（即 scale_factor = 0.80）
- 这一规则确保图形不会过度占据空间，保持与文本的视觉平衡
"""

from manim import VGroup, LEFT, RIGHT, UP, DOWN
from scripts.layout.zones.base import ZoneBase
from scripts.layout.constants import ZoneConstants


class GraphicsZone(ZoneBase):
    """图形区容器

    职责：
    1. 提供固定宽高的图形区域边界
    2. 溢出时优先缩放（layout.md 第 4.5 节）
    3. 防止图形底部进入字幕区（layout.md 第 7.1 节第 5 条）
    """

    def __init__(self, debug: bool = False, **kwargs):
        """初始化图形区容器

        两栏布局（has_title=False）下：
        - 图形区与主内容区共享 Y 边界 [-2.88, 3.6]（90% × safe_h = 6.48，9:1 比例）
        - 与 ZoneConstants.compute(has_title=False) 保持一致

        Args:
            debug: 调试模式，显示容器边框和填充
            **kwargs: 传递给 ZoneBase 的样式参数
        """
        zones = ZoneConstants.compute(
            ZoneConstants.SCREEN_WIDTH,
            ZoneConstants.SCREEN_HEIGHT,
            has_title=False,
        )
        super().__init__(
            x_min=ZoneConstants.GRAPHICS_X_MIN,
            x_max=ZoneConstants.GRAPHICS_X_MAX,
            y_min=zones["content_y_min"],
            y_max=zones["content_y_max"],
            debug=debug,
            **kwargs,
        )

    def place_content(self, graphics_group: VGroup, h_align: str = "center") -> VGroup:
        """将图形缩放至区域尺寸的80%

        Args:
            graphics_group: 图形组
            h_align: 水平对齐方式（center/left/right），默认 center

        Returns:
            已定位并缩放的图形组
        """
        import logging

        # Manim VGroup 用 get_critical_point 获取边界点
        x_min_g = graphics_group.get_critical_point(LEFT)[0]
        x_max_g = graphics_group.get_critical_point(RIGHT)[0]
        y_min_g = graphics_group.get_critical_point(DOWN)[1]
        y_max_g = graphics_group.get_critical_point(UP)[1]
        bb_w = x_max_g - x_min_g
        bb_h = y_max_g - y_min_g

        logging.info(
            f"[GraphicsZone.place_content] 输入: {type(graphics_group).__name__} "
            f"子对象数: {len(graphics_group.submobjects)}"
        )
        for i, sub in enumerate(graphics_group.submobjects):
            sx_min = sub.get_critical_point(LEFT)[0]
            sx_max = sub.get_critical_point(RIGHT)[0]
            sy_min = sub.get_critical_point(DOWN)[1]
            sy_max = sub.get_critical_point(UP)[1]
            logging.info(
                f"  子对象[{i}] {type(sub).__name__}: "
                f"w={sx_max-sx_min:.2f} h={sy_max-sy_min:.2f} "
                f"x=[{sx_min:.2f},{sx_max:.2f}] y=[{sy_min:.2f},{sy_max:.2f}]"
            )

        # 目标尺寸：区域大小的 80%
        target_w = self._width * 0.8
        target_h = self._height * 0.8

        # 用 critical_point 计算的边界尺寸更可靠
        scale_x = target_w / bb_w if bb_w > 0 else 1.0
        scale_y = target_h / bb_h if bb_h > 0 else 1.0
        scale_factor = min(scale_x, scale_y)

        logging.info(
            f"[GraphicsZone.place_content] 原始(bb): {bb_w:.2f}×{bb_h:.2f} | "
            f"区域: w={self._width:.2f} h={self._height:.2f} | "
            f"目标(80%): w={target_w:.2f} h={target_h:.2f} | "
            f"scale_x={scale_x:.3f} scale_y={scale_y:.3f} scale_factor={scale_factor:.3f}"
        )

        # 限制缩放范围，避免过大或过小
        scale_factor = max(0.3, min(scale_factor, 2.0))

        if scale_factor != 1.0:
            graphics_group.scale(scale_factor, about_point=graphics_group.get_center())

        # 缩放后重新获取尺寸用于定位
        scaled_width = graphics_group.get_width()
        scaled_height = graphics_group.get_height()

        # 水平对齐：根据 h_align 参数决定
        if h_align == "left":
            graphics_group.move_to([self._x_min + scaled_width / 2, self._center_y, 0])
        elif h_align == "right":
            graphics_group.move_to([self._x_max - scaled_width / 2, self._center_y, 0])
        else:  # center
            graphics_group.move_to([self._center_x, self._center_y, 0])

        self._content_group = graphics_group
        return graphics_group
