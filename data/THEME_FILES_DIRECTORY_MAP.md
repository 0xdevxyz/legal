# Theme & Layout Dateien - Verzeichnisstruktur

## Dateibaum mit voller Pfade

```
/home/clawd/saas/legal/
├── dashboard-react/
│   ├── tailwind.config.ts                          [94 Zeilen]
│   │   └── Theme Config mit Complyo Farbpalette
│   │       - darkMode: 'class'
│   │       - Custom Colors (blue, purple, indigo, dark, slate, accent, muted, border)
│   │       - Extended: backgroundImage, backdropBlur, boxShadow, animation, keyframes
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx                          [Root Layout]
│   │   │   │   └── ThemeProvider wrapper
│   │   │   │
│   │   │   ├── ai-compliance/
│   │   │   │   └── layout.tsx                      [Sub-Layout]
│   │   │   │
│   │   │   └── globals.css                         [915 Zeilen]
│   │   │       ├── @tailwind directives
│   │   │       ├── CSS Custom Properties (:root, .light, .dark)
│   │   │       ├── AI-Komponenten Styles (.ai-primary, .ai-card, etc.)
│   │   │       ├── Glassmorphism (.glass-effect, .glass-card, .glass-strong)
│   │   │       ├── Theme-aware Text Classes (.text-theme-primary, etc.)
│   │   │       ├── Sidebar Styles (.sidebar-nav, .sidebar-item)
│   │   │       ├── Gauge & Flow Animations
│   │   │       ├── Custom Scrollbar Styles
│   │   │       ├── Focus-Visible (WCAG 2.4.7)
│   │   │       └── @keyframes (ai-pulse, ai-loading, ai-scan-line, etc.)
│   │   │
│   │   └── components/
│   │       └── ui/
│   │           └── button.tsx                      [50 Zeilen]
│   │               ├── Variant: 'default' (gradient blue→purple)
│   │               ├── Variant: 'secondary' (zinc-800)
│   │               ├── Variant: 'outline' (border-based)
│   │               ├── Variant: 'ghost' (minimal)
│   │               ├── Variant: 'destructive' (red)
│   │               └── Size: sm, md, lg
│   │
│   └── contexts/
│       └── ThemeContext.tsx                        [77 Zeilen]
│           ├── ThemeProvider Component
│           ├── useTheme() Hook
│           ├── Theme State (light | dark)
│           ├── localStorage Persistierung ('complyo-theme')
│           └── System Preference Detection (prefers-color-scheme)
│
└── landing-react/
    ├── tailwind.config.ts                          [54 Zeilen]
    │   └── Theme Config (vereinfacht)
    │       - darkMode: 'class'
    │       - Custom Colors (complyo palette)
    │       - Animations (fade-in, slide-up, pulse-glow, float)
    │
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx                          [Root Layout]
    │   │   │   └── Theme Integration
    │   │   │
    │   │   └── globals.css                         [@tailwind directives]
    │   │
    │   ├── styles/
    │   │   └── design-system.css                   [390 Zeilen]
    │   │       ├── :root CSS Custom Properties
    │   │       │   ├── Brand Colors (--primary, --secondary)
    │   │       │   ├── Semantic Colors (--success, --warning, --danger, --info)
    │   │       │   ├── Neutral Colors (--dark, --gray, --white)
    │   │       │   ├── Spacing Variables (--spacing-xs bis --spacing-3xl)
    │   │       │   ├── Border Radius (--radius-sm bis --radius-full)
    │   │       │   ├── Shadows (--shadow-sm bis --shadow-2xl)
    │   │       │   ├── Typography (--font-sans, --font-mono)
    │   │       │   └── Transitions (--transition-fast, --transition-base, --transition-slow)
    │   │       │
    │   │       ├── Base Styles
    │   │       │   ├── * { box-sizing, padding, margin }
    │   │       │   ├── html { scroll-behavior }
    │   │       │   ├── body { font-family, colors }
    │   │       │   └── Typography (h1-h6, p, code)
    │   │       │
    │   │       ├── Component Styles
    │   │       │   ├── .btn, .btn-primary, .btn-secondary
    │   │       │   ├── .card, .card:hover
    │   │       │   ├── .badge, .badge-success, .badge-warning, etc.
    │   │       │   └── .gradient-text
    │   │       │
    │   │       ├── Animations
    │   │       │   ├── @keyframes fadeIn, slideInLeft, slideInRight, pulse
    │   │       │   └── .animate-fade-in, .animate-slide-in-left, etc.
    │   │       │
    │   │       ├── Responsive Utilities
    │   │       │   └── @media (max-width: 768px)
    │   │       │
    │   │       ├── Print Styles
    │   │       │   └── @media print
    │   │       │
    │   │       ├── Dark Mode
    │   │       │   ├── @media (prefers-color-scheme: dark)
    │   │       │   └── .dark { CSS Override }
    │   │       │
    │   │       └── Dark Mode Colors
    │   │           ├── --background, --foreground
    │   │           ├── --white, --gray, --dark
    │   │           ├── .dark body { background, color }
    │   │           └── .dark .bg-*, .dark .text-*
    │   │
    │   └── components/
    │       └── ui/
    │           └── button.tsx                      [50 Zeilen]
    │               └── [Identisch mit Dashboard]
```

---

## Absolute Dateipfade (vollständig)

### Theme/Config Dateien
1. `/home/clawd/saas/legal/dashboard-react/tailwind.config.ts`
2. `/home/clawd/saas/legal/landing-react/tailwind.config.ts`

### CSS/Styles Dateien
3. `/home/clawd/saas/legal/dashboard-react/src/app/globals.css` (915 Zeilen)
4. `/home/clawd/saas/legal/landing-react/src/app/globals.css`
5. `/home/clawd/saas/legal/landing-react/src/styles/design-system.css` (390 Zeilen)

### Theme/Context Dateien
6. `/home/clawd/saas/legal/dashboard-react/src/contexts/ThemeContext.tsx` (77 Zeilen)

### Layout Dateien
7. `/home/clawd/saas/legal/dashboard-react/src/app/layout.tsx`
8. `/home/clawd/saas/legal/dashboard-react/src/app/ai-compliance/layout.tsx`
9. `/home/clawd/saas/legal/landing-react/src/app/layout.tsx`

### Button-Komponenten
10. `/home/clawd/saas/legal/dashboard-react/src/components/ui/button.tsx` (50 Zeilen)
11. `/home/clawd/saas/legal/landing-react/src/components/ui/button.tsx` (50 Zeilen)

---

## Datei-Abhängigkeiten (Imports)

```
globals.css
  ├─→ Keine Imports (CSS Datei)
  └─→ Wird importiert in: layout.tsx

tailwind.config.ts
  ├─→ Konfiguriert: Tailwind CSS
  └─→ Wird gelesen von: Tailwind Build Process

ThemeContext.tsx
  ├─→ Importiert von: layout.tsx (als Provider)
  └─→ Bereitgestellt für: useTheme() Hook in Komponenten

button.tsx
  ├─→ Importiert: @/lib/utils (cn function)
  ├─→ Importiert: lucide-react (Loader2 Icon)
  └─→ Verwendet Tailwind Utility Classes

layout.tsx
  ├─→ Importiert: ThemeProvider
  ├─→ Importiert: globals.css (indirekt über import)
  └─→ Wrapper für alle Child Components
```

---

## CSS-Variablen-Übersicht

### Root Level CSS Custom Properties

**Dark Mode (Default)**
```css
:root {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card-bg: 240 10% 3.9%;
  --card-border: 240 3.7% 15.9%;
  --glass-bg: rgba(255, 255, 255, 0.03);
  --glass-border: rgba(255, 255, 255, 0.08);
  --gradient-mesh: linear-gradient(135deg, #09090b 0%, #18181b 35%, #09090b 100%);
}
```

**Light Mode Override**
```css
.light {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card-bg: 0 0% 100%;
  --card-border: 240 5.9% 90%;
  --glass-bg: rgba(255, 255, 255, 1);
  --glass-border: rgba(0, 0, 0, 0.07);
  --gradient-mesh: #f1f5f9;
}
```

**Dashboard Sidebar Variables**
```css
:root {
  --sidebar-width: 256px;
  --sidebar-collapsed-width: 72px;
  --topbar-height: 64px;
  --gauge-red: #ef4444;
  --gauge-yellow: #eab308;
  --gauge-light-green: #84cc16;
  --gauge-green: #22c55e;
  --flow-active: #f97316;
  --flow-inactive: #3f3f46;
  --sidebar-bg: #0c0a09;
  --sidebar-border: rgba(255,255,255,0.06);
  --sidebar-hover: rgba(255,255,255,0.05);
  --sidebar-active-bg: rgba(249,115,22,0.12);
  --sidebar-active-border: #f97316;
}

.light {
  --sidebar-bg: #ffffff;
  --sidebar-border: rgba(0,0,0,0.07);
  --sidebar-hover: rgba(0,0,0,0.04);
  --sidebar-active-bg: rgba(249,115,22,0.08);
  --sidebar-active-border: #f97316;
}
```

---

## CSS Klassen nach Kategorie

### Theme-Aware Text (Multi-Mode)
- `.text-theme-primary` → weiß (dark) / grau-900 (light)
- `.text-theme-secondary` → zinc-400 (dark) / grau-700 (light)
- `.text-theme-muted` → zinc-500 (dark) / grau-600 (light)

### Theme-Aware Backgrounds
- `.bg-theme-card` → zinc-900/80 (dark) / white (light)
- `.bg-theme-hover` → white/5 (dark) / gray-50 (light)

### Glassmorphism
- `.glass-effect` → Light glassmorphism
- `.glass-card` → Medium glassmorphism with shadow
- `.glass-strong` → Heavy glassmorphism

### AI-Components
- `.ai-primary` → Gradient Button mit Glitter
- `.ai-glow` → Pulsing Glow Effect
- `.ai-card` → Modern AI Card
- `.ai-gradient-text` → Gradient Text
- `.ai-badge` → Badge with Shadow
- `.ai-glass` → Glassmorphism variant
- `.ai-scanning` → Scan Line Animation
- `.ai-sparkle` → Sparkle Twinkle

### Sidebar Navigation
- `.sidebar-nav` → Container (sticky, flex)
- `.sidebar-nav.collapsed` → Collapsed state
- `.sidebar-item` → Individual nav item
- `.sidebar-item.active` → Active state with border

### Stats & Metrics
- `.stat-card-new` → New stat card style
- `.gauge-arc` → SVG gauge animation
- `.gauge-score-number` → Score counter
- `.flow-line-active` → Active flow line
- `.flow-line-inactive` → Inactive flow line

### Status Indicators
- `.status-led` → LED indicator
- `.status-led.green`, `.yellow`, `.red`, `.gray`

---

## Animationen - Vollständige Liste

### Tailwind Config Keyframes
1. `fadeIn` - 0.4s opacity transition
2. `slideUp` - 0.3s translateY(-16px → 0)
3. `slideDown` - 0.3s translateY(16px → 0)
4. `scaleIn` - 0.2s scale(0.95 → 1)
5. `pulseGlow` - 3s infinite blue/purple glow
6. `float` - 6s translateY(0 → -8px)
7. `gradient` - 8s background-position animation
8. `shimmer` - 2s translateX(-100% → 100%)

### CSS Keyframes in globals.css
1. `ai-pulse` - opacity + scale pulsation
2. `ai-glow-pulse` - scale pulsation
3. `ai-typing-bounce` - translateY bounce
4. `ai-loading` - translateX progress bar
5. `ai-float` - translateY float effect
6. `ai-scan-line` - translateX scanning line
7. `ai-sparkle-twinkle` - opacity + rotation + scale
8. `slide-in-up` - translateY(20px → 0) + opacity
9. `slide-in-from-bottom` - translateY(40px → 0) + opacity
10. `slide-in-from-right` - translateX(20px → 0) + opacity
11. `gauge-fill` - SVG stroke-dashoffset animation
12. `count-up` - scale(0.8 → 1) + opacity
13. `flow-pulse` - opacity + stroke-width pulsation
14. `flow-dash` - stroke-dashoffset animation

---

## Summary: Welche Dateien es gibt

### Hauptdateien (11 Dateien)

| # | Kategorie | Datei | Größe |
|---|-----------|-------|-------|
| 1 | Config | dashboard-react/tailwind.config.ts | 94 L |
| 2 | Config | landing-react/tailwind.config.ts | 54 L |
| 3 | Styles | dashboard-react/src/app/globals.css | 915 L |
| 4 | Styles | landing-react/src/app/globals.css | ? L |
| 5 | Design | landing-react/src/styles/design-system.css | 390 L |
| 6 | Context | dashboard-react/src/contexts/ThemeContext.tsx | 77 L |
| 7 | Layout | dashboard-react/src/app/layout.tsx | ? L |
| 8 | Layout | dashboard-react/src/app/ai-compliance/layout.tsx | ? L |
| 9 | Layout | landing-react/src/app/layout.tsx | ? L |
| 10 | Component | dashboard-react/src/components/ui/button.tsx | 50 L |
| 11 | Component | landing-react/src/components/ui/button.tsx | 50 L |

---

