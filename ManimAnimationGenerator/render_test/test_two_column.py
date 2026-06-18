#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两栏布局渲染测试：左 20 字中文文本 + 右物理受力分析图 + 滚动字幕。
主内容、字幕并发动画。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import Text, MathTex, VGroup, Line, Angle, FadeIn, FadeOut, config, WHITE, RIGHT, UP, DOWN
from scripts.layout.scene_base import LayoutScene
from scripts.layout.constants import ZoneConstants
from scripts.animation.subtitle_scroller import SubtitleScroller
from scripts.animation.typewriter import Typewriter
from scripts.physics_graphics import (
    create_inclined_plane,
    create_car,
    create_force_arrow,
    CIRCUIT_COLORS,
)


class TwoColumnTestScene(LayoutScene):
    """两栏布局测试场景：左文本 + 右受力分析图 + 并发字幕。"""

    layout_mode = "two_column"

    def construct(self):
        self.draw_zone_boundaries(layout_mode="two_column")

        # ============================================================
        # 左栏文本：题目/原理说明
        # ============================================================
        left_text = Text(
            "牛顿第二定律：加速度与合力成正比，与质量成反比",
            font_size=ZoneConstants.FONT_SIZE_MAIN_TWO_COL_LEFT,
        )

        # ============================================================
        # 步骤 1: 创建几何体（小车 + 斜面）并获取缩放后的位置
        # ============================================================
        slope_base_center = np.array([0, -0.5, 0])
        slope_length = 2.5
        slope_angle_deg = 30.0
        slope_angle_rad = np.radians(slope_angle_deg)
        slope_dx = slope_length * np.cos(slope_angle_rad)
        slope_dy = slope_length * np.sin(slope_angle_rad)

        slope = create_inclined_plane(
            base_center=slope_base_center.tolist(),
            length=slope_length,
            angle_deg=slope_angle_deg,
            label="",
            font_size=20,
        )

        car_pos_on_slope = slope_base_center + np.array([slope_dx / 3, slope_dy / 3, 0])
        car = create_car(
            bottom_center=car_pos_on_slope.tolist(),
            width=1.0,
            height=0.4,
            wheel_radius=0.12,
            label=r"m",
        )
        car.rotate(slope_angle_rad, about_point=car_pos_on_slope)

        angle_line1 = Line(
            slope_base_center,
            slope_base_center + np.array([slope_dx, 0, 0]),
            color=WHITE,
            stroke_width=1.5,
        )
        angle_line2 = Line(
            slope_base_center,
            slope_base_center + np.array([slope_dx, slope_dy, 0]),
            color=WHITE,
            stroke_width=1.5,
        )
        angle_arc = Angle(angle_line1, angle_line2, radius=0.4, color=WHITE)
        theta_label = MathTex(r"\theta", font_size=24, color=WHITE).move_to(
            slope_base_center + np.array([-0.4, -0.25, 0])
        )

        geometry_group = VGroup(slope, car, angle_arc, theta_label)

        # ============================================================
        # 步骤 2: 创建受力箭头（箭头长度已在 create_force_arrow 中设定）
        # 规则：所有力从重心(car_center)出发，方向符合物理规范
        # ============================================================
        car_center = car.named_parts["body"].get_center()

        gravity_color = CIRCUIT_COLORS["force_G"]
        normal_color = CIRCUIT_COLORS["force_N"]
        friction_color = CIRCUIT_COLORS["force_f"]

        # 重力：竖直向下，作用于重心
        # magnitude=1.0：箭头长度 = max(1.0*0.5, 3.0) = 3.0 单位
        gravity = create_force_arrow(
            car_center, [0, -1, 0],
            magnitude=1.0, label=r"\vec{G}", color=gravity_color,
        )
        # 支持力：垂直于斜面向上，作用于重心（方向沿法向）
        # magnitude=1.0：箭头长度 = max(1.0*0.5, 3.0) = 3.0 单位
        slope_normal = np.array([-np.sin(slope_angle_rad), np.cos(slope_angle_rad), 0])
        normal = create_force_arrow(
            car_center, slope_normal.tolist(),
            magnitude=1.0, label=r"\vec{F}_N", color=normal_color,
        )
        # 摩擦力：沿斜面向上（平衡重力沿斜面分力），作用于重心
        # magnitude=1.0：箭头长度 = max(1.0*0.5, 3.0) = 3.0 单位
        slope_up = np.array([np.cos(slope_angle_rad), np.sin(slope_angle_rad), 0])
        friction = create_force_arrow(
            car_center, slope_up.tolist(),  # 向上平衡 G·sinθ
            magnitude=1.0, label=r"\vec{f}", color=friction_color,
        )

        right_graphics = VGroup(geometry_group, gravity, normal, friction)

        # ============================================================
        # 步骤 4: 放置到两栏布局（左文本 + 右图形）
        # add_to_scene=False：让调用者自行控制添加时机，避免阻塞其他动画
        # ============================================================
        result = self.place_two_column(left_text, right_graphics, add_to_scene=False)

        # ============================================================
        # 步骤 5: 准备字幕（_prepare 自动把前两行 add 到 scene）
        # ============================================================
        subtitle_text = (
            "牛顿第二定律是经典力学的基础定律。"
            "加速度与合力成正比，与质量成反比。"
            "在斜面问题中，我们沿斜面方向分解重力。"
        )

        subtitle_zone = self.get_subtitle_zone(layout_mode="two_column")
        scroller = SubtitleScroller(self, subtitle_zone, font_size=18, chars_per_line=20)

        # ============================================================
        # 步骤 6: 精确时序控制
        # ============================================================
        subtitle_anim = scroller.build_subtitle_animation(subtitle_text)
        subtitle_run_time = scroller.total_duration
        content_run_time = 2.0  # 主内容打字机时长

        print(f"[DEBUG] 字幕字符数: {sum(len(l.text) for l in scroller._all_lines)}")
        print(f"[DEBUG] 字幕总时长: {subtitle_run_time:.2f}s")
        print(f"[DEBUG] 预期总时长: {subtitle_run_time + 1.5 + 1.0:.2f}s")

        # 并发播放：self.play() 会等待最长动画完成
        # 注意：place_two_column(add_to_scene=False) 返回的 result 已经包含了
        # 缩放+放置好的左右栏内容，无需再手动 add(right_graphics)
        self.play(
            Typewriter(left_text, run_time=content_run_time),
            subtitle_anim,
        )

        # 物理图形 FadeIn（字幕完成后）
        # 从 result 中提取右栏图形（result = VGroup(left_group, right_group)）
        right_group_in_result = result[1]  # 第二个是 right_group
        self.play(
            FadeIn(right_group_in_result, shift=UP * 0.2, run_time=1.5),
            run_time=1.5,
        )

        self.wait(1.0)


if __name__ == "__main__":
    config.quality = "medium_quality"
    config.format = "mp4"

    if "--disable_caching" not in sys.argv:
        sys.argv.append("--disable_caching")

    scene = TwoColumnTestScene(skip_env_check=True, debug=True)
    scene.render()
