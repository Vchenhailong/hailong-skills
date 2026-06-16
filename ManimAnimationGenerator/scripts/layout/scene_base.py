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
        skip_env_check: bool = False,
        interactive_env_check: bool = False,
        **kwargs,
    ):
        """初始化 LayoutScene

        Args:
            debug: 调试模式（绘制区域边界等）
            skip_env_check: True 时跳过 CJK 环境自检（CI/测试用）
            interactive_env_check: True 时自检失败弹 stdin 询问用户
                （需要 stdin 是 TTY；非 TTY 自动降级为非交互）
        """
        super().__init__(**kwargs)
        self.debug = debug
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

    def get_subtitle_zone(self, debug: Optional[bool] = None) -> SubtitleZone:
        """获取字幕区容器（懒加载）

        字幕区容器创建后会立即把自身加入 scene（容器 Rectangle 在
        debug 模式可见，非 debug 模式透明，不影响渲染）。
        这样 scene.mobjects 持有字幕区的引用，便于后续统一管理
        （清理、状态查询、跨场景复用等）。
        """
        if self._subtitle_zone is None:
            dbg = debug if debug is not None else self.debug
            self._subtitle_zone = SubtitleZone(scene=self, debug=dbg)
            self.add(self._subtitle_zone)
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
    # 内容放置 API（符合 layout.md 第 3.10 节）
    # ============================================================

    def place_in_main_zone(
        self,
        content: Union[Mobject, VGroup],
        layout_mode: str = "vertical",
    ) -> VGroup:
        """将内容放置在主内容区内（arrange + 预检 + zone.place_content）

        预检步骤确保单个子元素超宽时自动换行/缩放，
        避免与 place_two_column 行为不一致。

        Args:
            content: 单个元素或元素组
            layout_mode: 布局模式 (vertical/two_column/three_column/centered)

        Returns:
            已定位的 VGroup
        """
        if not isinstance(content, VGroup):
            content = VGroup(content)

        zone = self.get_main_content_zone(layout_mode)
        col_width = zone.x_max - zone.x_min
        col_height = zone.y_max - zone.y_min

        # 与 place_two_column/place_three_column 一致：先预检再 place
        content = self._precheck_mobject(
            content, max_width=col_width * 0.95, max_height=col_height * 0.9
        )

        if layout_mode == "centered":
            content.arrange(DOWN, buff=ZoneConstants.ROW_BUFF, center=True)
        else:
            content.arrange(DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT)

        return zone.place_content(content)

    def place_graphics(self, graphics: Mobject) -> Mobject:
        """将图形放置在图形区中心（含预检缩放）

        Args:
            graphics: 图形对象

        Returns:
            已定位的图形对象
        """
        zone = self.get_graphics_zone()
        col_width = zone.x_max - zone.x_min
        col_height = zone.y_max - zone.y_min
        graphics = self._precheck_mobject(
            graphics, max_width=col_width * 0.95, max_height=col_height * 0.9
        )
        return zone.place_content(graphics)

    def place_two_column(
        self,
        left_content: Mobject,
        right_content: Mobject,
    ) -> VGroup:
        """两栏布局：左内容区 + 右图形区

        内置**事前预检 + 事后校验**双层防护：
        1. **事前预检**（放置前）：逐对象测量宽度/高度，超限时自动缩放或换行
        2. **事后校验**（放置后）：validate_layout() 检测溢出，触发降级链

        Args:
            left_content: 左栏内容（公式/文字）
            right_content: 右栏图形

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

        # 对左栏内容做宽度预检+自动调整
        left_content = self._precheck_mobject(
            left_content,
            max_width=left_col_width * 0.95,
            max_height=left_col_height * 0.9,
        )
        # 对右栏图形做尺寸预检+自动调整
        right_content = self._precheck_mobject(
            right_content,
            max_width=right_col_width * 0.95,
            max_height=right_col_height * 0.9,
        )

        # 左栏：左栏内的内容左对齐 + 垂直居中（在左栏区域内）
        left_group = VGroup(left_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT
        )
        left_group = left_zone.place_content(left_group, h_align="left")

        # 右栏：右栏内的内容右对齐 + 垂直居中（在图形区区域内）
        right_group = VGroup(right_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=RIGHT
        )
        right_group = right_zone.place_content(right_group, h_align="right")

        # 两栏顶部对齐 + 边界校验。
        # 对齐后立即校验 top_overflow / bottom_overflow，越界则降级到
        # 居中/底部对齐。
        # zone_y_min / zone_y_max 语义对称（取最严格边界）。
        # 最严格下界 = max(zones.y_min)（各栏中最深的底部）
        # 最严格上界 = min(zones.y_max)（各栏中最浅的顶部）
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
        # union 校验改用 region="safe_area"（全局安全区），
        # 与多栏布局语义保持一致；同时透传 column_layout，
        # 确保动态分栏边界优先于静态常量。
        zones = ZoneConstants.compute(self.camera.frame_width, self.camera.frame_height)
        col_layout_list = ZoneConstants.compute_column_layout(
            zones, num_columns=2, has_graphics=True
        )
        # 显式构造覆盖全宽的 dict，让 union 校验的语义明确为
        # "全局安全区"而非"左栏"。
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

        # 按栏二次校验：
        # 上面 union 校验对单栏内部 "不超出本栏" 不敏感（X 边界跨度大）。
        # 这里用每栏各自的 X 边界再校验一次，捕获"左栏内容溢出到右栏"等穿栏越界。
        per_col_violations: list = []
        per_col_violations.extend(
            self.validate_layout(
                [left_group],
                region="content_two_col_left",
                column_layout=col_layout_list,
            )
        )
        per_col_violations.extend(
            self.validate_layout(
                [right_group],
                region="content_two_col_right",
                column_layout=col_layout_list,
            )
        )
        if per_col_violations:
            logging.warning(
                f"[place_two_column] 按栏校验发现 {len(per_col_violations)} 项违规，"
                "尝试自动优化"
            )
            # 传整段 col_layout_list，避免优化器只针对中栏做缩放
            # 而丢失对左/右栏违规的处理能力。
            self.handle_violation(
                per_col_violations, all_placed, column_layout=col_layout_list
            )

        # place_two_column 必须递归把 result 及其子对象 add 到场景中。
        # VGroup 不会自动 add submobjects 到 scene，
        # 必须显式 add 才能渲染（仅 `self.add(result)` 会导致嵌套
        # VGroup 渲染为空、主内容区不显示）。
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

        每栏独立缩放 + 独立定位到各自 X 边界，不共用 main_zone
        作为缩放参考系。任一栏超宽触发 main_zone 缩放会波及同 main_zone
        内其他栏，导致其他栏字号被缩到看不见。

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

        # 计算各栏可用尺寸（使用各栏独立的静态常量边界，不复用 main_zone 兜底）
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

        # 三栏独立预检 + 独立放置，每栏用自己的 X 边界：
        # - 左/中栏：左对齐到各自的 x_min
        # - 右栏：右对齐到 graphics_zone 的 x_max
        # 缩放以本栏 VGroup 中心为锚点（保持 X 不偏移），
        # move_to 再用缩放后的 width 重新计算左/右对齐坐标。
        left_col = VGroup(left_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF * 0.8, aligned_edge=LEFT
        )
        if left_col.width > left_col_width:
            scale_factor = (left_col_width * 0.95) / left_col.width
            if scale_factor < 1.0:
                left_col.scale(scale_factor, about_point=left_col.get_center())
                logging.info(f"[place_three_column] 左栏独立缩放: ×{scale_factor:.2f}")
        left_col.move_to([left_x_min + left_col.width / 2, main_zone.center_y, 0])

        mid_col = VGroup(mid_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT
        )
        if mid_col.width > mid_col_width:
            scale_factor = (mid_col_width * 0.95) / mid_col.width
            if scale_factor < 1.0:
                mid_col.scale(scale_factor, about_point=mid_col.get_center())
                logging.info(f"[place_three_column] 中栏独立缩放: ×{scale_factor:.2f}")
        mid_col.move_to([mid_x_min + mid_col.width / 2, main_zone.center_y, 0])

        right_col = (
            VGroup(right_content).arrange(
                DOWN, buff=ZoneConstants.ROW_BUFF, aligned_right=ZoneConstants.ROW_BUFF
            )
            if False
            else VGroup(right_content).arrange(
                DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=RIGHT
            )
        )
        if right_col.width > right_col_width:
            scale_factor = (right_col_width * 0.95) / right_col.width
            if scale_factor < 1.0:
                right_col.scale(scale_factor, about_point=right_col.get_center())
                logging.info(f"[place_three_column] 右栏独立缩放: ×{scale_factor:.2f}")
        right_col = right_zone.place_content(right_col, h_align="right")

        # 三栏顶部对齐 + 边界校验。
        # 与 place_two_column 同样的修复：原顶部对齐未校验对齐后是否完全
        # 在 zone 内。改为先尝试顶部对齐，越界则降级到居中/底部对齐。
        # zone_y_min / zone_y_max 语义对称（取最严格边界）。
        zone_y_min = max(main_zone.y_min, right_zone.y_min)
        zone_y_max = min(main_zone.y_max, right_zone.y_max)
        self._align_columns_within_zone(
            [left_col, mid_col, right_col],
            zone_y_min=zone_y_min,
            zone_y_max=zone_y_max,
            prefer="top",
        )

        # 与 place_two_column 保持一致，末尾添加事后校验。
        # 校验顺序：先按栏捕捉穿栏越界，再做整体 union 校验，
        # 避免 union 误报先污染导致按栏校验被跳过。
        all_placed = [left_col, mid_col, right_col]
        zones = ZoneConstants.compute(self.camera.frame_width, self.camera.frame_height)
        col_layout_list = ZoneConstants.compute_column_layout(
            zones, num_columns=3, has_graphics=True
        )

        # 先做按栏校验（per-col），更精确捕获穿栏越界
        per_col_violations: list = []
        per_col_violations.extend(
            self.validate_layout(
                [left_col],
                region="content_three_col_left",
                column_layout=col_layout_list,
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
            # 优化器 optimize() 期望接受 List[Dict]（整段三栏布局），
            # 可针对不同违规匹配对应栏位做缩放。
            self.handle_violation(
                per_col_violations, all_placed, column_layout=col_layout_list
            )

        # union 校验使用 safe_area（全局安全区）：
        # union 校验对单栏内部"不超出本栏"不敏感，但能捕获整体越出安全区。
        # 显式构造覆盖全宽的 dict，让 union 校验的语义明确为
        # "全局安全区"而非"左栏"。
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

        # place_three_column 同样必须递归 add 才能渲染嵌套 VGroup。
        result = VGroup(left_col, mid_col, right_col)
        self._add_recursive(result)
        return result

    def safe_place(self, mobject: Mobject) -> Mobject:
        """安全放置：确保不超出安全区域

        根据 layout.md 第 7 节，当元素超出安全边界时整体移动或缩放。

        处理顺序（先缩放，再位移，最后兜底二次校验）：
        1. **先缩放**：若内容尺寸（width/height）任一维度超出安全区，
           按比例缩放至 95% 边界内。这一步保证缩放后 content 必然能 fit，
           数学上消除了"同一轴向两端同时越界"的可能性
           （证明：若 content.height ≤ 0.95*safe_h，则 top-bottom ≤ 0.95*safe_h
            < safe_h，所以 top 和 bottom 不会同时超出 safe_y_min/max）
        2. **再位移**：对每个方向独立计算 shift 量，最后取较大绝对值方向
           作为净 shift。这避免了单一变量后写覆盖前写导致一方向被忽略。

        若内容尺寸本身已超出安全区，单纯 shift 无法 fit，
        必须先按比例 scale 到安全区的 95% 边界内再 shift。
        变量名采用无歧义命名（shift_top_to_y_max / shift_bottom_to_y_min），
        避免 up/down 含义混淆（down 在此上下文中是负值）。
        """
        safe_x_min = ZoneConstants.SAFE_AREA_X_MIN
        safe_x_max = ZoneConstants.SAFE_AREA_X_MAX
        safe_y_min = ZoneConstants.SAFE_AREA_Y_MIN
        safe_y_max = ZoneConstants.SAFE_AREA_Y_MAX
        safe_w = safe_x_max - safe_x_min
        safe_h = safe_y_max - safe_y_min

        # 步骤 1：先缩放
        # 检测内容尺寸是否超过安全区，超过则先按比例 scale 到 95% 边界内。
        # 这一步是消除"双端越界"的关键：缩放后 height ≤ 0.95*safe_h，
        # 几何上保证了 top - bottom < safe_h，shift 阶段只需处理单端越界。
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
                # 缩放后重新读取尺寸与位置（scale 会改变 get_width/height/get_*_edge）
                obj_w = mobject.width
                obj_h = mobject.height

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

        # 步骤 2：再位移
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
        # 用无歧义变量名 + 重新计算后变量符号已确定
        # shift_bottom_to_y_min 必为非负，shift_top_to_y_max 必为非正
        # 两者方向相反，简单相加取综合净 shift（极端双越界时取较大绝对值一侧）
        #
        # 理论上经过步骤 1 缩放后，content.height ≤ 0.95*safe_h，
        # 数学上 top 和 bottom 不可能同时越界（参见函数顶部 docstring 证明）。
        # 但作为防御性编程，仍保留"双端越界时取较大绝对值"的逻辑。
        # 若双端越界确实发生（如 obj_h=0 边界情况），
        # 在 shift 之后再做一次边界检查，必要时再缩放一次作为兜底。
        if shift_bottom_to_y_min != 0.0 and shift_top_to_y_max != 0.0:
            # 同时越上下界：取绝对值较大方向作为净 shift
            if abs(shift_bottom_to_y_min) >= abs(shift_top_to_y_max):
                shift_y = shift_bottom_to_y_min
            else:
                shift_y = shift_top_to_y_max
            logging.warning(
                f"[safe_place] 异常：双端 Y 越界同时发生 "
                f"(bottom={bottom:.2f} top={top:.2f} safe=[{safe_y_min}, {safe_y_max}])"
            )
        elif shift_bottom_to_y_min != 0.0:
            shift_y = shift_bottom_to_y_min
        else:
            shift_y = shift_top_to_y_max

        if shift_left_to_x_min != 0.0 and shift_right_to_x_max != 0.0:
            if abs(shift_left_to_x_min) >= abs(shift_right_to_x_max):
                shift_x = shift_left_to_x_min
            else:
                shift_x = shift_right_to_x_max
            logging.warning(
                f"[safe_place] 异常：双端 X 越界同时发生 "
                f"(left={left:.2f} right={right:.2f} safe=[{safe_x_min}, {safe_x_max}])"
            )
        elif shift_left_to_x_min != 0.0:
            shift_x = shift_left_to_x_min
        else:
            shift_x = shift_right_to_x_max

        if shift_x != 0.0 or shift_y != 0.0:
            mobject.shift(RIGHT * shift_x + UP * shift_y)

        # 兜底二次校验。shift 后再次测量边缘，
        # 若仍有越界（极端情况如初始 obj_h=0 导致缩放未触发），
        # 再做一次 scale 强制适配。这是最后一道防线。
        bottom = mobject.get_bottom()[1]
        top = mobject.get_top()[1]
        left = mobject.get_left()[0]
        right = mobject.get_right()[0]
        if (
            bottom < safe_y_min
            or top > safe_y_max
            or left < safe_x_min
            or right > safe_x_max
        ):
            obj_w = mobject.width
            obj_h = mobject.height
            scale_x = (safe_w * 0.95) / obj_w if obj_w > safe_w else 1.0
            scale_y = (safe_h * 0.95) / obj_h if obj_h > safe_h else 1.0
            scale_factor = min(scale_x, scale_y, 1.0)
            if scale_factor < 1.0:
                mobject.scale(scale_factor, about_point=mobject.get_center())
                logging.warning(
                    f"[safe_place] 兜底二次缩放: ×{scale_factor:.3f} "
                    f"(shift 后仍越界)"
                )
                # 二次缩放后再次尝试 shift（缩放后位置可能微偏）
                bottom = mobject.get_bottom()[1]
                top = mobject.get_top()[1]
                left = mobject.get_left()[0]
                right = mobject.get_right()[0]
                shift_y2 = 0.0
                shift_x2 = 0.0
                if bottom < safe_y_min:
                    shift_y2 = safe_y_min - bottom
                elif top > safe_y_max:
                    shift_y2 = safe_y_max - top
                if left < safe_x_min:
                    shift_x2 = safe_x_min - left
                elif right > safe_x_max:
                    shift_x2 = safe_x_max - right
                if shift_x2 != 0.0 or shift_y2 != 0.0:
                    mobject.shift(RIGHT * shift_x2 + UP * shift_y2)

        return mobject

    def _align_columns_within_zone(
        self,
        columns: List[Mobject],
        zone_y_min: float,
        zone_y_max: float,
        prefer: str = "top",
    ) -> str:
        """多栏顶部对齐 + 边界校验

        本函数实现"对齐后完全在 zone 内"的最优策略：
        1. 先尝试 prefer 指定的对齐方式（默认 top）
        2. 对齐后立即校验 top_overflow / bottom_overflow
        3. 越界则回退到原位置，尝试下一优先级对齐方式
        4. 优先级：top → center → bottom（或按 prefer 调整）
        5. 所有方式都越界（内容已超出 zone 高度）→ 按比例缩放兜底

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

            # 校验对齐后是否完全在 zone 内
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

        # 所有对齐方式都越界（内容本身已超出 zone 高度）
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

    def _precheck_mobject(
        self,
        mobject: Mobject,
        max_width: float,
        max_height: float,
    ) -> Mobject:
        """事前预检单个 Mobject 的尺寸，超限时自动调整

        处理策略（按对象类型分层）：
        1. **VGroup**：递归检查子元素，对每个超宽/超高的子元素分别处理
        2. **Text / MathTex**：
           - 宽度超限 → 调用 LayoutOptimizer 的换行逻辑重建为多行
           - 换行后仍超限 → 缩小 font_size
        3. **图形类 Mobject**（Arrow, Polygon, VGroup of shapes 等）：
           - 宽度或高度任一超限 → scale_to_fit 到可用范围内

        Args:
            mobject: 待检查的 Mobject
            max_width: 允许的最大宽度（Manim 单位）
            max_height: 允许的最大高度（Manim 单位）

        Returns:
            调整后的 Mobject（可能被原地修改，也可能返回原对象）
        """
        from manim import Text, MathTex, MarkupText

        # Tex 覆盖 MathTex，但显式列出所有文本类便于维护。
        # 任何含换行/缩放语义的文本对象都应在此注册。
        _TEXT_TYPES = (Text, MarkupText, MathTex)

        # VGroup：递归处理子元素
        if isinstance(mobject, VGroup) and len(mobject.submobjects) > 0:

            adjusted_submobjs = []
            for sub in mobject.submobjects:
                adjusted = self._precheck_mobject(sub, max_width, max_height)
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
        if isinstance(mobject, _TEXT_TYPES):
            # 先尝试换行
            fake_violation = {
                "type": (
                    "WIDTH_OVERFLOW" if obj_width > max_width else "HEIGHT_OVERFLOW"
                ),
                "column_width": max_width,
            }

            wrapped = self._layout_optimizer._apply_wrap([mobject], fake_violation)

            if wrapped and mobject.width <= max_width and mobject.height <= max_height:
                logging.info(f"[_precheck_mobject] 换行成功: {type(mobject).__name__}")
                return mobject

            # 换行不够或失败，尝试整体缩放
            scale_x = max_width / obj_width if obj_width > max_width else 1.0
            scale_y = max_height / obj_height if obj_height > max_height else 1.0
            scale_factor = min(scale_x, scale_y, 0.95)
            if scale_factor < 1.0:
                # 使用 about_point=mobject.get_center() 保持中心位置不变，
                # 避免相对锚点导致位置偏移（与 _precheck_mobject 图形分支保持一致）
                # 保留 95% 安全余量防再次越界
                min_size = LayoutOptimizer.MIN_FONT_SIZE
                current_font = getattr(mobject, "font_size", 32)
                if current_font * scale_factor < min_size:
                    scale_factor = min_size / max(current_font, 1)
                mobject.scale(
                    scale_factor,
                    about_point=mobject.get_center(),
                )
                logging.info(
                    f"[_precheck_mobject] 文本缩放(scale): "
                    f"{type(mobject).__name__} ×{scale_factor:.2f} "
                    f"(原始 w={obj_width:.2f} h={obj_height:.2f})"
                )
                return mobject

        # 图形类对象（非文本）：直接 scale_to_fit
        is_graphic = not isinstance(mobject, _TEXT_TYPES)
        if is_graphic and (obj_width > max_width or obj_height > max_height):
            scale_x = max_width / obj_width if obj_width > max_width else 1.0
            scale_y = max_height / obj_height if obj_height > max_height else 1.0
            scale_factor = min(scale_x, scale_y, 1.0)
            mobject.scale(scale_factor, about_point=mobject.get_center())
            logging.info(
                f"[_precheck_mobject] 图形缩放: "
                f"{type(mobject).__name__} ×{scale_factor:.2f} "
                f"(原始 w={obj_width:.2f} h={obj_height:.2f})"
            )
            return mobject

        return mobject

    def validate_layout(
        self,
        placed_objects: list,
        region: str = "content",
        overlap_pairs: list = None,
        allowed_overlap_pairs: list = None,
        allowed_overlap_patterns: dict = None,
        column_layout: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
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

        # column_layout 同时支持 Dict（单栏，union 校验）和 List[Dict]（多栏，per-col 校验）。
        # 统一规整为 List[Dict]，避免后续 list-style 访问对 Dict 失效。
        if isinstance(column_layout, dict):
            column_layout = [column_layout]

        # ---- 根据 region 确定边界 ----
        # 扩展 region 取值，每种栏位用对应区域的精确 X 边界。
        # 多栏 region 在传入 column_layout 时优先使用动态边界，
        # 避免静态常量与 compute_column_layout 计算结果不一致。
        _COLUMN_REGION_TO_INDEX = {
            "content_two_col_left": 0,
            "content_two_col_right": 1,
            "content_three_col_left": 0,
            "content_three_col_mid": 1,
            "content_three_col_right": 2,
        }
        if region in ("content", "content_single_col"):
            # 默认 / 向后兼容：单栏主内容区
            x_min = ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MIN
            x_max = ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MAX
            y_min = ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MIN
            y_max = ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MAX
        elif region == "content_two_col_left":
            # 两栏左栏（公式/文字）：默认 [-6.75, 1.35]
            x_min = ZoneConstants.MAIN_CONTENT_TWO_COL_X_MIN
            x_max = ZoneConstants.MAIN_CONTENT_TWO_COL_X_MAX
            y_min = ZoneConstants.MAIN_CONTENT_TWO_COL_Y_MIN
            y_max = ZoneConstants.MAIN_CONTENT_TWO_COL_Y_MAX
        elif region == "content_two_col_right":
            # 两栏右栏（图形）：默认 [1.85, 6.75]
            x_min = ZoneConstants.GRAPHICS_X_MIN
            x_max = ZoneConstants.GRAPHICS_X_MAX
            y_min = ZoneConstants.GRAPHICS_Y_MIN
            y_max = ZoneConstants.GRAPHICS_Y_MAX
        elif region == "content_three_col_left":
            # 三栏左栏（步骤/概念）
            x_min = ZoneConstants.THREE_COL_LEFT_X_MIN
            x_max = ZoneConstants.THREE_COL_LEFT_X_MAX
            y_min = ZoneConstants.THREE_COL_Y_MIN
            y_max = ZoneConstants.THREE_COL_Y_MAX
        elif region == "content_three_col_mid":
            # 三栏中栏（公式）
            x_min = ZoneConstants.THREE_COL_MID_X_MIN
            x_max = ZoneConstants.THREE_COL_MID_X_MAX
            y_min = ZoneConstants.THREE_COL_Y_MIN
            y_max = ZoneConstants.THREE_COL_Y_MAX
        elif region == "content_three_col_right":
            # 三栏右栏（图形）
            x_min = ZoneConstants.THREE_COL_RIGHT_X_MIN
            x_max = ZoneConstants.THREE_COL_RIGHT_X_MAX
            y_min = ZoneConstants.THREE_COL_Y_MIN
            y_max = ZoneConstants.THREE_COL_Y_MAX
        elif region == "graphics":
            x_min = ZoneConstants.GRAPHICS_X_MIN
            x_max = ZoneConstants.GRAPHICS_X_MAX
            y_min = ZoneConstants.GRAPHICS_Y_MIN
            y_max = ZoneConstants.GRAPHICS_Y_MAX
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
        # 动态列宽优先于静态常量，避免边界不一致
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

            # 第 2 层 - 类型/名称模式自动豁免
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

            # 动态容差 = max(0.05, max(stroke_a, stroke_b) * 0.55)
            # - 0.05 是 Manim 默认 stroke_width=4 / 72 ≈ 0.056 的安全下限
            # - 额外按对象的实际 stroke_width 加大容差（API 缺失时 try/except 兜底）
            # - 容差仍 < 最小 stroke 宽度，避免漏报真正的重叠
            base_tolerance = 0.05
            stroke_a = self._safe_get_stroke_width(obj_a)
            stroke_b = self._safe_get_stroke_width(obj_b)
            stroke_tolerance = max(stroke_a, stroke_b) * 0.55
            tolerance = max(base_tolerance, stroke_tolerance)

            if x_overlap > tolerance and y_overlap > tolerance:
                # 命中 ALLOWED_PATTERNS 模式时，stroke 接触
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
            # 对已 arrange 过的元素（Σheight + (N-1)*buff），包围盒高度
            # max(tops) - min(bottoms) 已等于其总占用高度，无需再加 buff。
            # 唯一可能漏报的情况是元素位置由调用方手动设置且未保持 buff，
            # 这种情况由 ELEMENT_OVERLAP 检查间接覆盖。
            # 单对象时本检查等价于单对象高度检查，意义不大，跳过以减少噪音。
            if len(placed_objects) >= 2:
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

        Manim 的 stroke_width 单位是 points（1 unit = 72 points），
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
        """[未实现] 计算打字动画时长。子类应重写。"""
        raise NotImplementedError(
            "LayoutScene._get_typing_run_time 应由子类重写以提供打字动画时长"
        )

    def _safe_speech_text(self, text: str) -> str:
        """[未实现] 清理语音文本中的特殊字符。子类应重写。"""
        raise NotImplementedError(
            "LayoutScene._safe_speech_text 应由子类重写以适配 TTS 引擎"
        )

    # ============================================================
    # 语音相关（占位，实际由 voiceover 处理）
    # ============================================================

    def set_speech_service(self, service):
        """设置语音服务"""
        self.speech_service = service

    def voiceover(self, text: str, **kwargs):
        """[未实现] 语音占位，子类应使用 manim_voiceover 的 with voiceover 块。"""
        raise NotImplementedError(
            "LayoutScene.voiceover 应由子类重写以接入 manim_voiceover"
        )

    # ============================================================
    # 坐标参考系（调试用，符合 layout.md 第 15 节）
    # ============================================================

    def add_coordinate_reference(self, debug: bool = True):
        """添加可视化坐标参考系（调试用）"""
        if not debug:
            return
        from manim import Axes, NumberPlane

        axes = Axes(
            x_range=[-7.5, 7.5, 1],
            y_range=[-4.5, 4.5, 1],
            x_length=15,
            y_length=9,
            axis_config={"color": "#888888", "stroke_width": 1},
            x_axis_config={"numbers_to_include": range(-7, 8)},
            y_axis_config={"numbers_to_include": range(-4, 5)},
        )
        axes.set_opacity(0.3)
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        self.add(axes, labels)
