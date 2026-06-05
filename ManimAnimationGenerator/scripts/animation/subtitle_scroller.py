#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕滚动管理器 - 预计算滚动系统

核心设计：
1. 字体大小 ↔ 行高 精确关联（动态计算，防重叠/遮盖）
2. 预计算滚动时序、距离、时长（所有参数提前计算好）
3. 前驱行与后继行联动滚动（速度、间距一致）
4. 底部固定位置（防止多行字幕抖动）
5. 字幕底衬+左侧强调条（借鉴 mathVideoMaker 视觉设计）

字体大小 ↔ 行高 换算公式：
- Manim 中 font_size 单位是 points，1 inch = 72 points
- 默认帧高 8 单位对应 8 inches
- line_height = font_size / 72 * frame_scale * line_height_ratio
- font_size=18 → line_height ≈ 0.29 单位
"""

from manim import Scene, VGroup, Text, Rectangle, RoundedRectangle, UP, DOWN, LEFT, FadeOut
from typing import List, Tuple, Optional
from dataclasses import dataclass
from scripts.layout.zones.subtitle_zone import SubtitleZone
from scripts.layout.constants import ZoneConstants as ZC
from scripts.subtitle_splitter import split_utterance


@dataclass
class ScrollEvent:
    """预计算的滚动事件"""
    # 触发时间（秒）
    trigger_time: float
    # 滚动距离（单位）
    scroll_distance: float
    # 动画时长（秒）
    duration: float
    # 滚出的行索引
    out_line_idx: int
    # 滚入的行索引
    in_line_idx: int


class SubtitleScroller:
    """字幕滚动管理器（预计算滚动系统）
    
    职责：
    1. 字体大小 ↔ 行高精确关联
    2. 预计算所有滚动事件（时序、距离、时长）
    3. 管理字幕行创建、排列、滚动动画
    4. 字幕底衬+左侧强调条视觉设计
    """
    
    def __init__(
        self,
        scene: Scene,
        subtitle_zone: SubtitleZone,
        font_size: int = ZC.SUBTITLE_FONT_SIZE,
        chars_per_line: int = 35,
    ):
        """初始化字幕滚动管理器
        
        Args:
            scene: Manim 场景实例
            subtitle_zone: 字幕区容器
            font_size: 字幕字号（默认 18）
            chars_per_line: 每行最大字符数
        """
        self._scene = scene
        self._zone = subtitle_zone
        self._font_size = font_size
        self._chars_per_line = chars_per_line
        
        # 可见行数（固定2行）
        self._visible_lines = ZC.SUBTITLE_VISIBLE_LINES
        # 滚动时长
        self._scroll_duration = ZC.SUBTITLE_SCROLL_DURATION
        # 底衬样式
        self._bg_color = ZC.SUBTITLE_BACKGROUND_COLOR
        self._bg_opacity = ZC.SUBTITLE_BACKGROUND_OPACITY
        self._accent_color = ZC.SUBTITLE_ACCENT_COLOR
        # 字幕颜色
        self._text_color = ZC.SUBTITLE_TEXT_COLOR
        # 底部固定位置
        self._bottom_fixed_y = ZC.SUBTITLE_ZONE_BOTTOM_FIXED_Y
        
        # 动态计算行高（字体大小 → 行高）
        self._line_height = self._calc_line_height(font_size)
        # 动态计算行间距（基于行高的比例）
        self._line_spacing = self._line_height * ZC.SUBTITLE_LINE_SPACING_RATIO
        # 滚动单位 = 行高 + 行间距
        self._scroll_unit = self._line_height + self._line_spacing
        
        # 运行时的行对象
        self._all_line_mobjs: List[Text] = []
        # 当前可见的行索引
        self._visible_indices: List[int] = []
        # 字幕组（包含底衬、强调条、文字）
        self._subtitle_group: Optional[VGroup] = None
        self._text_group: Optional[VGroup] = None
    
    @staticmethod
    def _calc_line_height(font_size: int) -> float:
        """根据字体大小计算实际行高
        
        公式：line_height = font_size / 72 * frame_scale * line_height_ratio
        
        Args:
            font_size: 字体大小（points）
            
        Returns:
            行高（manim 单位）
        """
        return (font_size / 72.0) * ZC.MANIM_FONT_TO_UNIT_RATIO * ZC.SUBTITLE_LINE_HEIGHT_RATIO
    
    def _create_background(self, width: float, height: float) -> Tuple[RoundedRectangle, Rectangle]:
        """创建字幕底衬和强调条
        
        底衬大小根据文字内容动态计算，确保完全包裹。
        
        Args:
            width: 文字宽度
            height: 文字高度
            
        Returns:
            (底衬, 强调条)
        """
        # 底衬内边距（基于行高计算）
        padding_h = self._line_height * 0.3
        padding_w = self._line_height * 0.8
        
        # 底衬
        bg = RoundedRectangle(
            width=width + padding_w * 2,
            height=height + padding_h * 2,
            corner_radius=ZC.SUBTITLE_BACKGROUND_CORNER_RADIUS,
            stroke_width=0,
            fill_color=self._bg_color,
            fill_opacity=self._bg_opacity,
        )
        
        # 强调条（左侧金色竖条，高度为文字高度的60%）
        accent = RoundedRectangle(
            width=ZC.SUBTITLE_ACCENT_WIDTH,
            height=height * 0.6,
            corner_radius=ZC.SUBTITLE_ACCENT_CORNER_RADIUS,
            stroke_width=0,
            fill_color=self._accent_color,
            fill_opacity=1.0,
        )
        # 强调条定位到底衬左侧
        accent.move_to([
            bg.get_left()[0] + ZC.SUBTITLE_ACCENT_OFFSET_LEFT,
            bg.get_center()[1],
            0
        ])
        
        return bg, accent
    
    def _align_to_bottom(self, group: VGroup) -> VGroup:
        """将字幕组底部对齐到固定位置（防抖动）
        
        Args:
            group: 字幕组
            
        Returns:
            已调整位置的对象
        """
        current_bottom = group.get_bottom()[1]
        if abs(current_bottom - self._bottom_fixed_y) > 0.001:
            group.shift(DOWN * (current_bottom - self._bottom_fixed_y))
        return group
    
    def _enforce_top_boundary(self, group: VGroup) -> VGroup:
        """强制执行字幕上界约束（防止侵入主内容区）
        
        Args:
            group: 字幕组
            
        Returns:
            已调整位置的对象
        """
        top_y = group.get_top()[1]
        max_top_y = ZC.SUBTITLE_ZONE_TOP_Y
        if top_y > max_top_y:
            group.shift(DOWN * (top_y - max_top_y))
        return group
    
    def _precompute_scroll_events(self, total_lines: int) -> List[ScrollEvent]:
        """预计算所有滚动事件
        
        Args:
            total_lines: 总行数
            
        Returns:
            滚动事件列表
        """
        events = []
        # 需要滚动的次数 = 总行数 - 可见行数
        scroll_count = total_lines - self._visible_lines
        
        for i in range(scroll_count):
            events.append(ScrollEvent(
                trigger_time=(i + 1) * (self._scroll_duration + 0.15),  # 间隔0.15s
                scroll_distance=self._scroll_unit,  # 动态计算：行高 + 间距
                duration=self._scroll_duration,
                out_line_idx=i,       # 第1行滚出
                in_line_idx=i + self._visible_lines,  # 第3行滚入
            ))
        
        return events
    
    def show(self, speech: str) -> Tuple[float, List[Text]]:
        """显示字幕，超出2行时自动滚动
        
        Args:
            speech: 语音文本
            
        Returns:
            (总滚动时间, 可见字幕对象列表)
        """
        # 1. 拆分文本为行
        lines = split_utterance(speech, max_chars=self._chars_per_line)
        
        # 2. 创建所有行对象
        self._all_line_mobjs = [
            Text(line_text, font_size=self._font_size, color=self._text_color)
            for line_text in lines
        ]
        
        # 3. 初始化可见索引
        self._visible_indices = list(range(min(self._visible_lines, len(lines))))
        
        # 4. 预计算滚动事件（使用动态滚动单位）
        scroll_events = self._precompute_scroll_events(len(lines))
        
        # 5. 构建字幕组
        self._build_subtitle_group()
        
        # 6. 逐个触发滚动事件
        total_time = 0.0
        for event in scroll_events:
            # 等待触发时间
            if event.trigger_time - total_time > 0.01:
                self._scene.wait(event.trigger_time - total_time)
            total_time = event.trigger_time
            
            # 执行滚动动画
            self._execute_scroll(event)
        
        return (total_time, [self._all_line_mobjs[i] for i in self._visible_indices])
    
    def _build_subtitle_group(self) -> None:
        """构建字幕组（底衬+强调条+文字）"""
        # 获取可见行对象
        visible_mobjs = [self._all_line_mobjs[i] for i in self._visible_indices]
        
        # 排列文字（底部对齐，使用动态行间距）
        self._text_group = VGroup(*visible_mobjs)
        self._text_group.arrange(DOWN, buff=self._line_spacing, aligned_edge=LEFT)
        
        # 创建底衬（根据实际文字大小）
        text_width = self._text_group.get_width()
        text_height = self._text_group.get_height()
        bg, accent = self._create_background(text_width, text_height)
        
        # 组装字幕组（底衬在最下层）
        self._subtitle_group = VGroup(bg, accent, self._text_group)
        
        # 底部对齐 + 上界约束
        self._align_to_bottom(self._subtitle_group)
        self._enforce_top_boundary(self._subtitle_group)
        
        # 添加到场景
        self._scene.add(self._subtitle_group)
    
    def _execute_scroll(self, event: ScrollEvent) -> None:
        """执行单次滚动动画（前驱滚出 = 后继滚入）
        
        使用动态计算的滚动距离，确保移出行 = 移入行。
        
        Args:
            event: 滚动事件
        """
        # 1. 滚出的行（即将消失）
        out_line = self._all_line_mobjs[event.out_line_idx]
        # 2. 滚入的行（即将出现）
        in_line = self._all_line_mobjs[event.in_line_idx]
        # 3. 当前第2行（保持位置参照）
        second_line = self._all_line_mobjs[self._visible_indices[1]]
        
        # 设置滚入行初始位置（在可见组下方）
        in_line.align_to(second_line, LEFT)
        in_line.move_to([
            in_line.get_center()[0],
            self._text_group.get_bottom()[1] - self._line_spacing,
            0
        ])
        in_line.set_opacity(0)
        
        # 联动滚动动画：
        # - 可见文字组整体上移（使用动态滚动距离）
        # - 滚入行同步上移并淡入
        # - 滚出行淡出
        self._scene.play(
            self._text_group.animate.shift(UP * event.scroll_distance),
            in_line.animate.shift(UP * event.scroll_distance).set_opacity(1),
            out_line.animate.set_opacity(0),
            run_time=event.duration,
        )
        
        # 移除已滚出的行
        self._scene.remove(out_line)
        
        # 更新可见索引
        self._visible_indices.pop(0)
        self._visible_indices.append(event.in_line_idx)
        
        # 重新排列可见文字组（使用动态行间距）
        visible_mobjs = [self._all_line_mobjs[i] for i in self._visible_indices]
        self._text_group = VGroup(*visible_mobjs)
        self._text_group.arrange(DOWN, buff=self._line_spacing, aligned_edge=LEFT)
        
        # 重建字幕组并重新对齐
        text_width = self._text_group.get_width()
        text_height = self._text_group.get_height()
        bg, accent = self._create_background(text_width, text_height)
        
        # 移除旧字幕组
        self._scene.remove(self._subtitle_group)
        
        # 创建新字幕组
        self._subtitle_group = VGroup(bg, accent, self._text_group)
        self._align_to_bottom(self._subtitle_group)
        self._enforce_top_boundary(self._subtitle_group)
        self._scene.add(self._subtitle_group)
    
    def hide(self) -> None:
        """隐藏字幕"""
        if self._subtitle_group:
            self._scene.play(FadeOut(self._subtitle_group))
            self._scene.remove(self._subtitle_group)
            self._subtitle_group = None
    
    @property
    def line_height(self) -> float:
        """获取当前字体大小对应的行高"""
        return self._line_height
    
    @property
    def scroll_unit(self) -> float:
        """获取滚动单位（行高 + 行间距）"""
        return self._scroll_unit