#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课程 JSON Schema 验证器 - 基于 references/json_schema.md

职责：
- 验证课程 JSON 文件的顶层结构
- 验证 atom 的必填字段和类型
- 验证 content 数组的 type 枚举值
- 验证 graphics 结构
- 验证 formula 类型中不包含中文
- 提供详细的错误报告

不验证范围（数理正确性）：
- 坐标值是否数学正确
- 几何关系是否成立
- 公式是否推导正确
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class ValidationError:
    """验证错误详情"""

    def __init__(self, path: str, field: str, message: str, value: Any = None):
        self.path = path
        self.field = field
        self.message = message
        self.value = value

    def __str__(self) -> str:
        value_str = f" (值: {self.value!r})" if self.value is not None else ""
        return f"[{self.path}] {self.field}: {self.message}{value_str}"


class CourseSchemaValidator:
    """课程 JSON Schema 验证器

    基于 references/json_schema.md 第 2 节定义

    使用示例：
        validator = CourseSchemaValidator()
        errors = validator.validate_file("courses/linear_programming_scene1.json")
        if errors:
            for err in errors:
                print(err)
            raise ValueError(f"JSON 验证失败，共 {len(errors)} 个错误")
    """

    # 合法的原子类型（json_schema.md 第 2.2 节）
    VALID_ATOM_TYPES = {
        "definition",
        "intuition",
        "operation",
        "counter_intuitive",
        "application",
        "summary",
    }

    # 合法的 content type（json_schema.md 第 2.4 节）
    VALID_CONTENT_TYPES = {"highlight", "content", "formula", "mixed"}

    # 兼容映射（json_schema.md 第 2.4 节）
    CONTENT_TYPE_ALIASES = {"text": "content", "title": "highlight"}

    # 合法的布局类型
    VALID_LAYOUT_TYPES = {"vertical", "two_column", "three_column", "centered"}

    # 合法的 graphics.type（技能枚举约束）
    VALID_GRAPHICS_TYPES = {
        "axes",
        "function",
        "polygon",
        "linear_algebra",
        "matrix_animation",
        "comparison",
        "image_effect",
        "physics",
        "three_d",
    }

    # 合法的 animation.type（技能枚举约束）
    VALID_ANIMATION_TYPES = {
        "fade_in",
        "typewriter",
        "highlight",
        "slide_in",
        "scale_in",
        "bounce",
        "blink",
    }

    # 中文正则
    CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")

    # MathTex/Tex 调用中 \text{} 包裹中文的正则（源码级扫描）
    # 匹配模式: MathTex(r"... \text{...中文...} ...") 或 Tex(r"... \text{...中文...} ...")
    CHINESE_IN_TEX_PATTERN = re.compile(
        r"(?:MathTex|Tex)\s*\(\s*r?[\"']([^\"]*\\text\s*\{[^\}]*[\u4e00-\u9fff][^\}]*\}[^\"]*)[\"']"
    )

    def validate_file(self, json_path: str) -> List[ValidationError]:
        """验证 JSON 文件

        Args:
            json_path: JSON 文件路径

        Returns:
            错误列表，空列表表示验证通过
        """
        path = Path(json_path)
        if not path.exists():
            return [ValidationError(str(path), "file", "文件不存在")]

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return [ValidationError(str(path), "json", f"JSON 解析失败: {e}")]

        return self.validate(data, path.name)

    def validate(
        self, data: Dict[str, Any], source: str = "data"
    ) -> List[ValidationError]:
        """验证课程数据

        Args:
            data: 解析后的 JSON 数据
            source: 数据源标识（用于错误报告）

        Returns:
            错误列表
        """
        errors = []

        # 顶层结构验证（json_schema.md 第 2.1 节）
        for field in ["topic", "version", "atoms"]:
            if field not in data:
                errors.append(ValidationError(source, field, "必填字段缺失"))

        if "topic" in data and not isinstance(data["topic"], str):
            errors.append(
                ValidationError(source, "topic", "类型应为 string", data["topic"])
            )

        if "version" in data and not isinstance(data["version"], str):
            errors.append(
                ValidationError(source, "version", "类型应为 string", data["version"])
            )

        if "prerequisites" in data:
            if not isinstance(data["prerequisites"], list):
                errors.append(
                    ValidationError(source, "prerequisites", "类型应为 array")
                )
            else:
                for i, item in enumerate(data["prerequisites"]):
                    if not isinstance(item, str):
                        errors.append(
                            ValidationError(
                                f"{source}.prerequisites[{i}]",
                                "item",
                                "类型应为 string",
                            )
                        )

        # atoms 验证
        if "atoms" in data:
            if not isinstance(data["atoms"], list):
                errors.append(ValidationError(source, "atoms", "类型应为 array"))
            else:
                for i, atom in enumerate(data["atoms"]):
                    atom_path = f"{source}.atoms[{i}]"
                    errors.extend(self._validate_atom(atom, atom_path))

        return errors

    def _validate_atom(self, atom: Dict[str, Any], path: str) -> List[ValidationError]:
        """验证单个原子对象

        Args:
            atom: 原子对象
            path: 路径标识

        Returns:
            错误列表
        """
        errors = []

        if not isinstance(atom, dict):
            return [ValidationError(path, "atom", "类型应为 object")]

        # 必填字段（json_schema.md 第 2.2 节）
        for field in ["id", "type", "content", "duration"]:
            if field not in atom:
                errors.append(ValidationError(path, field, "必填字段缺失"))

        # id 字段
        if "id" in atom and not isinstance(atom["id"], str):
            errors.append(ValidationError(path, "id", "类型应为 string"))

        # type 字段
        if "type" in atom:
            atom_type = atom["type"]
            if atom_type not in self.VALID_ATOM_TYPES:
                errors.append(
                    ValidationError(
                        path,
                        "type",
                        f"非法原子类型，应为 {sorted(self.VALID_ATOM_TYPES)} 之一",
                        atom_type,
                    )
                )

        # duration 字段：类型 + 范围 + 数值合理性校验
        if "duration" in atom:
            if not isinstance(atom["duration"], (int, float)):
                errors.append(ValidationError(path, "duration", "类型应为 number"))
            elif atom["duration"] <= 0:
                errors.append(
                    ValidationError(
                        path, "duration", "时长必须大于 0", atom["duration"]
                    )
                )
            elif atom["duration"] < 3.0:
                errors.append(
                    ValidationError(
                        path,
                        "duration",
                        f"时长 {atom['duration']}s 小于最小值 3.0s（语音朗读最低需求）",
                        atom["duration"],
                    )
                )
            elif atom["duration"] > 20.0:
                errors.append(
                    ValidationError(
                        path,
                        "duration",
                        f"时长 {atom['duration']}s 超过最大值 20.0s（应拆分原子）",
                        atom["duration"],
                    )
                )

            # duration 与 speech 字符数的匹配度校验
            # 计算公式: expected_duration = ceil(len(speech) / SPEECH_SPEED)
            # SPEECH_SPEED = 4.0 字符/秒，允许 ±3 秒误差（含动画缓冲）
            if "speech" in atom and isinstance(atom["speech"], str):
                speech_len = len(atom["speech"].strip())
                if speech_len > 0:
                    expected = max(speech_len / 4.0, 3.0)
                    actual = float(atom["duration"])
                    tolerance = 3.0  # 允许 ±3 秒误差（含动画过渡/停顿缓冲）
                    if abs(actual - expected) > tolerance:
                        errors.append(
                            ValidationError(
                                path,
                                "duration",
                                (
                                    f"与 speech 长度不匹配: "
                                    f"实际={actual:.1f}s, "
                                    f"期望≈{expected:.1f}s "
                                    f"({speech_len}字符 / 4字符每秒)"
                                ),
                                actual,
                            )
                        )

        # layout 字段（可选）
        if "layout" in atom:
            if atom["layout"] not in self.VALID_LAYOUT_TYPES:
                errors.append(
                    ValidationError(
                        path,
                        "layout",
                        f"非法布局类型，应为 {sorted(self.VALID_LAYOUT_TYPES)} 之一",
                        atom["layout"],
                    )
                )

        # speech 字段（可选）
        if "speech" in atom and not isinstance(atom["speech"], str):
            errors.append(ValidationError(path, "speech", "类型应为 string"))

        # content 数组验证
        if "content" in atom:
            content = atom["content"]
            if not isinstance(content, list):
                errors.append(ValidationError(path, "content", "类型应为 array"))
            elif len(content) == 0:
                errors.append(ValidationError(path, "content", "内容数组不能为空"))
            else:
                for j, item in enumerate(content):
                    item_path = f"{path}.content[{j}]"
                    errors.extend(self._validate_content_item(item, item_path))

        # graphics 字段（可选）
        if "graphics" in atom:
            graphics = atom["graphics"]
            if not isinstance(graphics, dict):
                errors.append(ValidationError(path, "graphics", "类型应为 object"))
            else:
                if "type" not in graphics:
                    errors.append(
                        ValidationError(f"{path}.graphics", "type", "必填字段缺失")
                    )
                elif graphics["type"] not in self.VALID_GRAPHICS_TYPES:
                    errors.append(
                        ValidationError(
                            f"{path}.graphics.type",
                            "type",
                            f"非法 graphics 类型，应为 {sorted(self.VALID_GRAPHICS_TYPES)} 之一",
                            graphics["type"],
                        )
                    )
                if "params" not in graphics:
                    errors.append(
                        ValidationError(f"{path}.graphics", "params", "必填字段缺失")
                    )
                elif not isinstance(graphics["params"], dict):
                    errors.append(
                        ValidationError(
                            f"{path}.graphics.params", "params", "类型应为 object"
                        )
                    )

        # animation 字段（可选，技能枚举约束）
        if "animation" in atom:
            animation = atom["animation"]
            if not isinstance(animation, dict):
                errors.append(ValidationError(path, "animation", "类型应为 object"))
            elif "type" in animation:
                if animation["type"] not in self.VALID_ANIMATION_TYPES:
                    errors.append(
                        ValidationError(
                            f"{path}.animation.type",
                            "type",
                            f"非法 animation 类型，应为 {sorted(self.VALID_ANIMATION_TYPES)} 之一",
                            animation["type"],
                        )
                    )

        return errors

    def _validate_content_item(
        self, item: Dict[str, Any], path: str
    ) -> List[ValidationError]:
        """验证 content 数组中的单个元素

        Args:
            item: content 元素
            path: 路径标识

        Returns:
            错误列表
        """
        errors = []

        if not isinstance(item, dict):
            return [ValidationError(path, "item", "类型应为 object")]

        # 必填字段（json_schema.md 第 2.3 节）
        for field in ["text", "type"]:
            if field not in item:
                errors.append(ValidationError(path, field, "必填字段缺失"))

        # type 验证
        if "type" in item:
            item_type = item["type"]

            # 兼容映射
            if item_type in self.CONTENT_TYPE_ALIASES:
                item_type = self.CONTENT_TYPE_ALIASES[item_type]

            if item_type not in self.VALID_CONTENT_TYPES:
                errors.append(
                    ValidationError(
                        path,
                        "type",
                        f"非法 content 类型，应为 {sorted(self.VALID_CONTENT_TYPES)} 之一",
                        item["type"],
                    )
                )

            # formula 类型禁止包含中文（json_schema.md 第 2.5 节）
            if item_type == "formula" and "text" in item:
                if self.CHINESE_RE.search(item["text"]):
                    errors.append(
                        ValidationError(
                            path,
                            "text",
                            "formula 类型禁止包含中文字符，请使用 mixed 类型 + tex_template: ctex",
                        )
                    )

        # text 字段
        if "text" in item and not isinstance(item["text"], str):
            errors.append(ValidationError(path, "text", "类型应为 string"))

        return errors

    def validate_and_report(self, json_path: str) -> str:
        """验证并生成人类可读的报告

        Args:
            json_path: JSON 文件路径

        Returns:
            报告字符串
        """
        errors = self.validate_file(json_path)

        if not errors:
            return f"✅ {json_path} 验证通过"

        lines = [f"❌ {json_path} 验证失败，共 {len(errors)} 个错误："]
        for err in errors:
            lines.append(f"  - {err}")

        return "\n".join(lines)

    # ================================================================
    # 源码级校验（G2.5：LaTeX 合规性前置检查）
    # ================================================================

    def validate_source_file(self, source_path: str) -> List[ValidationError]:
        """扫描 Python 源码中的 MathTex/Tex 中文污染

        检测规则（json_schema.md §2.5）：
        - 禁止在 MathTex() / Tex() 的参数字符串中出现 \text{...中文...}
        - 正确做法：中文使用 Text() 渲染，或拆分为 mixed 类型 + ctex 模板

        Args:
            source_path: Python 源码文件路径（如 content/xxx.py）

        Returns:
            错误列表，空表示无违规
        """
        path = Path(source_path)
        if not path.exists():
            return [ValidationError(str(path), "file", "源码文件不存在")]

        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            return [ValidationError(str(path), "file", f"读取失败: {e}")]

        errors = []
        lines = source.split("\n")

        for line_no, line in enumerate(lines, 1):
            # 跳过注释行
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            matches = self.CHINESE_IN_TEX_PATTERN.findall(line)
            for matched_tex in matches:
                # 提取 \text{} 中的中文内容用于报告
                text_match = re.search(r"\\text\s*\{([^}]*(?:[\u4e00-\u9fff])[^}]*)\}", matched_tex)
                chinese_content = text_match.group(1) if text_match else "(提取失败)"

                errors.append(
                    ValidationError(
                        f"{source_path}:{line_no}",
                        "CHINESE_IN_TEX_VIOLATION",
                        (
                            f"MathTex/Tex 参数中包含中文 "
                            f"(应使用 Text() 或 mixed+ctex 替代)"
                        ),
                        f"\\text{{{chinese_content}}}",
                    )
                )

        return errors

    def validate_source_and_report(self, source_path: str) -> str:
        """扫描源码并生成人类可读的报告

        Args:
            source_path: Python 源码路径

        Returns:
            报告字符串
        """
        errors = self.validate_source_file(source_path)

        if not errors:
            return f"✅ {source_path} 源码 LaTeX 合规性检查通过"

        lines = [f"❌ {source_path} 发现 {len(errors)} 处中文混入 MathTex/Tex："]
        for err in errors:
            lines.append(f"  - {err}")

        return "\n".join(lines)
