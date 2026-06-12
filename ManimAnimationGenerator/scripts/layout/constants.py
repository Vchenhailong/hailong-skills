#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域常量定义 - 严格映射 references/layout.md 第 2-3 节安全区域规范

所有区域边界基于 16:9 屏幕（15x9 单位，中心原点）
严禁在业务代码中硬编码区域边界，统一通过此类引用
"""


class ZoneConstants:
    """布局区域常量定义（对应 layout.md 第 2-3 节安全区域规范）"""

    # 屏幕基础尺寸（layout.md 第 2 节）
    # Manim 默认帧 16:9，frame_height=8.0 → Y ∈ [-4.0, 4.0]
    SCREEN_WIDTH = 15.0
    SCREEN_HEIGHT = 9.0

    # 安全区域（layout.md 第 2 节）
    # 内容安全区：Y ∈ [-2.8, 4.0]
    SAFE_AREA_X_MIN = -6.75
    SAFE_AREA_X_MAX = 6.75
    SAFE_AREA_Y_MIN = -2.8
    SAFE_AREA_Y_MAX = 4.0

    # 字幕区（高度≈1.05 容纳2行 font_size=18 + 合理间距，不缩放文字）
    # font_size=18 → 每行高约 0.23 单位，2行+间距约 0.56
    # 容器高度 1.05 单位，底部固定于 Y=-3.85，上界不超过 Y=-2.8
    SUBTITLE_ZONE_X_MIN = -7.0
    SUBTITLE_ZONE_X_MAX = 7.0
    SUBTITLE_ZONE_Y_MIN = -3.85
    SUBTITLE_ZONE_Y_MAX = -2.8
    SUBTITLE_ZONE_WIDTH = 14.0
    SUBTITLE_ZONE_HEIGHT = 1.05
    SUBTITLE_ZONE_CENTER_Y = -3.325

    # 主内容区（两栏，有图形时左60%/右40%）
    MAIN_CONTENT_TWO_COL_X_MIN = -6.75
    MAIN_CONTENT_TWO_COL_X_MAX = 1.35
    MAIN_CONTENT_TWO_COL_Y_MIN = -2.5
    MAIN_CONTENT_TWO_COL_Y_MAX = 3.0

    # 主内容区（单栏，全安全区）
    MAIN_CONTENT_SINGLE_COL_X_MIN = -6.75
    MAIN_CONTENT_SINGLE_COL_X_MAX = 6.75
    MAIN_CONTENT_SINGLE_COL_Y_MIN = -2.5
    MAIN_CONTENT_SINGLE_COL_Y_MAX = 3.0

    # 图形区（两栏时）
    GRAPHICS_X_MIN = 1.85
    GRAPHICS_X_MAX = 6.75
    GRAPHICS_Y_MIN = -2.5
    GRAPHICS_Y_MAX = 3.0

    # 三栏布局（有图形时左30%/中30%/右40%）
    THREE_COL_LEFT_X_MIN = -6.75
    THREE_COL_LEFT_X_MAX = -2.2
    THREE_COL_MID_X_MIN = -1.7
    THREE_COL_MID_X_MAX = 2.35
    THREE_COL_RIGHT_X_MIN = 2.85
    THREE_COL_RIGHT_X_MAX = 6.75
    THREE_COL_Y_MIN = -2.5
    THREE_COL_Y_MAX = 3.0

    # 标题区（layout.md 第 3.2 节表格）
    TITLE_Y = 3.5
    SUBTITLE_Y = 2.8
    MAIN_CONTENT_START_Y = 2.0
    MAIN_CONTENT_CENTER_Y = 0.0

    # 字体大小（layout.md 第 5.1-5.2 节）
    FONT_SIZE_TITLE = 40
    FONT_SIZE_SUBTITLE = 34
    # 主内容区：按技能 5.2 分栏模式字体规格
    FONT_SIZE_MAIN_SINGLE = 32  # 单栏
    FONT_SIZE_MAIN_TWO_COL_LEFT = 30  # 两栏左栏（步骤/说明）
    FONT_SIZE_MAIN_TWO_COL_FORMULA = 32  # 两栏中栏（公式）
    FONT_SIZE_MAIN_TWO_COL_GRAPHICS = 28  # 两栏右栏（图形/标注）
    FONT_SIZE_MAIN_THREE_COL_LEFT = 28  # 三栏左栏（步骤说明）
    FONT_SIZE_MAIN_THREE_COL_MID = 28  # 三栏中栏（公式）
    FONT_SIZE_MAIN_THREE_COL_RIGHT = 24  # 三栏右栏（图形/标注）
    FONT_SIZE_SUBTITLE_TEXT = 24

    # 间距（layout.md 第 6 节）
    ROW_BUFF = 0.6
    ELEMENT_BUFF = 0.3

    # 布局决策阈值（layout.md 第 11.2 节）
    VERTICAL_OVERFLOW_THRESHOLD = 5.5  # 垂直总高度超过此值触发分栏
    HORIZONTAL_OVERFLOW_THRESHOLD = 12.0  # 水平总宽度超过此值触发拆分

    # ============================================================
    # 字幕区常量（扩展）
    # ============================================================

    # 字幕可见行数
    SUBTITLE_VISIBLE_LINES = 2

    # 字幕默认字号
    SUBTITLE_FONT_SIZE = 18

    # Manim 字体大小转行高换算系数
    # 公式：line_height = font_size / 72 * frame_scale * line_height_ratio
    # font_size=18 在 frame_height=8 时，约 0.25 单位
    MANIM_FONT_TO_UNIT_RATIO = 8.0 / 72.0  # ≈ 0.111
    SUBTITLE_LINE_HEIGHT_RATIO = 1.15  # 行高系数（含上下留白）

    # 字幕行间距（基于默认字号的比例）
    SUBTITLE_LINE_SPACING_RATIO = 0.5  # 行间距占行高的比例

    # 字幕滚动动画时长（秒）
    SUBTITLE_SCROLL_DURATION = 0.4

    # 字幕区上界（防止侵入主内容区 Y=-2.5）
    SUBTITLE_ZONE_TOP_Y = -2.8

    # 字幕区底部固定 Y 坐标（用于底部对齐）
    SUBTITLE_ZONE_BOTTOM_FIXED_Y = -3.85

    # 字幕底衬样式
    SUBTITLE_BACKGROUND_COLOR = "#0e1828"
    SUBTITLE_BACKGROUND_OPACITY = 0.72
    SUBTITLE_BACKGROUND_PADDING_W = 0.4  # 底衬水平内边距
    SUBTITLE_BACKGROUND_PADDING_H = 0.2  # 底衬垂直内边距
    SUBTITLE_BACKGROUND_CORNER_RADIUS = 0.14

    # 字幕强调条样式
    SUBTITLE_ACCENT_COLOR = "#ffd166"  # 金色强调
    SUBTITLE_ACCENT_WIDTH = 0.09
    SUBTITLE_ACCENT_CORNER_RADIUS = 0.04
    SUBTITLE_ACCENT_OFFSET_LEFT = 0.18  # 距底衬左边距

    # 字幕颜色
    SUBTITLE_TEXT_COLOR = "#CCCCCC"

    # 字幕底衬与字幕的安全距离
    SUBTITLE_BACKGROUND_TO_TEXT_MARGIN = 0.1
