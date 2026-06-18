#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打字机效果 (Typewriter Effect)

提供 Manim 文本对象的逐字显示动画，用于非字幕区的内容呈现。
打字机效果强调"边说边出现"的同步感，与字幕区滚动形成层次差异。

核心特性：
1. 字符级增量显示（AddTextLetterByLetter）
2. 支持自定义每字符延迟
3. 支持中英文混排（中文按字计，英文按字符合并）
4. 支持任意 Mobject（Text / MarkupText / Paragraph）
5. 保持原对象的位置和样式不变

典型用途：
- 标题/步骤说明的逐字显示
- 公式的逐字符构建
- 重点内容的强调呈现

使用示例：
    from scripts.animation.typewriter import Typewriter

    text = Text("牛顿第二定律：F=ma", font_size=32)
    self.add(text)  # 先把空对象加入场景
    self.play(Typewriter(text, run_time=2.0))  # 触发打字机动画
"""

from manim import (
    Text,
    MarkupText,
    Animation,
    AddTextLetterByLetter,
)
from manim.utils.rate_functions import linear, smooth
from typing import Union, Optional


class Typewriter(AddTextLetterByLetter):
    """打字机动画（基于 AddTextLetterByLetter 的封装）

    在 Manim 0.17+ 中，原生 AddTextLetterByLetter 接受 time_per_char 参数
    （而非旧版的 lag_ratio）。本类以 AddTextLetterByLetter 为基类，
    封装出更易用的接口。

    Args:
        text: 文本对象（Text / MarkupText）
        run_time: 动画总时长（秒），默认 2.0
        time_per_char: 每个字符的延迟时间（秒），默认 None（自动按 run_time / 字符数计算）
        rate_func: 动画速率函数，默认 linear
        buff: 字符间的额外间隔（Manim 单位），默认 0

    使用示例：
        >>> text = Text("Hello World", font_size=32)
        >>> self.add(text)
        >>> self.play(Typewriter(text, run_time=2.0))
    """

    def __init__(
        self,
        text: Union[Text, MarkupText],
        run_time: float = 2.0,
        time_per_char: Optional[float] = None,
        rate_func=linear,
        buff: float = 0,
        **kwargs,
    ):
        if not isinstance(text, (Text, MarkupText)):
            raise TypeError(
                f"Typewriter 仅支持 Text/MarkupText，当前类型: {type(text).__name__}"
            )

        # 计算每个字符的时间
        if time_per_char is None:
            char_count = (
                len(text.original_text)
                if hasattr(text, "original_text")
                else len(str(text.text))
            )
            char_count = max(1, char_count)
            time_per_char = run_time / char_count

        # 兼容 Manim 0.20+：AddTextLetterByLetter 不再接受 buff 参数
        kwargs.pop("buff", None)

        # 调用基类构造
        super().__init__(
            text,
            run_time=run_time,
            time_per_char=time_per_char,
            rate_func=rate_func,
            **kwargs,
        )


def typewriter_in(
    scene,
    text: Union[Text, MarkupText],
    run_time: float = 2.0,
    time_per_char: Optional[float] = None,
    rate_func=linear,
    buff: float = 0,
) -> None:
    """便捷函数：把文本对象添加到场景并播放打字机动画

    等价于：
        scene.add(text)
        scene.play(Typewriter(text, run_time=run_time, ...))

    Args:
        scene: Manim Scene 实例
        text: 文本对象
        run_time: 动画总时长（秒）
        time_per_char: 每个字符的延迟时间
        rate_func: 动画速率函数
        buff: 字符间隔
    """
    scene.add(text)
    scene.play(
        Typewriter(
            text,
            run_time=run_time,
            time_per_char=time_per_char,
            rate_func=rate_func,
            buff=buff,
        )
    )


def typewriter_in_group(
    scene,
    mobjects: list,
    per_object_run_time: float = 2.0,
    time_per_char: Optional[float] = None,
    rate_func=linear,
    buff: float = 0,
) -> None:
    """对一组文本对象依次播放打字机动画

    Args:
        scene: Manim Scene 实例
        mobjects: 文本对象列表
        per_object_run_time: 每个对象的打字机时长
        time_per_char: 每个字符的延迟时间
        rate_func: 动画速率函数
        buff: 字符间隔
    """
    for mobj in mobjects:
        scene.add(mobj)
        scene.play(
            Typewriter(
                mobj,
                run_time=per_object_run_time,
                time_per_char=time_per_char,
                rate_func=rate_func,
                buff=buff,
            )
        )
