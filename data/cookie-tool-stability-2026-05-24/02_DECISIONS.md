# TASK-2/03-05: Decisions (ADR-Style)

## ADR-001: tcf_vendors – Migration + GVL-Seed statt Mock-Daten

**Status:** Accepted  
**Problem:** Tabelle fehlte komplett → 500 bei jedem TCF-Request  
**Optionen:**
1. Mock-Daten hardcoden (schnell, aber nicht wartbar)
2. Echte IAB GVL v3 laden und täglich aktualisieren ✅

**Entscheidung:** Option 2 – IAB GVL v3 von `vendor-list.consensu.org`. Täglich 03:00 Uhr via Cron. Seed im Initial-Run: 1169 Vendors.

---

## ADR-002: Policy-Endpoint – LATERAL JOIN statt ANY(array)

**Status:** Accepted  
**Problem:** `services`-Spalte ist JSONB (kein TEXT[]-Array), daher `ANY(c.services)` Typ-Fehler.  
**Fix:** `LEFT JOIN LATERAL jsonb_array_elements_text(c.services) AS svc_key ON true` + `JOIN cookie_services s ON s.service_key = svc_key`.  
**Fallback:** Wenn Site nicht konfiguriert → Minimal-Policy zurückgeben (kein 404/500).

---

## ADR-003: Stats-Endpoint – SQL-Injection schließen + days clampen

**Status:** Accepted  
**Problem:** `days` wurde per `% days` in den SQL-String interpoliert → SQL-Injection möglich.  
**Fix:** Parametrisierter Query `($2 * INTERVAL '1 day')` + Input-Clamping `days = max(1, min(days, 365))`.

---

## ADR-004: Stats 404 – Root-Cause

**Status:** Accepted  
**Befund:** Frontend (`ConsentStatistics.tsx`) verwendet korrekt `/api/cookie-compliance/stats/${siteId}`. Die 404 im Docker-Log (`/cookie-compliance/stats/...`) kommt von einem alten Widget-Request ohne `/api/`-Präfix – vermutlich `cookie_banner_v2.js` im iframe-Kontext.  
**Maßnahme:** Backend-Fix (SQL-Injection) bereits erledigt. Widget-Request-Fix als TODO für Phase 2 notiert (minor – kein echtes Dashboard-Problem).

---

## ADR-005: UX – Empty-States Live statt "--"

**Status:** Accepted  
**Problem:** Quick-Stat-Karten zeigten "--" ohne Kontext → wirkte wie kaputt.  
**Fix:** Seperate `loadQuickStats(siteId)`-Funktion lädt `stats?days=30` nach Config-Load. Bei `null`-Response: "Noch keine Daten"-Hinweis + "Banner einbinden →"-Button zur Integration-Tab.
