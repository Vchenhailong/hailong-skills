#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕区容器 - 固定宽高 14.0 x 0.65 单位

严格约束：
- X ∈ [-7.0, 7.0]
- Y ∈ [-3.95, -3.3]（底部固定，防抖动）
- 上界 Y=-2.8（防止侵入主内容区）
- 最多 2 行字幕，超出自动垂直滚动
- 字幕字号默认 18（不超过18）
- 字幕底衬+左侧强调条（借鉴 mathVideoMaker）
- 底部固定位置（防止多行字幕抖动）
"""

from manim import VGroup, UP
from scripts.layout.zones.base import ZoneBase
from scripts.layout.constants import ZoneConstants as ZC


class SubtitleZone(ZoneBase):
    """字幕区固定宽高容器组件
    
    职责：
    1. 提供固定宽高的物理边界（14.0 x 0.65 单位）
    2. 底部对齐（防止多行字幕抖动）
    3. 强制执行上界约束（防止侵入主内容区）
    4. 字幕内容安全区域内布局
    """
    
    def __init__(self, debug: bool = False, **kwargs):
        """初始化字幕区容器
        
        Args:
            debug: 调试模式，显示容器边框和填充
            **kwargs: 传递给 ZoneBase 的样式参数
        """
        super().__init__(
            x_min=ZC.SUBTITLE_ZONE_X_MIN,
            x_max=ZC.SUBTITLE_ZONE_X_MAX,
            y_min=ZC.SUBTITLE_ZONE_Y_MIN,
            y_max=ZC.SUBTITLE_ZONE_Y_MAX,
            debug=debug,
            **kwargs,
        )
    
    def place_content(self, content_group: VGroup) -> VGroup:
        """将字幕内容约束在容器内，底部对齐
        
        约束策略：
        1. 内容高度超过容器时按比例缩放
        2. 底部对齐（防抖动）
        3. 强制执行上界约束（防止侵入主内容区 Y=-2.5）
        
        Args:
            content_group: 字幕内容组（Text 或 VGroup）
            
        Returns:
            已定位的内容组
        """
        content_height = content_group.get_height()
        
        # 1. 内容高度超过容器时按比例缩放（使用底部作为缩放锚点）
        if content_height > self._height:
            scale_factor = self._height / content_height
            content_group.scale(scale_factor, about_point=content_group.get_bottom())
        
        # 2. 底部对齐（固定字幕底部位置，防抖动）
        current_bottom = content_group.get_bottom()[1]
        if abs(current_bottom - ZC.SUBTITLE_ZONE_BOTTOM_FIXED_Y) > 0.001:
            content_group.shift(UP * (ZC.SUBTITLE_ZONE_BOTTOM_FIXED_Y - current_bottom))
        
        # 3. 强制执行上界约束（防止侵入主内容区）
        top_y = content_group.get_top()[1]
        if top_y > ZC.SUBTITLE_ZONE_TOP_Y:
            content_group.shift(UP * (ZC.SUBTITLE_ZONE_TOP_Y - top_y))
        
        # 水平居中
        content_group.move_to([self._center_x, content_group.get_center()[1], 0])
        
        self._content_group = content_group
        return content_group
    
    def place_content_bottom_aligned(self, content_group: VGroup) -> VGroup:
        """将字幕内容底部对齐到固定位置（明确指定底部对齐）
        
        Args:
            content_group: 字幕内容组
            
        Returns:
            已定位的内容组
        """
        return self.place_content(content_group)
    
    def is_content_overflow(self, content_group: VGroup) -> bool:
        """检查内容是否溢出容器
        
        检查项：
        1. 内容底部是否低于字幕区下界
        2. 内容顶部是否高于字幕区上界
        """
        content_bottom = content_group.get_bottom()[1]
        content_top = content_group.get_top()[1]
        return (content_bottom < ZC.SUBTITLE_ZONE_Y_MIN or 
                content_top > ZC.SUBTITLE_ZONE_TOP_Y)
