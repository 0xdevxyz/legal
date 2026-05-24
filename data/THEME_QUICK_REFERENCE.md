# Theme & Komponenten - Quick Reference

## Schnelle Übersicht: Was du wo findest

### 1. Theme Umschalten (Dark/Light Mode)

**Benutzer-Perspective:**
```javascript
// In einer React Komponente
import { useTheme } from '@/contexts/ThemeContext';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <button onClick={toggleTheme}>
      Aktueller Mode: {theme}
    </button>
  );
}
```

**Technisch:**
- Datei: `/home/clawd/saas/legal/dashboard-react/src/contexts/ThemeContext.tsx`
- Hook: `useTheme()` liefert `{ theme, toggleTheme, setTheme }`
- Speicherung: localStorage ('complyo-theme')
- CSS-Klasse: `.dark` oder `.light` auf `<html>`

---

### 2. Button Component verwenden

**Beispiel:**
```jsx
import { Button } from '@/components/ui/button';

// Default (Gradient Blue→Purple)
<Button>Click me</Button>

// Mit Varianten
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Delete</Button>

// Mit Größen
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// Mit Loading State
<Button isLoading>Laden...</Button>

// Mit Custom CSS
<Button className="custom-class">Custom</Button>
```

**Quelle:**
- Datei: `/home/clawd/saas/legal/dashboard-react/src/components/ui/button.tsx`
- Varianten: default, secondary, outline, ghost, destructive
- Größen: sm, md, lg

---

### 3. CSS Klassen für Styling

#### Glassmorphism
```html
<!-- Light Blur -->
<div class="glass-effect">Content</div>

<!-- Medium Blur mit Shadow -->
<div class="glass-card">Card Content</div>

<!-- Heavy Blur -->
<div class="glass-strong">Strong Glass</div>
```

#### AI Components
```html
<!-- Gradient Button -->
<button class="ai-primary">AI Action</button>

<!-- Glowing Effect -->
<div class="ai-glow">Glow Content</div>

<!-- Modern AI Card -->
<div class="ai-card">AI Card</div>

<!-- Gradient Text -->
<h1 class="ai-gradient-text">Modern Text</h1>

<!-- Badge -->
<span class="ai-badge">AI</span>

<!-- Scanning Animation -->
<div class="ai-scanning">Loading...</div>

<!-- Sparkle Effect -->
<div class="ai-sparkle">✨ Special</div>
```

#### Theme-Aware Classes
```html
<!-- Automatisch wechselt mit Dark/Light Mode -->
<h1 class="text-theme-primary">Primary Text</h1>
<p class="text-theme-secondary">Secondary Text</p>
<span class="text-theme-muted">Muted Text</span>

<div class="bg-theme-card">Card Background</div>
<div class="bg-theme-hover">Hover Background</div>
```

#### Sidebar Navigation
```html
<nav class="sidebar-nav">
  <a href="/" class="sidebar-item">Home</a>
  <a href="/dashboard" class="sidebar-item active">Dashboard</a>
</nav>

<!-- Collapsed Mode -->
<nav class="sidebar-nav collapsed">
  ...
</nav>
```

---

### 4. CSS Custom Properties (Farben)

#### Primäre Farben
```css
/* In tailwind.config.ts definiert: */
complyo.blue:    #0ea5e9  /* Sky-500 */
complyo.purple:  #a855f7  /* Purple-500 */
complyo.indigo:  #6366f1  /* Indigo-500 */
complyo.accent:  #14b8a6  /* Teal-500 */
```

#### Use in CSS
```css
/* Tailwind Utilities */
<div class="bg-complyo-blue text-white">Blue Button</div>
<div class="border border-complyo-border">Border</div>

/* CSS Custom Properties */
:root {
  --background: 222.2 84% 4.9%;      /* Dark Mode */
  --foreground: 210 40% 98%;
  --card-bg: 240 10% 3.9%;
}

.light {
  --background: 0 0% 100%;           /* Light Mode */
  --foreground: 222.2 84% 4.9%;
}

/* Verwendung */
<div style="background: hsl(var(--background))">
  Dynamic Background
</div>
```

---

### 5. Animationen verwenden

#### Tailwind Animationen (aus config)
```html
<!-- Fade In -->
<div class="animate-fade-in">Fades in</div>

<!-- Slide Up -->
<div class="animate-slide-up">Slides up</div>

<!-- Slide Down -->
<div class="animate-slide-down">Slides down</div>

<!-- Scale In -->
<div class="animate-scale-in">Scales in</div>

<!-- Pulse Glow -->
<div class="animate-pulse-glow">Glowing pulse</div>

<!-- Float -->
<div class="animate-float">Floating element</div>

<!-- Gradient Animation -->
<div class="animate-gradient">Gradient shift</div>

<!-- Shimmer -->
<div class="animate-shimmer">Shimmering</div>
```

#### CSS Classes aus globals.css
```html
<!-- Fade In -->
<div class="animate-in">Slides in from bottom</div>
<div class="fade-in">Fades in</div>

<!-- Slide Animations -->
<div class="slide-in-from-bottom-4">From bottom</div>
<div class="slide-in-from-right">From right</div>

<!-- AI Animations -->
<div class="ai-float">Floating</div>
<div class="ai-pulse">Pulsing</div>
```

---

### 6. Dark/Light Mode Markup

#### Automatische Farb-Anpassung
```html
<!-- Diese Klassen passen sich automatisch an -->
<div class="text-white dark:text-white">Weiß im Dark Mode</div>

<!-- Light Mode Override -->
<div class="light text-gray-900">Grau im Light Mode</div>

<!-- Conditional nach Mode -->
<div class="bg-zinc-900/80 dark:bg-zinc-900/80">
  <!-- Wird mit .dark Klasse angewendet -->
</div>

<div class="light .glass-effect">
  <!-- Wird mit .light Klasse angewendet -->
</div>
```

#### HTML struktur
```html
<!-- Dark Mode aktiviert -->
<html class="dark">
  <!-- Alles wird dunkel -->
</html>

<!-- Light Mode aktiviert -->
<html class="light">
  <!-- Alles wird hell -->
</html>
```

---

### 7. Focus & Accessibility (WCAG 2.4.7)

```css
/* Automatisch auf allen interaktiven Elementen */
:focus-visible {
  outline: 2px solid #3b82f6;      /* Dark Mode: Blue */
  outline-offset: 2px;
}

.light :focus-visible {
  outline: 2px solid #2563eb;      /* Light Mode: Darker Blue */
  outline-offset: 2px;
}

/* Angewendet auf: */
button:focus-visible
a:focus-visible
input:focus-visible
select:focus-visible
textarea:focus-visible
[role="button"]:focus-visible
[role="tab"]:focus-visible
[role="menuitem"]:focus-visible
[tabindex]:focus-visible
```

---

### 8. Scrollbar Styling

#### Standardisiert für beide Modes
```css
/* WebKit Scrollbars (Chrome, Safari) */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  /* Dark Mode: #18181b, Light Mode: #f1f5f9 */
}

::-webkit-scrollbar-thumb {
  /* Gradient: zinc-700 to zinc-600 (dark) */
  /* Gradient: slate-400 to slate-500 (light) */
}

/* Firefox Scrollbar */
* {
  scrollbar-width: thin;
  scrollbar-color: #3f3f46 #18181b; /* Dark Mode */
}

.light * {
  scrollbar-color: #cbd5e1 #f1f5f9; /* Light Mode */
}
```

#### Custom AI Scrollbar
```html
<div class="ai-scrollbar">
  <!-- Gradient Scrollbar mit Blue→Purple -->
</div>
```

---

### 9. Gauge & Flow Widgets (Dashboard)

#### CSS Variables für Gauge
```css
--gauge-red:          #ef4444
--gauge-yellow:       #eab308
--gauge-light-green:  #84cc16
--gauge-green:        #22c55e
```

#### CSS Classes
```html
<!-- Gauge SVG Animation -->
<svg class="gauge-arc">...</svg>

<!-- Score Number Animation -->
<span class="gauge-score-number">95</span>

<!-- Flow Line (Active) -->
<line class="flow-line-active">...</line>

<!-- Flow Line (Inactive) -->
<line class="flow-line-inactive">...</line>

<!-- Stat Card -->
<div class="stat-card-new">Metric</div>
```

---

### 10. Sidebar Navigation Configuration

```css
--sidebar-width: 256px;
--sidebar-collapsed-width: 72px;
--topbar-height: 64px;

/* Dark Mode */
--sidebar-bg: #0c0a09;
--sidebar-border: rgba(255,255,255,0.06);
--sidebar-hover: rgba(255,255,255,0.05);
--sidebar-active-bg: rgba(249,115,22,0.12);
--sidebar-active-border: #f97316;

/* Light Mode */
.light {
  --sidebar-bg: #ffffff;
  --sidebar-border: rgba(0,0,0,0.07);
  --sidebar-hover: rgba(0,0,0,0.04);
  --sidebar-active-bg: rgba(249,115,22,0.08);
  --sidebar-active-border: #f97316;
}
```

---

## Dateipfad Schnelleinstieg

| Was | Wo |
|-----|-----|
| Theme umschalten | `/dashboard-react/src/contexts/ThemeContext.tsx` |
| Button Komponente | `/dashboard-react/src/components/ui/button.tsx` |
| Globale Styles | `/dashboard-react/src/app/globals.css` |
| Tailwind Config | `/dashboard-react/tailwind.config.ts` |
| Design System | `/landing-react/src/styles/design-system.css` |
| Root Layout | `/dashboard-react/src/app/layout.tsx` |
| Farbpalette | `tailwind.config.ts` → `theme.extend.colors.complyo` |
| Animationen | `tailwind.config.ts` → `theme.extend.animation` |

---

## Hä­ufige Aufgaben

### Task: Button mit Custom Color
```jsx
<Button 
  className="bg-complyo-accent hover:bg-teal-600"
>
  Accent Button
</Button>
```

### Task: Custom Card mit Glassmorphism
```jsx
<div className="glass-card p-6 rounded-2xl">
  <h2 className="text-theme-primary">Card Title</h2>
  <p className="text-theme-secondary">Description</p>
</div>
```

### Task: Animierte Komponente
```jsx
<div className="animate-fade-in space-y-4">
  <h1 className="ai-gradient-text">Title</h1>
  <Button className="ai-primary">Action</Button>
</div>
```

### Task: Theme Toggle hinzufügen
```jsx
import { useTheme } from '@/contexts/ThemeContext';

export function Header() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <header className="glass-strong">
      <button onClick={toggleTheme}>
        {theme === 'dark' ? '☀️' : '🌙'}
      </button>
    </header>
  );
}
```

### Task: Responsive Sidebar Item
```jsx
<a 
  href="/dashboard" 
  className="sidebar-item active"
>
  <Icon className="sidebar-item-icon" />
  <span className="sidebar-item-label">Dashboard</span>
</a>
```

---

## Color Palette Übersicht

```
COMPLYO COLOR PALETTE (Dashboard):
├── Primary Colors
│   ├── Blue:      #0ea5e9 (Sky-500)
│   ├── Purple:    #a855f7 (Purple-500)
│   └── Indigo:    #6366f1 (Indigo-500)
│
├── Dark Colors
│   ├── Dark:      #0c0a09 (Stone-950) — Background
│   └── Slate:     #18181b (Zinc-900) — Cards
│
└── Accents
    ├── Accent:    #14b8a6 (Teal-500)
    ├── Muted:     #27272a (Zinc-800)
    └── Border:    #3f3f46 (Zinc-700)

LANDING COLOR PALETTE:
├── Primary:       #2563eb (Blue-600)
├── Secondary:     #8b5cf6 (Violet)
├── Success:       #10b981
├── Warning:       #f59e0b
├── Danger:        #ef4444
└── Info:          #06b6d4
```

---

## Tipps & Best Practices

1. **Theme Provider nutzen**: Immer `useTheme()` Hook verwenden
2. **CSS Variables nutzen**: Verwende `--background`, `--foreground` etc.
3. **Glassmorphism Klassen**: `.glass-effect` für konsistente Effekte
4. **AI-Komponenten**: `.ai-*` Klassen für moderne Animationen
5. **Accessibility**: `:focus-visible` wird automatisch angewendet
6. **Responsive**: Sidebar wird auf Klein-Screens automatisch collapsed
7. **Animation Performance**: Nutze `transform` und `opacity` statt `width`/`height`
8. **Light Mode Test**: Immer beide Modi testen!

---

