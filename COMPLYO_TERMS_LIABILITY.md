# Complyo – Nutzungsbedingungen & Haftungsausschluss
## Rechtliche Rahmenbedingungen für KI-generierte Compliance-Fixes

**Stand:** 23. November 2025  
**Gültig ab:** Sofort  
**Anwendungsbereich:** Alle Nutzer der Complyo-Plattform

---

## § 1 Präambel – Das Complyo-Prinzip

Complyo ist ein **Patch-basiertes Compliance-Tool**, keine automatisierte Code-Überarbeitungs-Software.

**Unser Ansatz:**
- ✅ Wir **scannen** Ihre öffentlich zugängliche Website
- ✅ Wir **analysieren** Compliance-Lücken (DSGVO, WCAG, TTDSG, TMG)
- ✅ Wir **generieren** konkrete Code-Patches als Vorschläge
- ❌ Wir schreiben **NIEMALS** automatisch in Ihre Live-Systeme

**Der entscheidende Unterschied zu „Overlay-Tools":**
Wir erstellen echte Code-Fixes – aber **mit menschlicher Abnahme** als rechtlicher Sicherung.

---

## § 2 Haftung für KI-generierte Code-Fixes

### 2.1 Verantwortlichkeit

**Complyo wendet Code-Änderungen ausschließlich nach ausdrücklicher Bestätigung durch den Nutzer oder dessen technische Administratoren an.**

Die Verantwortung für das Ausrollen der Änderungen in produktive Systeme liegt **ausschließlich beim Nutzer**.

### 2.2 Generierungsprozess

**Complyo generiert Patches basierend auf öffentlich zugänglichem Code. Sie übernehmen die Verantwortung für die Anwendung dieser Änderungen in Ihrem System.**

Unsere KI analysiert:
- HTML-Struktur Ihrer Website
- CSS-Styles und Kontraste
- JavaScript-Implementierungen
- Cookies und Tracking-Skripte

Daraus erstellt sie:
- Code-Snippets (HTML/CSS/JS)
- Textvorlagen (Datenschutzerklärung, Impressum)
- Step-by-Step-Anleitungen

### 2.3 Keine Garantie für Fehlerfreiheit

**WICHTIG:** KI-generierte Inhalte können Fehler, Ungenauigkeiten oder nicht optimale Lösungen enthalten.

Complyo übernimmt **keine Haftung** für:
- Fehlerhafte Code-Snippets
- Unvollständige Rechtstexte
- Kompatibilitätsprobleme mit Ihrer Technologie
- Datenverlust durch fehlerhafte Anwendung
- Umsatzausfälle durch Website-Downtime

**Sie sind verpflichtet:**
- ✅ Jeden Fix vor Anwendung zu prüfen
- ✅ Backups zu erstellen
- ✅ In Testumgebungen zu testen (empfohlen)
- ✅ Bei rechtlichen Fragen einen Anwalt zu konsultieren

---

## § 3 Keine automatischen Code-Änderungen

### 3.1 Explizite Bestätigung erforderlich

**Jede Code-Anwendung erfordert Ihre explizite Zustimmung.**

Ablauf:
1. Sie klicken auf „Fix generieren"
2. Complyo erstellt einen Patch
3. Sie sehen eine **Diff-Ansicht** (Vorher/Nachher)
4. Sie entscheiden: Kopieren, Downloaden, oder Deployen
5. **Erst nach Ihrer Bestätigung** wird etwas angewendet

### 3.2 Keine Direktverbindung zu Live-Systemen (außer Premium)

**Standard-Plan (AI / Expert):**
- Fixes werden als ZIP, Code-Snippet oder Pull Request bereitgestellt
- **Sie** deployen manuell via FTP, Git, CMS, etc.
- Complyo hat **keinen** Zugriff auf Ihre Server

**Premium-Plan (Managed / 3.000€/Mo):**
- Optional: SFTP/SSH-Integration
- Staging-Preview mit Screenshot-Diff
- Live-Deployment **nur nach expliziter Freigabe**
- Mit Rollback-Funktion und Backups

### 3.3 Audit Trail

Jede Ihrer Aktionen wird protokolliert:
- Welcher Fix wurde wann heruntergeladen?
- Welcher Fix wurde wann angewendet?
- Von welcher IP-Adresse?
- Mit welchem Benutzer?

**Zweck:** Rechtliche Nachweisbarkeit, dass Änderungen bewusst und gewollt waren.

---

## § 4 Rechtssichere Texte – Disclaimer

### 4.1 eRecht24-Integration (Priorität)

Für **Impressum** und **Datenschutzerklärung** nutzen wir primär die **eRecht24 API** (falls verbunden).

**Garantie:**
- ✅ Abmahnsichere Rechtstexte von Rechtsanwälten
- ✅ Automatische Updates bei Gesetzesänderungen
- ✅ eRecht24 haftet für Richtigkeit

**Empfehlung:** Schließen Sie eine eRecht24-Mitgliedschaft ab (ab 14,90€/Monat).

### 4.2 KI-generierte Rechtstexte (Fallback)

Falls **keine** eRecht24-Integration besteht, generiert unsere KI Textvorlagen.

**WICHTIG:** Diese sind **NICHT** abmahnsicher!

**Haftungsausschluss:**
- ❌ Complyo übernimmt keine Haftung für KI-generierte Rechtstexte
- ✅ Sie **müssen** diese von einem Anwalt prüfen lassen
- ✅ Wir kennzeichnen KI-Texte deutlich: „⚠️ Bitte rechtlich prüfen lassen!"

---

## § 5 Rollback & Backup

### 5.1 Backup-Pflicht

**Vor jeder Code-Anwendung:**
- Complyo erstellt automatisch ein Backup (bei SSH/SFTP-Deployment)
- Bei manuellem Deployment: **Sie** sind für Backups verantwortlich

### 5.2 Rollback-Funktion

**Premium-Plan:**
- Jede Änderung wird versioniert
- "Zurück zur vorherigen Version"-Button im Dashboard
- Backup-Download jederzeit möglich

**Standard-Plan:**
- Backups werden lokal gespeichert
- Sie müssen manuell wiederherstellen

### 5.3 Aufbewahrungsfrist

Backups werden **30 Tage** gespeichert, danach automatisch gelöscht.

---

## § 6 Datenschutz

### 6.1 Welche Daten sammelt Complyo?

**Beim Website-Scan:**
- HTML-Quellcode (öffentlich zugänglich)
- CSS/JS-Dateien (öffentlich zugänglich)
- Screenshots (für Analyse)
- Keine personenbezogenen Daten Ihrer Besucher!

**Vom Nutzer:**
- E-Mail-Adresse
- Firmenname
- Zahlungsdaten (verschlüsselt via Stripe)
- Audit-Logs (IP, Zeitstempel, Aktionen)

### 6.2 DSGVO-Konformität

- Alle Daten werden in der EU gehostet (Hetzner, Deutschland)
- Keine Weitergabe an Dritte (außer Zahlungsdienstleister)
- Löschung auf Anfrage binnen 30 Tagen
- AVV (Auftragsverarbeitungsvertrag) auf Anfrage

---

## § 7 Gewährleistungsausschluss

### 7.1 Keine Compliance-Garantie

**Complyo garantiert NICHT, dass Ihre Website nach Anwendung aller Fixes 100% compliant ist.**

Gründe:
- Gesetze ändern sich ständig
- Individuelle Geschäftsmodelle erfordern individuelle Rechtsberatung
- Technische Limitierungen bei komplexen Websites

### 7.2 Empfehlung

**Für vollständige Rechtssicherheit:**
- ✅ Nutzen Sie Complyo als Basis
- ✅ Lassen Sie kritische Punkte von einem Anwalt prüfen
- ✅ Nutzen Sie eRecht24 für Rechtstexte
- ✅ Beauftragen Sie eine Datenschutzberatung (bei DSGVO-kritischen Projekten)

---

## § 8 Haftungsbegrenzung

### 8.1 Haftung auf Vorsatz und grobe Fahrlässigkeit begrenzt

Complyo haftet **nur** bei:
- Vorsätzlicher Schädigung
- Grob fahrlässigem Verhalten

**Ausgeschlossen:**
- Leichte Fahrlässigkeit
- Folgeschäden (Umsatzausfälle, Abmahnungen, etc.)
- Schäden durch fehlerhafte Anwendung der Patches

### 8.2 Maximalbetrag

Die Haftung ist begrenzt auf die **im letzten Jahr gezahlte Abo-Gebühr**, maximal **5.000 €**.

### 8.3 Ausnahmen

Keine Haftungsbegrenzung bei:
- Personenschäden
- Arglistig verschwiegenen Mängeln
- Produkthaftungsgesetz

---

## § 9 Widerrufsrecht & Erste Fix-Generierung

### 9.1 Widerrufsrecht (14 Tage)

Als Verbraucher haben Sie ein **14-tägiges Widerrufsrecht** ab Vertragsschluss.

**ABER:**

### 9.2 Erlöschen des Widerrufsrechts

**Mit der Generierung des ersten KI-Fixes erlischt Ihr Widerrufsrecht.**

Grund (§ 356 Abs. 5 BGB):
- Digitale Inhalte, die individuell für Sie erstellt werden
- KI-Kosten entstehen uns bereits bei der Generierung
- Sie erhalten sofort nutzbaren Content

**Vor dem ersten Fix:** Deutlicher Hinweis im UI mit Checkbox:
> ⚠️ „Mit dem Start der Fix-Generierung verfällt Ihr 14-tägiges Rückgaberecht. Dies gilt nur für den ersten generierten Fix."

---

## § 10 Preise & Abrechnung

### 10.1 Preismodelle

**AI Plan (149 €/Monat):**
- 10 Fix-Generierungen pro Stunde
- Code-Snippets + Anleitungen
- Community-Support

**Expert Plan (499 €/Monat):**
- Unbegrenzte Fix-Generierungen
- Vollständige Dokumente
- Priority E-Mail-Support
- Audit-Trail

**Managed Plan (3.000 €/Monat):**
- SFTP/SSH-Integration
- Staging-Preview
- Live-Deployment mit Rollback
- Dedicated Account Manager

### 10.2 Abrechnung

- Monatlich per Lastschrift/Kreditkarte (Stripe)
- Keine automatische Verlängerung (kann deaktiviert werden)
- Kündigung jederzeit zum Monatsende

---

## § 11 Änderungen dieser Bedingungen

Complyo behält sich vor, diese Bedingungen mit einer **Ankündigungsfrist von 30 Tagen** zu ändern.

Sie werden per E-Mail informiert. Widersprechen Sie nicht, gelten die neuen Bedingungen als akzeptiert.

---

## § 12 Schlussbestimmungen

### 12.1 Anwendbares Recht

Es gilt **deutsches Recht** unter Ausschluss des UN-Kaufrechts.

### 12.2 Gerichtsstand

Gerichtsstand für Streitigkeiten ist **[Ihr Firmensitz]**.

### 12.3 Salvatorische Klausel

Sollten einzelne Bestimmungen unwirksam sein, bleibt die Gültigkeit der übrigen Bestimmungen unberührt.

---

## § 13 Kontakt

**Complyo GmbH**  
[Ihre Adresse]  
E-Mail: legal@complyo.tech  
Telefon: [Ihre Nummer]

**Support:**  
E-Mail: support@complyo.tech  
Live-Chat: dashboard.complyo.tech

---

## Zusammenfassung – Das Wichtigste in Kürze

✅ **Complyo erstellt Patches, aber SIE entscheiden über die Anwendung**  
✅ **Explizite Bestätigung vor jeder Code-Änderung erforderlich**  
✅ **Keine automatischen Schreibzugriffe auf Ihre Server (außer Premium mit Ihrer Freigabe)**  
✅ **KI-Fixes können Fehler enthalten – Prüfung durch Sie erforderlich**  
✅ **Rechtstexte: eRecht24 (abmahnsicher) > KI (nur Vorlage, nicht abmahnsicher)**  
✅ **Audit Trail dokumentiert alle Ihre Aktionen**  
✅ **Backup & Rollback bei Premium-Plan verfügbar**  
✅ **Haftung auf Abo-Gebühr begrenzt (max. 5.000 €)**  
✅ **Widerrufsrecht erlischt mit dem ersten generierten Fix**

---

**Durch die Nutzung von Complyo erklären Sie sich mit diesen Bedingungen einverstanden.**

*Letzte Aktualisierung: 23. November 2025*


