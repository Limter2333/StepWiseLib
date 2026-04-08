# Memphis Design Chat UI - SPEC

## Concept & Vision

A vibrant, chaotic, delightfully 80s chat interface that channels the Memphis Design movement - Italian furniture vibes, geometric mayhem, and bold colors. The UI should feel like stepping into a Milano design studio in 1985, where every element bounces, wiggles, and demands attention. This isn't just a chat interface - it's a time machine wrapped in confetti.

## Design Language

### Aesthetic Direction
**Reference**: Ettore Sottsass + Memphis Group (1981-1987). Radical geometric shapes, bold color blocking, playful squiggles, terrazzo patterns, and unapologetic maximalism.

### Color Palette
```
--primary: #FFDE00      /* Bright Yellow - main accent */
--secondary: #FF6B9D    /* Hot Pink - energy */
--accent: #00BFFF       /* Electric Blue - contrast */
--background: #FFFFFF   /* White - canvas */
--text: #000000         /* Black - grounding */
--coral: #FF6B6B        /* Coral - warmth */
--teal: #00CED1         /* Dark Turquoise - variety */
--purple: #9B59B6       /* Purple - Memphis staple */
```

### Typography
- **Display**: "Helvetica Neue", Helvetica, Arial Black - bold, geometric, unapologetic
- **Body**: "Futura", "Trebuchet MS", sans-serif - geometric, readable
- **Accent**: System italic for decorative labels

### Spatial System
- Base unit: 8px
- Generous padding (24-48px)
- Overlapping elements for depth
- Asymmetric layouts breaking the grid

### Motion Philosophy
- **Bounce**: All interactive elements have elastic spring animations
- **Wiggle**: Squiggles animate continuously like living patterns
- **Pop**: Elements scale up突然 on appearance
- **Timing**: 300-500ms with ease-out or custom spring curves

### Visual Assets
- Custom SVG squiggles, zigzags, circles
- Dot patterns and grid backgrounds
- Confetti shapes (triangles, semicircles, plus signs)
- Wavy borders using CSS

## Layout & Structure

### Page Structure
```
┌─────────────────────────────────────────────────────────┐
│  ░░░ PATTERN HEADER ░░░  (squiggle + bouncing title)    │
├─────────┬───────────────────────────────────────────────┤
│         │                                               │
│  SIDE   │           CHAT AREA                          │
│  NAV    │    (messages with confetti decorations)      │
│         │                                               │
│ Squigle │                                               │
│ Confetti│                                               │
│ Pattern │                                               │
│ Terry   │                                               │
│         │                                               │
├─────────┼───────────────────────────────────────────────┤
│ TOKEN   │         INPUT AREA + BOUNCE BUTTON           │
│ STATS   │                                               │
└─────────┴───────────────────────────────────────────────┘
```

### Visual Pacing
- Header: Maximum chaos with animated squiggles
- Sidebar: Organized chaos with nav items as geometric shapes
- Chat: Clean messaging with decorative accents
- Input: Focused with bold CTA button

## Features & Interactions

### Core Features
1. **Chat Interface**: User input + AI responses with typing indicators
2. **Agent Status**: Animated squiggle patterns showing AI state
3. **Token Stats**: Visual bar chart with Memphis colors
4. **Sidebar Navigation**: Four sections as Memphis-style nav items

### Interaction Details

#### Send Button (BOUNCE)
- Default: Yellow background, black text, slight rotation
- Hover: Scale 1.1, rotate 5deg, shadow grows
- Active: Scale 0.95, bounce back
- Loading: Pulsing animation

#### Sidebar Nav Items
- Each item is a different geometric shape
- Hover: Wiggle animation + color shift
- Active: Bounce + scale

#### Chat Messages
- User: Right-aligned, pink bubble with confetti
- AI: Left-aligned, yellow bubble with squiggles
- Entrance: Pop + fade animation

### Status States
- Loading: "Loading patterns..." + bouncing dots
- Processing: "Adding squiggles..." + rotating squiggle
- Success: "Perfectly pattern!" + confetti burst
- Error: "Pattern failed. Retry." + shake animation
- Empty: "Pattern awaits..." + idle squiggle

## Component Inventory

### Header Component
- Animated squiggle SVG background
- "SQUIGLE. CONFETTI. PATTERN." title with bounce-in
- Subtitle with typewriter or fade effect

### Sidebar Navigation
- 4 nav items: Squigle (circle), Confetti (triangle), Pattern (square), Terry (squiggle text)
- Each with unique shape + color
- States: default, hover (wiggle), active (bounce)

### Chat Message Bubbles
- User bubble: #FF6B9D with white confetti dots
- AI bubble: #FFDE00 with black squiggles
- Rounded corners with hard geometric edges

### Input Area
- Large text input with thick black border
- Placeholder: "Type your message..."
- BOUNCE submit button

### Token Stats Panel
- Horizontal bar chart
- Each bar a different Memphis color
- Labels: Input Tokens, Output Tokens, Total

### Agent Status Indicator
- Animated squiggle/curve
- Color indicates state (yellow=idle, pink=thinking, blue=responding)
- Text label below

## Technical Approach

- **Stack**: Vanilla HTML/CSS/JS (single file)
- **Animations**: CSS keyframes + transitions, requestAnimationFrame for complex
- **Layout**: CSS Grid + Flexbox
- **No dependencies**: Pure implementation
