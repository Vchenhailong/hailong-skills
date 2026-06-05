#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# visual_actions.py - 视觉动作模板（供 AI 生成代码时嵌入）

from manim import *
from typing import Dict, Any, List, Optional


def highlight_matrix_cell(scene, matrix, row, col, color="#66DDFF"):
    """高亮矩阵的特定单元格"""
    entries = matrix.get_entries()
    if row < len(entries) and col < len(entries[0]):
        cell = entries[row][col]
        scene.play(Indicate(cell, color=color))


def show_dot_product_step(scene, row_vec, col_vec, result_cell, params=None):
    """逐步演示点积计算过程（需根据实际布局实现）"""
    pass


def show_geometry(scene, params: Dict[str, Any]):
    """展示几何图形（如向量变换、坐标系等）

    params 支持:
        - type: "axes" / "vector" / "transform"
        - x_range: list, 默认 [-3, 3, 1]
        - y_range: list, 默认 [-3, 3, 1]
        - vector: list, 默认 [2, 1, 0]
        - color: str, 默认 YELLOW
    """
    gtype = params.get("type", "axes")

    if gtype == "axes":
        x_range = params.get("x_range", [-3, 3, 1])
        y_range = params.get("y_range", [-3, 3, 1])
        axes = Axes(
            x_range=x_range,
            y_range=y_range,
            x_length=6,
            y_length=6,
        )
        scene.play(Create(axes))
    elif gtype == "vector":
        vector_coords = params.get("vector", [2, 1, 0])
        color = params.get("color", YELLOW)
        vector = Arrow(ORIGIN, vector_coords, color=color)
        scene.play(GrowArrow(vector))
    elif gtype == "transform":
        # 变换动画
        pass


def animate_vector_transform(scene, vector, matrix, params=None):
    """将向量应用矩阵变换并显示动画"""
    pass


def draw_angle(scene, vertex, line1, line2, radius=0.5, color="#66DDFF"):
    """绘制角标记（使用 Manim 的 Angle）"""
    angle = Angle(line1, line2, radius=radius, color=color)
    scene.play(Create(angle))


def add_equal_marks(scene, line, count=1, color="#66DDFF"):
    """为线段添加等长标记（单竖线/双竖线/三竖线）"""
    marks = VGroup()
    mid = line.get_center()
    direction = line.get_end() - line.get_start()
    length = direction.get_length()
    direction = direction.normalize()
    perp = rotate_vector(direction, PI / 2)
    mark_length = min(length * 0.1, 0.3)
    
    for i in range(count):
        offset = (i - (count - 1) / 2) * 0.08
        mark_line = Line(
            mid + perp * offset + direction * mark_length / 2,
            mid + perp * offset - direction * mark_length / 2,
            color=color,
            stroke_width=3,
        )
        marks.add(mark_line)
    scene.play(Create(marks))


def add_glow(scene, text, color="#66DDFF", radius=0.05):
    """为文字添加发光效果"""
    glow = text.copy().set_color(color).set_opacity(0.3)
    glow.scale(1 + radius)
    glow_text = VGroup(glow, text)
    scene.play(FadeIn(glow_text))
    return glow_text


def highlight_conclusion(scene, text, color="#66DDFF"):
    """高亮结论文字（发光 + Indicate）"""
    glow_text = add_glow(scene, text, color)
    scene.play(Indicate(text, color=color))


def draw_graphics(scene, graphics_desc: Dict[str, Any]):
    """根据 graphics 描述绘制图形，符合 json_schema.md 中定义的 graphics.type 枚举

    graphics_desc 结构:
        - type: 图形类型，合法值：
            axes, function, polygon, linear_algebra, matrix_animation,
            comparison, image_effect, physics, three_d
        - params: 图形参数
    """
    from manim import Axes, Circle, Polygon, Square, ParametricFunction, ThreeDScene

    gtype = graphics_desc.get("type")
    params = graphics_desc.get("params", {})

    if gtype == "axes":
        x_range = params.get("x_range", [-3, 3, 1])
        y_range = params.get("y_range", [-3, 3, 1])
        x_length = params.get("x_length", 6)
        y_length = params.get("y_length", 6)
        axes = Axes(
            x_range=x_range,
            y_range=y_range,
            x_length=x_length,
            y_length=y_length,
        )
        scene.play(Create(axes))

    elif gtype == "function":
        func_str = params.get("function", "sin(x)")
        x_range = params.get("x_range", [-3, 3])
        color = params.get("color", "#66DDFF")
        # 使用 lambda 安全解析（实际项目中应使用 sympy 或 eval 受限环境）
        try:
            import numpy as np
            def f(x):
                return eval(func_str, {"x": x, "np": np, "sin": np.sin, "cos": np.cos, "tan": np.tan})
            graph = Axes(
                x_range=[x_range[0], x_range[1], 0.5],
                y_range=[-2, 2, 0.5],
                x_length=6,
                y_length=4,
            ).plot(f, color=color)
            scene.play(Create(graph))
        except Exception as e:
            print(f"绘制函数图像失败: {e}")

    elif gtype == "polygon":
        shape = params.get("shape")
        color = params.get("color", "#66DDFF")
        fill_opacity = params.get("fill_opacity", 0.3)

        if shape == "square":
            side_length = params.get("side_length", 2)
            center = params.get("center", [0, 0])
            half = side_length / 2
            vertices = [
                [center[0] - half, center[1] - half, 0],
                [center[0] + half, center[1] - half, 0],
                [center[0] + half, center[1] + half, 0],
                [center[0] - half, center[1] + half, 0],
            ]
            polygon = Polygon(*vertices, color=color, fill_opacity=fill_opacity)
            scene.play(Create(polygon))

        elif shape == "triangle":
            vertices = params.get("vertices", [[-1, -1, 0], [1, -1, 0], [0, 1.5, 0]])
            polygon = Polygon(*vertices, color=color, fill_opacity=fill_opacity)
            scene.play(Create(polygon))

        elif shape == "rectangle":
            width = params.get("width", 4)
            height = params.get("height", 3)
            center = params.get("center", [0, 0])
            half_w = width / 2
            half_h = height / 2
            vertices = [
                [center[0] - half_w, center[1] - half_h, 0],
                [center[0] + half_w, center[1] - half_h, 0],
                [center[0] + half_w, center[1] + half_h, 0],
                [center[0] - half_w, center[1] + half_h, 0],
            ]
            polygon = Polygon(*vertices, color=color, fill_opacity=fill_opacity)
            scene.play(Create(polygon))

        elif shape == "circle":
            # 保留 circle 作为 polygon 的子类型以兼容旧数据
            radius = params.get("radius", 1.5)
            center = params.get("center", [0, 0])
            circle = Circle(radius=radius, color=color, fill_opacity=fill_opacity)
            circle.move_to(center)
            scene.play(Create(circle))

    elif gtype == "linear_algebra":
        vectors = params.get("vectors", [])
        transform_matrix = params.get("transform", None)

        axes = Axes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], x_length=6, y_length=6)
        scene.play(Create(axes))

        for vec in vectors:
            coords = vec.get("coords", [1, 0])
            color = vec.get("color", RED)
            arrow = Arrow(ORIGIN, coords, color=color)
            scene.play(GrowArrow(arrow))

        if transform_matrix:
            # 变换动画占位
            pass

    elif gtype == "matrix_animation":
        # 矩阵动画占位
        pass

    elif gtype == "comparison":
        # 对比图形占位
        pass

    elif gtype == "image_effect":
        # 图像效果占位
        pass

    elif gtype == "physics":
        obj_type = params.get("object", "block")
        position = params.get("position", [0, 0])
        forces = params.get("forces", [])

        if obj_type == "block":
            block = Square(side_length=1, color=BLUE, fill_opacity=0.5)
            block.move_to(position)
            scene.play(Create(block))

            for force in forces:
                direction = force.get("direction")
                color = force.get("color", WHITE)
                if direction == "down":
                    arrow = Arrow(block.get_center(), block.get_center() + DOWN, color=color)
                elif direction == "up":
                    arrow = Arrow(block.get_center(), block.get_center() + UP, color=color)
                else:
                    arrow = Arrow(block.get_center(), block.get_center() + RIGHT, color=color)
                scene.play(GrowArrow(arrow))

    elif gtype == "three_d":
        # 3D 图形占位，需要 ThreeDScene 配合
        pass

    else:
        raise ValueError(f"未知的 graphics.type: {gtype}")


# 模板注册表（用于最大化匹配）
TEMPLATE_REGISTRY = {
    "highlight_matrix_cell": highlight_matrix_cell,
    "show_geometry": show_geometry,
    "animate_vector_transform": animate_vector_transform,
    "draw_angle": draw_angle,
    "add_equal_marks": add_equal_marks,
    "add_glow": add_glow,
    "highlight_conclusion": highlight_conclusion,
    "draw_graphics": draw_graphics,
}


def apply_template(scene, template_name: str, params: Dict[str, Any]) -> None:
    """通用模板调用接口"""
    if template_name in TEMPLATE_REGISTRY:
        TEMPLATE_REGISTRY[template_name](scene, params)
    else:
        raise ValueError(f"未找到模板: {template_name}")
