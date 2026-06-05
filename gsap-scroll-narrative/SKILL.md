---
name: gsap-scroll-narrative
description: 用于创建 GSAP + ScrollTrigger + Lenis 滚动叙事动画的指南。当用户需要实现品牌故事页、产品发布页、营销落地页等滚动驱动的叙事性动画时使用。涵盖 pin 固定穿梭、多层视差、文字逐字/逐行揭示、Lottie 微动画、CSS Mask 层叠遮罩、Globe.GL 3D 地球、性能优化和移动端适配。
---

# GSAP 滚动叙事动画 Skill

## 初始化顺序（必须遵守）

顺序错误会导致动画延迟或不同步。

1. 先注册 GSAP 插件：`gsap.registerPlugin(ScrollTrigger, CustomEase, SplitText, Flip, Draggable, ScrollToPlugin)`
2. 初始化 Lenis 平滑滚动
3. 连接：`lenis.on('scroll', ScrollTrigger.update)`
4. 最后才创建 ScrollTrigger 实例

**最小集成代码：**

```javascript
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { CustomEase } from "gsap/CustomEase";
import { SplitText } from "gsap/SplitText";
import { Flip } from "gsap/Flip";
import { Draggable } from "gsap/Draggable";
import { ScrollToPlugin } from "gsap/ScrollToPlugin";
import Lenis from "lenis";

// 注册所有插件
gsap.registerPlugin(ScrollTrigger, CustomEase, SplitText, Flip, Draggable, ScrollToPlugin);

const lenis = new Lenis({
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  smoothWheel: true,
});

lenis.on("scroll", ScrollTrigger.update);

gsap.ticker.add((time) => {
  lenis.raf(time * 1000);
});
gsap.ticker.lagSmoothing(0);

// 最后创建 ScrollTrigger 实例
// gsap.timeline({ scrollTrigger: { ... } });
```

---

## 核心模式

本 skill 包含六个设计模式，按需组合使用。

### 模式一：Pin 固定穿梭（舷窗穿越）

用于实现"镜头推进/穿过物体"的沉浸式效果。以 Jesko Jets 的舷窗效果为典型：前景舷窗框静止，中景云层/天空推进，后景内容淡出。

**行为要求：**

- 使用 `pin: true` 固定 section，通过 `end: "+=N%"` 控制固定期间滚动距离
- 背景层做 `scale` 放大动画（从 1 到 >1），产生推进感
- 中景内容层做 `scale` 缩小 + `opacity` 淡出动画，产生"被甩在身后"的错觉
- 前景遮挡层（如舷窗框、舱门轮廓）只做 `opacity` 淡入，**不做任何 transform 动画**，保持静止以维持透视一致性
- 内容层在 pin 中后期淡出
- 设置 `scrub: 1`（数值而非 true）实现惯性跟随
- 设置 `anticipatePin: 1` 减少页面跳动
- 优先使用 `gsap.fromTo()` 定义起始和结束状态，避免反向滚动时状态漂移

**最小代码模板：**

```javascript
gsap
  .timeline({
    scrollTrigger: {
      trigger: ".pin-section",
      start: "top top",
      end: "+=150%",
      pin: true,
      scrub: 1,
      anticipatePin: 1,
    },
  })
  .fromTo(".bg-layer", { scale: 1 }, { scale: 1.4, ease: "none" }, 0)
  .fromTo(
    ".content-layer",
    { opacity: 1, scale: 1 },
    { opacity: 0, scale: 0.9, ease: "power2.in" },
    0.3,
  )
  .fromTo(".mask-layer", { opacity: 0 }, { opacity: 1, ease: "none" }, 0.5);
```

**何时用：** 需要"镜头推进/穿过"效果时（如 Jesko Jets 舷窗穿越风格）

**何时不用：** 只需要简单的远近层次感时，用模式二

**移动端：** 禁用 pin 固定，降级为基础入场动画（`opacity` + `translateY`）

---

### 模式二：多层视差

用于实现远近层次感，是辅助效果而非核心穿梭质感来源。

**行为要求：**

- 背景层 yPercent -20 左右（移动最慢）
- 内容层 yPercent -40 左右（中等速度）
- 前景层 yPercent -60 左右或静止（移动最快）
- 只对 `transform` 和 `opacity` 做动画（GPU 加速）
- 使用 `scrub: 1`

**最小代码模板：**

```javascript
gsap.utils.toArray(".parallax-layer").forEach((layer, i) => {
  const speed = [-20, -40, -60][i] || -30;
  gsap.fromTo(
    layer,
    { yPercent: 0 },
    {
      yPercent: speed,
      ease: "none",
      scrollTrigger: {
        trigger: layer.parentElement,
        start: "top bottom",
        end: "bottom top",
        scrub: 1,
      },
    },
  );
});
```

**何时用：** 只需要简单远近层次感、不需要穿过效果时

**何时不用：** 需要镜头推进/穿过效果时，用模式一

**移动端：** 完全禁用视差层动画（CSS `transform: none !important`）

---

### 模式三：叙事性滚动（文字揭示）

用于控制线性内容的展示节奏。结合 GSAP SplitText 实现逐字/逐行/逐词揭示。

**行为要求：**

- 建议每个阶段的进场动画在 `start: "top 80%"` 触发
- 使用 `scrub: 1` 而非 `true`
- 同一页面不要混用"阶段式"和"单元素驱动式"两种滚动模式
- 优先使用 `gsap.fromTo()` 确保双向滚动一致性
- 文字揭示使用 SplitText 分割后配合 `stagger` 动画

**最小代码模板：**

```javascript
// 逐行揭示
gsap.utils.toArray(".story-stage").forEach((stage) => {
  const split = new SplitText(stage.querySelectorAll(".stage-content"), {
    type: "lines,words",
    linesClass: "split-line",
  });

  gsap.fromTo(
    split.words,
    { opacity: 0, y: 40 },
    {
      opacity: 1,
      y: 0,
      stagger: 0.03,
      duration: 0.8,
      ease: "power3.out",
      scrollTrigger: {
        trigger: stage,
        start: "top 80%",
        end: "top 30%",
        scrub: 1,
      },
    },
  );
});

// 逐字揭示（标题）
const charSplit = new SplitText("[data-char-reveal]", { type: "chars" });
gsap.fromTo(
  charSplit.chars,
  { opacity: 0, y: 100 },
  {
    opacity: 1,
    y: 0,
    stagger: 0.02,
    duration: 1,
    ease: "power4.out",
    scrollTrigger: {
      trigger: "[data-char-reveal]",
      start: "top 85%",
    },
  },
);
```

**何时用：** 长页面品牌故事、产品特性逐层展开、标题文字动画

**何时不用：** 页面内容短、用户需要快速扫描时

**移动端：** 缩短动画时长到桌面端的 50%，减少叙事阶段数（5-6 → 3-4）

---

### 模式四：层叠穿越切换

用于实现模块间的无缝转场。

**行为要求：**

- 初始化时靠前的 section 设置更高 z-index
- Exit 动画：当前 section 缩小淡出，保持高 z-index
- Enter 动画：下一 section 从放大状态缩小到正常 + 淡入，z-index 比当前低，从后方穿出
- Exit 和 Enter 使用同一 scrollTrigger 同时驱动，确保无空白帧
- 层叠管理：
  - 前景遮挡层：z-index 30，`absolute`，只做 opacity
  - 内容层：z-index 20，`absolute`，可位移/缩放
  - 背景层：z-index 10，`absolute`，可缩放/视差
  - 容器：z-index 1，`relative`，pin 触发点

**最小代码模板：**

```javascript
// Section A: Exit
gsap.fromTo(
  ".section-a",
  { scale: 1, opacity: 1 },
  {
    scale: 0.9,
    opacity: 0,
    scrollTrigger: {
      trigger: ".section-a",
      start: "bottom bottom",
      end: "bottom top",
      scrub: 1,
    },
  },
);

// Section B: Enter (z-index 低于 section-a)
gsap.fromTo(
  ".section-b",
  { scale: 1.1, opacity: 0 },
  {
    scale: 1,
    opacity: 1,
    scrollTrigger: {
      trigger: ".section-b",
      start: "top bottom",
      end: "top top",
      scrub: 1,
    },
  },
);
```

**何时用：** 全屏区块间的电影感转场

**何时不用：** 常规内容流、需要保持滚动连续感时

**移动端：** 简化为基础淡入淡出，禁用 scale 变换

---

### 模式五：CSS Mask 层叠遮罩

用于实现非矩形边界的层叠效果（如舷窗形状、地球轮廓、蓝图遮罩）。

**行为要求：**

- 使用 `-webkit-mask-image` / `mask-image` 配合 PNG/WebP 遮罩图
- 遮罩图使用黑白或透明通道定义可见区域
- 通过 CSS 变量动态控制 `mask-position` 和 `mask-size` 实现动画
- 配合 `will-change: transform` 优化性能

**最小代码模板：**

```css
.masked-layer {
  -webkit-mask-image: url("mask-shape.webp");
  mask-image: url("mask-shape.webp");
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  --mask-x: 50%;
  --mask-y: 50%;
  --mask-size: 100% 150%;
  -webkit-mask-position: var(--mask-x) var(--mask-y);
  mask-position: var(--mask-x) var(--mask-y);
  -webkit-mask-size: var(--mask-size);
  mask-size: var(--mask-size);
  will-change: transform;
}
```

```javascript
// 动态控制遮罩位置产生推进感
gsap.to(".masked-layer", {
  "--mask-size": "150% 200%",
  "--mask-y": "30%",
  scrollTrigger: {
    trigger: ".masked-layer",
    start: "top center",
    end: "bottom top",
    scrub: 1,
  },
});
```

**何时用：** 需要非矩形边界（舷窗、地球仪、蓝图轮廓）的层叠效果

**何时不用：** 标准矩形布局无需遮罩

**移动端：** 简化遮罩复杂度，使用更低分辨率的遮罩图

---

### 模式六：Lottie 微动画集成

用于实现复杂的矢量动画（如滚动图标、Logo 动画、状态指示器）。

**行为要求：**

- 使用 `lottie-web` 库加载 JSON 动画文件
- 通过 `data-json` 属性声明动画资源路径
- 控制播放模式：`play: true` 自动播放、`loop: true` 循环
- 与 ScrollTrigger 联动时可控制播放进度

**最小代码模板：**

```javascript
import lottie from "lottie-web";

// 初始化 Lottie 元素
document.querySelectorAll("[data-json]").forEach((el) => {
  const animation = lottie.loadAnimation({
    container: el,
    renderer: "svg",
    loop: el.hasAttribute("loop") || false,
    autoplay: el.hasAttribute("play") || false,
    path: el.dataset.json,
  });

  // 存储引用供 ScrollTrigger 控制
  el._lottie = animation;
});

// 滚动联动播放
ScrollTrigger.create({
  trigger: ".lottie-section",
  start: "top bottom",
  end: "bottom top",
  onUpdate: (self) => {
    const lottieEl = document.querySelector(".lottie-animated");
    if (lottieEl && lottieEl._lottie) {
      lottieEl._lottie.goToAndStop(
        self.progress * lottieEl._lottie.totalFrames,
        true,
      );
    }
  },
});
```

**何时用：** 复杂矢量动画、滚动指示器、品牌 Logo 动画

**何时不用：** 简单动画可用纯 CSS/JS 实现时

**移动端：** 降低 Lottie 渲染质量或替换为静态图

---

## 全局规则

### Start/End 格式

- 格式：`"[元素边界] [视口边界]"`
- 边界位置：`top` / `center` / `bottom`
- 不是像素值
- 开发阶段开启 `markers: true` 可视化调试

### Scrub 取值

- `scrub: true`：严格跟随滚动，零延迟（仅适合进度条类精确映射）
- `scrub: 1`（数值）：有惯性跟随，叙事性滚动推荐
- 叙事性滚动应使用数值 scrub

### 动画声明原则

- ScrollTrigger 场景下**优先使用 `gsap.fromTo()`** 定义起始和结束状态
- 避免反向滚动时元素状态无法复位导致的动画错乱
- 只对 `transform` 和 `opacity` 做动画，确保 GPU 加速

### CSS 配合规范

```css
.pin-section {
  position: relative;
  overflow-x: hidden;
}

.anim-layer {
  position: absolute;
  will-change: transform, opacity;
}

/* 涉及 3D 透视时 */
.perspective-container {
  transform-style: preserve-3d;
}

/* 遮罩层 */
.masked-element {
  -webkit-mask-image: url("mask.webp");
  mask-image: url("mask.webp");
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
}
```

---

## Pin 副作用处理

- pin 会改变页面高度，可能导致后续动画位置偏移
- 使用 `anticipatePin: 1` 减少跳动
- 计算好 pin 高度，调整后续 section 的 start
- 图片/字体加载后必须刷新：

```javascript
Promise.all([document.fonts.ready, ...imagePromises]).then(() =>
  ScrollTrigger.refresh(),
);

window.addEventListener("load", () => ScrollTrigger.refresh());
```

---

## 资源预加载策略

- **首屏关键图**：`<link rel="preload">` 或 `fetchpriority="high"`
- **非首屏图片**：`loading="lazy"` + `decoding="async"`
- **视频背景**：静音自动播放、`preload="auto"`，准备静态图兜底
- **字体**：`font-display: swap`，避免 FOIT 导致 ScrollTrigger 高度计算偏差
- **Lottie JSON**：首屏关键动画预加载，非首屏按需加载
- **遮罩图**：与关联图片同时预加载

---

## 性能优化检查清单

按顺序检查：

1. 确保只对 `transform` 和 `opacity` 做动画
2. 确保使用 `requestAnimationFrame`，不直接在 scroll 回调中操作 DOM
3. 非首屏图片使用 `loading="lazy"`
4. 避免在循环中交替读写 DOM（布局抖动）
5. 动画元素添加 `will-change: transform, opacity`
6. 移动端禁用复杂动画
7. Lottie 动画使用 `renderer: 'canvas'` 替代 `'svg'` 提升性能（复杂场景）
8. 遮罩图使用 WebP 格式减少体积

---

## 移动端适配原则

渐进增强。桌面端完整体验，移动端降级：

- 禁用 pin 固定穿梭（降级为基础入场动画）
- 禁用多层视差（CSS `transform: none !important`）
- 缩短动画时长到桌面端的 50%
- 减少叙事阶段数
- Lenis 降低 `duration` 到 0.8
- Lottie 降低渲染质量或替换为静态图
- 简化 CSS Mask 效果

```javascript
const isMobile = window.matchMedia("(max-width: 768px)").matches;

const lenis = new Lenis({
  duration: isMobile ? 0.8 : 1.2,
  // ...
});
```

---

## 框架集成

### React

使用 `gsap.context()` 管理作用域，cleanup 中调用 `ctx.revert()`。

```javascript
useEffect(() => {
  const ctx = gsap.context(() => {
    // 创建 ScrollTrigger 动画
    // 初始化 Lottie
    // 初始化 SplitText
  }, containerRef);

  return () => ctx.revert();
}, []);
```

StrictMode 导致动画执行两次是正常的，不影响生产环境。

### Vue

在 `onMounted` 中初始化，`onUnmounted` 中清理。

```javascript
onMounted(() => {
  // 创建 ScrollTrigger 动画
  // 初始化 Lottie
});

onUnmounted(() => {
  ScrollTrigger.getAll().forEach((t) => t.kill());
});
```

---

## 增强交互效果（效果层面扩展）

补充自 gsap-skills 的效果增强，不替代 Lenis 方案。

### 效果一：布局状态保持

用于页面 resize、元素切换时，元素平滑过渡到新位置（而非跳变）。

**效果描述：** 用户切换 tab、展开/收起面板时，相关元素平滑滑动到新位置，保持视觉连续性。

```javascript
import { Flip } from "gsap/Flip";

gsap.registerPlugin(Flip);

// 获取元素当前状态
const state = Flip.getState(".card");

// DOM 变更后（如删除/添加元素）
card.remove();

// 播放状态过渡动画
Flip.from(state, {
  duration: 0.6,
  ease: "power2.inOut",
  absolute: true,
  onLeave: (element) => {
    // 自定义离开效果
  },
});
```

**何时用：** 列表增删、tab 切换、展开收起等需要保持视觉连续的交互

---

### 效果二：拖拽交互

元素可被用户自由拖拽，带物理惯性。

**效果描述：** 用户可拖动卡片/列表项，手指离开后继续滑动并自然减速。

```javascript
import { Draggable } from "gsap/Draggable";

gsap.registerPlugin(Draggable);

// 创建可拖拽元素（带边界约束）
Draggable.create(".draggable-card", {
  type: "x,y",
  bounds: ".container",
  inertia: true, // 物理惯性
  onDragEnd: function () {
    // 拖拽结束回调
  },
});
```

**何时用：** 卡片拖拽排序、滑动删除、健身/音乐等需要手势交互的场景

---

### 效果三：锚点平滑跳转

点击导航直接滚动到对应位置，带缓动效果。

**效果描述：** 用户点击"产品特性"导航，直接平滑滚动到对应位置，而非瞬间跳转。

```javascript
import { ScrollToPlugin } from "gsap/ScrollToPlugin";

gsap.registerPlugin(ScrollToPlugin);

// 点击锚点导航
document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const target = document.querySelector(link.getAttribute("href"));

    gsap.to(window, {
      duration: 1,
      scrollTo: { y: target, offsetY: 80 },
      ease: "power2.inOut",
    });
  });
});
```

**何时用：** 长页面导航、滚动目录、返回顶部等锚点跳转场景

---

### 效果四：列表重排动画

元素增删/排序时，周围元素自动滑入填补空位。

**效果描述：** 删除一个卡片后，其他卡片自动上浮填补空位，平滑无跳变。

```javascript
import { Flip } from "gsap/Flip";

// 监听列表项增删
function animateListChange() {
  const state = Flip.getState(".list-item");

  // DOM 更新（添加/删除/排序）
  updateList();

  // 播放补位动画
  Flip.from(state, {
    duration: 0.5,
    ease: "power2.out",
    absolute: true,
    stagger: 0.05,
  });
}
```

**何时用：** 待办列表删除、购物车移除商品、排行榜排序等

---

## React 增强：useGSAP Hook

替代手动 useEffect + context，更规范的清理方式。

```javascript
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

// 方式一：推荐（自动清理）
useGSAP(
  () => {
    gsap.to(".element", {
      x: 100,
      scrollTrigger: {
        trigger: ".element",
        start: "top bottom",
      },
    });
  },
  { scope: containerRef },
); // 指定作用域

// 方式二：多动画批量注册
useGSAP(
  () => {
    gsap.utils.toArray(".reveal").forEach((el) => {
      gsap.fromTo(
        el,
        { opacity: 0, y: 50 },
        { opacity: 1, y: 0, scrollTrigger: { trigger: el } },
      );
    });
  },
  { scope: containerRef },
);

// 方式三：带依赖
useGSAP(() => {
  gsap.to(ref.current, { x: value * 100 });
}, [value]);
```

**优势：**

- 自动管理清理，无内存泄漏
- 支持 StrictMode
- 支持批量注册

---

## Vue 增强：完整生命周期

```javascript
import { onMounted, onUnmounted, ref } from "vue";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export default {
  setup() {
    const containerRef = ref(null);
    let ctx = null;

    onMounted(() => {
      ctx = gsap.context(() => {
        // 创建所有 ScrollTrigger 动画
        gsap.utils.toArray(".section").forEach((section) => {
          gsap.fromTo(
            section,
            { opacity: 0, y: 100 },
            {
              opacity: 1,
              y: 0,
              scrollTrigger: {
                trigger: section,
                start: "top 80%",
              },
            },
          );
        });
      }, containerRef.value);
    });

    onUnmounted(() => {
      ctx && ctx.revert(); // 清理所有动画
    });

    return { containerRef };
  },
};
```

---

## 可访问性

- 确保 `prefers-reduced-motion` 生效时动画时长降为 0.01ms

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

- 颜色对比度符合 WCAG AA
- 关键信息不依赖动画传达
- Lottie 动画提供静态替代文本

---

## 常见问题诊断

| 现象               | 成因                             | 解决                                 |
| ------------------ | -------------------------------- | ------------------------------------ |
| 动画不触发         | start/end 值不合适               | 改用 `start: "top 80%"`              |
| 滚动时动画跳动     | scrub 用 true                    | 改为 `scrub: 1`                      |
| Lenis 下动画延迟   | 初始化顺序错误                   | 先 Lenis → update → 再 ScrollTrigger |
| 移动端卡顿         | 视差层太多                       | 移动端禁用视差                       |
| 水平滚动条         | yPercent 溢出                    | 容器加 `overflow-x: hidden`          |
| 图片加载后位置错位 | 未刷新 ScrollTrigger             | 调用 `ScrollTrigger.refresh()`       |
| 没有穿越感         | 用了 yPercent 视差而非 pin+scale | 改用 pin 固定 + 缩放                 |
| 遮罩跟着滚动       | 遮罩层加了 transform             | 遮罩层保持静止，只做 opacity         |
| 转场有空白帧       | Exit 和 Enter 不重叠             | 同一 scrollTrigger 同时驱动          |
| pin 后页面跳动     | 未设置 anticipatePin             | 添加 `anticipatePin: 1`              |
| pin 后后续内容错位 | pin 改变页面高度                 | 计算 pin 高度，调整后续 start        |
| 反向滚动状态错乱   | 使用了 from() 而非 fromTo()      | 改用 `gsap.fromTo()`                 |
| Lottie 动画不同步  | 未与 ScrollTrigger 联动          | 使用 `onUpdate` 控制播放帧           |
| SplitText 文字重叠 | 未等字体加载完成                 | 字体加载后执行 SplitText             |
| 遮罩边缘锯齿       | 遮罩图分辨率不足                 | 使用 2x 分辨率遮罩图                 |
