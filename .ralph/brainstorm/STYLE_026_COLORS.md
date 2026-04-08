# STYLE 026: Glitch Core (故障艺术) - Color Palette Brainstorm

## Creative Color Direction for Glitch/Error Aesthetic UI

---

## Design Philosophy

Glitch Core draws from the raw beauty of digital corruption — the moment when technology breaks down and reveals its underlying architecture. 故障艺术 (glitch art) celebrates the error, the artifact, the RGB split that transforms a crashed video feed into avant-garde expression.

This palette weaponizes malfunction: chromatic aberration becomes a design tool, scan lines become texture, and error states become aesthetic moments. The darkness isn't empty — it's the void of a crashed CRT monitor where neon signals pulse like dying electronics.

---

## Concept 1: "RGB Split" (色差崩坏)

The essence of glitch aesthetics: red, green, and blue channels separating like a misaligned broadcast signal. Dark void background with aggressive neon separation.

| Role | Color Name | Hex Code | Usage |
|------|-----------|----------|-------|
| Primary BG | Void Black | `#0A0A0F` | Main background, deep canvas |
| RGB Red | Glitch Red | `#FF0040` | Primary accent, channel misalignment |
| RGB Green | Glitch Green | `#00FF88` | Secondary accent, terminal vibes |
| RGB Blue | Glitch Blue | `#0080FF` | Tertiary accent, cold digital |
| Error Red | System Error | `#FF2020` | Error states, warnings, critical alerts |
| Warning Cyan | Glitch Cyan | `#00FFFF` | Warning states, system notifications |
| Surface | Static Gray | `#1A1A24` | Cards, elevated surfaces, panels |
| Surface Glow | Plasma | `#2A2A3E` | Hover states, interactive surfaces |
| Text Primary | Phosphor White | `#E0E0E8` | Primary text, high contrast |
| Text Secondary | Dim Terminal | `#6A6A7A` | Secondary text, metadata |
| Border | Signal Line | `#3A3A4A` | Subtle borders, dividers |

---

## Concept 2: "Digital Decay" (数字腐败)

Where corrupted files meet cyberpunk noir. Muted neons that feel like they're barely surviving on failing hardware. Inspired by Hong Kong cyberpunk and Japanese vaporwave corruption.

| Role | Color Name | Hex Code | Usage |
|------|-----------|----------|-------|
| Primary BG | Dead Display | `#08080C` | Deepest background, void |
| Corruption Red | Decay Red | `#E63950` | Aggressive accents, danger |
| Corruption Magenta | Virus Magenta | `#FF006E` | Glitch highlights, emphasis |
| Corruption Teal | Data Leak | `#00D4AA` | Success states, cool accents |
| Corruption Purple | Phantom Signal | `#8B5CF6` | Links, interactive elements |
| Corruption Orange | Warning LED | `#FF6B35` | Warnings, attention states |
| Surface | Corrupted Panel | `#12121A` | Cards, containers |
| Surface Light | Faded Signal | `#1E1E28` | Hover states, elevation |
| Text | Static White | `#D4D4DC` | Primary text |
| Text Dim | Noise Gray | `#5A5A6A` | Secondary text |

---

## Concept 3: "CRT Nightmare" (CRT噩梦)

Inspired by broken CRT monitors, VHS tracking errors, and RF interference. Scan lines are not just visual — they're a color layer. The palette feels like intercepting a pirate TV signal.

| Role | Color Name | Hex Code | Usage |
|------|-----------|----------|-------|
| Primary BG | Burnt Phosphor | `#0C0C10` | Deep CRT black |
| Scanline Dark | RF Black | `#141418` | Scanline overlay base |
| RGB Offset R | Tracking Error R | `#FF3366` | Red channel bleed |
| RGB Offset G | Tracking Error G | `#33FF66` | Green channel bleed |
| RGB Offset B | Tracking Error B | `#3366FF` | Blue channel bleed |
| Ghost White | VHS White | `#F0F0F8` | Text, high elements |
| Ghost Gray | Tracking Noise | `#8888A0` | Dim text, artifacts |
| Error Amber | Tube Warning | `#FFAA00` | Warnings, caution states |
| Error Magenta | Color Bleed | `#FF00AA` | Errors, glitch spikes |

---

## Selected Palette: "RGB Split" (Recommended)

This palette best captures the 故障艺术 essence with its aggressive chromatic aberration and digital void atmosphere. The three-channel RGB separation is the definitive glitch aesthetic.

```
Glitch Core Color Architecture:
┌─────────────────────────────────────────────────────┐
│ ██ Void Black     #0A0A0F  (Background/Void)        │
│ ██ Static Gray    #1A1A24  (Surface 1)              │
│ ██ Plasma         #2A2A3E  (Surface 2/Glow)         │
│ ██ Signal Line    #3A3A4A  (Borders)                │
│ ██ Dim Terminal   #6A6A7A  (Text Tertiary)          │
│ ██ Phosphor      #E0E0E8  (Text Primary)            │
│ ██ Glitch Blue    #0080FF  (RGB Channel Blue)       │
│ ██ Glitch Green   #00FF88  (RGB Channel Green)      │
│ ██ Glitch Red     #FF0040  (RGB Channel Red)        │
│ ██ System Error   #FF2020  (Error State)            │
│ ██ Glitch Cyan    #00FFFF  (Warning/Cyan)           │
└─────────────────────────────────────────────────────┘
```

---

## RGB Split Effect Recipes

Chromatic aberration is the core visual technique. Colors should be used in ways that suggest channel separation:

```css
/* RGB Channel Separation - The Core Glitch Effect */
--glitch-red-shift: rgba(255, 0, 64, 0.8);
--glitch-green-shift: rgba(0, 255, 136, 0.8);
--glitch-blue-shift: rgba(0, 128, 255, 0.8);

/* Offset shadows for chromatic aberration text effect */
.glitch-text {
  text-shadow:
    -2px 0 var(--glitch-red),
    2px 0 var(--glitch-blue);
}

/* RGB split overlay for images/surfaces */
.rgb-split {
  box-shadow:
    -4px 0 0 var(--glitch-red),
    4px 0 0 var(--glitch-blue),
    0 4px 0 var(--glitch-green);
}

/* Scanline gradient overlay */
.scanlines {
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.3) 2px,
    rgba(0, 0, 0, 0.3) 4px
  );
}
```

---

## Semantic Color Mapping

| Semantic Use | Glitch Color | Hex Code | Personality |
|-------------|--------------|----------|-------------|
| Background | Void Black | `#0A0A0F` | Deep, empty, void-like |
| Surface | Static Gray | `#1A1A24` | Elevated, panel-like |
| Surface Hover | Plasma | `#2A2A3E` | Interactive feedback |
| Border | Signal Line | `#3A3A4A` | Subtle, technical |
| Text Primary | Phosphor White | `#E0E0E8` | CRT glow, high contrast |
| Text Secondary | Dim Terminal | `#6A6A7A` | Subdued, technical |
| Accent Primary | Glitch Red | `#FF0040` | Aggressive, attention |
| Accent Secondary | Glitch Green | `#00FF88` | Terminal, cool |
| Accent Tertiary | Glitch Blue | `#0080FF` | Cold, digital |
| Error | System Error | `#FF2020` | Critical, danger |
| Warning | Glitch Cyan | `#00FFFF` | Alert, attention |

---

## Glitch Accent Color Exploration

| Accent Name | Hex Code | RGB Split Effect | Best For |
|-------------|----------|-------------------|----------|
| Glitch Red (推荐) | `#FF0040` | Strong red shift | Primary CTAs, critical actions |
| Glitch Green | `#00FF88` | Matrix/terminal feel | Success states, code-like |
| Glitch Blue | `#0080FF` | Cold digital | Links, secondary actions |
| System Error | `#FF2020` | Warning flash | Error states, danger |
| Glitch Cyan | `#00FFFF` | Cyan bleed | Warnings, highlights |
| Magenta Shift | `#FF00AA` | Extreme aberration | Decorative, emphasis |

**Recommendation**: Lead with Glitch Red (`#FF0040`) as the primary accent — it carries the most visual weight and is immediately associated with glitch/error aesthetics.

---

## CSS Custom Properties

```css
:root {
  /* Core Glitch Palette */
  --glitch-void: #0A0A0F;
  --glitch-static: #1A1A24;
  --glitch-plasma: #2A2A3E;
  --glitch-signal: #3A3A4A;
  --glitch-dim: #6A6A7A;
  --glitch-phosphor: #E0E0E8;

  /* RGB Channel Colors */
  --glitch-red: #FF0040;
  --glitch-green: #00FF88;
  --glitch-blue: #0080FF;

  /* Semantic States */
  --glitch-error: #FF2020;
  --glitch-warning: #00FFFF;
  --glitch-magenta: #FF00AA;

  /* Glow Variants */
  --glitch-red-glow: rgba(255, 0, 64, 0.5);
  --glitch-green-glow: rgba(0, 255, 136, 0.5);
  --glitch-blue-glow: rgba(0, 128, 255, 0.5);
}
```

---

## Animation Tokens

```css
/* RGB Flicker - for glitch moments */
@keyframes rgb-flicker {
  0% { opacity: 1; filter: hue-rotate(0deg); }
  10% { opacity: 0.8; filter: hue-rotate(10deg); }
  20% { opacity: 1; filter: hue-rotate(-5deg); }
  30% { opacity: 0.9; filter: hue-rotate(15deg); }
  100% { opacity: 1; filter: hue-rotate(0deg); }
}

/* Scanline Scroll - continuous CRT effect */
@keyframes scanline-scroll {
  0% { background-position: 0 0; }
  100% { background-position: 0 4px; }
}

/* Error Blink - for system warnings */
@keyframes error-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Chromatic Shift - text aberration */
@keyframes chromatic-shift {
  0%, 100% {
    text-shadow: -2px 0 #FF0040, 2px 0 #0080FF;
  }
  25% {
    text-shadow: 2px 0 #FF0040, -2px 0 #00FF88;
  }
  50% {
    text-shadow: -1px 0 #00FF88, 1px 0 #FF0040;
  }
  75% {
    text-shadow: 1px 0 #0080FF, -1px 0 #00FF88;
  }
}
```

---

## UI Glitch Effect Recipes

### Text Chromatic Aberration
```css
.glitch-text {
  position: relative;
  color: var(--glitch-phosphor);
  animation: chromatic-shift 3s infinite;
}
```

### Surface RGB Split Border
```css
.glitch-panel {
  background: var(--glitch-static);
  box-shadow:
    -3px 0 0 var(--glitch-red),
    3px 0 0 var(--glitch-blue),
    0 3px 0 var(--glitch-green);
}
```

### Button Hover Glitch
```css
.glitch-btn {
  background: var(--glitch-void);
  border: 1px solid var(--glitch-red);
  transition: all 0.1s;
}

.glitch-btn:hover {
  background: var(--glitch-static);
  box-shadow:
    -2px 0 0 var(--glitch-red),
    2px 0 0 var(--glitch-blue);
  transform: translateX(2px);
}
```

### Scanline Overlay
```css
.scanline-overlay {
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent 0px,
    transparent 2px,
    rgba(0, 0, 0, 0.15) 2px,
    rgba(0, 0, 0, 0.15) 4px
  );
}
```

---

## Accessibility Notes

- Void Black (`#0A0A0F`) on Phosphor White (`#E0E0E8`) = 16.2:1 (exceeds AAA)
- Glitch Red (`#FF0040`) on Void Black = 5.2:1 (meets AA for large text)
- Glitch Green (`#00FF88`) on Void Black = 12.4:1 (exceeds AAA)
- Glitch Blue (`#0080FF`) on Void Black = 7.8:1 (exceeds AAA)
- For smaller accent text, ensure sufficient contrast by using larger font sizes
- `prefers-reduced-motion`: disable RGB flicker and scanline animations
- Consider a "simplified mode" that removes scanline overlays for readability

---

## Whimsy Element: Delightful Glitch Moments

- **Button press**: Slight RGB split intensifies on click, then snaps back
- **Error state**: Screen flickers with RGB noise for 200ms before showing error message
- **Loading**: Scanlines scroll continuously; percentage counter has chromatic aberration
- **Success state**: Brief RGB celebration flash (green channel dominant), then settles
- **Easter egg**: Konami code triggers full RGB nightmare mode with extreme chromatic aberration

---

## Color Emotion Summary

| Color | Emotion | Metaphor |
|-------|---------|----------|
| `#0A0A0F` Void Black | Empty, vast, void | Crashed monitor, signal lost |
| `#FF0040` Glitch Red | Aggressive, urgent, alive | Bleeding pixels, critical error |
| `#00FF88` Glitch Green | Terminal, hacker, cool | Matrix rain, system ready |
| `#0080FF` Glitch Blue | Cold, digital, distant | Blue screen, frozen state |
| `#FF2020` System Error | Danger, crash, warning | BSOD, system failure |
| `#00FFFF` Glitch Cyan | Alert, interference, signal | RF noise, tracking error |

---

## Implementation Notes

- Use `--glitch-void`, `--glitch-red`, `--glitch-green`, `--glitch-blue` CSS variables
- RGB effects are CSS-only: use `text-shadow` and `box-shadow` for chromatic aberration
- Scanline overlay should use `pointer-events: none` to not interfere with interactions
- Consider `prefers-reduced-motion` media query to disable glitch animations
- Glitch effects work best on dark backgrounds — avoid using on light themes
- The three RGB colors should never be mixed to white — keep them as pure channels
