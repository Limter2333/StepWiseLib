# STYLE_016: Bauhaus Digital — AI Multi-Agent System UI

## Concept & Vision

A 1920s Bauhaus workshop reimagined as a command center for autonomous AI agents. The interface channels the revolutionary spirit of the Bauhaus school — geometric precision, primary color drama, and the radical belief that form serves function — into a digital workspace where multiple AI agents coordinate, communicate, and execute tasks. Every element is stripped to its essential geometric core: no decoration for its own sake, only shapes that communicate state, hierarchy, and action.

The tone is **confident, architectural, and slightly avant-garde** — like a de Stijl painting came alive as a control panel. Users should feel like conductors of an orchestrated machine.

---

## Design Language

### Aesthetic Direction

**Reference**: 1920s Bauhaus workshop posters + Paul Klee's grid paintings + Wim Crouwel's typographic systems, translated into a modern dashboard.

Bold geometry dominates. The primary color triad (red, yellow, blue) creates visual zones and state indicators against a stark black-and-white structural framework. Grid lines are visible as a design element, not hidden — echoing architectural blueprints.

### Color Palette

| Role | Color | Hex |
|------|-------|-----|
| Primary Red | Vermilion | `#E63946` |
| Primary Yellow | Chrome Yellow | `#FFBE0B` |
| Primary Blue | Ultramarine | `#3A86FF` |
| Black | Rich Black | `#0D0D0D` |
| White | Paper White | `#F8F9FA` |
| Neutral Dark | Charcoal | `#212529` |
| Neutral Mid | Concrete | `#6C757D` |
| Active Glow | Cyan (digital accent) | `#00F5D4` |

CSS Variables:
```css
:root {
  --bauhaus-red: #E63946;
  --bauhaus-yellow: #FFBE0B;
  --bauhaus-blue: #3A86FF;
  --bauhaus-black: #0D0D0D;
  --bauhaus-white: #F8F9FA;
  --bauhaus-charcoal: #212529;
  --bauhaus-concrete: #6C757D;
  --bauhaus-cyan: #00F5D4;
  
  --grid-line: rgba(0, 0, 0, 0.08);
  --grid-line-strong: rgba(0, 0, 0, 0.15);
}
```

### Typography

**Display / Headers**: `Bebas Neue` — all caps, condensed, monumental. Bauhaus letterforms meet industrial signage.
**Body / UI**: `Space Grotesk` — geometric but humanized, excellent for data-dense interfaces.
**Monospace / Code**: `JetBrains Mono` — for agent logs, IDs, technical readouts.

```css
/* Typography Scale */
--font-display: 'Bebas Neue', 'Arial Black', sans-serif;
--font-body: 'Space Grotesk', 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Consolas', monospace;

--text-xs: 0.75rem;    /* 12px - labels */
--text-sm: 0.875rem;   /* 14px - secondary */
--text-base: 1rem;      /* 16px - body */
--text-lg: 1.25rem;    /* 20px - subheads */
--text-xl: 1.5rem;     /* 24px - section titles */
--text-2xl: 2rem;       /* 32px - page titles */
--text-hero: 4rem;      /* 64px - hero statement */
```

### Spatial System

**Base unit**: 8px
**Grid**: 12-column with visible grid lines
**Gutters**: 16px (2 units)
**Margins**: 24px outer margins, 48px section spacing
**Border radius**: 0px (Bauhaus embraces sharp geometry) OR fully circular (50%) for emphasis elements

```css
--space-1: 8px;
--space-2: 16px;
--space-3: 24px;
--space-4: 32px;
--space-6: 48px;
--space-8: 64px;
```

### Motion Philosophy

Bauhaus is **geometric and decisive** — animations should feel precise, not bouncy. Think: mechanical linkages, clean reveals, direct paths.

- **Transitions**: `cubic-bezier(0.4, 0, 0.2, 1)` — smooth deceleration, no overshoot
- **Duration**: 200ms for micro-interactions, 400ms for state changes, 600ms for page elements
- **Entrance animations**: Elements slide in from grid intersections, staggered 50ms
- **Agent status pulses**: Slow, rhythmic glow (2s cycle) on active agents — like a heartbeat
- **Hover states**: Sharp geometric transforms — scale 1.02 on cards, color block shifts

```css
--ease-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--duration-fast: 200ms;
--duration-medium: 400ms;
--duration-slow: 600ms;
```

### Visual Assets

- **Geometric shapes as UI components**: Circles = agent avatars/indicators; Squares = task cards; Triangles = action triggers/direction
- **Grid overlay**: Visible 1px lines forming the underlying 12-column structure
- **Diagonal lines**: 45-degree separators between sections (Bauhaus diagonal composition)
- **Constructivist sunburst**: Radial lines emanating from key focal points
- **No rounded corners on primary containers** — sharp 90-degree edges enforce the geometric aesthetic

---

## Layout Architecture

### Overall Grid System

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER BAR (Black) - Logo, Nav, Status Summary              │
│  Height: 64px | Bebas Neue logo | Primary color accents    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │              │  │                                    │  │
│  │  AGENT       │  │  MAIN CANVAS                       │  │
│  │  ROSTER      │  │  (Task Flow / Agent Visualization)  │  │
│  │              │  │                                    │  │
│  │  240px fixed │  │  Flexible, fills remaining space   │  │
│  │              │  │                                    │  │
│  │  Each agent  │  │  Grid-based workspace with         │  │
│  │  = circle    │  │  geometric task nodes               │  │
│  │  indicator   │  │                                    │  │
│  │              │  │                                    │  │
│  └──────────────┘  └────────────────────────────────────┘  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  ACTION BAR (Bottom) - Quick actions, Agent spawn, Filters  │
│  Height: 72px | Yellow background | Triangle button shapes │
└─────────────────────────────────────────────────────────────┘
```

### Section Breakdown

**1. Header Bar (64px)**
- Black background (`#0D0D0D`)
- Left: Logo mark — a red circle with Bauhaus "B" lettermark in white
- Center: Navigation dots (geometric circles) for main sections
- Right: System status — a horizontal row of 5 small squares showing agent count (filled = active)
- Typography: Bebas Neue, white, tracking wide

**2. Agent Roster Panel (240px fixed width, left)**
- White background with visible grid lines
- Each agent represented as a circle (48px diameter)
  - Idle: White fill, black 2px border
  - Active: Blue fill, pulsing glow animation
  - Error: Red fill
  - Completed: Yellow fill
- Agent name in Space Grotesk below circle
- Role label in small caps, concrete color
- Vertical stack, 16px gap between agents

**3. Main Canvas (Flexible)**
- Subtle grid background (1px lines, 40px intervals)
- Task nodes as squares (120x120px):
  - Header strip in primary color (top 20px)
  - White body with task name
  - Status indicator triangle in corner
- Connection lines between tasks:
  - Straight lines with 45-degree elbow joints (constructivist style)
  - Line weight varies: 2px for sequential, 1px for parallel
- Agent position markers: circles that move along task paths

**4. Action Bar (72px, bottom)**
- Yellow background (`#FFBE0B`)
- Primary action buttons as triangles pointing right (play/continue)
- Secondary buttons as squares (pause, stop)
- Filter toggles as small circles
- Typography: Bebas Neue for labels, uppercase

### Responsive Strategy

- **Desktop (1200px+)**: Full layout as described
- **Tablet (768-1199px)**: Agent roster collapses to horizontal strip at top, canvas below
- **Mobile (< 768px)**: Tab-based navigation — Agents tab, Canvas tab, Actions tab

---

## Component Inventory

### 1. Agent Circle Indicator

**Purpose**: Represents individual AI agent status in roster and canvas

**Visual Spec**:
- Size: 48px diameter
- Border: 2px solid (color varies by state)
- States:
  - `idle`: Fill white, stroke black, no animation
  - `active`: Fill var(--bauhaus-blue), stroke var(--bauhaus-blue), box-shadow pulse (0 0 0 0 rgba(58, 134, 255, 0.4))
  - `error`: Fill var(--bauhaus-red), stroke var(--bauhaus-red)
  - `completed`: Fill var(--bauhaus-yellow), stroke var(--bauhaus-yellow)
  - `disabled`: Fill var(--bauhaus-concrete), stroke var(--bauhaus-concrete), opacity 0.5

**Hover**: Scale 1.1, cursor pointer
**Active/Selected**: White inner circle (20px) appears

**CSS Implementation**:
```css
.agent-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--bauhaus-black);
  background: var(--bauhaus-white);
  transition: all var(--duration-fast) var(--ease-out);
  position: relative;
}

.agent-circle:hover {
  transform: scale(1.1);
}

.agent-circle.active {
  background: var(--bauhaus-blue);
  border-color: var(--bauhaus-blue);
  animation: agentPulse 2s ease-in-out infinite;
}

@keyframes agentPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(58, 134, 255, 0.4); }
  50% { box-shadow: 0 0 0 12px rgba(58, 134, 255, 0); }
}

.agent-circle.selected::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--bauhaus-white);
}
```

### 2. Task Card (Square)

**Purpose**: Represents a task unit in the canvas workflow

**Visual Spec**:
- Size: 120px x 120px
- No border-radius (sharp corners)
- Top strip (20px): Primary color header (blue, yellow, or red based on priority)
- Body: White background, 12px padding
- Corner triangle: 16px right-pointing triangle in bottom-right, showing direction flow
- States:
  - `pending`: White body, black top strip
  - `in-progress`: Blue top strip, subtle blue tint on body
  - `completed`: Yellow top strip, checkmark in corner triangle
  - `failed`: Red top strip, X in corner triangle

**Hover**: Lift effect — translate Y -4px, box-shadow increases
**Active**: Blue 3px left border (accent bar)

**CSS Implementation**:
```css
.task-card {
  width: 120px;
  height: 120px;
  background: var(--bauhaus-white);
  border: 1px solid var(--bauhaus-black);
  position: relative;
  transition: all var(--duration-fast) var(--ease-out);
}

.task-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 20px;
  background: var(--bauhaus-charcoal);
}

.task-card.in-progress::before {
  background: var(--bauhaus-blue);
}

.task-card.completed::before {
  background: var(--bauhaus-yellow);
}

.task-card.failed::before {
  background: var(--bauhaus-red);
}

.task-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 0 0 16px 16px;
  border-color: transparent transparent var(--bauhaus-black) transparent;
}

.task-card:hover {
  transform: translateY(-4px);
  box-shadow: 4px 4px 0 var(--bauhaus-black);
}
```

### 3. Connection Line

**Purpose**: Shows task dependencies and agent flow paths

**Visual Spec**:
- Straight lines with 45-degree elbow turns (constructivist style)
- Stroke: 2px black
- Arrow heads: Small filled triangles at endpoints
- Color variants:
  - Sequential flow: Black
  - Parallel flow: Dashed (4px dash, 4px gap)
  - Active flow: Blue with animated dash pattern moving toward direction

**CSS Implementation**:
```css
.connection-line {
  stroke: var(--bauhaus-black);
  stroke-width: 2;
  fill: none;
}

.connection-line.parallel {
  stroke-dasharray: 4 4;
}

.connection-line.active {
  stroke: var(--bauhaus-blue);
  animation: flowDash 1s linear infinite;
}

@keyframes flowDash {
  to { stroke-dashoffset: -8; }
}
```

### 4. Primary Action Button (Triangle)

**Purpose**: Main CTA buttons (Start, Continue, Deploy)

**Visual Spec**:
- Shape: Right-pointing triangle
- Size: 48px base, 48px height
- Background: var(--bauhaus-red) (default), var(--bauhaus-blue) (hover)
- White symbol inside (play icon / arrow)
- No border-radius

**Hover**: Scale 1.05, background shifts to blue
**Active**: Scale 0.95 (pressed effect)
**Disabled**: Gray fill, opacity 0.5

**CSS Implementation**:
```css
.btn-triangle {
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 24px 0 24px 42px;
  border-color: transparent transparent transparent var(--bauhaus-red);
  background: transparent;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.btn-triangle:hover {
  border-left-color: var(--bauhaus-blue);
  transform: scale(1.05);
}

.btn-triangle:active {
  transform: scale(0.95);
}

.btn-triangle:disabled {
  border-left-color: var(--bauhaus-concrete);
  opacity: 0.5;
  cursor: not-allowed;
}
```

### 5. Secondary Action Button (Square)

**Purpose**: Secondary actions (Pause, Stop, Settings)

**Visual Spec**:
- Shape: Square
- Size: 40px x 40px
- Border: 2px solid var(--bauhaus-black)
- Background: white (default), var(--bauhaus-yellow) (hover)
- Symbol centered (pause bars, X, gear)
- No border-radius

**CSS Implementation**:
```css
.btn-square {
  width: 40px;
  height: 40px;
  background: var(--bauhaus-white);
  border: 2px solid var(--bauhaus-black);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-square:hover {
  background: var(--bauhaus-yellow);
}
```

### 6. Filter Toggle (Circle)

**Purpose**: Binary filter toggles (Show/Hide, On/Off)

**Visual Spec**:
- Size: 24px diameter
- Border: 2px solid var(--bauhaus-black)
- States:
  - Off: White fill
  - On: Filled with current accent color

**CSS Implementation**:
```css
.filter-toggle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid var(--bauhaus-black);
  background: var(--bauhaus-white);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.filter-toggle.active {
  background: var(--bauhaus-cyan);
}
```

### 7. Section Header

**Purpose**: Labels for major UI sections

**Visual Spec**:
- Typography: Bebas Neue, 24px, uppercase, letter-spacing 4px
- Left-aligned
- Thin horizontal line (1px, var(--bauhaus-black)) extending from text end to edge
- Color: var(--bauhaus-black)

**CSS Implementation**:
```css
.section-header {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  text-transform: uppercase;
  letter-spacing: 4px;
  color: var(--bauhaus-black);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.section-header::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--bauhaus-black);
}
```

### 8. Status Indicator Row

**Purpose**: Aggregate system status in header

**Visual Spec**:
- Row of 5 small squares (12px each)
- Filled squares = active count (blue)
- Empty squares = remaining (outline only)
- Compact horizontal arrangement

**CSS Implementation**:
```css
.status-indicators {
  display: flex;
  gap: 6px;
}

.status-square {
  width: 12px;
  height: 12px;
  border: 1px solid var(--bauhaus-white);
}

.status-square.filled {
  background: var(--bauhaus-blue);
}
```

### 9. Navigation Dot

**Purpose**: Section navigation in header

**Visual Spec**:
- Size: 12px diameter circles
- Active: Filled with white
- Inactive: White outline only
- Horizontal row with 24px spacing

**CSS Implementation**:
```css
.nav-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--bauhaus-white);
  background: transparent;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.nav-dot.active {
  background: var(--bauhaus-white);
}
```

### 10. Grid Background

**Purpose**: Visible underlying grid structure for Bauhaus authenticity

**Visual Spec**:
- 40px grid intervals
- 1px lines in var(--grid-line) (subtle)
- Intersections marked with small dots at crossings (optional accent)

**CSS Implementation**:
```css
.grid-background {
  background-image:
    linear-gradient(to right, var(--grid-line) 1px, transparent 1px),
    linear-gradient(to bottom, var(--grid-line) 1px, transparent 1px);
  background-size: 40px 40px;
}
```

---

## Interaction Patterns

### Agent Selection Flow
1. User clicks agent circle in roster
2. Circle scales to 1.1, selected state shows white inner circle
3. Main canvas highlights all tasks assigned to that agent with blue border
4. Agent details panel slides in from right (320px width)

### Task Drag-and-Drop
1. User hovers task card → card lifts (translate Y -4px, shadow increases)
2. User clicks and drags → card follows cursor with slight rotation (2deg)
3. Drop zones highlight as grid cells with blue fill (0.2 opacity)
4. On drop → card snaps to grid position with 200ms ease-out
5. Connection lines redraw automatically

### Flow Visualization
1. Active task flows show animated dashed lines moving toward next task
2. Animation speed: 1s for full dash cycle
3. When task completes → flow line turns yellow, animation stops
4. New flow originates from completed task's right edge triangle

### Multi-Agent Coordination View
1. When 2+ agents work on parallel tasks, their paths shown as parallel dashed lines
2. Convergence point (where agents meet) marked with a large circle node
3. Conflict indicators: Red pulsing triangle at intersection if agents would collide

### Error State Interaction
1. Failed task card's top strip turns red
2. X symbol appears in corner triangle
3. Card pulses once (scale 1.02 → 1.0)
4. Click card → error details panel opens below with red left border

### Spawn New Agent
1. User clicks triangle button in Action Bar
2. Modal appears with agent type selection (grid of 3 square options)
3. Each option: large square with geometric symbol (circle, square, triangle)
4. Select type → new agent circle animates into roster (fade in + scale from 0.5)

### Quick Filter
1. Filter toggles in Action Bar show active filters as filled cyan circles
2. Toggle click → instant filter application
3. Canvas filters tasks with 200ms fade transition for hidden items

---

## Layout Variations

### Dense Mode (Default)
- All panels visible
- Compact 120px task cards
- 40px grid background visible

### Focus Mode
- Agent roster hidden
- Main canvas expands to full width
- Task cards scale up to 160px
- Focus line: red 1px left border on container

### Comparison Mode
- Side-by-side canvas views (50/50 split)
- Each with its own agent highlighting
- Shared action bar at bottom
- Diagonal yellow divider line (45deg, 4px)

---

## Accessibility Considerations

- All interactive elements have visible focus states (2px var(--bauhaus-cyan) outline)
- Color is never the sole indicator — shapes and labels provide redundancy
- Agent circles include aria-label with agent name and status
- Task cards have aria-live regions for status updates
- Keyboard navigation: Tab through roster, Enter to select, Arrow keys to navigate canvas
- High contrast mode: Increase border weights to 3px, use pure black/white

---

## Key Design Principles Summary

| Bauhaus Principle | Digital Application |
|-------------------|---------------------|
| Primary colors only | Status = Red/Yellow/Blue + Black/White |
| Geometric forms | Circles=agents, Squares=tasks, Triangles=actions |
| Grid composition | 12-col visible grid, 40px intervals |
| Form follows function | Every shape has a purpose; no decorative elements |
| Asymmetric balance | Offset panels, diagonal flow lines, deliberate tension |
| Typography as graphic element | Bebas Neue monumental headers, generous tracking |

---

## Implementation Notes

- Use CSS Grid for main layout (header, roster, canvas, action bar)
- SVG for connection lines and geometric decorations
- CSS custom properties for theming and state changes
- No border-radius on containers — Bauhaus embraces sharp edges
- Limit shadows to hard-edged (no blur) for that constructivist depth
- Animations should feel mechanical, not organic — precise easing curves only
