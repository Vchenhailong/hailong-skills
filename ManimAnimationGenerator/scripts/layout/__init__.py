#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排版布局引擎 - 严格遵循 references/layout.md 规范

模块职责：
- constants: 区域常量定义
- zones: 区域容器组件（字幕区、主内容区、图形区）
- engine: 布局决策引擎（单栏/两栏/三栏自动切换）
- scene_base: LayoutScene 场景基类
"""

from scripts.layout.constants import ZoneConstants
from scripts.layout.zones.subtitle_zone import SubtitleZone
from scripts.layout.zones.main_content_zone import MainContentZone
from scripts.layout.zones.graphics_zone import GraphicsZone
from scripts.layout.engine import LayoutEngine
from scripts.layout.scene_base import LayoutScene

__all__ = [
    "ZoneConstants",
    "SubtitleZone",
    "MainContentZone",
    "GraphicsZone",
    "LayoutEngine",
    "LayoutScene",
]
