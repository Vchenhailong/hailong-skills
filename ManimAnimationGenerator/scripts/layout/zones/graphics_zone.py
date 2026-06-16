#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形区容器 - 固定宽度，溢出优先缩放

严格遵循 references/layout.md：
- 两栏模式：X ∈ [1.85, 6.75]，Y ∈ [-2.5, 3.11]
- 第 4.5 节：右侧图形区溢出时优先缩放，而非拆分
- layout.md 第 7.1 节：坐标轴标签不得进入字幕区
"""

from manim import VGroup
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
        
        Args:
            debug: 调试模式，显示容器边框和填充
            **kwargs: 传递给 ZoneBase 的样式参数
        """
        super().__init__(
            x_min=ZoneConstants.GRAPHICS_X_MIN,
            x_max=ZoneConstants.GRAPHICS_X_MAX,
            y_min=ZoneConstants.GRAPHICS_Y_MIN,
            y_max=ZoneConstants.GRAPHICS_Y_MAX,
            debug=debug,
            **kwargs,
        )
        
        self._default_scale_factor = 0.85
    
    def place_content(self, graphics_group: VGroup, h_align: str = "center") -> VGroup:
        """将图形约束在容器内，溢出优先缩放（layout.md 第 4.5 节）

        Args:
            graphics_group: 图形组
            h_align: 水平对齐方式（center/left/right），默认 center

        Returns:
            已定位并缩放的图形组
        """
        current_width = graphics_group.get_width()
        current_height = graphics_group.get_height()

        scale_factor = self._default_scale_factor

        if current_width > self._width:
            scale_factor = min(scale_factor, self._width / current_width)
        if current_height > self._height:
            scale_factor = min(scale_factor, self._height / current_height)

        if scale_factor < 1.0:
            graphics_group.scale(scale_factor, about_point=graphics_group.get_center())

        # 水平对齐：根据 h_align 参数决定（继承自 ZoneBase.place_content）
        # 修复：原 hardcode 居中会让 scene_base.place_two_column 传 h_align 时
        # 报 TypeError。现在支持 center/left/right 三种对齐方式。
        if h_align == "left":
            graphics_group.move_to([self._x_min + current_width / 2, self._center_y, 0])
        elif h_align == "right":
            graphics_group.move_to([self._x_max - current_width / 2, self._center_y, 0])
        else:  # center
            graphics_group.move_to([self._center_x, self._center_y, 0])

        # 修复 P0-5：删除原"防止图形底部进入字幕区"的死代码段。
        # 原代码 `subtitle_safe_y = SUBTITLE_ZONE_Y_MAX + 0.3 = -2.5` 与
        # `GRAPHICS_Y_MIN = -2.5` 相等，`if bottom_edge < -2.5` 永远为 false。
        # 原因：上方 move_to() 已把图形居中到 (center_x, center_y=0.305, 0)，
        # 且 scale_factor 已把图形缩到 zone 高度内，故 bottom >= -2.5 恒成立。
        # 真正的字幕区侵入防护由 place_two_column / place_three_column
        # 中的 validate_layout(..., region="safe_area") 统一处理。

        self._content_group = graphics_group
        return graphics_group
