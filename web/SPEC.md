# Retro Space Age AI Multi-Agent System - SPEC.md

## 1. Concept & Vision

**LAUNCH. MISSION. ORBIT.** — A mission control interface for AI agents reimagined through the lens of 1960s space race aesthetics. The interface evokes the tension of Apollo-era command modules: analog gauges, atomic orbital patterns, starburst decorations, and the heroic optimism of early space exploration. Every interaction feels like operating authentic space hardware — from the satisfying "TRANSMIT" button presses to the orbital animations that track agent status.

## 2. Design Language

### Aesthetic Direction
**Reference**: NASA Mission Control consoles + 1960s atomic age sci-fi (The Jetsons, Fallout vault aesthetics)
- Brass/aged metal textures with aged brown backgrounds
- Atomic orbital rings around key elements
- Starburst/放射状 decorations for emphasis
- Mission patch/badge motifs for status indicators
- CRT scan-line effects for retro-tech authenticity

### Color Palette
```
--primary: #FF6B35 (Atomic Orange - buttons, highlights)
--secondary: #008B8B (Teal - secondary actions, borders)
--accent: #FFFDD0 (Cream - text highlights, badges)
--background: #2F1F1F (Aged Brown - main background)
--text: #1A1A1A (Black - primary text)
--surface: #3D2A2A (Lighter brown - cards, panels)
--muted: #8B4513 (Brown - disabled states)
--peru: #CD853F (Peru - decorative accents)
--burlywood: #DEB887 (Burlywood - borders, lines)
--chocolate: #D2691E (Chocolate - hover states)
```

### Typography
- **Display**: "Orbitron" (Google Font) - headers, badges, mission titles
- **Body**: "Exo 2" (Google Font) - body text, inputs, labels
- **Accent**: "Share Tech Mono" (Google Font) - status readouts, technical data

### Spatial System
- 8px base unit
- Generous padding in mission panels (24-32px)
- Tight, precise spacing in status indicators
- Asymmetric layouts with overlapping elements

### Motion Philosophy
- **Orbital animations**: Continuous slow rotation of atomic rings (20-30s cycles)
- **Starburst pulse**: Gentle scale pulse on important elements
- **Gauge needles**: Smooth easing for status changes
- **Button feedback**: Press-down effect with slight glow
- **Page load**: Staggered fade-in from center outward

### Visual Assets
- Custom CSS atomic orbital rings (concentric circles with electrons)
- CSS starburst decorations (rotated squares, rays)
- SVG mission patches for agent status
- CSS gauge/fuel meter components
- Scan-line overlay effect

## 3. Layout & Structure

### Page Architecture
```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: Logo + Title "MISSION CONTROL" + Status Bar       │
├──────────┬──────────────────────────────────────────────────┤
│          │  MAIN CONTENT AREA                              │
│  SIDEBAR │  ┌──────────────────────────────────────────┐   │
│          │  │  Chat Interface (Primary)                │   │
│  Nav:    │  │  - Message history                         │   │
│  - MISSION│  │  - Input panel with TRANSMIT button      │   │
│  - LAUNCH │  └──────────────────────────────────────────┘   │
│  - ORBIT │  ┌──────────────────────────────────────────┐   │
│  - CAPSULE│  │  Agent Status Panel (Right/Bottom)      │   │
│  - HOUSTON│  │  - Astronaut badges                      │   │
│          │  │  - Orbital status indicators              │   │
│          │  └──────────────────────────────────────────┘   │
│          │  ┌──────────────────────────────────────────┐   │
│          │  │  Fuel Gauge (Token Usage)                 │   │
│          │  │  - Retro analog gauge aesthetic          │   │
│          │  └──────────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────────────┘
```

### Responsive Strategy
- Desktop: Full mission control layout with sidebar
- Tablet: Collapsible sidebar, stacked panels
- Mobile: Full-width panels, hamburger nav

## 4. Features & Interactions

### Chat Interface
- **Input**: Mission briefing text field with "Houston, standing by..." placeholder
- **Send button**: "TRANSMIT" with launch-glow effect on hover
- **Messages**: Styled as mission logs with timestamps
- **AI responses**: Displayed with "GROUND CONTROL" prefix and orbital decoration

### Agent Status Display
- **States**: Launching (pulsing orange), Orbiting (stable teal), Aborted (red), Splash (muted)
- **Badges**: Astronaut helmet icons with status colors
- **Progress rings**: Animated orbital paths showing agent activity

### Token Usage (Fuel Gauge)
- **Design**: 1960s analog fuel gauge with needle
- **Labels**: "FUEL RESERVES" with percentage
- **Animation**: Needle smoothly animates to new position
- **Warning**: Red zone at low fuel (<20%)

### Sidebar Navigation
- **Items**: Mission Control, Launch Bay, Orbit View, Capsule, Houston
- **Active state**: Glowing border + filled background
- **Hover**: Subtle lift effect with shadow
- **Icons**: Custom SVG space-themed icons

### Creative Copy Mapping
| Standard | Space Age |
|----------|-----------|
| Submit | TRANSMIT |
| Deploy | LAUNCH |
| Cancel | SPLASH |
| Error | ABORT |
| Retry | RETRY |
| Save | TRACK |
| Loading | "Countdown initiated..." |
| Processing | "Entering orbit..." |
| Success | "Mission accomplished." |
| Error | "Mission failed." |
| Empty | "No telemetry." |
| Waiting | "Awaiting launch window." |

## 5. Component Inventory

### Button (TRANSMIT/LAUNCH/ABORT)
- **Default**: Aged metal look with embossed text, subtle inner shadow
- **Hover**: Orange glow, slight scale up (1.02)
- **Active**: Pressed down effect, glow intensifies
- **Disabled**: Muted brown, no glow, "SCRUBBED" text

### Chat Message
- **User**: Right-aligned, orange accent border
- **AI**: Left-aligned, teal accent border, "GROUND CONTROL" prefix
- **Timestamp**: Monospace, muted color

### Status Badge
- **Design**: Circular badge with astronaut helmet icon
- **Colors**: Launching (#FF6B35), Orbiting (#008B8B), Aborted (#C73E3E), Splash (#888)
- **Animation**: Subtle pulse on Launch state

### Fuel Gauge
- **Design**: Semicircular gauge with tick marks
- **Needle**: Animated pointer with shadow
- **Zones**: Green (full), Yellow (mid), Red (low)
- **Digital readout**: Below gauge in monospace

### Navigation Item
- **Default**: Transparent with border
- **Hover**: Background fills, text brightens
- **Active**: Full background, glowing border, "ACTIVE" indicator

### Input Field
- **Design**: Inset shadow, monospace font
- **Placeholder**: "Houston, standing by..." in italic
- **Focus**: Orange glow border

## 6. Technical Approach

### Stack
- Single HTML file with embedded CSS and JavaScript
- No external dependencies except Google Fonts
- CSS custom properties for theming
- Vanilla JS for interactivity
- CSS animations (no libraries)

### Architecture
- Semantic HTML5 structure
- CSS Grid + Flexbox for layout
- CSS animations for all motion
- Event delegation for interactions
- LocalStorage for chat history persistence

### Key Implementation Details
- Atomic orbital rings via CSS border-radius + transforms
- Starburst via rotated pseudo-elements
- Scan-line effect via repeating linear gradient overlay
- Gauge needle via CSS transforms with transition
- CRT flicker via subtle opacity animation
