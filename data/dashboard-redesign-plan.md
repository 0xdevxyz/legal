# Dashboard Redesign Plan — Neuer Look (2026-05-02)

## Inspiration
- **Image-1 (DisputeFox)**: Helles, data-dichtes Dashboard mit Score-Gauge (Halbkreis), Tab-Navigation, Kachel-Layout, Farbindikatoren (Rot/Gelb/Grün)
- **Image-2 (Phoenix ZEUS-X)**: Dunkles, industrielles Dashboard mit Energy-Flow-Diagramm (Sankey-style), Bold-Headlines, Gauge-Anzeige (74%), Modul-Detail-Karten

## Design-Richtung
**Hybrides Dark-Theme**:
- Dunkler Hintergrund: `#09090b` / `#111113` (wie Phoenix)
- Accent: `#f97316` (Orange/Amber wie Phoenix) + `#22c55e` (Grün für positive Metriken)
- Score-Gauge im DisputeFox-Stil (Halbkreis, Farbskala, Trend-Indicator)
- Flow-Widget im Phoenix-Stil (Compliance-Bereiche als animierter Flow)
- Sidebar-Navigation statt reiner Top-Bar

## Architektur-Änderungen

### 1. Layout-Shell (layout.tsx)
```
RootLayout
└── Providers
    └── SidebarLayout (NEU)
        ├── Sidebar (NEU — links, collapsible)
        ├── TopBar (kompakt, nur Logo + SiteSwitcher + Avatar)
        └── main content (mit ml-sidebar-offset)
```

### 2. Neue Komponenten
| Datei | Zweck |
|-------|-------|
| `components/dashboard/Sidebar.tsx` | Collapsible Left-Nav: Icons + Labels, aktiver State |
| `components/dashboard/ComplianceGauge.tsx` | Halbkreis-Score (SVG, animiert, Farbskala Rot→Grün) |
| `components/dashboard/ComplianceFlowWidget.tsx` | 4 Compliance-Bereiche als Flow-Diagram mit Animationen |
| `components/dashboard/SidebarLayout.tsx` | Wrapper: flex-row, sidebar + content |

### 3. Geänderte Komponenten
| Datei | Änderung |
|-------|---------|
| `app/globals.css` | Sidebar-CSS-Variablen, Gauge-Styles, neue Animations |
| `app/layout.tsx` | SidebarLayout-Wrapper einbinden |
| `app/page.tsx` | Neues 3-Spalten-Grid: Gauge, Flow, Metriken |
| `components/dashboard/DashboardHeader.tsx` | Wird zu kompakter TopBar (Logo+Avatar only) |
| `components/dashboard/MetricsCards.tsx` | Kompaktere Kacheln, neue Farb-Kodierung |

## page.tsx — Neues Layout
```
┌────────────────────────────────────────────────────────┐
│  TopBar (h-16): Logo | SiteSwitcher | Avatar           │
├──────────────────────────────────────────────────────  │
│ Sidebar │  Main Content                                 │
│ (w-64)  │  ┌─────────────────────────────────────────┐ │
│         │  │ Row 1: ComplianceGauge + MetricsRow      │ │
│  Nav    │  ├─────────────────────────────────────────┤ │
│  Items  │  │ Row 2: ComplianceFlowWidget (full-width) │ │
│         │  ├─────────────────────────────────────────┤ │
│         │  │ Row 3: WebsiteAnalysis + LegalNews       │ │
│         │  ├─────────────────────────────────────────┤ │
│         │  │ Row 4: CookieCompliance + AICompliance   │ │
│         │  └─────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Sidebar Navigation Items
1. Dashboard (Home icon) → `/`
2. Website-Analyse (Globe icon) → `/` (scrollt zu DomainHeroSection)
3. Cookie-Compliance (Cookie icon) → `/cookie-compliance`
4. Barrierefreiheit (Eye icon) → `/accessibility`
5. AI-Compliance (Sparkles icon) → `/ai-compliance`
6. Legal-News (Newspaper icon) → `/` (scrollt zu LegalNews)
7. Dokumente (FileText icon) → `/docs`
8. Agentur (Building icon) → `/agency`
9. --- Divider ---
10. Einstellungen (Settings icon) → `/profile`
11. Abo (CreditCard icon) → `/subscription`

## ComplianceGauge — Spezifikation
- SVG Halbkreis (180°), stroke-dasharray animiert von 0 → score%
- Farbskala: `0-40` = Rot (#ef4444), `41-70` = Gelb (#eab308), `71-85` = Hellgrün (#84cc16), `86-100` = Grün (#22c55e)
- Score-Zahl: groß, bold, zentriert (animierte Counter-Animation)
- Trend-Badge: `▲ +X pts` in Grün oder `▼ -X pts` in Rot
- Subtitle: "Hello, {Name} — Ihr Compliance-Score"
- Rechts: 3 Tab-Buttons (DSGVO / Cookie / Barrierefreiheit) wie DisputeFox's Credit-Bureau-Tabs

## ComplianceFlowWidget — Spezifikation
- Links: "OUTPUT" Block mit Gesamt-Score
- Mitte: 4 animierte Flows (SVG curved paths)
  - DSGVO Score → Flow-Linie → rechts
  - Cookie Compliance → Flow-Linie → rechts
  - Barrierefreiheit → Flow-Linie → rechts
  - Legal Updates → Flow-Linie → rechts
- Rechts: Detail-Cards per Bereich mit Score + Status-LED
- Farblich: aktive Flows = orange (#f97316), inaktive = grau

## CSS-Variablen (globals.css Ergänzungen)
```css
--sidebar-width: 256px;
--sidebar-collapsed-width: 72px;
--topbar-height: 64px;
--gauge-red: #ef4444;
--gauge-yellow: #eab308;
--gauge-light-green: #84cc16;
--gauge-green: #22c55e;
--flow-active: #f97316;
--flow-inactive: #3f3f46;
```

## Implementierungsreihenfolge
1. globals.css — CSS-Grundlage
2. Sidebar.tsx — neue Komponente
3. ComplianceGauge.tsx — neue Komponente
4. ComplianceFlowWidget.tsx — neue Komponente
5. SidebarLayout.tsx — Wrapper
6. DashboardHeader.tsx → TopBar umbauen
7. layout.tsx — SidebarLayout einbinden
8. page.tsx — neues Grid-Layout

## Dateien NICHT ändern
- Alle bestehenden Widgets (WebsiteAnalysis, LegalNews, CookieComplianceWidget)
- AuthContext, ThemeContext
- API-Schichten (lib/api.ts etc.)
- Stores (stores/dashboard.ts)
