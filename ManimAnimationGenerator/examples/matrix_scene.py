#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# 矩阵课程动画示例
# 演示从 courses/ 目录读取 JSON 并生成动画
# 符合最新的 layout.md 和 json_schema.md 规范
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from manim import *
from manim_voiceover.services.edge import EdgeTTSService
from scripts.layout.scene_base import LayoutScene
from scripts.tex_tools import parse_mixed_content, math_symbols_to_speech
from scripts.subtitle_splitter import split_utterance
from scripts.layout.constants import ZoneConstants

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
JSON_PATH = os.path.join(PROJECT_ROOT, "courses", "matrix_course_example.json")


class MatrixScene(LayoutScene):
    """矩阵课程动画场景"""

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural"))

        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 纯标题过渡页（符合 layout.md 第 3.8 节）
        title = self.arrange_title_only(data["topic"])
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)
        self.play(FadeOut(title), run_time=0.8)

        # 播放原子
        for atom in data["atoms"]:
            self._play_atom(atom)

    def _play_atom(self, atom: dict):
        content_list = atom.get("content", [])
        layout = atom.get("layout", "vertical")
        speech = atom.get("speech", "")

        # 使用 parse_mixed_content 将 content 转为 Mobject 列表
        mobjs = parse_mixed_content(content_list, font_size=34)

        if not mobjs:
            return

        # 根据原子的 layout 字段选择布局
        if layout == "centered":
            # 单独居中模式
            group = VGroup(*mobjs).arrange(DOWN, buff=ZoneConstants.ROW_BUFF, center=True)
            group.move_to(ORIGIN)
        elif layout == "two_column":
            # 两栏布局：将前一半放左栏，后一半放右栏
            mid = len(mobjs) // 2
            left_objs = mobjs[:mid]
            right_objs = mobjs[mid:]
            # 使用基类的两栏方法（会自动处理顶部对齐、水平居中）
            group = self.place_two_column(VGroup(*left_objs), VGroup(*right_objs))
        elif layout == "three_column":
            # 三栏布局：均分三组
            third = max(1, len(mobjs) // 3)
            left_objs = mobjs[:third]
            mid_objs = mobjs[third:third*2]
            right_objs = mobjs[third*2:]
            group = self.place_three_column(
                VGroup(*left_objs),
                VGroup(*mid_objs),
                VGroup(*right_objs)
            )
        else:  # vertical 默认
            group = self.place_in_main_zone(VGroup(*mobjs), layout_mode="vertical")

        # 安全区域检查（已由 place_in_main_zone 等内部调用，但再调用一次也无妨）
        self.safe_place(group)

        # 内容淡入
        self.play(FadeIn(group), run_time=0.5)

        # 语音播放
        if speech:
            full_text = math_symbols_to_speech(speech)
            # 将长语音拆分为短句（每句不超过 30 字，符合字幕区容量）
            utterances = split_utterance(full_text, max_chars=30)
            for utt in utterances:
                if utt.strip():
                    with self.voiceover(text=utt) as tracker:
                        self.wait(tracker.duration)

        # 原子结束淡出（summary 类型的原子可保留稍长）
        if atom.get("type") != "summary":
            self.play(FadeOut(group), run_time=0.5)


if __name__ == "__main__":
    scene = MatrixScene()
    scene.render()