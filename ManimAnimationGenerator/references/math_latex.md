# LaTeX 公式规范

## 1. 基本语法

- 分式：\frac{a}{b}
- 根号：\sqrt{a}
- 指数/下标：a^2, x_i
- 求和/积分：\sum, \int
- 矩阵：\begin{matrix}...\end{matrix}
- 多行对齐：\begin{align*} ... \end{align*}

## 2. 公式完整性（禁止割裂）

- 每个 MathTex 对象必须包含一个完整的数学表达式单元（如整个等式、整个分式、整个矩阵）。
- 多行推导必须使用 align\* 环境整体放入一个 MathTex。
- 禁止将公式拆分为多个独立 MathTex 按行排列。

## 3. 长公式处理

- 若公式宽度 > 13.5 单位，使用 align\* 自动换行，并在等号处对齐。
- 分步推导时，每一步展示完整的前后式，而非碎片。

## 4. LaTeX 语法检查（AI 生成前执行）

- 检查括号匹配、命令是否存在、未转义字符（如 \_ ^ 需在 math 模式外转义）。
- 常见错误对照表：缺少 \right, \left; 非法命令（如化学专用）；未闭合的 {} 等。
- 若检查失败，AI 必须修正后再输出代码。

## 5. MathTex vs Tex 选择规范（强制）

### 5.1 核心区别

```
| 特性 | MathTex | Tex |
|------|---------|-----|
| 数学模式 | 自动进入数学模式 | 需要手动 $...$ 或 $$...$$ |
| 中文支持 | 不支持 | 支持（需配合 ctex 或 xeCJK） |
| 文本与公式混合 | 不便 | 方便 |
| 多行对齐 | 支持 align* | 支持但语法不同 |
| 渲染速度 | 快 | 稍慢 |
```

### 5.2 选择规则

```
| 场景 | 推荐 | 示例 |
|------|------|------|
| 纯数学公式（无中文） | MathTex | MathTex(r"E = mc^2") |
| 多行对齐公式 | MathTex | MathTex(r"\begin{align*}...\end{align*}") |
| 公式中有中文注释                  | Tex（必须配合 ctex 模板） | Tex(r"质能方程 $E=mc^2$...") |
| 纯文本说明（无公式） | Text | Text("这是一个说明") |
```

### 5.3 强制规范

1. 数学公式必须用 MathTex，除非包含中文
2. 中文字符禁止出现在 MathTex 中（会报错）
3. Tex 中的公式必须用 $...$ 包裹
4. 多行公式优先用 MathTex + align\* 环境
5. 禁止使用原始 LaTeX 字符串直接传给 Manim
6. 禁止使用 Text() 渲染任何数学内容（包括变量名如 `F_1`、下标如 `v_max`、希腊字母等）。LaTeX 可渲染所有数学符号，必须统一使用 MathTex 或 Tex+ctex

### 5.4 代码示例

正确：

```
formula = MathTex(r"\frac{d}{dx} x^2 = 2x")
multi = MathTex(r"\begin{align*} (x+y)^2 &= x^2 + 2xy + y^2 \\ &= x^2 + y^2 + 2xy \end{align*}")
mixed = Tex(r"导数 $\frac{d}{dx} x^2 = 2x$ 表示变化率")
```

错误：

```
bad = MathTex(r"能量 E = mc^2")  # MathTex 中包含中文
bad2 = Tex(r"E = mc^2 是质能方程")  # 公式未用 $ 包裹
```

### 5.5 常见数学环境速查

```
| 场景 | 推荐 | 备选 |
|------|------|------|
| 单行公式 | MathTex | Tex + $$ |
| 多行推导 | MathTex + align* | Tex + align* |
| 矩阵 | MathTex + matrix | Tex + pmatrix |
| 分段函数 | MathTex + cases | — |
```

## 6. 大运算符下标规范（强制）

### 6.1 适用对象

- 求和：`\sum`
- 积分：`\int`
- 乘积：`\prod`
- 最值：`\max`、`\min`
- 极限：`\lim`

### 6.2 下标写法

- 使用 `_{...}` 正确包裹下标内容
- 多字符下标必须用花括号：`\sum_{i=1}^{n}` ✅，`\sum_i=1^n` ❌

### 6.3 下标位置控制

- 行内公式默认下标在右下角：`$\sum_{i=1}^{n} x_i$`
- 强制下标在正下方：使用 `\limits`：`$\sum\limits_{i=1}^{n} x_i$`
- 在 `\[ ... \]` 或 `align*` 环境中，下标自动在正下方

### 6.4 正确示例

```latex
# 行内公式
$\max_{x \in X} f(x)$

# 强制正下方
$\max\limits_{x \in X} f(x)$

# 多行环境
\begin{align*}
\max_{x \in X} f(x) &= 5 \\
\min_{y \in Y} g(y) &= 2
\end{align*}
```

### 6.5 禁止行为

- 禁止拆分：`\max` + `\_{x \in X}`` 分开写
- 禁止遗漏花括号：`\max_x \in X`
- 禁止在 MathTex 中混入中文注释

### 6.6 最大值/最小值与变量组合

**标准写法**：

- 变量下标：`Z_{\max}`、`Z_{\min}`

**示例**：

```latex
Z_{\max} = \max_{x \in X} f(x) \quad
Z_{\min} = \min_{y \in Y} g(y)
```

## 7. 向量与字体规范（强制）

### 7.1 向量表示

- 箭头向量：`\vec{v}` 或 `\vec{AB}`
- 粗体向量：`\mathbf{v}` 或 `\bm{v}`（需 `\usepackage{bm}`）

### 7.2 选择规则

| 场景          | 推荐          | 示例                   |
| ------------- | ------------- | ---------------------- |
| 单字母向量    | `\vec{v}`     | `\vec{v} = (v_1, v_2)` |
| 多字母/点向量 | `\mathbf{AB}` | `\mathbf{AB}`          |
| 物理矢量      | `\vec{F}`     | `\vec{F} = m\vec{a}`   |

### 7.3 禁止行为

- 禁止直接使用 `v` 表示向量（应使用 `\vec{v}`）
- 禁止混用 `\mathbf` 和 `\vec` 表示同一向量

## 8. 省略号规范

| 命令     | 含义                     | 示例                       |
| -------- | ------------------------ | -------------------------- |
| `\dots`  | 低三点，用于列表末尾     | `a_1, a_2, \dots, a_n`     |
| `\cdots` | 居中三点，用于运算符之间 | `x_1 + x_2 + \cdots + x_n` |
| `\vdots` | 垂直三点                 | 矩阵中的行省略             |
| `\ddots` | 对角线三点               | 矩阵中的对角线省略         |

### 使用规则

- 矩阵中优先使用 `\cdots`、`\vdots`、`\ddots`
- 数列或列表中优先使用 `\dots`

## 9. 常用数理符号表

### 9.1 希腊字母

| 命令       | 符号 | 命令     | 符号 |
| ---------- | ---- | -------- | ---- |
| `\alpha`   | α    | `\beta`  | β    |
| `\gamma`   | γ    | `\delta` | δ    |
| `\epsilon` | ε    | `\zeta`  | ζ    |
| `\eta`     | η    | `\theta` | θ    |
| `\iota`    | ι    | `\kappa` | κ    |
| `\lambda`  | λ    | `\mu`    | μ    |
| `\nu`      | ν    | `\xi`    | ξ    |
| `\pi`      | π    | `\rho`   | ρ    |
| `\sigma`   | σ    | `\tau`   | τ    |
| `\upsilon` | υ    | `\phi`   | φ    |
| `\chi`     | χ    | `\psi`   | ψ    |
| `\omega`   | ω    |          |      |

### 9.2 数学常量

| 命令         | 符号 | 含义                 |
| ------------ | ---- | -------------------- |
| `\infty`     | ∞    | 无穷大               |
| `\pi`        | π    | 圆周率               |
| `\e`         | e    | 自然常数（直接写 e） |
| `\mathrm{i}` | i    | 虚数单位             |

### 9.3 关系运算符

| 命令      | 符号 | 含义     |
| --------- | ---- | -------- |
| `\neq`    | ≠    | 不等于   |
| `\leq`    | ≤    | 小于等于 |
| `\geq`    | ≥    | 大于等于 |
| `\approx` | ≈    | 约等于   |
| `\equiv`  | ≡    | 恒等于   |

### 9.4 集合符号

| 命令        | 符号 | 含义   |
| ----------- | ---- | ------ |
| `\in`       | ∈    | 属于   |
| `\notin`    | ∉    | 不属于 |
| `\subset`   | ⊂    | 包含于 |
| `\supset`   | ⊃    | 包含   |
| `\cup`      | ∪    | 并集   |
| `\cap`      | ∩    | 交集   |
| `\emptyset` | ∅    | 空集   |

### 9.5 逻辑符号

| 命令       | 符号 | 含义     |
| ---------- | ---- | -------- |
| `\forall`  | ∀    | 对于任意 |
| `\exists`  | ∃    | 存在     |
| `\implies` | ⇒    | 蕴含     |
| `\iff`     | ⇔    | 当且仅当 |

## 10. LaTeX Don't 违禁样例库

> **负向约束（Don't）比正向规则（Do）记忆强度高 3 倍。**
> 以下每一条对应一种已知的生产事故，代码写成这样 → 画面炸成这样。

### D1：MathTex 中包含中文字符

```python
# ❌ DON'T：MathTex 不支持中文，渲染报错 "Package inputenc Error"
bad = MathTex(r"能量 E = mc^2")

# ✅ DO：中文用 Tex 包裹，公式用 $...$
good = Tex(r"能量 $E = mc^2$")

# ❌ DON'T：中文下标未包裹，编译失败
bad = MathTex(r"F_{弹} = kx")

# ✅ DO：中文下标用 \text{} 包裹
good = MathTex(r"F_{\text{弹}} = kx")
```

**画面炸成**：黑色错误底纹 + 编译失败红字，或公式直接不渲染

---

### D2：下标花括号缺失或错位

```python
# ❌ DON'T：多字符下标未包裹花括号
bad = MathTex(r"\sum_i=1^n x_i")      # i=1^n 被解析为 i=1 的 n 次方
bad = MathTex(r"x_{ij} = y_{ij}")      # ij 被当作单个字符下标

# ✅ DO：每个下标独立包裹花括号
good = MathTex(r"\sum_{i=1}^{n} x_i")
good = MathTex(r"x_{ij} = y_{ij}")     # ij 双字符下标，LaTeX 自动合并
```

**画面炸成**：下标显示错误（i=1 被渲染为上标 n，或显示为 ij 而非 i,j 分开）

---

### D3：公式拆分导致的碎片化

```python
# ❌ DON'T：将多行公式拆为多个 MathTex（对齐线断裂）
row1 = MathTex(r"E = mc^2")
row2 = MathTex(r"= 3\times10^8")       # 对齐线消失，间距不可控

# ✅ DO：整体放入 align* 环境
good = MathTex(r"\begin{align*} E &= mc^2 \\ &= 3\times10^8 \end{align*}")

# ❌ DON'T：将公式原子拆分到独立 MathTex 按行排列（破坏原子完整性）
step1 = MathTex(r"x =")
step2 = MathTex(r"\frac{1}{2}")       # 公式被割裂，两段之间间距无法控制

# ✅ DO：每个原子保持独立 MathTex，但整体排列时不分割同一表达式的组成部分
group = VGroup(
    MathTex(r"x = \frac{1}{2}"),       # 原子内部完整
    MathTex(r"y = 2x"),
).arrange(DOWN, buff=0.5)
```

**画面炸成**：等号不对齐、间距忽大忽小、公式碎片感明显

---

### D4：多行环境缺少 `*`

```python
# ❌ DON'T：使用 align（自动编号）导致右侧多余编号干扰画面
bad = MathTex(r"\begin{align} x^2 &= 1 \\ x &= \pm 1 \end{align}")

# ✅ DO：使用 align*（无编号）
good = MathTex(r"\begin{align*} x^2 &= 1 \\ x &= \pm 1 \end{align*}")
```

**画面炸成**：右侧出现 "(1)" "(2)" 编号，遮挡内容或溢出画布

---

### D5：极限下标位置错误

```python
# ❌ DON'T：lim 下标未放在正下方（行内时默认在右下角）
bad = MathTex(r"lim_{x\to 0} x = 0")   # 下标在右下角，阅读困难

# ✅ DO：使用 \limits 强制正下方（行内公式）
good = MathTex(r"\lim\limits_{x\to 0} x = 0")

# ✅ 或：在 align* / \[ 环境中自动正下方
good2 = MathTex(r"\lim_{x\to 0} x = 0")  # 在 align* 环境中自动正下方
```

**画面炸成**：下标拥挤在右下角，与 lim 紧贴，难以区分上下标关系

---

### D6：向量表示混用

```python
# ❌ DON'T：同一场景中混用 \vec 和 \mathbf
mixed = MathTex(r"\vec{v} + \mathbf{w}")  # 两种风格，视觉不统一

# ✅ DO：同场景使用同一种向量表示法
good = MathTex(r"\vec{v} + \vec{w}")
```

**画面炸成**：同一动画中出现两种粗细/长度的箭头，混淆向量类型

---

### D7：省略号类型错误

```python
# ❌ DON'T：在矩阵对角线使用 \dots（低三点）
bad = MathTex(r"\begin{matrix} a_{11} & \dots & a_{1n} \\ \vdots & \ddots & \vdots \end{matrix}")

# ✅ DO：矩阵对角线使用 \ddots（对角三点）
good = MathTex(r"\begin{matrix} a_{11} & \cdots & a_{1n} \\ \vdots & \ddots & \vdots \end{matrix}")
```

**画面炸成**：对角线上的省略号方向错误，与矩阵行列不对齐

---

### D8：未转义的上下标符号

```python
# ❌ DON'T：在 math mode 外直接写 _ 或 ^（需转义或用 \text）
bad = Tex(r"x_1 + x_2 = y_3")           # _ 未转义，Tex 可能报错

# ✅ DO：纯公式用 MathTex；混排时 _ 在公式内自动转义
good_formula = MathTex(r"x_1 + x_2 = y_3")
good_mixed = Tex(r"$x_1 + x_2 = y_3$ 的解为")

# ❌ DON'T：在 MathTex 中使用未包裹的中文注释
bad = MathTex(r"x^2 \text{的平方} = y")  # \text{} 内部中文可能有字体问题

# ✅ DO：中文注释用 Tex；公式用纯 MathTex
good = VGroup(
    MathTex(r"x^2 = y"),
    Tex(r"（平方关系）")
).arrange(RIGHT)
```

**画面炸成**：字符消失、格式错乱或编译警告

---

### D9：分式嵌套过深导致字号自动缩小

```python
# ❌ DON'T：分式嵌套超过 2 层时自动字体过小，难以阅读
bad = MathTex(r"\frac{1}{\frac{1}{x}+1}")  # 自动缩小为极小字号

# ✅ DO：分式嵌套不超过 2 层，超过时拆步骤或用 \tfrac
good = MathTex(r"\frac{1}{\tfrac{1}{x}+1}")  # 强制用小字号分式
good2 = MathTex(r"\frac{x}{1+x}")            # 简化表达式
```

**画面炸成**：内部分式字号极小（可能 < 10pt），完全不可读

---

### D10：绝对值符号误用

```python
# ❌ DON'T：使用 | 作为绝对值符号（竖线在 math mode 中间距不当）
bad = MathTex(r"|x - 1| = 0")

# ✅ DO：使用 \left| 和 \right| 自动调整大小
good = MathTex(r"\left|x - 1\right| = 0")

# ❌ DON'T：矩阵行列式也用 |...|（与绝对值混淆）
bad2 = MathTex(r"|A| = ad - bc")  # 应为行列式

# ✅ DO：行列式使用 \det() 或 \left|...\right| 配合 align* 环境
good2 = MathTex(r"\det(A) = ad - bc")
```

**画面炸成**：竖线高度不匹配、内容溢出容器

---

### D11：P1 嵌套定界符

```python
# ❌ DON'T：$...$ 内嵌套 $，导致正则解析崩溃
bad = MathTex(r"$\sum_{i=1}^{$n$}$")   # 内层 $n$ 是嵌套

# ✅ DO：内层用 \(...\) 替代
good = MathTex(r"$\sum_{i=1}^{\(n\)}$")

# ❌ DON'T：中文下标 + 嵌套双重问题
bad2 = MathTex(r"$v_{共} = $v_{初}$")   # 嵌套且中文下标未包裹

# ✅ DO：中文下标用 \text{}，表达式合并
good2 = MathTex(r"$v_{\text{共}} = v_{\text{初}}$")
```

**画面炸成**：内侧 $ 提前配对，后续内容被解析为普通文本，公式渲染完全错位

---

### D12：P4 斜杠除法

```python
# ❌ DON'T：数学表达式中除法用斜杠
bad = MathTex(r"$\frac{a/b + c}{d}$")    # 需用 \frac

# ✅ DO：全部用 \frac 表示除法
good = MathTex(r"$\frac{\frac{a}{b} + c}{d}$")

# ❌ DON'T：物理表达式中用斜杠
bad2 = MathTex(r"$F = m \cdot a / t$")   # a/t 应为分式

# ✅ DO：\frac 用于物理量
good2 = MathTex(r"$F = \frac{m \cdot a}{t}$")

# ✅ 单位例外（允许斜杠）
speed = MathTex(r"$\frac{v}{m/s}$")  # m/s 是单位，正常
```

**画面炸成**：斜杠除法导致分子分母关系不明确，视觉优先级混乱

---

### D13：P5 表达式碎片化

```python
# ❌ DON'T：由 + = 等运算符连接的量被拆到多个 $...$ 块
bad1 = MathTex(r"$E$") + MathTex(r"$ = mc^2$")  # 等号跨块
bad2 = Tex(r"$x$ 与 $y$ 的和为 $x+y$")           # + 跨块

# ✅ DO：运算符连接的量必须在同一个 $...$ 内
good1 = MathTex(r"$E = mc^2$")
good2 = Tex(r"$x$ 与 $y$ 的和为 $x+y$")           # x+y 在同一块内

# ❌ DON'T：多行推导的中间等号被拆分
row1 = MathTex(r"$(x+y)^2$")
row2 = MathTex(r"$= x^2 + 2xy + y^2$")  # 等号在块外

# ✅ DO：多行用 align* 整体包裹
good3 = MathTex(
    r"\begin{align*} (x+y)^2 &= x^2 + 2xy + y^2 \\ "
    r"&= x^2 + y^2 + 2xy \end{align*}"
)
```

**画面炸成**：等号对齐线断裂、间距忽大忽小、碎片感明显

---

### D14：中文下标未包裹

```python
# ❌ DON'T：中文下标未用 \text{} 包裹
bad = MathTex(r"$v_{\text{共}}$")   # 若去掉 \text{}，会报错或显示异常

# ✅ DO：中文下标必须 \text{} 包裹
good = MathTex(r"$F_{\text{弹}} = kx$")
good2 = MathTex(r"$E_{\text{动}} = \frac{1}{2}mv^2$")

# ❌ DON'T：多行环境中中文下标遗漏
bad2 = MathTex(
    r"\begin{align*} v_{\text{共}} &= v_{\text{初}} + at \\ "
    r"E_k &= \frac{1}{2}mv^2 \end{align*}"
)
# 检查每个 _ 后的 { } 内容是否包含中文且未包裹
```

**画面炸成**：编译警告、字符显示异常或直接报错

---

### D15：P6 多行环境定界符错误

```python
# ❌ DON'T：多行环境用 $...$ 包裹（行内模式）
bad = MathTex(r"$\begin{align*} a &= b \\ c &= d \end{align*}$")
# Manim 侧：行内多行环境会被压缩成一维渲染，布局完全破坏

# ✅ DO：多行环境用 $$...$$ 包裹（行间模式）
good = MathTex(r"$$\begin{align*} a &= b \\ c &= d \end{align*}$$")

# ✅ 备选：align* 在 Manim 中直接写（不包裹 $...$）
good2 = MathTex(
    r"\begin{align*} a &= b \\ c &= d \end{align*}", display_only=False
)

# ❌ DON'T：matrix / array / gather 环境同样需注意
bad2 = MathTex(r"$\begin{matrix} 1 & 2 \\ 3 & 4 \end{matrix}$")
```

**画面炸成**：多行环境被压缩为一行、等号/对齐线消失、字体被强制缩小
