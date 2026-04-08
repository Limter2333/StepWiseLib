# AI Multi-Agent System - Neo-Brutalist Style

## 1. Concept & Vision

A bold, aggressive AI multi-agent system landing page that channels Neo-Brutalist design with raw geometric power. The page exudes confidence and rebellion—"BREAK THE NOISE" isn't just text, it's a manifesto. Every element screams intentionality with thick borders, hard shadows, and uncompromising color clashes that demand attention.

## 2. Design Language

### Aesthetic Direction
- **Movement**: Neo-Brutalist / Memphis Design Revival
- **Reference**: Early 90s web meets contemporary bold editorial design
- **Mood**: Aggressive, confident, unapologetic, disruptive

### Color Palette
| Name | Hex | Usage |
|------|-----|-------|
| Orange | `#FF6B35` | Primary accent, CTAs |
| Cyan | `#2EC4B6` | Secondary accent, highlights |
| Yellow | `#FFDD00` | Shadows, emphasis |
| Red | `#E71D36` | Alerts, active states |
| Deep Blue | `#011627` | Text, borders, backgrounds |
| White | `#FFFFFF` | Backgrounds, text on dark |

### Typography
- **Primary**: Space Grotesk (700, 900) - Google Fonts
- **Monospace**: JetBrains Mono - fallback for code/console
- **Headings**: 900 weight, oversized with clamp(48px, 8vw, 96px)
- **Body**: 700 weight, 16-18px
- **Transform**: UPPERCASE for nav and important labels

### Spatial System
- Border width: 4px solid black everywhere
- Hard shadow: 6px 6px 0 #FFDD00
- Hover shadow: 8px 8px 0 #011627
- Base spacing unit: 8px
- Section padding: 80px vertical, responsive down to 40px

### Motion Philosophy
- **Hover transforms**: translate(-4px, -4px) - elements lift and shift left-up
- **Transitions**: 150ms ease-out for snappy, mechanical feel
- **No soft animations** - movements are deliberate and abrupt
- **Console typing**: Character-by-character reveal for terminal effect

### Visual Assets
- **Icons**: Geometric shapes only - circles, squares, triangles
- **Agent nodes**: Colored circles with initials
- **Decorative**: Diagonal stripes, grid patterns as accents

## 3. Layout & Structure

### Page Flow
1. **Navigation** (sticky): Bold horizontal bar with geometric color blocks
2. **Hero**: Full viewport, massive typography, asymmetric card composition
3. **Stats**: 4-column grid of contrasting stat cards
4. **Features**: 3-column brutalist feature cards
5. **Agents**: 6 circular agent nodes with interconnections
6. **Console**: Terminal-style activity monitor
7. **Footer**: High-contrast CTA with giant text

### Responsive Breakpoints
- Desktop: 1024px+ (full layout)
- Tablet: 768px-1023px (2-column grids)
- Mobile: <768px (single column, stacked)

## 4. Features & Interactions

### Navigation
- Fixed top bar with logo and nav links
- Hover: background color shift, translate effect
- Active state: inverted colors

### Hero Section
- Main title: "BREAK. THE. NOISE." in massive type
- Animated gradient background
- Floating asymmetric cards with agent previews

### Stats Cards
- Each card has distinct background color
- Numbers animate counting up on scroll into view
- Hover: lift + shadow change

### Feature Cards
- 3 columns, equal height
- Icon + title + description
- Hover: full lift effect with shadow swap to dark

### Agent Nodes
- 6 circular nodes in hexagonal-ish layout
- Each with unique color and 2-letter initials
- Connected by animated dashed lines
- Hover: pulse animation

### Console Window
- Terminal aesthetic with blinking cursor
- Auto-scrolling log of agent activities
- Typing animation for new entries

### Footer CTA
- Giant "JOIN THE REBELLION" text
- Email input with brutalist styling
- Submit button with hover state

## 5. Component Inventory

### Button
- Default: Yellow background, 4px border, 6px shadow
- Hover: translate(-4px, -4px), shadow extends to 8px dark
- Active: translate back, shadow shrinks

### Card
- White background, 4px border
- 6px yellow shadow
- Hover: translate(-4px, -4px), dark shadow

### Input Field
- White background, 4px border
- Focus: cyan border, no shadow change
- JetBrains Mono font

### Nav Link
- Uppercase, bold
- Hover: background fill, translate

### Stat Block
- Full background color
- Giant number, small label
- Hover: scale(1.02)

### Agent Circle
- 80px diameter circle
- 4px border
- Centered initials
- Hover: scale(1.1), shadow appears

## 6. Technical Approach

### Implementation
- Single HTML file with embedded CSS and JS
- CSS custom properties for all colors
- CSS Grid and Flexbox for layouts
- Vanilla JS for interactions and console simulation
- IntersectionObserver for scroll animations

### Key CSS Patterns
```css
--border: 4px solid #011627;
--shadow: 6px 6px 0 #FFDD00;
--shadow-hover: 8px 8px 0 #011627;
--transition: 150ms ease-out;
```

### Performance
- Font preloading for Space Grotesk
- Minimal JS, no external dependencies
- CSS-only animations where possible
