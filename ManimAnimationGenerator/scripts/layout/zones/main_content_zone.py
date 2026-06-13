#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主内容区容器 - 根据布局模式动态调整宽度

严格遵循 references/layout.md：
- 单栏模式：X ∈ [-6.75, 6.75]，Y ∈ [-2.5, 3.11]
- 两栏模式：X ∈ [-6.75, 1.35]，Y ∈ [-2.5, 3.11]
- 三栏模式：主内容区为左栏+中栏，X ∈ [-6.75, 2.35]，Y ∈ [-2.5, 3.11]

排版对齐规范（ZoneConstants 对齐算法）：
- 左栏（index=0）：LEFT  → 内容左边缘对齐栏左边界 x_min
- 中栏（index=1）：LEFT  → 内容左边缘对齐栏左边界 x_min（三栏模式）
- 右栏（index=2）：RIGHT → 内容右边缘对齐栏右边界 x_max（三栏模式）
- 调用 ZoneConstants.align_content_in_column() 进行栏位对齐
"""

from manim import VGroup
from scripts.layout.zones.base import ZoneBase
from scripts.layout.constants import ZoneConstants


class MainContentZone(ZoneBase):
    """主内容区容器

    根据布局模式（单栏/两栏/三栏）动态设置边界
    三栏模式时，主内容区包含左栏（步骤说明）和中栏（公式），
    图形区由 GraphicsZone 独立管理（layout.md 第 3.6 节）
    """

    def __init__(
        self,
        layout_mode: str = "vertical",
        debug: bool = False,
        **kwargs,
    ):
        """初始化主内容区容器

        Args:
            layout_mode: 布局模式，可选 "vertical", "two_column", "three_column", "centered"
            debug: 调试模式，显示容器边框和填充
            **kwargs: 传递给 ZoneBase 的样式参数
        """
        boundaries = self._get_boundaries(layout_mode)

        super().__init__(
            x_min=boundaries["x_min"],
            x_max=boundaries["x_max"],
            y_min=boundaries["y_min"],
            y_max=boundaries["y_max"],
            debug=debug,
            **kwargs,
        )

        self._layout_mode = layout_mode

    def _get_boundaries(self, mode: str) -> dict:
        """根据布局模式返回边界坐标"""
        boundaries = {
            "vertical": {
                "x_min": ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MIN,
                "x_max": ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MAX,
                "y_min": ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MIN,
                "y_max": ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MAX,
            },
            "two_column": {
                "x_min": ZoneConstants.MAIN_CONTENT_TWO_COL_X_MIN,
                "x_max": ZoneConstants.MAIN_CONTENT_TWO_COL_X_MAX,
                "y_min": ZoneConstants.MAIN_CONTENT_TWO_COL_Y_MIN,
                "y_max": ZoneConstants.MAIN_CONTENT_TWO_COL_Y_MAX,
            },
            "three_column": {
                # 三栏模式：主内容区包含左栏（步骤说明）和中栏（公式）
                # 左栏 X ∈ [-6.75, -2.2]，中栏 X ∈ [-1.7, 2.35]
                # 因此主内容区 X 范围取 [-6.75, 2.35]
                "x_min": ZoneConstants.THREE_COL_LEFT_X_MIN,
                "x_max": ZoneConstants.THREE_COL_MID_X_MAX,  # 中栏右边界
                "y_min": ZoneConstants.THREE_COL_Y_MIN,
                "y_max": ZoneConstants.THREE_COL_Y_MAX,
            },
            "centered": {
                # 居中模式：内容整体垂直居中（Y=0），使用单栏安全宽度
                "x_min": ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MIN,
                "x_max": ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MAX,
                "y_min": ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MIN,
                "y_max": ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MAX,
            },
        }

        if mode not in boundaries:
            raise ValueError(
                f"Unknown layout mode: {mode}. Must be one of {list(boundaries.keys())}"
            )

        return boundaries[mode]

    @property
    def layout_mode(self) -> str:
        """获取当前布局模式"""
        return self._layout_mode
