# SPEC: Vaporwave Elegant AI Multi-Agent System

## 1. Concept & Vision

**LUXE. OPULENT. MARBLE.** — 一个将奢华蒸汽波美学与高端大理石纹理融合的 AI 多智能体系统界面。界面散发出拜占庭皇室的奢华感，结合 80 年代蒸汽波的复古未来主义。每个元素都沉浸在香槟金、玫瑰金和深紫 plum 的渐变中，仿佛用户正在一座金色大理石宫殿中与 AI 对话。

**情感目标**: 用户感觉自己像一个帝王，在金色管道(GOLD PIPE)中流淌着智慧。

## 2. Design Language

### Aesthetic Direction
- **风格**: 奢华蒸汽波 × 拜占庭宫廷 × 大理石神殿
- **关键词**: Marble veins, Gold filigree, Champagne bubbles, Velvet shadows, Crystal shimmer

### Color Palette
```css
--color-primary: #F7E7CE;      /* Champagne - 主高光 */
--color-secondary: #B76E79;     /* Rose Gold - 副强调 */
--color-accent: #DDA0DD;       /* Plum - 紫色点缀 */
--color-bg-deep: #1A1520;      /* Deep Plum - 深色背景 */
--color-bg-wine: #2D1F2D;      /* Dark Wine - 卡片背景 */
--color-text: #FFFFFF;         /* White - 主文字 */
--color-almond: #E8D5C4;       /* Almond - 辅助色 */
--color-purple-light: #C9A0DC; /* Light Purple - 辅助色 */
--color-cream: #F0E6DC;        /* Cream - 辅助色 */
```

### Typography
- **Display**: Cormorant (Google Fonts) - 优雅衬线，用于标题
- **Body**: Playfair Display (Google Fonts) - 经典衬线，用于正文
- **Accent**: Cinzel (Google Fonts) - 装饰字体，用于按钮和状态

### Spatial System
- 基础间距: 8px 网格
- 容器圆角: 16px-24px
- 边框: 1px 渐变金边
- 阴影: 多层柔和发光 + 大理石纹理叠加

### Motion Philosophy
- **入场动画**: 优雅淡入 + 微微上浮 (400ms ease-out)
- **悬停效果**: 金色光晕扩散 (200ms)
- **状态转换**: 丝绸般的渐变过渡 (300ms)
- **背景**: 缓慢流动的渐变云雾 (20s 循环)
- **大理石纹理**: 微微闪烁的光泽变化

### Visual Assets
- 大理石纹理 (CSS 渐变模拟)
- 金色 filigree 装饰边框
- 优雅分隔线
- 微光粒子效果
- 玻璃拟态卡片

## 3. Layout & Structure

### Page Structure
```
┌─────────────────────────────────────────────────────────────┐
│  MARBLE HEADER - Logo + Title + Token Wealth Bar           │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│   LUXE       │           CHAT AREA                          │
│   SIDEBAR    │    ┌─────────────────────────────────┐       │
│              │    │  AI Response Card               │       │
│  - Luxe      │    └─────────────────────────────────┘       │
│  - Opulent   │    ┌─────────────────────────────────┐       │
│  - Marble    │    │  User Message Card              │       │
│  - Gold      │    └─────────────────────────────────┘       │
│  - Champagne  │                                              │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│              │  ┌─────────────────────────────────────────┐  │
│  LUXURY      │  │  INPUT AREA - Marble texture           │  │
│  STATUS      │  └─────────────────────────────────────────┘  │
│              │           [CHAMPAGNE]                        │
└──────────────┴──────────────────────────────────────────────┘
```

### Responsive Strategy
- Desktop (>1200px): 完整侧边栏 + 宽聊天区
- Tablet (768-1200px): 收起侧边栏，浮动导航
- Mobile (<768px): 底部导航，全屏聊天

## 4. Features & Interactions

### Chat Interface
- 用户输入 → 消息卡片 (右对齐，香槟色边框)
- AI 回复 → 消息卡片 (左对齐，玫瑰金边框)
- 打字效果: 光标闪烁 + 逐字显示
- 空状态: "Dry glass." + 空杯子 SVG 动画

### Agent Status Display
- **Indulging** (运行中): 金色脉冲光环
- **Wasting** (终止中): 红色渐渐消失
- **Restored** (已恢复): 绿色钻石闪耀
- **Awaiting** (等待中): 银色彩虹流动
- **Diminished** (失败): 紫色暗光

### Token Wealth Bar
- 进度条显示已用/总量
- 金色填充 + 香槟泡沫动画
- 数值以 "₵" 符号展示

### Luxury Actions
| 原词 | 奢华词 | 颜色 |
|------|--------|------|
| Submit | CHAMPAGNE | #F7E7CE |
| Deploy | INDULGE | #B76E79 |
| Terminate | WASTE | #DDA0DD |
| Cancel | DIMINISH | #C9A0DC |
| Retry | RESTORE | #E8D5C4 |
| Save | COLLECT | #F0E6DC |

### Status Messages
- Loading: "Pouring champagne..."
- Processing: "Living lavishly..."
- Success: "Excellence achieved."
- Error: "Spilled champagne."
- Empty: "Dry glass."
- Waiting: "Awaiting refill."

### Side Navigation
- 5个导航项: Luxe / Opulent / Marble / Gold / Champagne
- 悬停时: 金色光晕 + 图标放大
- 激活时: 底部金色滑块

## 5. Component Inventory

### Message Card
- **Default**: 深酒红背景，1px 金色渐变边框
- **User**: 右对齐，香槟色强调
- **AI**: 左对齐，玫瑰金强调
- **Hover**: 边框发光增强

### Action Button
- **Default**: 透明背景，金色边框，渐变文字
- **Hover**: 金色光晕扩散，背景微亮
- **Active**: 按下缩放0.98，内发光
- **Disabled**: 50%透明度，无交互

### Status Badge
- 圆角胶囊形状
- 状态色 + 微光动画
- 图标 + 文字组合

### Navigation Item
- **Default**: 银灰色文字
- **Hover**: 金色光晕，淡入
- **Active**: 金色文字，底部指示条

### Token Wealth Bar
- 外框: 金色边框，大理石纹理
- 填充: 香槟金渐变，泡沫动画
- 标签: Cinzel 字体，₵ 符号

## 6. Technical Approach

- **Framework**: Vanilla HTML/CSS/JS (单文件部署)
- **Fonts**: Google Fonts CDN (Cormorant, Playfair Display, Cinzel)
- **Icons**: 内联 SVG (自定义奢华风格)
- **Animations**: CSS @keyframes + CSS Variables
- **Layout**: CSS Grid + Flexbox
- **No external dependencies** for maximum performance

### Performance Targets
- First Contentful Paint: <1.5s
- Bundle size: <50KB
- Lighthouse Performance: >90
