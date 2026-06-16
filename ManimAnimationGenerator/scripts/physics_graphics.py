#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物理图形工厂函数模块 - 遵循 IEC 60617 / GB/T 4728 / GB/T 4460 / 人教版标准

提供电路元件、基础图元、组装工具、动画函数等完整物理图形绘制能力。
所有图元遵循对应的国际/国家标准（IEC 60617 / GB/T 4728 / GB/T 4460）和人教版教材规范。

标准优先级：IEC 60617 / GB/T 4728 > GB/T 4460 > 人教版教材 > ANSI

---
图元实现文件索引：
  - 电路元件：create_battery, create_resistor, create_bulb, create_switch,
              create_ammeter, create_voltmeter, create_capacitor, create_rheostat
  - 基础图元：create_wire, create_junction_dot, create_arc_bridge, create_force_arrow
  - 组装工具：build_series_circuit, build_parallel_branch
  - 动画函数：create_current_dots, animate_current_flow, set_switch_state, set_bulb_state

> ⚠️ 重要：真实有效的图元绘制必须使用本文件中的工厂函数。
> physics.md 文档中的示例代码仅作为规范说明，实际调用请使用本文件的函数。
"""

import numpy as np
from manim import (
    VGroup,
    Line,
    Circle,
    Rectangle,
    DoubleArrow,
    DashedLine,
    Vector,
    Square,
    Angle,
    RightAngle,
    Elbow,
    Polygon,
    Dot,
    ArrowTip,
    Arrow,
    Arc,
    MathTex,
    Text,
    MarkupText,
    WHITE,
    YELLOW_C,
    ORANGE,
    PI,
    RIGHT,
    UP,
    DOWN,
    LEFT,
    ORIGIN,
    AnimationGroup,
    Transform,
)
from typing import List, Optional

try:
    from manim import MoveAlongPath
except ImportError:
    MoveAlongPath = None  # 旧版 Manim 可能无此动画类


# ════════════════════════════════════════════════════════════
# 电路元件尺寸常量（对应 physics.md Section 15.3 量化值）
# 标准依据：IEC 60617 / GB/T 4728 / 人教版教材
# ════════════════════════════════════════════════════════════

BATTERY_LONG_HALF = 0.35  # 正极长线半长（IEC 60617-02 比例约定）
BATTERY_SHORT_HALF = 0.2  # 负极短线半长
BATTERY_GAP = 0.15  # 极板间距
RESISTOR_WIDTH = 1.0  # 电阻矩形宽度（IEC 60617-04 S00139）
RESISTOR_HEIGHT = 0.4  # 电阻矩形高度
BULB_RADIUS = 0.3  # 灯泡圆半径（人教版教材）
WIRE_LENGTH = 0.3  # 元件自动引出导线长度（IEC 连接规范最小值）
SWITCH_CONTACT_GAP = 0.4  # 开关触点间距（GB/T 4728.02）
SWITCH_DOT_RADIUS = 0.04  # 开关触点圆半径
METER_RADIUS = 0.25  # 电表圆半径（人教版教材）
CAPACITOR_PLATE_LENGTH = 0.6  # 电容极板长度（IEC 60617-04 S00145）
CAPACITOR_PLATE_GAP = 0.5  # 电容极板间距
RHEOSTAT_WIDTH = 1.2  # 滑动变阻器矩形宽度（人教版教材）
RHEOSTAT_HEIGHT = 0.4  # 滑动变阻器矩形高度


# ════════════════════════════════════════════════════════════
# 方向计算辅助函数
# ════════════════════════════════════════════════════════════


def _unit_direction(start, end):
    """计算从 start 到 end 的单位方向向量（3D）

    Args:
        start: 起点，可为 list 或 numpy array [x, y, z]
        end: 终点，同格式

    Returns:
        numpy array，单位方向向量 [dx, dy, 0]
    """
    d = np.array(end, dtype=float) - np.array(start, dtype=float)
    length = np.linalg.norm(d)
    if length < 1e-6:
        return np.array(RIGHT)
    return d / length


def _perpendicular(vec):
    """计算二维方向向量的垂直向量（逆时针 90° 旋转）

    Args:
        vec: 方向向量 [dx, dy, dz]

    Returns:
        numpy array [-dy, dx, 0.0]，与 vec 垂直且在 XY 平面内
    """
    return np.array([-vec[1], vec[0], 0.0])


# ════════════════════════════════════════════════════════════
# 颜色常量（对应 physics.md Section 13 + Section 15.2.1）
# ════════════════════════════════════════════════════════════

CIRCUIT_COLORS = {
    "wire": "#FFFFFF",  # 导线（白）
    "component": "#374151",  # 元件描边（深灰蓝，html-parser COLORS.shape.primary）
    "highlight": "#D97706",  # 高亮强调（琥珀）
    "current_red": "#FF6666",  # 电流方向（红，传统正电荷方向）
    "path_green": "#66FFAA",  # 通路高亮（绿）
    "short_yellow": "#FFDD66",  # 短路警示（黄）
    "break_red": "#FF4444",  # 断路标记（红）
    # 修复 P0-C：力矢量颜色严格遵循 references/physics.md 15.2.1 力-色固定映射表
    # 力学域内最小色相差 51°，确保多力共存时高辨识度
    "force_G": "#EF4444",  # 重力 G（红，H:0°）
    "force_N": "#3B82F6",  # 支持力 N（蓝，H:217°）
    "force_f": "#EAB308",  # 摩擦力 f（黄，H:51°）
    "force_F": "#22C55E",  # 外力/推力 F（绿，H:142°
    "force_T": "#A855F7",  # 拉力/张力 T（紫，H:272°）
    "force_buoyancy": "#06B6D4",  # 浮力（青，H:188°）
    "force_combined": "#9CA3AF",  # 合力（中灰，无彩 S:7%）
}


# ════════════════════════════════════════════════════════════
# 电路元件工厂函数（遵循 IEC 60617 / GB/T 4728 / 人教版标准）
# ════════════════════════════════════════════════════════════


def create_battery(start, end, label="", voltage=""):
    """创建电池元件（IEC 60617-02 S00001 / GB/T 4728.02）

    功能：创建标准电池符号，长线为正极(+)，短线为负极(-)，比例约 2:1。
         start 端为负极侧，end 端为正极侧。包含两段引出导线。

    参数：
        start: 负极终端位置 [x, y, 0]
        end: 正极终端位置 [x, y, 0]
        label: 元件标签 MathTex（如 "E_1"），默认空
        voltage: 电压标注 MathTex（如 "\\mathcal{E}=9\\text{V}"），默认空

    返回：VGroup，named_parts 含 wire_left/short_line/long_line/wire_right；
         connection_points 含 start/end 端子坐标；component_type="battery"

    标准依据：IEC 60617-02 S00001 / GB/T 4728.02
    """
    start, end = np.array(start, dtype=float), np.array(end, dtype=float)
    unit_dir = _unit_direction(start, end)
    perp = _perpendicular(unit_dir)
    center = (start + end) / 2

    neg_pos = center - unit_dir * (BATTERY_GAP / 2)
    pos_pos = center + unit_dir * (BATTERY_GAP / 2)

    long_line = Line(
        pos_pos - perp * BATTERY_LONG_HALF,
        pos_pos + perp * BATTERY_LONG_HALF,
        stroke_width=2,
        color=WHITE,
    )
    short_line = Line(
        neg_pos - perp * BATTERY_SHORT_HALF,
        neg_pos + perp * BATTERY_SHORT_HALF,
        stroke_width=2,
        color=WHITE,
    )
    wire_left = Line(start, neg_pos, stroke_width=2, color=WHITE)
    wire_right = Line(pos_pos, end, stroke_width=2, color=WHITE)

    group = VGroup(wire_left, short_line, long_line, wire_right)

    # 极性标记（IEC 60617 强制要求：正负极标识不得缺失）
    # 使用显式坐标定位标签，基于元件几何中心+垂直方向偏移（遵循 F1：禁用 .next_to()）
    plus_sign = MathTex("+", font_size=20)
    plus_sign.move_to(long_line.get_center() + perp * (BATTERY_LONG_HALF + 0.08))
    minus_sign = MathTex("-", font_size=20)
    minus_sign.move_to(short_line.get_center() + perp * (BATTERY_SHORT_HALF + 0.08))
    group.add(plus_sign, minus_sign)

    if voltage:
        v_lbl = MathTex(voltage, font_size=28)
        v_lbl.move_to(group.get_center() + perp * (0.5 + 0.15))
        group.add(v_lbl)
    if label:
        l_obj = MathTex(label, font_size=28)
        l_obj.move_to(group.get_center() + (-perp) * (0.5 + 0.15))
        group.add(l_obj)

    group.connection_points = {"start": start.copy(), "end": end.copy()}
    group.named_parts = {
        "wire_left": wire_left,
        "short_line": short_line,
        "long_line": long_line,
        "wire_right": wire_right,
    }
    group.component_type = "battery"
    return group


def create_resistor(start, end, label="", resistance=""):
    """创建电阻元件（IEC 60617-04 S00139 / GB/T 4728.04 欧式矩形）

    功能：创建欧式矩形电阻符号（非 ANSI 锯齿形），矩形居中于 start/end 之间，
         导线拆分为两段分别接矩形左右端点（遵循 IEC 绘制原则：禁止单线穿过元件）。

    参数：
        start: 左终端位置 [x, y, 0]
        end: 右终端位置 [x, y, 0]
        label: 元件标签 MathTex（如 "R_1"），默认空
        resistance: 电阻值标注 MathTex（如 "R=100\\Omega"），默认空

    返回：VGroup，named_parts 含 body/wire_left/wire_right；
         connection_points 含 start/end 端子坐标；component_type="resistor"

    标准依据：IEC 60617-04 S00139 / GB/T 4728.04（欧式矩形，禁止美式锯齿）
    """
    start, end = np.array(start, dtype=float), np.array(end, dtype=float)
    unit_dir = _unit_direction(start, end)
    perp = _perpendicular(unit_dir)
    center = (start + end) / 2

    angle = np.arctan2(unit_dir[1], unit_dir[0])

    body = Rectangle(
        width=RESISTOR_WIDTH,
        height=RESISTOR_HEIGHT,
        color=WHITE,
        stroke_width=2,
    )
    body.move_to(center)
    body.rotate(angle)

    left_edge = center - unit_dir * (RESISTOR_WIDTH / 2)
    right_edge = center + unit_dir * (RESISTOR_WIDTH / 2)

    wire_left = Line(start, left_edge, stroke_width=2, color=WHITE)
    wire_right = Line(right_edge, end, stroke_width=2, color=WHITE)

    group = VGroup(wire_left, body, wire_right)

    if label:
        l_obj = MathTex(label, font_size=28)
        l_obj.move_to(body.get_center() + perp * (RESISTOR_HEIGHT / 2 + 0.1 + 0.12))
        group.add(l_obj)
    if resistance:
        r_lbl = MathTex(resistance, font_size=24)
        r_lbl.move_to(body.get_center() + (-perp) * (RESISTOR_HEIGHT / 2 + 0.1 + 0.1))
        group.add(r_lbl)

    group.connection_points = {"start": start.copy(), "end": end.copy()}
    group.named_parts = {"body": body, "wire_left": wire_left, "wire_right": wire_right}
    group.component_type = "resistor"
    return group


def create_bulb(center=None, radius=BULB_RADIUS, label="", lit=False):
    """创建灯泡元件（人教版初中物理通用符号）

    功能：创建圆形外框 + 内部叉号 (×) 的灯泡符号。
         两端各自带 0.3 单位长度的引出导线（遵循 IEC 60617 连接规范）。
         lit=False 时 YELLOW_C 空心；lit=True 时 ORANGE 半透明填充。

    参数：
        center: 灯泡中心位置 [x, y, 0]，默认 ORIGIN
        radius: 圆半径，默认 0.3
        label: 标签 MathTex，默认空
        lit: 是否点亮状态，默认 False

    返回：VGroup，named_parts 含 outer/cross_l1/cross_l2/wire_left/wire_right；
         connection_points 含 start/end（导线两端接点）；component_type="bulb"

    标准依据：人教版初中物理教材灯泡符号
    """
    center = np.array(center, dtype=float) if center is not None else np.array(ORIGIN)

    stroke_color = YELLOW_C
    outer = Circle(radius=radius, color=stroke_color, stroke_width=2)
    outer.move_to(center)

    if lit:
        outer.set_fill(ORANGE, opacity=0.6)

    cs = radius * 0.55
    cross_l1 = Line(
        center + np.array([-cs, -cs, 0]),
        center + np.array([cs, cs, 0]),
        stroke_color=stroke_color,
        stroke_width=1.5,
    )
    cross_l2 = Line(
        center + np.array([-cs, cs, 0]),
        center + np.array([cs, -cs, 0]),
        stroke_color=stroke_color,
        stroke_width=1.5,
    )

    # 添加自动引出导线（各 0.3 单位，符合 IEC 连接规范）
    wire_left = Line(
        center + np.array([-radius - WIRE_LENGTH / 2, 0, 0]),
        center + np.array([-radius, 0, 0]),
        stroke_color=stroke_color,
        stroke_width=2,
    )
    wire_right = Line(
        center + np.array([radius, 0, 0]),
        center + np.array([radius + WIRE_LENGTH / 2, 0, 0]),
        stroke_color=stroke_color,
        stroke_width=2,
    )

    group = VGroup(wire_left, outer, cross_l1, cross_l2, wire_right)

    if label:
        l_obj = MathTex(label, font_size=28)
        l_obj.move_to(outer.get_center() + UP * (radius + 0.1 + 0.12))
        group.add(l_obj)

    # 导线两端为新的 connection_points
    start_pt = wire_left.get_start()
    end_pt = wire_right.get_end()
    group.connection_points = {"start": start_pt, "end": end_pt}
    group.named_parts = {
        "outer": outer,
        "cross_l1": cross_l1,
        "cross_l2": cross_l2,
        "wire_left": wire_left,
        "wire_right": wire_right,
    }
    group.component_type = "bulb"
    return group


def create_switch(start, end, closed=False, label=""):
    """创建开关元件（GB/T 4728.02 S00061 / 人教版）

    功能：创建双触点 + 开关臂符号。closed=True 时臂为直线连接两触点；
         closed=False 时臂从第一触点向垂直方向偏 45° 抬起。

    参数：
        start: 第一触点侧终端位置 [x, y, 0]
        end: 第二触点侧终端位置 [x, y, 0]
        closed: 闭合状态，默认 False（断开）
        label: 标签 MathTex，默认空

    返回：VGroup，named_parts 含 dot1/dot2/arm；
         connection_points 含 start/end 端子坐标；component_type="switch"

    标准依据：GB/T 4728.02 S00061 / 人教版教材
    """
    start, end = np.array(start, dtype=float), np.array(end, dtype=float)
    unit_dir = _unit_direction(start, end)
    perp = _perpendicular(unit_dir)
    center = (start + end) / 2

    dot1_pos = center - unit_dir * (SWITCH_CONTACT_GAP / 2)
    dot2_pos = center + unit_dir * (SWITCH_CONTACT_GAP / 2)

    dot1 = Dot(point=dot1_pos, radius=SWITCH_DOT_RADIUS, color=WHITE)
    dot2 = Dot(point=dot2_pos, radius=SWITCH_DOT_RADIUS, color=WHITE)

    if closed:
        arm = Line(dot1_pos, dot2_pos, stroke_width=2, color=WHITE)
    else:
        arm_len = SWITCH_CONTACT_GAP * 0.75
        open_end = dot1_pos + unit_dir * arm_len * 0.7 + perp * arm_len * 0.7
        arm = Line(dot1_pos, open_end, stroke_width=2, color=WHITE)

    wire_left = Line(start, dot1_pos, stroke_width=2, color=WHITE)
    wire_right = Line(dot2_pos, end, stroke_width=2, color=WHITE)

    group = VGroup(wire_left, dot1, dot2, arm, wire_right)

    if label:
        l_obj = MathTex(label, font_size=28)
        l_obj.move_to(
            group.get_center() + perp * (SWITCH_CONTACT_GAP / 2 + 0.15 + 0.12)
        )
        group.add(l_obj)

    group.connection_points = {
        "start": start.copy(),
        "end": end.copy(),
        "dot1": dot1_pos.copy(),
        "dot2": dot2_pos.copy(),
    }
    group.named_parts = {
        "dot1": dot1,
        "dot2": dot2,
        "arm": arm,
        "wire_left": wire_left,
        "wire_right": wire_right,
    }
    group.component_type = "switch"
    group.closed = closed
    return group


def create_ammeter(center=None, radius=METER_RADIUS, label=""):
    """创建电流表元件（人教版教材）

    功能：创建圆圈内字母 A 的电流表符号，串联接入电路。

    参数：
        center: 中心位置 [x, y, 0]，默认 ORIGIN
        radius: 圆半径，默认 0.25
        label: 标签 MathTex，默认空

    返回：VGroup，named_parts 含 circle/marker；
         connection_points 含 left/right（串联接点）；component_type="ammeter"

    标准依据：人教版教材电流表符号（串联接入）
    """
    center = np.array(center, dtype=float) if center is not None else np.array(ORIGIN)

    circle = Circle(radius=radius, color=WHITE, stroke_width=2)
    circle.move_to(center)
    marker = Text("A", font_size=24, color=WHITE).move_to(center)

    group = VGroup(circle, marker)

    if label:
        l_obj = MathTex(label, font_size=28)
        l_obj.move_to(circle.get_center() + UP * (radius + 0.1 + 0.12))
        group.add(l_obj)

    left_pt = center + np.array([-radius, 0, 0])
    right_pt = center + np.array([radius, 0, 0])
    group.connection_points = {"left": left_pt, "right": right_pt}
    group.named_parts = {"circle": circle, "marker": marker}
    group.component_type = "ammeter"
    return group


def create_voltmeter(center=None, radius=METER_RADIUS, label=""):
    """创建电压表元件（人教版教材）

    功能：创建圆圈内字母 V 的电压表符号，并联接入被测元件。

    参数：
        center: 中心位置 [x, y, 0]，默认 ORIGIN
        radius: 圆半径，默认 0.25
        label: 标签 MathTex，默认空

    返回：VGroup，named_parts 含 circle/marker；
         connection_points 含 left/right（并联接点）；component_type="voltmeter"

    标准依据：人教版教材电压表符号（并联接入）
    """
    center = np.array(center, dtype=float) if center is not None else np.array(ORIGIN)

    circle = Circle(radius=radius, color=WHITE, stroke_width=2)
    circle.move_to(center)
    marker = Text("V", font_size=24, color=WHITE).move_to(center)

    group = VGroup(circle, marker)

    if label:
        l_obj = MathTex(label, font_size=28)
        l_obj.move_to(circle.get_center() + UP * (radius + 0.1 + 0.12))
        group.add(l_obj)

    left_pt = center + np.array([-radius, 0, 0])
    right_pt = center + np.array([radius, 0, 0])
    group.connection_points = {"left": left_pt, "right": right_pt}
    group.named_parts = {"circle": circle, "marker": marker}
    group.component_type = "voltmeter"
    return group


def create_capacitor(
    center=None,
    plate_length=CAPACITOR_PLATE_LENGTH,
    plate_gap=CAPACITOR_PLATE_GAP,
    label="",
):
    """创建电容元件（IEC 60617-04 S00145 / GB/T 4728.04）

    功能：创建两条平行等长线段（极板）符号，T 型 ⊥ 接入规范。
         极板水平放置，连接点在极板中心上下方向（用于垂直导线接入）。

    参数：
        center: 极板间隙中心位置 [x, y, 0]，默认 ORIGIN
        plate_length: 极板长度，默认 0.6
        plate_gap: 极板间距，默认 0.5
        label: 标签 MathTex（如 "C"），默认空

    返回：VGroup，named_parts 含 upper_plate/lower_plate；
         connection_points 含 top/bottom（极板中心，T型接入点）；
         component_type="capacitor"

    标准依据：IEC 60617-04 S00145 / GB/T 4728.04（T 型 ⊥ 接入）
    """
    center = np.array(center, dtype=float) if center is not None else np.array(ORIGIN)

    upper_y = center[1] + plate_gap / 2
    lower_y = center[1] - plate_gap / 2
    cx = center[0]

    upper_plate = Line(
        [cx - plate_length / 2, upper_y, 0],
        [cx + plate_length / 2, upper_y, 0],
        stroke_width=3,
        color=WHITE,
    )
    lower_plate = Line(
        [cx - plate_length / 2, lower_y, 0],
        [cx + plate_length / 2, lower_y, 0],
        stroke_width=3,
        color=WHITE,
    )

    group = VGroup(upper_plate, lower_plate)

    if label:
        l_obj = MathTex(label, font_size=28)
        # 标签置于极板组左侧（显式坐标，遵循 F1：禁用 .next_to()）
        label_pos = group.get_center() + LEFT * (
            CAPACITOR_PLATE_LENGTH / 2 + 0.15 + 0.12
        )
        l_obj.move_to(label_pos)
        group.add(l_obj)

    top_pt = np.array([cx, upper_y, 0])
    bottom_pt = np.array([cx, lower_y, 0])
    group.connection_points = {"top": top_pt, "bottom": bottom_pt}
    group.named_parts = {"upper_plate": upper_plate, "lower_plate": lower_plate}
    group.component_type = "capacitor"
    return group


def create_rheostat(start, end, label=""):
    """创建滑动变阻器元件（人教版教材）

    功能：创建矩形电阻本体 + 带箭头滑片 + "P" 标注的滑动变阻器符号。

    参数：
        start: 左终端位置 [x, y, 0]
        end: 右终端位置 [x, y, 0]
        label: 标签 MathTex，默认空

    返回：VGroup，named_parts 含 body/slider_line/slider_arrow/slider_label；
         connection_points 含 start/end 端子坐标；component_type="rheostat"

    标准依据：人教版教材滑动变阻器符号
    """
    start, end = np.array(start, dtype=float), np.array(end, dtype=float)
    unit_dir = _unit_direction(start, end)
    perp = _perpendicular(unit_dir)
    center = (start + end) / 2
    angle = np.arctan2(unit_dir[1], unit_dir[0])

    body = Rectangle(
        width=RHEOSTAT_WIDTH,
        height=RHEOSTAT_HEIGHT,
        color=WHITE,
        stroke_width=2,
    )
    body.move_to(center)
    body.rotate(angle)

    # 滑片线（沿本体上边缘，从左到右方向）
    slider_start = center - unit_dir * (RHEOSTAT_WIDTH * 0.4)
    slider_end = center + unit_dir * (RHEOSTAT_WIDTH * 0.3)
    slider_line = Line(
        slider_start,
        slider_end,
        stroke_color=YELLOW_C,
        stroke_width=2,
    )

    # 滑片箭头（指向滑片方向）
    slider_arrow = ArrowTip(angle=angle, color=YELLOW_C)
    slider_arrow.move_to(slider_end)
    slider_arrow.scale(0.3)

    # 滑片标签（显式坐标定位，遵循 F1：禁用 .next_to()）
    slider_label = MathTex("P", font_size=24)
    slider_label.move_to(slider_arrow.get_center() + perp * 0.2)

    left_edge = center - unit_dir * (RHEOSTAT_WIDTH / 2)
    right_edge = center + unit_dir * (RHEOSTAT_WIDTH / 2)
    wire_left = Line(start, left_edge, stroke_width=2, color=WHITE)
    wire_right = Line(right_edge, end, stroke_width=2, color=WHITE)

    group = VGroup(
        wire_left,
        body,
        slider_line,
        slider_arrow,
        slider_label,
        wire_right,
    )

    if label:
        l_obj = MathTex(label, font_size=28)
        l_obj.move_to(body.get_center() + (-perp) * (RHEOSTAT_HEIGHT / 2 + 0.1 + 0.12))
        group.add(l_obj)

    group.connection_points = {"start": start.copy(), "end": end.copy()}
    group.named_parts = {
        "body": body,
        "slider_line": slider_line,
        "slider_arrow": slider_arrow,
        "slider_label": slider_label,
        "wire_left": wire_left,
        "wire_right": wire_right,
    }
    group.component_type = "rheostat"
    return group


# ════════════════════════════════════════════════════════════
# 基础图元工厂函数
# ════════════════════════════════════════════════════════════


def create_wire(start, end, color=WHITE, stroke_width=2):
    """创建导线段（IEC 60617 / GB/T 4728 / 人教版）

    功能：创建横平竖直的导线段（水平或垂直），禁止斜线。
         自动校验方向，若起终点同时在 X 和 Y 方向有差异则报错。

    参数：
        start: 起点 [x, y, 0]
        end: 终点 [x, y, 0]
        color: 导线颜色，默认 WHITE
        stroke_width: 导线线宽，默认 2

    返回：Line 对象（非 VGroup），附带 connection_points 属性

    标准依据：IEC 60617 / GB/T 4728（导线横平竖直，禁止斜线转弯）
    """
    start, end = np.array(start, dtype=float), np.array(end, dtype=float)

    dx = abs(end[0] - start[0])
    dy = abs(end[1] - start[1])
    tolerance = 1e-4

    if dx > tolerance and dy > tolerance:
        raise ValueError(
            f"导线必须横平竖直：start={start[:2]} → end={end[:2]} "
            f"同时存在 X 偏移({dx:.4f})和 Y 偏移({dy:.4f})"
        )

    wire = Line(start, end, stroke_width=stroke_width, color=color)
    wire.connection_points = {"start": start.copy(), "end": end.copy()}
    wire.component_type = "wire"
    return wire


def create_junction_dot(point, radius=0.05):
    """创建节点圆点（GB/T 4728 连接节点标记）

    功能：在导线交叉且连通处创建实心圆点，标识电气连接节点。

    参数：
        point: 节点位置 [x, y, 0]
        radius: 圆点半径，默认 0.05（GB/T 4728 标准）

    返回：Dot 对象，附带 connection_points 属性

    标准依据：GB/T 4728（三线交点处必须标注实心圆点）
    """
    point = np.array(point, dtype=float)
    dot = Dot(point=point, radius=radius, color=WHITE)
    dot.connection_points = {"center": point.copy()}
    dot.component_type = "junction_dot"
    return dot


def create_arc_bridge(cross_point, radius=0.08):
    """创建跨线弧（GB/T 4728 导线交叉不连通标记）

    功能：在导线交叉但不连通处创建小半圆弧，标识无电气连接。
         弧线默认水平跨越（上方导线跨过下方导线）。

    参数：
        cross_point: 交叉点位置 [x, y, 0]
        radius: 半圆弧半径，默认 0.08

    返回：Arc 对象（半圆弧），附带 connection_points 属性

    标准依据：GB/T 4728（导线交叉不连通处画跨线弧，区分于节点圆点）
    """
    cross_point = np.array(cross_point, dtype=float)

    # 半圆弧：从左到右跨过交叉点，中心在交叉点上方
    arc = Arc(
        radius=radius,
        start_angle=0,
        angle=PI,
        color=WHITE,
        stroke_width=2,
    )
    arc.move_to(cross_point + np.array([0, radius, 0]))

    arc.connection_points = {"center": cross_point.copy()}
    arc.component_type = "arc_bridge"
    return arc


def create_inclined_plane(
    base_center: List[float] = None,
    length: float = 3.0,
    angle_deg: float = 30.0,
    label: str = "",
    font_size: int = 24,
) -> VGroup:
    """创建斜面（人教版高中物理力学）

    功能：创建直角三角形斜面，底边水平，斜边倾角可指定。

    参数：
        base_center: 斜面底部中心位置 [x, y, 0]
        length: 斜面斜边长度，默认 3.0
        angle_deg: 倾斜角度（度），默认 30.0
        label: 标签 MathTex（如 "m" 或 "θ=30°"），默认空
        font_size: 标签字号，默认 24

    返回：VGroup，包含斜面三角形；
         无 connection_points（非电路元件）；component_type="inclined_plane"

    标准依据：人教版高中物理必修一斜面模型
    """
    if base_center is None:
        base_center = ORIGIN
    bc = np.array(base_center, dtype=float)

    angle_rad = np.radians(angle_deg)
    dx = length * np.cos(angle_rad)
    dy = length * np.sin(angle_rad)

    # 斜面三角形：底边 + 垂直边 + 斜边
    triangle = Polygon(
        bc,
        bc + np.array([dx, 0, 0]),
        bc + np.array([dx, dy, 0]),
        fill_color="#555555",
        fill_opacity=0.6,
        stroke_color="#888888",
        stroke_width=2,
    )

    group = VGroup(triangle)

    if label:
        label_pos = bc + np.array([dx / 2, -0.3, 0])
        label_obj = MathTex(label, font_size=font_size, color="#888888")
        label_obj.move_to(label_pos)
        group.add(label_obj)

    group.component_type = "inclined_plane"
    return group


def create_force_arrow(origin, direction_vector, magnitude=1.0, label="", color=None):
    """创建力矢量箭头（GB/T 4460-2013 / 人教版）

    功能：创建从作用点出发的实心三角箭头力矢量，长度与大小成正比。
         颜色遵循力-色固定映射表，标签置于箭头末端外侧。

    参数：
        origin: 作用点（质心或接触点）[x, y, 0]
        direction_vector: 力方向向量 [dx, dy, 0]（无需归一化）
        magnitude: 力的大小（影响箭头长度），默认 1.0
        label: LaTeX 标签（如 "\\vec{F}_N"），默认空
        color: 箭头颜色，默认 None（自动根据 label 映射力-色表）

    返回：VGroup，named_parts 含 arrow/label_text；
         connection_points 含 origin/tip；component_type="force_arrow"

    坐标快照行为：
        connection_points 中的 origin/tip 在函数调用时记录为静态快照。
        若传入的 origin 来自已变换过的图元（如旋转后的小车），
        必须确保该坐标本身是变换后的实时值（通过 .get_center()、
        .get_bottom()、named_parts["xxx"].get_xxx() 动态获取），
        而非该图元的 connection_points 快照。

    标准依据：GB/T 4460-2013 第 7 章（实心三角箭头，从作用点出发）
    """
    origin = np.array(origin, dtype=float)
    d_vec = np.array(direction_vector, dtype=float)
    d_len = np.linalg.norm(d_vec)

    if d_len < 1e-6:
        raise ValueError("力方向向量不能为零向量")

    unit_d = d_vec / d_len
    # 长度与力大小成正比，比例尺 0.5 单位/牛顿（可按场景调整）
    scale = 0.5
    end_point = origin + unit_d * magnitude * scale

    # 颜色自动映射
    if color is None:
        color = _map_force_color(label)

    arrow = Arrow(
        start=origin,
        end=end_point,
        buff=0.15,
        stroke_width=3,
        color=color,
        max_tip_length_to_length_ratio=0.2,
    )

    group = VGroup(arrow)

    if label:
        lbl = MathTex(label, font_size=28)
        # 标签置于箭头末端外侧（沿方向延伸，略微偏移垂直方向）
        perp = np.array([-unit_d[1], unit_d[0], 0])
        tip_pos = end_point + unit_d * 0.3
        lbl.move_to(tip_pos + perp * 0.2)
        group.add(lbl)

    group.connection_points = {
        "origin": origin.copy(),
        "tip": end_point.copy(),
    }
    group.named_parts = {"arrow": arrow}
    if label:
        group.named_parts["label_text"] = group[1]
    group.component_type = "force_arrow"
    return group


def _map_force_color(label):
    """根据力标签自动映射颜色（对应 physics.md Section 15.2.1 力-色映射表）

    Args:
        label: LaTeX 标签字符串，含力名称关键字

    Returns:
        Manim 颜色值字符串
    """
    if not label:
        return CIRCUIT_COLORS["force_F"]

    mappings = {
        "G": CIRCUIT_COLORS["force_G"],  # 重力
        "N": CIRCUIT_COLORS["force_N"],  # 支持力
        "f": CIRCUIT_COLORS["force_f"],  # 摩擦力
        "F": CIRCUIT_COLORS["force_F"],  # 外力/推力
        "T": CIRCUIT_COLORS["force_T"],  # 拉力
        "浮": CIRCUIT_COLORS["force_buoyancy"],  # 浮力
        "合": CIRCUIT_COLORS["force_combined"],  # 合力
    }
    for key, color in mappings.items():
        if key in label:
            return color
    return CIRCUIT_COLORS["force_F"]


# ════════════════════════════════════════════════════════════
# 力学与流体类图元（人教版教材 / GB/T 4460）
# ════════════════════════════════════════════════════════════


def create_car(
    bottom_center=None, width=1.4, height=0.6, wheel_radius=0.2, label="", color=None
):
    """创建小车图元（人教版初中物理 / 高中力学）

    功能：创建矩形车身 + 两个圆形车轮的小车符号。
         用于牛顿运动定律（加速度、摩擦力）、动能定理等教学场景。

    参数：
        bottom_center: 车底中心位置 [x, y, 0]，默认 ORIGIN
        width: 车身宽度，默认 1.4
        height: 车身高度，默认 0.6
        wheel_radius: 车轮半径，默认 0.2
        label: 标签 MathTex（如 "m=1kg"），默认空
        color: 车身/车轮颜色，默认 None（使用 WHITE）

    返回：VGroup，named_parts 含 body/wheel_l/wheel_r；
         connection_points 含 center（质心）；component_type="car"

    坐标快照行为：
        connection_points 和 named_parts 中的坐标在 VGroup 创建时被记录为静态快照。
        对返回的 VGroup 执行 .rotate()、.scale()、.shift() 等变换后，
        这些快照坐标不会自动更新。调用者必须在变换后通过动态查询获取正确坐标：

        - 质心: car.named_parts["body"].get_center()     （而非 car.connection_points["center"]）
        - 底部: car.get_bottom() 或 car.named_parts["body"].get_bottom()
        - 左轮: car.named_parts["wheel_l"].get_center()
        - 右轮: car.named_parts["wheel_r"].get_center()

    标准依据：人教版初中物理教材小车符号
    """
    bottom_center = (
        np.array(bottom_center, dtype=float)
        if bottom_center is not None
        else np.array(ORIGIN)
    )
    body_color = color if color else WHITE

    # 车身（矩形，底部中心定位）
    body_bottom = bottom_center + np.array([0, wheel_radius * 2, 0])
    body_center = body_bottom + np.array([0, height / 2, 0])
    body = Rectangle(
        width=width,
        height=height,
        color=body_color,
        stroke_width=2,
    )
    body.move_to(body_center)

    # 左侧车轮（位于车身左下方）
    wheel_l_center = bottom_center + np.array(
        [-width / 2 + wheel_radius * 1.5, wheel_radius, 0]
    )
    wheel_l = Circle(radius=wheel_radius, color=body_color, stroke_width=2)
    wheel_l.move_to(wheel_l_center)

    # 右侧车轮（位于车身右下方）
    wheel_r_center = bottom_center + np.array(
        [width / 2 - wheel_radius * 1.5, wheel_radius, 0]
    )
    wheel_r = Circle(radius=wheel_radius, color=body_color, stroke_width=2)
    wheel_r.move_to(wheel_r_center)

    group = VGroup(body, wheel_l, wheel_r)

    if label:
        lbl = MathTex(label, font_size=28)
        lbl.move_to(body.get_center() + UP * (height / 2 + 0.1 + 0.12))
        group.add(lbl)

    group.connection_points = {"center": body_center.copy()}
    group.named_parts = {"body": body, "wheel_l": wheel_l, "wheel_r": wheel_r}
    group.component_type = "car"
    return group


def create_lever(
    fulcrum=None, length=3.0, label_left="", label_right="", label_fulcrum=""
):
    """创建杠杆图元（人教版简单机械 / GB/T 4460）

    功能：创建直杆 + 支点三角形的杠杆符号，支持在左右两端标注动力/阻力。

    参数：
        fulcrum: 支点位置 [x, y, 0]，默认 ORIGIN
        length: 杠杆总长度，默认 3.0
        label_left: 左端（动力）标签 MathTex（如 "F_1"），默认空
        label_right: 右端（阻力）标签 MathTex（如 "F_2"），默认空
        label_fulcrum: 支点标签（如 "支点"），默认空

    返回：VGroup，named_parts 含 bar/fulcrum_triangle；
         connection_points 含 left/right（杠杆两端）；component_type="lever"

    标准依据：人教版简单机械杠杆符号
    """
    fulcrum = (
        np.array(fulcrum, dtype=float) if fulcrum is not None else np.array(ORIGIN)
    )

    bar_left = fulcrum + np.array([-length / 2, 0, 0])
    bar_right = fulcrum + np.array([length / 2, 0, 0])

    # 杠杆直杆
    bar = Line(bar_left, bar_right, stroke_width=4, color=WHITE)

    # 支点三角形（倒三角）
    tri_half_w = 0.3
    tri_height = 0.25
    triangle_pts = [
        fulcrum + np.array([0, -tri_height, 0]),
        fulcrum + np.array([-tri_half_w, 0, 0]),
        fulcrum + np.array([tri_half_w, 0, 0]),
    ]
    from manim import Polygon

    fulcrum_triangle = Polygon(
        *triangle_pts,
        color=WHITE,
        stroke_width=2,
        fill_opacity=0,
    )

    group = VGroup(bar, fulcrum_triangle)

    # 左端力臂标签（显式坐标定位，遵循 F1：禁用 .next_to()）
    if label_left:
        lbl_l = MathTex(label_left, font_size=28)
        lbl_l.move_to(bar_left + DOWN * 0.3)
        group.add(lbl_l)

    # 右端力臂标签
    if label_right:
        lbl_r = MathTex(label_right, font_size=28)
        lbl_r.move_to(bar_right + DOWN * 0.3)
        group.add(lbl_r)

    # 支点标签
    if label_fulcrum:
        lbl_f = Text(label_fulcrum, font_size=20, color=WHITE)
        lbl_f.move_to(fulcrum + DOWN * 0.2)
        group.add(lbl_f)

    group.connection_points = {
        "fulcrum": fulcrum.copy(),
        "left": bar_left.copy(),
        "right": bar_right.copy(),
    }
    group.named_parts = {"bar": bar, "fulcrum_triangle": fulcrum_triangle}
    group.component_type = "lever"
    return group


def create_wall(
    position="bottom", length=3.0, height=0.5, orientation="vertical", label=""
):
    """创建墙体图元（人教版力学 / 碰撞/弹力场景）

    功能：创建矩形框架内填充满 45° 斜线纹理（砖墙/刚性墙符号）。
         水平墙体（position="bottom"）用于斜面、滑块等场景；
         垂直墙体（orientation="vertical"）用于竖直碰撞场景。

    参数：
        position: 墙体放置基准位置关键词，默认 "bottom"
                  （"bottom" = Y轴下方，Y轴向上坐标系）
        length: 墙体长度，默认 3.0
        height: 墙体高度，默认 0.5
        orientation: 墙体朝向，"horizontal"（默认）或 "vertical"
        label: 标签 MathTex，默认空

    返回：VGroup，含 wall_rect + 斜线纹理列表；
         connection_points 含 top/bottom 或 left/right；
         component_type="wall"

    标准依据：人教版教材力学墙体符号（矩形+45°斜线纹理=刚性边界）
    """
    # 确定墙体基准坐标（position="bottom" 时墙体在 Y=0 以下）
    if position == "bottom":
        anchor = np.array([-length / 2, -height / 2, 0], dtype=float)
        anchor_top = anchor + np.array([0, height, 0])
    else:
        # 垂直墙体：左侧边缘对齐 anchor
        anchor = np.array([-length / 2, -height / 2, 0], dtype=float)
        anchor_top = anchor + np.array([0, height, 0])

    wall_rect = Rectangle(
        width=length,
        height=height,
        color=WHITE,
        stroke_width=2,
    )
    wall_rect.move_to(anchor + np.array([length / 2, height / 2, 0]))

    group = VGroup(wall_rect)

    # 45° 斜线纹理（均匀填充矩形内部）
    line_spacing = 0.25  # 斜线间距
    n_lines = int(length / line_spacing) + 2
    for i in range(n_lines):
        x_offset = -length / 2 + i * line_spacing

        # 上斜线（从左下到右上的 45° 斜线段）
        # 确保斜线在矩形范围内
        x1 = max(x_offset, -length / 2)
        y1 = max(0, -height / 2)
        x2 = min(x_offset + line_spacing * 2, length / 2)
        y2 = min(line_spacing * 2, height / 2)

        if x1 < length / 2 and x2 > -length / 2:
            # 截取矩形内的部分
            slant_line = Line(
                [x1, -height / 2, 0],
                [x2, height / 2, 0],
                color=WHITE,
                stroke_width=1,
            )
            group.add(slant_line)

    if label:
        lbl = MathTex(label, font_size=28)
        lbl.move_to(wall_rect.get_center() + UP * (height / 2 + 0.1 + 0.12))
        group.add(lbl)

    if orientation == "vertical":
        group.connection_points = {
            "left": anchor.copy(),
            "right": anchor + np.array([length, 0, 0]),
        }
    else:
        group.connection_points = {
            "bottom": anchor.copy(),
            "top": anchor_top.copy(),
        }
    group.named_parts = {"wall_rect": wall_rect}
    group.component_type = "wall"
    return group


def create_container(pts, label="", style=None):
    """创建容器图元（人教版物理浮力实验）

    功能：创建任意多边形容器轮廓（梯形/矩形/任意形状）。
         参考 draw-engine.js drawContainer 的多边形闭合路径规范。
         默认使用梯形（截头锥形烧杯截面），常用于浮力实验。

    参数：
        pts: 容器顶点列表，至少 3 个点 [[x,y], ...]，闭合路径
             默认梯形：底部窄、顶部宽（截头锥形）
        label: 标签 MathTex（如 "液面"），默认空
        style: 样式字典，默认空
            stroke_color: 轮廓颜色，默认 WHITE
            line_width: 线宽，默认 2
            opacity: 透明度，默认 1.0

    返回：VGroup，named_parts 含 boundary_polygon；
         connection_points 含 top（液面上沿）；
         component_type="container"

    标准依据：人教版物理浮力实验容器（梯形截面烧杯）
    """
    style = style or {}
    stroke_color = style.get("stroke_color", WHITE)
    line_width = style.get("line_width", 2)
    opacity = style.get("opacity", 1.0)

    if len(pts) < 3:
        raise ValueError(f"容器至少需要 3 个顶点，当前只有 {len(pts)} 个")

    pts_arr = [np.array(p, dtype=float) for p in pts]
    boundary_pts = pts_arr + [pts_arr[0]]  # 闭合

    # 创建多边形边界线
    lines = []
    for i in range(len(boundary_pts) - 1):
        line = Line(
            boundary_pts[i],
            boundary_pts[i + 1],
            stroke_width=line_width,
            color=stroke_color,
        )
        lines.append(line)

    group = VGroup(*lines)
    if opacity < 1.0:
        group.set_stroke(opacity=opacity)

    if label:
        # 标签置于容器几何中心
        cx = sum(p[0] for p in pts_arr) / len(pts_arr)
        cy = sum(p[1] for p in pts_arr) / len(pts_arr)
        lbl = MathTex(label, font_size=28).move_to([cx, cy, 0])
        group.add(lbl)

    # 计算顶边中点（液面基准线）
    top_points = sorted(pts_arr, key=lambda p: p[1], reverse=True)
    top_edge = [top_points[0], top_points[1]] if len(top_points) >= 2 else [pts_arr[-1]]
    top_mid = sum(np.array(top_edge)) / len(top_edge)

    group.connection_points = {"top": top_mid}
    group.named_parts = {"boundary_polygon": group}
    group.component_type = "container"
    return group


def create_liquid(pts, color="#4DABF7", style=None):
    """创建液体填充图元（人教版物理浮力实验）

    功能：在多边形区域（容器内）填充液体颜色。
         参考 draw-engine.js drawLiquid 的 fill 逻辑。
         填充颜色默认为淡蓝色（常见液体配色）。

    参数：
        pts: 液体区域顶点列表 [[x,y], ...]（通常与容器下层重合）
        color: 填充颜色，默认 "#4DABF7"（淡蓝/水的颜色）
        style: 样式字典，默认空
            fill_color: 覆盖颜色
            opacity: 填充透明度，默认 0.7

    返回：VGroup，named_parts 含 fill_polygon；
         component_type="liquid"

    标准依据：人教版物理浮力实验液体填充表示
    """
    style = style or {}
    fill_color = style.get("fill_color", color)
    opacity = style.get("opacity", 0.7)

    if len(pts) < 3:
        raise ValueError(f"液体区域至少需要 3 个顶点，当前只有 {len(pts)} 个")

    pts_arr = [np.array(p, dtype=float) for p in pts]
    from manim import Polygon as PolyFill

    fill_poly = PolyFill(
        *pts_arr,
        color=fill_color,
        stroke_width=0,
        fill_opacity=opacity,
    )

    fill_poly.component_type = "liquid"
    fill_poly.named_parts = {"fill_polygon": fill_poly}
    fill_poly.connection_points = {}

    # 返回单个多边形对象，而非 VGroup
    return fill_poly


# ════════════════════════════════════════════════════════════
# 电路组装工具
# ════════════════════════════════════════════════════════════


def build_series_circuit(components_config, start_pos=None, direction=RIGHT):
    """构建完整串联回路（IEC 60617 / GB/T 4728 / 人教版）

    功能：根据元件配置列表构建矩形串联回路，元件沿指定方向排列在回路顶部，
         回路底部和两侧用导线闭合。自动添加节点圆点。

    参数：
        components_config: 元件配置列表，每项为 dict:
            {"type": "battery|resistor|bulb|switch|ammeter|rheostat",
             "params": {type-specific kwargs}}
        start_pos: 回路左上角起点 [x, y, 0]，默认 [-3, 1, 0]
        direction: 主排列方向（RIGHT/UP 等），默认 RIGHT（水平排列）

    返回：VGroup，含所有元件、导线、节点；附带 circuit_meta 属性

    标准依据：IEC 60617 / GB/T 4728（闭合回路、导线横平竖直、节点标记）
    """
    if start_pos is None:
        start_pos = np.array([-3, 1, 0], dtype=float)
    else:
        start_pos = np.array(start_pos, dtype=float)

    dir_vec = np.array(direction, dtype=float)
    dir_len = np.linalg.norm(dir_vec)
    if dir_len < 1e-6:
        dir_vec = np.array(RIGHT)
    else:
        dir_vec = dir_vec / dir_len

    perp = _perpendicular(dir_vec)
    component_spacing = 1.5
    loop_height = 2.0  # 回路高度（底部到顶部间距）

    parts = VGroup()
    current_pos = start_pos.copy()
    component_list = []

    for config in components_config:
        comp_type = config.get("type", "")
        params = config.get("params", {})

        comp_start = current_pos.copy()
        comp_end = current_pos + dir_vec * component_spacing

        comp = _create_from_config(comp_type, comp_start, comp_end, params)
        parts.add(comp)
        component_list.append(comp)
        current_pos = comp_end.copy()

    # 回路底部闭合路径
    end_top = current_pos.copy()

    # 右侧竖直导线（下拐）
    corner_right_top = end_top.copy()
    corner_right_bottom = end_top - perp * loop_height
    wire_right_down = Line(
        corner_right_top, corner_right_bottom, stroke_width=2, color=WHITE
    )
    parts.add(wire_right_down)

    # 底部水平导线（回路底边）
    corner_left_bottom = start_pos - perp * loop_height
    wire_bottom = Line(
        corner_right_bottom, corner_left_bottom, stroke_width=2, color=WHITE
    )
    parts.add(wire_bottom)

    # 左侧竖直导线（上拐回起点）
    wire_left_up = Line(corner_left_bottom, start_pos, stroke_width=2, color=WHITE)
    parts.add(wire_left_up)

    # 节点圆点（GB/T 4728 要求 T 型连接处标注实心圆点）
    for corner in [
        corner_right_top,
        corner_right_bottom,
        corner_left_bottom,
        start_pos,
    ]:
        junction = create_junction_dot(corner)
        parts.add(junction)

    parts.circuit_meta = {
        "components": component_list,
        "start_pos": start_pos.copy(),
        "end_top": end_top.copy(),
        "corners": {
            "right_top": corner_right_top.copy(),
            "right_bottom": corner_right_bottom.copy(),
            "left_bottom": corner_left_bottom.copy(),
        },
        "loop_height": loop_height,
    }
    return parts


def build_parallel_branch(
    main_circuit, branch_start_node, branch_end_node, components_config
):
    """构建并联分支（IEC 60617 / GB/T 4728 / 人教版）

    功能：在主回路两个节点之间插入并联分支，分支沿垂直方向展开，
         元件水平排列在分支内，两端用导线连接到主回路节点。

    参数：
        main_circuit: 主回路 VGroup（由 build_series_circuit 返回）
        branch_start_node: 分支起点坐标 [x, y, 0]（主回路上的节点）
        branch_end_node: 分支终点坐标 [x, y, 0]（主回路上的节点）
        components_config: 分支内元件配置列表（同 build_series_circuit 格式）

    返回：VGroup，含分支元件、导线、节点；附带 branch_meta 属性

    标准依据：IEC 60617 / GB/T 4728（并联节点实心圆点标记）
    """
    branch_start = np.array(branch_start_node, dtype=float)
    branch_end = np.array(branch_end_node, dtype=float)
    branch_dir = _unit_direction(branch_start, branch_end)
    perp = _perpendicular(branch_dir)

    branch_depth = 0.8  # 分支向垂直方向偏移的距离
    component_spacing = 1.2

    parts = VGroup()

    # 分支起点和终点的偏移位置（向垂直方向偏移）
    b_start = branch_start - perp * branch_depth
    b_end = branch_end - perp * branch_depth

    # 入口竖直导线
    wire_in = create_wire(branch_start, b_start)
    parts.add(wire_in)

    current_pos = b_start.copy()
    component_list = []

    for config in components_config:
        comp_type = config.get("type", "")
        params = config.get("params", {})
        comp_start = current_pos.copy()
        comp_end = current_pos + branch_dir * component_spacing

        comp = _create_from_config(comp_type, comp_start, comp_end, params)
        parts.add(comp)
        component_list.append(comp)
        current_pos = comp_end.copy()

    # 出口竖直导线
    wire_out = create_wire(b_end, branch_end)
    parts.add(wire_out)

    # 节点圆点（并联接入点必须标注）
    parts.add(create_junction_dot(branch_start))
    parts.add(create_junction_dot(branch_end))

    parts.branch_meta = {
        "components": component_list,
        "branch_start": branch_start.copy(),
        "branch_end": branch_end.copy(),
    }
    return parts


def _create_from_config(comp_type, comp_start, comp_end, params):
    """根据配置字典创建元件实例

    Args:
        comp_type: 元件类型字符串
        comp_start: 元件起点坐标
        comp_end: 元件终点坐标
        params: 元件参数字典

    Returns:
        对应类型的 VGroup 元件实例
    """
    type_map = {
        "battery": create_battery,
        "resistor": create_resistor,
        "switch": create_switch,
        "rheostat": create_rheostat,
    }
    center_map = {
        "bulb": create_bulb,
        "ammeter": create_ammeter,
        "voltmeter": create_voltmeter,
        "capacitor": create_capacitor,
    }

    if comp_type in type_map:
        return type_map[comp_type](comp_start, comp_end, **params)
    elif comp_type in center_map:
        center = (comp_start + comp_end) / 2
        return center_map[comp_type](center=center, **params)
    else:
        raise ValueError(f"未知元件类型: {comp_type}")


# ════════════════════════════════════════════════════════════
# 电流流动动画
# ════════════════════════════════════════════════════════════


def create_current_dots(wire_path, n_dots=8, color="#FF6666", radius=0.04):
    """创建电流方向移动电荷点（人教版 / physics.md Section 8.2）

    功能：沿导线路径均匀分布移动电荷点，用于电流方向可视化。

    参数：
        wire_path: 导线 Line 或 VMobject 路径对象
        n_dots: 电荷点数量，默认 8
        color: 点颜色，默认 "#FF6666"（电流方向红）
        radius: 点半径，默认 0.04

    返回：VGroup，包含均匀分布的 Dot 对象

    标准依据：人教版教材 / physics.md Section 8.2（正电荷移动方向标注）
    """
    dots = VGroup()
    for i in range(n_dots):
        proportion = (i + 0.5) / n_dots
        point = wire_path.point_at_proportion(proportion)
        dot = Dot(point=point, radius=radius, color=color)
        dots.add(dot)

    dots.component_type = "current_dots"
    dots._wire_path = wire_path
    return dots


def animate_current_flow(scene, dots_group, path, duration=2.0, direction="forward"):
    """播放电流流动动画（人教版 / physics.md Section 8.2）

    功能：驱动电荷点沿导线路径移动，表示电流方向。
         forward=正电荷方向（从正极到负极外部路径）；
         reverse=反向（电子流方向，可选）。

    参数：
        scene: Manim Scene 对象
        dots_group: create_current_dots 返回的 VGroup
        path: 导线路径 VMobject（Line / Polyline 等）
        duration: 动画时长（秒），默认 2.0
        direction: "forward" 或 "reverse"，默认 "forward"

    标准依据：人教版教材 / physics.md Section 8.2
    """
    if MoveAlongPath is not None:
        anim_path = path
        if direction == "reverse":
            anim_path = path.copy().reverse_direction()

        animations = []
        for dot in dots_group:
            anim = MoveAlongPath(dot, anim_path, run_time=duration)
            animations.append(anim)
        scene.play(AnimationGroup(*animations, lag_ratio=0.05))
    else:
        # 旧版 Manim 回退方案：逐点移动
        path_start = path.get_start()
        path_end = path.get_end()
        if direction == "reverse":
            target = path_start
        else:
            target = path_end

        animations = [dot.animate.move_to(target) for dot in dots_group]
        scene.play(AnimationGroup(*animations, lag_ratio=0.05, run_time=duration))


# ════════════════════════════════════════════════════════════
# 元件状态切换函数
# ════════════════════════════════════════════════════════════


def set_switch_state(switch_group, closed):
    """生成开关状态切换动画（GB/T 4728.02 / 人教版）

    功能：返回 Transform 动画，将开关臂从断开态切换为闭合态或反之。
         使用 Transform 保持 VGroup 内部引用有效性。

    参数：
        switch_group: create_switch 返回的 VGroup
        closed: 目标状态（True=闭合，False=断开）

    返回：Transform 动画对象，可由 scene.play() 执行

    标准依据：GB/T 4728.02 S00061（开关臂闭合/断开态切换）
    """
    arm = switch_group.named_parts["arm"]
    dot1_pos = switch_group.connection_points["dot1"]
    dot2_pos = switch_group.connection_points["dot2"]

    if closed:
        new_arm = Line(dot1_pos, dot2_pos, stroke_width=2, color=WHITE)
    else:
        unit_dir = _unit_direction(dot1_pos, dot2_pos)
        perp = _perpendicular(unit_dir)
        arm_len = SWITCH_CONTACT_GAP * 0.75
        open_end = dot1_pos + unit_dir * arm_len * 0.7 + perp * arm_len * 0.7
        new_arm = Line(dot1_pos, open_end, stroke_width=2, color=WHITE)

    switch_group.closed = closed
    return Transform(arm, new_arm)


def set_bulb_state(bulb_group, lit):
    """生成灯泡点亮/熄灭动画（人教版教材）

    功能：返回 Transform 动画，切换灯泡的填充状态。
         lit=True：ORANGE 半透明填充（点亮）；
         lit=False：移除填充（熄灭，恢复 YELLOW_C 空心）。

    参数：
        bulb_group: create_bulb 返回的 VGroup
        lit: 目标状态（True=点亮，False=熄灭）

    返回：Transform 动画对象，可由 scene.play() 执行

    标准依据：人教版教材（点亮=橙色半透明，熄灭=黄色空心）
    """
    outer = bulb_group.named_parts["outer"]
    center = outer.get_center()

    if lit:
        new_outer = Circle(radius=BULB_RADIUS, color=YELLOW_C, stroke_width=2)
        new_outer.set_fill(ORANGE, opacity=0.6)
        new_outer.move_to(center)
    else:
        new_outer = Circle(radius=BULB_RADIUS, color=YELLOW_C, stroke_width=2)
        new_outer.move_to(center)

    return Transform(outer, new_outer)


# ════════════════════════════════════════════════════════════
# 统一导出列表
# ════════════════════════════════════════════════════════════

__all__ = [
    # 颜色常量
    "CIRCUIT_COLORS",
    # 电路元件
    "create_battery",
    "create_resistor",
    "create_bulb",
    "create_switch",
    "create_ammeter",
    "create_voltmeter",
    "create_capacitor",
    "create_rheostat",
    # 尺寸常量
    "BATTERY_LONG_HALF",
    "BATTERY_SHORT_HALF",
    "BATTERY_GAP",
    "RESISTOR_WIDTH",
    "RESISTOR_HEIGHT",
    "BULB_RADIUS",
    "WIRE_LENGTH",
    "SWITCH_CONTACT_GAP",
    "SWITCH_DOT_RADIUS",
    "METER_RADIUS",
    "CAPACITOR_PLATE_LENGTH",
    "CAPACITOR_PLATE_GAP",
    "RHEOSTAT_WIDTH",
    "RHEOSTAT_HEIGHT",
    # 辅助函数
    "_unit_direction",
    "_perpendicular",
    # 基础图元（电路）
    "create_wire",
    "create_junction_dot",
    "create_arc_bridge",
    "create_force_arrow",
    # 力学与流体图元（人教版 / GB/T 4460）
    "create_car",
    "create_lever",
    "create_wall",
    "create_inclined_plane",
    "create_container",
    "create_liquid",
    # 电路组装
    "build_series_circuit",
    "build_parallel_branch",
    # 电流动画
    "create_current_dots",
    "animate_current_flow",
    # 状态切换
    "set_switch_state",
    "set_bulb_state",
]
