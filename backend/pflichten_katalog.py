"""
Pflichten-Katalog (Phase 7.2 „Pflichtenradar") — Rules as Code.

Jede Pflicht ist ein Datensatz mit einer applies()-Logik über das Firmenprofil.
Haftungs-Design (nicht verhandelbar, siehe planning/STRUKTUR_FIXES_LAUNCH_PLAN.md
Phase 7.0):
- Ergebnis ist IMMER "trifft wahrscheinlich zu" / "prüfen" / "wahrscheinlich
  nicht" — nie ein Rechtsurteil (RDG: Selbst-Check, keine Rechtsberatung).
- Jede Aussage trägt confidence + evidence (welche Profil-Antworten sie
  ausgelöst haben) + legal_basis.
- "Trifft nicht zu" wird nur mit Begründung und niedriger härterer Aussage
  ausgegeben ("keine Indizien im Profil"), nie als Garantie.

Profil-Schema (company_profiles.answers, JSONB):
  employees:  '1-9' | '10-49' | '50-249' | '250+'
  revenue:    '<=2m' | '2-10m' | '10-50m' | '>50m'
  b2c:                bool  (Angebot richtet sich an Verbraucher)
  online_shop:        bool  (Verkauf/Vertragsabschluss online)
  digital_service:    bool  (digitale Dienstleistung: Buchung, Konto, App …)
  uses_ai_chat:       bool  (KI-Chatbot/-Assistent im Kundenkontakt)
  uses_ai_decisions:  bool  (KI in Bewerbung/Scoring/Preisen o. ä.)
  ai_generated_content: bool (veröffentlicht KI-generierte Inhalte/Bilder)
  sends_b2b_invoices: bool  (stellt Rechnungen an Unternehmen in DE)
  sells_connected_products: bool (Produkte mit digitalen Elementen/Software)
  critical_sector:    bool  (Energie/Gesundheit/Transport/IT-Dienste/… NIS2-Sektor)
  newsletter:         bool  (E-Mail-Marketing)
  employees_data:     bool  (Beschäftigte, deren Daten verarbeitet werden) — default True
"""
from typing import Any, Callable, Dict, List, Optional

APPLIES = "applies"          # trifft nach Profil-Indizien wahrscheinlich zu
CHECK = "check"              # Indizien unklar/teilweise — selbst prüfen
NOT_INDICATED = "not_indicated"  # keine Indizien im Profil


def _small_company(p: Dict) -> bool:
    """Kleinstunternehmen i. S. d. BFSG: <10 MA und ≤2 Mio. € Umsatz."""
    return p.get("employees") == "1-9" and p.get("revenue") == "<=2m"


def _mid_or_large(p: Dict) -> bool:
    return p.get("employees") in ("50-249", "250+")


Rule = Dict[str, Any]

# Jede Regel: evaluate(profile) -> (status, evidence:list[str], why:str)
PFLICHTEN: List[Rule] = [
    {
        "id": "dsgvo_datenschutzerklaerung",
        "law": "DSGVO / DDG",
        "title": "Datenschutzerklärung auf der Website",
        "legal_basis": "Art. 13/14 DSGVO",
        "deadline": None,
        "risk_range": [500, 20000],
        "todo": "Vollständige, aktuelle Datenschutzerklärung bereitstellen (Complyo-Rechtstext-Generator).",
        "scan_pillar": "gdpr",
        "confidence": 0.95,
        "evaluate": lambda p: (APPLIES, ["Website vorhanden"],
                               "Jede geschäftliche Website, die personenbezogene Daten verarbeitet (schon Server-Logs), braucht eine Datenschutzerklärung."),
    },
    {
        "id": "impressum",
        "law": "DDG (ex TMG)",
        "title": "Impressum (Anbieterkennzeichnung)",
        "legal_basis": "§ 5 DDG",
        "deadline": None,
        "risk_range": [500, 50000],
        "todo": "Impressum mit allen Pflichtangaben verlinken (von jeder Seite erreichbar).",
        "scan_pillar": "legal",
        "confidence": 0.95,
        "evaluate": lambda p: (APPLIES, ["geschäftsmäßige Website"],
                               "Geschäftsmäßige Online-Angebote brauchen ein Impressum."),
    },
    {
        "id": "ttdsg_cookie_consent",
        "law": "TDDDG (ex TTDSG)",
        "title": "Cookie-/Tracking-Einwilligung (Consent-Banner)",
        "legal_basis": "§ 25 TDDDG",
        "deadline": None,
        "risk_range": [1000, 30000],
        "todo": "Consent-Management einsetzen; nicht notwendige Cookies erst nach Einwilligung (Complyo Cookie-Banner).",
        "scan_pillar": "cookies",
        "confidence": 0.9,
        "evaluate": lambda p: (APPLIES, ["Website mit Standard-Technik"],
                               "Sobald nicht zwingend notwendige Cookies/Tracker eingesetzt werden, ist Einwilligung Pflicht. Der Website-Scan zeigt den Ist-Zustand."),
    },
    {
        "id": "bfsg",
        "law": "BFSG",
        "title": "Digitale Barrierefreiheit (Website/Shop)",
        "legal_basis": "§§ 3, 14 BFSG i. V. m. BFSGV",
        "deadline": "2025-06-28 (in Kraft)",
        "risk_range": [5000, 100000],
        "todo": "WCAG-2.1-AA-Konformität herstellen + Erklärung zur Barrierefreiheit veröffentlichen (Complyo A11y-Modul).",
        "scan_pillar": "accessibility",
        "confidence": 0.85,
        "evaluate": lambda p: (
            (NOT_INDICATED, ["kein B2C", "kein Online-Vertragsschluss"],
             "Das BFSG erfasst v. a. Verbraucher-gerichtete E-Commerce-/Dienstleistungsangebote — dafür gibt es im Profil keine Indizien.")
            if not (p.get("b2c") and (p.get("online_shop") or p.get("digital_service")))
            else (CHECK, ["B2C", "Online-Shop/-Dienstleistung", "Kleinstunternehmen"],
                  "Grundsätzlich erfasst; als Kleinstunternehmen (<10 MA, ≤2 Mio. €) sind Dienstleistungen aber ausgenommen (§ 3 Abs. 3 BFSG) — Produktverkauf nicht. Einordnung selbst prüfen.")
            if _small_company(p)
            else (APPLIES, ["B2C", "Online-Shop/-Dienstleistung"],
                  "Verbrauchergerichteter elektronischer Geschäftsverkehr fällt unter das BFSG; die Frist ist abgelaufen.")
        ),
    },
    {
        "id": "ai_act_transparenz",
        "law": "EU AI Act",
        "title": "KI-Transparenz gegenüber Nutzern (Chatbots, KI-Inhalte)",
        "legal_basis": "Art. 50 KI-VO (VO (EU) 2024/1689)",
        "deadline": "2026-08-02 (bußgeldbewehrt)",
        "risk_range": [1000, 15000000],
        "todo": "KI-Interaktion kennzeichnen (Chatbot-Hinweis); KI-generierte Inhalte/Deepfakes kennzeichnen.",
        "scan_pillar": None,
        "confidence": 0.9,
        "evaluate": lambda p: (
            (APPLIES,
             [k for k, v in [("KI-Chatbot", p.get("uses_ai_chat")), ("KI-generierte Inhalte", p.get("ai_generated_content"))] if v],
             "Beim Einsatz von KI im Kundenkontakt bzw. bei veröffentlichten KI-Inhalten gelten die Transparenzpflichten des Art. 50.")
            if (p.get("uses_ai_chat") or p.get("ai_generated_content"))
            else (NOT_INDICATED, ["kein KI-Einsatz angegeben"],
                  "Ohne KI-Systeme mit Nutzerkontakt greifen die Art.-50-Pflichten nicht. Der Website-Scan prüft zusätzlich auf eingebundene KI-Widgets.")
        ),
    },
    {
        "id": "ai_act_hochrisiko",
        "law": "EU AI Act",
        "title": "Hochrisiko-Prüfung beim KI-Einsatz in Personal/Scoring",
        "legal_basis": "Art. 6 i. V. m. Anhang III KI-VO",
        "deadline": "2026-08-02",
        "risk_range": [10000, 15000000],
        "todo": "Einsatzzweck gegen Anhang III prüfen; ggf. Betreiberpflichten (Art. 26): menschliche Aufsicht, Doku, Schulung (Complyo AI-Act-Modul).",
        "scan_pillar": None,
        "confidence": 0.7,
        "evaluate": lambda p: (
            (CHECK, ["KI in Bewerbungs-/Scoring-/Preisentscheidungen"],
             "KI in Beschäftigung/Bewerbung, Kredit-Scoring u. ä. ist regelmäßig Hochrisiko (Anhang III) — ob Ihr konkreter Einsatz erfasst ist, muss einzeln geprüft werden.")
            if p.get("uses_ai_decisions")
            else (NOT_INDICATED, ["kein entscheidender KI-Einsatz angegeben"],
                  "Ohne KI-gestützte Entscheidungen über Personen keine Anhang-III-Indizien.")
        ),
    },
    {
        "id": "e_rechnung",
        "law": "Wachstumschancengesetz",
        "title": "E-Rechnung im B2B (Empfang jetzt, Versand gestaffelt)",
        "legal_basis": "§ 14 UStG n. F.",
        "deadline": "Empfang seit 2025-01-01; Versand ab 2027/2028 (nach Umsatz)",
        "risk_range": [0, 5000],
        "todo": "Empfang strukturierter E-Rechnungen (XRechnung/ZUGFeRD) sicherstellen; Versand-Fahrplan festlegen.",
        "scan_pillar": None,
        "confidence": 0.9,
        "evaluate": lambda p: (
            (APPLIES, ["B2B-Rechnungen in DE"],
             "Inländische B2B-Umsätze: E-Rechnungs-Empfang ist bereits Pflicht, der Versand wird nach Umsatzgröße gestaffelt Pflicht.")
            if p.get("sends_b2b_invoices")
            else (NOT_INDICATED, ["keine B2B-Rechnungen angegeben"],
                  "Ohne inländische B2B-Rechnungen keine E-Rechnungs-Pflicht.")
        ),
    },
    {
        "id": "nis2",
        "law": "NIS2 / NIS2UmsuCG",
        "title": "Cybersicherheits-Pflichten (Risikomanagement, Meldewege)",
        "legal_basis": "NIS2-RL (EU) 2022/2555, dt. Umsetzung",
        "deadline": "Registrierung/Nachweise nach Inkrafttreten der dt. Umsetzung",
        "risk_range": [10000, 7000000],
        "todo": "Betroffenheit klären (Sektor + Größe); Risikomanagement nach Stand der Technik, Melde- und Registrierungspflichten vorbereiten.",
        "scan_pillar": None,
        "confidence": 0.65,
        "evaluate": lambda p: (
            (CHECK, ["NIS2-Sektor", "≥50 MA bzw. ≥10 Mio. € Umsatz erwartet"],
             "Sektorzugehörigkeit + Größenschwelle deuten auf NIS2-Betroffenheit — die Einstufung (wichtig/besonders wichtig) muss einzeln geprüft werden.")
            if (p.get("critical_sector") and (_mid_or_large(p) or p.get("revenue") in ("10-50m", ">50m")))
            else (CHECK, ["NIS2-Sektor", "unter Größenschwelle"],
                  "Sektor erfasst, Größenschwelle nach Profil wohl nicht erreicht — Lieferketten-Anforderungen von Kunden können trotzdem greifen.")
            if p.get("critical_sector")
            else (NOT_INDICATED, ["kein NIS2-Sektor angegeben"],
                  "Ohne Zugehörigkeit zu einem NIS2-Sektor keine direkten Pflichten; als Zulieferer regulierter Kunden können vertragliche Anforderungen kommen.")
        ),
    },
    {
        "id": "cra",
        "law": "Cyber Resilience Act",
        "title": "Produkt-Cybersicherheit für Produkte mit digitalen Elementen",
        "legal_basis": "VO (EU) 2024/2847",
        "deadline": "Meldepflichten ab 2026-09-11; Hauptpflichten ab 2027-12-11",
        "risk_range": [10000, 15000000],
        "todo": "Produktportfolio klassifizieren; Security-by-Design, Schwachstellenmanagement und Update-Prozesse aufsetzen.",
        "scan_pillar": None,
        "confidence": 0.7,
        "evaluate": lambda p: (
            (APPLIES, ["Produkte mit digitalen Elementen"],
             "Hersteller/Inverkehrbringer vernetzter Produkte oder Software fallen unter den CRA — die Fristen laufen bereits.")
            if p.get("sells_connected_products")
            else (NOT_INDICATED, ["keine digitalen Produkte angegeben"],
                  "Ohne Produkte mit digitalen Elementen keine CRA-Herstellerpflichten.")
        ),
    },
    {
        "id": "uwg_newsletter",
        "law": "UWG",
        "title": "Einwilligung für E-Mail-Marketing (Double-Opt-in)",
        "legal_basis": "§ 7 Abs. 2 Nr. 2 UWG, Art. 6 DSGVO",
        "deadline": None,
        "risk_range": [1000, 15000],
        "todo": "Double-Opt-in nachweisbar dokumentieren; Abmeldelink in jeder Mail.",
        "scan_pillar": None,
        "confidence": 0.9,
        "evaluate": lambda p: (
            (APPLIES, ["Newsletter/E-Mail-Marketing"],
             "Werbe-Mails ohne nachweisbare Einwilligung sind abmahnfähig — Double-Opt-in ist der etablierte Nachweisweg.")
            if p.get("newsletter")
            else (NOT_INDICATED, ["kein E-Mail-Marketing angegeben"],
                  "Ohne E-Mail-Marketing keine § 7-UWG-Einwilligungspflicht.")
        ),
    },
    {
        "id": "dsgvo_verzeichnis",
        "law": "DSGVO",
        "title": "Verzeichnis von Verarbeitungstätigkeiten (VVT)",
        "legal_basis": "Art. 30 DSGVO",
        "deadline": None,
        "risk_range": [500, 10000],
        "todo": "VVT anlegen und aktuell halten (auch kleine Unternehmen: Ausnahme greift praktisch fast nie, da regelmäßige Verarbeitung).",
        "scan_pillar": None,
        "confidence": 0.85,
        "evaluate": lambda p: (APPLIES, ["laufende Datenverarbeitung (Kunden/Beschäftigte)"],
                               "Die 250-MA-Ausnahme gilt nicht bei regelmäßiger Verarbeitung — Kunden- und Beschäftigtendaten sind regelmäßig."),
    },
    {
        "id": "dsgvo_dsb",
        "law": "DSGVO / BDSG",
        "title": "Datenschutzbeauftragte:r erforderlich?",
        "legal_basis": "Art. 37 DSGVO, § 38 BDSG",
        "deadline": None,
        "risk_range": [2500, 50000],
        "todo": "Prüfen: i. d. R. ab 20 Personen mit ständiger automatisierter Verarbeitung → DSB benennen und melden.",
        "scan_pillar": None,
        "confidence": 0.75,
        "evaluate": lambda p: (
            (CHECK, ["≥10 Beschäftigte"],
             "Ab 20 Personen mit ständiger Datenverarbeitung ist ein DSB Pflicht — bei Ihrer Größenklasse prüfen, wie viele Beschäftigte regelmäßig personenbezogene Daten verarbeiten.")
            if p.get("employees") in ("10-49", "50-249", "250+")
            else (NOT_INDICATED, ["<10 Beschäftigte"],
                  "Unter 20 verarbeitenden Personen besteht i. d. R. keine Benennungspflicht (Ausnahmen: z. B. umfangreiche sensible Daten).")
        ),
    },
    {
        "id": "widerruf_shop",
        "law": "BGB / EGBGB",
        "title": "Widerrufsbelehrung + Muster-Widerrufsformular im Shop",
        "legal_basis": "§§ 312g, 355 BGB, Art. 246a EGBGB",
        "deadline": None,
        "risk_range": [1000, 15000],
        "todo": "Widerrufsbelehrung, Muster-Formular und Button-Lösung (zahlungspflichtig bestellen) prüfen (Complyo-Rechtstexte).",
        "scan_pillar": "legal",
        "confidence": 0.9,
        "evaluate": lambda p: (
            (APPLIES, ["B2C", "Online-Shop"],
             "Fernabsatzverträge mit Verbrauchern lösen Widerrufsrechte und Informationspflichten aus.")
            if (p.get("b2c") and p.get("online_shop"))
            else (NOT_INDICATED, ["kein B2C-Online-Shop"],
                  "Ohne Verbraucher-Fernabsatz keine Widerrufsbelehrungspflicht.")
        ),
    },
]


def evaluate_pflichten(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Wendet den Katalog auf ein Profil an. Rein deterministisch, keine KI."""
    results: List[Dict[str, Any]] = []
    for rule in PFLICHTEN:
        try:
            status, evidence, why = rule["evaluate"](profile)
        except Exception:
            status, evidence, why = CHECK, ["Auswertung fehlgeschlagen"], \
                "Diese Pflicht konnte nicht automatisch eingeordnet werden — bitte selbst prüfen."
        results.append({
            "id": rule["id"],
            "law": rule["law"],
            "title": rule["title"],
            "legal_basis": rule["legal_basis"],
            "deadline": rule["deadline"],
            "risk_range": rule["risk_range"],
            "todo": rule["todo"],
            "scan_pillar": rule["scan_pillar"],
            "confidence": rule["confidence"],
            "status": status,
            "evidence": evidence,
            "why": why,
        })
    order = {APPLIES: 0, CHECK: 1, NOT_INDICATED: 2}
    results.sort(key=lambda r: (order[r["status"]], -r["risk_range"][1]))
    return {
        "items": results,
        "counts": {
            "applies": sum(1 for r in results if r["status"] == APPLIES),
            "check": sum(1 for r in results if r["status"] == CHECK),
            "not_indicated": sum(1 for r in results if r["status"] == NOT_INDICATED),
        },
        "disclaimer": (
            "Automatisierter Selbst-Check auf Basis Ihrer Profilangaben — "
            "Information, keine Rechtsberatung. Jede Einordnung nennt die "
            "Angaben, auf denen sie beruht (evidence), und eine Konfidenz. "
            "Für verbindliche Prüfung: Anwalt/Anwältin hinzuziehen."
        ),
    }
