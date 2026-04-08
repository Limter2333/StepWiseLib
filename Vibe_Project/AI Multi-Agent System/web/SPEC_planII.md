# SPEC.md — Retro Terminal UI (Plan II)

## 1. Concept & Vision

**BOOT.EXECUTE.TERMINAL.** — A nostalgic journey to the golden age of computing where CRT monitors glowed with phosphor green text and every keystroke felt powerful. This interface channels the mystique of 1980s mainframe terminals: the hum of the cathode ray, the persistence of phosphor burn-in, and the raw command-line authority that made users feel like they were interfacing directly with machine intelligence.

The experience should feel like sitting in front of a well-worn IBM 3278 terminal in a dimly lit computer room — authentic, slightly mysterious, and undeniably cool.

## 2. Design Language

### Aesthetic Direction
**Reference**: IBM 3278 terminal meets WarGames (1983) — authentic CRT phosphor glow with subtle screen artifacts, scan lines, and that distinctive green-on-black that defined an era of computing.

### Color Palette
```css
--phosphor-green: #00FF00;      /* Primary - classic phosphor green */
--amber: #FFB000;               /* Secondary - amber terminal variant */
--bright-green: #33FF33;        /* Accent - highlight green */
--deep-green: #003300;          /* Auxiliary - darker green for depth */
--crt-black: #0D0D0D;           /* Background - CRT off-black */
--dim-amber: #CC9900;           /* Auxiliary amber for warnings */
--glow-green: rgba(0,255,0,0.15); /* Glow effects */
--scanline-dark: rgba(0,0,0,0.3); /* Scanline overlay */
```

### Typography
- **Display**: `VT323` (Google Fonts) — Authentic retro terminal font
- **Body**: `Fira Code` (Google Fonts) — Modern monospace with ligatures
- **Accent**: `IBM Plex Mono` (Google Fonts) — Classic IBM terminal feel
- **Fallback**: `monospace`

### Spatial System
- Base unit: 8px grid
- Terminal padding: 24px
- Component spacing: 16px
- Line height: 1.5 for readability
- Border radius: 0px (sharp corners authentic to era)

### Motion Philosophy
All animations evoke CRT behavior:
- **Screen flicker**: Subtle random opacity fluctuation (0.98-1.0) at irregular intervals
- **Scanline crawl**: Slow vertical movement of scanline overlay
- **Cursor blink**: Classic 530ms on/off cycle
- **Text glow pulse**: Subtle brightness oscillation on phosphor text
- **Screen shake**: Micro-shake on error events
- **Boot sequence**: Staggered line-by-line text reveal on load

### Visual Assets
- No external images — pure CSS effects
- Scanlines via repeating linear gradient
- CRT curvature via subtle border-radius and box-shadow
- Screen reflection via gradient overlay
- Vignette effect via radial gradient

## 3. Layout & Structure

### Page Architecture
```
┌─────────────────────────────────────────────────────────────┐
│  ░░░ CRT SCREEN CONTAINER (curved edges, vignette) ░░░     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ HEADER: BOOT.EXECUTE.TERMINAL. + System Time        │   │
│  ├──────────────┬──────────────────────────────────────┤   │
│  │ SIDEBAR      │  MAIN TERMINAL AREA                   │   │
│  │              │  ┌────────────────────────────────┐  │   │
│  │ > BOOT       │  │ Terminal Output (chat history) │  │   │
│  │ > EXECUTE    │  │                                │  │   │
│  │ > TERMINAL   │  │                                │  │   │
│  │ > BASH       │  ├────────────────────────────────┤  │   │
│  │              │  │ Status Bar: Agent | Tokens     │  │   │
│  │ ───────────  │  ├────────────────────────────────┤  │   │
│  │ AGENT STATUS │  │ > Command Input_               │  │   │
│  │ [●] Online   │  └────────────────────────────────┘  │   │
│  └──────────────┴──────────────────────────────────────┘   │
│  ░░░░░░░░░░░░░░░░ SCANLINES OVERLAY ░░░░░░░░░░░░░░░░░░░   │
└─────────────────────────────────────────────────────────────┘
```

### Responsive Strategy
- Desktop (>1024px): Full sidebar + terminal layout
- Tablet (768-1024px): Collapsible sidebar, condensed terminal
- Mobile (<768px): Bottom nav, full-width terminal, stacked status

## 4. Features & Interactions

### Core Features

**A. Command Input System**
- Prompt format: `C:\> ` prefix
- Input field with blinking cursor
- Submit on Enter key
- Commands: `help`, `clear`, `status`, `tokens`, `boot`, `exec`, `chat <message>`

**B. Chat Interface**
- Terminal-style message display
- User messages: bright green, right-aligned or indented
- Agent messages: standard green, left-aligned
- System messages: amber color
- Timestamps in military format (HH:MM:SS)

**C. Agent Status Display**
- States: Online (green pulse), Offline (dim), Processing (amber blink)
- Visual indicator: filled circle with glow
- Status text updates in real-time

**D. Token Usage Display**
- Format: `TOKEN-USAGE: XXX,XXX / 1,000,000`
- Animated counter on value change
- Warning state at 80% (amber), critical at 95% (red blink)

**E. Sidebar Navigation**
- Four nav items: BOOT, EXECUTE, TERMINAL, BASH
- Active state: bright green background glow
- Hover: amber highlight
- Each triggers different terminal context

### Interaction Details

| Action | Response |
|--------|----------|
| Page Load | Boot sequence animation: lines appear one by one |
| Type command | Characters appear with subtle keyclick sound (CSS only visual) |
| Submit | Screen flicker, processing indicator |
| Error | Brief screen shake, red flash |
| Hover nav item | Amber glow, slight scale |
| Click nav item | Active state, content switch with fade |
| Scroll terminal | Smooth scroll, scanline parallax |

### Edge Cases
- Empty input: subtle shake, amber "C:\> awaiting input"
- Unknown command: "C:\> error: command not recognized"
- Long message: word-wrap with indent continuation
- Network error: "C:\> CONNECTION LOST" with reconnect prompt

## 5. Component Inventory

### CRT Screen Container
- Outer bezel effect (dark gray gradient)
- Inner screen with slight curvature illusion
- Vignette overlay (darker corners)
- Scanline overlay (2px repeating lines)
- Subtle screen reflection (top gradient)
- States: Normal, Flicker (random), Shake (error)

### Terminal Output Area
- Scrollable message container
- Auto-scroll to bottom on new message
- Custom scrollbar (thin, green)
- Message types: user, agent, system, error
- States: Empty (show watermark), Scrolled (show scroll indicator)

### Command Input
- Full-width input field
- Green text on dark background
- Blinking block cursor (CSS animation)
- Prefix label "C:\>"
- States: Default, Focused (brighter glow), Disabled (during processing)

### Navigation Item
- Uppercase text
- Left border indicator on active
- Icon prefix (text-based: > or ▸)
- States: Default, Hover (amber), Active (green glow bg), Disabled (dim)

### Status Indicator
- Circular dot (8px)
- Color based on state
- Pulsing animation on processing
- Label text beside

### Token Counter
- Monospace digits
- Progress bar underneath
- Numeric display with comma formatting
- States: Normal (green), Warning (amber), Critical (red blink)

### Boot Sequence Lines
- Appear one at a time with delay
- Typing effect for each line
- Final line triggers main UI fade-in

## 6. Technical Approach

### Stack
- Single HTML file with embedded CSS and JavaScript
- No external dependencies except Google Fonts
- Pure CSS animations (no JS animation libraries)
- CSS custom properties for theming
- Vanilla JS for interactivity

### Architecture
```javascript
// State management
const state = {
  agentStatus: 'online' | 'offline' | 'processing',
  tokenUsage: { used: 0, total: 1000000 },
  messages: [],
  activeNav: 'terminal',
  isBooting: true
};

// Event handlers
- handleCommandSubmit()
- handleNavClick()
- handleScroll()
- simulateAgentResponse()
- updateTokenDisplay()
- triggerBootSequence()
```

### Key Implementation Details
- CSS `mix-blend-mode` for scanline overlay
- CSS `@keyframes` for all animations
- `requestAnimationFrame` for smooth token counter
- `IntersectionObserver` for scroll-triggered effects
- CSS `backdrop-filter` where supported
- `prefers-reduced-motion` media query respect

### Performance Considerations
- Hardware-accelerated transforms only
- Debounced scroll handlers
- CSS `will-change` hints for animated elements
- Lazy animation initialization after boot sequence
