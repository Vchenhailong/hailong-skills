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
        "definition", "intuition", "operation",
        "counter_intuitive", "application", "summary",
    }
    
    # 合法的 content type（json_schema.md 第 2.4 节）
    VALID_CONTENT_TYPES = {"highlight", "content", "formula", "mixed"}
    
    # 兼容映射（json_schema.md 第 2.4 节）
    CONTENT_TYPE_ALIASES = {"text": "content", "title": "highlight"}
    
    # 合法的布局类型
    VALID_LAYOUT_TYPES = {"vertical", "two_column", "three_column", "centered"}
    
    # 合法的 graphics.type（技能枚举约束）
    VALID_GRAPHICS_TYPES = {
        "axes", "function", "polygon", "linear_algebra",
        "matrix_animation", "comparison", "image_effect",
        "physics", "three_d",
    }
    
    # 合法的 animation.type（技能枚举约束）
    VALID_ANIMATION_TYPES = {
        "fade_in", "typewriter", "highlight", "slide_in",
        "scale_in", "bounce", "blink",
    }
    
    # 中文正则
    CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
    
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
    
    def validate(self, data: Dict[str, Any], source: str = "data") -> List[ValidationError]:
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
            errors.append(ValidationError(source, "topic", "类型应为 string", data["topic"]))
        
        if "version" in data and not isinstance(data["version"], str):
            errors.append(ValidationError(source, "version", "类型应为 string", data["version"]))
        
        if "prerequisites" in data:
            if not isinstance(data["prerequisites"], list):
                errors.append(ValidationError(source, "prerequisites", "类型应为 array"))
            else:
                for i, item in enumerate(data["prerequisites"]):
                    if not isinstance(item, str):
                        errors.append(ValidationError(f"{source}.prerequisites[{i}]", "item", "类型应为 string"))
        
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
                errors.append(ValidationError(path, "type",
                    f"非法原子类型，应为 {sorted(self.VALID_ATOM_TYPES)} 之一", atom_type))
        
        # duration 字段
        if "duration" in atom:
            if not isinstance(atom["duration"], (int, float)):
                errors.append(ValidationError(path, "duration", "类型应为 number"))
            elif atom["duration"] <= 0:
                errors.append(ValidationError(path, "duration", "时长必须大于 0", atom["duration"]))
        
        # layout 字段（可选）
        if "layout" in atom:
            if atom["layout"] not in self.VALID_LAYOUT_TYPES:
                errors.append(ValidationError(path, "layout",
                    f"非法布局类型，应为 {sorted(self.VALID_LAYOUT_TYPES)} 之一", atom["layout"]))
        
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
                    errors.append(ValidationError(f"{path}.graphics", "type", "必填字段缺失"))
                elif graphics["type"] not in self.VALID_GRAPHICS_TYPES:
                    errors.append(ValidationError(f"{path}.graphics.type", "type",
                        f"非法 graphics 类型，应为 {sorted(self.VALID_GRAPHICS_TYPES)} 之一", graphics["type"]))
                if "params" not in graphics:
                    errors.append(ValidationError(f"{path}.graphics", "params", "必填字段缺失"))
                elif not isinstance(graphics["params"], dict):
                    errors.append(ValidationError(f"{path}.graphics.params", "params", "类型应为 object"))
        
        # animation 字段（可选，技能枚举约束）
        if "animation" in atom:
            animation = atom["animation"]
            if not isinstance(animation, dict):
                errors.append(ValidationError(path, "animation", "类型应为 object"))
            elif "type" in animation:
                if animation["type"] not in self.VALID_ANIMATION_TYPES:
                    errors.append(ValidationError(f"{path}.animation.type", "type",
                        f"非法 animation 类型，应为 {sorted(self.VALID_ANIMATION_TYPES)} 之一", animation["type"]))
        
        return errors
    
    def _validate_content_item(self, item: Dict[str, Any], path: str) -> List[ValidationError]:
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
                errors.append(ValidationError(path, "type",
                    f"非法 content 类型，应为 {sorted(self.VALID_CONTENT_TYPES)} 之一", item["type"]))
            
            # formula 类型禁止包含中文（json_schema.md 第 2.5 节）
            if item_type == "formula" and "text" in item:
                if self.CHINESE_RE.search(item["text"]):
                    errors.append(ValidationError(path, "text",
                        "formula 类型中禁止包含中文字符，请拆分为 content + formula"))
        
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
