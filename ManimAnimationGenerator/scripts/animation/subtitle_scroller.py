#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕滚动管理器 - 预计算滚动系统

核心设计：
1. 字体大小 ↔ 行高 精确关联（动态计算，防重叠/遮盖）
2. 预计算滚动时序、距离、时长（所有参数提前计算好）
3. 前驱行与后继行联动滚动（速度、间距一致）
4. 底部固定位置（防止多行字幕抖动）
5. 字幕底衬（自适应半透明背景）

字体大小 ↔ 行高 换算公式：
- Manim 中 font_size 单位是 points，1 inch = 72 points
- 默认帧高 8 单位对应 8 inches
- line_height = font_size / 72 * frame_scale * line_height_ratio
- font_size=18 → line_height ≈ 0.29 单位
"""

from manim import (
    Scene,
    VGroup,
    Text,
    RoundedRectangle,
    UP,
    DOWN,
    LEFT,
    FadeOut,
)
from typing import List, Optional, Tuple
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
    4. 字幕底衬视觉设计（自适应半透明背景）
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
        # 滚动动画过渡时长（仅控制滚动动画平滑度，不决定显示时间）
        self._scroll_duration = ZC.SUBTITLE_SCROLL_DURATION
        # 语音朗读速度（字符/秒），用于计算每行显示时间
        self._speech_speed = ZC.SUBTITLE_SPEECH_SPEED
        # 底衬样式
        self._bg_color = ZC.SUBTITLE_BACKGROUND_COLOR
        self._bg_opacity = ZC.SUBTITLE_BACKGROUND_OPACITY
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
        # 修复 P0-D：所有 N 行一次性 arrange 好的整组（用于整组平移 + 裁切）
        # 关键设计：滚动 = 整组平移一行高度 + 同步 opacity 切换
        # 任意瞬间字幕区只显示 visible_lines 行，且位置固定不变
        self._all_line_group: Optional[VGroup] = None
        # 当前可见的行索引
        self._visible_indices: List[int] = []
        # 字幕组（包含底衬、文字）
        self._subtitle_group: Optional[VGroup] = None
        self._text_group: Optional[VGroup] = None

    @staticmethod
    def _calc_line_height(font_size: int) -> float:
        """根据字体大小计算实际行高

        公式：line_height = (font_size / 72.0) * SUBTITLE_LINE_HEIGHT_RATIO

        Manim 默认 1 单位 = 1 inch = 72 points，font_size 本身就是 points，
        因此 font_size/72 即为换算到 Manim 单位的基础值，再乘以行高系数。

        修复 P0-N4：原公式错误地多乘了 MANIM_FONT_TO_UNIT_RATIO（8/72≈0.111），
        导致实际行高只有正确值的 1/8（font_size=18 → 0.039 而非 ~0.35），
        字幕行间几乎贴在一起，多行滚动时频繁重叠。已修正为正确的换算公式。
        实测验证：font_size=18 → line_height ≈ 0.35，与 Manim Text 实际渲染高度一致。

        Args:
            font_size: 字体大小（points）

        Returns:
            行高（manim 单位）
        """
        return (font_size / 72.0) * ZC.SUBTITLE_LINE_HEIGHT_RATIO

    def _create_background(self, width: float, height: float) -> RoundedRectangle:
        """创建字幕底衬

        底衬大小根据文字内容动态计算，确保完全包裹。

        Args:
            width: 文字宽度
            height: 文字高度

        Returns:
            底衬 RoundedRectangle
        """
        padding_h = self._line_height * 0.3
        padding_w = self._line_height * 0.8

        bg = RoundedRectangle(
            width=width + padding_w * 2,
            height=height + padding_h * 2,
            corner_radius=ZC.SUBTITLE_BACKGROUND_CORNER_RADIUS,
            stroke_width=0,
            fill_color=self._bg_color,
            fill_opacity=self._bg_opacity,
        )
        return bg

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

    def _precompute_scroll_events(
        self, lines: List[str], max_duration: Optional[float] = None
    ) -> List[ScrollEvent]:
        """预计算所有滚动事件（基于语音速度动态计算显示时间）

        时序关联规则（json_schema.md §2.5）：
        - 原始触发时间基于 SPEECH_SPEED（4字符/秒）计算
        - 若提供了 max_duration 且原始总时间 > max_duration，
          则对所有 trigger_time 进行等比缩放，确保滚动在 Atom 生命周期内完成

        Args:
            lines: 所有字幕行的文本内容列表
            max_duration: Atom 总时长上限（秒），用于约束滚动时序

        Returns:
            滚动事件列表
        """
        events = []
        # 需要滚动的次数 = 总行数 - 可见行数
        scroll_count = len(lines) - self._visible_lines
        if scroll_count <= 0:
            return events

        # 计算每行的显示时间（基于字符数 / 语音速度）
        def calc_display_time(text: str) -> float:
            """根据文本字符数计算朗读显示时间，最短保底 1.5 秒"""
            char_count = len(text.strip())
            if char_count == 0:
                return 1.5
            return max(char_count / self._speech_speed, 1.5)

        line_display_times = [calc_display_time(line) for line in lines]

        # 累积时间：每次滚动后，新滚入的行需要完整显示
        # 第 0 次（初始）：前 visible_lines 行同时显示，取其中最长的一行作为首屏停留时间
        cumulative_time = (
            max(line_display_times[: self._visible_lines])
            if self._visible_lines > 0
            else 3.0
        )

        raw_events = []
        for i in range(scroll_count):
            # 本次滚出的行索引和滚入的行索引
            out_idx = i
            in_idx = i + self._visible_lines

            raw_events.append(
                {
                    "trigger_time": cumulative_time,
                    "scroll_distance": self._scroll_unit,
                    "duration": self._scroll_duration,
                    "out_line_idx": out_idx,
                    "in_line_idx": in_idx,
                }
            )

            # 下一次滚动触发时间 = 当前时间 + 新滚入行的显示时间
            cumulative_time += line_display_times[in_idx]

        # ── 时序缩放：若总时间超限，等比压缩 ──
        total_raw_time = cumulative_time
        if max_duration is not None and total_raw_time > max_duration:
            scale_factor = max_duration / total_raw_time
            for ev in raw_events:
                ev["trigger_time"] *= scale_factor

        for ev in raw_events:
            events.append(ScrollEvent(**ev))

        return events

    def show(
        self, speech: str, max_duration: Optional[float] = None
    ) -> Tuple[float, List[Text]]:
        """显示字幕，超出2行时自动滚动

        滚动时序与 Atom 关联：
        - 所有滚动事件的 trigger_time 以 max_duration 为上限进行缩放
        - 若未提供 max_duration，则使用预计算的语音速度时间（可能超过 Atom 生命周期）

        Args:
            speech: 语音文本
            max_duration: 该 Atom 的总时长（秒），用于约束滚动时序。
                         当计算出的总滚动时间 > max_duration 时，
                         等比压缩每个触发时间，确保滚动在 Atom 结束前完成。

        Returns:
            (总滚动时间, 可见字幕对象列表)
        """
        # ── 生命周期清理：先移除上一轮的字幕组（幂等，无残留时 no-op）──
        self.hide()

        # 1. 拆分文本为行
        lines = split_utterance(speech, max_chars=self._chars_per_line)

        # 2. 创建所有行对象
        self._all_line_mobjs = [
            Text(line_text, font_size=self._font_size, color=self._text_color)
            for line_text in lines
        ]

        # 3. 初始化可见索引
        self._visible_indices = list(range(min(self._visible_lines, len(lines))))

        # 4. 预计算滚动事件（基于字符数动态计算显示时间，支持 max_duration 缩放）
        scroll_events = self._precompute_scroll_events(lines, max_duration=max_duration)

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
        """构建字幕组（底衬+文字）

        修复 P0-D：原实现只创建"当前可见"的 2 行 VGroup，滚动时通过
        "旧 2 行上移 + 新行飞入 + 旧行淡出"三组并行 animate 实现滚动，
        导致过渡期间 3 行在同一字幕区并存 → 文字重叠 + 错位。
        现改为"整组预排 + 整体平移 + 边界淡入淡出"模式：
        1. 把所有 N 行一次性 VGroup.arrange(DOWN, buff=line_spacing)
        2. 整体平移到字幕区：line[0].top y = SUBTITLE_ZONE_TOP_Y - 0.14
           （与原"两行居中于字幕区底部"设计一致，line[0] 在上、line[1] 在下）
        3. 前 visible_lines 行 opacity=1，其余 opacity=0
        4. 底衬居中于"当前可见 2 行"（即 line[0] + line[1]）

        滚动时只需将 _all_line_group 整组平移一行高度（UP * scroll_unit），
        同步把滚出顶部的行 opacity=0，滚入底部的行 opacity=1。
        任意瞬间字幕区只显示 2 行固定位置，0 错位、0 飞入、0 漂出。
        """
        # 1) 预排所有 N 行（一次性 arrange DOWN）
        #    arrange(DOWN) 后 line[0] 在最上，line[N-1] 在最下
        self._all_line_group = VGroup(*self._all_line_mobjs)
        self._all_line_group.arrange(DOWN, buff=self._line_spacing, aligned_edge=LEFT)

        # 2) 整体平移：line[0].top y 位于字幕区内固定位置
        #    字幕区：Y ∈ [-3.85, -2.8]，高 1.05
        #    两行字幕总高 = 2L + S = 0.91 → 留 0.14 padding
        #    line[0].top y = -2.8 - 0.14 = -2.94（与原设计一致）
        target_line0_top_y = ZC.SUBTITLE_ZONE_TOP_Y - 0.14
        current_top_y = self._all_line_group.get_top()[1]
        self._all_line_group.shift(UP * (target_line0_top_y - current_top_y))

        # 3) 初始可见性：前 visible_lines 行 opacity=1，其余 opacity=0
        for i, line in enumerate(self._all_line_mobjs):
            line.set_opacity(1 if i < self._visible_lines else 0)

        # 4) 创建底衬（按当前可见 2 行的尺寸）
        #    注意：line[0] + line[1] 的实际位置由 _all_line_group 决定，
        #    但它们的 width/height 独立于位置（get_width/height 测的是尺寸）
        visible_mobjs = [self._all_line_mobjs[i] for i in self._visible_indices]
        text_width = max(visible_mobjs[0].width, visible_mobjs[1].width)
        text_height = (
            visible_mobjs[0].height + visible_mobjs[1].height + self._line_spacing
        )
        bg = self._create_background(text_width, text_height)

        # 5) 底衬居中于当前可见 2 行（取 line[0] 和 line[1] 中心的均值）
        visible_center_y = (
            visible_mobjs[0].get_center()[1] + visible_mobjs[1].get_center()[1]
        ) / 2
        bg.move_to([0, visible_center_y, 0])

        # 6) 组装：底衬在下层，all_line_group 在上层
        self._subtitle_group = VGroup(bg, self._all_line_group)

        # 兼容性：维护 self._text_group（虽然新逻辑不再使用，但保留属性避免外部引用报错）
        # 注意：这里创建一个仅用于测量/兼容的 VGroup，不影响渲染位置
        self._text_group = VGroup(*visible_mobjs)

        # 7) 顶部边界约束（防止侵入主内容区）
        self._enforce_top_boundary(self._subtitle_group)
        # 8) 把底衬重新对齐到（可能被平移后的）可见 2 行中心
        #    _enforce_top_boundary 可能下移了 subtitle_group，
        #    需要重新计算可见 2 行中心并把 bg 重新对齐
        self._align_bg_to_visible_lines()

        self._scene.add(self._subtitle_group)

    def _align_bg_to_visible_lines(self) -> None:
        """把底衬重新对齐到当前可见 2 行的中心

        修复 P0-D：在 _enforce_top_boundary 可能平移了 subtitle_group 之后，
        底衬位置需要同步更新。否则底衬会与可见 2 行错位。
        """
        if not self._subtitle_group or len(self._visible_indices) < 2:
            return
        bg = self._subtitle_group[0]
        visible_mobjs = [self._all_line_mobjs[i] for i in self._visible_indices]
        visible_center_y = (
            visible_mobjs[0].get_center()[1] + visible_mobjs[1].get_center()[1]
        ) / 2
        bg.move_to([0, visible_center_y, 0])

    def _update_background_size(self) -> None:
        """根据当前可见 2 行更新底衬尺寸

        修复 P0-D：滚动后当前可见 2 行的成员发生变化（line[k] 离开，
        line[k+visible_lines] 进入），新行的 width 可能不同，
        需要重新调整底衬宽度。
        """
        if not self._subtitle_group or len(self._visible_indices) < 2:
            return
        visible_mobjs = [self._all_line_mobjs[i] for i in self._visible_indices]
        new_width = max(visible_mobjs[0].width, visible_mobjs[1].width)
        new_height = (
            visible_mobjs[0].height + visible_mobjs[1].height + self._line_spacing
        )
        padding_h = self._line_height * 0.3
        padding_w = self._line_height * 0.8
        bg = self._subtitle_group[0]
        bg.stretch_to_fit_width(new_width + padding_w * 2)
        bg.stretch_to_fit_height(new_height + padding_h * 2)
        # 重新对齐到当前可见 2 行中心
        self._align_bg_to_visible_lines()

    def _execute_scroll(self, event: ScrollEvent) -> None:
        """执行单次滚动动画（整组平移 + 同步裁切）

        修复 P0-D：原实现用 3 个并行 animate（旧 2 行上移 + 新行飞入 + 旧行淡出），
        导致过渡期间旧 2 行与新飞入行在同一字幕区并存 → 文字重叠 + 错位。
        现改为"整组预排 + 整体平移 + 边界淡入淡出"：
        1. 新行 opacity 立即设为 1（准备滚入）
        2. 整组 _all_line_group 向上平移一行高度（UP * scroll_unit）
        3. 旧行 opacity 同步淡出到 0
        4. 滚出顶部的行自然落到字幕区上方（被 opacity=0 隐藏）
        5. 滚入底部的行自然进入字幕区（opacity=1 显示）

        关键：任意瞬间字幕区只显示 2 行（位置固定不变），
        没有"飞入"、"漂出"、"错位"现象。

        Args:
            event: 滚动事件
        """
        out_line = self._all_line_mobjs[event.out_line_idx]
        in_line = self._all_line_mobjs[event.in_line_idx]

        # 滚入的新行：先设为可见（与整组平移同步进行，无飞入延迟）
        in_line.set_opacity(1)

        # 整组平移一行高度 + 同步设置滚出行为隐藏
        # 两个 animate 并行：整组上移 + 滚出行淡出
        # 字幕区位置固定：line[0] 和 line[1] 始终在同一位置
        self._scene.play(
            self._all_line_group.animate.shift(UP * event.scroll_distance),
            out_line.animate.set_opacity(0),
            run_time=event.duration,
        )

        # 更新可见索引
        self._visible_indices.pop(0)
        self._visible_indices.append(event.in_line_idx)

        # 兼容性：更新 self._text_group 引用
        visible_mobjs = [self._all_line_mobjs[i] for i in self._visible_indices]
        self._text_group = VGroup(*visible_mobjs)

        # 更新底衬尺寸（新行的宽度可能不同）
        self._update_background_size()

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
