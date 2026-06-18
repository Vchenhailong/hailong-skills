#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕滚动管理器 - 预置位 + UpdateFromAlphaFunc 模式

设计原则（对应 references/subtitle_scroller.md）：
1. 可见字幕最多 2 行，每行不超过 20 字
2. 字幕速度 4 字/秒
3. 滚动时：旧第1行消失，旧第2行移入原第1行位置，新行移入原第2行位置
4. 滚动时长和行间距全程一致

核心实现：
- 所有行在 _prepare 时就放在最终位置上（slot_0_y 或 slot_1_y）
- 用 UpdateFromAlphaFunc(alpha=0→1) 驱动动画：
  - 旧第1行：opacity 1→0，y 不变（原地淡出）
  - 旧第2行：opacity 1→1（保持），y slot_1_y→slot_0_y（上移）
  - 新  行：opacity 0→1，y slot_1_y→slot_1_y（从 slot_1_y 开始，淡入）
- 滚动期间新行停在 slot_1_y（不额外偏移），旧第1行原地淡出
- 动画结束后新行就在 slot_1_y，无需回调修正
- 不依赖任何 callback / slot 引用
"""

from manim import Scene, VGroup, Text, UP, DOWN
from typing import List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from scripts.layout.zones.subtitle_zone import SubtitleZone
from scripts.layout.constants import ZoneConstants as ZC
from scripts.subtitle_splitter import split_utterance


@dataclass
class ScrollEvent:
    trigger_time: float
    duration: float
    in_line_idx: int


class SubtitleScroller:
    """
    字幕滚动管理器（预置位 + alpha 驱动模式）

    与 references/subtitle_scroller.md 对照：
    - 最多 2 行可见，每行 ≤ 20 字（chars_per_line）
    - 速度 4 字/秒（_speech_speed）
    - 滚动触发时机：读完当前屏（2行）的字符总时间
    - 滚动动画：旧第1行消失，旧第2行移入原第1行，新行移入原第2行
    - 滚动时长一致（_scroll_duration）
    """

    def __init__(
        self,
        scene: Scene,
        subtitle_zone: SubtitleZone,
        font_size: int = 18,
        chars_per_line: int = ZC.SUBTITLE_CHARS_PER_LINE,
    ):
        self._scene = scene
        self._zone = subtitle_zone
        self._font_size = font_size
        self._chars_per_line = chars_per_line
        self._scroll_duration = ZC.SUBTITLE_SCROLL_DURATION
        self._speech_speed = ZC.SUBTITLE_SPEECH_SPEED
        self._text_color = ZC.SUBTITLE_TEXT_COLOR

        # 行高
        self._line_height = (font_size / 72.0) * ZC.SUBTITLE_LINE_HEIGHT_RATIO
        self._line_spacing = self._line_height * ZC.SUBTITLE_LINE_SPACING_RATIO
        self._row_pitch = self._line_height + self._line_spacing

        # 槽位坐标
        zone_center_y = (subtitle_zone.y_min + subtitle_zone.y_max) / 2
        self._slot_0_y = zone_center_y + self._row_pitch / 2  # 上行
        self._slot_1_y = zone_center_y - self._row_pitch / 2  # 下行

        # 字幕行
        self._all_lines: List[Text] = []
        self._scroll_events: List[ScrollEvent] = []
        self._last_tick_time = 0.0
        self._speech_start_time = 0.0

    # ─────────────────────────────────────────────────────────────────
    # 公开 API
    # ─────────────────────────────────────────────────────────────────

    def show(self, speech: str, max_duration: Optional[float] = None) -> Tuple[float, List[Text]]:
        """显示字幕（串行播放，与主内容并发时用 build_subtitle_animation）"""
        anim = self.build_subtitle_animation(speech, max_duration=max_duration)
        duration = self.total_duration
        self._scene.play(anim, run_time=duration)
        return duration, [self._all_lines[0], self._all_lines[1]]

    def build_subtitle_animation(self, speech: str, max_duration: Optional[float] = None):
        """返回 Succession 动画对象，可与主内容并发播放

        字幕总时长 = 所有字符的朗读时间（字符数 / 4.0 字/秒）
                  + 滚动动画总时长（滚动次数 × scroll_duration）
        """
        from manim import Succession, Wait
        self._prepare(speech)
        n = len(self._all_lines)
        if n == 0:
            self._total_duration = max_duration or 1.0
            return Wait(run_time=self._total_duration)

        char_count = sum(len(l.text) for l in self._all_lines)
        speech_duration = char_count / self._speech_speed
        scroll_duration_total = len(self._scroll_events) * self._scroll_duration
        self._total_duration = speech_duration + scroll_duration_total

        if not self._scroll_events:
            return Wait(run_time=max(0.1, self._total_duration))

        return self._build_succession()

    @property
    def total_duration(self) -> float:
        return getattr(self, "_total_duration", 0.0)

    def hide(self) -> None:
        for line in self._all_lines:
            if line in self._scene.mobjects:
                self._scene.remove(line)
        self._all_lines = []
        self._scroll_events = []

    # ─────────────────────────────────────────────────────────────────
    # 内部实现
    # ─────────────────────────────────────────────────────────────────

    def _prepare(self, speech: str) -> None:
        """准备字幕：拆分 + 创建 Text + 预置位"""
        self.hide()
        lines = split_utterance(speech, max_chars=self._chars_per_line)
        if not lines:
            return

        self._all_lines = [
            Text(t, font_size=self._font_size, color=self._text_color)
            for t in lines
        ]

        # 预置位：每行放在它最终显示的槽位上（slot_0_y 或 slot_1_y）
        # L0 → slot_0, L1 → slot_1
        # 滚动发生后：L1 → slot_0, L2 → slot_1, ...
        # 滚动前的行：按 (i % 2) 决定在 slot_0 还是 slot_1
        for i, line in enumerate(self._all_lines):
            slot_y = self._slot_0_y if (i % 2 == 0) else self._slot_1_y
            line.move_to([0.0, slot_y, 0.0])

        # 初始时只显示前 2 行（L0 → slot_0, L1 → slot_1）
        # 后续行虽然也在 scene 中，但 opacity=0（不可见）
        # 注意：必须把所有行都 add 到 scene，这样 UpdateFromAlphaFunc 才能工作
        self._scene.add(*self._all_lines)
        # 前 visible_lines 之外的全部设为 opacity=0
        for i, line in enumerate(self._all_lines):
            if i >= 2:
                line.set_opacity(0)

        # 预计算滚动事件
        line_char_counts = [len(l.text) for l in self._all_lines]
        scroll_count = len(lines) - 2
        events = []
        cumulative = 0.0
        for i in range(scroll_count):
            # 滚动 i 在读完 L0 到 L_i 后触发
            # 每次累加当前行 L_i 的字符数
            cumulative += line_char_counts[i]
            events.append(ScrollEvent(
                trigger_time=cumulative / self._speech_speed,
                duration=self._scroll_duration,
                in_line_idx=i + 2,  # 新行索引 = L_{i+2}
            ))
        self._scroll_events = events

    def _build_succession(self):
        """构建 Succession：初始保持 + 滚动动画"""
        from manim import Succession, AnimationGroup, Wait, FadeIn, UpdateFromAlphaFunc

        animations = []
        events = self._scroll_events
        scroll_dur = self._scroll_duration

        # 跟踪当前可见行
        visible_lines = [
            (self._all_lines[0], self._slot_0_y),
            (self._all_lines[1], self._slot_1_y),
        ]

        # 初始：前两行已通过 _prepare 设置 opacity=1，这里只是确保它们正确显示
        # 用 AnimationGroup 把初始 FadeIn（瞬间完成）和 Wait 并发
        if events:
            first_t = events[0].trigger_time
            init_group = AnimationGroup(
                FadeIn(self._all_lines[0], run_time=0.01),
                FadeIn(self._all_lines[1], run_time=0.01),
                Wait(run_time=first_t) if first_t > 0.01 else Wait(run_time=0.01),
            )
            animations.append(init_group)

        for ev in events:
            old_top, old_top_y = visible_lines[0]
            old_bot, old_bot_y = visible_lines[1]
            new_line = self._all_lines[ev.in_line_idx]

            # 新行从 slot_1 下方淡入，避免与旧行抢位
            new_line.move_to([0.0, self._slot_1_y, 0.0])
            new_line.set_opacity(0)

            # 1) 旧 slot_0：淡出并下移出可视区，避免与后序上移行叠影
            hide_y = self._slot_1_y - self._row_pitch
            fade_out_anim = UpdateFromAlphaFunc(
                old_top,
                lambda m, alpha, _sy=old_top_y, _hy=hide_y: (
                    m.set_y(_sy + (_hy - _sy) * alpha).set_opacity(1 - alpha)
                ),
                run_time=scroll_dur,
            )

            # 2) 旧 slot_1：上移到 slot_0
            move_up_anim = UpdateFromAlphaFunc(
                old_bot,
                lambda m, alpha, _sy=old_bot_y, _ty=self._slot_0_y: (
                    m.set_y(_sy + (_ty - _sy) * alpha).set_opacity(1)
                ),
                run_time=scroll_dur,
            )

            # 3) 新行：从 slot_1_y - delta 淡入并微微上移到 slot_1_y
            delta = self._row_pitch * 0.5
            new_start_y = self._slot_1_y - delta
            new_end_y = self._slot_1_y
            fade_in_anim = UpdateFromAlphaFunc(
                new_line,
                lambda m, alpha, _sy=new_start_y, _ey=new_end_y: (
                    m.move_to([0.0, _sy + (_ey - _sy) * alpha, 0.0]).set_opacity(alpha)
                ),
                run_time=scroll_dur,
            )

            # 并发组：3 件事同时进行
            group = AnimationGroup(
                fade_out_anim,
                move_up_anim,
                fade_in_anim,
            )
            animations.append(group)

            # 更新可见行
            visible_lines = [(old_bot, self._slot_0_y), (new_line, self._slot_1_y)]

            # 滚动之间等待
            idx = events.index(ev)
            if idx + 1 < len(events):
                next_t = events[idx + 1].trigger_time
                wait_t = next_t - ev.trigger_time - scroll_dur
                if wait_t > 0.05:
                    animations.append(Wait(run_time=wait_t))

        # 最后字幕结束后停留
        last_ev = events[-1]
        end_t = last_ev.trigger_time + scroll_dur
        if self._total_duration > end_t:
            animations.append(Wait(run_time=self._total_duration - end_t))

        return Succession(*animations)
