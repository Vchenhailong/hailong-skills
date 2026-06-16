#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
布局决策引擎 - 严格遵循 references/layout.md 第 11.2 节决策流程

职责：
- 根据内容数量、是否有图形，自动决策单栏/两栏/三栏
- 预估内容宽高，触发溢出处理
- 返回布局模式和对应的区域配置

决策树（layout.md 第 11.2 节）：
1. 计算垂直总高度 (V_H)。如果 V_H < 5.5 单位，使用垂直排列
2. 如果垂直溢出（V_H > 5.5），计算水平总宽度 (H_W)
   - 如果 H_W < 13.5 单位，切换为水平排列
   - 如果 H_W >= 13.5 单位，触发强制拆分：将内容数组均分为左右两组，创建两个垂直排列的 VGroup，将这两个 VGroup 进行水平并排（arrange(RIGHT)），形成两栏布局
3. 如果以上均失败，必须在 JSON 设计阶段将该原子拆分为多个独立原子
"""

from enum import Enum
from typing import Optional, Tuple, Dict, Any
from manim import Mobject, VGroup, DOWN, RIGHT, UP, LEFT, ORIGIN
from scripts.layout.constants import ZoneConstants


class LayoutMode(Enum):
    """布局模式枚举"""

    VERTICAL = "vertical"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    CENTERED = "centered"


class LayoutDecision:
    """布局决策结果

    Attributes:
        mode: 布局模式
        should_scale: 是否需要缩放
        scale_factor: 缩放系数
        error_message: 错误信息（无法安全布局时）
    """

    def __init__(
        self,
        mode: LayoutMode = LayoutMode.VERTICAL,
        should_scale: bool = False,
        scale_factor: float = 1.0,
        error_message: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.mode = mode
        self.should_scale = should_scale
        self.scale_factor = scale_factor
        self.error_message = error_message
        self.extra = extra or {}

    @property
    def is_safe(self) -> bool:
        """判断当前决策是否安全"""
        return self.error_message is None


class LayoutEngine:
    """布局决策引擎

    根据内容特征自动选择最优布局模式
    """

    @staticmethod
    def measure_content_dims(
        mobjs: list,
        buff: float = ZoneConstants.ROW_BUFF,
    ) -> Tuple[float, float]:
        """实时测量内容对象的实际宽高

        使用 VGroup.arrange(DOWN, buff=buff) 模拟真实堆叠后再测量，
        替代纯包围盒的测量方式，确保布局决策基于真实堆叠尺寸。
        符合 SKILL.md M2：仅用 VGroup.arrange() 布局。

        Args:
            mobjs: 要测量的 Mobject 列表
            buff: 元素间垂直间距（默认 ZoneConstants.ROW_BUFF）

        Returns:
            (total_width, total_height): 内容的总宽度和总高度
            - 对于垂直排列：total_height = Σ 各元素高度 + (n-1) × buff
            - 对于水平排列：total_width = Σ 各元素宽度 + (n-1) × buff
            - 实际返回的是 arrange 后 VGroup 的 width/height

        示例::

            # 创建内容
            texts = [Text(f"Line {i}") for i in range(3)]
            width, height = LayoutEngine.measure_content_dims(texts)
            print(f"内容宽 {width:.2f}, 高 {height:.2f}")
        """
        if not mobjs:
            return 0.0, 0.0

        # 必须先 arrange 才返回真实堆叠尺寸（修复 P0-1）
        temp_group = VGroup(*mobjs).arrange(DOWN, buff=buff, aligned_edge=LEFT)
        return temp_group.width, temp_group.height

    @staticmethod
    def decide(
        content_count: int,
        has_graphics: bool,
        has_multirow_formulas: bool,
        has_steps: bool = False,
        estimated_height: float = 0.0,
        estimated_width: float = 0.0,
    ) -> LayoutDecision:
        """执行布局决策（layout.md 第 11.2 节决策流程）

        Args:
            content_count: 内容元素数量
            has_graphics: 是否有图形内容
            has_multirow_formulas: 是否有多行公式
            has_steps: 是否有步骤说明（三栏触发条件）
            estimated_height: 预估垂直总高度
            estimated_width: 预估水平总宽度

        Returns:
            LayoutDecision 布局决策结果
        """
        # 原子类型推荐布局（layout.md 第 10 节）
        # definition/intuition: 有图则两栏，无图则单栏
        # operation: 两栏（左步骤，右图形）
        # counter_intuitive: 两栏（左错误，右正确）
        # application: 两栏（左描述，右效果）
        # summary: 三栏（左概念，中公式，右应用）

        if has_steps and has_graphics and has_multirow_formulas:
            return LayoutDecision(mode=LayoutMode.THREE_COLUMN)

        if content_count >= 8:
            if has_multirow_formulas:
                return LayoutDecision(mode=LayoutMode.THREE_COLUMN)
            return LayoutDecision(mode=LayoutMode.TWO_COLUMN)

        if has_graphics:
            return LayoutDecision(mode=LayoutMode.TWO_COLUMN)

        if content_count >= 5:
            return LayoutDecision(mode=LayoutMode.TWO_COLUMN)

        if estimated_height > ZoneConstants.VERTICAL_OVERFLOW_THRESHOLD:
            if estimated_width < ZoneConstants.HORIZONTAL_OVERFLOW_THRESHOLD:
                return LayoutDecision(
                    mode=LayoutMode.TWO_COLUMN,
                    should_scale=True,
                    scale_factor=ZoneConstants.VERTICAL_OVERFLOW_THRESHOLD
                    / estimated_height,
                )
            else:
                return LayoutDecision(
                    mode=LayoutMode.TWO_COLUMN,
                    should_scale=True,
                    scale_factor=0.8,
                    error_message=(
                        f"内容预估高度 {estimated_height:.1f} 单位 > {ZoneConstants.VERTICAL_OVERFLOW_THRESHOLD} 单位，"
                        f"宽度 {estimated_width:.1f} 单位 > {ZoneConstants.HORIZONTAL_OVERFLOW_THRESHOLD} 单位。"
                        f"建议: 将该原子拆分为更细粒度的原子"
                    ),
                )

        return LayoutDecision(mode=LayoutMode.VERTICAL)

    @staticmethod
    def arrange_content(
        mobjs: list,
        mode: LayoutMode,
        buff: float = ZoneConstants.ROW_BUFF,
    ) -> VGroup:
        """根据布局模式排列内容

        Args:
            mobjs: 内容对象列表
            mode: 布局模式
            buff: 行间距

        Returns:
            已排列的 VGroup
        """
        if not mobjs:
            return VGroup()

        group = VGroup(*mobjs)

        if mode == LayoutMode.VERTICAL:
            group.arrange(DOWN, buff=buff, aligned_edge=LEFT)

        elif mode == LayoutMode.TWO_COLUMN:
            mid = len(mobjs) // 2
            left_objs = mobjs[:mid]
            right_objs = mobjs[mid:]

            left_col = VGroup(*left_objs).arrange(DOWN, buff=buff, aligned_edge=LEFT)
            if right_objs:
                right_col = VGroup(*right_objs).arrange(
                    DOWN, buff=buff, aligned_edge=LEFT
                )
                group = VGroup(left_col, right_col).arrange(
                    RIGHT, buff=ZoneConstants.ELEMENT_BUFF
                )
            else:
                group = left_col

        elif mode == LayoutMode.THREE_COLUMN:
            third = max(1, len(mobjs) // 3)
            left_objs = mobjs[:third]
            mid_objs = mobjs[third : third * 2]
            right_objs = mobjs[third * 2 :]

            left_col = VGroup(*left_objs).arrange(
                DOWN, buff=buff * 0.8, aligned_edge=LEFT
            )
            mid_col = (
                VGroup(*mid_objs).arrange(DOWN, buff=buff, aligned_edge=LEFT)
                if mid_objs
                else VGroup()
            )
            right_col = (
                VGroup(*right_objs).arrange(DOWN, buff=buff * 0.8, aligned_edge=LEFT)
                if right_objs
                else VGroup()
            )

            cols = [c for c in [left_col, mid_col, right_col] if len(c) > 0]
            if cols:
                group = VGroup(*cols).arrange(RIGHT, buff=ZoneConstants.ELEMENT_BUFF)
            else:
                group = left_col

        elif mode == LayoutMode.CENTERED:
            group.arrange(DOWN, buff=buff, aligned_edge=LEFT)
            group.move_to(ORIGIN)  # 整体垂直居中

        return group
