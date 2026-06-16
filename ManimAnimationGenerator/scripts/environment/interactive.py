#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境自检的交互层：当自动检测失败时，通过 stdin 询问用户

设计原则：
1. 默认不交互（保护 CI / 批处理）
2. 仅当 LayoutScene(interactive_env_check=True) 时启用
3. 必须检测 stdin.isatty()：非交互终端（pipe / 重定向）下自动降级到非交互
4. 所有 prompt 都提供 timeout（避免用户走了后被卡住）
"""

from __future__ import annotations

import os
import sys
import logging
import shutil
from pathlib import Path
from typing import List, Optional

from scripts.environment.cjk_checker import (
    _which_with_texlive_fallback,
    CJKReport,
    RenderPath,
)
from scripts.environment.cjk_installer import (
    install_suggested_commands,
    install_missing,
    print_suggested,
    AUTO_INSTALL_SUPPORTED,
)


_LOG = logging.getLogger("manim_skill")


# ============================================================
# 交互能力探测
# ============================================================


def is_interactive_available() -> bool:
    """当前 stdin 能否做交互询问

    Returns:
        True: 有真实 TTY（用户能直接输入）
        False: pipe / 重定向 / IDE 嵌入式终端（不能输入）
    """
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


# ============================================================
# 询问用户
# ============================================================


def _prompt_yes_no(question: str, default: bool = False, timeout: float = 30.0) -> Optional[bool]:
    """询问 y/n 问题

    Args:
        question: 提示语
        default: 用户直接回车时的默认选择
        timeout: 等待用户输入的最长秒数

    Returns:
        True / False / None（超时或不可交互时）
    """
    if not is_interactive_available():
        return None
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        # 用 select 模拟超时（Unix-only，Windows 下退化）
        if hasattr(sys.stdin, "fileno") and os.name == "posix":
            import select

            print(question + suffix, end=" ", flush=True)
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if not rlist:
                print("\n[timeout]")
                return None
            line = sys.stdin.readline().strip().lower()
        else:
            print(question + suffix, end=" ", flush=True)
            line = sys.stdin.readline().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n[interrupted]")
        return None
    except Exception as e:
        _LOG.warning(f"[interactive] prompt 异常: {e}")
        return None

    if not line:
        return default
    if line in ("y", "yes", "是", "好"):
        return True
    if line in ("n", "no", "否", "不"):
        return False
    # 其它输入：递归再问一次（最多 1 次）
    print(f"  无效输入 '{line}'，请输入 y 或 n")
    return _prompt_yes_no(question, default, timeout=5.0)


def _prompt_path(question: str, must_exist: bool = True) -> Optional[Path]:
    """询问用户输入路径

    Args:
        question: 提示语
        must_exist: 是否必须存在

    Returns:
        用户输入的 Path 或 None（不可交互/取消/无效）
    """
    if not is_interactive_available():
        return None
    try:
        print(question, end=" ", flush=True)
        line = sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        print("\n[interrupted]")
        return None
    except Exception as e:
        _LOG.warning(f"[interactive] prompt 异常: {e}")
        return None

    if not line:
        return None

    p = Path(line).expanduser()
    if must_exist and not p.exists():
        print(f"  路径 '{p}' 不存在，请重新运行")
        return None
    return p


# ============================================================
# 主流程
# ============================================================


def interactive_env_setup(report: CJKReport) -> CJKReport:
    """在自动检测失败后，给用户一次机会手动指定 / 确认安装

    工作流：
    1. 打印当前检测结果 + 建议安装命令
    2. 询问：是否手动指定 TeX Live / kpsewhich 路径？
    3. 如果用户提供了路径 → 验证 → 重新探测
    4. 如果用户不指定 → 询问：是否自动安装？
    5. 如果用户确认安装 → 调 install_missing(auto_install=True)
    6. 安装后重新探测
    7. 返回最新的 CJKReport

    Args:
        report: check() 的初始结果

    Returns:
        更新后的 CJKReport（如果用户走了所有步骤但仍未解决，
        返回值与入参可能相同，仍是 text_pango_only）
    """
    if not is_interactive_available():
        _LOG.info(
            "[interactive] 非交互终端（stdin/stdout 不是 TTY），跳过询问"
        )
        _LOG.info("[interactive] 如需自动检测，请安装 TeX Live + xeCJK + 中文字体")
        return report

    _LOG.info("=" * 60)
    _LOG.info("CJK 环境自检未通过，进入交互模式")
    _LOG.info("=" * 60)
    report.print_human()
    print_suggested(report)

    # ---- 步骤 1：询问是否手动指定路径 ----
    print()
    ans = _prompt_yes_no(
        "是否手动指定 TeX Live / kpsewhich 路径？", default=False
    )
    if ans is True:
        user_path = _prompt_path(
            "请输入 TeX Live 安装根目录（如 E:\\texlive\\2026）：",
            must_exist=True,
        )
        if user_path is not None:
            # 把用户路径导出到环境变量，再让 _which_with_texlive_fallback 找到
            os.environ["TEXLIVE_ROOT"] = str(user_path)
            _LOG.info(f"[interactive] 已设置 TEXLIVE_ROOT={user_path}")
            # 重新跑检测
            from scripts.environment.cjk_checker import check as recheck

            new_report = recheck(verbose=False)
            if new_report.ok and new_report.render_path != RenderPath.TEXT_PANGO_ONLY:
                _LOG.info("[interactive] ✓ 重新检测通过！")
                return new_report
            else:
                _LOG.warning("[interactive] 指定路径后仍未通过，继续询问安装")

    # ---- 步骤 2：询问是否自动安装 ----
    print()
    family = sys.platform
    if family.startswith("win"):
        print("Windows 上不自动执行安装（需管理员权限 + 人工确认）")
        print_suggested(report)
        return report

    if family not in AUTO_INSTALL_SUPPORTED:
        _LOG.info(f"[interactive] 平台 {family} 不在自动安装支持列表")
        return report

    ans = _prompt_yes_no(
        f"是否自动执行安装命令（需要 {'sudo' if family == 'linux' else '管理员'}）？",
        default=False,
    )
    if ans is True:
        _LOG.info("[interactive] 开始执行安装...")
        result = install_missing(report, auto_install=True, dry_run=False)
        if result["executed"]:
            _LOG.info("[interactive] ✓ 安装成功，重新检测...")
            from scripts.environment.cjk_checker import check as recheck

            return recheck(verbose=False)
        else:
            _LOG.warning("[interactive] 安装失败或被跳过")
            for cmd in result["skipped"]:
                _LOG.warning(f"  跳过: {cmd.command}")
    else:
        _LOG.info("[interactive] 已跳过自动安装，请人工执行上述命令")

    return report


def run_setup(interactive: bool = False, force_refresh: bool = False) -> CJKReport:
    """场景 setup 阶段调用的主入口

    Args:
        interactive: 是否在检测失败后弹交互询问
        force_refresh: 强制重新探测（跳过缓存）

    Returns:
        CJKReport（含最终 render_path 推荐）
    """
    from scripts.environment.cjk_checker import check_cached, check

    if force_refresh:
        report = check(verbose=False)
    else:
        report = check_cached(verbose=False)

    # 自动检测通过 → 直接返回
    if report.ok and report.render_path != RenderPath.TEXT_PANGO_ONLY:
        return report

    # 自动检测失败 + 交互模式开启 → 询问用户
    if interactive:
        return interactive_env_setup(report)

    # 自动检测失败 + 非交互 → 打 warning 返回原 report
    _LOG.warning(
        f"[env] 渲染路径回退到 {report.render_path}，"
        f"建议安装缺失组件（见 install_suggested_commands）"
    )
    return report


if __name__ == "__main__":
    # 直接运行时：默认非交互（方便 CI / 调试）；加 --interactive 切到交互模式
    interactive = "--interactive" in sys.argv
    r = run_setup(interactive=interactive, force_refresh=True)
    print("=" * 60)
    print(f"Final render_path: {r.render_path}")
    print(f"Final chinese_fonts: {r.chinese_fonts}")
