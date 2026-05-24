# 🌱 Green Compliance Module - Technische Spezifikation
## Nachhaltigkeits-Scanner für EFRE-Förderungsfähigkeit

**Version**: 1.0  
**Status**: Konzeptphase  
**Priorität**: KRITISCH für EFRE-Antrag  
**Entwicklungszeit**: 4-6 Wochen  

---

## 🎯 Projektziel

Integration eines **Nachhaltigkeits-Scanners** in Complyo, der KMU hilft, den CO₂-Fußabdruck ihrer Websites zu messen und zu reduzieren. Dieses Feature ist **essentiell** für EFRE-Förderfähigkeit (Klimaschutz-Kriterium).

---

## 📊 Features & Funktionsumfang

### 1. CO₂-Fußabdruck-Analyse ⭐ KERN-FEATURE

**Was wird gemessen:**
- **Data Transfer**: Seitengröße, Anzahl Requests, Medien
- **Server-Energie**: Hosting-Standort, Energiequelle (grün/grau)
- **User-Verhalten**: Seitenaufrufe, Traffic-Volumen
- **Caching**: Browser-Cache, CDN-Nutzung

**Berechnungsformel:**
```
CO₂ (g) = Data Transfer (GB) × Energy per GB (kWh) × Carbon Intensity (g/kWh)

Beispiel:
- Seitengröße: 2,5 MB
- Monatliche Besucher: 10.000
- Durchschnittliche Seitenaufrufe pro Besuch: 3

Total Data = 2,5 MB × 10.000 × 3 = 75 GB/Monat
Energy = 75 GB × 0,81 kWh/GB = 60,75 kWh
CO₂ = 60,75 kWh × 442 g/kWh (EU-Durchschnitt) = 26,8 kg CO₂/Monat
```

**Output für User:**
```json
{
  "co2_per_visit": 0.89,  // Gramm CO₂
  "co2_monthly": 26800,   // Gramm CO₂
  "co2_yearly": 321600,   // Gramm CO₂ = 321,6 kg
  "rating": "D",          // A+ bis F
  "percentile": 65,       // Besser als 35% aller Websites
  "tree_equivalent": 14   // Anzahl Bäume zum Ausgleich
}
```

### 2. Energie-Effizienz-Score 🔋

**Gemessene Faktoren:**

| Faktor | Gewichtung | Messmethode |
|--------|------------|-------------|
| Page Speed Score | 30% | Google Lighthouse |
| Image Optimization | 25% | Dateigröße vs. Display-Größe |
| HTTP Requests | 20% | Anzahl externe Ressourcen |
| Caching Strategy | 15% | Cache-Headers, CDN |
| Code Efficiency | 10% | Minification, Bundling |

**Score-Berechnung:**
```python
efficiency_score = (
    page_speed * 0.30 +
    image_optimization * 0.25 +
    http_efficiency * 0.20 +
    caching_score * 0.15 +
    code_quality * 0.10
) * 100
```

**Rating-System:**
- **A+ (90-100)**: Best in Class - nachhaltige Website
- **A (80-89)**: Sehr gut
- **B (70-79)**: Gut
- **C (60-69)**: Durchschnitt
- **D (50-59)**: Verbesserungsbedarf
- **E (40-49)**: Kritisch
- **F (<40)**: Nicht akzeptabel

### 3. Green Hosting Check ✅

**Prüfung:**
- Server-Standort (Deutschland/EU bevorzugt)
- Energiequelle (100% erneuerbare Energien?)
- Hosting-Anbieter in Green-Web-Foundation-Datenbank
- Zertifikate (ISO 14001, EU Ecolabel, etc.)

**Datenquellen:**
- The Green Web Foundation API
- Hosting-Provider-Datenbank (manuell gepflegt)
- Whois + IP-Geolocation

**Output:**
```json
{
  "is_green": true,
  "provider": "Hetzner",
  "location": "Deutschland (Falkenstein)",
  "renewable_energy": 100,  // Prozent
  "certification": ["ISO 14001"],
  "recommendation": "Excellent! Ihr Hosting nutzt 100% erneuerbare Energien."
}
```

### 4. CSRD-Konformität (Corporate Sustainability Reporting Directive) 📋

**Für größere KMU (ab 250 Mitarbeiter):**

Automatische Überprüfung digitaler Nachhaltigkeits-Pflichten:
- ✅ CO₂-Transparenz der digitalen Assets
- ✅ Energieverbrauch-Dokumentation
- ✅ Nachhaltigkeitsziele (Scope 3 Emissions)

**Report-Export:**
- PDF-Report mit allen Nachhaltigkeits-Metriken
- CSV-Export für eigene CSRD-Berichte
- Integration in bestehende Sustainability-Software (z.B. Plan A, Planetly)

### 5. Automatische Optimierungsvorschläge 🛠️

**Konkrete Empfehlungen mit Impact-Schätzung:**

```json
{
  "recommendations": [
    {
      "title": "Bilder komprimieren",
      "impact": "high",
      "co2_saving_yearly": 45.2,  // kg CO₂
      "implementation": "automatic",  // oder "manual"
      "description": "15 Bilder sind nicht optimiert (WebP-Format nutzen)",
      "auto_fix_available": true
    },
    {
      "title": "Browser-Caching aktivieren",
      "impact": "medium",
      "co2_saving_yearly": 18.7,
      "implementation": "manual",
      "description": "Cache-Headers fehlen für statische Ressourcen"
    }
  ],
  "total_potential_savings": 120.5  // kg CO₂/Jahr
}
```

---

## 🏗️ Technische Architektur

### Backend-Komponenten

```
backend/
├── sustainability/
│   ├── __init__.py
│   ├── green_scanner.py         # Hauptlogik
│   ├── co2_calculator.py        # CO₂-Berechnung
│   ├── efficiency_analyzer.py   # Performance-Analyse
│   ├── hosting_checker.py       # Green-Hosting-Check
│   ├── csrd_compliance.py       # CSRD-Prüfung
│   └── recommendation_engine.py # Auto-Optimierungen
├── routes/
│   └── green_routes.py          # API-Endpunkte
└── database/
    └── green_scans.sql          # DB-Schema
```

### Neue Datenbank-Tabellen

```sql
-- CO₂-Scan-Ergebnisse
CREATE TABLE green_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    website_id UUID REFERENCES websites(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- CO₂-Metriken
    co2_per_visit_grams DECIMAL(10,2),
    co2_monthly_kg DECIMAL(10,2),
    co2_yearly_kg DECIMAL(10,2),
    
    -- Effizienz-Scores
    efficiency_score INT,  -- 0-100
    rating VARCHAR(5),     -- A+ bis F
    percentile INT,        -- 0-100
    
    -- Page-Metriken
    page_size_kb DECIMAL(10,2),
    http_requests INT,
    images_count INT,
    unoptimized_images INT,
    
    -- Hosting
    is_green_hosting BOOLEAN,
    hosting_provider VARCHAR(255),
    server_location VARCHAR(255),
    renewable_energy_percent INT,
    
    -- CSRD
    csrd_compliant BOOLEAN,
    csrd_score INT,
    
    -- Empfehlungen
    recommendations JSONB,
    potential_savings_yearly_kg DECIMAL(10,2),
    
    -- Meta
    scan_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Green-Hosting-Provider-Datenbank
CREATE TABLE green_hosting_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(255) UNIQUE NOT NULL,
    renewable_energy_percent INT DEFAULT 100,
    country VARCHAR(100),
    certifications TEXT[],
    verified BOOLEAN DEFAULT false,
    source VARCHAR(255),  -- z.B. "Green Web Foundation"
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Vorausgefüllte Daten
INSERT INTO green_hosting_providers (provider_name, renewable_energy_percent, country, certifications, verified) VALUES
('Hetzner', 100, 'Deutschland', ARRAY['ISO 14001'], true),
('IONOS', 100, 'Deutschland', ARRAY['EU Ecolabel'], true),
('Mittwald', 100, 'Deutschland', ARRAY['ISO 14001'], true),
('netcup', 100, 'Deutschland', ARRAY[], true),
('all-inkl.com', 100, 'Deutschland', ARRAY[], true);
```

### API-Endpunkte

```python
# GET /api/green/scan/{website_id}
# Startet Green-Scan für eine Website

# GET /api/green/results/{scan_id}
# Abrufen der Scan-Ergebnisse

# GET /api/green/stats/{user_id}
# Aggregierte Nachhaltigkeits-Statistiken

# POST /api/green/optimize/{website_id}
# Auto-Fix für Nachhaltigkeitsprobleme

# GET /api/green/report/{scan_id}/pdf
# PDF-Report herunterladen
```

---

## 🔌 Externe APIs & Dependencies

### 1. The Green Web Foundation API
```bash
# Check if domain uses green hosting
GET https://api.thegreenwebfoundation.org/greencheck/{domain}
```

**Beispiel Response:**
```json
{
  "url": "complyo.tech",
  "hosted_by": "Hetzner Online GmbH",
  "hosted_by_website": "https://www.hetzner.com",
  "partner": null,
  "green": true,
  "hosted_by_id": 128
}
```

### 2. Website Carbon Calculator
```bash
# Alternative: Website Carbon API
GET https://api.websitecarbon.com/site?url=complyo.tech
```

### 3. Google PageSpeed Insights API
```bash
# Performance-Metriken
GET https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={API_KEY}
```

### 4. Own Calculation (primäre Methode)

**Vorteile eigener Berechnung:**
- Keine API-Abhängigkeit
- Anpassbar an deutsche/EU-Standards
- Kostenlos & skalierbar

**Basis-Formel (Sustainable Web Design Model):**
```python
def calculate_co2_per_visit(page_size_bytes):
    """
    Berechnet CO₂-Emission pro Seitenaufruf
    Basierend auf: Sustainable Web Design Model v3
    """
    GB_PER_BYTE = 1 / (1024**3)
    KWH_PER_GB = 0.81  # 2023 global average
    CARBON_INTENSITY_EU = 0.275  # kg CO₂/kWh (EU-Durchschnitt 2024)
    
    # System Boundaries
    DATACENTER_FACTOR = 0.15
    NETWORK_FACTOR = 0.14
    END_USER_DEVICE = 0.52
    PRODUCTION = 0.19  # Herstellung der Infrastruktur
    
    gb_transferred = page_size_bytes * GB_PER_BYTE
    energy_kwh = gb_transferred * KWH_PER_GB
    co2_grams = energy_kwh * CARBON_INTENSITY_EU * 1000
    
    return co2_grams
```

---

## 🎨 Frontend-Integration (Dashboard)

### Neues Dashboard-Tab: "Nachhaltigkeit"

**Wireframe:**
```
┌─────────────────────────────────────────────────────┐
│  🌱 Nachhaltigkeit                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  CO₂-Fußabdruck: 26,8 kg/Monat                     │
│  Rating: ████░░░░ D                                │
│  Besser als 35% aller Websites                     │
│                                                     │
│  ┌──────────────┬──────────────┬──────────────┐   │
│  │ CO₂/Besuch   │ Jahres-CO₂   │ Bäume nötig │   │
│  │ 0,89 g       │ 321 kg       │ 14 Stück    │   │
│  └──────────────┴──────────────┴──────────────┘   │
│                                                     │
│  🔋 Effizienz-Score: 62/100                        │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ ✅ Green Hosting aktiv                       │  │
│  │ Provider: Hetzner (100% erneuerbar)         │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  📋 Optimierungsvorschläge (3)                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ 🔴 HOCH: Bilder komprimieren                │  │
│  │    💾 Spart 45 kg CO₂/Jahr                  │  │
│  │    [Auto-Fix anwenden]                      │  │
│  ├─────────────────────────────────────────────┤  │
│  │ 🟠 MITTEL: Browser-Caching aktivieren       │  │
│  │    💾 Spart 18 kg CO₂/Jahr                  │  │
│  │    [Anleitung anzeigen]                     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  [📥 Nachhaltigkeits-Report herunterladen (PDF)]  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### React-Komponenten (Next.js)

```typescript
// dashboard/components/sustainability/GreenScoreCard.tsx
interface GreenScoreCardProps {
  scanResult: GreenScanResult;
}

export function GreenScoreCard({ scanResult }: GreenScoreCardProps) {
  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h3 className="text-2xl font-bold text-green-600">
        🌱 Nachhaltigkeits-Score
      </h3>
      <div className="mt-4">
        <div className="text-5xl font-bold">{scanResult.rating}</div>
        <p className="text-gray-600">
          Besser als {scanResult.percentile}% aller Websites
        </p>
      </div>
      
      <div className="grid grid-cols-3 gap-4 mt-6">
        <MetricCard 
          title="CO₂/Besuch"
          value={`${scanResult.co2_per_visit} g`}
          icon="🌍"
        />
        <MetricCard 
          title="Jahres-CO₂"
          value={`${scanResult.co2_yearly} kg`}
          icon="📊"
        />
        <MetricCard 
          title="Bäume"
          value={scanResult.tree_equivalent}
          icon="🌳"
        />
      </div>
    </div>
  );
}
```

---

## 📈 EFRE-Relevanz & Argumentation

### Wie dieses Modul die Förderfähigkeit erhöht:

| EFRE-Kriterium | Beitrag durch Green Module | Bewertung |
|----------------|----------------------------|-----------|
| **Klimaschutz** | Direkter CO₂-Reduktionsbeitrag messbar | ⭐⭐⭐⭐⭐ |
| **Digitalisierung** | Digitale Tools für Nachhaltigkeit | ⭐⭐⭐⭐⭐ |
| **Innovation** | Erste Compliance-Plattform mit CO₂-Tracking | ⭐⭐⭐⭐⭐ |
| **KMU-Nutzen** | KMU können CSRD-Pflichten erfüllen | ⭐⭐⭐⭐ |
| **Messbarkeit** | Klare KPIs (kg CO₂ gespart) | ⭐⭐⭐⭐⭐ |

### Formulierung für EFRE-Antrag:

> **"Complyo Green hilft KMU, ihre digitale CO₂-Bilanz zu optimieren und EU-Klimaziele zu erreichen. Durch automatisierte Analyse und Optimierung können Websites bis zu 80% ihres CO₂-Fußabdrucks reduzieren. Messbare Einsparungen: 50 Tonnen CO₂/Jahr bei 500 KMU-Nutzern."**

---

## 🚀 Implementierungs-Roadmap

### Phase 1: MVP (Wochen 1-2)
- [ ] CO₂-Kalkulator entwickeln (eigene Formel)
- [ ] Green Web Foundation API integrieren
- [ ] Basic Dashboard-Ansicht
- [ ] Datenbank-Schema aufsetzen

### Phase 2: Erweiterte Features (Wochen 3-4)
- [ ] Google PageSpeed Integration
- [ ] Optimierungsvorschläge-Engine
- [ ] Auto-Fix für Bilder (Kompression)
- [ ] PDF-Report-Generator

### Phase 3: CSRD & Enterprise (Wochen 5-6)
- [ ] CSRD-Compliance-Checks
- [ ] CSV-Export für Berichte
- [ ] API für externe Tools (Planetly, Plan A)
- [ ] Advanced Analytics (Trends, Vergleiche)

### Phase 4: Marketing & Launch (Woche 7+)
- [ ] Landing Page für Green Module
- [ ] Case Studies mit CO₂-Einsparungen
- [ ] PR: "Erste Compliance-Plattform mit CO₂-Tracking"
- [ ] EFRE-Antrag mit Green Module als Kern-Feature

---

## 💰 Kosten-Kalkulation

### Entwicklungskosten

| Position | Aufwand | Kosten |
|----------|---------|--------|
| Backend-Entwicklung | 120h @ 80€/h | 9.600 € |
| Frontend-Entwicklung | 80h @ 75€/h | 6.000 € |
| API-Integration | 40h @ 80€/h | 3.200 € |
| Testing & QA | 40h @ 65€/h | 2.600 € |
| Projektmanagement | 40h @ 90€/h | 3.600 € |
| **GESAMT** | **320h** | **25.000 €** |

### Laufende Kosten

| Position | Kosten/Monat |
|----------|--------------|
| Google PageSpeed API | 0 € (kostenlos bis 25k Requests) |
| Green Web Foundation | 0 € (Open Data) |
| Server-Ressourcen | 50 € (zusätzlicher Compute) |
| **GESAMT** | **50 €/Monat** |

### ROI für EFRE-Antrag

**Investment**: 25.000 € (einmalig) + 600 €/Jahr (laufend)  
**EFRE-Förderung**: Bis zu 40.000 € (Teil des 310k-Gesamtantrags)  
**Break-Even**: Nach 15-20 zusätzlichen Business-Kunden (à 199€/Monat)

**Marketing-Vorteil**: 
- Alleinstellungsmerkmal im Markt
- ESG-Compliance als Verkaufsargument
- EFRE-Förderung als "Qualitätssiegel"

---

## 📊 Success Metrics (KPIs)

### Nach 6 Monaten:

| Metrik | Ziel | Messmethode |
|--------|------|-------------|
| **Aktive Green-Scans** | 500/Monat | Dashboard-Analytics |
| **Gesamt-CO₂-Einsparung** | 10 Tonnen | Aggregierte Scan-Daten |
| **Auto-Fix-Anwendungen** | 200 | Fix-Tracking |
| **Green-Modul-Nutzer** | 150 KMU | User-Segment-Analyse |
| **CSRD-Reports generiert** | 50 | Report-Downloads |

### Nach 12 Monaten:

| Metrik | Ziel |
|--------|------|
| **Gesamt-CO₂-Einsparung** | 50 Tonnen |
| **Green-Modul-Nutzer** | 500 KMU |
| **Medien-Erwähnungen** | 10 Artikel (Fachpresse) |
| **Auszeichnungen** | 1 (z.B. GreenTech Award) |

---

## 🔗 Weitere Ressourcen

### Wissenschaftliche Grundlagen:
- [Sustainable Web Design Model](https://sustainablewebdesign.org/)
- [Website Carbon Calculator Methodology](https://www.websitecarbon.com/how-does-it-work/)
- [The Green Web Foundation](https://www.thegreenwebfoundation.org/)

### Compliance-Standards:
- [CSRD - EU Directive](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2464)
- [GHG Protocol - Scope 3 Emissions](https://ghgprotocol.org/scope-3-calculation-guidance)

### Best Practices:
- [Google Web Vitals](https://web.dev/vitals/)
- [MDN: Website Performance](https://developer.mozilla.org/en-US/docs/Learn/Performance)

---

**Status**: ✅ Bereit zur Implementierung  
**Nächster Schritt**: Entwickler-Kickoff + EFRE-Antrag-Integration  
**Verantwortlich**: CTO + Sustainability Lead  

---

