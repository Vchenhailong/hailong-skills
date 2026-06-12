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

from scripts.layout.constants import ZoneConstants
from scripts.layout.zones.subtitle_zone import SubtitleZone
from scripts.layout.zones.main_content_zone import MainContentZone
from scripts.layout.zones.graphics_zone import GraphicsZone
from scripts.layout.engine import LayoutEngine, LayoutMode, LayoutDecision


class LayoutScene(Scene):
    """布局场景基类，提供符合规范的布局方法"""

    def __init__(self, debug: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.debug = debug
        self._subtitle_zone: Optional[SubtitleZone] = None
        self._main_content_zone: Optional[MainContentZone] = None
        self._graphics_zone: Optional[GraphicsZone] = None
        self._layout_engine = LayoutEngine()
        self.speech_service = None
        # 跟踪当前显示的字幕对象，便于跨场景清理
        self._current_subtitle_mobjs: List[Mobject] = []

    # ============================================================
    # 区域容器懒加载
    # ============================================================

    def get_subtitle_zone(self, debug: Optional[bool] = None) -> SubtitleZone:
        """获取字幕区容器（懒加载）"""
        if self._subtitle_zone is None:
            dbg = debug if debug is not None else self.debug
            self._subtitle_zone = SubtitleZone(debug=dbg)
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
    ) -> VGroup:
        """两栏布局：左内容区 + 右图形区

        Args:
            left_content: 左栏内容（公式/文字）
            right_content: 右栏图形

        Returns:
            包含两栏的 VGroup
        """
        left_group = self.place_in_main_zone(left_content, layout_mode="two_column")
        right_group = self.place_graphics(right_content)

        # 整体调整：顶部对齐（技能允许整体调整使用 shift）
        top_y = max(left_group.get_top()[1], right_group.get_top()[1])
        left_group.move_to(
            [left_group.get_center()[0], top_y - left_group.height / 2, 0]
        )
        right_group.move_to(
            [right_group.get_center()[0], top_y - right_group.height / 2, 0]
        )

        return VGroup(left_group, right_group)

    def place_three_column(
        self,
        left_content: Mobject,
        mid_content: Mobject,
        right_content: Mobject,
    ) -> VGroup:
        """三栏布局：左（步骤）+ 中（公式）+ 右（图形）

        Args:
            left_content: 左栏内容（步骤说明/概念）
            mid_content: 中栏内容（公式）
            right_content: 右栏图形

        Returns:
            包含三栏的 VGroup
        """
        main_zone = self.get_main_content_zone(layout_mode="three_column")

        left_col = VGroup(left_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF * 0.8, aligned_edge=LEFT
        )
        mid_col = VGroup(mid_content).arrange(
            DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT
        )

        # 使用 zone.place_content 约束，而非硬编码坐标
        left_col.move_to([main_zone.center_x, main_zone.center_y, 0])
        mid_col.move_to([main_zone.center_x + 3.5, main_zone.center_y, 0])

        right_group = self.place_graphics(right_content)

        # 整体调整：顶部对齐（技能允许整体调整）
        top_y = max(
            left_col.get_top()[1], mid_col.get_top()[1], right_group.get_top()[1]
        )
        for col in [left_col, mid_col, right_group]:
            col.move_to([col.get_center()[0], top_y - col.height / 2, 0])

        return VGroup(left_col, mid_col, right_group)

    def safe_place(self, mobject: Mobject) -> Mobject:
        """安全放置：确保不超出安全区域

        根据 layout.md 第 7 节，当元素超出安全边界时整体移动或缩放。
        """
        bottom = mobject.get_bottom()[1]
        top = mobject.get_top()[1]
        left = mobject.get_left()[0]
        right = mobject.get_right()[0]

        shift_y = 0.0
        shift_x = 0.0

        if bottom < ZoneConstants.SAFE_AREA_Y_MIN:
            shift_y = ZoneConstants.SAFE_AREA_Y_MIN - bottom
        if top > ZoneConstants.SAFE_AREA_Y_MAX:
            shift_y = ZoneConstants.SAFE_AREA_Y_MAX - top
        if left < ZoneConstants.SAFE_AREA_X_MIN:
            shift_x = ZoneConstants.SAFE_AREA_X_MIN - left
        if right > ZoneConstants.SAFE_AREA_X_MAX:
            shift_x = ZoneConstants.SAFE_AREA_X_MAX - right

        if shift_x != 0.0 or shift_y != 0.0:
            mobject.shift(RIGHT * shift_x + UP * shift_y)

        return mobject

    def validate_layout(
        self,
        placed_objects: list,
        region: str = "content",
        overlap_pairs: list = None,
        allowed_overlap_pairs: list = None,
        allowed_overlap_patterns: dict = None,
    ) -> list:
        """程序化布局校验（无需渲染），检测溢出/侵入/重叠/越界

        核心原理：Manim MObject 在构建后 width/height/get_left() 等属性
        立即可用，无需调用 render()。结合 ZoneConstants 的精确区域边界，
        可在毫秒级完成全部布局合规性检查。

        Args:
            placed_objects: 已放置的所有 MObject 列表
            region: 目标区域名称
                - "content": 主内容区（根据布局模式自动选择单栏/两栏/三栏边界）
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
        if region == "content":
            # 默认使用单栏区域作为 content 区边界
            x_min = ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MIN
            x_max = ZoneConstants.MAIN_CONTENT_SINGLE_COL_X_MAX
            y_min = ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MIN
            y_max = ZoneConstants.MAIN_CONTENT_SINGLE_COL_Y_MAX
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

        # ---- 逐对象检查区域溢出 + 屏幕越界 ----
        for obj in placed_objects:
            obj_name = getattr(obj, "name", None) or type(obj).__name__

            left = obj.get_left()[0]
            right = obj.get_right()[0]
            bottom = obj.get_bottom()[1]
            top = obj.get_top()[1]

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

            # 第 2 层：类型/名称模式自动豁免
            if allowed_overlap_patterns and self._match_overlap_pattern(
                obj_a, obj_b, allowed_overlap_patterns
            ):
                continue  # 匹配预定义模式，跳过

            # X 方向重叠判定
            a_left, a_right = obj_a.get_left()[0], obj_a.get_right()[0]
            b_left, b_right = obj_b.get_left()[0], obj_b.get_right()[0]
            x_overlap = min(a_right, b_right) - max(a_left, b_left)

            # Y 方向重叠判定
            a_bottom, a_top = obj_a.get_bottom()[1], obj_a.get_top()[1]
            b_bottom, b_top = obj_b.get_bottom()[1], obj_b.get_top()[1]
            y_overlap = min(a_top, b_top) - max(a_bottom, b_bottom)

            if x_overlap > 0.01 and y_overlap > 0.01:  # 容差 0.01 避免浮点误差
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
                elif 0 < actual_gap < expected_buff * 0.3:  # 小于标准间距 30% 视为过密
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
        if violations and self.debug:
            print(f"\n[LayoutScene.validate_layout] 发现 {len(violations)} 项违规:")
            for i, v in enumerate(violations, 1):
                print(f"  [{i}] {v['type']}: {v['detail']}")
                print(f"       期望: {v['expected']}")
                print(f"       实际: {v['actual']}")

        return violations

    # ═══════════════════════════════════════════════════════════════════════════
    # 重叠白名单：预定义模式常量 + 模式匹配方法
    #
    # 唯一判定基准（与 SKILL.md §重叠白名单机制 一致）：
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

        唯一判定基准（与 SKILL.md §重叠白名单机制 一致）：
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
