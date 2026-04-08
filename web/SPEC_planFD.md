# SPEC: Swiss Brutalist AI Multi-Agent System

## 1. Concept & Vision

**GRID. MODULE. SYSTEM.** — Where Swiss precision meets brutalist force. Every pixel has its place and purpose. This is not a dashboard; it is a command grid. The interface channels the mathematical rigor of the International Typographic Style with the raw, unapologetic power of brutalist architecture. Think Zurich train station signage system, but for AI agents.

## 2. Design Language

### Aesthetic Direction
Swiss International Style + Brutalist concrete texture. Sharp geometric forms. Exposed grid structure. Bold red accent lines that slice through the composition like architectural markings on blueprints.

### Color Palette
```
--primary:     #808080 (Concrete Gray)
--secondary:   #E00041 (Swiss Red)
--accent:      #000000 (Black)
--background:  #FFFFFF (White)
--text:        #000000 (Black)
--silver:      #C0C0C0 (Silver)
--bright-red:  #FF1744 (Bright Red)
--dark-gray:   #333333 (Dark Gray)
--light-gray:  #F0F0F0 (Light Gray)
```

### Typography
- **Display**: Helvetica Neue Bold — classic Swiss precision
- **Body**: Inter — modern clarity
- **Accent**: SF Mono — technical monospace for data/stats

### Spatial System
- 8px base grid
- 24px module spacing
- 48px section gaps
- Heavy 4px borders on interactive elements
- Red accent lines: 2px solid

### Motion Philosophy
- Precise 200ms ease-out transitions
- Grid alignment animations on state changes
- Red underline sweep on hover (left-to-right, 150ms)
- Status changes with 300ms scale pulse
- No bounce, no overshoot — brutalist restraint

### Visual Assets
- Grid overlay pattern (subtle, 1px lines at 24px intervals)
- "GRID SYSTEM" watermark in background
- Red corner markers at grid intersections
- Module status indicators as geometric shapes

## 3. Layout & Structure

### Page Structure
```
┌─────────────────────────────────────────────────────────┐
│ GRID. MODULE. SYSTEM.                    [GRID SYSTEM] │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌────────────────────────────────────────┐ │
│ │          │ │                                        │ │
│ │  NAV     │ │           MAIN CONTENT                 │ │
│ │  GRID    │ │                                        │ │
│ │  MODULE  │ │  - Chat Interface                      │ │
│ │  SYSTEM  │ │  - Agent Status Grid                   │ │
│ │  DATA    │ │  - Token Usage Stats                   │ │
│ │  CONFIG  │ │                                        │ │
│ │          │ │                                        │ │
│ └──────────┘ └────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ STATUS: MODULE COMPLETE.    │    TOKENS: 12,847 / 50K  │
└─────────────────────────────────────────────────────────┘
```

### Grid System
- Strict 12-column grid with visible guidelines
- Sidebar: fixed 240px width
- Main area: fluid with 24px padding
- Red 2px vertical divider between sections

### Responsive Strategy
- Desktop-first (1200px+)
- Tablet: collapse sidebar to icons
- Mobile: stack layout, maintain grid aesthetics

## 4. Features & Interactions

### Chat Interface
- User input: large textarea with monospace font
- AI responses: card-based with timestamp and module attribution
- Typing indicator: pulsing red square
- States: Empty ("No data."), Loading ("Initializing module..."), Processing ("Processing data..."), Success ("Module complete."), Error ("System failure.")

### Agent Status Display
- Grid of module cards (3 columns)
- Status indicators: ONLINE (green dot), PROCESSING (red pulse), OFFLINE (gray)
- Hover: red border sweep, scale 1.02

### Token Usage Statistics
- Progress bar with percentage
- Exact numbers: "12,847 / 50,000"
- Color shifts: gray → red as usage increases

### Sidebar Navigation
- Vertical list with red active indicator
- Hover: red underline sweep
- Icons + labels

### Action Buttons
- BUILD, COMPILE, TERMINATE, ABORT, REBUILD, SAVE
- Brutalist: heavy borders, no border-radius
- Hover: red background with white text
- Active: scale 0.98

## 5. Component Inventory

### ChatMessage
- Default: white card, black text, timestamp in silver
- AI Response: left red border (4px)
- User Message: right-aligned, gray background

### AgentCard
- Default: white with 2px black border
- Hover: 2px red border, subtle shadow
- Active/Processing: red top border (4px)
- Offline: opacity 0.6

### TokenMeter
- Container: black border, gray background
- Fill: red gradient
- Text: monospace, exact values

### NavItem
- Default: black text
- Hover: red underline (2px, animated)
- Active: red left border + bold text

### ActionButton
- Default: black border, white background, black text
- Hover: red background, white text
- Disabled: gray border, gray text
- Active: scale 0.98

### StatusIndicator
- Online: #00C853 (green)
- Processing: #E00041 (red, pulsing)
- Offline: #808080 (gray)

## 6. Technical Approach

### Stack
- Single HTML file with embedded CSS and JavaScript
- No external dependencies except Google Fonts
- Vanilla JS for interactions

### Architecture
- CSS Grid for main layout
- CSS Custom Properties for theming
- Event delegation for button handlers
- Mock data for chat and agent status

### Key Implementation Details
- Grid overlay via CSS background pattern
- Red underline animation via pseudo-elements and clip-path
- Status pulse via CSS keyframes
- Swiss typography via Helvetica Neue + proper leading
