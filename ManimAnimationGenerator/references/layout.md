# 布局规范

> 预期布局见 https://excalidraw.com/#json=O-vBchO387w-jxxVxpFe6,lWFiW8UU6aHjTDFOKF4HlA
> 也可以见技能中的 `references/layout_concept.html` 文件

## 1. 布局方法优先级（强制执行）

### 1.0 核心原则：按需组装，而非自动依赖

> **重要**：`create_*` 工厂函数只负责创建**单个元件**，最终的布局组装需要根据实际场景手动调整。这是 Manim 动画制作的通用最佳实践。

| 场景             | 推荐方式     | 说明                                         |
| ---------------- | ------------ | -------------------------------------------- |
| **任意图元绘制** | **手动组装** | 显式创建每个元件、连接线和节点，完全控制布局 |
| 力学示意图       | 手动组装     | 小车、斜面、杠杆等需要精确放置               |
| 电路图           | 手动组装     | 串并联混合、开关、仪表等复杂连接             |
| 复杂几何图形     | 手动组装     | 确保各部件位置关系正确                       |

**为什么推荐手动组装？**

1. **精确控制**：每个元件的位置、旋转、间距都可以精确设置
2. **灵活适配**：不同场景需要不同的布局，手动组装可以随时调整
3. **易于调试**：哪里不对改哪里，不用担心工厂函数的内部逻辑

### 1.1 允许的方法

1. VGroup.arrange() - 首选，自动排列子元素
   使用 VGroup 将多个元素组合，然后调用 arrange() 方法按照指定方向和间距排列

2. VGroup 嵌套 + arrange() - 实现复杂布局
   先分别排列各列，再将列组合并排列

3. .shift() - 仅允许用于整体位置调整（如将整个 VGroup 移动到起始高度），禁止对单个元素使用
   仅允许对整体 VGroup 使用 shift() 进行位置调整

4. **直接指定坐标** - 用于精确放置元件
   渲染代码示例：根据场景需要，直接指定元件位置参数（如斜面上元件的底部中心坐标）

### 1.2 严禁的方法（禁止使用）

- .next_to() - 禁止
- .align_to() - 禁止
- .move_to() - 禁止（纯标题场景除外）
- 直接赋值坐标（如 .set_x()、.set_y()、.move_to([x,y,z])）- 禁止
- 对单个元素使用 .shift() - 禁止

### 1.3 唯一例外

- 纯标题场景：标题整体居中允许（整体居中）
- 字幕区：由系统自动定位，无需手动设置

## 2. 布局安全区域（强制）

> 设计的核心规则：
> 标准 16:9 配置
> 安全区：Y ∈ [safe_y_min, safe_y_max]（上下边距对称，frame_height=8，safe_h=7.2）
> 三区（标题+主内容+字幕）：标题 20% / 主内容 70% / 字幕 10%
> 两区（主内容+字幕，无标题）：主内容 90% / 字幕 10%

- 标准 16:9 配置：`config.frame_height=8, frame_width≈14.22`，中心原点
- 安全区域：X ∈ [safe_x_min, safe_x_max]，Y ∈ [safe_y_min, safe_y_max]（正负对称，safe_h=7.2）
- 字幕专用区：Y ∈ [safe_y_min, safe_y_min + safe_h×10%]（由 compute() 动态计算）
- 所有教学内容的最低 Y ≥ safe_y_min + safe_h×10%
- 布局安全区域基于 16:9 比例，通过 `ZoneConstants.compute()` 动态计算

## 3. 分区布局与顶部居中规范（强制）

### 3.1 安全边界定义

标准配置 `config.frame_height=8`（16:9），中心原点 `(0, 0)`

**边界公式**（确定性推导）：

```
屏幕边界 = ±(frame_width/2, frame_height/2)

安全区 X = ±(frame_width/2 × (1 - MARGIN_RATIO_X × 2))
         = ±(frame_width/2 × 94.94%)
         = ±safe_x_max

安全区 Y = ±(frame_height/2 - MARGIN_Y)
         = ±safe_y_max

其中：
  - MARGIN_RATIO_X = 2.53%（水平边距比例）
  - MARGIN_Y = 0.4（垂直对称边距）
  - safe_h = frame_height - 2 × MARGIN_Y = 7.2
```

**区域边界表**（通过 `ZoneConstants.compute()` 动态计算）：

```
| 边界 | 公式 | 说明 |
|------|------|------|
| 屏幕边界 | ±(frame_width/2, frame_height/2) | 全屏范围（固定原点） |
| 安全区域 | X ∈ [±(frame_width/2 × 94.94%)], Y ∈ [±safe_h/2] | 内容安全区 |
| 字幕区 | X ∈ 同安全区, Y ∈ [safe_y_min, safe_y_min + safe_h×10%] | 字幕专用 |
| 主内容区 | X ∈ [safe_x_min, two_left_x_max] | 公式/文字（两栏时） |
| 图形区 | X ∈ [two_right_x_min, safe_x_max] | 图形（两栏时） |
```

> **安全区中心 = ORIGIN = (0, 0)**，所有偏移量相对于此原点计算。

### 3.2 区域划分

```
| 区域 | 对齐方式 | 默认 Y 位置 | 说明 |
|------|----------|-------------|------|
| 标题区 | 居中 | Y = title_zone_center | 视频标题、章节标题 |
| 副标题区 | 居中 | Y = subtitle_zone_center | 阶段说明、子标题 |
| 主内容区 | 居中左对齐 | 第一个元素 Y ≈ title_zone_center - safe_h×20% | 公式、推导步骤、文字说明 |
| 图形区 | 居中 | 与主内容区顶部对齐 | 几何图形、坐标系、图表 |
| 字幕区 | 居中（系统自动） | Y = subtitle_zone_center（2行 + 行间距） | 语音字幕（固定，防止抖动） |
```

### 3.3 布局整体示意图

```
+--------------------------------------------------------------------+
|                          标题区（居中）                          |  Y = title_zone_center
|                          副标题区（居中）                        |  Y = subtitle_zone_center
+----------------------------------+--------------------------------+
|                                  |                                |
|          主内容区                |            图形区              |
|        （居中左对齐）            |            （居中）             |
|                                  |                                |
|       X ∈ [safe_x_min,          |       X ∈ [two_right_x_min,   |
|              two_left_x_max]     |              safe_x_max]       |
|       Y ∈ [content_y_min,       |       Y ∈ [content_y_min,    |
|              content_y_max]      |              content_y_max]    |
|                                  |                                |
+----------------------------------+--------------------------------+
|                          字幕区（居中）                              |  Y = subtitle_zone_center
+--------------------------------------------------------------------+
```

> 坐标通过 `ZoneConstants.compute()` 动态计算。标准 16:9 配置下：safe_x_min ≈ -6.75, two_left_x_max ≈ 1.35。

### 3.4 单栏布局

当无图形或无需分栏时，主内容区使用全安全区，单栏布局：

```
+--------------------------------------------------------------------+
|                          标题区（居中）                          |  Y = title_zone_center
|                          副标题区（居中）                        |  Y = subtitle_zone_center
+--------------------------------------------------------------------+
|                                                                    |
|                        主内容区（居中）                            |
|                        X ∈ [safe_x_min, safe_x_max]               |
|                        Y ∈ [content_y_min, content_y_max]          |
|                                                                    |
+--------------------------------------------------------------------+
|                          字幕区（居中）                              |  Y = subtitle_zone_center
+--------------------------------------------------------------------+
```

单栏模式字体大小：

- 主公式/正文：32
- 标题重点：40
- 副标题：34
- 字幕：**统一 18**（单栏/两栏/三栏均为 18px）

### 3.5 两栏布局

当同时有文字内容和图形时，分为左右两栏（**有图形时**：左 60%、右 40%，无图形时：优先均分 50%/50%，其次按内容动态）：

```
+----------------------------------+--------------------------------+
|                                  |                                |
|          主内容区                |            图形区              |
|        （居中左对齐）            |            （居中）             |
|                                  |                                |
|       X ∈ [safe_x_min,         |       X ∈ [two_right_x_min,   |
|              two_left_x_max]     |              safe_x_max]       |
|       Y ∈ [content_y_min,     |       Y ∈ [content_y_min,      |
|              content_y_max]      |              content_y_max]   |
|                                  |                                |
+-------------------+--------------+--------------------------------+
|                          字幕区（居中）                              |  Y = subtitle_zone_center
+--------------------------------------------------------------------+
```

两栏模式字体大小：

- 主公式/正文：32
- 标题重点：40
- 副标题：34
- 图形区标注：**统一 22**（两栏/三栏均为 22px）
- 字幕：**统一 18**（单栏/两栏/三栏均为 18px）

两栏宽度比例（可JSON覆盖）：有图形时默认左 60%、右 40%；无图形时默认均分 50%/50%

### 3.6 三栏布局

当需要步骤说明、公式、图形三者同时展示时，分为三栏（**有图形时**：左 30%、中 30%、右 40%，无图形时：优先均分 1/3 各栏，其次按内容动态）：

```
+-------------------+--------------------+-------------------------+
|                   |                    |                         |
|      左栏         |       中栏          |        右栏             |
|   （步骤说明）    |      （公式）       |      （图形）           |
|                   |                    |                         |
| X ∈ [safe_x_min,       | X ∈ [three_mid_x_min,    | X ∈ [three_right_x_min,    |
|       three_left_x_max] |       three_mid_x_max]   |       safe_x_max]           |
| Y ∈ [content_y_min,   | Y ∈ [content_y_min,      | Y ∈ [content_y_min,        |
|       content_y_max]   |       content_y_max]     |       content_y_max]        |
|                   |                    |                         |
+-------------------+--------------------+-------------------------+
|                          字幕区（居中）                              |  Y = subtitle_zone_center
+--------------------------------------------------------------------+
```

三栏模式字体大小：

- 左栏（步骤说明）：28
- 中栏（公式）：28
- 右栏（图形标注）：**统一 22**（两栏/三栏均为 22px）
- 标题重点：40
- 副标题：34
- 字幕：**统一 18**（单栏/两栏/三栏均为 18px）

三栏宽度比例（可JSON覆盖）：有图形时默认左 30%、中 30%、右 40%；无图形时默认均分 1/3 各栏
三栏内容分配：左栏概念/文字说明，中栏公式，右栏图形/应用

### 3.7 默认布局规则

**绝大多数场景**：主内容区 + 字幕区（标题/副标题通常不与主内容共存）

**过渡场景**：仅标题（垂直居中，Y = 0）

### 3.8 区域显示规则（兼容）

- 无主内容时（如纯标题过渡页）：标题/副标题整体垂直居中（Y = 0）
- 无标题时：副标题上移到 Y = title_zone_center，主内容上移到 Y = content_y_max
- 无副标题时：标题与主内容间距缩小至 0.8 单位
- 无图形时：两栏/三栏自动降级为单栏
- 无公式时：三栏自动降级为两栏

### 3.9 标题区单独场景规则（强制）

当场景仅包含标题（无主内容、无图形、无字幕）时：

- 标题独立为一个场景
- 标题整体垂直居中（Y = 0），而非顶部居中
- 标题字体大小：40px
- 标题颜色：#66DDFF
- 标题动画：Write 或 FadeIn
- 场景时长：2-3 秒（不包含语音）

实现模板：

```
title = Text("标题", font_size=40, color="#66DDFF")
title.move_to(ORIGIN)
self.play(Write(title), run_time=1.5)
self.wait(1.0)
self.play(FadeOut(title), run_time=0.5)
```

### 3.10 字幕区高度规范

**字体到坐标单位换算**：

```
标题区高度 = max(安全区高 × 2/10, Text(font_size=40).height)
字幕区高度 = max(安全区高 × 1/10, Text(font_size=18).height)
```

**动态计算**（ZoneConstants.compute(frame_width, frame_height)）：

```
总窗口 = (config.frame_width, config.frame_height)
安全区 = 总窗口 - 边距比例 × 2          （MARGIN_RATIO = 5%）
标题区高 = max(安全区高 × 20%, 实测标题文字高度)
字幕区高 = max(安全区高 × 10%, 实测字幕文字高度)
内容区高 = 安全区高 - 标题高 - 字幕高 - 间距
```

> 不可使用 font_size × (8/72) × 1.15 等经验公式估算文字高度，Manim 映射比例随分辨率动态变化。应使用 Text().height 实测。

**安全区域内比例规则**（标准 16:9 配置 frame_height=8, frame_width≈14.22）：

| 模式                     | 标题:内容:字幕 | 字幕占比   | 字幕高度     | 字幕范围                            | 内容高度     |
| ------------------------ | -------------- | ---------- | ------------ | ----------------------------------- | ------------ |
| 三区（标题+主内容+字幕） | 2:7:1          | 1/10 = 10% | safe_h × 10% | Y ∈ [safe_y_min, content_y_min]     | safe_h × 70% |
| 两区（主内容+字幕）      | —:9:1          | 1/10 = 10% | safe_h × 10% | Y ∈ [safe_y_min, content_y_min_two] | safe_h × 90% |

> **说明**：字幕区高度取"比例值（安全区×10%）"和"实测文字高度"两者的较大值，确保比例规范和内容不被截断均满足。上表为标准配置下的计算结果，非固定常量——使用 ZoneConstants.compute() 动态获取。

### 3.11 标题区位置规则汇总

```
| 场景类型 | 标题 Y 位置 | 副标题 Y 位置 | 主内容起始 Y |
|----------|-------------|---------------|--------------|
| 单独标题 | 0（垂直居中） | — | — |
| 标题 + 副标题（无主内容） | 整体垂直居中 | 整体垂直居中 | — |
| 标题 + 主内容 | title_zone_center | subtitle_zone_center | content_y_max |
| 标题 + 副标题 + 主内容 | title_zone_center | subtitle_zone_center | content_y_max |
| 无标题 | — | title_zone_center | content_y_max_two |
```

### 3.12 主内容顶部居中的实现

单栏模式：

```python
content = VGroup(*objects).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
content.move_to(ORIGIN).align_to(ORIGIN, UP)
content.shift(UP * 2.0)
content.shift(LEFT * 3.0)  # 居中左对齐
self.play(FadeIn(content))
```

两栏模式：

```python
left_column = VGroup(*texts).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
right_column = VGroup(*graphics).arrange(DOWN, buff=0.6, center=True)

left_column.move_to(ORIGIN).align_to(ORIGIN, UP).shift(UP * 2.0)
left_column.shift(LEFT * 3.5)

right_column.move_to(ORIGIN).align_to(ORIGIN, UP).shift(UP * 2.0)
right_column.shift(RIGHT * 3.5)

self.play(FadeIn(left_column), FadeIn(right_column))
```

三栏模式：

```python
left_col = VGroup(*steps).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
mid_col = VGroup(*formulas).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
right_col = VGroup(*graphics).arrange(DOWN, buff=0.6, center=True)

left_col.move_to(ORIGIN).align_to(ORIGIN, UP).shift(UP * 2.0).shift(LEFT * 4.5)
mid_col.move_to(ORIGIN).align_to(ORIGIN, UP).shift(UP * 2.0)
right_col.move_to(ORIGIN).align_to(ORIGIN, UP).shift(UP * 2.0).shift(RIGHT * 4.5)

self.play(FadeIn(left_col), FadeIn(mid_col), FadeIn(right_col))
```

纯标题过渡页：
title = Text("标题", font_size=40)
title.move_to(ORIGIN)
self.play(FadeIn(title))

### 3.13 验证清单

- 主内容区居中左对齐（非整体居中）
- 图形区在右侧（两栏/三栏模式时）
- 主内容区与图形区顶部对齐
- 标题和副标题居中
- 内容未超出安全边界
- 字体大小符合分栏模式要求
- 单独标题场景整体垂直居中

## 4. 分栏模式

### 4.1 何时使用分栏

- 内容同时包含：图形 + 公式推导 + 文字说明
- 左侧图形区：几何图形、坐标系、图表
- 总元素超过 8 个，单栏排列会导致溢出
- 需要对比展示（如左右对比、前后步骤对比）

### 4.2 分栏模式

**宽度比例规则**：

- 两栏（**有图形时**）：默认**左 60%、右 40%**（无图形时：优先均分 50%/50%，其次按内容动态）
- 三栏（**有图形时**）：默认**左 30%、中 30%、右 40%**（无图形时：优先均分 1/3 各栏，其次按内容动态）
- 所有比例均可在 JSON 中通过 col_ratio 覆盖

**固定间距**：栏间至少 0.5 单位空白，防止视觉粘连

```
| 模式 | 栏数 | 典型用途 | 宽度分配（X 范围） | 比例 |
|------|------|----------|-------------------|------|
| 单栏 | 1 | 纯推导、纯图形 | 全宽 [safe_x_min, safe_x_max] | — |
| 两栏 | 2 | 图形（右）+ 推导/文字（左） | 左 [safe_x_min, two_left_x_max]，右 [two_right_x_min, safe_x_max] | 60% / 40% |
| 三栏 | 3 | 步骤说明（左）+ 公式（中）+ 图形（右） | 左 [safe_x_min, three_left_x_max]，中 [three_mid_x_min, three_mid_x_max]，右 [three_right_x_min, safe_x_max] | 30% / 30% / 40% |
| 两栏对比 | 2 (并列) | 前后对比、错误 vs 正确 | 左 [safe_x_min, 两栏对比左_x_max]，右 [两栏对比右_x_min, safe_x_max] | 50% / 50% |
```

### 4.3 栏间间距规范

- 栏与栏之间至少保留 0.5 单位空白（防止内容视觉粘连）
- 相邻栏的内容不可跨栏（禁止箭头跨越复杂连接，除非使用连线）

### 4.4 动态切换栏数

- 同一视频的不同阶段可使用不同栏数
- 切换时使用 FadeOut + FadeIn 过渡，避免内容混淆

### 4.5 分栏时的防重叠规则

- 每栏内部独立使用 next_to 纵向排列，栏间不重叠由 X 范围保证
- 若某一栏内容溢出安全区域（Y < safe_y_min + safe_h×10% 或 Y > safe_y_max），仅该栏执行分组刷新，不影响其他栏
- 右侧图形区溢出时优先缩放，左侧文字区溢出时优先拆分步骤

### 4.6 分栏遵循的优先级

- 内容逻辑优先于美观：若分栏导致内容割裂（如公式被拆到两栏），优先使用单栏或重新组织
- 手机/小屏幕兼容：若渲染目标为 16:9，分栏安全；若为 4:3，建议只用两栏

### 4.7 分栏时的顶部居中规则（强制）

1. 每栏内部：内容从顶部开始排列（首个元素 Y ≈ content_y_max）
2. 栏间对齐：所有栏的顶部位置必须一致（使用 align_to() 实现）
3. 水平分布：多栏组合整体水平居中，栏间距 >= 0.5 单位
4. 高度独立：各栏高度可不同，不影响顶部对齐

### 4.8 两栏布局代码示例

两栏布局：各自从顶部开始，顶部对齐

```
left_col = VGroup(formula1, formula2).arrange(DOWN, buff=0.6, center=True)
right_col = VGroup(graph1, graph2).arrange(DOWN, buff=0.6, center=True)
```

各自顶部对齐

```
left_col.move_to(ORIGIN).align_to(ORIGIN, UP).shift(UP * 2.0)
right_col.move_to(ORIGIN).align_to(ORIGIN, UP).shift(UP * 2.0)
```

水平定位

```
left_col.align_to(ORIGIN, LEFT).shift(LEFT * 3.5)
right_col.align_to(ORIGIN, RIGHT).shift(RIGHT * 3.5)

self.play(FadeIn(left_col), FadeIn(right_col))
```

### 4.9 三栏布局典型示例（矩阵乘法讲解）

```
| 栏位 | 内容 | 宽度 | X 范围 |
|------|------|------|--------|
| 左栏 | 操作步骤编号 | safe_w × 30% | [safe_x_min, three_left_x_max] |
| 中栏 | 公式 | safe_w × 30% | [three_mid_x_min, three_mid_x_max] |
| 右栏 | 矩阵图形 | safe_w × 40% | [three_right_x_min, safe_x_max] |
```

> 宽度和坐标由 `ZoneConstants.compute()` 动态计算。

### 4.10 图形占分栏 80% 规则（强制）

**核心原则**：图形（受力分析图、几何图、坐标系、示意图等）始终占分栏宽高的 **80%**，取宽/高限制中较小者确保不溢出边界

**具体要求**：

1. **宽度适配**：图形的整体宽度应接近分栏内边距宽度，不得显著小于分栏宽度（浪费空间）
2. **高度适配**：图形高度应在分栏高度范围内尽量撑满，不得只占一小部分（如图中车只占 10% 高度）
3. **缩放策略**：直接计算缩放系数，使图形最终占分栏宽高的 **80%**（取宽/高限制中较小者，确保不溢出边界）。除零时保持原尺寸
4. **标注空间**：缩放时同步放大标注字号，保持标注与图形的比例协调

**实现方式**：

```python
# 获取分栏坐标
graphics_zone = scene.get_graphics_zone()
zone_w = graphics_zone.x_max - graphics_zone.x_min
zone_h = graphics_zone.y_max - graphics_zone.y_min

# 获取图形原始尺寸
fig_w, fig_h = graphic.width, graphic.height

# 直接缩放至分栏宽高的 80%（取宽/高限制中较小者，确保不溢出边界）
scale = min(zone_w * 0.80 / fig_w, zone_h * 0.80 / fig_h) if fig_w > 1e-6 and fig_h > 1e-6 else 1.0

# scale 在 0.5~1.0 之间：不缩小，保留原始尺寸
if scale != 1.0:
    graphic.scale(scale, about_point=graphic.get_center())
    graphic.move_to(graphics_zone.get_center())
```

> **注意**：此规则仅适用于图形区（GRAPHICS）；主内容区（文字/公式）以内容自然尺寸为准，无需应用此缩放规则。

## 5. 字体大小

### 5.1 基础字体

```
| 元素 | 字体大小 | 说明 |
|------|----------|------|
| 标题重点 | 40 | 视频标题、章节标题 |
| 副标题 | 34 | 阶段说明、子标题 |
| 字幕 | 18 | 语音字幕（固定） |
```

### 5.2 分栏模式字体（主内容区）

```
| 布局模式 | 左栏（步骤/说明） | 中栏（公式） | 右栏（图形/标注） |
|----------|------------------|-------------|------------------|
| 单栏 | 32 | 32 | -- |
| 两栏 | 30 | 32 | 28 |
| 三栏 | 28 | 28 | 24 |

注：字幕统一使用 18px（不随分栏模式变化）
```

### 5.3 字体调整规则

- 分栏越多，字体适当减小，确保内容不溢出
- 公式字体（中栏）始终不小于其他栏
- 图形标注字体可适当小于公式字体

## 6. 元素间距

- 行间距 >= 0.6，元素间距 >= 0.3
- 使用 arrange(DOWN, buff=0.6) 等相对定位
- 元素间距指不同内容块之间的垂直距离，不包括同一公式内部的行距

## 7. 防止内容重叠与溢出（AI 必须实现运行时动态调整）

- 生成代码时，调用 `scripts/layout/scene_base.py` 中 `LayoutScene` 的方法，在 construct 开始时虚拟测量所有元素的包围盒
- 若任何元素底部 < safe_y_min + safe_h×10%，整体上移；若顶部 > safe_y_max，整体缩放（优先缩小，字体不小于 24）
- 若仍溢出，触发分组刷新（FadeOut 老旧内容组）
- 具体实现见 `scripts/layout/scene_base.py` 中 `LayoutScene` 的 `safe_place()` / `place_two_column()` / `place_three_column()` 与 `validate_layout()` 方法

### 7.1 坐标系特殊规则（优先级高于普通防重叠）

#### 1. 坐标系绘制规范

- 画布中心为逻辑原点 (0,0)，X 右正 Y 上正。
- 所有坐标由数学公式推导，生成顺序：基准原点 -> 顶点 -> 中点 -> 交点/切点 -> 辅助点。
- 中点 = 两点算术平均；交点 = 联立方程求解；切点 = 垂直/距离条件。
- 禁止硬编码、视觉估算。

#### 2. 坐标轴范围

- 轴范围必须超出图形内容边界：左 <= 图形最小 X - 1.0，右 >= 最大 X + 1.0；下 <= 最小 Y - 0.8，上 >= 最大 Y + 1.0。

#### 3. 坐标轴标签

- 轴末端标注 x, y（字号 22），原点标 O。
- 关键整数刻度点必须标注数字（字号 22，颜色 #CCCCCC），刻度线长 0.1。
- 可选网格线（#333333，透明度 0.5，密度 1 单位）。

#### 4. 坐标系作为背景层

- 坐标轴线和网格线不属于教学内容，不参与普通元素的间距计算（即不与轴线检测重叠）。

#### 5. 轴线可进入字幕区

- 轴线超出图形范围的规则优先于字幕专用区（Y >= safe_y_min + safe_h×10%），但轴线末端的 x、y 标签（字号 22）和刻度数字（字号 22）不得进入字幕区。

#### 6. 与轴线标签重叠的处理

- 若普通元素（公式、图形、标注）与坐标轴标签（x、y、刻度数字）重叠，必须平移或缩放普通元素，确保不与标签重叠（标签视为前景）。

#### 7. 坐标轴标签的固定位置

- x 轴标签：默认在 (图形最大X + 0.5, -3.0)
- y 轴标签：默认在 (-0.5, 图形最大Y + 0.4)
- 刻度数字：紧贴刻度线外侧（正方向外侧偏移 0.1 单位）

#### 8. 位置关系验证

- 两点重合、三点共线、平行/垂直、直线与圆相切等必须先联立判断，后绘图。

#### 9. 几何关系验证

- 距离、角度计算使用精确公式，必须与绘图结果一致。

## 8. 用户可配置参数

在生成代码的文件头部，包含一个 config 字典：

```
config = {
"font_size_main": 34,
"font_size_title": 40,
"subtitle_font_size": 24,
"color_emphasis": "#66DDFF",
"color_highlight": "#FFDD66",
"speech_rate": 4.0,
# 注意：step_duration 由字幕字符数动态计算（duration = chars / 4.0）
# 无字幕时最小 2.5s（动画 0.5s + 缓冲 2s）
}
```

## 9. 字幕区规范

### 9.1 字幕显示规则

- 字幕统一使用 `18px`
- 字幕固定在底部 Y = `subtitle_zone_center`（由 `ZoneConstants.compute()` 动态计算）
- 水平居中显示
- 单行最大字符数：20个汉字 / 40个英文字符
- 超长文本自动拆分（优先在标点处断行）

### 9.2 时序规范

字幕显示必须遵循以下时序：

```
时间轴:  [内容入场] → [字幕显示] → [语音播放] → [淡出]
         ↑           ↑            ↑          ↑
      动画策略   FadeIn(字幕)  _play_speech()  FadeOut(全部)
      (按animation.type)  (字幕已可见，同步)   (主内容+字幕同时)
```

**禁止**: 在语音播完后再显示字幕（会导致学习者听不到对应内容）

### 9.3 清理安全规则

调用 `_hide()` 时：

- 必须逐项检查 `mobj in scene.mobjects`
- **禁止** 对已 FadeOut 的对象调用 `scene.remove()`
- **禁止** 对未添加到场景的对象调用 `scene.remove()`

## 10. 排版预估最佳实践（AI 静态计算用）

### 9.1 核心参数定义

| 参数             | 值                         | 说明                             |
| ---------------- | -------------------------- | -------------------------------- |
| 屏幕宽高         | frame_width × frame_height | 标准 16:9 配置（frame_height=8） |
| 安全区域 X       | [safe_x_min, safe_x_max]   | 留出 MARGIN_RATIO_X × 2 边距     |
| 安全区域 Y       | [safe_y_min, safe_y_max]   | 底部 safe_h×10% 给字幕           |
| 主字体大小       | 34                         | 对应行高约 0.6 单位              |
| 公式字符平均宽度 | 0.6 单位                   | 含下标、上标略微增加             |
| 行间距 buff      | 0.6 单位                   | arrange(DOWN, buff=0.6)          |
| 边距             | 1.0 单位                   | 左右各留 1.0 更安全              |

### 9.2 垂直空间预估公式

单元素占用高度 = 字体对应高度（≈ 字体/100 × 1.2）+ buff

对于 font_size=34，估算高度 = 0.6 + 0.6 = 1.2 单位

可用垂直范围 = safe_y_max - (safe_y_min + safe_h×10%) = safe_h×90%

最大容纳元素数 = safe_h×90% ÷ 单元素高度

强制分栏阈值：

- 元素数 >= 5 时，建议启用两栏
- 元素数 >= 8 时，必须启用两栏或三栏

### 9.3 水平空间预估公式

单字符宽度（font_size=34）≈ 0.6 单位

单行公式最大宽度 = 屏幕宽 - 左右边距 = 15.5 - 2 = 13.5 单位

最大字符数 = 13 ÷ 0.6 ≈ 21 字符

分栏时的宽度分配（以两栏为例，有图形时）：

- 左栏 X 范围 [safe_x_min, two_left_x_max] -> 宽度 safe_w × 60%
- 右栏 X 范围 [two_right_x_min, safe_x_max] -> 宽度 safe_w × 40%
- 栏间距 0.5 单位
- 左栏最大字符数 = safe_w × 60% ÷ 0.6 ≈ safe_w ÷ 1.0 字符（按 0.6 单位/字符计）

### 9.4 分栏触发规则（决策树）

元素总数 <= 4 -> 单栏居中
元素总数 5-7 -> 建议两栏（左侧文字/公式，右侧图形）
元素总数 >= 8 -> 强制两栏或三栏

特殊条件（任一触发）：

- 存在图形 + 多行公式 + 步骤说明 -> 直接三栏
- 单个公式宽度 > 10 字符 -> 不要放左栏，改到中栏或使用多行（align\*）
- 需要左右对比（错误 vs 正确） -> 两栏对比模式

### 9.5 字号与边距的联动调整

当内容较多时，可整体缩放元素，但需满足：

- 主公式字体最小不低于 28，否则难以辨认
- 缩放系数 s = 目标最大总高度 / 当前总高度
- 若 s < 0.8，触发强制分栏，而不是继续缩放

### 9.6 布局决策代码模板（AI 生成参考）

```python
def estimate_layout(total_elements, has_graphics, has_multirow_formulas):
   if total_elements <= 4:
      mode = "single_column"
   elif total_elements <= 7:
      mode = "two_column" if has_graphics else "single_column"
   else:
      mode = "three_column" if has_multirow_formulas else "two_column"
   return mode
```

## 10. 原子类型与布局绑定（强制）

| 原子类型          | 默认布局                       | 说明                     |
| ----------------- | ------------------------------ | ------------------------ |
| definition        | 有图则两栏，无图则单栏         | 放不下时拆分为多个 scene |
| intuition         | 有图则两栏，无图则单栏         | 直观体验优先展示图形     |
| operation         | 两栏（左步骤，右图形）         | 步骤可跨场景延续         |
| counter_intuitive | 两栏（左错误，右正确）         | 对比展示                 |
| application       | 两栏（左描述，右效果）         | 应用案例展示             |
| summary           | 三栏（左概念，中公式，右应用） | 总结回顾                 |

## 10. 分栏布局算法（强制执行）

### 10.1 宽度处理流程

```
1. 获取总宽度：从 ZoneConstants.compute() 获取安全区宽度 safe_width（如 13.5 单位）
2. 按比例分配：根据分栏模式和图形存在情况分配每一栏宽度
   - 两栏（有图形）：左 60%，右 40%
   - 两栏（无图形）：均分 50% / 50%
   - 三栏（有图形）：左 30%，中 30%，右 40%
   - 三栏（无图形）：均分 1/3 / 1/3 / 1/3
3. 内容适配：
   - 将内容放入分配宽度的容器
   - 若内容宽度 > 容器宽度，按优先级处理：
     ① 缩小字号（缩到下限，如 80%）
     ② 换行（文本/公式使用 align* 环境）
     ③ 触发拆分（过宽内容拆为多个原子）
   - 直到拆分后通过
4. 记录实际宽度：每一栏的实际宽度（可能小于分配宽度）
```

### 10.2 高度处理流程

```
1. 计算每栏高度：根据实际内容和换行结果，计算每栏整体高度
2. 顶部对齐：找到所有栏顶部 Y 的最大值，将每栏向上移动，使所有栏顶部对齐
3. 高度检测：检查每栏高度是否超过安全区允许的最大高度
4. 溢出处理：
   - 若某栏超出安全区，在 validate_layout() 中记录违规
   - 由 split_atom.py 按栏位拆分内容
   - 重新走宽度分配流程，直到拆分后通过
```

### 10.3 宽度与高度的交互

```
宽度和高度不是独立的：
- 宽度决定换行：分配宽度后，文本/公式可能换行，而换行直接影响高度
- 高度影响布局：某栏高度变高后，可能触发溢出拆分
- 拆分后重新分配：拆分出的新原子，需要重新走宽度分配流程

因此必须串联处理：
分配宽度 → 内容适配（可能换行）→ 计算高度 → 检测溢出 → 必要时拆分 → 重新分配宽度 → 直到拆分后通过
```

### 10.4 分栏算法调用接口

```
实现参考：从 scripts.layout.constants 导入 ZoneConstants，
调用 ZoneConstants.compute(frame_width, frame_height) 动态计算所有区域边界，
通过返回的字典获取安全区宽度和分栏宽度参数
```

### 10.5 分栏内容对齐算法（强制执行）

#### 10.5.1 对齐规则

多栏布局中，内容按栏位索引对齐：

| 栏位 | 索引                 | 对齐方向       | 对齐说明                                 |
| ---- | -------------------- | -------------- | ---------------------------------------- |
| 左栏 | 0                    | LEFT（左对齐） | 内容左边缘对齐栏左边界 `x_min`           |
| 中栏 | 1（三栏）            | LEFT（左对齐） | 内容左边缘对齐栏左边界 `x_min`           |
| 右栏 | 1（两栏）/ 2（三栏） | CENTER（居中） | 内容中心对齐栏中线 `(x_min + x_max) / 2` |

#### 10.5.2 对齐流程

1. 获取栏位索引 `column_index`
2. 调用 `ZoneConstants.get_column_alignment(column_index)` 获取对齐方向
3. 调用 `ZoneConstants.get_column_anchor_x(column, alignment)` 获取锚点 X 坐标
4. 将内容水平移动到锚点

#### 10.5.3 Manim 实现要点

- 使用 `RIGHT` / `LEFT` / `ORIGIN` 常量作为对齐参考边
- 不要使用绝对坐标硬编码对齐，应通过 `get_column_anchor_x()` 动态计算
- 所有栏位顶部必须对齐（共用同一 `y_max`，由顶部对齐算法保证）

## 11. 单个原子的内容排列规则

### 11.1 布局原则：智能适应，默认垂直

- 默认垂直排列：同一原子内的 content 数组元素默认使用垂直排列（arrange(DOWN)），符合阅读习惯
- 自动溢出处理：AI 必须根据元素预估宽度和高度，动态决定最终布局，防止内容超出安全区域

### 11.2 决策流程（强制执行）

AI 应遵循以下逻辑来决定布局：

1. 计算垂直总高度 (V_H)。如果 V_H < 5.5 单位，使用垂直排列
2. 如果垂直溢出（V_H > 5.5），计算水平总宽度 (H_W)
   - 如果 H_W < 13.5 单位，切换为水平排列
   - 如果 H_W >= 13.5 单位，触发强制拆分：将内容数组均分为左右两组，创建两个垂直排列的 VGroup，将这两个 VGroup 进行水平并排（arrange(RIGHT)），形成两栏布局

注意：本节描述的「两栏布局」为**临时应急布局**，仅在内容超出安全区域时自动触发。其栏宽度由内容均分决定，与第 4.2 节定义的「标准两栏布局」不同。标准两栏布局（有图形时左 60%、右 40%）是默认推荐布局，应急布局仅在溢出时使用。

3. 如果以上均失败（如内容导致两栏也溢出），则必须在 JSON 设计阶段就将该原子拆分为多个独立原子

### 11.3 布局参数

| 布局类型 | 排列方式               | 间距(buff)    | 对齐     | 整体位置                      |
| -------- | ---------------------- | ------------- | -------- | ----------------------------- |
| 垂直排列 | arrange(DOWN)          | 0.4           | 居中     | 顶部居中（Y = content_y_max） |
| 水平排列 | arrange(RIGHT)         | 0.3           | 居中     | 垂直居中（Y = 0）             |
| 两栏布局 | 左右各 arrange(DOWN)   | 0.5（栏间距） | 顶部对齐 | 水平居中                      |
| 三栏布局 | 左中右各 arrange(DOWN) | 0.4（栏间距） | 顶部对齐 | 水平居中                      |

三栏布局说明：

- 左栏：宽度约 safe_w × 30%，适合步骤说明（字体 30）
- 中栏：宽度约 safe_w × 30%，适合公式展示（字体 34）
- 右栏：宽度约 safe_w × 40%，适合图形或标注（字体 22）
- 栏间距：0.4 单位

### 11.4 禁止行为

- 禁止因强行使用水平排列导致内容超出屏幕右侧
- 禁止在可以垂直排列时因参数设置不当导致底部超出

### 11.5 公式独立成行规则（强制）

核心原则：重要公式、长公式或核心定义必须独立成行，禁止与普通文本水平混排

原因：

- 避免因内容超宽导致布局溢出
- 保证公式的视觉突出性和可读性
- 符合数学教材的排版习惯

实现方式（按优先级排序）：

1. 方式一：拆分为独立原子（推荐）

```
   // 原子 1：文字说明
   { "id": "desc", "content": [{"text": "矩阵的严格定义：", "type": "content"}] }

   // 原子 2：公式独立展示
   { "id": "formula", "content": [{"text": "A = \\begin{bmatrix} a_{11} & a_{12} \\\\ a_{21} & a_{22} \\end{bmatrix}", "type": "formula"}] }

   // 原子 3：解释
   { "id": "explain", "content": [{"text": "其中 a_{ij} 表示第 i 行第 j 列的元素", "type": "content"}] }
```

2. 方式二：同一原子内强制垂直排列

```json
{
  "id": "definition*with_formula",
  "layout": "vertical",
  "content": [
    { "text": "矩阵的严格定义：", "type": "content" },
    {
      "text": "A = \\begin{bmatrix} a*{11} & a*{12} \\\\ a*{21} & a*{22} \\end{bmatrix}",
      "type": "formula"
    },
    { "text": "其中 a*{ij} 表示第 i 行第 j 列的元素", "type": "content" }
  ]
}
```

禁止行为：

- 禁止将长公式与文字在同一原子内水平混排
- 禁止在 formula 类型中混入中文字符（必须先拆分）

判断标准：
满足以下任一条件即视为重要公式，必须独立成行：

- 公式宽度预估大于等于 8 单位
- 公式包含矩阵、积分、求和等复杂结构
- 公式是核心定理或关键结论

## 12. 跨场景与分场规则

### 12.1 分场触发条件

- 总原子数 > 30 时自动分场
- 单原子无法容纳时（高度/宽度超出阈值）自动分拆

### 12.2 跨场景规则

- 右栏图形始终保持在每个场景中（同步显示）
- 左栏步骤/公式按场景分拆
- 步骤可跨场景延续

### 12.3 自动分场反馈

- AI 自动分场后，向用户输出分场说明
- 说明包含：分场原因、场景数量、每个场景包含的原子

### 12.4 拆分实现参考

拆分逻辑的具体实现见 `scripts/split_atom.py`

## 13. 布局决策兜底策略

当 AI 按顺序执行以下判断后仍无法确定安全布局时：

1. 安全边界检查 -> 溢出
2. 原子类型推荐布局 -> 无法容纳
3. 元素数量检查 -> > 6
4. 内容宽度/高度检查 -> 超出阈值
5. 缩放（字体最小 28px）-> 仍溢出
6. 触发分栏（单栏->两栏->三栏）-> 仍溢出
7. 拆分原子 -> 仍无法容纳

最终兜底方案：

- 报错并终止渲染，输出详细的错误信息：
  - 哪个原子（id）导致失败
  - 估算的内容宽度/高度
  - 建议的手动调整方案

错误信息示例：
[Layout Error] 原子 'definition_formal' 无法安全布局
预估高度: 6.8 单位 > 5.5 单位
预估宽度: 14.2 单位 > 13.5 单位
元素数量: 9 个 > 6 个
建议: 将该原子拆分为 2-3 个独立原子

不允许：强制使用滚动条或超出画布

## 14. 验证清单（排版布局相关）

> 以下检查项仅适用于**排版布局代码**（区域容器定位、内容元素排版），动画/装饰/辅助代码不受此限制。

- [ ] 排版布局代码中无 `.next_to(` 调用（应使用 Zone 对象坐标或 VGroup.arrange()）
- [ ] 排版布局代码中无 `.align_to(` 调用（应使用 Zone 对象坐标）
- [ ] 排版布局代码中无 `.move_to(` 调用（仅标题/副标题居中使用 ORIGIN 除外）
- [ ] 排版布局代码中无 `.shift(` 调用（应使用 Zone 对象坐标或 VGroup.arrange()）
- [ ] 坐标无硬编码（均通过 ZoneConstants 或 Zone 对象推导）
- [ ] 所有排版元素均通过 VGroup.arrange() 或 Zone 坐标定位
- [ ] 主内容区居中左对齐（非整体居中）
- [ ] 图形区在右侧（两栏/三栏模式时）
- [ ] 主内容区与图形区顶部对齐
- [ ] 标题和副标题居中
- [ ] 内容未超出安全边界
- [ ] 字体大小符合分栏模式要求
- [ ] 单独标题场景整体垂直居中

## 15. 坐标参考系规范（强制执行）

### 目的

为帮助 AI 精确计算坐标，减少布局错误，在开发和调试阶段必须使用可视化坐标参考系。

### 坐标参考系的添加

在场景的 `construct()` 方法开头，添加 `NumberPlane` 或 `Axes`：

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        # 添加坐标参考系（调试用）
        axes = Axes(
            x_range=[-7.5, 7.5, 1],
            y_range=[-4.5, 4.5, 1],
            x_length=15,
            y_length=9,
            axis_config={"color": BLUE},
            x_axis_config={"numbers_to_include": range(-7, 8)},
            y_axis_config={"numbers_to_include": range(-4, 5)},
        )
        self.add(axes)
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        self.add(labels)
```

### 坐标转换方法

使用 `axes.c2p(x, y)` 将数学坐标转换为屏幕坐标：

正确做法：使用坐标转换

```python
point = axes.c2p(2, 3)
circle = Circle(radius=0.2).move_to(point)
```

错误做法：硬编码坐标

circle = Circle(radius=0.2).move_to([2, 3, 0])

### 调试模式与生产模式

- 开发调试阶段：保留坐标参考系（`self.add(axes)`）
- 最终视频：注释或删除 `self.add(axes)`，仅保留图形

## 16. 运行时动态调整机制（新增）

### 16.1 概述

当 `validate_layout()` 检测布局违规时，系统会自动执行**3 轮递进调整策略**，无需人工干预。

**调整流程**：

```
validate_layout() 返回违规 → LayoutOptimizer.optimize() 自动执行
                                                     ↓
                        第 1 轮：缩小字号（scale_font）→ 重新测量 → 验证
                                                     ↓（失败）
                        第 2 轮：换行策略（wrap_content）→ 重新测量 → 验证
                                                     ↓（失败）
                        第 3 轮：拆分原子（split_atom）→ 调用外部回调 → 结束
```

### 16.2 自动优化器使用

**在场景代码中调用**：

```
渲染代码示例：继承 LayoutScene 类，在 construct 中创建内容并组合为 VGroup，
调用 place_in_main_zone 放置内容，调用 validate_layout 验证布局，
如有违规调用 handle_violation 自动处理，检查处理结果并输出日志
```

**手动处置模式**（仅输出报告）：

```
渲染代码示例：调用 handle_violation 时传入 auto_optimize=False 参数，
仅输出违规报告而不执行自动优化
```

### 16.3 字体自适应算法

**静态预估**（在设计阶段）：

```python
from layout.constants import ZoneConstants

# 根据可用宽度自动计算字号
content_width = 12.0  # 预估内容宽度
available_width = 13.5  # 栏位宽度
font_size = ZoneConstants.auto_font_size(
    content_width=content_width,
    available_width=available_width,
    base_size=32,
    min_size=24,
    max_size=34
)
# 返回结果：28（根据比例自动缩小）
```

**运行时实测**（在渲染阶段）：

```python
from layout.engine import LayoutEngine

# 实测内容尺寸
texts = [Text(f"Line {i}") for i in range(5)]
width, height = LayoutEngine.measure_content_dims(texts)
print(f"实际宽={width:.2f}, 高={height:.2f}")
```

### 16.4 调整策略详解

| 轮次        | 策略                       | 适用范围           | 执行条件           | 调整幅度      |
| ----------- | -------------------------- | ------------------ | ------------------ | ------------- |
| **第 1 轮** | `scale_font`（缩小字号）   | 宽度溢出、高度溢出 | 当前字号 > 24px    | 缩放到 0.9 倍 |
| **第 2 轮** | `wrap_content`（换行策略） | 高度溢出（公式）   | 公式长度 > 60 字符 | 插入换行符    |
| **第 3 轮** | `split_atom`（拆分原子）   | 任意溢出           | 字号已触及下限     | 调用外部回调  |

### 16.5 日志输出示例

**成功优化**：

```
[handle_violation] 发现 2 项违规
[handle_violation] 优化成功！共执行 2 轮调整
  - 第 1 轮：策略=scale_font, 成功
  - 第 2 轮：策略=wrap_content, 成功
```

**优化失败**：

```
[handle_violation] 发现 3 项违规
[handle_violation] 优化失败，建议人工干预
  经过 3 轮自动优化仍无法解决布局问题。
  建议：将相关原子拆分为更细粒度的独立原子。
  调整日志：
    第 1 轮：策略=scale_font, 类型=WIDTH_OVERFLOW, 成功
    第 2 轮：策略=wrap_content, 类型=HEIGHT_OVERFLOW, 失败
    第 3 轮：策略=split_atom, 类型=WIDTH_OVERFLOW, 成功（触发回调）
```

### 16.6 回调机制

当需要拆分原子时，优化器会调用 `on_split_callback`：

```python
def _on_atom_split(self, violation_type, mobjects, suggested_id):
    """拆分原子回调"""
    logging.warning(f"需要拆分原子 {suggested_id} (类型={violation_type})")
    logging.warning("建议工程师操作：将 JSON 中该原子拆分为 2-3 个独立原子")
```

**工程师操作**：

1. 查看日志，定位需要拆分的原子 ID
2. 打开对应 JSON 文件
3. 将该原子拆分为多个独立原子（内容均分）
4. 重新生成代码

### 16.7 与布局决策引擎的配合

**布局决策流程**（`LayoutEngine.decide()`）：

```
1. 静态预估内容尺寸（estimated_height/width）
   ↓
2. 根据阈值决策布局模式（单栏/两栏/三栏）
   ↓
3. 运行时实测内容尺寸（LayoutEngine.measure_content_dims()）
   ↓
4. 验证布局（validate_layout()）
   ↓
5. 如果有违规 → 自动优化（handle_violation()）
   ↓
6. 如果优化失败 → 建议人工拆分原子
```

### 16.8 代码示例

**完整流程示例**：

```python
from manim import *
from layout.scene_base import LayoutScene
from layout.engine import LayoutEngine
from layout.constants import ZoneConstants

class OptimizationDemo(LayoutScene):
    def construct(self):
        # 1. 决策布局（基于静态预估）
        content_count = 10
        has_graphics = True
        layout_decision = LayoutEngine.decide(
            content_count=content_count,
            has_graphics=has_graphics,
            has_multirow_formulas=True
        )

        # 2. 创建内容
        texts = [Text(f"Line {i} - 这是一段较长的文本内容") for i in range(10)]
        all_mobjects = VGroup(*texts)

        # 3. 放置内容（根据决策的布局模式）
        if layout_decision.mode == LayoutMode.TWO_COLUMN:
            group = self.place_two_column(left_content=texts[0:5], right_content=texts[5:10])
        else:
            group = self.place_in_main_zone(all_mobjects, layout_mode="vertical")

        # 4. 验证布局
        violations = self.validate_layout(list(all_mobjects))

        # 5. 自动优化（如有违规）
        if violations:
            # 实测内容尺寸（用于调试）
            width, height = LayoutEngine.measure_content_dims(all_mobjects)
            print(f"实测宽度={width:.2f}, 高度={height:.2f}")

            # 自动处理违规
            result = self.handle_violation(violations, list(all_mobjects))
            if result and not result.success:
                print(f"优化失败，建议人工干预")
```

### 坐标参考系的样式

- 网格线颜色：建议使用 GREY 或 BLUE，透明度 0.3
- 刻度数字：字号 20，颜色 GREY
- 确保不干扰教学内容（调试后可隐藏）

### 验证清单

- [ ] 涉及坐标计算的场景已添加 Axes 或 NumberPlane
- [ ] 使用 axes.c2p() 而非硬编码坐标

## 附录 A. 负向约束速查（Don't）

> **用途**：当布局代码写成这样 → 画面炸成这样。Agent 必须避免以下任意一条。
> 对应 SKILL.md 中的 [负向约束速查索引](../SKILL.md#负向约束速查索引dont-quick-reference)。

### L-D1：硬编码坐标

❌ DON'T：坐标硬编码 → 分辨率/宽高比变化时元素溢出画布

渲染代码示例：使用固定坐标数组直接定位图形元素

✅ DO：使用 axes.c2p() 转换坐标系，使用 VGroup.arrange() 相对布局

渲染代码示例：使用坐标转换函数定位，使用组合布局方法统一排列

**画面炸成**：16:9 下正常 → 4:3 下元素被挤出屏幕

---

### L-D2：逐个对象独立 shift（替代 VGroup.arrange）

❌ DON'T：逐个 .shift() 定位 → 元素间相对位置无法统一调整

渲染代码示例：逐个移动对象并累积偏移量

✅ DO：整体 VGroup + .arrange() / .next_to()

渲染代码示例：将多个对象组合后使用统一排列方法

**画面炸成**：局部微调牵一发动全身，改动一处需手动修正 10+ 处偏移

---

### L-D3：直接放置元素到画布边缘，不调用 place_in_safe_area()

❌ DON'T：直接放置元素到画布边缘

渲染代码示例：直接将元素移动到接近画布边界的坐标位置

✅ DO：所有放置逻辑必须通过 place_in_safe_area()

渲染代码示例：调用安全区域放置方法进行定位

**画面炸成**：元素超出 SCREEN_WIDTH/HEIGHT 边界 → 渲染被截断

---

### L-D4：场景不继承 LayoutScene

❌ DON'T：场景不继承 LayoutScene → 所有布局约束失效

渲染代码示例：创建不继承布局场景基类的场景

✅ DO：所有场景必须继承 LayoutScene

渲染代码示例：声明继承自 LayoutScene 的场景类

**画面炸成**：无 validate_layout() 可用，布局问题仅能在渲染后发现

---

### L-D5：手动估算坐标而非公式推导

❌ DON'T：手动估算中点

渲染代码示例：使用硬编码算术平均或直接写数字计算中点

✅ DO：使用 Midpoint 类推导

渲染代码示例：使用中点类推导坐标并转换

**画面炸成**：辅助线不对齐，几何关系错误

---

### L-D6：跨域混用坐标参考系

❌ DON'T：混用数学坐标系和像素坐标

渲染代码示例：同时使用像素坐标和数学坐标定位不同元素

✅ DO：统一使用数学坐标系（Y轴向上），全部 axes.c2p()

渲染代码示例：统一使用数学坐标转换方法

**画面炸成**：公式与图形位置完全不匹配

---

### L-D7：浮力场景未配重叠白名单

❌ DON'T：浮力场景未使用 allowed_overlap_patterns

渲染代码示例：直接验证布局而不配置允许的重叠模式

✅ DO：浮力场景配置 overlap_patterns

渲染代码示例：在验证布局时传入允许的重叠模式参数

**画面炸成**：合法的物体-液体接触被误判为布局错误，导致物理场景失真

---

### L-D8：使用废弃的脚本路径

- **DON'T**：引用已废弃的脚本路径（如 `scripts.layout_base.LayoutScene`）
- **DO**：使用当前有效路径 `scripts.layout.scene_base.LayoutScene`；推荐方法名 `scene.safe_place(obj)` / `scene.place_two_column(left, right)` / `scene.validate_layout(objs)`

**画面炸成**：ImportError，渲染直接失败

- [ ] 调试完成后可隐藏坐标参考系
