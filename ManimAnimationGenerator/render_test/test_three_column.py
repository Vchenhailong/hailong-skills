#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三栏布局渲染测试：左中文文本 + 中LaTeX公式 + 右Manim电路图 + 滚动字幕。

遵循规范：
- SKILL.md 排版布局绝对遵循红线（M1-M7 / F1-F7）
- layout.md 分栏布局规范 + 区域安全边界
- physics.md 电路图 IEC 60617 / GB/T 4728 + 人教版规范
- math_latex.md 公式完整性 + 数值与单位间空格
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    create_resistor,
    create_ammeter,
    create_voltmeter,
    create_bulb,
    create_wire,
    create_junction_dot,
    create_current_arrow,
    validate_circuit_topology,
)


class ThreeColumnTestScene(LayoutScene):
    """三栏布局测试场景：左文字说明 + 中公式推导 + 右Manim电路图。

    电路规格（physics.md 规范）：
    - 电源电压：9V
    - R₁ = 10Ω，R₂ = 20Ω（并联）
    - 并联支路整体与灯泡 L₁ 串联
    - 电流表串联在干路测量总电流
    - 电压表并联在 R₁ 两端

    电路拓扑：
    电源(+) → 电流表 → 并联节点A → [R₁上支路 / R₂下支路] → 并联节点B → 灯泡 → 电源(-)
    """

    layout_mode = "three_column"
    debug = True

    def construct(self):
        # ──────────────────────────────────────────────────────────────────
        # 步骤 1：创建各栏内容
        # ──────────────────────────────────────────────────────────────────

        # 左栏：步骤说明
        left_text = Text(
            "混联电路分析：R₁与R₂并联后，再与灯泡L₁串联。"
            "电流表测总电流，电压表测R₁电压。",
            font_size=ZoneConstants.FONT_SIZE_MAIN_THREE_COL_LEFT,
        )

        # 中栏：公式
        formula1 = MathTex(
            r"I = \frac{U}{R}",
            font_size=ZoneConstants.FONT_SIZE_MAIN_THREE_COL_MID,
        )
        formula2 = MathTex(
            r"R_{\text{eq}} = \frac{R_1 R_2}{R_1 + R_2}",
            font_size=ZoneConstants.FONT_SIZE_MAIN_THREE_COL_MID,
        )
        mid_formulas = VGroup(formula1, formula2)
        mid_formulas.arrange(DOWN, buff=ZoneConstants.ROW_BUFF * 1.5)

        # 右栏：Manim 电路图
        circuit = self._build_manim_circuit()

        # ──────────────────────────────────────────────────────────────────
        # 步骤 2：使用 place_three_column 放置三栏
        # ──────────────────────────────────────────────────────────────────
        result = self.place_three_column(left_text, mid_formulas, circuit)

        # ──────────────────────────────────────────────────────────────────
        # 步骤 3：字幕准备
        # ──────────────────────────────────────────────────────────────────
        subtitle_zone = self.get_subtitle_zone(layout_mode="three_column")
        scroller = SubtitleScroller(self, subtitle_zone, chars_per_line=20)
        subtitle_text = "混联电路中，并联部分电压相等，各支路电流之和等于干路电流。"
        scroller._prepare(subtitle_text)
        scroller._last_tick_time = 0.0

        # ──────────────────────────────────────────────────────────────────
        # 步骤 4：动画执行
        # ──────────────────────────────────────────────────────────────────
        self.play(Typewriter(left_text, run_time=2.0), run_time=2.0)

        for formula in mid_formulas:
            self.play(Write(formula), run_time=1.0)

        self.play(FadeIn(circuit), run_time=1.0)

        self.play(scroller.build_subtitle_animation(subtitle_text), run_time=3.0)

    def _build_manim_circuit(self) -> VGroup:
        """使用 Manim 原生绘图构建混联电路。

        电路拓扑（physics.md IEC 60617 / GB/T 4728 规范）：
        电源(+) → 电流表A → 并联节点A → [R₁上支路 / R₂下支路] → 并联节点B → 灯泡L₁ → 电源(-)
        电压表V：并联在R₁两端

        测量规范（physics.md §10.7）：
        - 电流表：串联在干路，测量总电流 I = I₁ + I₂
        - 电压表：并联在R₁两端，测量 U₁ = U₂（并联电压相等）
        """
        # ═══════════════════════════════════════════════════════════════════
        # 坐标规划（右栏区域 X∈[2.35, 6.75], Y∈[-2.88, 3.60]）
        # ═══════════════════════════════════════════════════════════════════
        # Y 坐标
        main_y = 0.8      # 主回路线
        upper_y = 2.0     # R₁ 上支路
        lower_y = -0.6    # R₂ 下支路
        bat_top_y = 2.5   # 电池正极
        bat_bot_y = -1.0  # 电池负极

        # X 坐标
        bat_x = 2.6       # 电池 x 位置
        amm_x = 3.2       # 电流表中心
        node_a_x = 3.8    # 并联节点A
        r1_x_left = 4.1   # R₁ 左侧
        r1_x_right = 5.1  # R₁ 右侧
        r2_x_left = 4.1   # R₂ 左侧
        r2_x_right = 5.1  # R₂ 右侧
        node_b_x = 5.4    # 并联节点B
        bulb_x = 6.0      # 灯泡中心

        # ═══════════════════════════════════════════════════════════════════
        # 创建电池（垂直放置）
        # ═══════════════════════════════════════════════════════════════════
        battery = create_battery(
            start=[bat_x, bat_bot_y, 0],
            end=[bat_x, bat_top_y, 0],
            voltage=r"9\,\text{V}",
        )

        # ═══════════════════════════════════════════════════════════════════
        # 创建电流表（串联在干路，测量总电流 I）
        # ═══════════════════════════════════════════════════════════════════
        ammeter = create_ammeter(
            center=[amm_x, main_y, 0],
            label="",
        )

        # ═══════════════════════════════════════════════════════════════════
        # 创建 R₁ 电阻（10Ω，上支路）
        # ═══════════════════════════════════════════════════════════════════
        resistor1 = create_resistor(
            start=[r1_x_left, upper_y, 0],
            end=[r1_x_right, upper_y, 0],
            label=r"R_1",
            resistance=r"10\,\Omega",
        )

        # ═══════════════════════════════════════════════════════════════════
        # 创建 R₂ 电阻（20Ω，下支路）
        # ═══════════════════════════════════════════════════════════════════
        resistor2 = create_resistor(
            start=[r2_x_left, lower_y, 0],
            end=[r2_x_right, lower_y, 0],
            label=r"R_2",
            resistance=r"20\,\Omega",
        )

        # ═══════════════════════════════════════════════════════════════════
        # 创建灯泡 L₁（串联在并联部分之后）
        # ═══════════════════════════════════════════════════════════════════
        bulb = create_bulb(
            center=[bulb_x, main_y, 0],
            label=r"L_1",
        )

        # ═══════════════════════════════════════════════════════════════════
        # 创建电压表（并联在 R₁ 两端）
        # ═══════════════════════════════════════════════════════════════════
        voltmeter = create_voltmeter(
            center=[(r1_x_left + r1_x_right) / 2, upper_y + 0.8, 0],
            label="",
        )

        # ═══════════════════════════════════════════════════════════════════
        # 创建导线（遵循"横平竖直"规范）
        # ═══════════════════════════════════════════════════════════════════
        wires = []

        # 电池正极 → 垂直向上到主回路线
        wires.append(create_wire([bat_x, bat_top_y, 0], [bat_x, main_y, 0]))

        # 主回路线：电池 → 电流表 → 并联节点A
        wires.append(create_wire([bat_x, main_y, 0], [amm_x - 0.25, main_y, 0]))  # 电池 → 电流表
        wires.append(create_wire([amm_x + 0.25, main_y, 0], [node_a_x, main_y, 0]))  # 电流表 → 节点A

        # 并联节点A → R₁ 和 R₂（分支）
        # → R₁（上支路）
        wires.append(create_wire([node_a_x, main_y, 0], [node_a_x, upper_y, 0]))  # 垂直向上
        wires.append(create_wire([node_a_x, upper_y, 0], [r1_x_left, upper_y, 0]))  # 水平到R₁

        # → R₂（下支路）
        wires.append(create_wire([node_a_x, main_y, 0], [node_a_x, lower_y, 0]))  # 垂直向下
        wires.append(create_wire([node_a_x, lower_y, 0], [r2_x_left, lower_y, 0]))  # 水平到R₂

        # R₁ → 并联节点B（右侧汇合）
        wires.append(create_wire([r1_x_right, upper_y, 0], [node_b_x, upper_y, 0]))

        # R₂ → 并联节点B（右侧汇合）
        wires.append(create_wire([r2_x_right, lower_y, 0], [node_b_x, lower_y, 0]))

        # 并联节点B → 灯泡 → 回到电池
        wires.append(create_wire([node_b_x, upper_y, 0], [node_b_x, main_y, 0]))  # 上端垂直向下
        wires.append(create_wire([node_b_x, lower_y, 0], [node_b_x, main_y, 0]))  # 下端垂直向上
        wires.append(create_wire([bulb_x - 0.35, main_y, 0], [bulb_x + 0.35, main_y, 0]))  # 灯泡内部
        wires.append(create_wire([bulb_x + 0.35, main_y, 0], [bat_x, main_y, 0]))  # 灯泡 → 电池
        wires.append(create_wire([bat_x, main_y, 0], [bat_x, bat_bot_y, 0]))  # 电池负极垂直向下

        # ═══════════════════════════════════════════════════════════════════
        # 创建节点圆点（T型连接标记）
        # ═══════════════════════════════════════════════════════════════════
        junctions = []

        # 并联节点A（分支点）
        junctions.append(create_junction_dot([node_a_x, main_y, 0]))

        # R₁ 左侧节点
        junctions.append(create_junction_dot([r1_x_left, upper_y, 0]))

        # R₁ 右侧节点
        junctions.append(create_junction_dot([r1_x_right, upper_y, 0]))

        # R₂ 左侧节点
        junctions.append(create_junction_dot([r2_x_left, lower_y, 0]))

        # R₂ 右侧节点
        junctions.append(create_junction_dot([r2_x_right, lower_y, 0]))

        # 并联节点B（汇合点）
        junctions.append(create_junction_dot([node_b_x, upper_y, 0]))
        junctions.append(create_junction_dot([node_b_x, lower_y, 0]))

        # ═══════════════════════════════════════════════════════════════════
        # 创建电流标注箭头
        # ═══════════════════════════════════════════════════════════════════
        current_arrows = []

        # 总电流 I（干路）
        current_arrows.append(create_current_arrow(
            [amm_x - 0.4, main_y + 0.15, 0],
            [amm_x + 0.1, main_y + 0.15, 0],
            label=r"I",
        ))

        # R₁ 电流 I₁
        current_arrows.append(create_current_arrow(
            [r1_x_left + 0.2, upper_y - 0.2, 0],
            [r1_x_right - 0.2, upper_y - 0.2, 0],
            label=r"I_1",
        ))

        # R₂ 电流 I₂
        current_arrows.append(create_current_arrow(
            [r2_x_left + 0.2, lower_y - 0.2, 0],
            [r2_x_right - 0.2, lower_y - 0.2, 0],
            label=r"I_2",
        ))

        # ═══════════════════════════════════════════════════════════════════
        # 合并所有元件
        # ═══════════════════════════════════════════════════════════════════
        circuit = VGroup(
            battery,
            ammeter,
            resistor1,
            resistor2,
            bulb,
            voltmeter,
            *wires,
            *junctions,
            *current_arrows,
        )

        # 电路拓扑验证
        is_valid, errors = validate_circuit_topology(circuit)
        if is_valid:
            print(f"[ThreeColumnTest] 电路拓扑验证通过")
        else:
            print(f"[ThreeColumnTest] 电路拓扑警告: {errors}")

        return circuit


if __name__ == "__main__":
    config.quality = "low_quality"
    config.format = "mp4"

    if "--disable_caching" not in sys.argv:
        sys.argv.append("--disable_caching")

    scene = ThreeColumnTestScene(skip_env_check=True, debug=True)
    scene.render()
