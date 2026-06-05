#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
布局规范静态检查脚本

功能：
1. 检查 Manim 代码是否使用了禁止的布局方法
2. 区分允许的例外情况
3. 输出检查报告

用法：
    python scripts/validate_layout.py scene.py
    python scripts/validate_layout.py scenes/*.py
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple


class LayoutValidator:
    """布局规范验证器"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.line_checks = []

    def check_file(self, filepath: Path) -> Tuple[bool, List[str], List[str]]:
        """检查单个文件"""
        self.errors = []
        self.warnings = []

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        self._check_shift_usage(content, lines)
        self._check_move_to_exception(content, lines)
        self._check_forbidden_methods(content, lines)
        self._check_recommended_usage(content)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _check_shift_usage(self, content: str, lines: List[str]):
        """检查 .shift() 使用：只允许对 VGroup 整体使用"""
        # 查找所有 .shift( 调用
        for line_no, line in enumerate(lines, 1):
            shift_match = re.search(r'\.shift\(', line)
            if not shift_match:
                continue

            # 向上查找是否在 VGroup 上调用
            # 简单检查：同一行或上一行是否有 VGroup 赋值
            is_on_vgroup = False
            
            # 检查当前行
            if re.search(r'VGroup\(.*?\)\.shift\(', line):
                is_on_vgroup = True
            # 检查上一行
            if line_no > 1 and re.search(r'VGroup\(.*?\)$', lines[line_no - 2]):
                is_on_vgroup = True
            # 检查当前行是否有 group = VGroup 的变量名
            if re.search(r'[a-z_]+(?:_col|_group|group)\.shift\(', line, re.IGNORECASE):
                is_on_vgroup = True

            if not is_on_vgroup:
                self.errors.append(f"行 {line_no}: 禁止对单个元素使用 .shift()，仅允许对 VGroup 整体使用")

    def _check_move_to_exception(self, content: str, lines: List[str]):
        """检查 .move_to()：只允许纯标题场景 title.move_to(ORIGIN)"""
        for line_no, line in enumerate(lines, 1):
            move_match = re.search(r'\.move_to\(', line)
            if not move_match:
                continue

            # 检查是否为纯标题场景
            is_title_exception = False
            if re.search(r'title\s*=\s*Text\(.*?\)', line) and 'ORIGIN' in line:
                is_title_exception = True
            if 'move_to(ORIGIN)' in line and 'title' in line.lower():
                is_title_exception = True

            if not is_title_exception:
                self.errors.append(f"行 {line_no}: 禁止使用 .move_to()，纯标题场景除外")

    def _check_forbidden_methods(self, content: str, lines: List[str]):
        """检查其他禁止方法"""
        forbidden = [
            (r'\.next_to\(', '.next_to()'),
            (r'\.align_to\(', '.align_to()'),
        ]

        for pattern, name in forbidden:
            for line_no, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    self.errors.append(f"行 {line_no}: 禁止使用 {name}")

        # 检查硬编码坐标
        coord_pattern = r'\[-?\d+\.?\d*,\s*-?\d+\.?\d*,\s*-?\d+\.?\d*\]'
        for line_no, line in enumerate(lines, 1):
            if re.search(coord_pattern, line):
                if 'ORIGIN' not in line and 'UP' not in line and 'DOWN' not in line:
                    if 'LEFT' not in line and 'RIGHT' not in line:
                        self.warnings.append(f"行 {line_no}: 疑似硬编码坐标，建议使用相对定位")

    def _check_recommended_usage(self, content: str):
        """检查推荐方法的使用"""
        if not re.search(r'VGroup\(.*?\)\.arrange\(', content):
            self.warnings.append("未检测到 VGroup.arrange() 使用，建议优先使用此方法进行布局")

    def _check_safe_place(self, content: str):
        """检查是否调用了 safe_place"""
        if not re.search(r'\.safe_place\(', content):
            self.warnings.append("未检测到 safe_place() 调用，建议在布局后调用以确保安全区域")


def main():
    parser = argparse.ArgumentParser(description="布局规范静态检查")
    parser.add_argument('files', nargs='+', help='要检查的 Python 文件')
    args = parser.parse_args()

    validator = LayoutValidator()
    all_valid = True

    for filepath_str in args.files:
        filepath = Path(filepath_str)
        if not filepath.exists():
            print(f"文件不存在: {filepath}")
            continue

        print(f"\n检查: {filepath}")
        print("-" * 50)

        is_valid, errors, warnings = validator.check_file(filepath)

        for warn in warnings:
            print(f"⚠️  {warn}")

        for err in errors:
            print(f"❌ {err}")

        if is_valid:
            print("✅ 布局规范检查通过")
        else:
            print("❌ 布局规范检查失败")
            all_valid = False

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()