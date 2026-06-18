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
        """根据布局模式返回边界坐标

        两栏/三栏布局（has_title=False）使用 90% 高度比例：
        - 主内容 Y ∈ [-2.88, 3.6]（90% × safe_h = 6.48）
        - 字幕 Y ∈ [-3.6, -2.88]（10% × safe_h = 0.72）

        单栏/居中布局（has_title=True，三区模式）使用 70% 高度比例：
        - 标题 Y ∈ [2.64, 4.0]（20% × safe_h = 1.36）
        - 主内容 Y ∈ [-2.12, 2.64]（70% × safe_h = 4.76）
        - 字幕 Y ∈ [-2.8, -2.12]（10% × safe_h = 0.68）
        """
        # 两栏 / 三栏：与 ZoneConstants.compute(has_title=False) 保持一致
        if mode in ("two_column", "three_column"):
            return {
                "x_min": self._col_x_min(mode),
                "x_max": self._col_x_max(mode),
                # 主内容 Y 上界 = safe_y_max = 4.0（无标题区，直接到顶）
                # 主内容 Y 下界 = safe_y_min + subtitle_zone_h = -2.8 + 1.36 = -1.44
                "y_min": ZoneConstants.SAFE_AREA_Y_MIN
                + ZoneConstants.compute(
                    ZoneConstants.SCREEN_WIDTH,
                    ZoneConstants.SCREEN_HEIGHT,
                    has_title=False,
                )["subtitle_height"],
                "y_max": ZoneConstants.SAFE_AREA_Y_MAX,
            }

        # vertical / centered（三区模式）：与 ZoneConstants.compute(has_title=True) 保持一致
        return {
            "x_min": ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MIN,
            "x_max": ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MAX,
            "y_min": ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MIN,
            "y_max": ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MAX,
        }

    def _col_x_min(self, mode: str) -> float:
        if mode == "two_column":
            return ZoneConstants.MAIN_CONTENT_TWO_COL_X_MIN
        return ZoneConstants.THREE_COL_LEFT_X_MIN

    def _col_x_max(self, mode: str) -> float:
        if mode == "two_column":
            return ZoneConstants.MAIN_CONTENT_TWO_COL_X_MAX
        return ZoneConstants.THREE_COL_MID_X_MAX

    @property
    def layout_mode(self) -> str:
        """获取当前布局模式"""
        return self._layout_mode
