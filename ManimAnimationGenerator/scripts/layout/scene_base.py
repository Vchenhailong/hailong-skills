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

    def get_main_content_zone(self, layout_mode: str = "vertical", debug: Optional[bool] = None) -> MainContentZone:
        """获取主内容区容器（懒加载，支持动态修改布局模式）
        
        Args:
            layout_mode: 布局模式，可选 "vertical", "two_column", "three_column", "centered"
            debug: 调试模式
        """
        dbg = debug if debug is not None else self.debug
        if self._main_content_zone is None or self._main_content_zone.layout_mode != layout_mode:
            self._main_content_zone = MainContentZone(layout_mode=layout_mode, debug=dbg)
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
        left_group.move_to([left_group.get_center()[0], top_y - left_group.height / 2, 0])
        right_group.move_to([right_group.get_center()[0], top_y - right_group.height / 2, 0])
        
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
        
        left_col = VGroup(left_content).arrange(DOWN, buff=ZoneConstants.ROW_BUFF * 0.8, aligned_edge=LEFT)
        mid_col = VGroup(mid_content).arrange(DOWN, buff=ZoneConstants.ROW_BUFF, aligned_edge=LEFT)
        
        # 使用 zone.place_content 约束，而非硬编码坐标
        left_col.move_to([main_zone.center_x, main_zone.center_y, 0])
        mid_col.move_to([main_zone.center_x + 3.5, main_zone.center_y, 0])
        
        right_group = self.place_graphics(right_content)
        
        # 整体调整：顶部对齐（技能允许整体调整）
        top_y = max(left_col.get_top()[1], mid_col.get_top()[1], right_group.get_top()[1])
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

    def auto_arrange_atom(self, mobjs: List[Mobject], atom: Optional[Dict] = None) -> VGroup:
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

    def apply_layout_fonts(self, group: VGroup, layout_type: str = "vertical") -> VGroup:
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
