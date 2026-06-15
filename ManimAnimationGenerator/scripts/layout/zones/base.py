#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域容器基类 - 定义所有区域容器的通用接口

设计原则：
- 每个区域容器提供固定宽高的物理边界
- 子类实现具体的边界约束、定位、溢出处理逻辑
- 支持调试模式可视化容器范围
"""

from manim import Rectangle, VGroup, Mobject
from typing import Optional
from scripts.layout.constants import ZoneConstants


class ZoneBase(VGroup):
    """区域容器抽象基类
    
    职责：
    1. 提供固定宽高的物理边界
    2. 约束内容在安全区域内，防止越界
    3. 支持调试模式可视化容器范围
    """

    def __init__(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        debug: bool = False,
        container_stroke_color: str = "#444444",
        container_stroke_width: float = 1.0,
        container_stroke_opacity: float = 0.3,
        container_fill_color: str = "#000000",
        container_fill_opacity: float = 0.05,
    ):
        """初始化区域容器
        
        Args:
            x_min: 区域左边界 X 坐标
            x_max: 区域右边界 X 坐标
            y_min: 区域下边界 Y 坐标
            y_max: 区域上边界 Y 坐标
            debug: 调试模式，显示容器边框和填充
            container_stroke_color: 容器边框颜色
            container_stroke_width: 容器边框宽度
            container_stroke_opacity: 容器边框透明度
            container_fill_color: 容器填充颜色
            container_fill_opacity: 容器填充透明度
        """
        super().__init__()
        
        self._x_min = x_min
        self._x_max = x_max
        self._y_min = y_min
        self._y_max = y_max
        self._debug = debug
        
        self._width = x_max - x_min
        self._height = y_max - y_min
        self._center_x = (x_min + x_max) / 2
        self._center_y = (y_min + y_max) / 2
        
        self._container = Rectangle(
            width=self._width,
            height=self._height,
            stroke_color=container_stroke_color,
            stroke_width=container_stroke_width,
            stroke_opacity=container_stroke_opacity if debug else 0.0,
            fill_color=container_fill_color,
            fill_opacity=container_fill_opacity if debug else 0.0,
        )
        self._container.move_to([self._center_x, self._center_y, 0])
        self.add(self._container)
        
        self._content_group: Optional[VGroup] = None
    
    @property
    def container(self) -> Rectangle:
        """获取容器矩形对象"""
        return self._container
    
    @property
    def x_min(self) -> float:
        """左边界 X 坐标"""
        return self._x_min
    
    @property
    def x_max(self) -> float:
        """右边界 X 坐标"""
        return self._x_max
    
    @property
    def y_min(self) -> float:
        """下边界 Y 坐标"""
        return self._y_min
    
    @property
    def y_max(self) -> float:
        """上边界 Y 坐标"""
        return self._y_max
    
    @property
    def center_x(self) -> float:
        """中心 X 坐标"""
        return self._center_x
    
    @property
    def center_y(self) -> float:
        """中心 Y 坐标"""
        return self._center_y
    
    @property
    def width(self) -> float:
        """容器宽度"""
        return self._width
    
    @property
    def height(self) -> float:
        """容器高度"""
        return self._height
    
    def place_content(self, content_group: VGroup, h_align: str = "center") -> VGroup:
        """将内容约束在容器内（子类可重写定位逻辑）

        Args:
            content_group: 内容组
            h_align: 水平对齐方式，可选 "left" | "center" | "right"

        Returns:
            已定位的内容组
        """
        content_width = content_group.get_width()
        content_height = content_group.get_height()

        # 溢出检测与缩放：内容超出容器时按比例缩放
        scale_factor = 1.0
        if content_width > self._width:
            scale_factor = min(scale_factor, self._width / content_width)
        if content_height > self._height:
            scale_factor = min(scale_factor, self._height / content_height)

        if scale_factor < 1.0:
            content_group.scale(scale_factor, about_point=content_group.get_center())

        # 水平对齐：根据 h_align 参数决定
        if h_align == "left":
            content_group.move_to([self._x_min + content_width / 2, self._center_y, 0])
        elif h_align == "right":
            content_group.move_to([self._x_max - content_width / 2, self._center_y, 0])
        else:  # center
            content_group.move_to([self._center_x, self._center_y, 0])

        self._content_group = content_group
        return content_group
    
    def is_content_overflow(self, content_group: VGroup) -> bool:
        """检查内容是否溢出容器
        
        Args:
            content_group: 内容组
            
        Returns:
            True 表示内容超出容器边界
        """
        left = content_group.get_left()[0]
        right = content_group.get_right()[0]
        top = content_group.get_top()[1]
        bottom = content_group.get_bottom()[1]
        
        return (left < self._x_min or right > self._x_max or
                top > self._y_max or bottom < self._y_min)
    
    def clamp_to_zone(self, content_group: VGroup) -> VGroup:
        """将内容强制约束在容器范围内
        
        Args:
            content_group: 内容组
            
        Returns:
            已调整位置的内容组
        """
        left = content_group.get_left()[0]
        right = content_group.get_right()[0]
        top = content_group.get_top()[1]
        bottom = content_group.get_bottom()[1]
        
        shift_x = 0.0
        shift_y = 0.0
        
        if left < self._x_min:
            shift_x = self._x_min - left
        elif right > self._x_max:
            shift_x = self._x_max - right
        
        if top > self._y_max:
            shift_y = self._y_max - top
        elif bottom < self._y_min:
            shift_y = self._y_min - bottom
        
        if shift_x != 0.0 or shift_y != 0.0:
            from manim import RIGHT, UP
            content_group.shift(RIGHT * shift_x + UP * shift_y)
        
        return content_group
    
    def get_safe_left_x(self, margin: float = 0.1) -> float:
        """获取容器内安全的左边界 X 坐标"""
        return self._x_min + margin
    
    def get_safe_right_x(self, margin: float = 0.1) -> float:
        """获取容器内安全的右边界 X 坐标"""
        return self._x_max - margin
    
    def get_safe_top_y(self, margin: float = 0.1) -> float:
        """获取容器内安全的顶部 Y 坐标"""
        return self._y_max - margin
    
    def get_safe_bottom_y(self, margin: float = 0.1) -> float:
        """获取容器内安全的底部 Y 坐标"""
        return self._y_min + margin
    
    def center_y_only(self, content_group: VGroup) -> VGroup:
        """仅调整 Y 方向到容器中心，保持 X 位置不变
        
        用于滚动字幕等需要保持水平对齐但需垂直居中的场景。
        
        Args:
            content_group: 内容组
            
        Returns:
            已调整 Y 位置的内容组
        """
        current_center_y = content_group.get_center()[1]
        if abs(current_center_y - self._center_y) > 0.001:
            content_group.shift(UP * (self._center_y - current_center_y))
        return content_group
