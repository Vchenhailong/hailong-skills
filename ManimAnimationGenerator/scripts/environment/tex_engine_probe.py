#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX 引擎可用性探测

返回各引擎（pdflatex / xelatex / lualatex）的可执行文件路径、
版本号以及基础能力报告（是否能处理 CJK）。

不修改任何系统状态，只做只读探测。
"""

from __future__ import annotations

import shutil
import subprocess
import platform
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


@dataclass
class TexEngineReport:
    """单 LaTeX 引擎的探测结果"""

    engine: str  # 'pdflatex' / 'xelatex' / 'lualatex'
    available: bool = False
    path: Optional[str] = None
    version: str = ""
    cjk_capable: bool = False  # 引擎层支持 CJK（xelatex 默认可，pdflatex 需宏包）
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TexProbeResult:
    """完整探测结果"""

    engines: List[TexEngineReport] = field(default_factory=list)
    os_name: str = ""
    python_version: str = ""
    manim_version: str = ""
    recommendation: str = ""  # 推荐的引擎名
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return {
            "engines": [e.to_dict() for e in self.engines],
            "os_name": self.os_name,
            "python_version": self.python_version,
            "manim_version": self.manim_version,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


def _run_version(engine_path: str) -> str:
    """运行 <engine> --version 拿到首行版本号（失败返回空串）"""
    try:
        # encoding="utf-8" + errors="ignore" 解决 Windows 进程 stdout 非 UTF-8 的问题
        out = subprocess.run(
            [engine_path, "--version"],
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,  # Windows 杀软扫描时易超时
        )
        first_line = (
            (out.stdout or out.stderr).splitlines()[0]
            if (out.stdout or out.stderr)
            else ""
        )
        return first_line.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _probe_single(engine: str) -> TexEngineReport:
    """探测单个引擎"""
    report = TexEngineReport(engine=engine)
    # 使用与 cjk_checker 一致的 TeX Live 兜底路径探测（Windows 上 TeX Live 默认不在 PATH）
    # 延迟导入避免循环引用
    from scripts.environment.cjk_checker import _which_with_texlive_fallback

    path = _which_with_texlive_fallback(engine)
    if not path:
        report.available = False
        report.notes = f"{engine} 不在 PATH 中，也未在常见 TeX Live 安装目录中找到"
        return report

    report.available = True
    report.path = path
    report.version = _run_version(path)

    # 引擎层 CJK 支持能力
    # xelatex / lualatex：原生支持 Unicode + 字体配置，CJK 默认可用
    # pdflatex：CJK 需要 CJKutf8 / ctex / xeCJK 等宏包配合
    if engine in ("xelatex", "lualatex"):
        report.cjk_capable = True
    else:
        report.cjk_capable = False
        report.notes = "pdflatex 处理 CJK 需 CJKutf8 / ctex 等宏包"
    return report


def probe_tex_engines() -> TexProbeResult:
    """探测所有 LaTeX 引擎，返回综合报告

    Returns:
        TexProbeResult：含每个引擎的可用性、版本、推荐引擎

    Example:
        >>> result = probe_tex_engines()
        >>> result.recommendation
        'xelatex'
        >>> for e in result.engines:
        ...     print(e.engine, e.available, e.cjk_capable)
    """
    import sys
    import datetime

    result = TexProbeResult(
        os_name=platform.platform(),
        python_version=sys.version.split()[0],
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )

    # Manim 版本（可选）
    try:
        import manim  # type: ignore

        result.manim_version = getattr(manim, "__version__", "unknown")
    except ImportError:
        result.manim_version = "not installed"

    # 各引擎探测
    for engine in ("pdflatex", "xelatex", "lualatex"):
        result.engines.append(_probe_single(engine))

    # 推荐引擎：有 xelatex 优先；只有 pdflatex 也行但需 CJK 宏包
    available = [e for e in result.engines if e.available]
    xelatex = next((e for e in available if e.engine == "xelatex"), None)
    lualatex = next((e for e in available if e.engine == "lualatex"), None)
    pdflatex = next((e for e in available if e.engine == "pdflatex"), None)

    if xelatex:
        result.recommendation = "xelatex"
    elif lualatex:
        result.recommendation = "lualatex"
    elif pdflatex:
        result.recommendation = "pdflatex"
    else:
        result.recommendation = ""

    return result


def print_report(result: TexProbeResult) -> None:
    """把探测结果以人类可读形式打印"""
    print("=" * 60)
    print(f"OS          : {result.os_name}")
    print(f"Python      : {result.python_version}")
    print(f"Manim       : {result.manim_version}")
    print(f"推荐引擎    : {result.recommendation or '(无可用引擎)'}")
    print("-" * 60)
    for e in result.engines:
        status = "OK" if e.available else "MISSING"
        cjk = "CJK✓" if e.cjk_capable else "CJK✗"
        ver = e.version[:50] if e.version else "-"
        print(f"  [{status:>7}] {e.engine:<10} {cjk}  {ver}")
        if e.notes:
            print(f"             备注: {e.notes}")
    print("=" * 60)


if __name__ == "__main__":
    r = probe_tex_engines()
    print_report(r)
