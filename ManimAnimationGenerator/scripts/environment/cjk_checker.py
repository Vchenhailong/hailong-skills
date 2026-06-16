#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CJK 综合自检：LaTeX 引擎 + 宏包 + 中文字体

输出 CJKReport：
- engine：哪个 LaTeX 引擎可用
- engine_recommendation：渲染路径推荐
- cjk_packages：xeCJK / CJKutf8 / ctex / fontspec 哪些可用
- chinese_fonts：系统检测到的中文字体（微软雅黑 / 思源黑体 / Noto Sans CJK）
- render_path：建议走 Tex/minipage 还是 Text(Pango)
- warnings / errors：可读的问题清单

不修改任何系统状态。

子进程调用约定（重要，防止后人误改）：
- 探测类（kpsewhich / xelatex / --version 等）：使用 shell=False，传 list 形式参数
  - 原因：路径是绝对路径不需要 shell PATH 解析，无 metacharacter 风险，跨平台行为一致
- 安装类（cjk_installer.py 的 apt/brew 命令）：使用 shell=True，命令是字符串
  - 原因：命令含 `&&` 链（sudo apt update && sudo apt install ...）
- 禁止把 .bat / .cmd 文件用 shell=False 调用（Windows 上需走 cmd）
- 禁止用 shell=True 调长路径参数（引号转义易错）
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
import platform
import concurrent.futures
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from scripts.environment.tex_engine_probe import (
    probe_tex_engines,
    TexProbeResult,
    TexEngineReport,
)


# CJK 字体候选名（跨平台）
CJK_FONT_CANDIDATES = {
    "windows": [
        "Microsoft YaHei",
        "Microsoft YaHei UI",
        "SimHei",
        "SimSun",
        "KaiTi",
    ],
    "darwin": [
        "PingFang SC",
        "Heiti SC",
        "STHeiti",
        "Hiragino Sans GB",
        "Noto Sans CJK SC",
    ],
    "linux": [
        "Noto Sans CJK SC",
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "Source Han Sans SC",
        "AR PL UMing CN",
    ],
}

# LaTeX 宏包候选
CJK_PACKAGES = {
    "xelatex": ["xeCJK", "fontspec", "ctex", "CJKutf8"],
    "lualatex": ["luatexja", "fontspec"],
    "pdflatex": ["CJKutf8", "ctex", "inputenc"],
}


@dataclass
class CJKReport:
    """CJK 综合自检报告"""

    ok: bool = False  # 整体是否通过（能找到至少一种可行渲染路径）
    render_path: str = ""  # 'tex_minipage' | 'tex_standard' | 'text_pango_only'
    recommended_engine: str = ""
    available_engines: List[str] = field(default_factory=list)
    cjk_packages: Dict[str, List[str]] = field(default_factory=dict)  # engine -> [pkg]
    chinese_fonts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    probe: Optional[Dict] = None  # 完整 TexProbeResult 引用

    def to_dict(self) -> Dict:
        return {
            "ok": self.ok,
            "render_path": self.render_path,
            "recommended_engine": self.recommended_engine,
            "available_engines": self.available_engines,
            "cjk_packages": self.cjk_packages,
            "chinese_fonts": self.chinese_fonts,
            "warnings": self.warnings,
            "errors": self.errors,
            "notes": self.notes,
            "probe": self.probe,
        }

    def print_human(self) -> None:
        print("=" * 60)
        print("CJK 环境自检报告")
        print("=" * 60)
        status = "通过" if self.ok else "需要修复"
        print(f"总体       : {status}")
        print(f"渲染路径   : {self.render_path}")
        print(f"推荐引擎   : {self.recommended_engine or '(无)'}")
        if self.available_engines:
            print(f"可用引擎   : {', '.join(self.available_engines)}")
        if self.chinese_fonts:
            print(f"中文字体   : {', '.join(self.chinese_fonts)}")
        else:
            print("中文字体   : (未检测到)")

        if self.cjk_packages:
            print("-" * 60)
            print("CJK LaTeX 宏包：")
            for eng, pkgs in self.cjk_packages.items():
                print(f"  {eng}: {', '.join(pkgs) if pkgs else '(未检测)'}")

        if self.notes:
            print("-" * 60)
            print("提示：")
            for n in self.notes:
                print(f"  • {n}")

        if self.warnings:
            print("-" * 60)
            print("警告：")
            for w in self.warnings:
                print(f"  ⚠ {w}")

        if self.errors:
            print("-" * 60)
            print("错误：")
            for e in self.errors:
                print(f"  ✗ {e}")
        print("=" * 60)


# ============================================================
# 盘符并行扫描（避免慢盘/离线盘阻塞）
# ============================================================


# 单盘符扫描超时（秒）：覆盖本地 SSD 30ms / 慢盘 1-3s / 离线盘无限等待
_DRIVE_SCAN_TIMEOUT = 3.0
# 全局扫描总超时：即使有 5 个盘都慢，也最多等这么久
_OVERALL_SCAN_TIMEOUT = 4.0


def _check_drive_for_texlive(drive: str) -> List[Path]:
    """单盘符扫描：在 <drive>:\texlive\ 下找 YYYY 年份子目录

    此函数在线程中执行，需要自己处理异常（不能抛回主线程）。
    慢盘 / 离线盘会 hang 住 OS 调用本身，这里靠外层超时兜底。
    """
    results: List[Path] = []
    d = Path(drive + "\\texlive")
    if not d.exists():
        return results
    try:
        for year_dir in d.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                results.append(year_dir)
    except OSError:
        pass
    return results


def _scan_drives_for_texlive_parallel(
    drives: tuple = ("C:", "D:", "E:", "F:", "G:"),
) -> List[Path]:
    """并行扫描多个盘符查找 TeX Live 安装目录

    设计要点：
    1. 用 ThreadPoolExecutor 并行：5 个盘符最多等最慢的那个
    2. 外层 as_completed 带超时：超过 _OVERALL_SCAN_TIMEOUT 秒就放弃等待
    3. executor.shutdown(wait=False, cancel_futures=True)：不让慢盘阻塞退出
       （cancel_futures 是 Python 3.9+ 才有的；旧版本会被忽略，慢盘继续跑也无妨）

    Args:
        drives: 要扫描的盘符列表

    Returns:
        找到的 TeX Live 年份目录列表（Path 对象）
    """
    candidate_roots: List[Path] = []
    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=len(drives), thread_name_prefix="tex-scan"
    )
    try:
        future_to_drive = {
            executor.submit(_check_drive_for_texlive, d): d for d in drives
        }
        try:
            for future in concurrent.futures.as_completed(
                future_to_drive, timeout=_OVERALL_SCAN_TIMEOUT
            ):
                try:
                    roots = future.result(timeout=_DRIVE_SCAN_TIMEOUT)
                    candidate_roots.extend(roots)
                except concurrent.futures.TimeoutError:
                    # 单个盘符扫描超时，跳过
                    continue
                except OSError:
                    continue
        except concurrent.futures.TimeoutError:
            # 全局超时：放弃等待剩余盘符（线程池里它们继续跑，互不阻塞）
            pass
    finally:
        # 关键：wait=False + cancel_futures=True
        # 不让 ThreadPoolExecutor.__exit__ 阻塞在慢盘上
        if hasattr(executor, "shutdown"):
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                # Python < 3.9 不支持 cancel_futures
                executor.shutdown(wait=False)

    return candidate_roots


# ============================================================
# 宏包探测
# ============================================================


def _which_with_texlive_fallback(binary_name: str) -> Optional[str]:
    """跨平台查找可执行文件，TeX Live PATH 兜底

    Windows 上 TeX Live 默认不加入 PATH（用户装完通常不会手动添加），
    直接 shutil.which 经常返回 None。这里在 PATH 找不到时，
    按平台探测常见的 TeX Live 安装目录。

    Args:
        binary_name: 如 "kpsewhich" / "pdflatex" / "fc-list"

    Returns:
        可执行文件绝对路径，或 None
    """
    # 1) 先走标准 PATH（Windows 上 shutil.which 自动处理 .exe / .bat）
    found = shutil.which(binary_name)
    if found:
        return found

    # 2) 平台特定的兜底搜索路径
    candidates: List[Path] = []
    family = _detect_os_family()

    if family == "windows":
        # TeX Live Windows 安装可能在多个盘符的 \texlive\YYYY\bin\windows\
        # 也可能用户自定义目录（如 E:\texlive\2026）
        # 用并行扫描 + 超时退出避免慢盘/离线盘阻塞
        candidate_roots = _scan_drives_for_texlive_parallel()

        # 优先级 2: 用户自定义 TEXLIVE_HOME / TEXLIVE_ROOT 环境变量
        for env_key in ("TEXLIVE_ROOT", "TEXLIVE_HOME", "TeXLiveRoot"):
            val = os.environ.get(env_key)
            if val:
                p = Path(val)
                if p.exists():
                    candidate_roots.append(p)

        # 优先级 3: MikTeX 安装目录（Windows 另一种 TeX 发行版）
        for miktex_root in (
            Path("C:/Program Files/MiKTeX/miktex/bin/x64"),
            Path("C:/Program Files (x86)/MiKTeX/miktex/bin"),
        ):
            if miktex_root.exists():
                candidate_roots.append(miktex_root)

        # 组装候选路径（TeX Live Windows: <root>\bin\windows\kpsewhich.exe）
        bin_subdir = "windows" if family == "windows" else ""
        for root in candidate_roots:
            if bin_subdir:
                candidates.append(root / "bin" / bin_subdir / f"{binary_name}.exe")
            else:
                candidates.append(root / f"{binary_name}.exe")
        # MiKTeX 路径（已是 bin 目录，不要再追加 bin/windows）
        for root in candidate_roots:
            if any(p in str(root) for p in ("MiKTeX", "MikTeX")):
                candidates.append(root / f"{binary_name}.exe")

    elif family == "darwin":
        # MacTeX 默认路径
        for root in (
            Path("/usr/local/texlive"),
            Path("/Library/TeX/texbin"),
        ):
            if root.exists():
                if root.name == "texlive":
                    for year_dir in root.iterdir():
                        if year_dir.is_dir() and year_dir.name.isdigit():
                            candidates.append(
                                year_dir / "bin" / "universal-darwin" / binary_name
                            )
                else:
                    candidates.append(root / binary_name)

    elif family == "linux":
        # Linux TeX Live 可能装在 /usr/bin 或 /usr/local/texlive/...
        for root in (
            Path("/usr/bin"),
            Path("/usr/local/texlive"),
        ):
            if root.exists():
                if root.name == "texlive":
                    for year_dir in root.iterdir():
                        if year_dir.is_dir() and year_dir.name.isdigit():
                            candidates.append(
                                year_dir / "bin" / "x86_64-linux" / binary_name
                            )
                            candidates.append(
                                year_dir / "bin" / "universal-linux" / binary_name
                            )
                else:
                    candidates.append(root / binary_name)

    # 3) 在候选路径中查找第一个存在的
    for cand in candidates:
        if cand.exists() and os.access(cand, os.X_OK):
            return str(cand)

    return None


def _check_package_with_kpsewhich(pkg: str) -> bool:
    """用 kpsewhich <pkg>.sty 探测宏包是否安装（LaTeX 路径下）

    Windows 兼容：自动探测 TeX Live / MiKTeX 默认安装路径。
    """
    kpse = _which_with_texlive_fallback("kpsewhich")
    if not kpse:
        return False
    try:
        # encoding="utf-8" + errors="ignore" 解决 Windows 进程 stdout 非 UTF-8 的问题
        out = subprocess.run(
            [kpse, f"{pkg}.sty"],
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,  # 修复原 3s 太短，Windows 杀软扫描时易超时
        )
        return out.returncode == 0 and bool(out.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _probe_packages(engine: str) -> List[str]:
    """探测某个引擎下可用的 CJK 宏包

    Returns:
        该引擎下已安装的 CJK 宏包列表
    """
    candidates = CJK_PACKAGES.get(engine, [])
    return [p for p in candidates if _check_package_with_kpsewhich(p)]


# ============================================================
# 中文字体探测
# ============================================================


def _detect_os_family() -> str:
    """返回 'windows' / 'darwin' / 'linux'"""
    s = platform.system().lower()
    if s.startswith("win"):
        return "windows"
    if s.startswith("darwin"):
        return "darwin"
    if s.startswith("linux"):
        return "linux"
    return s


def _probe_fonts_linux() -> List[str]:
    """Linux 用 fc-list 探测中文字体"""
    fc_list = _which_with_texlive_fallback(
        "fc-list"
    )  # fc-list 不在 TeX Live，这里实际是 PATH 查找
    if not fc_list:
        return []
    try:
        out = subprocess.run(
            [fc_list, ":lang=zh", "family"],
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
        )
        families = set()
        for line in (out.stdout or "").splitlines():
            # fc-list 输出形如 "Noto Sans CJK SC:style=Regular"
            family = line.split(":")[0].strip()
            if family:
                families.add(family)
        # 与候选名做交集，保留顺序
        return [f for f in CJK_FONT_CANDIDATES["linux"] if f in families]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []


def _probe_fonts_windows() -> List[str]:
    """Windows 中文字体探测：系统字体 + 用户字体 + 注册表"""
    found: List[str] = []

    # 1) 系统字体目录 C:/Windows/Fonts
    system_fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"

    # 2) Win10+ 用户级字体目录 %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts
    user_fonts = (
        Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
        / "Microsoft/Windows/Fonts"
    )

    name_to_files = {
        "Microsoft YaHei": ["msyh.ttc", "msyh.ttf", "msyhbd.ttc"],
        "Microsoft YaHei UI": ["msyhui.ttc"],
        "SimHei": ["simhei.ttf"],
        "SimSun": ["simsun.ttc", "simsun.ttf"],
        "KaiTi": ["simkai.ttf"],
        "FangSong": ["simfang.ttf"],
        "YouYuan": ["simyou.ttf"],
    }

    for fonts_dir in (system_fonts, user_fonts):
        if not fonts_dir.exists():
            continue
        try:
            for display_name, files in name_to_files.items():
                if display_name in found:
                    continue
                for fname in files:
                    if (fonts_dir / fname).exists():
                        found.append(display_name)
                        break
        except OSError:
            pass

    # 3) 注册表（最权威，但 Windows 专属）
    # 通过 winreg 读取 HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts
    # 拿到的是"显示名 → 实际文件名"映射，能覆盖到自定义安装
    try:
        import winreg  # type: ignore  # 平台专属，Windows 才有

        registry_fonts = _read_windows_font_registry()
        for display_name in name_to_files:
            if display_name in found:
                continue
            # 注册表里键名是 "Microsoft YaHei (TrueType)" 这种
            # 我们做模糊匹配（去掉括号内容）
            name_key = display_name.split(" ")[0]  # 简化匹配
            for reg_name in registry_fonts:
                if name_key.lower() in reg_name.lower() and (
                    "yahei" in reg_name.lower()
                    or "simhei" in reg_name.lower()
                    or "simsun" in reg_name.lower()
                    or "kaiti" in reg_name.lower()
                ):
                    found.append(display_name)
                    break
    except ImportError:
        pass  # 非 Windows，跳过
    except OSError:
        pass  # 注册表读取失败

    return found


def _read_windows_font_registry() -> List[str]:
    """从 Windows 注册表读取已安装字体名（仅 Windows 平台）"""
    import winreg  # type: ignore

    fonts = []
    # HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts
    reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root, reg_path) as key:
                i = 0
                while True:
                    try:
                        name, _, _ = winreg.EnumValue(key, i)
                        fonts.append(name)
                        i += 1
                    except OSError:
                        break
        except OSError:
            continue
    return fonts


def _probe_fonts_darwin() -> List[str]:
    """macOS 通过系统字体目录探测"""
    candidates_dirs = [
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
        Path.home() / "Library" / "Fonts",
    ]
    found = []
    # 简化：检查常见中文字体文件存在
    name_to_file = {
        "PingFang SC": ["PingFang.ttc"],
        "STHeiti": ["STHeiti Medium.ttc", "STHeiti Light.ttc"],
        "Hiragino Sans GB": ["Hiragino Sans GB.ttc"],
        "Noto Sans CJK SC": ["NotoSansCJKsc-Regular.otf"],
    }
    for d in candidates_dirs:
        if not d.exists():
            continue
        for name, files in name_to_file.items():
            for f in files:
                if (d / f).exists() and name not in found:
                    found.append(name)
    return found


def _probe_chinese_fonts() -> List[str]:
    """跨平台探测中文字体"""
    family = _detect_os_family()
    if family == "linux":
        fonts = _probe_fonts_linux()
    elif family == "windows":
        fonts = _probe_fonts_windows()
    elif family == "darwin":
        fonts = _probe_fonts_darwin()
    else:
        fonts = []
    return fonts


# ============================================================
# 综合判定
# ============================================================


def _decide_render_path(report: CJKReport) -> str:
    """根据探测结果决定走哪条渲染路径

    Returns:
        'tex_minipage'   - xelatex + 中文字体 + CJK 宏包齐全，可走 minipage
        'tex_standard'   - 有 LaTeX 引擎但 CJK 条件不完整，走标准 Tex（少中文）
        'text_pango_only' - 强制走 Manim Text（Pango 渲染中文）
    """
    if report.recommended_engine in ("xelatex", "lualatex") and report.chinese_fonts:
        # 有现代引擎 + 字体，至少可以走 Tex
        if report.cjk_packages.get(report.recommended_engine):
            return "tex_minipage"
        else:
            return "tex_standard"
    elif report.recommended_engine in ("xelatex", "lualatex"):
        # 有引擎但没字体 → Tex 仍可走但 CJK 字符可能渲染失败
        report.warnings.append(
            f"{report.recommended_engine} 可用但未检测到系统中文字体，"
            "CJK 字符可能渲染为方块"
        )
        return "text_pango_only"
    elif report.recommended_engine == "pdflatex":
        if report.cjk_packages.get("pdflatex"):
            return "tex_standard"
        report.warnings.append(
            "只有 pdflatex 可用且未检测到 CJK 宏包，建议走 Text 路径"
        )
        return "text_pango_only"
    else:
        # 完全没有 LaTeX 引擎
        report.warnings.append("未检测到任何 LaTeX 引擎，强制走 Text 路径")
        return "text_pango_only"


def _populate_issues(report: CJKReport) -> None:
    """根据报告内容填充 warnings / errors / notes"""
    if not report.available_engines:
        report.errors.append(
            "未找到任何 LaTeX 引擎（pdflatex/xelatex/lualatex）。"
            "请安装 TeX 发行版（TeX Live / MiKTeX / MacTeX）"
        )
    if not report.chinese_fonts:
        report.warnings.append(
            "未检测到系统中文字体。Windows 需安装微软雅黑，"
            "Linux 需安装 Noto Sans CJK / WenQuanYi"
        )
    if report.render_path == "text_pango_only":
        report.notes.append(
            "推荐渲染路径：Text (Pango)。"
            "LayoutScene._wrap_text_object 已具备字符估算换行 + 子对象 fill 修复"
        )
    elif report.render_path == "tex_minipage":
        report.notes.append(
            "推荐渲染路径：Tex (minipage + xeCJK/fontspec)。"
            "可以使用 LayoutScene.tex_render_with_minipage(text, width)"
        )
    elif report.render_path == "tex_standard":
        report.notes.append(
            "推荐渲染路径：标准 Tex (pdflatex + CJK 宏包)。"
            "CJK 字符可渲染但不保证复杂排版"
        )


def check(verbose: bool = False) -> CJKReport:
    """执行 CJK 综合自检

    Args:
        verbose: 是否打印人类可读报告

    Returns:
        CJKReport：含所有探测维度、推荐渲染路径、问题清单

    Example:
        >>> report = check()
        >>> if not report.ok:
        ...     print(report.errors)
        >>> if report.render_path == "tex_minipage":
        ...     scene.use_minipage_path()
    """
    report = CJKReport()

    # 1) LaTeX 引擎
    probe = probe_tex_engines()
    report.probe = probe.to_dict()
    report.recommended_engine = probe.recommendation
    report.available_engines = [e.engine for e in probe.engines if e.available]

    # 2) 各引擎的 CJK 宏包
    for engine in report.available_engines:
        report.cjk_packages[engine] = _probe_packages(engine)

    # 3) 中文字体
    report.chinese_fonts = _probe_chinese_fonts()

    # 4) 渲染路径决策
    report.render_path = _decide_render_path(report)

    # 5) 整体 OK 判定：能找到至少一种可行路径
    report.ok = bool(report.available_engines) or bool(report.chinese_fonts)

    # 6) 填充提示信息
    _populate_issues(report)

    if verbose:
        report.print_human()

    return report


# ============================================================
# 缓存
# ============================================================

_CACHE_DIR = Path.home() / ".manim_skill_cache"
_CACHE_FILE = _CACHE_DIR / "cjk_env_state.json"


def _save_cache(report: CJKReport) -> None:
    """缓存报告（避免每次渲染都重新探测）"""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass  # 缓存失败不阻塞


def _load_cache() -> Optional[CJKReport]:
    """读取缓存（若存在）"""
    if not _CACHE_FILE.exists():
        return None
    try:
        data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        r = CJKReport()
        r.ok = data.get("ok", False)
        r.render_path = data.get("render_path", "")
        r.recommended_engine = data.get("recommended_engine", "")
        r.available_engines = data.get("available_engines", [])
        r.cjk_packages = data.get("cjk_packages", {})
        r.chinese_fonts = data.get("chinese_fonts", [])
        r.warnings = data.get("warnings", [])
        r.errors = data.get("errors", [])
        r.notes = data.get("notes", [])
        r.probe = data.get("probe")
        return r
    except (json.JSONDecodeError, OSError):
        return None


def check_cached(verbose: bool = False, force_refresh: bool = False) -> CJKReport:
    """带缓存的自检（推荐在场景 setup 中使用）

    Args:
        verbose: 打印报告
        force_refresh: 强制重新探测（默认从缓存读）
    """
    if not force_refresh:
        cached = _load_cache()
        if cached is not None:
            if verbose:
                cached.print_human()
            return cached
    report = check(verbose=verbose)
    _save_cache(report)
    return report


# RenderPath 字符串常量（方便类型提示）
class RenderPath:
    TEX_MINIPAGE = "tex_minipage"
    TEX_STANDARD = "tex_standard"
    TEXT_PANGO_ONLY = "text_pango_only"


if __name__ == "__main__":
    r = check(verbose=True)
    _save_cache(r)
