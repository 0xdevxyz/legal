# 📋 Technical Debt & TODOs

> Letzte Aktualisierung: November 2025  
> Gefunden: 80 TODO/FIXME Einträge in 26 Dateien

---

## 🔴 KRITISCH - Muss vor Production behoben werden

### 1. Authentifizierung
| Datei | Zeile | Problem |
|-------|-------|---------|
| `legal_ai_routes.py` | 20 | `# TODO: Echte Auth implementieren` - Verwendet Test-User |
| `cookie_compliance_routes.py` | 351 | `# TODO: Get user_id from session/auth` |
| `widget_routes.py` | 462 | `# user_id: int = Depends(get_current_user_id) # TODO: Add auth` |

**Fix:** Auth-Dependency von `auth_service.py` in alle Routes einbinden.

### 2. Stripe Integration
| Datei | Zeile | Problem |
|-------|-------|---------|
| `stripe_routes.py` | 32 | `"pro_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY", "price_XXXXX")` |

**Fix:** Echte Stripe Price-IDs in `.env` setzen oder Fallback entfernen.

---

## 🟠 HOCH - Sollte zeitnah behoben werden

### 3. Datenbank-Integration
| Datei | Zeile | Problem |
|-------|-------|---------|
| `widget_routes.py` | 178 | Analytics nicht in DB gespeichert |
| `widget_routes.py` | 261 | Usage-Count nicht aus DB geladen |
| `widget_routes.py` | 479 | Fixes nicht aus DB geladen |
| `legal_ai_routes.py` | 173 | Feedback nicht für ML-Training gespeichert |
| `public_routes.py` | 1388 | Widget-Analytics nicht gespeichert |

### 4. Admin-Checks fehlen
| Datei | Zeile | Problem |
|-------|-------|---------|
| `ai_legal_routes.py` | 632, 673 | `TODO: Admin-Check einbauen` |
| `legal_change_routes.py` | 364 | `TODO: Admin-Check einbauen` |

---

## 🟡 MITTEL - Funktionalität fehlt

### 5. Feature-Implementierungen
| Datei | Zeile | Feature |
|-------|-------|---------|
| `main_production.py` | 624 | LiveValidator für Fix-Validierung |
| `fix_apply_routes.py` | 348 | Staging-Preview-Feature |
| `fix_apply_routes.py` | 381 | Background-Task-Tracking |
| `expert_service_routes.py` | 271 | Email-Service-Integration |
| `legal_change_routes.py` | 549 | Automatische Fix-Anwendung |
| `widgets/cookie_consent.js` | 214 | Cookie-Settings-Modal |

### 6. Daten-Vervollständigung
| Datei | Zeile | Problem |
|-------|-------|---------|
| `ai_legal_routes.py` | 728-731 | Industry, compliance_areas, services nicht geladen |
| `legal_change_routes.py` | 201-202 | Compliance-Areas nicht aus Config |
| `fix_generator.py` | 703 | Services nicht aus Scan-Ergebnissen |

---

## 🟢 NIEDRIG - Template-Platzhalter (BEABSICHTIGT)

Diese TODOs sind **absichtlich** und für **Benutzer gedacht**:

### AI Act Dokumenten-Generator (`ai_act_doc_generator.py`)
- Zeilen 189-400: `[TODO: ...]` Platzhalter in HTML-Templates
- Diese werden vom Benutzer im generierten Dokument ausgefüllt
- **KEINE Änderung nötig**

### Code-Templates (`ai_fix_engine/handlers/code_handler.py`)
- Zeilen 139, 164, 173, 187: `<!-- TODO: An Ihre Bedürfnisse anpassen -->`
- Template-Kommentare für generierte Fixes
- **KEINE Änderung nötig**

### Prompt-Templates (`compliance_engine/prompts/`)
- Beispiel-Platzhalter wie `[+49 XXX XXXXXXXX]`
- **KEINE Änderung nötig**

---

## 📊 Zusammenfassung

| Priorität | Anzahl | Status |
|-----------|--------|--------|
| 🔴 KRITISCH | 4 | Muss vor Production behoben werden |
| 🟠 HOCH | 9 | Zeitnah beheben |
| 🟡 MITTEL | 11 | Geplante Features |
| 🟢 NIEDRIG | 56 | Beabsichtigte Platzhalter |

---

## ✅ Quick Wins (< 1h)

1. **Auth in Routes einbinden:**
   ```python
   from auth_service import get_current_user
   
   @router.get("/api/...")
   async def endpoint(current_user: dict = Depends(get_current_user)):
       user_id = current_user["user_id"]
   ```

2. **Admin-Check implementieren:**
   ```python
   async def require_admin(current_user: dict = Depends(get_current_user)):
       if not current_user.get("is_superuser"):
           raise HTTPException(status_code=403, detail="Admin access required")
       return current_user
   ```

3. **Stripe Price-IDs:**
   - In Stripe Dashboard die Price-IDs kopieren
   - In `.env` als `STRIPE_PRICE_PRO_MONTHLY=price_xxx` setzen

---

## 🗓️ Empfohlene Reihenfolge

1. **Woche 1:** Kritische Auth-Fixes
2. **Woche 2:** Datenbank-Integration für Analytics
3. **Woche 3:** Admin-Checks & Feature-Implementierungen
4. **Fortlaufend:** Template-Platzhalter können bleiben

