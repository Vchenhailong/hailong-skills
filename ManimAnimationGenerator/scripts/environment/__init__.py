#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境自检与 CJK 字体 / LaTeX 引擎 / 包依赖管理模块

提供：
- tex_engine_probe：探测 pdflatex / xelatex / lualatex 可用性
- cjk_checker：综合自检（CJK 字体、宏包、引擎），输出渲染路径推荐
- cjk_installer：缺失组件自动安装（按平台分发命令）
- interactive：自动检测失败后的交互询问层（stdin 输入路径 / 确认安装）

设计原则：
- 检测只在第一次渲染时执行，结果缓存到 env_state.json
- 检测失败不阻塞渲染，仅写 warning 并 fallback 到默认路径
- 安装操作要求用户显式确认（auto_install=True 才会执行）
- 交互询问仅在 interactive_env_check=True 且 stdin 是 TTY 时启用
"""

from scripts.environment.tex_engine_probe import probe_tex_engines, TexEngineReport
from scripts.environment.cjk_checker import (
    check,
    check_cached,
    CJKReport,
    RenderPath,
    _save_cache,
    _load_cache,
)
from scripts.environment.cjk_installer import (
    install_missing,
    install_suggested_commands,
    print_suggested,
    AUTO_INSTALL_SUPPORTED,
)
from scripts.environment.interactive import (
    is_interactive_available,
    interactive_env_setup,
    run_setup,
)

__all__ = [
    "probe_tex_engines",
    "TexEngineReport",
    "check",
    "check_cached",
    "CJKReport",
    "RenderPath",
    "install_missing",
    "install_suggested_commands",
    "print_suggested",
    "AUTO_INSTALL_SUPPORTED",
    "is_interactive_available",
    "interactive_env_setup",
    "run_setup",
]
