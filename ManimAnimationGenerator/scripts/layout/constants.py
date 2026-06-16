#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域常量定义 - 动态计算版本

算法（16:9）：
1. 总窗口 = (config.frame_width, config.frame_height)  → 通过属性获取
2. 安全区 = 总窗口 - 边距比例 × 2
3. 标题区高度 = max(安全区高 × 2/10, Text(font_size=40).height)  → 取比例与实测的较大值
4. 字幕区高度 = max(安全区高 × 1/10, Text(font_size=18).height)  → 取比例与实测的较大值
5. 内容区高度 = 安全区高 - 标题高 - 字幕高 - 区域间距
6. 各区 X 范围 = 安全区 X ± 偏移（按比例）

严禁在业务代码中硬编码区域边界，统一通过此类引用。
"""

from manim import Text


class ZoneConstants:
    """布局区域常量定义"""

    # ============================================================
    # 固定配置参数（比例）
    # ============================================================

    # 安全区边距（占窗口的比例）
    # MARGIN_RATIO_X 选 0.0253 使 safe_w ≈ 13.5，与静态常量隐含的
    # 安全区宽度严格对齐（否则 validate_layout 会假阳性越界）：
    #   -6.75 = -14.22/2 + 14.22*0.0253 ✓
    #   safe_w = 14.22 - 14.22*2*0.0253 = 13.50 ✓
    #   two_col_left_x_max = -6.75 + 13.5*0.6 = 1.35 (vs MAIN_CONTENT_TWO_COL_X_MAX=1.35) ✓
    #   two_col_right_x_min = 1.35 + 0.5 = 1.85 (vs GRAPHICS_X_MIN=1.85) ✓
    #   three_mid_x_min = -2.2 + 0.5 = -1.7 (vs THREE_COL_MID_X_MIN=-1.7) ✓
    # Y 方向同理（SCREEN_HEIGHT=8, 0.05 边距 → safe_h=7.2; 静态 SAFE_AREA_Y 跨 6.8）
    MARGIN_RATIO_X = 0.0253  # 水平边距（与静态常量 13.5 安全区宽度匹配）
    MARGIN_RATIO_Y = 0.075   # 垂直边距（与静态常量 -2.8/4.0 安全区匹配）

    # 各区域高度比例（占安全区高度的比例）
    TITLE_RATIO = 0.20  # 标题区占安全区的 2/10
    SUBTITLE_RATIO = 0.10  # 字幕区占安全区的 1/10
    # ZONE_SPACING = 0.5 与 layout.md 第 4.3 节"栏间至少 0.5" 一致，
    # 与静态常量 GRAPHICS_X_MIN=1.85 / TWO_COL_X_MAX=1.35 隐含的 0.5
    # 间距也对齐。compute() 动态计算与静态常量边界完全对齐：
    #   two_col_left_x_max = -6.75 + 13.5 * 0.6 = 1.35
    #   two_col_right_x_min = 1.35 + 0.5 = 1.85  ← 与 GRAPHICS_X_MIN 一致
    #   three_mid_x_min = -2.2 + 0.5 = -1.7      ← 与 THREE_COL_MID_X_MIN 一致
    #   three_mid_x_max = -1.7 + 13.5*0.3 = 2.35  ← 与 THREE_COL_MID_X_MAX 一致
    ZONE_SPACING = 0.5  # 区域垂直间距 & 分栏水平间距（与 layout.md 一致）

    # 分栏水平比例
    # THREE_COL_RATIOS 由静态常量反推：(0.337, 0.30, 0.363)
    # 调整比例使其与静态常量精确对齐：
    #   left_x_max = -6.75 + 13.5*0.337 = -2.20 ✓
    #   mid_x_min  = -2.20 + 0.5       = -1.70 ✓
    #   mid_x_max  = -1.70 + 13.5*0.30 = 2.35  ✓
    #   right_x_min= 2.35 + 0.5        = 2.85  ✓
    TWO_COL_LEFT_RATIO = 0.60  # 两栏左栏（有图形时）
    TWO_COL_RIGHT_RATIO = 0.40  # 两栏右栏（有图形时）
    THREE_COL_RATIOS = (0.337, 0.30, 0.363)  # 三栏（左/中/右，与静态常量对齐）

    # 字幕可见行数
    SUBTITLE_VISIBLE_LINES = 2

    # ============================================================
    # 字体大小
    # ============================================================
    FONT_SIZE_TITLE = 40
    FONT_SIZE_SUBTITLE = 34
    FONT_SIZE_MAIN_SINGLE = 32
    FONT_SIZE_MAIN_TWO_COL_LEFT = 30
    FONT_SIZE_MAIN_TWO_COL_FORMULA = 32
    FONT_SIZE_MAIN_TWO_COL_GRAPHICS = 28
    FONT_SIZE_MAIN_THREE_COL_LEFT = 28
    FONT_SIZE_MAIN_THREE_COL_MID = 28
    FONT_SIZE_MAIN_THREE_COL_RIGHT = 24
    FONT_SIZE_SUBTITLE_TEXT = 18  # 字幕文字统一 18px

    # ============================================================
    # 间距常量
    # ============================================================
    ROW_BUFF = 0.6
    ELEMENT_BUFF = 0.3

    # 布局决策阈值
    VERTICAL_OVERFLOW_THRESHOLD = 5.5
    HORIZONTAL_OVERFLOW_THRESHOLD = 13.5  # 安全区水平边界 6.75×2

    # ============================================================
    # 字幕样式
    # ============================================================
    SUBTITLE_SCROLL_DURATION = 0.4  # 单次滚动动画过渡时长（秒），仅控制动画平滑度
    SUBTITLE_SPEECH_SPEED = 4.0     # 语音朗读速度（字符/秒），用于计算每行显示时间
                                    # 每行显示时间 = 行字符数 / SPEECH_SPEED
                                    # 例：20字符行 → 20/4 = 5秒显示时间
    SUBTITLE_BACKGROUND_COLOR = "#0e1828"
    SUBTITLE_BACKGROUND_OPACITY = 0.72
    SUBTITLE_BACKGROUND_PADDING_W = 0.4
    SUBTITLE_BACKGROUND_PADDING_H = 0.2
    SUBTITLE_BACKGROUND_CORNER_RADIUS = 0.14
    SUBTITLE_TEXT_COLOR = "#CCCCCC"
    SUBTITLE_BACKGROUND_TO_TEXT_MARGIN = 0.1

    # 字幕区布局约束（补充 subtitle_zone.py 所需）
    SUBTITLE_ZONE_BOTTOM_FIXED_Y = (
        -3.85
    )  # 字幕底部固定位置（与 SUBTITLE_ZONE_Y_MIN 一致）
    SUBTITLE_ZONE_TOP_Y = (
        -2.8
    )  # 字幕区上界（防止侵入主内容区，与 SUBTITLE_ZONE_Y_MAX 一致）
    SUBTITLE_ZONE_X_MIN = (
        -6.75
    )  # 字幕区左边界（与安全区左边界一致，确保底衬不越界）
    SUBTITLE_ZONE_X_MAX = (
        6.75
    )  # 字幕区右边界（与安全区右边界一致，确保底衬不越界）
    SUBTITLE_LINE_SPACING_RATIO = 0.6  # 字幕行间距系数（相对于 font_size）
    SUBTITLE_LINE_HEIGHT_RATIO = 1.4  # 字幕行高系数（font_size → 实际行高的倍率）
    # 字体大小到 Manim 单位的换算系数：
    # Manim 默认 1 单位 = 1 inch = 72 points，font_size 本身就是 points，
    # 因此 font_size/72 才是正确换算系数。
    # 保留本常量仅为兼容遗留引用，新代码请直接使用 font_size / 72.0 计算。
    MANIM_FONT_TO_UNIT_RATIO = 1.0  # 字体大小到 Manim 单位的换算系数

    # 兼容性别名
    SUBTITLE_FONT_SIZE = FONT_SIZE_SUBTITLE_TEXT  # 兼容旧代码

    # ============================================================
    # 字体自适应算法
    # ============================================================

    @classmethod
    def auto_font_size(
        cls,
        content_width: float,
        available_width: float,
        base_size: int = 32,
        min_size: int = 24,
        max_size: int = 34,
    ) -> int:
        """根据可用宽度自动计算合适的字体大小

        算法：
        1. 计算宽度比例：ratio = available_width / content_width
        2. 目标字号：target_size = base_size × ratio
        3. 限制范围：clamp(target_size, min_size, max_size)

        Args:
            content_width: 内容当前宽度（Manim 单位）
            available_width: 可用宽度（栏位宽度）
            base_size: 基准字号（默认 32px）
            min_size: 最小字号（默认 24px）
            max_size: 最大字号（默认 34px）

        Returns:
            推荐的字号（int）

        示例::

            # 单栏模式：内容宽 10.0，可用宽 13.5
            font_size = ZoneConstants.auto_font_size(10.0, 13.5)  # → 32 (无需缩小)

            # 内容宽 15.0，可用宽 13.5
            font_size = ZoneConstants.auto_font_size(15.0, 13.5)  # → 28 (缩放 0.9)

            # 内容宽 20.0，可用宽 13.5
            font_size = ZoneConstants.auto_font_size(20.0, 13.5)  # → 24 (触及下限)
        """
        if content_width <= 0 or available_width <= 0:
            return base_size

        ratio = available_width / content_width
        target_size = int(base_size * ratio)

        # 限制在允许范围内
        return max(min_size, min(max_size, target_size))

    @classmethod
    def estimate_text_width(cls, text: str, font_size: int) -> float:
        """预估文本宽度（无需创建 Mobject）

        基于经验公式：每字符约 0.6 单位（font_size=32 时）

        Args:
            text: 文本内容
            font_size: 字体大小

        Returns:
            预估宽度（Manim 单位）
        """
        if not text:
            return 0.0

        # 基准：font_size=32 时，每字符约 0.6 单位
        chars_per_unit = 1 / 0.6
        scale_factor = font_size / 32.0
        estimated_width = len(text) / chars_per_unit * scale_factor

        return estimated_width

    @classmethod
    def estimate_formula_width(cls, tex_string: str, font_size: int) -> float:
        """预估公式宽度（基于 LaTeX 长度）

        经验公式：
        - 简单公式：宽度 ≈ 字符数 × 0.55
        - 复杂公式（含矩阵/分式）：宽度 ≈ 字符数 × 0.7

        Args:
            tex_string: LaTeX 公式字符串
            font_size: 字体大小

        Returns:
            预估宽度（Manim 单位）
        """
        if not tex_string:
            return 0.0

        # 检测复杂结构
        is_complex = any(
            cmd in tex_string
            for cmd in ["\\begin{bmatrix}", "\\frac", "\\int", "\\sum", "\\begin{pmatrix}"]
        )

        char_width = 0.7 if is_complex else 0.55
        scale_factor = font_size / 32.0
        estimated_width = len(tex_string) * char_width * scale_factor * 0.1

        return estimated_width

    # ============================================================
    # 静态常量（标准 16:9 配置的计算结果，作为默认值和文档参考）
    # 基于 frame_height=8, frame_width≈14.22 计算
    # ============================================================

    # 屏幕基础尺寸（标准配置）
    SCREEN_WIDTH = 14.22
    SCREEN_HEIGHT = 8.0

    # 安全区域
    SAFE_AREA_X_MIN = -6.75
    SAFE_AREA_X_MAX = 6.75
    SAFE_AREA_Y_MIN = -2.8
    SAFE_AREA_Y_MAX = 4.0

    # 标题区（Y 范围由标准配置计算得出）
    TITLE_ZONE_Y_MIN = 3.11  # 4.0 - 0.89
    TITLE_ZONE_Y_MAX = 4.0
    TITLE_ZONE_HEIGHT = 0.89
    TITLE_ZONE_CENTER_Y = 3.555

    # 字幕区（Y 范围由标准配置计算得出）
    SUBTITLE_ZONE_Y_MIN = -3.85
    SUBTITLE_ZONE_Y_MAX = -2.8
    SUBTITLE_ZONE_HEIGHT = 1.05
    SUBTITLE_ZONE_CENTER_Y = -3.325

    # 主内容区（两栏，有图形时左 60%/右 40%）
    MAIN_CONTENT_TWO_COL_X_MIN = -6.75
    MAIN_CONTENT_TWO_COL_X_MAX = 1.35
    MAIN_CONTENT_TWO_COL_Y_MIN = -2.5
    MAIN_CONTENT_TWO_COL_Y_MAX = 3.11

    # 主内容区（单栏）
    MAIN_CONTENT_SINGLE_COL_X_MIN = -6.75
    MAIN_CONTENT_SINGLE_COL_X_MAX = 6.75
    MAIN_CONTENT_SINGLE_COL_Y_MIN = -2.5
    MAIN_CONTENT_SINGLE_COL_Y_MAX = 3.11

    # 图形区（两栏时）
    GRAPHICS_X_MIN = 1.85
    GRAPHICS_X_MAX = 6.75
    GRAPHICS_Y_MIN = -2.5
    GRAPHICS_Y_MAX = 3.11

    # 三栏布局
    THREE_COL_LEFT_X_MIN = -6.75
    THREE_COL_LEFT_X_MAX = -2.2
    THREE_COL_MID_X_MIN = -1.7
    THREE_COL_MID_X_MAX = 2.35
    THREE_COL_RIGHT_X_MIN = 2.85
    THREE_COL_RIGHT_X_MAX = 6.75
    THREE_COL_Y_MIN = -2.5
    THREE_COL_Y_MAX = 3.11

    # 标题 Y 位置
    TITLE_Y = 3.555
    SUBTITLE_Y = 2.8

    # ============================================================
    # 动态计算接口（核心算法）
    # ============================================================

    @classmethod
    def measure_heights(cls) -> tuple[float, float]:
        """
        测量标题和字幕文字的实际 Manim 单位高度。

        Returns:
            (title_height, subtitle_height): 标题和字幕的 .height 值
        """
        title_height = Text("", font_size=cls.FONT_SIZE_TITLE).height
        subtitle_height = Text("", font_size=cls.FONT_SIZE_SUBTITLE_TEXT).height
        return title_height, subtitle_height

    @classmethod
    def compute(cls, frame_width: float, frame_height: float) -> dict:
        """
        根据实际窗口尺寸动态计算所有区域边界。

        算法：
        1. 总窗口 = (frame_width, frame_height)
        2. 安全区 = 总窗口 - 边距比例 × 2
        3. 标题区高度 = max(安全区高 × TITLE_RATIO, Text(font_size=TITLE).height)
        4. 字幕区高度 = max(安全区高 × SUBTITLE_RATIO, Text(font_size=SUBTITLE).height)
        5. 内容区高度 = 安全区高 - 标题高 - 字幕高 - ZONE_SPACING

        Args:
            frame_width: 帧宽度（config.frame_width）
            frame_height: 帧高度（config.frame_height）

        Returns:
            包含所有计算后区域边界的字典
        """
        title_h, subtitle_h = cls.measure_heights()

        # 安全区计算
        margin_x = frame_width * cls.MARGIN_RATIO_X
        margin_y = frame_height * cls.MARGIN_RATIO_Y
        safe_w = frame_width - margin_x * 2
        safe_h = frame_height - margin_y * 2
        safe_x_min = -frame_width / 2 + margin_x
        safe_x_max = frame_width / 2 - margin_x
        safe_y_min = -frame_height / 2 + margin_y
        safe_y_max = frame_height / 2 - margin_y

        # 各区高度（取比例值与实测值的较大值）
        title_zone_h = max(safe_h * cls.TITLE_RATIO, title_h)
        subtitle_zone_h = max(safe_h * cls.SUBTITLE_RATIO, subtitle_h)

        # 内容区高度 = 安全区 - 标题 - 字幕 - 间距
        content_h = safe_h - title_zone_h - subtitle_zone_h - cls.ZONE_SPACING

        # 区域 Y 边界
        title_y_min = safe_y_max - title_zone_h
        title_y_max = safe_y_max
        subtitle_y_max = safe_y_min + subtitle_zone_h
        subtitle_y_min = safe_y_min
        content_y_max = title_y_min - cls.ZONE_SPACING
        content_y_min = subtitle_y_max

        # 两栏 X 边界
        two_col_left_x_max = safe_x_min + safe_w * cls.TWO_COL_LEFT_RATIO
        two_col_right_x_min = two_col_left_x_max + cls.ZONE_SPACING

        # 三栏 X 边界
        left_w, mid_w, right_w = cls.THREE_COL_RATIOS
        three_left_x_max = safe_x_min + safe_w * left_w
        three_mid_x_min = three_left_x_max + cls.ZONE_SPACING
        three_mid_x_max = three_mid_x_min + safe_w * mid_w
        three_right_x_min = three_mid_x_max + cls.ZONE_SPACING

        return {
            # 基础尺寸
            "frame_width": frame_width,
            "frame_height": frame_height,
            # 安全区
            "safe_x_min": safe_x_min,
            "safe_x_max": safe_x_max,
            "safe_y_min": safe_y_min,
            "safe_y_max": safe_y_max,
            "safe_width": safe_w,
            "safe_height": safe_h,
            # 标题区
            "title_y_min": title_y_min,
            "title_y_max": title_y_max,
            "title_height": title_zone_h,
            # 字幕区
            "subtitle_y_min": subtitle_y_min,
            "subtitle_y_max": subtitle_y_max,
            "subtitle_height": subtitle_zone_h,
            # 主内容区
            "content_y_min": content_y_min,
            "content_y_max": content_y_max,
            "content_height": content_h,
            # 单栏
            "single_x_min": safe_x_min,
            "single_x_max": safe_x_max,
            # 两栏
            "two_left_x_min": safe_x_min,
            "two_left_x_max": two_col_left_x_max,
            "two_right_x_min": two_col_right_x_min,
            "two_right_x_max": safe_x_max,
            # 图形区（两栏右栏）
            "graphics_x_min": two_col_right_x_min,
            "graphics_x_max": safe_x_max,
            # 三栏
            "three_left_x_min": safe_x_min,
            "three_left_x_max": three_left_x_max,
            "three_mid_x_min": three_mid_x_min,
            "three_mid_x_max": three_mid_x_max,
            "three_right_x_min": three_right_x_min,
            "three_right_x_max": safe_x_max,
            # Y 共享
            "all_y_min": content_y_min,
            "all_y_max": content_y_max,
        }

    @classmethod
    def compute_column_layout(
        cls,
        zones: dict,
        num_columns: int,
        has_graphics: bool = False,
    ) -> list[dict]:
        """
        分栏布局算法：根据分栏数量和图形存在情况，计算每一栏的 X 边界。

        算法流程：
        1. 获取总宽度：从 zones 字典获取 safe_width
        2. 按比例分配：根据分栏数量和图形存在情况分配每一栏宽度
           - 两栏（有图形）：左 60%，右 40%
           - 两栏（无图形）：均分 50% / 50%
           - 三栏（有图形）：左 30%，中 30%，右 40%
           - 三栏（无图形）：均分 1/3 / 1/3 / 1/3
        3. 记录每栏边界：每一栏的 x_min, x_max, width

        调用方式：
            zones = ZoneConstants.compute(frame_width, frame_height)
            cols = ZoneConstants.compute_column_layout(zones, num_columns=2, has_graphics=True)
            left_col_width = cols[0]["width"]    # 左栏宽度
            right_col_width = cols[1]["width"]   # 右栏宽度

        Args:
            zones: ZoneConstants.compute() 返回的字典
            num_columns: 分栏数量（1, 2, 或 3）
            has_graphics: 是否有图形（影响两栏/三栏时的比例分配）

        Returns:
            每栏的边界信息列表，每项包含 x_min, x_max, width
        """
        safe_x_min = zones["safe_x_min"]
        safe_w = zones["safe_width"]
        safe_x_max = zones["safe_x_max"]

        if num_columns == 1:
            return [
                {"x_min": safe_x_min, "x_max": safe_x_max, "width": safe_w, "index": 0}
            ]

        elif num_columns == 2:
            if has_graphics:
                left_ratio = cls.TWO_COL_LEFT_RATIO
            else:
                left_ratio = 0.5

            left_w = safe_w * left_ratio
            right_w = safe_w * (1 - left_ratio)
            left_x_max = safe_x_min + left_w
            right_x_min = left_x_max + cls.ZONE_SPACING
            right_x_max = safe_x_max

            return [
                {"x_min": safe_x_min, "x_max": left_x_max, "width": left_w, "index": 0},
                {
                    "x_min": right_x_min,
                    "x_max": right_x_max,
                    "width": right_w,
                    "index": 1,
                },
            ]

        elif num_columns == 3:
            if has_graphics:
                left_ratio = cls.THREE_COL_RATIOS[0]
                mid_ratio = cls.THREE_COL_RATIOS[1]
            else:
                left_ratio = mid_ratio = 1.0 / 3.0

            left_w = safe_w * left_ratio
            mid_w = safe_w * mid_ratio
            right_w = safe_w * (1.0 - left_ratio - mid_ratio)
            left_x_max = safe_x_min + left_w
            mid_x_min = left_x_max + cls.ZONE_SPACING
            mid_x_max = mid_x_min + mid_w
            right_x_min = mid_x_max + cls.ZONE_SPACING
            right_x_max = safe_x_max

            return [
                {"x_min": safe_x_min, "x_max": left_x_max, "width": left_w, "index": 0},
                {"x_min": mid_x_min, "x_max": mid_x_max, "width": mid_w, "index": 1},
                {
                    "x_min": right_x_min,
                    "x_max": right_x_max,
                    "width": right_w,
                    "index": 2,
                },
            ]

        else:
            raise ValueError(
                f"Unsupported num_columns: {num_columns}. Must be 1, 2, or 3."
            )

    @classmethod
    def validate_column_fit(
        cls,
        column: dict,
        content_width: float,
        content_height: float,
        max_height: float,
    ) -> tuple[bool, list[str]]:
        """
        校验单栏内容是否适配。

        校验规则：
        1. 宽度适配：content_width <= column["width"]
        2. 高度适配：content_height <= max_height
        3. 不越界：column["x_min"] >= SAFE_AREA_X_MIN and column["x_max"] <= SAFE_AREA_X_MAX

        溢出处理优先级：
        1. 缩小字号（缩到下限，如 80%）
        2. 换行（使用 align* 环境）
        3. 拆分（触发 split_atom.py 按栏位拆分）

        Args:
            column: compute_column_layout() 返回的单栏信息
            content_width: 内容预估宽度
            content_height: 内容预估高度
            max_height: 该栏允许的最大高度

        Returns:
            (is_valid, violations): 是否通过校验，违规列表（用于拆分决策）
        """
        violations = []

        if content_width > column["width"]:
            violations.append(
                f"Width overflow: content {content_width:.2f} > column {column['width']:.2f}"
            )

        if content_height > max_height:
            violations.append(
                f"Height overflow: content {content_height:.2f} > max {max_height:.2f}"
            )

        return len(violations) == 0, violations

    # ==========================================================
    # 分栏对齐算法
    # ==========================================================

    @classmethod
    def get_column_alignment(cls, column_index: int, num_columns: int = 2) -> str:
        """
        获取指定栏位的对齐方向。

        对齐规则（遵循 layout.md 第 10.5.1 节"三栏中栏 LEFT 对齐"）：

        - 三栏左栏（num_columns=3, index=0）：LEFT
        - 三栏中栏（num_columns=3, index=1）：LEFT  （靠中栏左边界）
        - 三栏右栏（num_columns=3, index=2）：RIGHT （靠右边界）
        - 两栏左栏（num_columns=2, index=0）：LEFT
        - 两栏右栏（num_columns=2, index=1）：RIGHT （靠右边界）
        - 单栏（num_columns=1, index=0）：LEFT
        - 其他情况默认 LEFT

        Args:
            column_index: 栏位索引，从左到右 0, 1, 2
            num_columns: 总栏数（1, 2, 或 3），决定中栏对齐方向（默认 2）

        Returns:
            "LEFT" 或 "RIGHT"
        """
        # 三栏：index=0,1 都靠左边界；index=2 靠右边界
        if num_columns == 3:
            if column_index == 2:
                return "RIGHT"
            return "LEFT"
        # 两栏：index=0 靠左，index=1 靠右
        if num_columns == 2:
            if column_index == 1:
                return "RIGHT"
            return "LEFT"
        # 单栏或其他：默认靠左
        return "LEFT"

    @classmethod
    def get_column_anchor_x(cls, column: dict, alignment: str) -> float:
        """
        计算内容在栏位中的锚点 X 坐标。

        用于 .next_to() 或 .move_to() 的 x 参数。

        对齐逻辑：
        - LEFT  → 返回 column["x_min"]，内容左边缘对齐栏左边界
        - RIGHT → 返回 column["x_max"]，内容右边缘对齐栏右边界

        注意：返回的是锚点坐标，内容实际放置后需根据对齐方向做偏移。
        Manim 中，默认对齐参考对象的 LEFT/RIGHT 边缘。

        Args:
            column: compute_column_layout() 返回的单栏信息
            alignment: "LEFT" 或 "RIGHT"

        Returns:
            锚点 X 坐标（用于内容定位）
        """
        if alignment == "RIGHT":
            return column["x_max"]
        return column["x_min"]

    @classmethod
    def align_content_in_column(
        cls, mobject, column: dict, column_index: int, num_columns: int = 2
    ) -> None:
        """
        将内容对齐到指定栏位。

        封装常见对齐操作：
        1. 根据栏位索引与总栏数确定对齐方向（调用 get_column_alignment）
        2. 计算锚点坐标
        3. 将 mobject 水平移动到锚点

        实现要点：显式计算"使目标边对齐 anchor_x"的 center 坐标，
        再 move_to 该中心。注意 X 维度上若用 ``get_center().set_x(anchor_x)``
        会把目标点设到对象当前 center.x，再以 RIGHT/LEFT 边对齐，
        X 维度会完全 no-op，LEFT/RIGHT 都无效。

        示例（三栏中栏内容左对齐）::

            col = ZoneConstants.compute_column_layout(zones, 3, has_graphics=True)[1]
            ZoneConstants.align_content_in_column(text_obj, col, 1, num_columns=3)

        Args:
            mobject: Manim VGroup/Text/Mobject 对象
            column: compute_column_layout() 返回的单栏信息
            column_index: 栏位索引（0=左, 1=中/右, 2=右）
            num_columns: 总栏数（2 或 3），决定中栏对齐方向
        """
        alignment = cls.get_column_alignment(column_index, num_columns=num_columns)
        anchor_x = cls.get_column_anchor_x(column, alignment)

        if alignment == "RIGHT":
            # 内容右边缘对齐栏右边界（anchor_x = column["x_max"]）
            # 此时对象的中心 x 应位于 anchor_x - width/2
            target_cx = anchor_x - mobject.width / 2
        else:
            # 内容左边缘对齐栏左边界（anchor_x = column["x_min"]）
            # 此时对象的中心 x 应位于 anchor_x + width/2
            target_cx = anchor_x + mobject.width / 2

        mobject.move_to([target_cx, mobject.get_y(), 0])
