#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LayoutScene 场景基类 - 聚合所有布局组件

职责：
- 提供场景初始化（字幕区、主内容区、图形区容器）
- 提供高层 API（place_content, place_in_zone, safe_place 等）
- 聚合 zones / engine 模块，实现符合 layout.md 的布局

严格遵循 references/layout.md 第 3.10 节实现模板
"""

from manim import Scene, VGroup, Mobject, DOWN, LEFT, RIGHT, UP, ORIGIN
from typing import List, Dict, Any, Optional, Union
import logging

from scripts.layout.constants import ZoneConstants
from scripts.layout.zones.subtitle_zone import SubtitleZone
from scripts.layout.zones.main_content_zone import MainContentZone
from scripts.layout.zones.graphics_zone import GraphicsZone
from scripts.layout.engine import LayoutEngine, LayoutMode, LayoutDecision
from scripts.layout.optimizer import LayoutOptimizer, OptimizationResult


class LayoutScene(Scene):
    """布局场景基类，提供符合规范的布局方法"""

    # 类级别标记：环境自检是否已完成
    _env_check_done: bool = False
    _env_render_path: str = ""  # 缓存渲染路径，避免每个场景都查

    def __init__(
        self,
        debug: bool = True,
        layout_mode: Optional[str] = None,  # None 表示使用类属性
        skip_env_check: bool = False,
        interactive_env_check: bool = False,
        **kwargs,
    ):
        """初始化 LayoutScene

        Args:
            debug: 调试模式（绘制区域边界等）
            layout_mode: 布局模式，None 表示使用类属性（推荐），显式传值可覆盖
            skip_env_check: True 时跳过 CJK 环境自检（CI/测试用）
            interactive_env_check: True 时自检失败弹 stdin 询问用户
                （需要 stdin 是 TTY；非 TTY 自动降级为非交互）
        """
        super().__init__(**kwargs)
        self.debug = debug
        # None 表示使用类属性（子类可定义 class layout_mode = "three_column"）
        self.layout_mode = layout_mode if layout_mode is not None else getattr(self, 'layout_mode', 'vertical')
        self._subtitle_zone: Optional[SubtitleZone] = None
        self._main_content_zone: Optional[MainContentZone] = None
        self._graphics_zone: Optional[GraphicsZone] = None
        self._layout_engine = LayoutEngine()
        self._layout_optimizer = LayoutOptimizer(on_split_callback=self._on_atom_split)
        self.speech_service = None
        # 跟踪当前显示的字幕对象，便于跨场景清理
        self._current_subtitle_mobjs: List[Mobject] = []
        # 环境自检配置
        self._skip_env_check = skip_env_check
        self._interactive_env_check = interactive_env_check

    # ============================================================
    # 环境自检（渲染前执行一次，结果缓存到类级别）
    # ============================================================

    def setup(self):
        """Manim Scene 生命周期钩子：渲染前调用

        在第一次构造 LayoutScene 时执行 CJK / LaTeX 引擎自检，
        决定推荐渲染路径。结果缓存到 LayoutScene._env_render_path。
        后续场景实例不再重复探测。

        行为：
        - skip_env_check=True：完全跳过
        - interactive_env_check=True 且检测失败：弹 stdin 询问
        - 否则：只打 warning + 建议命令
        """
        super().setup()
        if self._skip_env_check or LayoutScene._env_check_done:
            return
        try:
            from scripts.environment import (
                check_cached,
                run_setup,
                RenderPath,
            )

            if self._interactive_env_check:
                # 交互模式：检测失败时弹询问
                report = run_setup(interactive=True, force_refresh=False)
            else:
                # 自动模式：只打 warning
                report = check_cached(verbose=False)

            LayoutScene._env_render_path = report.render_path
            import logging

            logging.getLogger("manim_skill").info(
                f"[env-check] 渲染路径={report.render_path}, "
                f"推荐引擎={report.recommended_engine}, "
                f"中文字体={len(report.chinese_fonts)}个"
            )
            if report.warnings:
                for w in report.warnings:
                    logging.getLogger("manim_skill").warning(f"[env-check] {w}")
            if report.errors:
                for e in report.errors:
                    logging.getLogger("manim_skill").error(f"[env-check] {e}")
            LayoutScene._env_check_done = True
        except Exception as e:
            import logging

            logging.getLogger("manim_skill").warning(
                f"[env-check] 自检失败，使用默认渲染路径: {e}"
            )
            LayoutScene._env_check_done = True  # 失败后不再重试

        # ── debug 模式自动绘制辅助层 ──
        if self.debug:
            from manim import NumberPlane

            half_w = ZoneConstants.SCREEN_WIDTH / 2
            half_h = ZoneConstants.SCREEN_HEIGHT / 2
            ref_plane = NumberPlane(
                x_range=[-half_w, half_w, 1],
                y_range=[-half_h, half_h, 1],
                x_length=ZoneConstants.SCREEN_WIDTH,
                y_length=ZoneConstants.SCREEN_HEIGHT,
                axis_config={"color": "#888888", "stroke_width": 1},
                background_line_style={
                    "stroke_color": "#444444",
                    "stroke_width": 0.5,
                    "stroke_opacity": 0.3,
                },
            )
            self.add(ref_plane)

        # debug 模式自动绘制布局边界（layout_mode 由子类设置，框架自动处理）
        # 项目层零实现：只需设 class layout_mode = "two_column" + debug=True
        if self.debug and hasattr(self, "layout_mode") and self.layout_mode:
            self.draw_zone_boundaries(layout_mode=self.layout_mode)

    # 项目层设置 layout_mode 即可，框架自动在 setup() 中绘制 debug 边界
    layout_mode: str = "vertical"

    @classmethod
    def get_render_path(cls) -> str:
        """获取当前环境的推荐渲染路径（setup 后才有值）"""
        return cls._env_render_path

    @classmethod
    def is_minipage_available(cls) -> bool:
        """是否可走 minipage 渲染路径（xelatex + xeCJK + 中文字体）"""
        return cls._env_render_path == "tex_minipage"

    # ============================================================
    # 区域容器懒加载
    # ============================================================

    def get_subtitle_zone(
        self,
        layout_mode: str = "vertical",
        debug: Optional[bool] = None,
    ) -> SubtitleZone:
        """获取字幕区容器（懒加载）

        Args:
            layout_mode: 布局模式，决定字幕区高度（10%）
            debug: 调试模式
        """
        if self._subtitle_zone is None or getattr(
            self._subtitle_zone, "_has_title", None
        ) != (layout_mode not in ("two_column", "three_column")):
            dbg = debug if debug is not None else self.debug
            has_title = layout_mode not in ("two_column", "three_column")
            self._subtitle_zone = SubtitleZone(
                scene=self, debug=dbg, has_title=has_title
            )
        return self._subtitle_zone

    def get_main_content_zone(
        self, layout_mode: str = "vertical", debug: Optional[bool] = None
    ) -> MainContentZone:
        """获取主内容区容器（懒加载，支持动态修改布局模式）

        Args:
            layout_mode: 布局模式，可选 "vertical", "two_column", "three_column", "centered"
            debug: 调试模式
        """
        dbg = debug if debug is not None else self.debug
        if (
            self._main_content_zone is None
            or self._main_content_zone.layout_mode != layout_mode
        ):
            self._main_content_zone = MainContentZone(
                layout_mode=layout_mode, debug=dbg
            )
        return self._main_content_zone

    def get_graphics_zone(self, debug: Optional[bool] = None) -> GraphicsZone:
        """获取图形区容器（懒加载）"""
        if self._graphics_zone is None:
            dbg = debug if debug is not None else self.debug
            self._graphics_zone = GraphicsZone(debug=dbg)
        return self._graphics_zone

    # ============================================================
    # 调试模式：布局区域边界可视化
    # ============================================================

    def draw_zone_boundaries(
        self,
        layout_mode: str = "vertical",
        include_columns: bool = True,
        line_color: str = "#00FF66",
        line_dash_length: float = 0.15,
        line_dash_gap: float = 0.08,
        text_color: str = "#FFD700",
        text_size: int = 18,
        text_opacity: float = 1.0,
        label_margin: float = 0.12,
    ) -> None:
        """在场景中绘制各布局区域的边界（虚线 + 区域名/比例/坐标文字标签）

        标签布局原则（信息清晰、充分、不与内容冲突）：
        - 区域名 + 比例/高度放区域**内部中心**，绝不侵入相邻区域
        - 标题区 [2.16, 3.6] 名 → 中心 y=2.88
        - 主内容区 [-2.88, 3.6] 名 → 内部顶部 y=3.4
        - 字幕区 [-3.6, -2.88] 名 → 中心 y=-3.24
        - 分栏 (LEFT_COL/MID_COL/RIGHT_COL/GRAPHICS) 名 → 主内容区底部内部 y=-2.0
        - X 边界值 → 各区域**内部左右边缘**紧贴
        - Y 边界值 → 各区域**内部右上角**
        - 所有文字保持不透明（text_opacity=1.0），字号 18，颜色高亮
        - SAFE_AREA 同时绘制，标签放在其内部最顶部 y=3.7

        Args:
            layout_mode: 布局模式（"vertical" / "two_column" / "three_column" / "centered"）
            include_columns: 是否同时绘制分栏边界（两栏/三栏有效）
            line_color: 边界虚线颜色
            line_dash_length: 虚线段长度（Manim 单位）
            line_dash_gap: 虚线段间隔
            text_color: 文字颜色
            text_size: 边界值文字字号
            text_opacity: 文字透明度（默认 1.0 完全不透明，便于肉眼观察）
            label_margin: 文字标签与边界的内缩距离
        """
        from manim import (
            DashedLine,
            Text,
            VGroup,
        )

        # 兼容 Manim 0.20+ 的 DashedLine API
        dash_ratio = (
            line_dash_gap / (line_dash_length + line_dash_gap)
            if (line_dash_length + line_dash_gap) > 0
            else 0.5
        )

        # 两栏/三栏 → 两区（主内容 90% + 字幕 10%），无标题区
        # vertical/centered → 三区（标题 20% + 主内容 70% + 字幕 10%）
        has_title = layout_mode not in ("two_column", "three_column")
        zones = ZoneConstants.compute(
            self.camera.frame_width, self.camera.frame_height, has_title=has_title
        )
        safe_h = zones["safe_height"]

        # 收集所有需要绘制的矩形区域（含名称、比例、坐标、标签位置）
        # name_pos: (x, y) 区域名放置位置（区域内部）
        # xy_pos: (x, y) X/Y 边界值放右上角
        rects: list = []
        debug_group = VGroup()

        rects.append(
            {
                "name": "SAFE_AREA",
                "meta": f"h={safe_h:.2f}",
                "x_min": zones["safe_x_min"],
                "x_max": zones["safe_x_max"],
                "y_min": zones["safe_y_min"],
                "y_max": zones["safe_y_max"],
                # SAFE_AREA 标签放主内容区左下角内侧 (x=-5.0, y=-1.7)，避开边界值标签
                "name_pos": (zones["safe_x_min"] + 1.75, zones["safe_y_min"] + 1.1),
                "show_xy_inside": True,
            }
        )
        if "title_y_min" in zones:
            rects.append(
                {
                    "name": "TITLE",
                    "meta": f"[20%] h={zones['title_height']:.2f}",
                    "x_min": zones["safe_x_min"],
                    "x_max": zones["safe_x_max"],
                    "y_min": zones["title_y_min"],
                    "y_max": zones["title_y_max"],
                    "name_pos": (
                        (zones["safe_x_min"] + zones["safe_x_max"]) / 2,
                        (zones["title_y_min"] + zones["title_y_max"]) / 2,
                    ),
                    "show_xy_inside": True,
                }
            )
        # 字幕区统一占 10%（两区/三区/vertical/centered 均已统一为 9:1）
        subtitle_pct = "10%"
        rects.append(
            {
                "name": "SUBTITLE",
                "meta": f"[{subtitle_pct}] h={zones['subtitle_height']:.2f}",
                "x_min": zones["safe_x_min"],
                "x_max": zones["safe_x_max"],
                "y_min": zones["subtitle_y_min"],
                "y_max": zones["subtitle_y_max"],
                # SUBTITLE 标签放字幕区右上角内部 (x=4.0, y=-2.20)，避开字幕行 (slot_0/slot_1)
                "name_pos": (
                    zones["safe_x_max"] - 2.75,
                    zones["subtitle_y_max"] - 0.08,
                ),
                "show_xy_inside": True,
            }
        )

        if layout_mode == "two_column":
            rects.append(
                {
                    "name": "MAIN_CONTENT",
                    "meta": f"[90%] h={zones['content_height']:.2f}",
                    "x_min": zones["two_left_x_min"],
                    "x_max": zones["two_left_x_max"],
                    "y_min": zones["content_y_min"],
                    "y_max": zones["content_y_max"],
                    # 主内容区标签放内部顶部 (y=2.45)，绝不侵入字幕区
                    "name_pos": (
                        (zones["two_left_x_min"] + zones["two_left_x_max"]) / 2,
                        zones["content_y_max"] - 0.2,
                    ),
                    "show_xy_inside": True,
                }
            )
            rects.append(
                {
                    "name": "GRAPHICS",
                    "meta": f"[同高] h={zones['content_height']:.2f}",
                    "x_min": zones["graphics_x_min"],
                    "x_max": zones["graphics_x_max"],
                    "y_min": zones["content_y_min"],
                    "y_max": zones["content_y_max"],
                    "name_pos": (
                        (zones["graphics_x_min"] + zones["graphics_x_max"]) / 2,
                        zones["content_y_max"] - 0.2,
                    ),
                    "show_xy_inside": True,
                }
            )
            # 分栏竖线：画在 MAIN_CONTENT 右边界，贯穿字幕区上界到内容区下界
            col_divider_x = zones["two_left_x_max"]
            col_divider = DashedLine(
                [col_divider_x, zones["subtitle_y_max"], 0],
                [col_divider_x, zones["content_y_max"], 0],
                color=line_color,
                stroke_width=2.0,
                dash_length=line_dash_length,
                dashed_ratio=dash_ratio,
            )
            debug_group.add(col_divider)
        elif layout_mode == "three_column":
            # 绘制两条分栏竖线
            # 第一条：左栏和中栏之间的分隔线
            col_divider1_x = zones["three_left_x_max"]
            col_divider1 = DashedLine(
                [col_divider1_x, zones["subtitle_y_max"], 0],
                [col_divider1_x, zones["content_y_max"], 0],
                color=line_color,
                stroke_width=2.0,
                dash_length=line_dash_length,
                dashed_ratio=dash_ratio,
            )
            debug_group.add(col_divider1)

            # 第二条：中栏和右栏之间的分隔线
            col_divider2_x = zones["three_mid_x_max"]
            col_divider2 = DashedLine(
                [col_divider2_x, zones["subtitle_y_max"], 0],
                [col_divider2_x, zones["content_y_max"], 0],
                color=line_color,
                stroke_width=2.0,
                dash_length=line_dash_length,
                dashed_ratio=dash_ratio,
            )
            debug_group.add(col_divider2)

            for col_name, x_min, x_max in [
                ("LEFT_COL", zones["three_left_x_min"], zones["three_left_x_max"]),
                ("MID_COL", zones["three_mid_x_min"], zones["three_mid_x_max"]),
                ("RIGHT_COL", zones["three_right_x_min"], zones["three_right_x_max"]),
            ]:
                rects.append(
                    {
                        "name": col_name,
                        "meta": f"h={zones['content_height']:.2f}",
                        "x_min": x_min,
                        "x_max": x_max,
                        "y_min": zones["content_y_min"],
                        "y_max": zones["content_y_max"],
                        "name_pos": ((x_min + x_max) / 2, zones["content_y_max"] - 0.2),
                        "show_xy_inside": True,
                    }
                )
        else:
            rects.append(
                {
                    "name": "MAIN_CONTENT",
                    "meta": f"[70%] h={zones['content_height']:.2f}",
                    "x_min": zones["single_x_min"],
                    "x_max": zones["single_x_max"],
                    "y_min": zones["content_y_min"],
                    "y_max": zones["content_y_max"],
                    "name_pos": (
                        (zones["single_x_min"] + zones["single_x_max"]) / 2,
                        zones["content_y_max"] - 0.2,
                    ),
                    "show_xy_inside": True,
                }
            )

        for rect in rects:
            x_min, x_max = rect["x_min"], rect["x_max"]
            y_min, y_max = rect["y_min"], rect["y_max"]
            name = rect["name"]
            meta = rect.get("meta", "")
            name_x, name_y = rect["name_pos"]

            # 4 条虚线边界（上 / 下 / 左 / 右）— 每条线都是区域边界
            top = DashedLine(
                [x_min, y_max, 0],
                [x_max, y_max, 0],
                color=line_color,
                stroke_width=2.0,
                dash_length=line_dash_length,
                dashed_ratio=dash_ratio,
            )
            bottom = DashedLine(
                [x_min, y_min, 0],
                [x_max, y_min, 0],
                color=line_color,
                stroke_width=2.0,
                dash_length=line_dash_length,
                dashed_ratio=dash_ratio,
            )
            left = DashedLine(
                [x_min, y_min, 0],
                [x_min, y_max, 0],
                color=line_color,
                stroke_width=2.0,
                dash_length=line_dash_length,
                dashed_ratio=dash_ratio,
            )
            right = DashedLine(
                [x_max, y_min, 0],
                [x_max, y_max, 0],
                color=line_color,
                stroke_width=2.0,
                dash_length=line_dash_length,
                dashed_ratio=dash_ratio,
            )
            debug_group.add(top, bottom, left, right)

            # ── 区域名 + 元信息（放区域内部中心/指定位置）──
            name_label = Text(
                f"{name}  {meta}",
                font_size=text_size,
                color=text_color,
                weight="BOLD",
            )
            name_label.set_opacity(text_opacity)
            name_label.move_to([name_x, name_y, 0])
            debug_group.add(name_label)

            # X 边界值（放区域内部左右边缘紧贴）
            x_min_label = Text(
                f"x={x_min:.2f}",
                font_size=text_size,
                color=text_color,
                weight="BOLD",
            ).set_opacity(text_opacity)
            x_min_label.move_to([x_min + label_margin, (y_min + y_max) / 2, 0])

            x_max_label = Text(
                f"x={x_max:.2f}",
                font_size=text_size,
                color=text_color,
                weight="BOLD",
            ).set_opacity(text_opacity)
            x_max_label.move_to([x_max - label_margin, (y_min + y_max) / 2, 0])
            debug_group.add(x_min_label, x_max_label)

            # Y 边界值（放区域内部右上角紧贴；错开 Y 避免与 x_max 重叠）
            y_min_label = Text(
                f"y={y_min:.2f}",
                font_size=text_size,
                color=text_color,
                weight="BOLD",
            ).set_opacity(text_opacity)
            y_min_label.move_to([x_max - label_margin * 5, y_min + label_margin, 0])

            y_max_label = Text(
                f"y={y_max:.2f}",
                font_size=text_size,
                color=text_color,
                weight="BOLD",
            ).set_opacity(text_opacity)
            y_max_label.move_to([x_max - label_margin * 5, y_max - label_margin, 0])
            debug_group.add(y_min_label, y_max_label)

        # 把整个调试组添加到场景
        self._add_recursive(debug_group)
        self._debug_overlay = debug_group

    # ============================================================
    # 内容放置 API（符合 layout.md 第 3.10 节）
    # ============================================================

    def place_in_main_zone(
        self,
        content: Union[Mobject, VGroup],
        layout_mode: str = "vertical",
    ) -> VGroup:
        """将内容放置在主内容区内（仅使用 arrange + zone.place_content）

        Args:
            content: 单个元素或元素组
            layout_mode: 布局模式 (vertical/two_column/three_column/centered)

        Returns:
            已定位的 VGroup
        """
        if not isinstance(content, VGroup):
            content = VGroup(content)

        zone = self.get_main_content_zone(layout_mode)

        if layout_mode == "centered":
            content.arrange(DOWN, buff=ZoneConstants.ROW_BUFF, center=True)
        else:
            content.arrange(DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT)

        return zone.place_content(content)

    def place_graphics(self, graphics: Mobject) -> Mobject:
        """将图形放置在图形区中心

        Args:
            graphics: 图形对象

        Returns:
            已定位的图形对象
        """
        zone = self.get_graphics_zone()
        return zone.place_content(graphics)

    def place_two_column(
        self,
        left_content: Mobject,
        right_content: Mobject,
        add_to_scene: bool = True,
    ) -> VGroup:
        """两栏布局：左内容区 + 右图形区

        内置**事前预检 + 事后校验**双层防护：
        1. **事前预检**（放置前）：逐对象测量宽度/高度，超限时自动缩放或换行
        2. **事后校验**（放置后）：validate_layout() 检测溢出，触发降级链

        Args:
            left_content: 左栏内容（公式/文字）
            right_content: 右栏图形
            add_to_scene: 是否自动添加到场景（默认 True）。设为 False 时，
                          调用者需自行控制添加时机（如配合 FadeIn 使用）

        Returns:
            包含两栏的 VGroup
        """
        # ── 事前预检：获取各栏可用尺寸 ──
        left_zone = self.get_main_content_zone(layout_mode="two_column")
        right_zone = self.get_graphics_zone()
        left_col_width = left_zone.x_max - left_zone.x_min
        right_col_width = right_zone.x_max - right_zone.x_min
        left_col_height = left_zone.y_max - left_zone.y_min
        right_col_height = right_zone.y_max - right_zone.y_min

        # 左栏：宽度预检+自动调整（文本/公式需要检查换行）
        left_content = self._precheck_mobject(
            left_content,
            max_width=left_col_width * 0.95,
            max_height=left_col_height * 0.9,
        )

        # 右栏：纯图形组跳过预检，由 GraphicsZone.place_content 统一处理 80% 缩放
        right_content = self._precheck_mobject(
            right_content,
            max_width=right_col_width * 0.95,
            max_height=right_col_height * 0.9,
            skip_for_graphics_zone=True,
        )

        # 左栏：左栏内的内容左对齐 + 垂直居中（在左栏区域内）
        left_group = VGroup(left_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT
        )
        left_group = left_zone.place_content(left_group, h_align="left")

        # 右栏：右栏内的内容水平居中 + 垂直居中（在图形区区域内）
        right_group = VGroup(right_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT
        )
        right_group = right_zone.place_content(right_group, h_align="center")

        # 原实现仅将两栏上移到最高栏顶部位置，未校验对齐后是否仍完全
        # 在 zone 内。当任一栏高度 > zone 高度时，顶部对齐后底部会越界
        # （content_top 在 zone_y_max 但 content_bottom 超出 zone_y_min）。
        # 现改为先尝试顶部对齐，对齐后立即校验，若越界则降级到居中/底部对齐。

        # 最严格下界 = max(zones.y_min)（各栏中最深的底部）
        # 最严格上界 = min(zones.y_max)（各栏中最浅的顶部）
        # 原 min() 误用为"最宽松下界"，会在 zone 高度不同时引发底部越界漏检。
        zone_y_min = max(left_zone.y_min, right_zone.y_min)
        zone_y_max = min(left_zone.y_max, right_zone.y_max)
        self._align_columns_within_zone(
            [left_group, right_group],
            zone_y_min=zone_y_min,
            zone_y_max=zone_y_max,
            prefer="top",
        )

        # 组装最终结果
        result = VGroup(left_group, right_group)

        # ── 事后校验：放置后必须校验，溢出时自动走优化链 ──
        all_placed = [left_group, right_group]

        # 之前 region="content" 实际是单栏边界，与多栏布局脱节，
        # 导致多栏内整体溢出/穿栏越界无法被捕获。
        # 同时透传 column_layout，确保动态分栏边界优先于静态常量。
        zones = ZoneConstants.compute(self.camera.frame_width, self.camera.frame_height)
        col_layout_list = ZoneConstants.compute_column_layout(
            zones, num_columns=2, has_graphics=True
        )

        # 让 union 校验的语义明确为"全局安全区"而非"左栏"。
        col_layout_for_union = {
            "x_min": ZoneConstants.SAFE_AREA_X_MIN,
            "x_max": ZoneConstants.SAFE_AREA_X_MAX,
            "width": ZoneConstants.SAFE_AREA_X_MAX - ZoneConstants.SAFE_AREA_X_MIN,
        }
        violations = self.validate_layout(
            all_placed,
            region="safe_area",
            column_layout=col_layout_for_union,
        )
        if violations:
            # 获取当前分栏信息供优化器使用
            opt_result = self.handle_violation(
                violations, all_placed, column_layout=col_layout_for_union
            )
            if opt_result and not opt_result.is_successful:
                logging.warning(
                    "[place_two_column] 自动优化失败，建议拆分原子或缩小内容"
                )

        # 上面 union 校验对单栏内部 "不超出本栏" 不敏感（X 边界跨度大）。
        # 这里用每栏各自的 X 边界再校验一次，捕获"左栏内容溢出到右栏"等穿栏越界。
        per_col_violations: list = []
        per_col_violations.extend(
            self.validate_layout(
                [left_group],
                region="content_two_col_left",
            )
        )
        per_col_violations.extend(
            self.validate_layout(
                [right_group],
                region="content_two_col_right",
                column_layout=col_layout_list,  # 同上
            )
        )
        if per_col_violations:
            logging.warning(
                f"[place_two_column] 按栏校验发现 {len(per_col_violations)} 项违规，"
                "尝试自动优化"
            )

            # 避免优化器只针对中栏做缩放而丢失对左/右栏违规的处理能力。
            self.handle_violation(
                per_col_violations, all_placed, column_layout=col_layout_list
            )

        # 之前仅 `self.add(result)` 但 result 是 VGroup(VGroup, VGroup) 嵌套结构，
        # VGroup 不会自动 add submobjects 到 scene，导致 VGroup 自身渲染为空、
        # 主内容区不显示（仅字幕可见）。

        if add_to_scene:
            self._add_recursive(result)
        return result

    def _add_recursive(self, mobject: Mobject) -> None:
        """递归 add mobject 及其所有子对象到场景中

        Manim 的 VGroup.add 不会把 submobjects 自动加入 scene.mobjects，
        必须显式 add 才能渲染。本方法递归展平嵌套 VGroup，避免渲染空 VGroup。
        """
        if mobject is None:
            return
        self.add(mobject)
        if hasattr(mobject, "submobjects") and mobject.submobjects:
            for sub in mobject.submobjects:
                self._add_recursive(sub)

    def place_three_column(
        self,
        left_content: Mobject,
        mid_content: Mobject,
        right_content: Mobject,
    ) -> VGroup:
        """三栏布局：左（步骤）+ 中（公式）+ 右（图形）

        内置**事前预检**：三栏内容在放置前均做宽度/高度检测，
        超限时自动换行（文本）或缩放（图形）。中栏保留原有的
        scale-to-fit 作为第二道防线。


        place_content 兜底缩放。当任一栏（如中栏 MathTex）超宽触发缩放时，
        main_zone 缩放会波及到 left_col（在同一 main_zone 内），导致左栏
        文本字号被缩到看不见。
        现改为：每栏独立缩放 + 独立定位到各自 X 边界，不共用 main_zone
        作为缩放参考系。

        Args:
            left_content: 左栏内容（步骤说明/概念）
            mid_content: 中栏内容（公式）
            right_content: 右栏图形

        Returns:
            包含三栏的 VGroup
        """
        # 获取各栏区域
        main_zone = self.get_main_content_zone(layout_mode="three_column")
        right_zone = self.get_graphics_zone()

        main_width = main_zone.x_max - main_zone.x_min
        main_height = main_zone.y_max - main_zone.y_min

        # 左栏独立边界
        left_x_min = ZoneConstants.THREE_COL_LEFT_X_MIN
        left_x_max = ZoneConstants.THREE_COL_LEFT_X_MAX
        left_col_width = left_x_max - left_x_min  # 4.55
        # 中栏独立边界
        mid_x_min = ZoneConstants.THREE_COL_MID_X_MIN
        mid_x_max = ZoneConstants.THREE_COL_MID_X_MAX
        mid_col_width = mid_x_max - mid_x_min  # 4.05
        # 右栏独立边界
        right_col_width = right_zone.x_max - right_zone.x_min
        right_col_height = right_zone.y_max - right_zone.y_min

        left_content = self._precheck_mobject(
            left_content, max_width=left_col_width * 0.92, max_height=main_height * 0.9
        )
        mid_content = self._precheck_mobject(
            mid_content, max_width=mid_col_width * 0.92, max_height=main_height * 0.9
        )
        right_content = self._precheck_mobject(
            right_content,
            max_width=right_col_width * 0.95,
            max_height=right_col_height * 0.9,
        )

        # 左栏：左对齐到 THREE_COL_LEFT_X_MIN
        left_col = VGroup(left_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF * 0.8, aligned_edge=LEFT
        )
        # 左栏独立防超宽缩放（仅在 left_col 实际超过 left_col_width 时触发）

        if left_col.width > left_col_width:
            scale_factor = (left_col_width * 0.95) / left_col.width
            if scale_factor < 1.0:
                left_col.scale(scale_factor, about_point=left_col.get_center())
                logging.info(
                    f"[place_three_column] 左栏独立缩放: ×{scale_factor:.2f} "
                    f"(left_col_width={left_col_width:.2f}, "
                    f"content_width={left_col.width:.2f})"
                )
        # 左对齐到左栏左边界
        left_col.move_to([left_x_min + left_col.width / 2, main_zone.center_y, 0])

        # 中栏：左对齐到 THREE_COL_MID_X_MIN
        mid_col = VGroup(mid_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT
        )
        # 中栏独立防超宽缩放
        if mid_col.width > mid_col_width:
            scale_factor = (mid_col_width * 0.95) / mid_col.width
            if scale_factor < 1.0:
                mid_col.scale(scale_factor, about_point=mid_col.get_center())
                logging.info(
                    f"[place_three_column] 中栏独立缩放: ×{scale_factor:.2f} "
                    f"(mid_col_width={mid_col_width:.2f}, "
                    f"content_width={mid_col.width:.2f})"
                )
        # 中栏左对齐到中栏左边界
        mid_col.move_to([mid_x_min + mid_col.width / 2, main_zone.center_y, 0])

        # 右栏：右栏内的内容水平居中 + 垂直居中（在 graphics_zone 内）
        right_col = VGroup(right_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT
        )
        # 右栏独立防超宽缩放（仅在 right_col 实际超过 right_col_width 时触发）
        if right_col.width > right_col_width:
            scale_factor = (right_col_width * 0.95) / right_col.width
            if scale_factor < 1.0:
                right_col.scale(scale_factor, about_point=right_col.get_center())
                logging.info(
                    f"[place_three_column] 右栏独立缩放: ×{scale_factor:.2f} "
                    f"(right_col_width={right_col_width:.2f}, "
                    f"content_width={right_col.width:.2f})"
                )
        right_col = right_zone.place_content(right_col, h_align="center")

        # 在 zone 内。现改为先尝试顶部对齐，越界则降级到居中/底部对齐。

        # 最严格下界 = max(zones.y_min)，最严格上界 = min(zones.y_max)。
        zone_y_min = max(main_zone.y_min, right_zone.y_min)
        zone_y_max = min(main_zone.y_max, right_zone.y_max)
        self._align_columns_within_zone(
            [left_col, mid_col, right_col],
            zone_y_min=zone_y_min,
            zone_y_max=zone_y_max,
            prefer="top",
        )

        # 同时调整校验顺序为 per-col → union：先按栏捕捉穿栏越界，
        # 再做整体 union 校验，避免 union 误报先污染导致按栏校验被跳过。
        all_placed = [left_col, mid_col, right_col]
        zones = ZoneConstants.compute(self.camera.frame_width, self.camera.frame_height)
        col_layout_list = ZoneConstants.compute_column_layout(
            zones, num_columns=3, has_graphics=True
        )

        per_col_violations: list = []
        per_col_violations.extend(
            self.validate_layout(
                [left_col],
                region="content_three_col_left",
            )
        )
        per_col_violations.extend(
            self.validate_layout(
                [mid_col],
                region="content_three_col_mid",
                column_layout=col_layout_list,
            )
        )
        per_col_violations.extend(
            self.validate_layout(
                [right_col],
                region="content_three_col_right",
                column_layout=col_layout_list,
            )
        )
        if per_col_violations:
            logging.warning(
                f"[place_three_column] 按栏校验发现 {len(per_col_violations)} 项违规，"
                "尝试自动优化"
            )

            # 对左/右栏违规的处理能力。优化器 optimize() 期望接受 List[Dict]
            # （整段三栏布局），可针对不同违规匹配对应栏位做缩放。
            self.handle_violation(
                per_col_violations, all_placed, column_layout=col_layout_list
            )

        # union 校验对单栏内部"不超出本栏"不敏感，但能捕获整体越出安全区。

        # 只是左栏），让 union 校验的语义明确为"全局安全区"而非"左栏"。
        col_layout_for_union = {
            "x_min": ZoneConstants.SAFE_AREA_X_MIN,
            "x_max": ZoneConstants.SAFE_AREA_X_MAX,
            "width": ZoneConstants.SAFE_AREA_X_MAX - ZoneConstants.SAFE_AREA_X_MIN,
        }
        violations = self.validate_layout(
            all_placed,
            region="safe_area",
            column_layout=col_layout_for_union,
        )
        if violations:
            opt_result = self.handle_violation(
                violations, all_placed, column_layout=col_layout_for_union
            )
            if opt_result and not opt_result.is_successful:
                logging.warning(
                    "[place_three_column] 自动优化失败，建议拆分原子或缩小内容"
                )

        result = VGroup(left_col, mid_col, right_col)
        self._add_recursive(result)
        return result

    def safe_place(self, mobject: Mobject) -> Mobject:
        """安全放置：确保不超出安全区域

        根据 layout.md 第 7 节，当元素超出安全边界时整体移动或缩放。


        导致同时超出上下界时只处理了一个。这里分别记录下界（向上 shift）
        和上界（向下 shift），最终对 x/y 各取一个合并的 shift 量。


        必须先按比例 scale 到安全区的 95% 边界内再 shift。
        同时将变量名改为无歧义命名（shift_top_to_y_max / shift_bottom_to_y_min），
        避免 up/down 含义混淆（down 在此上下文中是负值）。
        """
        safe_x_min = ZoneConstants.SAFE_AREA_X_MIN
        safe_x_max = ZoneConstants.SAFE_AREA_X_MAX
        safe_y_min = ZoneConstants.SAFE_AREA_Y_MIN
        safe_y_max = ZoneConstants.SAFE_AREA_Y_MAX
        safe_w = safe_x_max - safe_x_min
        safe_h = safe_y_max - safe_y_min

        # 单纯 shift 无法 fit 这种 case。
        obj_w = mobject.width
        obj_h = mobject.height
        if obj_w > safe_w or obj_h > safe_h:
            scale_x = (safe_w * 0.95) / obj_w if obj_w > safe_w else 1.0
            scale_y = (safe_h * 0.95) / obj_h if obj_h > safe_h else 1.0
            scale_factor = min(scale_x, scale_y, 1.0)
            if scale_factor < 1.0:
                mobject.scale(scale_factor, about_point=mobject.get_center())
                logging.info(
                    f"[safe_place] 内容尺寸超安全区，先缩放至 95% 边界: "
                    f"×{scale_factor:.3f} (原始 w={obj_w:.2f} h={obj_h:.2f})"
                )

        bottom = mobject.get_bottom()[1]
        top = mobject.get_top()[1]
        left = mobject.get_left()[0]
        right = mobject.get_right()[0]

        # "shift_*_to_*" 明确表示把 * 边移到 * 目标 Y/X 坐标。
        # shift_bottom_to_y_min > 0 表示把底边向上移到安全下界（正向上）
        # shift_top_to_y_max    < 0 表示把顶边向下移到安全上界（负向上）
        shift_bottom_to_y_min = 0.0  # 把内容底边对齐到安全下界所需的 Y 位移（向上为正）
        shift_top_to_y_max = 0.0  # 把内容顶边对齐到安全上界所需的 Y 位移（向下为负）
        shift_left_to_x_min = 0.0  # 把内容左边缘对齐到安全左界所需的 X 位移（向右为正）
        shift_right_to_x_max = (
            0.0  # 把内容右边缘对齐到安全右界所需的 X 位移（向左为负）
        )

        # 下界：内容底部低于安全下界 → 向上 shift（数值为正）
        if bottom < safe_y_min:
            shift_bottom_to_y_min = safe_y_min - bottom
        # 上界：内容顶部高于安全上界 → 向下 shift（数值为负）
        if top > safe_y_max:
            shift_top_to_y_max = safe_y_max - top
        # 左界：内容左边缘小于安全左界 → 向右 shift（数值为正）
        if left < safe_x_min:
            shift_left_to_x_min = safe_x_min - left
        # 右界：内容右边缘大于安全右界 → 向左 shift（数值为负）
        if right > safe_x_max:
            shift_right_to_x_max = safe_x_max - right

        # 综合 X / Y 的方向，叠加 shift（极端情况下上下同时越界时取较大约束）

        # shift_bottom_to_y_min 必为非负，shift_top_to_y_max 必为非正
        # 两者方向相反，简单相加取综合净 shift（极端双越界时取较大绝对值一侧）
        if shift_bottom_to_y_min != 0.0 and shift_top_to_y_max != 0.0:
            # 同时越上下界：取绝对值较大方向作为净 shift
            if abs(shift_bottom_to_y_min) >= abs(shift_top_to_y_max):
                shift_y = shift_bottom_to_y_min
            else:
                shift_y = shift_top_to_y_max
        elif shift_bottom_to_y_min != 0.0:
            shift_y = shift_bottom_to_y_min
        else:
            shift_y = shift_top_to_y_max

        if shift_left_to_x_min != 0.0 and shift_right_to_x_max != 0.0:
            if abs(shift_left_to_x_min) >= abs(shift_right_to_x_max):
                shift_x = shift_left_to_x_min
            else:
                shift_x = shift_right_to_x_max
        elif shift_left_to_x_min != 0.0:
            shift_x = shift_left_to_x_min
        else:
            shift_x = shift_right_to_x_max

        if shift_x != 0.0 or shift_y != 0.0:
            mobject.shift(RIGHT * shift_x + UP * shift_y)

        return mobject

    def scale_to_fit_zone(
        self,
        mobject: Mobject,
        region: str = "graphics",
    ) -> Mobject:
        """将图形等比缩放至合理尺寸，充分利用分栏空间（M7 强制规则实现）

        策略：
        1. 计算缩放系数使图形最终占分栏宽高的 80%（取宽/高限制中较小者，确保不溢出）
        2. 除零时保持图形原尺寸

        Args:
            mobject: 待缩放的图形对象（VGroup 或任意 Mobject）
            region: 目标区域标识，"graphics"（图形区，默认）或 "content"（主内容区）

        Returns:
            缩放后的 mobject（链式调用）
        """
        if region == "graphics":
            zone = self.get_graphics_zone()
        elif region == "content":
            zone = self.get_main_content_zone(layout_mode=self.layout_mode)
        else:
            zone = self.get_main_content_zone(layout_mode=self.layout_mode)

        zone_w = zone.x_max - zone.x_min
        zone_h = zone.y_max - zone.y_min
        zone_center = zone.get_center()

        # 先获取缩放前的原始尺寸
        fig_w = mobject.width
        fig_h = mobject.height

        # 避免除零
        if fig_w < 1e-6 or fig_h < 1e-6:
            return mobject

        # 直接缩放至分栏宽高的 80%（允许图形显著放大或缩小）
        scale = min((zone_w * 0.80) / fig_w, (zone_h * 0.80) / fig_h) if fig_w > 1e-6 and fig_h > 1e-6 else 1.0

        # scale 在 0.5~1.0 之间：不缩小，保留原始尺寸
        if scale != 1.0:
            about = mobject.get_center()
            mobject.scale(scale, about_point=about)
            logging.info(
                f"[scale_to_fit_zone] region={region}, scale={scale:.2f} "
                f"(原始 w={fig_w:.2f} h={fig_h:.2f} → 目标占分栏 80% (w={zone_w*0.80:.2f} h={zone_h*0.80:.2f}))"
            )

        # 居中到目标区域
        mobject.move_to(zone_center)
        return mobject

    def _align_columns_within_zone(
        self,
        columns: List[Mobject],
        zone_y_min: float,
        zone_y_max: float,
        prefer: str = "top",
    ) -> str:
        """多栏顶部对齐 + 边界校验

        顶部对齐后立即校验 top_overflow / bottom_overflow。
        越界则回退到原位置，尝试下一优先级对齐方式。
        优先级：top → center → bottom（或按 prefer 调整）。
        所有方式都越界（内容已超出 zone 高度）→ 按比例缩放兜底。

        Args:
            columns: 待对齐的栏对象列表（每个已是定位好的 Mobject）
            zone_y_min: zone 底边界
            zone_y_max: zone 顶边界
            prefer: 首选对齐方式，"top" / "center" / "bottom"

        Returns:
            最终采用的对齐方式（"top" / "center" / "bottom" / "scaled"）
        """
        if not columns:
            return prefer

        # 构造对齐方式优先级队列
        if prefer == "top":
            align_priority = ["top", "center", "bottom"]
        elif prefer == "center":
            align_priority = ["center", "top", "bottom"]
        elif prefer == "bottom":
            align_priority = ["bottom", "center", "top"]
        else:
            align_priority = ["top", "center", "bottom"]

        # 记录原始位置（用于越界时回退）
        original_positions = [(c.get_center()[0], c.get_center()[1]) for c in columns]

        for align_mode in align_priority:
            if align_mode == "top":
                # 顶部对齐：所有栏的顶部对齐到最高栏顶部（保持 Y 向上移动）
                top_y = max(c.get_top()[1] for c in columns)
                for c in columns:
                    c.shift(UP * (top_y - c.get_top()[1]))
            elif align_mode == "center":
                # 居中对齐：所有栏中心对齐到 zone 中线
                center_y = (zone_y_min + zone_y_max) / 2
                for c in columns:
                    c.move_to([c.get_center()[0], center_y, 0])
            else:  # bottom
                # 底部对齐：所有栏底部对齐到 zone_y_min
                bottom_y_target = zone_y_min
                for c in columns:
                    shift_amount = bottom_y_target - c.get_bottom()[1]
                    c.shift(UP * shift_amount)

            top_overflow = max(c.get_top()[1] for c in columns) - zone_y_max
            bottom_overflow = zone_y_min - min(c.get_bottom()[1] for c in columns)
            # 1e-2 容差，避免浮点误差误判
            if top_overflow <= 0.01 and bottom_overflow <= 0.01:
                if align_mode != prefer:
                    logging.info(
                        f"[_align_columns_within_zone] 顶部对齐越界，"
                        f"降级到 {align_mode} 对齐（top_overflow={top_overflow:.2f}, "
                        f"bottom_overflow={bottom_overflow:.2f}）"
                    )
                return align_mode

            # 越界 → 回退到原位置，尝试下一对齐方式
            for c, (cx, cy) in zip(columns, original_positions):
                c.move_to([cx, cy, 0])
            logging.debug(
                f"[_align_columns_within_zone] {align_mode} 对齐越界，"
                f"回退后尝试下一优先级 "
                f"（top_overflow={top_overflow:.2f}, "
                f"bottom_overflow={bottom_overflow:.2f}）"
            )

        # 兜底：按比例缩放到 zone 高度的 95% 后再顶部对齐
        highest_top = max(c.get_top()[1] for c in columns)
        lowest_bottom = min(c.get_bottom()[1] for c in columns)
        content_height = highest_top - lowest_bottom
        zone_height = zone_y_max - zone_y_min
        if content_height > zone_height and content_height > 0:
            scale_factor = (zone_height * 0.95) / content_height
            for c in columns:
                c.scale(scale_factor, about_point=c.get_center())
            # 缩放后再次顶部对齐
            top_y = max(c.get_top()[1] for c in columns)
            for c in columns:
                c.shift(UP * (top_y - c.get_top()[1]))
            logging.warning(
                f"[_align_columns_within_zone] 所有对齐方式越界，"
                f"已按 ×{scale_factor:.2f} 缩放兜底"
            )
            return "scaled"

        # 极端情况：所有对齐 + 缩放都未生效（zone 高度 ≤ 0 等异常）
        return prefer

    def _is_pure_graphics_group(self, mobject: "Mobject") -> bool:
        """判断 VGroup 是否为纯图形组（不含文本/公式）

        Args:
            mobject: 待检查的 Mobject

        Returns:
            True 如果是纯图形 VGroup，False 否则
        """
        from manim import Text, MathTex, VGroup

        if not isinstance(mobject, VGroup):
            return False

        text_types = (Text, MathTex)
        try:
            from manim import MarkupText
            text_types = (Text, MathTex, MarkupText)
        except ImportError:
            pass

        for sub in mobject.get_family():
            if isinstance(sub, text_types):
                return False

        return True

    def _precheck_mobject(
        self,
        mobject: Mobject,
        max_width: float,
        max_height: float,
        skip_for_graphics_zone: bool = False,
    ) -> Mobject:
        """事前预检单个 Mobject 的尺寸，超限时自动调整

        处理策略（按对象类型分层）：
        1. **VGroup**：递归检查子元素，对每个超宽/超高的子元素分别处理
           - 若 skip_for_graphics_zone=True 且为纯图形组，跳过预检（由目标 zone 处理）
        2. **Text / MathTex**：
           - 宽度超限 → 调用 LayoutOptimizer 的换行逻辑重建为多行
           - 换行后仍超限 → 缩小 font_size
        3. **图形类 Mobject**（Arrow, Polygon 等）：
           - 宽度或高度任一超限 → scale_to_fit 到可用范围内

        Args:
            mobject: 待检查的 Mobject
            max_width: 允许的最大宽度（Manim 单位）
            max_height: 允许的最大高度（Manim 单位）
            skip_for_graphics_zone: 若为 True，VGroup 跳过预检（用于图形区由 place_content 统一处理）

        Returns:
            调整后的 Mobject（可能被原地修改，也可能返回原对象）
        """
        from manim import Text, MathTex

        # VGroup：递归处理子元素
        if isinstance(mobject, VGroup) and len(mobject.submobjects) > 0:

            # skip_for_graphics_zone=True 时，跳过整个 VGroup 的预检，
            # 由 GraphicsZone.place_content 统一处理 80% 缩放
            if skip_for_graphics_zone:
                return mobject

            # 替代直接覆盖属性 `mobject.submobjects = adjusted_submobjs`，
            # 后者在部分 VGroup 实现中会丢失父对象属性（h_align、layout_mode、name 等）。
            adjusted_submobjs = []
            for sub in mobject.submobjects:
                adjusted = self._precheck_mobject(
                    sub, max_width, max_height, skip_for_graphics_zone
                )
                adjusted_submobjs.append(adjusted)
            # 保留 VGroup 引用：原位更新子对象列表，避免属性丢失
            mobject.submobjects[:] = adjusted_submobjs

            # 整体仍超限时按比例 scale 一次（兜底第二道防线）
            current_w = mobject.width
            current_h = mobject.height
            if current_w > max_width or current_h > max_height:
                scale_x = max_width / current_w if current_w > max_width else 1.0
                scale_y = max_height / current_h if current_h > max_height else 1.0
                scale_factor = min(scale_x, scale_y, 0.95)
                if scale_factor < 1.0:
                    mobject.scale(scale_factor, about_point=mobject.get_center())
                    logging.info(
                        f"[_precheck_mobject] VGroup 兜底缩放: "
                        f"×{scale_factor:.2f} (子对象调整后整体 "
                        f"w={current_w:.2f} h={current_h:.2f} 仍超限)"
                    )
            return mobject

        obj_width = mobject.width
        obj_height = mobject.height

        # 未超限，直接返回原对象
        if obj_width <= max_width and obj_height <= max_height:
            return mobject

        # 文本/公式对象：优先换行，其次缩放
        if isinstance(mobject, (Text, MathTex)):
            # 先尝试换行
            fake_violation = {
                "type": (
                    "WIDTH_OVERFLOW" if obj_width > max_width else "HEIGHT_OVERFLOW"
                ),
                "column_width": max_width,
            }
            optimizer = LayoutOptimizer()
            wrapped = optimizer._apply_wrap([mobject], fake_violation)

            if wrapped and mobject.width <= max_width and mobject.height <= max_height:
                logging.info(f"[_precheck_mobject] 换行成功: {type(mobject).__name__}")
                return mobject

            # 换行不够或失败，尝试整体缩放

            # - MathTex 优先走 _apply_wrap（已在上方尝试），不再依赖 font_size 属性
            # - 对所有文本用 mobject.scale(...) 整体缩放，绕开 font_size 属性对
            #   MathTex 失效的问题，并触发 Manim 内部重排
            scale_x = max_width / obj_width if obj_width > max_width else 1.0
            scale_y = max_height / obj_height if obj_height > max_height else 1.0
            scale_factor = min(scale_x, scale_y, 0.95)
            if scale_factor < 1.0:
                # 使用 about_point=mobject.get_center() 保持中心位置不变，
                # 避免相对锚点导致位置偏移（与 _precheck_mobject 图形分支保持一致）
                # 保留 95% 安全余量防再次越界
                # 同时配合 min_font_size 保护（仅记录，不再依赖 font_size 属性）
                min_size = LayoutOptimizer.MIN_FONT_SIZE
                current_font = getattr(mobject, "font_size", 32)
                if current_font * scale_factor < min_size:
                    scale_factor = min_size / max(current_font, 1)
                mobject.scale(
                    max(scale_factor, 0.5),
                    about_point=mobject.get_center(),
                )
                logging.info(
                    f"[_precheck_mobject] 文本缩放(scale): "
                    f"{type(mobject).__name__} ×{scale_factor:.2f} "
                    f"(原始 w={obj_width:.2f} h={obj_height:.2f})"
                )
                return mobject

        # 图形类对象（非文本）：直接 scale_to_fit
        is_graphic = not isinstance(mobject, (Text, MathTex))
        if is_graphic and (obj_width > max_width or obj_height > max_height):
            scale_x = max_width / obj_width if obj_width > max_width else 1.0
            scale_y = max_height / obj_height if obj_height > max_height else 1.0
            scale_factor = min(scale_x, scale_y, 1.0)
            # 图形缩放下限：不低于 MIN_GRAPHICS_SCALE_RATIO（=0.80）
            if scale_factor < ZoneConstants.MIN_GRAPHICS_SCALE_RATIO:
                scale_factor = ZoneConstants.MIN_GRAPHICS_SCALE_RATIO

            # 改用 about_point=mobject.get_center()（与 arrange_content 一致）
            mobject.scale(scale_factor, about_point=mobject.get_center())
            logging.info(
                f"[_precheck_mobject] 图形缩放: "
                f"{type(mobject).__name__} ×{scale_factor:.2f} "
                f"(原始 w={obj_width:.2f} h={obj_height:.2f})"
            )
            # 缩放后强制应用 stroke_width 下限（即使缩放也不能减小此最小线宽）
            self._enforce_min_stroke_width(mobject)
            return mobject

        return mobject

    def _enforce_min_stroke_width(self, mobj: Mobject) -> None:
        """强制设置 Mobject 的 stroke_width 不低于 MIN_STROKE_WIDTH_POINTS（=3 points）

        即使经过缩放，线宽也不能进一步减小此最小值。
        递归应用到所有子对象。
        """
        POINTS_PER_UNIT = 72.0
        min_stroke_units = ZoneConstants.MIN_STROKE_WIDTH_POINTS / POINTS_PER_UNIT
        try:
            current_sw = getattr(mobj, "stroke_width", None)
            if current_sw is not None and current_sw < min_stroke_units:
                mobj.stroke_width = min_stroke_units
        except Exception:
            pass
        if hasattr(mobj, "submobjects") and mobj.submobjects:
            for sub in mobj.submobjects:
                self._enforce_min_stroke_width(sub)

    def validate_layout(
        self,
        placed_objects: list,
        region: str = "content",
        overlap_pairs: list = None,
        allowed_overlap_pairs: list = None,
        allowed_overlap_patterns: dict = None,
        column_layout: Optional[Dict[str, Any]] = None,
    ) -> list:
        """程序化布局校验（无需渲染），检测溢出/侵入/重叠/越界

        核心原理：Manim MObject 在构建后 width/height/get_left() 等属性
        立即可用，无需调用 render()。结合 ZoneConstants 的精确区域边界，
        可在毫秒级完成全部布局合规性检查。

        Args:
            placed_objects: 已放置的所有 MObject 列表
            region: 目标区域名称
                - "content" / "content_single_col": 单栏主内容区（别名等价）
                - "content_two_col_left": 两栏布局的左栏（公式/文字栏）
                - "content_two_col_right": 两栏布局的右栏（图形栏）
                - "content_three_col_left": 三栏布局的左栏（步骤/概念）
                - "content_three_col_mid": 三栏布局的中栏（公式）
                - "content_three_col_right": 三栏布局的右栏（图形）
                - "graphics": 图形区
                - "subtitle": 字幕区
                - "safe_area": 全局安全区域
                - "screen": 屏幕边界
            overlap_pairs: 需要检查重叠的 (obj_a, obj_b) 对列表。
                         若为 None，则对 placed_objects 中所有相邻对做两两检查。
            allowed_overlap_pairs: **允许合法重叠的对象对列表**，每项为 (obj_a, obj_b) 元组。
                         出现在此列表中的对象对将跳过重叠检测。
                         典型用途：
                           - 力矢量箭头(Arrow) 与被分析物体（箭尾必须接触物体表面）
                           - 标注文本(Tex) 与被标注对象（标签紧贴目标）
                           - 电路导线端点与元件引脚（连接点重合）
                           - 坐标轴刻度标签与轴线
            allowed_overlap_patterns: **按对象类型/名称模式自动豁免重叠的规则字典**。
                         当一对对象的类型组合匹配某个 pattern key 时，自动跳过重叠检测。
                         格式: { "pattern_name": (type_a_matcher, type_b_matcher) }
                         其中 matcher 可以是:
                           - str: 精确匹配 type(obj).__name__
                           - tuple of str: 匹配其中任一类型名
                           - callable(obj) -> bool: 自定义判断函数
                         内置预定义模式（可直接引用常量）:
                           ALLOWED_PATTERNS = {
                               "force_arrow_on_object": ("Arrow", ...),   # 力箭头 vs 物体
                               "label_on_target": ("Tex", ...),           # 标注 vs 目标
                               "wire_to_component": ("Line", ...),       # 导线 vs 元件
                           }
            column_layout: 动态分栏布局信息（由 compute_column_layout 返回）。
                         提供后，多栏校验（content_two_col_* / content_three_col_*）
                         将使用动态计算边界，而非静态常量，确保与实际渲染一致。

        Returns:
            违规列表，每条为 dict:
            {
                "type": str,          # "REGION_OVERFLOW" | "REGION_INTRUSION"
                                      # | "ELEMENT_OVERLAP" | "SCREEN_OUT_OF_BOUNDS"
                                      # | "STACK_OVERFLOW" | "WIDTH_EXCEEDS_COLUMN"
                                      # | "ABNORMAL_SPACING" | "OVER_DENSE" | "TOO_SPARSE"
                                      # | "CENTER_OFFSET"
                "object_name": str,   # 违规对象的名称（取自 mobject.name 或 type 名）
                "region": str,        # 目标区域名
                "expected": str,      # 期望的约束条件描述
                "actual": str,        # 实际测量值
                "detail": str,        # 人类可读的详细说明
            }
            空列表 [] 表示全部通过。
        """
        violations = []

        # ---- 根据 region 确定边界 ----

        # 与多栏布局（两栏/三栏）脱节，导致左栏内容溢出到右栏区域无法被捕获。
        # 现在扩展 region 取值，每种栏位用对应区域的精确 X 边界。

        # 避免静态常量与 compute_column_layout 计算结果不一致。
        _COLUMN_REGION_TO_INDEX = {
            "content_two_col_left": 0,
            "content_two_col_right": 1,
            "content_three_col_left": 0,
            "content_three_col_mid": 1,
            "content_three_col_right": 2,
        }
        # 多栏布局时使用 ZoneConstants.compute(has_title=False) 动态计算 Y 边界
        # 两栏/三栏 Y 范围 = [-2.88, 3.6]（90%），单栏/centered Y 范围 = [-2.88, 2.16]（70%）
        _zones_two_col = ZoneConstants.compute(
            ZoneConstants.SCREEN_WIDTH, ZoneConstants.SCREEN_HEIGHT, has_title=False
        )
        _two_col_y_min = _zones_two_col["content_y_min"]
        _two_col_y_max = _zones_two_col["content_y_max"]
        _zones_three_col = _zones_two_col
        _three_col_y_min = _zones_two_col["content_y_min"]
        _three_col_y_max = _zones_two_col["content_y_max"]

        if region in ("content", "content_single_col"):
            # 默认 / 向后兼容：单栏主内容区
            x_min = ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MIN
            x_max = ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MAX
            y_min = ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MIN
            y_max = ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MAX
        elif region == "content_two_col_left":
            # 两栏左栏（公式/文字）
            x_min = ZoneConstants.MAIN_CONTENT_TWO_COL_X_MIN
            x_max = ZoneConstants.MAIN_CONTENT_TWO_COL_X_MAX
            y_min = _two_col_y_min
            y_max = _two_col_y_max
        elif region == "content_two_col_right":
            # 两栏右栏（图形）
            x_min = ZoneConstants.GRAPHICS_X_MIN
            x_max = ZoneConstants.GRAPHICS_X_MAX
            y_min = _two_col_y_min
            y_max = _two_col_y_max
        elif region == "content_three_col_left":
            # 三栏左栏（步骤/概念）
            x_min = ZoneConstants.THREE_COL_LEFT_X_MIN
            x_max = ZoneConstants.THREE_COL_LEFT_X_MAX
            y_min = _three_col_y_min
            y_max = _three_col_y_max
        elif region == "content_three_col_mid":
            # 三栏中栏（公式）
            x_min = ZoneConstants.THREE_COL_MID_X_MIN
            x_max = ZoneConstants.THREE_COL_MID_X_MAX
            y_min = _three_col_y_min
            y_max = _three_col_y_max
        elif region == "content_three_col_right":
            # 三栏右栏（图形）
            x_min = ZoneConstants.THREE_COL_RIGHT_X_MIN
            x_max = ZoneConstants.THREE_COL_RIGHT_X_MAX
            y_min = _three_col_y_min
            y_max = _three_col_y_max
        elif region == "graphics":
            x_min = ZoneConstants.GRAPHICS_X_MIN
            x_max = ZoneConstants.GRAPHICS_X_MAX
            y_min = _two_col_y_min
            y_max = _two_col_y_max
        elif region == "subtitle":
            x_min = ZoneConstants.SUBTITLE_ZONE_X_MIN
            x_max = ZoneConstants.SUBTITLE_ZONE_X_MAX
            y_min = ZoneConstants.SUBTITLE_ZONE_Y_MIN
            y_max = ZoneConstants.SUBTITLE_ZONE_Y_MAX
        elif region == "safe_area":
            x_min = ZoneConstants.SAFE_AREA_X_MIN
            x_max = ZoneConstants.SAFE_AREA_X_MAX
            y_min = ZoneConstants.SAFE_AREA_Y_MIN
            y_max = ZoneConstants.SAFE_AREA_Y_MAX
        elif region == "screen":
            x_min = -ZoneConstants.SCREEN_WIDTH / 2
            x_max = ZoneConstants.SCREEN_WIDTH / 2
            y_min = -ZoneConstants.SCREEN_HEIGHT / 2
            y_max = ZoneConstants.SCREEN_HEIGHT / 2
        else:
            raise ValueError(f"未知区域: {region}")

        # 如果传入了动态 column_layout，覆盖多栏 region 的 X 边界

        if column_layout and region in _COLUMN_REGION_TO_INDEX:
            idx = _COLUMN_REGION_TO_INDEX[region]
            if 0 <= idx < len(column_layout):
                col = column_layout[idx]
                x_min = col["x_min"]
                x_max = col["x_max"]

        # ---- 逐对象检查区域溢出 + 屏幕越界 ----
        # 坐标日志（debug 模式）：每个对象输出快照卡片 + 末尾汇总表
        if self.debug:
            print(f"\n[LayoutScene] validate_layout() 坐标快照  region={region}")
            print(
                f"  区域边界: x∈[{x_min:.2f}, {x_max:.2f}]  y∈[{y_min:.2f}, {y_max:.2f}]"
            )
            print("  ─" * 70)

        for idx, obj in enumerate(placed_objects, 1):
            obj_name = getattr(obj, "name", None) or type(obj).__name__
            obj_type = type(obj).__name__

            left = obj.get_left()[0]
            right = obj.get_right()[0]
            bottom = obj.get_bottom()[1]
            top = obj.get_top()[1]
            cx, cy = obj.get_center()[0], obj.get_center()[1]

            # ── debug 坐标快照卡片 ──
            if self.debug:
                # 快速判断是否在区域内
                in_region = (
                    left >= x_min
                    and right <= x_max
                    and bottom >= y_min
                    and top <= y_max
                )
                status = "✓ OK" if in_region else "✗ 越界"
                print(
                    f"  #{idx:02d} {obj_type:<20s} | name={obj_name:<20s} | "
                    f"center=({cx:>7.2f}, {cy:>6.2f}) | "
                    f"X=[{left:>6.2f}, {right:<6.2f}] Y=[{bottom:>6.2f}, {top:<6.2f}] | "
                    f"w={obj.width:.2f} h={obj.height:.2f} | {status}"
                )

            # 检查区域溢出
            if right > x_max:
                violations.append(
                    {
                        "type": "REGION_OVERFLOW",
                        "object_name": obj_name,
                        "region": region,
                        "expected": f"right_x <= {x_max:.2f}",
                        "actual": f"right_x = {right:.2f}, width = {obj.width:.2f}",
                        "detail": f"{obj_name} 右边界超出 {region} 区右边界 ({right:.2f} > {x_max:.2f})",
                    }
                )
            if left < x_min:
                violations.append(
                    {
                        "type": "REGION_OVERFLOW",
                        "object_name": obj_name,
                        "region": region,
                        "expected": f"left_x >= {x_min:.2f}",
                        "actual": f"left_x = {left:.2f}",
                        "detail": f"{obj_name} 左边界超出 {region} 区左边界 ({left:.2f} < {x_min:.2f})",
                    }
                )
            if top > y_max:
                violations.append(
                    {
                        "type": "REGION_OVERFLOW",
                        "object_name": obj_name,
                        "region": region,
                        "expected": f"top_y <= {y_max:.2f}",
                        "actual": f"top_y = {top:.2f}, height = {obj.height:.2f}",
                        "detail": f"{obj_name} 上边界超出 {region} 区上边界 ({top:.2f} > {y_max:.2f})",
                    }
                )
            if bottom < y_min:
                violations.append(
                    {
                        "type": "REGION_OVERFLOW",
                        "object_name": obj_name,
                        "region": region,
                        "expected": f"bottom_y >= {y_min:.2f}",
                        "actual": f"bottom_y = {bottom:.2f}",
                        "detail": f"{obj_name} 下边界超出 {region} 区下边界 ({bottom:.2f} < {y_min:.2f})",
                    }
                )

            # 检查屏幕越界（更严格的绝对边界）
            screen_hw = ZoneConstants.SCREEN_WIDTH / 2
            screen_hh = ZoneConstants.SCREEN_HEIGHT / 2
            if (
                right > screen_hw
                or left < -screen_hw
                or top > screen_hh
                or bottom < -screen_hh
            ):
                violations.append(
                    {
                        "type": "SCREEN_OUT_OF_BOUNDS",
                        "object_name": obj_name,
                        "region": "screen",
                        "expected": f"[{-screen_hw:.1f}, {screen_hw:.1f}] x [{-screen_hh:.1f}, {screen_hh:.1f}]",
                        "actual": f"[{left:.2f}, {right:.2f}] x [{bottom:.2f}, {top:.2f}]",
                        "detail": f"{obj_name} 超出屏幕边界",
                    }
                )

            # 检查字幕区侵入（仅非 subtitle 区域的对象需要检查）
            if region != "subtitle" and bottom < ZoneConstants.SUBTITLE_ZONE_Y_MAX:
                violations.append(
                    {
                        "type": "REGION_INTRUSION",
                        "object_name": obj_name,
                        "region": "subtitle_zone",
                        "expected": f"bottom_y >= {ZoneConstants.SUBTITLE_ZONE_Y_MAX:.2f}",
                        "actual": f"bottom_y = {bottom:.2f}",
                        "detail": f"{obj_name} 侵入字幕区 (底部 Y={bottom:.2f} < 字幕区上界 {ZoneConstants.SUBTITLE_ZONE_Y_MAX:.2f})",
                    }
                )

        # debug 分隔线
        if self.debug:
            print("  ─" * 70)
            print(
                f"[LayoutScene] 共 {len(placed_objects)} 个对象  违规 {len(violations)} 项"
            )

        # ---- 两两重叠检查（含白名单过滤）----
        pairs_to_check = overlap_pairs
        if pairs_to_check is None:
            # 默认检查所有相邻对
            pairs_to_check = [
                (placed_objects[i], placed_objects[i + 1])
                for i in range(len(placed_objects) - 1)
            ]

        # 构建允许重叠的对象 id 集合（用于 O(1) 查找）
        allowed_set = set()
        if allowed_overlap_pairs:
            for pair_a, pair_b in allowed_overlap_pairs:
                allowed_set.add((id(pair_a), id(pair_b)))
                # 双向：顺序无关
                allowed_set.add((id(pair_b), id(pair_a)))

        for obj_a, obj_b in pairs_to_check:
            name_a = getattr(obj_a, "name", None) or type(obj_a).__name__
            name_b = getattr(obj_b, "name", None) or type(obj_b).__name__

            # ── 白名单过滤（两层）──

            # 第 1 层：显式对象对白名单
            if (id(obj_a), id(obj_b)) in allowed_set:
                continue  # 跳过，这是合法重叠

            # 命中 ALLOWED_PATTERNS（如 force_arrow_on_object 等）时，stroke 接触
            # 视为合法，跳过 ELEMENT_OVERLAP 检测。后续仍走精细化容差比较。
            pattern_matched = False
            if allowed_overlap_patterns and self._match_overlap_pattern(
                obj_a, obj_b, allowed_overlap_patterns
            ):
                pattern_matched = True

            # X 方向重叠判定
            a_left, a_right = obj_a.get_left()[0], obj_a.get_right()[0]
            b_left, b_right = obj_b.get_left()[0], obj_b.get_right()[0]
            x_overlap = min(a_right, b_right) - max(a_left, b_left)

            # Y 方向重叠判定
            a_bottom, a_top = obj_a.get_bottom()[1], obj_a.get_top()[1]
            b_bottom, b_top = obj_b.get_bottom()[1], obj_b.get_top()[1]
            y_overlap = min(a_top, b_top) - max(a_bottom, b_bottom)

            # - 0.05 是 Manim 默认 stroke_width=4 / 72 ≈ 0.056 的安全下限
            # - 额外按对象的实际 stroke_width 加大容差（API 缺失时 try/except 兜底）
            # - 容差仍 < 最小 stroke 宽度，避免漏报真正的重叠
            base_tolerance = 0.05
            stroke_a = self._safe_get_stroke_width(obj_a)
            stroke_b = self._safe_get_stroke_width(obj_b)
            stroke_tolerance = max(stroke_a, stroke_b) * 0.55
            tolerance = max(base_tolerance, stroke_tolerance)

            if x_overlap > tolerance and y_overlap > tolerance:

                # 应豁免（物理图元间天然存在空间关系，不是布局错误）
                if pattern_matched:
                    continue
                violations.append(
                    {
                        "type": "ELEMENT_OVERLAP",
                        "object_name": f"{name_a} vs {name_b}",
                        "region": "--",
                        "expected": "no bounding_box intersection",
                        "actual": (
                            f"overlap area: dx={x_overlap:.2f}, dy={y_overlap:.2f}\n"
                            f"  {name_a}: x=[{a_left:.2f}, {a_right:.2f}] y=[{a_bottom:.2f}, {a_top:.2f}]\n"
                            f"  {name_b}: x=[{b_left:.2f}, {b_right:.2f}] y=[{b_bottom:.2f}, {b_top:.2f}]"
                        ),
                        "detail": f"{name_a} 与 {name_b} 存在空间重叠",
                    }
                )

        # ================================================================
        # 区域内部内容校验（intra-region checks）
        # 检查区域内各对象之间的高宽关系、堆叠总尺寸、间距合理性
        # ================================================================

        if len(placed_objects) >= 1:
            # ---- 1. 堆叠总高度 vs 区域可用高度 ----
            # 计算所有对象的包围盒总高度（从最顶部到最底部）
            all_tops = [o.get_top()[1] for o in placed_objects]
            all_bottoms = [o.get_bottom()[1] for o in placed_objects]
            stack_total_height = max(all_tops) - min(all_bottoms)
            region_avail_height = y_max - y_min

            if stack_total_height > region_avail_height:
                violations.append(
                    {
                        "type": "STACK_OVERFLOW",
                        "object_name": f"region_{region}",
                        "region": region,
                        "expected": f"total_height <= {region_avail_height:.2f} (区域可用高度)",
                        "actual": (
                            f"stacked_height = {stack_total_height:.2f}\n"
                            f"  对象数: {len(placed_objects)}, "
                            f"top={max(all_tops):.2f}, bottom={min(all_bottoms):.2f}"
                        ),
                        "detail": (
                            f"区域内 {len(placed_objects)} 个对象堆叠后 "
                            f"总高度 ({stack_total_height:.2f}) 超出区域可用高度 "
                            f"({region_avail_height:.2f})，差值 {stack_total_height - region_avail_height:.2f}"
                        ),
                    }
                )

            # ---- 2. 各对象宽度 vs 区域/列宽 ----
            region_avail_width = x_max - x_min
            for obj in placed_objects:
                obj_name = getattr(obj, "name", None) or type(obj).__name__
                if obj.width > region_avail_width * 0.98:  # 允许 2% 容差
                    violations.append(
                        {
                            "type": "WIDTH_EXCEEDS_COLUMN",
                            "object_name": obj_name,
                            "region": region,
                            "expected": f"width <= {region_avail_width * 0.98:.2f} (列宽的 98%)",
                            "actual": f"width = {obj.width:.2f}, 列宽 = {region_avail_width:.2f}",
                            "detail": (
                                f"{obj_name} 宽度 ({obj.width:.2f}) 接近或超过 "
                                f"{region} 区可用宽度 ({region_avail_width:.2f})"
                            ),
                        }
                    )

            # ---- 3. 相邻元素间距合理性检查 ----

            # 时，相邻对象可能来自不同栏（已设计有 0.5 单位列间距），
            # 水平间距 5.51 是正常设计，触发 ABNORMAL_SPACING 误报。
            # 仅当 region 是单栏/具体栏（content_*/single_col/*_left/mid/right）
            # 时才做间距检查；safe_area 校验只关心"是否整体越界"，不关心列间距。
            skip_spacing_check = region in ("safe_area", "screen")
            if not skip_spacing_check:
                for i in range(len(placed_objects) - 1):
                    obj_a = placed_objects[i]
                    obj_b = placed_objects[i + 1]
                    name_a = getattr(obj_a, "name", None) or type(obj_a).__name__
                    name_b = getattr(obj_b, "name", None) or type(obj_b).__name__

                    # 垂直间距（假设垂直排列，即 DOWN 方向 arrange）
                    gap_v = obj_a.get_bottom()[1] - obj_b.get_top()[1]

                    # 水平间距（假设水平排列，即 RIGHT 方向 arrange）
                    gap_h = obj_b.get_left()[0] - obj_a.get_right()[0]

                    # 取绝对值较大的作为实际间距（判断是垂直还是水平排列）
                    if abs(gap_v) > abs(gap_h):
                        actual_gap = gap_v
                        direction = "vertical"
                        expected_buff = ZoneConstants.ROW_BUFF
                    else:
                        actual_gap = gap_h
                        direction = "horizontal"
                        expected_buff = ZoneConstants.ELEMENT_BUFF

                    # 间距为负数表示重叠（已由上面的重叠检测捕获），这里只检查间距异常大
                    if actual_gap > expected_buff * 4:  # 超过标准间距 4 倍视为异常稀疏
                        violations.append(
                            {
                                "type": "ABNORMAL_SPACING",
                                "object_name": f"{name_a} -> {name_b}",
                                "region": region,
                                "expected": f"gap ≈ {expected_buff:.2f} (标准间距)",
                                "actual": f"gap = {actual_gap:.2f} ({direction})",
                                "detail": (
                                    f"{name_a} 与 {name_b} 之间的 {direction} 间距 "
                                    f"({actual_gap:.2f}) 远大于标准间距 ({expected_buff:.2f})，"
                                    f"可能存在布局不紧凑或遗漏元素"
                                ),
                            }
                        )
                    elif (
                        0 < actual_gap < expected_buff * 0.3
                    ):  # 小于标准间距 30% 视为过密
                        violations.append(
                            {
                                "type": "ABNORMAL_SPACING",
                                "object_name": f"{name_a} -> {name_b}",
                                "region": region,
                                "expected": f"gap >= {expected_buff * 0.3:.2f} (最小舒适间距)",
                                "actual": f"gap = {actual_gap:.2f} ({direction})",
                                "detail": (
                                    f"{name_a} 与 {name_b} 之间的 {direction} 间距 "
                                    f"({actual_gap:.2f}) 过小（标准 {expected_buff:.2f}），"
                                    f"视觉上可能拥挤"
                                ),
                            }
                        )

            # ---- 4. 区域填充率检查 ----
            # 计算所有对象的总面积 vs 区域可用面积
            total_content_area = sum(o.width * o.height for o in placed_objects)
            region_area = region_avail_width * region_avail_height
            fill_ratio = total_content_area / region_area if region_area > 0 else 0

            if fill_ratio > 0.92 and len(placed_objects) > 3:
                violations.append(
                    {
                        "type": "OVER_DENSE",
                        "object_name": f"region_{region}_{len(placed_objects)}_items",
                        "region": region,
                        "expected": f"fill_ratio <= 0.92 或减少元素数量",
                        "actual": f"fill_ratio = {fill_ratio:.2%}, area = {total_content_area:.2f}/{region_area:.2f}",
                        "detail": (
                            f"{region} 区域内容过于密集（填充率 {fill_ratio:.0%}），"
                            f"{len(placed_objects)} 个对象总面积接近区域面积，"
                            f"建议拆分到多个场景或减小字号"
                        ),
                    }
                )
            elif fill_ratio < 0.05 and len(placed_objects) >= 1:
                violations.append(
                    {
                        "type": "TOO_SPARSE",
                        "object_name": f"region_{region}_{len(placed_objects)}_items",
                        "region": region,
                        "expected": f"fill_ratio >= 0.05 或增加内容",
                        "actual": f"fill_ratio = {fill_ratio:.2%}, area = {total_content_area:.2f}/{region_area:.2f}",
                        "detail": (
                            f"{region} 区域内容过于稀疏（填充率 {fill_ratio:.0%}），"
                            f"大量空白可能影响视觉效果"
                        ),
                    }
                )

            # ---- 5. 视觉重心偏移检查 ----
            # 加权计算所有对象的几何中心
            total_weight = sum(o.width * o.height for o in placed_objects)
            if total_weight > 0:
                weighted_cx = (
                    sum(o.get_center()[0] * o.width * o.height for o in placed_objects)
                    / total_weight
                )
                weighted_cy = (
                    sum(o.get_center()[1] * o.width * o.height for o in placed_objects)
                    / total_weight
                )

                region_cx = (x_min + x_max) / 2
                region_cy = (y_min + y_max) / 2

                offset_x = abs(weighted_cx - region_cx)
                offset_y = abs(weighted_cy - region_cy)

                # 水平偏移超过区域宽度的 15% 视为明显偏移
                if offset_x > region_avail_width * 0.15:
                    violations.append(
                        {
                            "type": "CENTER_OFFSET",
                            "object_name": f"region_{region}_content_group",
                            "region": region,
                            "expected": f"|cx - region_cx| <= {region_avail_width * 0.15:.2f}",
                            "actual": (
                                f"content_cx = {weighted_cx:.2f}, region_cx = {region_cx:.2f}, "
                                f"offset_x = {offset_x:.2f}"
                            ),
                            "detail": (
                                f"{region} 区域内容的视觉重心水平偏移 "
                                f"{offset_x:.2f} 单位（区域中心 {region_cx:.2f}），"
                                f"建议使用 VGroup.arrange(center=True) 居中"
                            ),
                        }
                    )
                # 垂直偏移超过区域高度的 20% 视为明显偏移
                if offset_y > region_avail_height * 0.2:
                    violations.append(
                        {
                            "type": "CENTER_OFFSET",
                            "object_name": f"region_{region}_content_group",
                            "region": region,
                            "expected": f"|cy - region_cy| <= {region_avail_height * 0.2:.2f}",
                            "actual": (
                                f"content_cy = {weighted_cy:.2f}, region_cy = {region_cy:.2f}, "
                                f"offset_y = {offset_y:.2f}"
                            ),
                            "detail": (
                                f"{region} 区域内容的视觉重心垂直偏移 "
                                f"{offset_y:.2f} 单位（区域中心 {region_cy:.2f}）"
                            ),
                        }
                    )

        # ---- 输出结果 ----
        # debug 模式：无论有无违规都输出快照汇总；发现违规时附加详细报告
        if self.debug:
            if violations:
                print(f"\n[LayoutScene.validate_layout] 发现 {len(violations)} 项违规:")
                for i, v in enumerate(violations, 1):
                    print(f"  [{i}] {v['type']}: {v['detail']}")
                    print(f"       期望: {v['expected']}")
                    print(f"       实际: {v['actual']}")
            else:
                print(
                    f"[LayoutScene.validate_layout] 全部 {len(placed_objects)} 个对象布局合规 ✓"
                )

        return violations

    # ============================================================
    # 自动违规处置方法
    # ============================================================

    def handle_violation(
        self,
        violations: List[Dict[str, Any]],
        mobjects: List[Mobject],
        column_layout: Optional[Dict] = None,
        auto_optimize: bool = True,
    ) -> Optional[OptimizationResult]:
        """处理布局违规 - 自动执行处置策略

        可选模式：
        1. 自动优化模式（auto_optimize=True）：调用 LayoutOptimizer 自动执行 3 轮调整
        2. 手动处置模式（auto_optimize=False）：返回违规报告，等待人工干预

        Args:
            violations: validate_layout() 返回的违规列表
            mobjects: 需要优化的 Mobject 列表（会原地修改）
            column_layout: 当前栏位布局信息（含 x_min/x_max/width）
            auto_optimize: 是否启用自动优化（默认 True）

        Returns:
            自动优化时返回 OptimizationResult；手动模式返回 None

        示例::

            violations = self.validate_layout(all_mobjects)
            if violations:
                result = self.handle_violation(violations, all_mobjects)
                if result and result.success:
                    print("自动优化成功")
                elif result and not result.success:
                    print(f"自动优化失败：{result.error_message}")
        """
        if not violations:
            return None

        logging.info(f"[handle_violation] 发现 {len(violations)} 项违规")

        if not auto_optimize:
            # 手动处置模式：仅输出报告
            self._print_violation_report(violations)
            return None

        # 自动优化模式
        result = self._layout_optimizer.optimize(
            mobjects=mobjects,
            violations=violations,
            column_layout=column_layout,
        )

        if result.is_successful:
            logging.info(
                f"[handle_violation] 优化成功！共执行 {result.rounds_executed} 轮调整"
            )
            for adj in result.adjustments:
                logging.info(
                    f"  - 第{adj['round']}轮：策略={adj['strategy']}, "
                    f"{'成功' if adj['success'] else '失败'}"
                )
        else:
            logging.warning(f"[handle_violation] 优化失败，建议人工干预")
            logging.warning(f"  {result.error_message}")

        return result

    def _print_violation_report(self, violations: List[Dict[str, Any]]) -> None:
        """打印违规报告（仅供人工查看）"""
        print("\n" + "=" * 70)
        print("[LayoutScene] 布局违规报告")
        print("=" * 70)
        for i, v in enumerate(violations, 1):
            print(f"\n[{i}] {v['type']}")
            print(f"    对象：{v['object_name']}")
            print(f"    期望：{v['expected']}")
            print(f"    实际：{v['actual']}")
            print(f"    详情：{v['detail']}")
        print("\n" + "=" * 70)
        print("建议: 根据违规类型调整布局或调用 handle_violation(auto_optimize=True)")
        print("=" * 70 + "\n")

    def _on_atom_split(
        self,
        violation_type: str,
        mobjects: List[Mobject],
        suggested_id: str,
    ) -> None:
        """拆分原子回调 - 当字号缩小和换行均无效时触发

        Args:
            violation_type: 违规类型（WIDTH_OVERFLOW / HEIGHT_OVERFLOW）
            mobjects: 需要拆分的 Mobject 列表
            suggested_id: 建议的原子 ID 前缀

        注：此方法仅记录日志，实际拆分由 JSON 设计阶段处理。
        外部代码可捕获此日志，手动拆分原子并重新生成代码。
        """
        obj_names = [getattr(m, "name", type(m).__name__) for m in mobjects]
        logging.warning(
            f"[_on_atom_split] 需要拆分原子 {suggested_id} "
            f"(类型={violation_type}, 对象={obj_names})"
        )
        logging.warning(
            f"建议工程师操作：将 JSON 中该原子拆分为 2-3 个独立原子，"
            f"每个包含原内容的 1/2 或 1/3"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # 重叠白名单：预定义模式常量 + 模式匹配方法
    #
    # 唯一判定基准（与 SKILL.md 重叠白名单机制 一致）：
    #   语义相关 → 允许重叠    语义无关 → 禁止重叠（报告 ELEMENT_OVERLAP）
    # 以下模式是"语义相关性"的近似实现：按 Manim 类型名推断语义关系。
    # ═══════════════════════════════════════════════════════════════════════════

    # 物理图形类型全集（用于 physics_scene_catch_all 通配模式）
    # 覆盖 R1(力作用) + R2(电连接) + R3(场贯穿) + R4(浸入流体) 语义关系
    PHYSICS_GRAPHIC_TYPES = (
        # 箭头/矢量
        "Arrow",
        "Vector",
        "DoubleArrow",
        "CurvedArrow",
        # 连线/导线/场线
        "Line",
        "DashedLine",
        "DottedLine",
        # 几何形体（物体/容器/液体）
        "Polygon",
        "Rectangle",
        "Square",
        "RegularPolygon",
        "Circle",
        "Ellipse",
        "Arc",
        "CubicBezier",
        # 点/标记
        "Dot",
        "SmallDot",
        "LabeledDot",
        # 通用（自定义图形、VGroup 组合体等）
        "VMobject",
    )

    ALLOWED_PATTERNS = {
        # ════════════════════════════════════════════
        # 物理类合法重叠模式 → 对应语义关系 R1~R4
        # ════════════════════════════════════════════
        # R1+R2+R3+R4 全覆盖：任意两个物理图元之间的重叠全部放行
        # 原因：物理绘图中图元间天然存在空间关系，这些重叠不是布局错误，而是
        # 物理正确性的体现。此模式覆盖以下所有具体物理子模式，作为第一优先级匹配。
        "physics_scene_catch_all": (
            PHYSICS_GRAPHIC_TYPES,  # A 端：任意图元
            PHYSICS_GRAPHIC_TYPES,  # B 端：任意图元（含同类）
        ),
        # 以下为具体子模式（对应 R1-R4，保留供禁用通配后精确控制时使用）
        # R1: 力作用于物体 —— 箭头类 → 与接触物体语义相关
        "force_arrow_on_object": (
            ("Arrow", "Vector", "DoubleArrow", "CurvedArrow"),
            None,  # 箭头 vs 任意物体（力作用）
        ),
        # R2: 电连接 —— 连线类 → 与连接目标语义相关
        "wire_to_component": (
            ("Line", "DashedLine", "VMobject"),
            None,  # 导线 vs 任意元件（电连接）
        ),
        # R11: 坐标轴刻度 —— 文本数字 + 轴线类型 → 推断为刻度标签
        "axis_tick_label": (
            ("Tex", "MathTex", "Integer", "DecimalNumber"),
            ("NumberLine", "Axes", "ThreeDAxes"),
        ),
        # R4: 浸入流体 —— 固体 vs 液体Polygon → 推断为浸入关系
        "object_submerged_in_liquid": (
            (
                "Polygon",
                "Rectangle",
                "Square",
                "RegularPolygon",
                "Circle",
                "Ellipse",
                "VMobject",
            ),
            ("Polygon",),  # 液体
        ),
        # ════════════════════════════════════════════
        # 数学/几何类合法重叠模式 → 对应语义关系 R5~R11
        # ════════════════════════════════════════════
        # R7: 顶点标记 —— 点 + 多边形 → 推断为顶点重合
        "geometry_vertex_point": (
            ("Dot", "SmallDot", "LabeledDot"),  # 点类型
            (
                "Polygon",
                "Triangle",
                "Rectangle",
                "Square",
                "RegularPolygon",
                "Circle",
                "Ellipse",
                "Arc",
                "CubicBezier",
                "VMobject",
            ),  # 几何图形类型
        ),
        # R6: 几何依附 —— 虚线 + 图形 → 推断为辅助线
        "auxiliary_line_on_figure": (
            ("Line", "DashedLine", "DottedLine"),
            (
                "Polygon",
                "Triangle",
                "Rectangle",
                "Square",
                "RegularPolygon",
                "Circle",
                "Ellipse",
                "Arc",
                "VMobject",
            ),
        ),
        # R7: 角标记 —— 弧/直角符号 + 顶点 → 推断为角度标记
        "angle_mark_at_vertex": (
            ("Arc", "RightAngle", "Angle", "Elbow"),
            ("Dot", "SmallDot", "Polygon", "Triangle", "Line", "VMobject"),
        ),
        # R5: 标注(几何) —— 文本 + 几何图形 → 推断为顶点/边标签
        "geometry_label_on_figure": (
            ("Tex", "MathTex", "Text"),
            (
                "Polygon",
                "Triangle",
                "Rectangle",
                "Square",
                "RegularPolygon",
                "Circle",
                "Ellipse",
                "Arc",
                "Line",
                "DashedLine",
                "VMobject",
            ),
        ),
        # R8: 符号标记 —— ⊥∥文本 + 线段 → 推断为垂直平行标记
        "perpendicular_parallel_mark": (
            ("Tex", "MathTex", "VGroup"),  # ⊥/∥ 符号通常用 Tex 或 VGroup 组合
            ("Line", "DashedLine", "Polygon", "Triangle", "VMobject"),
        ),
        # R9: 尺寸标注 —— 箭头/大括号 + 线段 → 推断为长度标注
        "dimension_arrow_on_segment": (
            ("Arrow", "DoubleArrow", "Line", "Brace"),
            ("Line", "DashedLine", "Segment", "Polygon", "Triangle", "VMobject"),
        ),
        # R10: 曲线标注 —— 直线 + 曲线 → 推断为切线/法线/渐近线
        "curve_annotation": (
            ("Line", "DashedLine", "Arrow", "Vector", "VMobject"),
            (
                "ParametricFunction",
                "FunctionGraph",
                "ImplicitFunction",
                "Arc",
                "VMobject",
            ),
        ),
        # ════════════════════════════════════════════
        # 通用合法重叠模式（数学+物理共用）
        # ════════════════════════════════════════════
        # R5: 标注(通用) —— 文本类 → 推断为某对象的标注
        "label_on_target": (
            ("Tex", "MathTex", "Text", "MarkupText"),
            None,  # 标注文本 vs 任何被标注目标
        ),
    }

    def _match_overlap_pattern(
        self,
        obj_a: Mobject,
        obj_b: Mobject,
        patterns: dict,
    ) -> bool:
        """检查一对对象是否匹配某个预定义的重叠豁免模式。

        唯一判定基准（与 SKILL.md 重叠白名单机制 一致）：
            语义相关 → 允许重叠    语义无关 → 禁止重叠
        本方法通过类型匹配推断语义相关性（按 ALLOWED_PATTERNS 中的模式定义）。

        Args:
            obj_a: 第一个对象
            obj_b: 第二个对象
            patterns: 模式字典，格式同 ALLOWED_PATTERNS

        Returns:
            True 表示该对对象的重叠应被豁免（推断为语义相关，跳过 ELEMENT_OVERLAP 检测）
        """
        type_a = type(obj_a).__name__
        type_b = type(obj_b).__name__

        for pattern_name, (matcher_a, matcher_b) in patterns.items():
            # 尝试 (a, b) 和 (b, a) 两种顺序
            if self._type_matches(type_a, matcher_a) and self._type_matches(
                type_b, matcher_b
            ):
                if self.debug:
                    print(
                        f"  [overlap_whitelist] 豁免 {pattern_name}: "
                        f"{type_a} vs {type_b}"
                    )
                return True
            if self._type_matches(type_a, matcher_b) and self._type_matches(
                type_b, matcher_a
            ):
                if self.debug:
                    print(
                        f"  [overlap_whitelist] 豁免 {pattern_name}(反向): "
                        f"{type_a} vs {type_b}"
                    )
                return True

        return False

    @staticmethod
    def _type_matches(type_name: str, matcher) -> bool:
        """检查类型名是否匹配给定的 matcher 规则

        Args:
            type_name: 对象的类名字符串（如 "Arrow", "MathTex"）
            matcher: 匹配规则，支持三种形式：
                     - str: 精确匹配类名
                     - tuple of str: 匹配其中任一类名
                     - None: 通配（匹配任何类型）
                     - callable(obj_type_str) -> bool: 自定义判断函数

        Returns:
            是否匹配
        """
        if matcher is None:
            return True  # None = 通配符
        if isinstance(matcher, str):
            return type_name == matcher
        if isinstance(matcher, tuple):
            return type_name in matcher
        if callable(matcher):
            return matcher(type_name)
        return False

    @staticmethod
    def _safe_get_stroke_width(mobject: Mobject) -> float:
        """安全地获取 Mobject 的最大 stroke_width（以 Manim 单位返回）


        通过除以 72 转为 Manim 单位，用于动态调整重叠检测容差。

        实现细节：
        - 优先调用 get_stroke_widths() 取最大值（API 已被 Manim 标记为 deprecated）
        - 不可用时回退到 stroke_width 属性
        - 全部异常时返回 0（表示无 stroke 影响）

        Args:
            mobject: 任意 Mobject

        Returns:
            stroke 宽度（Manim 单位），恒 >= 0
        """
        # Manim 默认 stroke_width = 4 points = 4/72 ≈ 0.0556 manim units
        POINTS_PER_UNIT = 72.0
        try:
            # 优先尝试 get_stroke_widths()（已被 deprecated 但仍可用）
            stroke_widths = mobject.get_stroke_widths()
            if stroke_widths is not None and len(stroke_widths) > 0:
                return float(max(stroke_widths)) / POINTS_PER_UNIT
        except (AttributeError, Exception):
            pass
        # 回退：直接读取 stroke_width 属性
        try:
            sw = getattr(mobject, "stroke_width", None)
            if sw is not None:
                return float(sw) / POINTS_PER_UNIT
        except Exception:
            pass
        return 0.0

    def auto_arrange_atom(
        self, mobjs: List[Mobject], atom: Optional[Dict] = None
    ) -> VGroup:
        """根据 atom 的 layout 字段自动排列内容

        Args:
            mobjs: 内容对象列表
            atom: 原子字典（包含 layout 字段）

        Returns:
            已排列的 VGroup
        """
        if not mobjs:
            return VGroup()

        if atom and "layout" in atom:
            layout_value = atom["layout"]
            mode_map = {
                "vertical": LayoutMode.VERTICAL,
                "two_column": LayoutMode.TWO_COLUMN,
                "three_column": LayoutMode.THREE_COLUMN,
                "centered": LayoutMode.CENTERED,
            }
            mode = mode_map.get(layout_value, LayoutMode.VERTICAL)
        else:
            mode = LayoutMode.VERTICAL

        arranged = self._layout_engine.arrange_content(mobjs, mode)
        return arranged

    def apply_layout_fonts(
        self, group: VGroup, layout_type: str = "vertical"
    ) -> VGroup:
        """应用布局字体样式

        Args:
            group: 内容组
            layout_type: 布局类型

        Returns:
            已标记布局类型的内容组
        """
        group._layout_type = layout_type
        return group

    def _get_typing_run_time(self, mobj: Mobject) -> float:
        """计算打字动画时长"""
        return 1.0

    def _safe_speech_text(self, text: str) -> str:
        """清理语音文本"""
        return text

    # ============================================================
    # 语音相关（占位，实际由 voiceover 处理）
    # ============================================================

    def set_speech_service(self, service):
        """设置语音服务"""
        self.speech_service = service

    def voiceover(self, text: str, **kwargs):
        """语音占位，实际应使用 manim_voiceover 的 with voiceover"""
        # 这个方法在实际场景中会被覆盖，这里仅为保持接口一致
        return self

    # ============================================================
    # 坐标参考系（调试用，符合 layout.md 第 15 节）
    # ============================================================

    def add_coordinate_reference(self, debug: bool = True):
        """添加可视化坐标参考系（调试用）"""
        if not debug:
            return
        from manim import Axes, NumberPlane

        half_w = ZoneConstants.SCREEN_WIDTH / 2
        half_h = ZoneConstants.SCREEN_HEIGHT / 2
        axes = Axes(
            x_range=[-half_w, half_w, 1],
            y_range=[-half_h, half_h, 1],
            x_length=ZoneConstants.SCREEN_WIDTH,
            y_length=ZoneConstants.SCREEN_HEIGHT,
            axis_config={"color": "#888888", "stroke_width": 1},
        )
        axes.set_opacity(0.3)
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        self.add(axes, labels)
