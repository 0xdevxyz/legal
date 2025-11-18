# 🎨 Complyo Modern Landing Page

Eine hochprofessionelle, conversion-optimierte Landing Page für Complyo.

## ✨ Features

### Design
- **Moderne Gradienten**: Blau/Lila/Rosa Farbverläufe
- **Glassmorphism**: Frosted-Glass-Effekte für moderne UI
- **Smooth Animations**: Framer Motion für flüssige Übergänge
- **Responsive Design**: Optimiert für alle Bildschirmgrößen
- **Accessibility**: WCAG 2.1 AA konform

### Sektionen

1. **ModernHero**
   - Animierte Gradienten-Hintergründe
   - Accessibility Widget Vorschau
   - Dual-CTA Buttons
   - Trust Badge mit Sparkles

2. **TrustBanner**
   - Kundenlogos
   - Social Proof

3. **FeaturesShowcase**
   - 12 Hauptfeatures mit Icons
   - Hover-Animationen
   - Gradient-Cards

4. **ComplianceSection**
   - WCAG 2.1, ADA, EN 301-549, Section 508
   - Privacy by Design Statement
   - ISO 27001 Badge

5. **IntegrationsSection**
   - 6+ Issue-Tracking-Integrationen
   - GitHub, Jira, Trello, Asana, Notion, Slack
   - Dunkler Hintergrund mit Pattern

6. **PricingModern**
   - 3 Preisstufen (100/500/1.500 Seiten)
   - UserWay-ähnliches Design
   - Empfohlen-Badge
   - Gradient-Cards

7. **TestimonialsModern**
   - Slider mit 3 Testimonials
   - Trust Badges (G2, Trustpilot, Capterra, TrustRadius)
   - Navigation mit Dots

8. **CTAModern**
   - Finale Conversion-Sektion
   - Animierte Hintergrund-Blobs
   - Dual-CTA mit Trust Line

9. **FooterModern**
   - 4 Link-Spalten (Produkte, Lösungen, Compliance, Unternehmen)
   - Social Media Links
   - Kontaktinformationen
   - W3C Badge

## 🚀 Verwendung

### URL-Zugriff

Die neue Landing Page ist über den URL-Parameter erreichbar:

```
http://localhost:3003/?variant=modern
```

**Produktions-URL:**
```
https://complyo.tech/?variant=modern
```

### Andere Varianten

- `/?variant=professional` - Professional Landing (Eye-Able-Stil)
- `/?variant=original` - Original Complyo Landing
- `/?variant=high-conversion` - High-Conversion Landing
- `/` - Gewichteter A/B-Test (67% Professional, 17% Original, 16% High-Conversion)

## 🎯 Komponenten-Struktur

```
src/components/
├── ComplyoModernLanding.tsx         # Haupt-Landing-Page
└── modern-landing/
    ├── ModernHero.tsx               # Hero-Sektion
    ├── TrustBanner.tsx              # Trust-Banner
    ├── FeaturesShowcase.tsx         # Features-Grid
    ├── ComplianceSection.tsx        # Compliance Standards
    ├── IntegrationsSection.tsx      # Integrationen
    ├── PricingModern.tsx            # Pricing-Tabelle
    ├── TestimonialsModern.tsx       # Testimonials-Slider
    ├── CTAModern.tsx                # CTA-Sektion
    └── FooterModern.tsx             # Footer
```

## 🎨 Design-Tokens

### Farben

- **Primary Blue**: `from-blue-600 to-purple-600`
- **Secondary Purple**: `from-purple-500 to-pink-500`
- **Accent**: `from-cyan-500 to-blue-500`
- **Success**: `from-green-500 to-emerald-500`
- **Warning**: `from-yellow-400 to-orange-400`

### Animationen

```typescript
// Blob Animation
animate={{
  scale: [1, 1.2, 1],
  rotate: [0, 90, 0],
}}
transition={{
  duration: 20,
  repeat: Infinity,
  ease: "easeInOut"
}}

// Fade In
initial={{ opacity: 0, y: 20 }}
whileInView={{ opacity: 1, y: 0 }}
viewport={{ once: true }}

// Hover Scale
whileHover={{ scale: 1.05, y: -5 }}
```

## 📱 Responsive Breakpoints

- **Mobile**: `< 768px`
- **Tablet**: `768px - 1024px`
- **Desktop**: `> 1024px`

Alle Komponenten nutzen Tailwind CSS Breakpoints:
- `sm:` - 640px
- `md:` - 768px
- `lg:` - 1024px
- `xl:` - 1280px

## 🔧 Anpassungen

### CTAs anpassen

Die CTA-Links können in den jeweiligen Komponenten angepasst werden:

```typescript
// ModernHero.tsx, CTAModern.tsx
href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
```

### Preise ändern

In `PricingModern.tsx` das `plans` Array bearbeiten:

```typescript
const plans = [
  {
    name: '100 Seiten',
    price: '990',
    // ...
  },
  // ...
];
```

### Testimonials aktualisieren

In `TestimonialsModern.tsx` das `testimonials` Array bearbeiten:

```typescript
const testimonials = [
  {
    name: 'Russell M.',
    text: '...',
    // ...
  },
  // ...
];
```

## 🎯 Performance

- **Framer Motion**: Tree-shaking für optimale Bundle-Size
- **Lazy Loading**: Komponenten werden beim Scrollen geladen
- **Optimierte Assets**: SVG-Icons via Lucide React
- **Responsive Images**: Next.js Image-Komponente für Optimierung

## 📊 A/B Testing

Die Landing Page ist vollständig in das A/B-Testing-System integriert:

1. Variante wird automatisch getrackt
2. Session-ID wird gespeichert
3. Analytics-Events werden gefeuert

## 🚀 Deployment

Die Landing Page ist sofort produktionsbereit:

```bash
# Development
npm run dev

# Production Build
npm run build
npm start
```

## 📝 Weitere Informationen

- **Tailwind Config**: `/tailwind.config.ts`
- **Global Styles**: `/src/app/globals.css`
- **Type Definitions**: `/src/types/`

---

**Erstellt**: 2025-11-15  
**Version**: 1.0.0  
**Design**: Modern, conversion-optimiert
**Framework**: Next.js 14 + TypeScript + Tailwind CSS + Framer Motion

