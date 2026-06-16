#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CJK 组件自动安装器

按平台提供安装命令建议，**不直接执行**（除非显式传入 auto_install=True）。

设计原则：
1. 默认只返回 shell 命令建议，让用户人工执行（最安全）
2. 显式 auto_install=True 时，按平台执行安装命令（需要管理员权限）
3. 安装成功后写日志；失败时给出回退建议
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

from scripts.environment.cjk_checker import CJKReport


# 平台支持标记
AUTO_INSTALL_SUPPORTED = {"linux", "darwin"}  # Windows 上 auto_install 拒绝执行（请人工安装）


@dataclass
class InstallCommand:
    """一条安装命令"""

    platform: str  # 'linux' / 'darwin' / 'windows'
    package_manager: str  # 'apt' / 'brew' / 'choco' / 'miktex' ...
    command: str
    description: str
    requires_admin: bool = True


# 已知场景的安装命令模板
_LINUX_APT_TEXLIVE = InstallCommand(
    platform="linux",
    package_manager="apt",
    command=(
        "sudo apt update && "
        "sudo apt install -y "
        "texlive-xetex texlive-lang-chinese texlive-fonts-recommended "
        "texlive-fonts-extra texlive-latex-extra "
        "fonts-noto-cjk fonts-noto-cjk-extra"
    ),
    description="Debian/Ubuntu 安装 xelatex + xeCJK + Noto CJK 字体",
    requires_admin=True,
)

_DARWIN_BREW_MACTEX = InstallCommand(
    platform="darwin",
    package_manager="brew",
    command=(
        "brew install --cask mactex && "
        "brew tap homebrew/cask-fonts && "
        "brew install --cask font-noto-sans-cjk-sc"
    ),
    description="macOS 安装 MacTeX + Noto CJK",
    requires_admin=False,
)

_WINDOWS_CHOCO = InstallCommand(
    platform="windows",
    package_manager="choco",
    command=(
        "choco install miktex -y && "
        "refreshenv"
    ),
    description="Windows 安装 MiKTeX（中文字体通常系统自带）",
    requires_admin=True,
)

# 仅字体安装（已装 TeX 但缺字体）
_LINUX_APT_FONTS_ONLY = InstallCommand(
    platform="linux",
    package_manager="apt",
    command="sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra",
    description="仅安装 Noto CJK 字体（xelatex 已存在的情况）",
    requires_admin=True,
)


# ============================================================
# 公开 API
# ============================================================


def install_suggested_commands(report: CJKReport) -> List[InstallCommand]:
    """根据 CJKReport 推荐安装命令（仅返回，不执行）

    Args:
        report: check() 返回的报告

    Returns:
        按优先级排序的安装命令列表（最优先的在前）
    """
    family = _platform_family()
    cmds: List[InstallCommand] = []

    needs_tex = not report.available_engines
    needs_fonts = not report.chinese_fonts
    needs_cjk_pkg = (
        report.recommended_engine in ("xelatex", "lualatex", "pdflatex")
        and not report.cjk_packages.get(report.recommended_engine, [])
    )

    if family == "linux":
        if needs_tex or needs_cjk_pkg:
            cmds.append(_LINUX_APT_TEXLIVE)
        if needs_fonts and not needs_tex:
            cmds.append(_LINUX_APT_FONTS_ONLY)
    elif family == "darwin":
        if needs_tex or needs_cjk_pkg:
            cmds.append(_DARWIN_BREW_MACTEX)
    elif family == "windows":
        if needs_tex or needs_cjk_pkg:
            cmds.append(_WINDOWS_CHOCO)
    # 其它平台：返回空列表，让用户自行判断

    return cmds


def install_missing(
    report: CJKReport,
    auto_install: bool = False,
    dry_run: bool = True,
) -> Dict:
    """尝试安装缺失组件

    Args:
        report: CJKReport
        auto_install: True 时**实际执行**安装命令（需管理员权限）
        dry_run: True 时只返回将要执行的命令，不执行

    Returns:
        字典 { "commands": [...], "executed": [...], "skipped": [...] }

    Security:
        auto_install=False 是默认行为，强制要求用户人工确认。
        auto_install=True 在 Windows 上直接拒绝执行。
    """
    family = _platform_family()
    cmds = install_suggested_commands(report)
    result = {"commands": cmds, "executed": [], "skipped": []}

    if not cmds:
        return result

    if dry_run:
        return result  # 仅返回命令

    if not auto_install:
        result["skipped"] = cmds
        return result

    if family not in AUTO_INSTALL_SUPPORTED:
        result["skipped"] = cmds
        return result

    for cmd in cmds:
        if cmd.requires_admin and shutil.which("sudo") is None and family == "linux":
            # 没有 sudo，跳过
            result["skipped"].append(cmd)
            continue
        try:
            # 用 shell 执行（命令本身可能含 && 链）
            shell_cmd = cmd.command
            out = subprocess.run(
                shell_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,  # 10 分钟上限
            )
            if out.returncode == 0:
                result["executed"].append(cmd)
            else:
                result["skipped"].append(cmd)
        except (subprocess.TimeoutExpired, OSError):
            result["skipped"].append(cmd)

    return result


# ============================================================
# 工具
# ============================================================


def _platform_family() -> str:
    s = platform.system().lower()
    if s.startswith("win"):
        return "windows"
    if s.startswith("darwin"):
        return "darwin"
    if s.startswith("linux"):
        return "linux"
    return s


def print_suggested(report: CJKReport) -> None:
    """把安装建议打到 stdout"""
    cmds = install_suggested_commands(report)
    if not cmds:
        print("✓ 你的环境已满足 CJK 渲染要求，无需安装")
        return
    print("-" * 60)
    print("建议安装命令（按平台）：")
    for c in cmds:
        admin = "需要管理员" if c.requires_admin else "无需管理员"
        print(f"\n[{c.platform} / {c.package_manager}] {c.description} ({admin})")
        print(f"  $ {c.command}")
    print("-" * 60)
    print("提示：Windows 推荐人工安装 MiKTeX；Linux/macOS 可复制命令执行。")


if __name__ == "__main__":
    from scripts.environment.cjk_checker import check

    r = check(verbose=True)
    print_suggested(r)
