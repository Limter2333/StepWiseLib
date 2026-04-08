# Retro Diner Modern AI System - SPEC.md

## 1. Concept & Vision

**ORDER UP! FRESH & HOT** — 一个现代版50年代餐厅风格的AI多智能体系统界面。活力与怀旧结合，让用户感觉就像走进一个时尚的餐车吧台，每个AI任务就像点一份热腾腾的餐点。霓虹灯闪烁，铬合金闪闪发光，乙烯基纹理与现代卡片设计交织，营造出温暖而充满能量的用餐氛围。

## 2. Design Language

### Aesthetic Direction
- **风格**: 时尚餐车 / 现代版50年代Diner / 活力怀旧
- **参考**: 1950s American Diner meets Modern Web Design
- **关键词**: 霓虹发光、铬合金光泽、乙烯基纹理、弹跳动画、温馨氛围

### Color Palette
```css
--primary: #DC143C;      /* Cherry Red - 主色调 */
--secondary: #008080;    /* Teal - 次要色 */
--accent: #FFD700;      /* Chrome Gold - 强调色 */
--background: #FFFDD0;   /* Cream - 背景色 */
--text: #1A1A1A;         /* Black - 文字色 */
--chrome: #C0C0C0;       /* Chrome - 铬合金 */
--beige: #F5F5DC;        /* Beige - 米色辅助 */
--dark-slate: #2F4F4F;   /* Dark Slate - 深色辅助 */
--coral: #FF6B6B;        /* Coral - 珊瑚色 */
```

### Typography
- **Display Font**: Pacifico (复古手写风格) - 用于标题和霓虹文字
- **Body Font**: Josefin Sans (现代无衬线) - 用于正文和UI元素
- **Accent Font**: Quicksand (柔和圆润) - 用于按钮和辅助文字

### Spatial System
- **Base Unit**: 8px
- **Border Radius**: 12px (卡片), 8px (按钮), 50% (圆形元素)
- **Shadow**: 多层阴影模拟霓虹发光效果
- **Grid**: CSS Grid + Flexbox 混用

### Motion Philosophy
- **入场动画**: 弹跳效果 (bounce), 300-500ms
- **霓虹闪烁**: CSS animation + box-shadow glow, 1.5s infinite
- **悬停效果**: scale(1.02) + glow intensify, 200ms ease
- **状态转换**: 淡入淡出 250ms ease-in-out
- **按钮按压**: scale(0.95) + 颜色加深

### Visual Assets
- **Icons**: Lucide Icons (线条风格)
- **Decorative**: CSS伪元素创建霓虹管效果、乙烯基纹理
- **Textures**: CSS渐变模拟金属光泽

## 3. Layout & Structure

### Page Structure
```
┌─────────────────────────────────────────────────────────┐
│  HEADER (Neon Sign Title + Subtitle)                     │
├─────────┬───────────────────────────────────────────────┤
│         │  MAIN CONTENT AREA                            │
│  SIDE   │  ┌─────────────────────────────────────────┐  │
│  NAV    │  │  Chat Interface (DINER BOOTH)           │  │
│         │  │  - Messages (Order Tickets)              │  │
│ Counter │  │  - Input (Order Counter)                 │  │
│ Grill   │  └─────────────────────────────────────────┘  │
│ Menu    │  ┌─────────────────────────────────────────┐  │
│ Booth   │  │  Agent Status Panel (SHORT ORDER COOKS) │  │
│ Jukebox │  │  - Grid of agent cards with status      │  │
│         │  └─────────────────────────────────────────┘  │
│         │  ┌─────────────────────────────────────────┐  │
│         │  │  Token Stats (PLATE PROGRESS)           │  │
│         │  │  - Progress bar styled as plate         │  │
│         │  └─────────────────────────────────────────┘  │
└─────────┴───────────────────────────────────────────────┘
```

### Responsive Strategy
- **Desktop**: 侧边栏固定 (240px) + 主内容区 fluid
- **Tablet**: 侧边栏可折叠 (icons only)
- **Mobile**: 底部导航 + 全屏内容区

## 4. Features & Interactions

### Chat Interface (DINER BOOTH)
- **消息显示**: 模拟点餐小票样式，左侧AI消息，右侧用户消息
- **输入框**: 模拟点餐台，带霓虹边框聚焦效果
- **发送按钮**: "ORDER" 按钮，按压时有弹跳反馈
- **状态文案**:
  - Loading: "Firing up the grill..."
  - Processing: "Cooking up something good..."
  - Success: "Order up!"
  - Error: "Kitchen fire!"

### Agent Status Panel (SHORT ORDER COOKS)
- **Agent卡片**: 显示名字、状态、当前任务
- **状态类型**:
  - Grilling (处理中) - 红色 + 火焰动画
  - Serving (就绪) - 绿色 + 打钩
  - Closed (空闲) - 灰色 + 横线
  - Waiting (等待) - 黄色 + 旋转
- **交互**: 悬停显示详情弹窗

### Token Usage (PLATE PROGRESS)
- **进度条**: 模拟盘子上菜进度
- **显示**: 已用/总量 + 百分比
- **动画**: 填充时带有光泽扫过效果

### Sidebar Navigation (Counter)
- **导航项**: Counter, Grill, Menu, Booth, Jukebox
- **图标**: 餐馆相关图标
- **当前状态**: 霓虹高亮效果
- **悬停**: 发光增强 + 轻微位移

### Action Buttons
| 原始 | 餐厅版本 |
|------|----------|
| Submit | ORDER |
| Deploy | GRILL |
| Terminate | CLOSE |
| Cancel | BURN |
| Retry | REORDER |
| Save | TOGO |

## 5. Component Inventory

### Neon Sign Component
- **Default**: 发光文字，带外发光
- **Hover**: 闪烁效果
- **Animation**: 持续柔和的脉动

### Order Ticket (Chat Message)
- **AI Message**: 左侧对齐，米色背景，铬合金边框
- **User Message**: 右侧对齐，珊瑚色背景，金色边框
- **Timestamp**: 小字号，底部

### Diner Button
- **Default**: 霓虹边框，透明背景
- **Hover**: 背景填充，发光增强
- **Active**: 按压缩小，颜色加深
- **Disabled**: 灰色，无动画

### Agent Card
- **Grilling**: 红色边框 + 火焰图标 + 脉动
- **Serving**: 绿色边框 + 勾选图标 + 稳定
- **Closed**: 灰色边框 + 横线图标 + 静止
- **Waiting**: 黄色边框 + 旋转图标 + 等待动画

### Plate Progress Bar
- **Container**: 盘子形状 (圆形边缘)
- **Fill**: 从左到右填充，带光泽效果
- **Label**: 顶部显示 "Your order is X% ready!"

## 6. Technical Approach

### Stack
- **单文件HTML**: HTML + CSS + Vanilla JavaScript
- **无外部依赖**: 纯原生实现，最大兼容性
- **Google Fonts**: Pacifico, Josefin Sans, Quicksand

### Architecture
- **CSS Variables**: 统一管理颜色和间距
- **CSS Animations**: @keyframes 定义所有动画
- **Event Delegation**: JavaScript事件委托优化
- **Responsive**: CSS Grid + Media Queries

### Key Implementation
- 霓虹效果: text-shadow + box-shadow 多层叠加
- 铬合金光泽: linear-gradient + pseudo-elements
- 乙烯基纹理: repeating-linear-gradient 模拟
- 弹跳动画: cubic-bezier(0.68, -0.55, 0.265, 1.55)
