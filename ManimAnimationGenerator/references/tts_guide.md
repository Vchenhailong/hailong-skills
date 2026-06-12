# TTS 语音合成与处理规范

## 1. 核心原则
- 优先使用厂商 TTS 服务（阿里云、豆包），备选 EdgeTTS
- 数学符号必须转义为人类自然语言读音
- 语音依赖必须完整预安装（详见第 6 节）
- 无语音模式：用户明确要求时不生成语音，仅字幕与动画

## 2. TTS 方案选择（强制优先级）

```markdown
| 优先级 | 方案 | 适用场景 | 发音可控 | 网络要求 |
|--------|------|----------|----------|----------|
| 1（强烈推荐） | 阿里云或豆包 TTS | 数学/物理教学，需纠正术语读音 | 支持 SSML | 需要 |
| 2（备选） | EdgeTTS (natural 语音包) | 无云端账号或不愿注册 | 不可控 | 需要 |
| 禁用 | gTTS | — | — | 需要 VPN |
```

决策规则：
- 若用户有云端 TTS 账号 -> 使用云端 TTS + SSML 纠正数学术语
- 若无云端账号 -> 提示告知 EdgeTTS 的详细限制，征得同意后使用
- 若用户明确要求离线 -> 提醒用户需要人工录制语音，建议走线上服务渠道

## 3. 数学符号转义表（强制）

在传给 TTS 的文本中，必须将以下符号替换为中文读音：

### 3.1 Unicode 数学符号

```markdown
| Unicode | 转义后 | 说明 |
|---------|--------|------|
| = | 等于 | 等号 |
| ≠ | 不等于 | 不等号 |
| ≈ | 约等于 | 近似等号 |
| ≡ | 恒等于 | 恒等号 |
| ≤ | 小于等于 | 小于等于号 |
| ≥ | 大于等于 | 大于等于号 |
| < | 小于 | 小于号 |
| > | 大于 | 大于号 |
| ± | 正负 | 正负号 |
| ∓ | 负正 | 负正号 |
| × | 乘以 | 乘号 |
| ÷ | 除以 | 除号 |
| · | 点乘 | 点乘号 |
| √ | 根号 | 根号 |
| ∞ | 无穷大 | 无穷大 |
| ∠ | 角 | 角符号 |
| ⊥ | 垂直于 | 垂直符号 |
| ∥ | 平行于 | 平行符号 |
| △ | 三角形 | 三角形符号 |
| □ | 正方形 | 正方形符号 |
| ○ | 圆 | 圆符号 |
| ° | 度 | 度符号 |
| ∵ | 因为 | 因为符号 |
| ∴ | 所以 | 所以符号 |
| ∈ | 属于 | 属于符号 |
| ∉ | 不属于 | 不属于符号 |
| ⊂ | 包含于 | 包含于符号 |
| ⊃ | 包含 | 包含符号 |
| ⊆ | 子集于 | 子集于符号 |
| ⊇ | 超集于 | 超集于符号 |
| ∪ | 并集 | 并集符号 |
| ∩ | 交集 | 交集符号 |
| ∅ | 空集 | 空集符号 |
| ∀ | 对于任意 | 全称量词 |
| ∃ | 存在 | 存在量词 |
| → | 趋向于 | 箭头 |
| ⇒ | 推出 | 双线箭头 |
| ⇔ | 等价于 | 双向箭头 |
```

### 3.2 Unicode 希腊字母

```markdown
| Unicode | 转义后 | Unicode | 转义后 |
|---------|--------|---------|--------|
| α | 阿尔法 | β | 贝塔 |
| γ | 伽马 | δ | 德尔塔 |
| ε | 艾普西龙 | ζ | 泽塔 |
| η | 伊塔 | θ | 西塔 |
| ι | 约塔 | κ | 卡帕 |
| λ | 兰姆达 | μ | 缪 |
| ν | 纽 | ξ | 克西 |
| π | 派 | ρ | 柔 |
| σ | 西格玛 | τ | 陶 |
| υ | 宇普西龙 | φ | 斐 |
| χ | 凯 | ψ | 普西 |
| ω | 欧米伽 | | |
```

### 3.3 LaTeX 符号

```markdown
| LaTeX 符号 | 转义后 | 示例原文 | 示例转义后 |
|------------|--------|----------|------------|
| \neq | 不等于 | a \neq b | a 不等于 b |
| \leq | 小于等于 | a \leq b | a 小于等于 b |
| \geq | 大于等于 | a \geq b | a 大于等于 b |
| \approx | 约等于 | a \approx b | a 约等于 b |
| \times | 乘以 | a \times b | a 乘以 b |
| \cdot | 点乘 | a \cdot b | a 点乘 b |
| \div | 除以 | a \div b | a 除以 b |
| \frac | 分之 | \frac{a}{b} | b 分之 a |
| \sqrt | 根号 | \sqrt{a} | 根号 a |
| \sum | 求和 | \sum_{i=1}^n | 求和 i 从 1 到 n |
| \int | 积分 | \int f(x)dx | 积分 f x d x |
| \prod | 连乘 | \prod_{i=1}^n | 连乘 i 从 1 到 n |
| \lim | 极限 | \lim_{x \to 0} | 极限 x 趋向于 0 |
| \angle | 角 | \angle ABC | 角 A B C |
| \perp | 垂直于 | AB \perp CD | A B 垂直于 C D |
| \parallel | 平行于 | AB \parallel CD | A B 平行于 C D |
| \triangle | 三角形 | \triangle ABC | 三角形 A B C |
| \odot | 圆 | \odot O | 圆 O |
| \circ | 度 | 90^\circ | 90 度 |
| \to | 趋向于 | x \to 0 | x 趋向于 0 |
| \Rightarrow | 推出 | A \Rightarrow B | A 推出 B |
| \Leftrightarrow | 等价于 | A \Leftrightarrow B | A 等价于 B |
| \because | 因为 | \because x=y | 因为 x 等于 y |
| \therefore | 所以 | \therefore x=y | 所以 x 等于 y |
| \in | 属于 | a \in S | a 属于 S |
| \notin | 不属于 | a \notin S | a 不属于 S |
| \subset | 包含于 | A \subset B | A 包含于 B |
| \subseteq | 子集于 | A \subseteq B | A 是 B 的子集 |
| \cup | 并集 | A \cup B | A 并 B |
| \cap | 交集 | A \cap B | A 交 B |
| \emptyset | 空集 | \emptyset | 空集 |
| \infty | 无穷大 | \infty | 无穷大 |
| \alpha | 阿尔法 | \alpha | 阿尔法 |
| \beta | 贝塔 | \beta | 贝塔 |
| \gamma | 伽马 | \gamma | 伽马 |
| \delta | 德尔塔 | \delta | 德尔塔 |
| \epsilon | 艾普西龙 | \epsilon | 艾普西龙 |
| \zeta | 泽塔 | \zeta | 泽塔 |
| \eta | 伊塔 | \eta | 伊塔 |
| \theta | 西塔 | \theta | 西塔 |
| \iota | 约塔 | \iota | 约塔 |
| \kappa | 卡帕 | \kappa | 卡帕 |
| \lambda | 兰姆达 | \lambda | 兰姆达 |
| \mu | 缪 | \mu | 缪 |
| \nu | 纽 | \nu | 纽 |
| \xi | 克西 | \xi | 克西 |
| \pi | 派 | \pi | 派 |
| \rho | 柔 | \rho | 柔 |
| \sigma | 西格玛 | \sigma | 西格玛 |
| \tau | 陶 | \tau | 陶 |
| \upsilon | 宇普西龙 | \upsilon | 宇普西龙 |
| \phi | 斐 | \phi | 斐 |
| \chi | 凯 | \chi | 凯 |
| \psi | 普西 | \psi | 普西 |
| \omega | 欧米伽 | \omega | 欧米伽 |
```

实现方式：在生成 voiceover(text=...) 前，调用 tex_tools.py 中的 math_symbols_to_speech(text) 函数自动替换。

## 4. Azure TTS 配置（推荐）

### 4.1 依赖安装
pip install "manim-voiceover[azure]"

### 4.2 环境变量
创建 .env 文件：

```
AZURE_SUBSCRIPTION_KEY=你的密钥
AZURE_SERVICE_REGION=eastasia
```

### 4.3 数学术语纠正（SSML 示例）

```python
from manim_voiceover.services.azure import AzureService

self.set_speech_service(
    AzureService(
        voice="zh-CN-YunxiNeural",
        style="serious",
        rate=0,
        pitch=0,
    )
)

ssml = """
<speak>
在几何学中，<phoneme alphabet="sapi" phrase="chui zhi">垂直</phoneme>是指...
</speak>
"""
with self.voiceover(ssml=ssml) as tracker:
    ...
```

### 4.4 推荐语音包

```
| 语音 | 风格 | 适用场景 |
|------|------|----------|
| zh-CN-YunxiNeural | 严肃/沉稳 | 数学推导、物理讲解 |
| zh-CN-XiaoxiaoNeural | 自然/亲切 | 概念启蒙、科普 |
| zh-CN-YunyangNeural | 新闻/专业 | 长篇定义、定理陈述 |
```

### 4.5 免费额度
每月 50 万字符（约 500 分钟语音）
注册地址：https://azure.microsoft.com/zh-cn/services/cognitive-services/text-to-speech/

### 4.6 其他 TTS 服务
MOSS-TTS-Nano: https://github.com/OpenMOSS/MOSS-TTS-Nano

## 5. EdgeTTS 备选方案

### 5.1 限制说明（必须告知用户）
EdgeTTS 存在以下问题：
1. 无法控制数学术语读音（如垂直可能读成垂脚）
2. 依赖网络，且部分区域可能不稳定
3. 不支持 SSML，无法纠正发音

### 5.2 使用方式
```
from manim_voiceover.services.edge import EdgeTTSService

self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural"))
```

### 5.3 可用语音包
- zh-CN-XiaoxiaoNeural（女声，自然）
- zh-CN-YunxiNeural（男声，适合数学）
- zh-CN-YunyangNeural（男声，新闻风格）

## 6. 依赖预安装清单（强制）

根据官方文档 https://voiceover.manim.community/en/stable/installation.html，必须安装以下依赖：

### 6.1 Python 包
pip install --upgrade "manim-voiceover[all]"

### 6.2 系统依赖

```markdown
| 操作系统 | PortAudio | SoX | gettext |
|----------|-----------|-----|---------|
| Debian/Ubuntu | sudo apt install portaudio19-dev && pip install pyaudio | sudo apt-get install sox libsox-fmt-all | sudo apt install gettext |
| macOS | brew install portaudio && pip install pyaudio | brew install sox | brew install gettext |
| Windows | pip install pyaudio（自带二进制） | 需从源码安装 | 需从 MinGW 或 Cygwin 安装 |
```

### 6.3 验证安装
wget https://github.com/ManimCommunity/manim-voiceover/raw/main/examples/gtts-example.py
manim -pql gtts-example.py --disable_caching

重要：每次渲染必须加 --disable_caching 标志。

## 7. 无语音模式

当用户明确要求无语音时：
- 不调用 set_speech_service()
- 不使用 with self.voiceover 块
- 仅使用 self.play() 和 self.wait() 控制节奏

## 8. 验证清单（添加到 verification_checklist.md）

- [ ] 已根据用户选择配置正确的 TTS 服务（云端 TTS / EdgeTTS）
- [ ] 数学符号已转义为自然语言（包括 Unicode 和 LaTeX 符号）
- [ ] 依赖已完整安装（PortAudio、SoX、gettext）
- [ ] 渲染命令包含 --disable_caching
- [ ] 若使用 EdgeTTS，已告知用户发音限制

## 负向约束（Don't）

> **用途**：当 TTS 代码写成这样 → 画面/音画炸成这样。Agent 必须避免以下任意一条。
> 对应 SKILL.md 中的 [负向约束速查索引](../SKILL.md#负向约束速查索引dont-quick-reference)。

### T-D1：TTS 文本未经过符号映射

```python
# ❌ DON'T：直接发送 LaTeX 给 TTS 引擎
tts_text = r"lim_{x→0} sin(x)/x = 1"  # 下划线、上标符号被直接读出

# ✅ DO：必须通过 math_symbols_to_speech() 映射
from tex_tools import math_symbols_to_speech
tts_text = math_symbols_to_speech(r"lim_{x→0} sin(x)/x = 1")
# 输出: "lim x趋近于0 sin(x)除以x 等于1"
```

**画面炸成**：TTS 读出"LaTeX 代码"，听众以为是系统故障

---

### T-D2：TTS 文本包含 LaTeX 分隔符

```python
# ❌ DON'T：LaTeX 分隔符出现在 TTS 文本中
bad = r"$x^2$ 的导数是 $2x$"  # $ 符号被 TTS 读出

# ✅ DO：TTS 前清除 LaTeX 分隔符
good = "x的平方的导数是2x"    # 或通过映射函数处理
```

**画面炸成**：TTS 读出 "dollar x caret 2 dollar"，严重干扰收听

---

### T-D3：highlight_range 超出公式字符范围

```python
# ❌ DON'T：highlight_range 指定了不存在的字符位置
bad = {
    "content": [{"text": r"$\frac{d}{dx}x^2 = 2x$", "type": "formula"}],
    "highlight_range": [50, 60]   # 公式只有约 20 字符
}

# ✅ DO：highlight_range 必须覆盖 content 中 formula 项的字符范围
formula_text = r"$\frac{d}{dx}x^2 = 2x$"
good = {"highlight_range": [0, len(formula_text)]}
```

**画面炸成**：高亮区域与公式不对应，字幕动画高亮了错误的内容

---

### T-D4：duration 留默认值（未估算）

```python
# ❌ DON'T：所有 step 的 duration 使用固定值
step = {"duration": 6.0} * 20   # 全部 6 秒

# ✅ DO：每步根据 tts_text 实际字数估算朗读时长
step = {
    "tts_text": "导数的几何意义是函数图像上某一点的切线斜率",
    "duration": 5.5,             # 约 20 字 / 4字/秒 ≈ 5秒
}

# 校验规则：
# - min_duration = ceil(len(speech) / 4)（向上取整）
# - 若 duration < min_duration，自动修正为 min_duration
```

**画面炸成**：字幕闪退或长时间停留，音画节奏混乱

**字幕滚动同步**：
- 语音速度：约4字符/秒
- 滚动触发：每朗读完2行后触发一次滚动
- 滚动时机计算：`scroll_interval = duration / (scroll_count + 1)`