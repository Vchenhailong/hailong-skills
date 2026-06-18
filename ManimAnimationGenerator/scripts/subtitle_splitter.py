#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕拆分工具 - 将长语音文本拆分为合适的字幕段落
"""

import re
from typing import List


def split_utterance(text: str, max_chars: int = 20) -> List[str]:
    """
    将语音文本拆分为不超过max_chars个字符的段落

    算法：
    1. 在中文标点（，。！？；、）处切分
    2. 分隔符跟在前一个 chunk（避免下一个 chunk 出现前导标点）
    3. 单 chunk 超过 max_chars 时按 max_chars 硬切
       - 硬切时在边界前找最近的标点，让分句在自然边界处结束
       - 找不到则纯硬切

    参数:
        text: 原始语音文本
        max_chars: 每段最大字符数

    返回:
        拆分后的文本列表（每段不超过 max_chars）
    """
    if not text:
        return []

    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    # 切分时把分隔符留在前一个 chunk（lookbehind 保留分隔符）
    chunks = re.split(r'(?<=[，。！？；、])', text)

    result = []
    current_chunk = ""
    for chunk in chunks:
        if not chunk:
            continue
        if len(current_chunk) + len(chunk) <= max_chars:
            current_chunk += chunk
        else:
            if current_chunk:
                result.append(current_chunk)
            # 单 chunk 超长：硬切
            if len(chunk) > max_chars:
                # 智能切分：在边界前找最近的标点位置
                sub_chunks = _smart_split_long_chunk(chunk, max_chars)
                result.extend(sub_chunks)
                current_chunk = ""
            else:
                current_chunk = chunk

    if current_chunk:
        result.append(current_chunk)

    return [r.strip() for r in result if r.strip()]


def _smart_split_long_chunk(chunk: str, max_chars: int) -> List[str]:
    """把超长 chunk 切成多个 sub_chunk，每个 ≤ max_chars

    切分策略：
    - 在 [0, max_chars] 范围内找最近的标点（，。！？；、）作为切点
    - 找不到则按 max_chars 硬切
    """
    PUNCT = set("，。！？；、")
    result = []
    remaining = chunk
    while len(remaining) > max_chars:
        # 在 [0, max_chars] 范围内（含 max_chars）找最近的标点
        # 优先找最右边的标点（让前面尽量填满）
        cut_pos = -1
        for i in range(max_chars, 0, -1):
            if remaining[i] in PUNCT:
                cut_pos = i + 1  # 切到标点之后
                break
        if cut_pos <= 0:
            # 没找到标点，硬切
            cut_pos = max_chars
        result.append(remaining[:cut_pos])
        remaining = remaining[cut_pos:]
    if remaining:
        result.append(remaining)
    return result
