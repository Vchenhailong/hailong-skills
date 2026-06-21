#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三栏布局渲染测试 - 按网表规则绘制并联电路"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import (
    Text,
    MathTex,
    VGroup,
    DOWN,
    Write,
    FadeIn,
    config,
)
from scripts.layout.scene_base import LayoutScene
from scripts.layout.constants import ZoneConstants
from scripts.animation.subtitle_scroller import SubtitleScroller
from scripts.animation.typewriter import Typewriter
from scripts.physics_graphics import (
    create_battery,
    create_switch,
    create_resistor,
    create_ammeter,
    create_voltmeter,
    create_bulb,
    create_wire,
    create_junction_dot,
    validate_circuit_topology,
    WIRE_LENGTH,
    METER_RADIUS,
    RESISTOR_WIDTH,
)


class ThreeColumnTestScene(LayoutScene):
    """三栏布局测试场景"""

    layout_mode = "three_column"
    debug = True

    def construct(self):
        left_text = Text(
            "混联电路分析：R₁与R₂并联后，再与灯泡L₁串联。"
            "电流表测总电流，电压表测R₁电压。",
            font_size=ZoneConstants.FONT_SIZE_MAIN_THREE_COL_LEFT,
        )

        formula1 = MathTex(r"I = \frac{U}{R}")
        formula2 = MathTex(r"R_{\text{eq}} = \frac{R_1 R_2}{R_1 + R_2}")
        mid_formulas = VGroup(formula1, formula2)
        mid_formulas.arrange(DOWN, buff=ZoneConstants.ROW_BUFF * 1.5)

        circuit = self._build_manim_circuit()
        result = self.place_three_column(left_text, mid_formulas, circuit)

        subtitle_zone = self.get_subtitle_zone(layout_mode="three_column")
        scroller = SubtitleScroller(self, subtitle_zone, chars_per_line=20)
        subtitle_text = "混联电路中，并联部分电压相等，各支路电流之和等于干路电流。"

        self.play(Typewriter(left_text, run_time=2.0), run_time=2.0)
        for formula in mid_formulas:
            self.play(Write(formula), run_time=1.0)
        self.play(FadeIn(circuit), run_time=1.0)
        self.play(scroller.build_subtitle_animation(subtitle_text), run_time=3.0)

    def _build_manim_circuit(self) -> VGroup:
        """按网表规则绘制混联电路（匹配参考图布局）

        参考图拓扑（从左到右，扁矩形回路）：
          E(电源) → S(开关) → 并联块[R1‖R2, V测R1] → A(电流表) → ↓回线→ L(灯泡) → ←E-

        严格遵循 netlist.md 五步流程：
        1. 定范围 → 2. 定拓扑(含网表注释) → 3. 取坐标 → 4. 做连接(L型) → 5. 组合验证
        """

        # ─────────────────────────────────────────────────────────────────────
        # 一、定范围（netlist.md §一：仅从布局系统/物理常量获取）
        # ─────────────────────────────────────────────────────────────────────
        X_MIN = ZoneConstants.THREE_COL_RIGHT_X_MIN  # 2.35
        X_MAX = ZoneConstants.THREE_COL_RIGHT_X_MAX  # 6.75
        Y_MID = ZoneConstants.THREE_COL_Y_MID  # ≈0.36 (主干Y基准)
        GW = WIRE_LENGTH  # 0.3 (导线长度)
        MR = METER_RADIUS  # 0.25 (电表/灯泡半径)
        RW = RESISTOR_WIDTH  # 1.0 (电阻宽度)
        HB = ZoneConstants.THREE_COL_BRANCH_OFFSET  # 0.8 (并联垂直偏移)
        Y_RET = ZoneConstants.THREE_COL_RETURN_Y  # -2.0 (回线Y坐标)

        # Y轴层级定义
        Y_TOP = Y_MID + HB  # 上支路(R1)Y坐标
        Y_BOT = Y_MID - HB  # 下支路(R2)Y坐标

        # ─────────────────────────────────────────────────────────────────────
        # 二、定拓扑（netlist.md §二：纯逻辑校验，无坐标参与）
        #
        #   sch = '''E 0 1; down        % 电源 N0(-)→N1(+)
        #   S 1 2; right       % 开关 N1→N2
        #   R1 3 4; right      % R1水平 N3→N4 (并联上支路)
        #   R2 5 6; right      % R2水平 N5→N6 (并联下支路)
        #   V 4 6; down        % 电压表测R1(N4→N6), 在R1正上方
        #   A 7 8; right       % 电流表 N7→N8 (汇合后主干)
        #   L 9 0; ...         % 灯泡 N9→N0 (回线底部)'''
        #
        #   节点定义：
        #     N0  = 电源负极（回线终点）
        #     N1  = 电源正极 / 开关入口 / DFS起点
        #     N2  = 开关出口 / 分支前导
        #     N3  = R1左端(上支路入口)
        #     N4  = R1右端(上支路出口) / 电压表一端
        #     N5  = R2左端(下支路入口)
        #     N6  = R2右端(下支路出口) / 并联汇合点(q) / 电压表另一端
        #     N7  = 汇合后 / 电流表入口
        #     N8  = 电流表出口 / 回线下行起点
        #     N9  = 灯泡入口(回线上)
        #
        #   拓扑校验：
        #     串联链前段：N1→N2（电源+开关）
        #     并联块(p=N2延伸, q=N6)：上支路=R1(N3→N4) ‖ 下支路=R2(N5→N6)
        #     电压表V并联在R1两端(N4→N6)
        #     串联链续：q(N6)→N7→A(N7→N8)→回线(N8→N9→L→N0)
        #     闭环：DFS从N1出发，覆盖所有节点，回到N0 ✓
        # ─────────────────────────────────────────────────────────────────────

        # ─────────────────────────────────────────────────────────────────────
        # 三、取坐标 & 创建元件（netlist.md §三：常量组合，禁止自算/半值）
        #
        #  布局示意（X轴从左到右）：
        #    E    S         R1───┐     A
        #    |    ├──branch─┤V   ├──merge──○──↓
        #    |              R2───┘           │
        #    └────────────────────────────L─┘
        # ─────────────────────────────────────────────────────────────────────

        # --- 主干 X 轴定位（常量组合，从左到右）---
        E_x = X_MIN + GW  # 电源X
        S_left = E_x + GW  # 开关左端口X
        S_right = S_left + GW * 2  # 开关右端口X（宽度≈2*GW）
        branch_x = S_right + GW  # 并联分支点X
        R1_x_start = branch_x + GW  # R1左端X（横出段后）
        R1_x_end = R1_x_start + RW  # R1右端X（电阻宽度RW）
        R2_x_start = branch_x + GW  # R2左端X（与R1上下对齐）
        R2_x_end = R2_x_start + RW  # R2右端X（与R1等宽）
        merge_x = R1_x_end + GW  # 汇合点X（R1右侧预留导线）
        A_in_x = merge_x + GW  # 电流表入口X
        A_cx = A_in_x + MR  # 电流表圆心X
        A_out_x = A_cx + MR  # 电流表出口X

        # --- 1. 电源（竖直）：负极N0在下, 正极N1在上对齐Y_MID ---
        battery = create_battery(
            start=[E_x, Y_MID - GW, 0],  # N0: 负极
            end=[E_x, Y_MID, 0],  # N1: 正极
            voltage=r"9\,\text{V}",
        )

        # --- 2. 开关（水平导线穿过，触点左右排列）：left=N1, right=N2 ---
        # "horizontal" 模式 = 导线水平 + 触点左右 = 参考图标准画法
        switch = create_switch(
            start=[S_left, Y_MID, 0],
            end=[S_right, Y_MID, 0],
            closed=False,  # 未闭合状态（参考图）
            label=r"S",
            orientation="horizontal",  # 导线水平/触点左右
        )

        # --- 3. R1（水平，并联上支路）：N3→N4 ---
        resistor1 = create_resistor(
            start=[R1_x_start, Y_TOP, 0],  # N3: 左端
            end=[R1_x_end, Y_TOP, 0],  # N4: 右端
            label=r"R_1",
            resistance=r"10\,\Omega",
        )

        # --- 4. R2（水平，并联下支路）：N5→N6 ---
        resistor2 = create_resistor(
            start=[R2_x_start, Y_BOT, 0],  # N5: 左端
            end=[R2_x_end, Y_BOT, 0],  # N6: 右端(=q汇合点)
            label=r"R_2",
            resistance=r"20\,\Omega",
        )

        # --- 5. 电压表（圆心定位在R1正上方）：测R1两端电压(N4→N6) ---
        V_cx = (R1_x_start + R1_x_end) / 2  # R1中点X（用均值，非EW/2偏移）
        V_cy = Y_TOP + MR + GW  # R1正上方（MR+GW确保不重叠）
        voltmeter = create_voltmeter(
            center=[V_cx, V_cy, 0],
            label=r"V",
        )

        # --- 6. 电流表（圆心定位，在汇合点右侧主干上）：测总电流 ---
        ammeter = create_ammeter(
            center=[A_cx, Y_MID, 0],
            label=r"A",
        )

        # --- 7. 灯泡（圆心定位在回线上）：串联在回路底部 ---
        L_cx = (E_x + A_out_x) / 2  # 居中于电源和电流表之间
        bulb = create_bulb(
            center=[L_cx, Y_RET, 0],
            label=r"L_1",
        )

        # ─────────────────────────────────────────────────────────────────────
        # 四、端口获取（netlist.md §三：统一 .start_port/.end_port）
        # ─────────────────────────────────────────────────────────────────────
        E_neg = battery.start_port  # N0
        E_pos = battery.end_port  # N1
        S_start = switch.start_port  # N1(=E_pos侧)
        S_end = switch.end_port  # N2
        R1_start = resistor1.start_port  # N3 (R1左端)
        R1_end = resistor1.end_port  # N4 (R1右端)
        R2_start = resistor2.start_port  # N5 (R2左端)
        R2_end = resistor2.end_port  # N6 (=q, R2右端)
        V_left = voltmeter.left_port  # 电压表左端
        V_right = voltmeter.right_port  # 电压表右端
        A_in_port = ammeter.left_port  # N7 (电流表入口)
        A_out_port = ammeter.right_port  # N8 (电流表出口)
        L_in_port = bulb.left_port  # N9 (灯泡入口)
        L_out_port = bulb.right_port  # 灯泡出口

        # 预定义锚点坐标（基于已确定的常量组合）
        pt_branch = np.array([branch_x, Y_MID, 0])  # 分支点(p前导)

        # ─────────────────────────────────────────────────────────────────────
        # 五、做连接（netlist.md §四：全L型走线，所有导线命名）
        # ─────────────────────────────────────────────────────────────────────
        wires = []
        junctions = []

        # ----- 5.1 电源正极(N1) → 竖直到Y_MID → 水平到开关入口 -----
        # （电池端口现在指向实际极板位置，需要L型走线）
        pt_E_S_mid = np.array([E_x, Y_MID, 0])  # 中转点（电源X + 主干Y）
        W_E_S_vert = create_wire(E_pos, pt_E_S_mid)  # 竖直向上到主干
        wires.append(W_E_S_vert)
        W_E_S_horiz = create_wire(pt_E_S_mid, S_start)  # 水平向右到开关左触点
        wires.append(W_E_S_horiz)
        junctions.append(create_junction_dot(pt_E_S_mid))

        # ----- 5.2 开关出口(N2) → 分支点 -----
        W_S_branch = create_wire(S_end, pt_branch)
        wires.append(W_S_branch)
        junctions.append(create_junction_dot(S_end))
        junctions.append(create_junction_dot(pt_branch))  # T型分岔点

        # ----- 5.3 R1 并联上支路（三段式L型 + 接入段水平导线）-----
        # 横出 → 纵跨 → 水平接入(避免与电阻边缘重叠)
        pt_R1_corner = np.array([R1_x_start - GW, Y_MID, 0])  # L型拐点(左移GW)
        pt_R1_lead_in = np.array([R1_x_start - GW, Y_TOP, 0])  # R1左端外侧接入点

        W_R1_horiz_out = create_wire(pt_branch, pt_R1_corner)  # 横出：水平向右
        wires.append(W_R1_horiz_out)

        W_R1_vert_up = create_wire(pt_R1_corner, pt_R1_lead_in)  # 纵跨：竖直向上
        wires.append(W_R1_vert_up)

        W_R1_access = create_wire(pt_R1_lead_in, R1_start)  # 接入：水平进入R1左端
        wires.append(W_R1_access)
        junctions.append(create_junction_dot(R1_start))

        # ----- 5.4 R2 并联下支路（三段式L型 + 接入段水平导线）-----
        pt_R2_corner = np.array([R2_x_start - GW, Y_MID, 0])  # L型拐点(左移GW)
        pt_R2_lead_in = np.array([R2_x_start - GW, Y_BOT, 0])  # R2左端外侧接入点

        W_R2_horiz_out = create_wire(
            pt_branch, pt_R2_corner
        )  # 横出：水平向右(共用pt_branch)
        wires.append(W_R2_horiz_out)

        W_R2_vert_down = create_wire(pt_R2_corner, pt_R2_lead_in)  # 纵跨：竖直向下
        wires.append(W_R2_vert_down)

        W_R2_access = create_wire(pt_R2_lead_in, R2_start)  # 接入：水平进入R2左端
        wires.append(W_R2_access)
        junctions.append(create_junction_dot(R2_start))

        # ----- 5.5 并联汇合（R1/R2右端 → 引出段水平导线 → 主干Y_MID → 汇合点）-----
        pt_merge = np.array([merge_x, Y_MID, 0])  # 汇合点

        # R1右端 → 水平引出 → 下降到Y_MID → 向右到汇合点
        pt_R1_lead_out = np.array([R1_x_end + GW, Y_TOP, 0])  # R1右端外侧引出点
        pt_R1_merge_corner = np.array([R1_x_end + GW, Y_MID, 0])

        W_R1_lead_out = create_wire(R1_end, pt_R1_lead_out)  # 引出：水平离开R1右端
        wires.append(W_R1_lead_out)
        W_R1_merge_down = create_wire(pt_R1_lead_out, pt_R1_merge_corner)  # 竖直下降
        wires.append(W_R1_merge_down)
        W_R1_to_merge = create_wire(pt_R1_merge_corner, pt_merge)  # 水平向右到汇合点
        wires.append(W_R1_to_merge)

        # R2右端 → 水平引出 → 上升到Y_MID → 向右到汇合点
        pt_R2_lead_out = np.array([R2_x_end + GW, Y_BOT, 0])  # R2右端外侧引出点
        pt_R2_merge_corner = np.array([R2_x_end + GW, Y_MID, 0])

        W_R2_lead_out = create_wire(R2_end, pt_R2_lead_out)  # 引出：水平离开R2右端
        wires.append(W_R2_lead_out)
        W_R2_merge_up = create_wire(pt_R2_lead_out, pt_R2_merge_corner)  # 竖直上升
        wires.append(W_R2_merge_up)
        W_R2_to_merge = create_wire(pt_R2_merge_corner, pt_merge)  # 水平向右到汇合点
        wires.append(W_R2_to_merge)
        junctions.append(create_junction_dot(pt_merge))

        # ----- 5.6 电压表接线（L型 + 接入段水平导线：V在R1正上方）-----
        # V_left → L型拐点 → 水平接入 → R1左端(N3)
        pt_V_L_corner = np.array([R1_x_start - GW, V_cy, 0])  # L型拐点(与R1同X偏左GW)
        pt_V_L_lead = np.array(
            [R1_x_start - GW, Y_TOP, 0]
        )  # 与R1左端同Y的接入点(复用pt_R1_lead_in)

        W_V_L_horiz = create_wire(V_left, pt_V_L_corner)  # 水平向左
        wires.append(W_V_L_horiz)
        W_V_L_vert = create_wire(pt_V_L_corner, pt_V_L_lead)  # 竖直向下
        wires.append(W_V_L_vert)
        W_V_L_access = create_wire(pt_V_L_lead, R1_start)  # 水平进入R1左端
        wires.append(W_V_L_access)
        junctions.append(create_junction_dot(pt_V_L_corner))

        # V_right → L型拐点 → 水平接入 → R1右端(N4)
        pt_V_R_corner = np.array([R1_x_end + GW, V_cy, 0])  # L型拐点(与R1同X偏右GW)
        pt_V_R_lead = np.array(
            [R1_x_end + GW, Y_TOP, 0]
        )  # 与R1右端同Y的接入点(复用pt_R1_lead_out)

        W_V_R_horiz = create_wire(V_right, pt_V_R_corner)  # 水平向右
        wires.append(W_V_R_horiz)
        W_V_R_vert = create_wire(pt_V_R_corner, pt_V_R_lead)  # 竖直向下
        wires.append(W_V_R_vert)
        W_V_R_access = create_wire(pt_V_R_lead, R1_end)  # 水平进入R1右端
        wires.append(W_V_R_access)
        junctions.append(create_junction_dot(pt_V_R_corner))

        # ----- 5.7 汇合点 → 电流表入口 -----
        W_merge_A = create_wire(pt_merge, A_in_port)
        wires.append(W_merge_A)
        junctions.append(create_junction_dot(A_in_port))

        # ----- 5.8 回线（电流表出口 → 水平引出 → 向下 → 经灯泡(含引出段) → 回到电源负极）-----
        #  8.1 电流表出口(N8) → 水平引出GW → 竖直向下到回线高度（与电阻/灯泡一致）
        pt_A_lead_out = np.array([A_out_x + GW, Y_MID, 0])  # 电流表右端外侧引出点
        pt_A_bottom = np.array([A_out_x + GW, Y_RET, 0])  # 引出点正下方

        W_A_lead_out = create_wire(A_out_port, pt_A_lead_out)  # 引出：水平向右GW
        wires.append(W_A_lead_out)
        W_A_down = create_wire(pt_A_lead_out, pt_A_bottom)  # 竖直向下
        wires.append(W_A_down)
        junctions.append(create_junction_dot(A_out_port))
        junctions.append(create_junction_dot(pt_A_bottom))

        #  8.2 回线右段：电流表下方 → 水平引出 → 灯泡右端（避免与灯泡边缘重叠）
        pt_L_lead_out = np.array([L_out_port[0] + GW, Y_RET, 0])  # 灯泡右端外侧引出点

        W_ret_to_L_horiz = create_wire(pt_A_bottom, pt_L_lead_out)  # 水平向左到引出点
        wires.append(W_ret_to_L_horiz)
        W_ret_to_L_access = create_wire(pt_L_lead_out, L_out_port)  # 水平进入灯泡右端
        wires.append(W_ret_to_L_access)
        junctions.append(create_junction_dot(L_out_port))

        #  8.3 回线左段：灯泡左端 → 水平引出 → 电源正下方（避免与灯泡边缘重叠）
        pt_L_lead_in = np.array([L_in_port[0] - GW, Y_RET, 0])  # 灯泡左端外侧引出点
        pt_E_below = np.array([E_x, Y_RET, 0])

        W_L_E_lead_out = create_wire(L_in_port, pt_L_lead_in)  # 引出：水平离开灯泡左端
        wires.append(W_L_E_lead_out)
        W_L_to_E = create_wire(pt_L_lead_in, pt_E_below)  # 水平向左到电源下方
        wires.append(W_L_to_E)
        junctions.append(create_junction_dot(L_in_port))
        junctions.append(create_junction_dot(pt_E_below))

        #  8.4 回线末段：电源正下方 → 电源负极(N0)（竖直向上）
        W_E_return = create_wire(pt_E_below, E_neg)
        wires.append(W_E_return)
        junctions.append(create_junction_dot(E_neg))

        # ─────────────────────────────────────────────────────────────────────
        # 六、组合验证（netlist.md §四 + validate_circuit_topology）
        # ─────────────────────────────────────────────────────────────────────
        circuit = VGroup(
            battery,
            switch,
            resistor1,
            resistor2,
            voltmeter,
            ammeter,
            bulb,
            *wires,
            *junctions,
        )

        is_valid, errors = validate_circuit_topology(circuit)
        print(
            f"[ThreeColumnTest] {'✓ 拓扑验证通过' if is_valid else '✗ 拓扑问题: ' + str(errors)}"
        )

        return circuit


if __name__ == "__main__":
    config.quality = "low_quality"
    if "--disable_caching" not in sys.argv:
        sys.argv.append("--disable_caching")
    scene = ThreeColumnTestScene(skip_env_check=True, debug=True)
    scene.render()
