#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域常量定义 - 动态计算版本

设计规则（与 references/layout.md 保持一致）：
- 安全区：Y ∈ [-3.6, 3.6]（上下边距对称 0.4，frame_height=8，safe_h=7.2）
- 三区（标题+主内容+字幕）：标题 20% / 主内容 70% / 字幕 10%
- 两区（主内容+字幕，无标题）：主内容 90% / 字幕 10%
- X 方向：安全区 X ∈ [-6.75, 6.75]，水平边距 0.0253
- 严禁在业务代码中硬编码区域边界，统一通过此类引用。
"""

from manim import Text


class ZoneConstants:
    """布局区域常量定义"""

    # ============================================================
    # 边距（正负对称：safe_y = ±3.6，safe_h = 7.2）
    # 用户要求：7.2 × 90% = 6.48（主内容），7.2 × 10% = 0.72（字幕）
    # ============================================================
    MARGIN_TOP_Y = 0.4  # 上边距（避免内容顶到屏幕边沿）
    MARGIN_BOTTOM_Y = 0.4  # 下边距（与上边距对称，让 safe_y 范围 ±3.6）
    MARGIN_RATIO_X = 0.0253  # 水平对称边距（safe_w ≈ 13.5）

    # ============================================================
    # 各区域高度比例（占安全区高度 = 7.2）
    # ============================================================
    # 三区（标题+主内容+字幕）：2:7:1
    THREE_ZONE_TITLE_RATIO = 0.20
    THREE_ZONE_CONTENT_RATIO = 0.70
    THREE_ZONE_SUBTITLE_RATIO = 0.10
    # 两区（主内容+字幕，无标题）：9:1
    TWO_ZONE_CONTENT_RATIO = 0.90
    TWO_ZONE_SUBTITLE_RATIO = 0.10
    # 兼容性别名（旧代码引用）
    TITLE_RATIO = THREE_ZONE_TITLE_RATIO
    SUBTITLE_RATIO = THREE_ZONE_SUBTITLE_RATIO

    # ============================================================
    # 区域间距
    # ============================================================
    ZONE_SPACING = 0.5  # 分栏水平间距（X 方向）
    ZONE_SPACING_Y = 0.0  # 区域垂直间距（Y 方向设为 0，让三区严格按 2:7:1 比例）

    # ============================================================
    # 分栏水平比例
    # ============================================================
    TWO_COL_LEFT_RATIO = 0.60  # 两栏左栏
    TWO_COL_RIGHT_RATIO = 0.40  # 两栏右栏
    THREE_COL_RATIOS = (
        0.30,
        0.30,
        0.40,
    )  # 三栏（左/中/右）：左30%、中30%、右40%（layout.md 规范）

    # ============================================================
    # 字幕可见行数
    # ============================================================
    SUBTITLE_VISIBLE_LINES = 2

    # ============================================================
    # 字体默认大小定义
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
    FONT_SIZE_SUBTITLE_TEXT = 18

    # ============================================================
    # 自动缩放下限
    # ============================================================
    MIN_CONTENT_FONT_SIZE = 24
    MIN_GRAPHICS_SCALE_RATIO = 0.80
    MIN_STROKE_WIDTH_POINTS = 3.0

    # ============================================================
    # 字幕处理参数
    # ============================================================
    SUBTITLE_CHARS_PER_LINE = 20
    SUBTITLE_VISIBLE_LINES_MAX = 2
    SUBTITLE_SPEECH_RATE = 4.0
    SUBTITLE_DURATION_FORMULA = "duration_seconds = subtitle_chars / 4.0"

    # ============================================================
    # 间距常量
    # ============================================================
    ROW_BUFF = 0.3
    ELEMENT_BUFF = 0.3

    # 布局决策阈值
    VERTICAL_OVERFLOW_THRESHOLD = 5.5
    HORIZONTAL_OVERFLOW_THRESHOLD = 13.5

    # ============================================================
    # 字幕样式
    # ============================================================
    SUBTITLE_SCROLL_DURATION = 0.4
    SUBTITLE_SPEECH_SPEED = 4.0
    SUBTITLE_BACKGROUND_COLOR = "#0e1828"
    SUBTITLE_BACKGROUND_OPACITY = 0.72
    SUBTITLE_BACKGROUND_PADDING_W = 0.4
    SUBTITLE_BACKGROUND_PADDING_H = 0.2
    SUBTITLE_BACKGROUND_CORNER_RADIUS = 0.14
    SUBTITLE_TEXT_COLOR = "#CCCCCC"
    SUBTITLE_BACKGROUND_TO_TEXT_MARGIN = 0.1

    # 字幕区布局约束（实际值由 _init_dynamic_bounds() 派生）
    # 两区模式：subtitle_y_max = 主内容_y_min = 3.6 - 7.2×0.9 = -2.88
    # 三区模式：subtitle_y_max = -3.6 + 7.2×0.1 = -2.88
    # 底部固定 = subtitle_y_min - 字幕字号对应高度 - 边距
    SUBTITLE_ZONE_BOTTOM_FIXED_Y = None
    SUBTITLE_ZONE_BOTTOM_Y = None
    SUBTITLE_ZONE_TOP_Y = None
    SUBTITLE_ZONE_X_MIN = -6.75
    SUBTITLE_ZONE_X_MAX = 6.75
    # 行高 = font_size/72 × RATIO（Manim 1 单位 = 1 inch = 72 pt）
    # font_size=18 → line_height = 18/72 ≈ 0.226，与 Manim Text 实际高度一致
    SUBTITLE_LINE_SPACING_RATIO = 0.2  # 行间距 = line_height × 0.2
    SUBTITLE_LINE_HEIGHT_RATIO = 1.0  # 修复：原 1.4 导致 line_height=0.316，字幕行超出字幕区上界
    MANIM_FONT_TO_UNIT_RATIO = 1.0

    # 兼容性别名
    SUBTITLE_FONT_SIZE = FONT_SIZE_SUBTITLE_TEXT

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
        """根据可用宽度自动计算合适的字体大小"""
        if content_width <= 0 or available_width <= 0:
            return base_size
        ratio = available_width / content_width
        target_size = int(base_size * ratio)
        return max(min_size, min(max_size, target_size))

    @classmethod
    def estimate_text_width(cls, text: str, font_size: int) -> float:
        """预估文本宽度（无需创建 Mobject）"""
        if not text:
            return 0.0
        chars_per_unit = 1 / 0.6
        scale_factor = font_size / 32.0
        return len(text) / chars_per_unit * scale_factor

    @classmethod
    def estimate_formula_width(cls, tex_string: str, font_size: int) -> float:
        """预估公式宽度（基于 LaTeX 长度）"""
        is_complex = any(
            cmd in tex_string
            for cmd in [
                "\\begin{bmatrix}",
                "\\frac",
                "\\int",
                "\\sum",
                "\\begin{pmatrix}",
            ]
        )
        char_width = 0.7 if is_complex else 0.55
        scale_factor = font_size / 32.0
        return len(tex_string) * char_width * scale_factor * 0.1

    # ============================================================
    # 静态常量（实际值由 _init_dynamic_bounds() 从 compute() 派生）
    # 设计原则：所有 Y 边界不写死字面量，统一从 compute() 派生
    # 传少量变量（safe_h、ratio）→ 计算所有边界
    # 标准 16:9 配置：frame_height=8, frame_width=14.22
    # 正负对称边距 MARGIN_TOP_Y=MARGIN_BOTTOM_Y=0.4
    # safe_y 范围 = ±3.6，高度 = 7.2
    # ============================================================

    SCREEN_WIDTH = 14.22
    SCREEN_HEIGHT = 8.0

    # 安全区（正负对称：Y∈[-3.6, 3.6]，高度 7.2）
    SAFE_AREA_X_MIN = None  # 派生：-frame_width/2 + safe_w/2
    SAFE_AREA_X_MAX = None
    SAFE_AREA_Y_MIN = None  # 派生：-safe_h/2
    SAFE_AREA_Y_MAX = None  # 派生：+safe_h/2

    # 标题区 Y 范围（仅三区模式）：safe_h × 20% = 1.44 → [2.16, 3.6]
    TITLE_ZONE_Y_MIN = None
    TITLE_ZONE_Y_MAX = None
    TITLE_ZONE_HEIGHT = None
    TITLE_ZONE_CENTER_Y = None

    # 字幕区 Y 范围（三区模式 10%）：safe_h × 0.1 = 0.72 → [-3.6, -2.88]
    SUBTITLE_ZONE_Y_MIN = None
    SUBTITLE_ZONE_Y_MAX = None
    SUBTITLE_ZONE_HEIGHT = None
    SUBTITLE_ZONE_CENTER_Y = None

    # 主内容区 Y 范围（单栏/三区模式 70%）：safe_h × 0.7 = 5.04 → [-2.88, 2.16]
    MAIN_CONTENT_SINGLE_COL_X_MIN = -6.75
    MAIN_CONTENT_SINGLE_COL_X_MAX = 6.75
    MAIN_CONTENT_SINGLE_COL_Y_MIN = None
    MAIN_CONTENT_SINGLE_COL_Y_MAX = None

    # 主内容区（两栏，有图形时左 60%/右 40%）
    # Y 范围（两区模式 90%）：safe_h × 0.9 = 6.48 → [-2.88, 3.6]
    MAIN_CONTENT_TWO_COL_X_MIN = -6.75
    MAIN_CONTENT_TWO_COL_X_MAX = None  # 派生：safe_x_min + safe_w * 0.6
    MAIN_CONTENT_TWO_COL_Y_MIN = None
    MAIN_CONTENT_TWO_COL_Y_MAX = None

    # 图形区（两栏时）：Y 范围 = 主内容 Y 范围（两区 90%）
    GRAPHICS_X_MIN = None  # 派生：two_col_x_max + spacing
    GRAPHICS_X_MAX = 6.75
    GRAPHICS_Y_MIN = None
    GRAPHICS_Y_MAX = None

    # 三栏布局：Y 范围 = 主内容 Y 范围（两区 80%）
    THREE_COL_LEFT_X_MIN = -6.75
    THREE_COL_LEFT_X_MAX = None
    THREE_COL_MID_X_MIN = None
    THREE_COL_MID_X_MAX = None
    THREE_COL_RIGHT_X_MIN = None
    THREE_COL_RIGHT_X_MAX = 6.75
    THREE_COL_Y_MIN = None
    THREE_COL_Y_MAX = None

    # 标题/副标题 Y 位置
    TITLE_Y = None
    SUBTITLE_Y = None

    # ============================================================
    # 动态计算接口
    # ============================================================

    @classmethod
    def _init_dynamic_bounds(cls) -> None:
        """从 compute() 派生所有 Y 边界常量（避免硬编码字面量）

        核心设计：用尽量少的变量传递计算
        - 中心点 = 0（屏幕中心 = 安全区中心，明确且不变）
        - 高度 = safe_h = frame_height - top_margin - bottom_margin
        - 比例 = title/content/subtitle 各自占比
        所有 X/Y 边界 = center + height × ratio，结果保留 2 位小数
        """
        zones2col = cls.compute(cls.SCREEN_WIDTH, cls.SCREEN_HEIGHT, has_title=False)
        zones3col = cls.compute(cls.SCREEN_WIDTH, cls.SCREEN_HEIGHT, has_title=True)

        def r(x):
            """保留两位小数"""
            return round(x, 2)

        # 安全区（核心：center=0, half=3.6）
        cls.SAFE_AREA_X_MIN = r(zones2col["safe_x_min"])
        cls.SAFE_AREA_X_MAX = r(zones2col["safe_x_max"])
        cls.SAFE_AREA_Y_MIN = r(zones2col["safe_y_min"])
        cls.SAFE_AREA_Y_MAX = r(zones2col["safe_y_max"])

        # 标题区（三区，从安全区上界向下铺）
        cls.TITLE_ZONE_Y_MIN = r(zones3col["title_y_min"])
        cls.TITLE_ZONE_Y_MAX = r(zones3col["title_y_max"])
        cls.TITLE_ZONE_HEIGHT = r(zones3col["title_height"])
        cls.TITLE_ZONE_CENTER_Y = r(
            (zones3col["title_y_min"] + zones3col["title_y_max"]) / 2
        )
        cls.TITLE_Y = cls.TITLE_ZONE_CENTER_Y

        # 字幕区（三区 10%，从安全区下界向上铺）
        cls.SUBTITLE_ZONE_Y_MIN = r(zones3col["subtitle_y_min"])
        cls.SUBTITLE_ZONE_Y_MAX = r(zones3col["subtitle_y_max"])
        cls.SUBTITLE_ZONE_HEIGHT = r(zones3col["subtitle_height"])
        cls.SUBTITLE_ZONE_CENTER_Y = r(
            (zones3col["subtitle_y_min"] + zones3col["subtitle_y_max"]) / 2
        )

        # 主内容区（单栏 = 三区 70%，夹在标题与字幕之间）
        cls.MAIN_CONTENT_SINGLE_COL_Y_MIN = r(zones3col["content_y_min"])
        cls.MAIN_CONTENT_SINGLE_COL_Y_MAX = r(zones3col["content_y_max"])

        # 主内容区（两栏 = 两区 90%，从安全区上界向下铺 90%）
        cls.MAIN_CONTENT_TWO_COL_Y_MIN = r(zones2col["content_y_min"])
        cls.MAIN_CONTENT_TWO_COL_Y_MAX = r(zones2col["content_y_max"])
        cls.MAIN_CONTENT_TWO_COL_X_MAX = r(zones2col["two_left_x_max"])

        # 图形区（X 从两栏分界开始，Y 同主内容两栏）
        cls.GRAPHICS_X_MIN = r(zones2col["graphics_x_min"])
        cls.GRAPHICS_Y_MIN = r(zones2col["content_y_min"])
        cls.GRAPHICS_Y_MAX = r(zones2col["content_y_max"])

        # 三栏布局（X 按比例切分，Y 同主内容两栏）
        cls.THREE_COL_LEFT_X_MAX = r(zones2col["three_left_x_max"])
        cls.THREE_COL_MID_X_MIN = r(zones2col["three_mid_x_min"])
        cls.THREE_COL_MID_X_MAX = r(zones2col["three_mid_x_max"])
        cls.THREE_COL_RIGHT_X_MIN = r(zones2col["three_right_x_min"])
        cls.THREE_COL_Y_MIN = r(zones2col["content_y_min"])
        cls.THREE_COL_Y_MAX = r(zones2col["content_y_max"])

        # 字幕区顶部/底部固定（两区模式，10% 高度，9:1 比例）
        cls.SUBTITLE_ZONE_TOP_Y = r(zones2col["subtitle_y_max"])
        cls.SUBTITLE_ZONE_BOTTOM_Y = r(zones2col["subtitle_y_min"])
        # 字幕底部固定 Y = subtitle_y_min - 边距
        cls.SUBTITLE_ZONE_BOTTOM_FIXED_Y = r(zones2col["subtitle_y_min"] - 0.15)
        # 副标题 Y 位置（位于主内容区内略偏上）
        cls.SUBTITLE_Y = r(cls.SUBTITLE_ZONE_CENTER_Y + 0.04)

    @classmethod
    def measure_heights(cls) -> tuple[float, float]:
        """测量标题和字幕文字的实际 Manim 单位高度"""
        title_height = Text("", font_size=cls.FONT_SIZE_TITLE).height
        subtitle_height = Text("", font_size=cls.FONT_SIZE_SUBTITLE_TEXT).height
        return title_height, subtitle_height

    @classmethod
    def compute(
        cls, frame_width: float, frame_height: float, has_title: bool = True
    ) -> dict:
        """根据实际窗口尺寸动态计算所有区域边界

        算法：
        1. 总窗口 = (frame_width, frame_height)
        2. 安全区 = (X 方向对称边距) + (Y 方向非对称边距：上 0, 下 1.2)
        3. 三区：标题 = safe_h × 20%, 主内容 = safe_h × 70%, 字幕 = safe_h × 10%
        4. 两区：主内容 = safe_h × 90%, 字幕 = safe_h × 10%

        Args:
            frame_width: 帧宽度
            frame_height: 帧高度
            has_title: 是否包含标题区（True=三区, False=两区）

        Returns:
            包含所有计算后区域边界的字典
        """
        title_h, subtitle_h = cls.measure_heights()

        # 安全区计算（X 对称，Y 非对称）
        margin_x = frame_width * cls.MARGIN_RATIO_X
        margin_top_y = cls.MARGIN_TOP_Y
        margin_bottom_y = cls.MARGIN_BOTTOM_Y
        safe_w = frame_width - margin_x * 2
        safe_h = frame_height - margin_top_y - margin_bottom_y
        safe_x_min = -frame_width / 2 + margin_x
        safe_x_max = frame_width / 2 - margin_x
        safe_y_min = -frame_height / 2 + margin_bottom_y
        safe_y_max = frame_height / 2 - margin_top_y

        # 区域高度（按比例 + 实测取较大值）
        if has_title:
            title_zone_h = max(safe_h * cls.THREE_ZONE_TITLE_RATIO, title_h)
            content_zone_h = max(safe_h * cls.THREE_ZONE_CONTENT_RATIO, 1.0)
            subtitle_zone_h = max(safe_h * cls.THREE_ZONE_SUBTITLE_RATIO, subtitle_h)
        else:
            title_zone_h = 0.0
            content_zone_h = max(safe_h * cls.TWO_ZONE_CONTENT_RATIO, 1.0)
            subtitle_zone_h = max(safe_h * cls.TWO_ZONE_SUBTITLE_RATIO, subtitle_h)

        # Y 边界（从顶到底）
        if has_title:
            title_y_min = safe_y_max - title_zone_h
            title_y_max = safe_y_max
            content_y_max = title_y_min - cls.ZONE_SPACING_Y
        else:
            title_y_min = title_y_max = None
            content_y_max = safe_y_max - cls.ZONE_SPACING_Y  # 无标题时主内容直接到顶

        subtitle_y_min = safe_y_min
        subtitle_y_max = safe_y_min + subtitle_zone_h
        content_y_min = subtitle_y_max + cls.ZONE_SPACING_Y

        # X 边界（两栏/三栏）
        two_col_left_x_max = safe_x_min + safe_w * cls.TWO_COL_LEFT_RATIO
        two_col_right_x_min = two_col_left_x_max + cls.ZONE_SPACING

        left_w, mid_w, right_w = cls.THREE_COL_RATIOS
        three_left_x_max = safe_x_min + safe_w * left_w
        three_mid_x_min = three_left_x_max + cls.ZONE_SPACING
        three_mid_x_max = three_mid_x_min + safe_w * mid_w
        three_right_x_min = three_mid_x_max + cls.ZONE_SPACING

        result = {
            "frame_width": frame_width,
            "frame_height": frame_height,
            "has_title": has_title,
            "safe_x_min": safe_x_min,
            "safe_x_max": safe_x_max,
            "safe_y_min": safe_y_min,
            "safe_y_max": safe_y_max,
            "safe_width": safe_w,
            "safe_height": safe_h,
            "content_y_min": content_y_min,
            "content_y_max": content_y_max,
            "content_height": content_y_max - content_y_min,
            "single_x_min": safe_x_min,
            "single_x_max": safe_x_max,
            "two_left_x_min": safe_x_min,
            "two_left_x_max": two_col_left_x_max,
            "two_right_x_min": two_col_right_x_min,
            "two_right_x_max": safe_x_max,
            "graphics_x_min": two_col_right_x_min,
            "graphics_x_max": safe_x_max,
            "three_left_x_min": safe_x_min,
            "three_left_x_max": three_left_x_max,
            "three_mid_x_min": three_mid_x_min,
            "three_mid_x_max": three_mid_x_max,
            "three_right_x_min": three_right_x_min,
            "three_right_x_max": safe_x_max,
            "all_y_min": content_y_min,
            "all_y_max": content_y_max,
        }
        if has_title:
            result.update(
                {
                    "title_y_min": title_y_min,
                    "title_y_max": title_y_max,
                    "title_height": title_zone_h,
                }
            )
        result.update(
            {
                "subtitle_y_min": subtitle_y_min,
                "subtitle_y_max": subtitle_y_max,
                "subtitle_height": subtitle_zone_h,
            }
        )
        return result

    @classmethod
    def compute_column_layout(
        cls,
        zones: dict,
        num_columns: int,
        has_graphics: bool = False,
    ) -> list[dict]:
        """分栏布局算法：按比例分配 X 边界"""
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
            return [
                {"x_min": safe_x_min, "x_max": left_x_max, "width": left_w, "index": 0},
                {
                    "x_min": right_x_min,
                    "x_max": safe_x_max,
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
            return [
                {"x_min": safe_x_min, "x_max": left_x_max, "width": left_w, "index": 0},
                {"x_min": mid_x_min, "x_max": mid_x_max, "width": mid_w, "index": 1},
                {
                    "x_min": right_x_min,
                    "x_max": safe_x_max,
                    "width": right_w,
                    "index": 2,
                },
            ]
        else:
            raise ValueError(f"Unsupported num_columns: {num_columns}")

    @classmethod
    def validate_column_fit(
        cls,
        column: dict,
        content_width: float,
        content_height: float,
        max_height: float,
    ) -> tuple[bool, list[str]]:
        """校验单栏内容是否适配"""
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

    # ============================================================
    # 分栏对齐算法
    # ============================================================

    @classmethod
    def get_column_alignment(cls, column_index: int, num_columns: int = 2) -> str:
        """获取指定栏位的对齐方向"""
        if num_columns == 3:
            if column_index == 2:
                return "CENTER"
            return "LEFT"
        if num_columns == 2:
            if column_index == 1:
                return "CENTER"
            return "LEFT"
        return "LEFT"

    @classmethod
    def get_column_anchor_x(cls, column: dict, alignment: str) -> float:
        """计算内容在栏位中的锚点 X 坐标"""
        if alignment == "RIGHT":
            return column["x_max"]
        if alignment == "CENTER":
            return (column["x_min"] + column["x_max"]) / 2
        return column["x_min"]

    @classmethod
    def align_content_in_column(
        cls, mobject, column: dict, column_index: int, num_columns: int = 2
    ) -> None:
        """将内容对齐到指定栏位"""
        alignment = cls.get_column_alignment(column_index, num_columns=num_columns)
        anchor_x = cls.get_column_anchor_x(column, alignment)
        if alignment == "RIGHT":
            target_cx = anchor_x - mobject.width / 2
        else:
            target_cx = anchor_x + mobject.width / 2
        mobject.move_to([target_cx, mobject.get_y(), 0])


# ============================================================
# 模块加载时执行一次：注入所有派生常量
# 必须在 ZoneConstants 类定义完成后调用
# ============================================================
ZoneConstants._init_dynamic_bounds()
