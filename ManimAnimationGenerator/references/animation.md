# 动画规范

## 1. 核心原则

- 动画是教学的辅助工具，不得喧宾夺主
- 每个动画必须有明确的教学目的
- 动画节奏与语音同步，每步 6 秒（0.5 秒动画 + 5.5 秒语音/缓冲）
- 禁止抖动、旋转、圆周运动等花哨效果

## 2. 打字机效果

### 2.1 适用场景
- 所有文字内容（公式、定义、说明）必须使用打字机效果逐字显示
- 标题、路径图等过渡性内容除外

### 2.2 实现方式
- 纯文本：`AddTextLetterByLetter`
- 公式（MathTex）：`Write`（逐元素显示）

### 2.3 速度参数
- 中文：0.05 秒/字符
- 英文字母：0.03 秒/字符
- 公式：按元素个数计算，每个元素 0.15 秒

### 2.4 元素间延迟
- 同一原子内的多个元素之间延迟 0.2 秒

### 2.5 语音同步
- 打字机动画应在语音开始后立即播放
- 动画时长应略短于语音时长（预留 0.3~0.5 秒缓冲）

## 3. 高亮动画

### 3.1 适用场景
- 当前步骤的主题
- 当前讲解的公式整体
- 当前关注的图形区域

### 3.2 时序要求（强制）
- 高亮动画必须在打字机效果完成后执行
- 高亮动画必须在闪烁动画之前执行
- 即：打字机 -> 高亮 -> 闪烁

### 3.3 实现方式
- 2D 元素：box-shadow + border + scale
- 3D 物体：材质颜色变化 + 边缘轮廓

### 3.4 参数
- 高亮颜色：#66DDFF（浅蓝）
- 动画时长：0.3 秒
- 缓动函数：ease

### 3.5 触发方式
- 步骤切换时自动高亮当前元素
- 语音关键词匹配触发
- 用户可通过 JSON 的 `highlight` 字段手动指定

### 3.6 代码示例
```javascript
element.classList.add('highlight-animate')
element.style.transition = 'all 0.3s ease'
element.style.boxShadow = '0 0 15px #66DDFF'
element.style.border = '2px solid #66DDFF'
element.style.transform = 'scale(1.02)'
```
## 4. 闪烁动画

### 4.1 适用场景
- 当前项（正在操作的元素）强调
- 矩阵乘法对应项闪烁
- 公式中的当前操作数
- 图形中的当前操作元素
- 推导步骤中的当前项

### 4.2 时序要求（强制）
- 闪烁动画必须在高亮动画完成后执行
- 即：打字机 -> 高亮 -> 闪烁
- 完整时序：内容显示完成 -> 整体高亮（0.3秒）-> 当前项闪烁3次（约1.8秒）

### 4.3 参数
- 闪烁颜色：#FFDD66（黄色）
- 闪烁次数：3 次
- 闪烁间隔：0.3 秒
- 动画时长：0.3 秒/次

### 4.4 实现方式
```javascript
let blinkCount = 0
const interval = setInterval(() => {
    if (blinkCount >= 6) {
        clearInterval(interval)
        element.classList.remove('highlight-animate')
        return
    }
    if (blinkCount % 2 === 0) {
        element.classList.add('highlight-animate')
        element.style.backgroundColor = '#FFDD66'
    } else {
        element.classList.remove('highlight-animate')
        element.style.backgroundColor = ''
    }
    blinkCount++
}, 300)
```

### 4.5 触发方式
- 自动触发：AI 根据语音内容判断当前项
- 手动触发：用户在 JSON 中设置 `current_item: true`

## 5. 发光效果

### 5.1 适用场景（仅限关键结论）
- 最终结论公式（如 E = mc^2 的最终呈现）
- 核心定理陈述
- 视频结尾的知识网络图标题

### 5.2 使用规范
- 每视频不超过 3 处
- 发光颜色：`#66DDFF` 或 `#FFFFFF`
- 发光强度：中等（opacity 0.3 ~ 0.5）
- 发光半径：0.05 ~ 0.1 单位

### 5.3 实现方式
```python
def add_glow(text, color="#66DDFF", opacity=0.3, scale=1.05):
    glow = text.copy().set_color(color).set_opacity(opacity)
    glow.scale(scale)
    return VGroup(glow, text)

conclusion = MathTex("E = mc^2", font_size=40)
glow_conclusion = add_glow(conclusion)
self.play(FadeIn(glow_conclusion))
```

### 5.4 禁止行为
- 对正文、普通公式、步骤说明使用发光
- 全局使用发光

## 6. 轨迹绘制

### 6.1 适用场景
- 物理运动轨迹（抛物线、圆周运动、抛体运动）
- 函数曲线（sin(x)、cos(x)、exp(x) 等）
- 几何辅助线（垂线、中线、角平分线）
- 向量路径（位移向量、速度向量变化）
- 数理图形（包括但不限于几何、线性代数、力分析、磁场等）

### 6.2 绘制方式
- 动态绘制：逐点出现，像写字一样
- 与语音同步：讲到哪绘制到哪

### 6.3 样式规范
- 实线曲线（函数图像、运动轨迹）：实线，默认颜色 #66DDFF
- 辅助线（几何作图中的辅助线）：虚线，默认颜色 #888888
- 向量路径：实线 + 箭头，默认颜色 #66DDFF
- 所有样式遵循教材和人类阅读习惯

### 6.4 实现方式

函数图像逐点绘制：
```python
def draw_function_dynamic(expr, x_range, color, duration):
    points = []
    for x in x_range:
        y = eval(expr)
        points.append(self.grid.toScreen(x, y))
    curve = VMobject()
    curve.set_points_smoothly(points)
    self.play(Create(curve), run_time=duration)
```

辅助线虚线绘制：
```python
aux_line = DashedLine(start, end, color="#888888", stroke_width=2)
self.play(Create(aux_line))
```

轨迹动态绘制（逐点）：
```python
trajectory = VMobject()
for point in trajectory_points:
    new_trajectory = trajectory.copy().append_points(point)
    self.play(Transform(trajectory, new_trajectory), run_time=0.05)
```

### 6.5 语音同步
- 通过 animation.delay 与语音同步
- 语音播放到轨迹的某个关键点时，触发该段的绘制

### 6.6 轨迹绘制验收清单
- [ ] 轨迹逐点出现，与语音同步
- [ ] 实线/虚线样式符合教材习惯
- [ ] 辅助线使用虚线，颜色 #888888
- [ ] 函数曲线使用实线，颜色 #66DDFF
- [ ] 向量路径带箭头

## 7. 动画与语音同步规则

### 7.1 时序控制
- 使用 speechStartTime 记录语音开始时间
- 通过 animation.delay 设置动画触发时间（相对于语音开始）
- 动画 duration 应与语音内容匹配

### 7.2 完整时序要求（强制）

每个原子的动画执行顺序：
0.0-2.5 秒：打字机效果（内容逐字显示）
2.5-2.8 秒：高亮动画（当前步骤整体高亮，0.3秒）
2.8-4.6 秒：闪烁动画（当前项闪烁3次，每次0.3秒，间隔0.3秒，共1.8秒）
4.6-6.0 秒：缓冲时间（等待语音结束，或进入下一步）

### 7.3 当前项自动判断
AI 自动识别当前项：
- 语音中提到的具体元素（如"第一行第一列"、"向量 i"、"重力"）
- 公式中正在计算的部分（如"1×5"）
- 图形中正在操作的部分
- 推导步骤中正在变换的部分
- 每个步骤的第一个新元素

### 7.4 优先级
- 用户可通过 JSON 中的 animation 字段覆盖默认动画
- 当前项闪烁优先级高于普通高亮

## 8. 动画验证清单

- [ ] 所有文字使用打字机效果
- [ ] 打字机 -> 高亮 -> 闪烁 时序正确
- [ ] 当前步骤整体高亮（#66DDFF）
- [ ] 当前项闪烁 3 次（#FFDD66）
- [ ] 关键结论使用发光效果（不超过 3 处）
- [ ] 轨迹动态绘制，与语音同步
- [ ] 辅助线使用虚线
- [ ] 动画时长与语音匹配
- [ ] 动画与语音通过 delay 同步
- [ ] 无抖动、旋转、圆周运动等禁止效果
