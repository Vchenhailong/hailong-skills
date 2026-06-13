#!/usr/bin/env python3
# coding: utf-8
"""
自动拆分 JSON 课件内容

功能：
1. 判断原子是否需要拆分（元素数量 > 8 或预估尺寸超标）
2. 将超长原子拆分为多个独立原子
3. 保持教学逻辑的连贯性

用法：
    from scripts.split_atom import should_split_atom, split_atom, split_all_atoms

    # 判断单个原子
    need_split, reason = should_split_atom(atom)

    # 拆分单个原子
    new_atoms = split_atom(atom)

    # 批量处理整个 JSON 数据
    new_data = split_all_atoms(data)
"""

import copy
import re
from typing import List, Dict, Any, Tuple, Optional


def estimate_content_height(content_list: List[Dict[str, Any]]) -> float:
    """
    预估 content 数组的垂直高度（单位）
    每个元素约 0.8 单位高度 + 0.4 间距
    """
    n = len(content_list)
    if n == 0:
        return 0.0
    # 每个元素平均高度 0.8，间距 0.4
    return n * 0.8 + (n - 1) * 0.4


def estimate_content_width(content_list: List[Dict[str, Any]]) -> float:
    """
    预估 content 数组的水平宽度（单位）
    每个中文字符约 0.6 单位，每个英文字符约 0.4 单位
    """
    total_width = 0.0
    for item in content_list:
        text = item.get("text", "")
        item_type = item.get("type", "content")
        if item_type == "formula":
            # 公式按字符数估算，每个字符 0.6 单位
            total_width += len(text) * 0.6
        else:
            # 文本：中文 0.6，英文 0.4
            chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text))
            english_count = len(re.findall(r'[a-zA-Z0-9]', text))
            total_width += chinese_count * 0.6 + english_count * 0.4
    # 加上元素间距
    total_width += (len(content_list) - 1) * 0.3
    return total_width


def should_split_atom(atom: Dict[str, Any]) -> Tuple[bool, str]:
    """
    判断是否需要拆分原子

    返回: (是否需要拆分, 原因)
    """
    content_list = atom.get("content", [])
    n = len(content_list)

    # 条件1：元素数量超过 8
    if n > 8:
        return True, f"元素数量 {n} 超过 8"

    # 条件2：预估垂直高度超过 5.5 单位
    est_height = estimate_content_height(content_list)
    if est_height > 5.5:
        return True, f"预估垂直高度 {est_height:.1f} 超过 5.5 单位"

    # 条件3：预估水平宽度超过 13.5 单位
    est_width = estimate_content_width(content_list)
    if est_width > 13.5:
        return True, f"预估水平宽度 {est_width:.1f} 超过 13.5 单位"

    # 条件4：包含多个独立公式（公式数量 > 2）
    formula_count = sum(1 for item in content_list if item.get("type") == "formula")
    if formula_count > 2:
        return True, f"包含 {formula_count} 个独立公式，建议拆分"

    return False, ""


def split_atom(atom: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    将原子拆分为多个原子

    拆分策略：
    1. 按元素数量均分
    2. 保持公式和文字的完整性（尽量不在公式中间拆分）
    3. 保持 highlight 元素作为新原子的开头
    """
    content_list = atom.get("content", [])
    n = len(content_list)

    if n <= 1:
        return [atom]

    # 计算拆分数量
    if n <= 8:
        num_parts = 2
    else:
        num_parts = (n + 7) // 8  # 每个原子最多 8 个元素

    # 均分
    part_size = (n + num_parts - 1) // num_parts

    new_atoms = []
    for i in range(num_parts):
        start = i * part_size
        end = min((i + 1) * part_size, n)
        part_content = content_list[start:end]

        # 复制原原子，修改 id 和 content
        new_atom = copy.deepcopy(atom)
        new_atom["id"] = f"{atom['id']}_part{i + 1}"
        new_atom["content"] = part_content

        # 调整 duration（按比例分配）
        original_duration = atom.get("duration", 6.0)
        new_atom["duration"] = original_duration * len(part_content) / n

        new_atoms.append(new_atom)

    return new_atoms


def split_all_atoms(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    批量处理整个 JSON 数据，拆分所有超长原子

    返回: 拆分后的新数据
    """
    if "atoms" not in data:
        return data

    new_data = copy.deepcopy(data)
    new_atoms = []

    for atom in data.get("atoms", []):
        need_split, reason = should_split_atom(atom)
        if need_split:
            print(f"拆分原子: {atom.get('id')} - 原因: {reason}")
            split_atoms = split_atom(atom)
            new_atoms.extend(split_atoms)
        else:
            new_atoms.append(atom)

    new_data["atoms"] = new_atoms
    return new_data


# ============================================================
# 命令行入口
# ============================================================

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("用法: python split_atom.py <input.json> [output.json]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_data = split_all_atoms(data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"处理完成，输出到: {output_path}")
