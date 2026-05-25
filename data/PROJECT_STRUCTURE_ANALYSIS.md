# Projektstruktur - Theme, Layout und Komponenten Analyse

Datum: 2026-05-02
Status: Vollständige Inventarisation durchgeführt

## 1. Theme-Dateien

### Dashboard React
- **Tailwind Config**: `/home/clawd/saas/legal/dashboard-react/tailwind.config.ts`
  - Dark Mode aktiviert: `darkMode: 'class'`
  - Custom Colors (Complyo Color Palette)
  - Extended Animations und Keyframes
  
- **Global CSS**: `/home/clawd/saas/legal/dashboard-react/src/app/globals.css`
  - Größe: 915 Zeilen
  - Enthält: AI-Komponenten-Styles, Theme-CSS, Glassmorphism, Animations
  - Light/Dark Mode CSS Variables
  - Sidebar Navigation Styles
  - Gauge und Flow Widget Animations

- **Theme Context**: `/home/clawd/saas/legal/dashboard-react/src/contexts/ThemeContext.tsx`
  - Theme Zustandsverwaltung (Light/Dark)
  - localStorage Persistierung
  - System Preference Detection
  - Hook: `useTheme()`

### Landing React
- **Tailwind Config**: `/home/clawd/saas/legal/landing-react/tailwind.config.ts`
  - Gleiche Struktur wie Dashboard
  - Vereinfachte Color-Palette
  
- **Design System CSS**: `/home/clawd/saas/legal/landing-react/src/styles/design-system.css`
  - Umfassende Design Token Definitionen
  - CSS Custom Properties für Farben, Abstände, Radien, Schatten
  - Base Styles für Typography und Komponenten
  - Dark Mode Media Query Support

- **Global CSS**: `/home/clawd/saas/legal/landing-react/src/app/globals.css`
  - (Tailwind Base/Components/Utilities)

---

## 2. Layout-Dateien

### Dashboard
- **Main Layout**: `/home/clawd/saas/legal/dashboard-react/src/app/layout.tsx`
  - Root Layout mit ThemeProvider Integration
  - Metadata und Fonts
  - Provider-Wrapper Struktur

- **AI Compliance Sub-Layout**: `/home/clawd/saas/legal/dashboard-react/src/app/ai-compliance/layout.tsx`
  - Spezialisiertes Layout für AI-Compliance Sektion

### Landing
- **Main Layout**: `/home/clawd/saas/legal/landing-react/src/app/layout.tsx`
  - Root Layout mit Theme Integration
  - Globale Styles und Metadata

---

## 3. Button-Komponenten

### Dashboard Button Component
**Datei**: `/home/clawd/saas/legal/dashboard-react/src/components/ui/button.tsx`
**Größe**: 50 Zeilen

```typescript
Interface ButtonProps:
- variant: 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive'
- size: 'sm' | 'md' | 'lg'
- isLoading: boolean
- className: string
- disabled: boolean

Varianten (mit Tailwind):
1. default: Gradient (Sky → Purple), Glowing Shadow
2. secondary: Zinc-800, Border-based
3. outline: Border-2, Hover-bg
4. ghost: Minimal, Hover-bg only
5. destructive: Red Theme
```

### Landing Button Component
**Datei**: `/home/clawd/saas/legal/landing-react/src/components/ui/button.tsx`
- Identische Struktur wie Dashboard

---

## 4. Farbpalette (Complyo)

### Dashboard tailwind.config.ts
```
- complyo.blue: #0ea5e9 (Sky-500)
- complyo.purple: #a855f7 (Purple-500)
- complyo.indigo: #6366f1 (Indigo-500)
- complyo.dark: #0c0a09 (Stone-950)
- complyo.slate: #18181b (Zinc-900)
- complyo.accent: #14b8a6 (Teal-500)
- complyo.muted: #27272a (Zinc-800)
- complyo.border: #3f3f46 (Zinc-700)
```

### Design System CSS Variables (Landing)
```
Primär: #2563eb (Blue-600)
Sekundär: #8b5cf6 (Violet)
Success: #10b981
Warning: #f59e0b
Danger: #ef4444
Info: #06b6d4
```

---

## 5. Theme-Management System

### CSS Variables (Root)
```css
Dark Mode (Default):
- --background: 222.2 84% 4.9% (sehr dunkel)
- --foreground: 210 40% 98% (hell)
- --card-bg: 240 10% 3.9%
- --card-border: 240 3.7% 15.9%

Light Mode:
- --background: 0 0% 100% (weiß)
- --foreground: 222.2 84% 4.9% (dunkelgrau)
- --card-bg: 0 0% 100%
- --card-border: 240 5.9% 90%
```

### Sidebar Theme Variables
```css
Dark Mode:
- --sidebar-bg: #0c0a09
- --sidebar-border: rgba(255,255,255,0.06)
- --sidebar-active-bg: rgba(249,115,22,0.12)
- --sidebar-active-border: #f97316

Light Mode:
- --sidebar-bg: #ffffff
- --sidebar-border: rgba(0,0,0,0.07)
```

---

## 6. CSS Klassen-Struktur

### AI-Komponenten Styles (globals.css)
```
.ai-primary          → Gradient Button mit Glitter Effect
.ai-glow             → Glowing Box Animation
.ai-card             → Modern Card mit Glassmorphism
.ai-gradient-text    → Gradient Text Effect
.ai-badge            → Badge Component
.ai-glass            → Glassmorphism Background
.ai-scanning         → Scan Animation Line
.ai-sparkle          → Sparkle Twinkle Effect
```

### Glassmorphism Classes
```
.glass-effect        → Light Blur mit transparentem Hintergrund
.glass-card          → Stärkere Version für Cards
.glass-strong        → Maximale Undurchsichtigkeit
```

### Theme-Aware Text Classes
```
.text-theme-primary  → Weiß (dark) / Grau-900 (light)
.text-theme-secondary → Zinc-400 (dark) / Grau-700 (light)
.text-theme-muted    → Zinc-500 (dark) / Grau-600 (light)
```

---

## 7. Animations

### Tailwind Keyframes (config)
- `fade-in`: 0.4s cubic-bezier
- `slide-up`: 0.3s translateY
- `slide-down`: 0.3s translateY
- `scale-in`: 0.2s scale transform
- `pulse-glow`: 3s infinite blue/purple glow
- `float`: 6s translateY infinite
- `gradient`: 8s background-position infinite
- `shimmer`: 2s translateX infinite

### CSS @keyframes (globals.css)
- `ai-pulse`: Opacity + Scale Pulsation
- `ai-typing-bounce`: Bounce Animation für Typing-Indicator
- `ai-loading`: Loading Bar Animation
- `ai-scan-line`: Scanning Effect
- `ai-sparkle-twinkle`: Sparkle Twinkle
- `slide-in-up`, `slide-in-from-bottom`: Slide Animations
- `gauge-fill`: Gauge SVG Fill Animation

---

## 8. Dateiübersicht (Zusammenfassung)

| Kategorie | Datei | Zeilen | Zweck |
|-----------|-------|--------|-------|
| Theme Config | `dashboard-react/tailwind.config.ts` | 94 | Tailwind Theme Config |
| Theme Config | `landing-react/tailwind.config.ts` | 54 | Tailwind Theme Config (Landing) |
| Global Styles | `dashboard-react/src/app/globals.css` | 915 | Haupt-Styles + AI/Theme |
| Design System | `landing-react/src/styles/design-system.css` | 390 | Design Token System |
| Theme Context | `dashboard-react/src/contexts/ThemeContext.tsx` | 77 | Theme State Management |
| Button UI | `dashboard-react/src/components/ui/button.tsx` | 50 | Button Component |
| Button UI | `landing-react/src/components/ui/button.tsx` | 50 | Button Component |
| Layout | `dashboard-react/src/app/layout.tsx` | - | Root Layout |
| Layout | `landing-react/src/app/layout.tsx` | - | Landing Root Layout |

---

## 9. Theme-Modi

### Dark Mode (Standard)
- Aktiviert durch Klasse `.dark` auf `<html>`
- Gradient Mesh Hintergrund
- Glassmorphism mit 0.03 opacity
- Blaue/Purple Akzentfarben auf dunklem Grund

### Light Mode
- Aktiviert durch Klasse `.light` auf `<html>`
- Clean White Background mit Gradient
- Stärkere Kontraste
- Focus Indikatoren mit Blue-600

### Theme Persistierung
- `localStorage.setItem('complyo-theme', theme)`
- Fallback auf System Preference via `prefers-color-scheme`

---

## 10. Wichtige CSS-Techniken

1. **CSS Custom Properties**: Dark/Light Mode Switching über `--background`, `--foreground`
2. **@layer Directives**: Tailwind Layer Organization (base, components, utilities)
3. **backdrop-filter**: Glassmorphism Effects
4. **background-clip**: Text Gradient Effects
5. **CSS Grid + Flex**: Layout-Struktur
6. **SVG Animations**: Gauge, Flow Widget Strokes
7. **Focus-visible**: WCAG 2.4.7 Compliance (2px outline)
8. **Scrollbar Styling**: Gradient Scrollbar in beiden Modes

---

## 11. Responsive Design

- Tailwind default breakpoints werden verwendet
- Media Queries für Print und prefers-color-scheme
- Mobile-First Ansatz
- Sidebar responsive (collapsed auf klein)

---

## Architektur Summary

```
Theme System:
├── Tailwind Config (tailwind.config.ts)
├── CSS Variables (:root, .light, .dark)
├── React Context (ThemeContext + useTheme)
├── Global Styles (globals.css)
└── Component Styles (UI Components)

Komponenten:
├── Button (5 Varianten)
├── Cards (glass-effect, glass-card, glass-strong)
├── AI-Elemente (glow, badge, scanning)
└── Theme-aware Text/Bg Classes

Dark/Light Mode:
├── localStorage Persistierung
├── System Preference Fallback
├── Class-based Switching (.dark / .light)
└── CSS Variable Override
```

---

