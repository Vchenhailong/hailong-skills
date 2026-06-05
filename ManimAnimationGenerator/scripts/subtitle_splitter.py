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
    
    参数:
        text: 原始语音文本
        max_chars: 每段最大字符数
    
    返回:
        拆分后的文本列表
    """
    if len(text) <= max_chars:
        return [text]

    result = []
    chunks = re.split(r'(?<=[，。！？；、])', text)

    current_chunk = ""
    for chunk in chunks:
        if len(current_chunk) + len(chunk) <= max_chars:
            current_chunk += chunk
        else:
            if current_chunk:
                result.append(current_chunk)
            if len(chunk) > max_chars:
                sub_chunks = [chunk[i:i+max_chars] for i in range(0, len(chunk), max_chars)]
                result.extend(sub_chunks[:-1])
                current_chunk = sub_chunks[-1]
            else:
                current_chunk = chunk

    if current_chunk:
        result.append(current_chunk)

    return [r.strip() for r in result if r.strip()]
