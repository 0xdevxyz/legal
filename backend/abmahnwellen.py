"""
Abmahn-Radar: bekannte, laufende Abmahn- und Bußgeldwellen im deutschen
Website-Recht, verknüpft mit dem eigenen Messbefund.

Warum eine eigene, kuratierte Liste statt des Rechts-Monitorings: Der
Änderungs-Feed (pflichten_events.py) sagt „zu Ihren Pflichten gibt es diese
Meldungen“. Er sagt nicht, ob die eigene Website das hat, worum es in der
Welle geht. Genau diese Brücke schlägt dieses Modul: jede Welle trägt die
Pflicht aus dem Katalog (rule_id), die Scan-Säule (scan_pillar) und
Stichwörter, mit denen das Dashboard die Befunde des aktuellen Scans
zuordnet.

Ehrlichkeit vor Dramatik:
- `art` unterscheidet, wer fordert: „abmahnung“ (Mitbewerber, Verband,
  Betroffener über Anwalt) oder „bussgeld“ (Aufsichtsbehörde). Beides
  zusammen ist möglich und steht dann als „abmahnung_und_bussgeld“.
- `typische_forderung_euro` nennt nur Spannen, die sich begründen lassen
  (Gerichtsentscheidung, Anwaltsgebühr nach RVG, Verbandspauschale).
  Wo es keine belastbare Praxis gibt, steht null und die Begründung sagt
  warum. Bußgeldrahmen aus dem Gesetz sind KEINE typische Forderung und
  stehen nur in der Beschreibung.
- Seit dem Gesetz zur Stärkung des fairen Wettbewerbs (02.12.2020) können
  Mitbewerber bei Verstößen gegen Informations- und Kennzeichnungspflichten
  im Internet sowie bei DSGVO-Verstößen von Unternehmen unter 250
  Beschäftigten KEINEN Ersatz der Abmahnkosten verlangen (§ 13 Abs. 4 UWG).
  Verbände können es weiterhin, und der Unterlassungsanspruch bleibt. Diese
  Einschränkung muss der Nutzer kennen, sonst schätzt er das Risiko falsch.
- `quelle_url` nur, wenn die Adresse allgemein bekannt und stabil ist
  (gesetze-im-internet.de, eur-lex.europa.eu, datenschutzkonferenz-de.de).
  Aktenzeichen stehen im Text; erfundene Links gibt es nicht.

Anwaltskosten nach RVG (Anlage 2, Stand 2021, 1,3 Geschäftsgebühr plus
20 € Auslagenpauschale, netto), als Anker für die Spannen:
  Gegenstandswert  3.000 €  ->  ~310 €
  Gegenstandswert 10.000 €  ->  ~820 €
  Gegenstandswert 20.000 €  ->  ~1.020 €
  Gegenstandswert 30.000 €  ->  ~1.260 €
"""
from typing import Any, Dict, List, Optional

from pflichten_katalog import APPLIES, CHECK, NOT_INDICATED

# Betroffenheit je Welle (siehe betroffenheit_bestimmen)
WAHRSCHEINLICH = "wahrscheinlich"
PRUEFEN = "pruefen"
UNWAHRSCHEINLICH = "unwahrscheinlich"
UNBEKANNT = "unbekannt"

# Ab diesem Säulenwert gilt die Säule als unauffällig (gleiche Schwelle wie
# die Ist-Zustand-Anzeige im Pflichten-Report: >= 80 grün).
SAEULE_UNAUFFAELLIG_AB = 80

ART_ABMAHNUNG = "abmahnung"
ART_BUSSGELD = "bussgeld"
ART_BEIDES = "abmahnung_und_bussgeld"

Welle = Dict[str, Any]

ABMAHNWELLEN: List[Welle] = [
    {
        "id": "google_fonts",
        "titel": "Google Fonts von Google-Servern geladen",
        "beschreibung": (
            "Das LG München I hat am 20.01.2022 (Az. 3 O 17493/20) einem Besucher "
            "100 € Schadensersatz zugesprochen, weil seine IP-Adresse beim Laden "
            "von Google Fonts ohne Einwilligung an Google übertragen wurde. Darauf "
            "folgte 2022 eine Welle mit zehntausenden gleichlautenden Schreiben, "
            "die meist 170 € forderten; gegen die Absender ermittelte später die "
            "Staatsanwaltschaft. Die Rechtsfrage selbst ist damit nicht erledigt: "
            "extern geladene Schriften bleiben ein Datenabfluss, der ohne "
            "Einwilligung nicht gedeckt ist."
        ),
        "rule_id": "dsgvo_datenschutzerklaerung",
        "scan_pillar": "gdpr",
        "stichwoerter": ["google fonts", "fonts.googleapis", "fonts.gstatic", "externe schrift"],
        "art": ART_ABMAHNUNG,
        "wer_fordert": "Betroffene (Besucher) über Anwälte; Schadensersatz nach Art. 82 DSGVO",
        "typische_forderung_euro": [100, 170],
        "forderung_quelle": (
            "100 € Schadensersatz laut LG München I (3 O 17493/20); die "
            "Serienschreiben 2022 forderten 170 € je Website."
        ),
        "seit": "2022-01",
        "quelle_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    },
    {
        "id": "cookie_banner_ablehnen",
        "titel": "Cookie-Banner ohne gleichwertiges Ablehnen",
        "beschreibung": (
            "Banner, die nur „Alle akzeptieren“ anbieten oder das Ablehnen hinter "
            "Einstellungen verstecken, holen nach Auffassung der Datenschutz-"
            "aufsichtsbehörden (DSK-Orientierungshilfe Telemedien) keine wirksame "
            "Einwilligung nach § 25 TDDDG ein. Die Aufsichtsbehörden prüfen das "
            "seit 2022 in koordinierten Aktionen und verhängen Bußgelder; "
            "daneben mahnen Verbraucherverbände und Mitbewerber solche Banner ab. "
            "Der Scan prüft, ob ein Ablehnen-Knopf vorhanden und gleichwertig ist."
        ),
        "rule_id": "ttdsg_cookie_consent",
        "scan_pillar": "cookies",
        "stichwoerter": [
            "ablehnen", "cookie-banner", "cookie-consent", "consent-banner",
            "einwilligung", "consent", "dark pattern", "vorangekreuzt",
        ],
        "art": ART_BEIDES,
        "wer_fordert": "Datenschutzaufsicht (Bußgeld); Verbraucherverbände und Mitbewerber (Abmahnung)",
        "typische_forderung_euro": [300, 1300],
        "forderung_quelle": (
            "Verbandspauschale ab ca. 300 € bzw. Anwaltskosten nach RVG bei "
            "Gegenstandswerten von 10.000 bis 30.000 € (ca. 820 bis 1.260 € netto). "
            "Bußgelder der Aufsicht kommen unabhängig davon hinzu und sind nicht "
            "als typischer Wert belegbar."
        ),
        "seit": "2022-03",
        "quelle_url": "https://www.datenschutzkonferenz-de.de/",
    },
    {
        "id": "tracking_vor_einwilligung",
        "titel": "Tracking-Dienste laden vor der Einwilligung",
        "beschreibung": (
            "Google Analytics, Meta Pixel und ähnliche Dienste dürfen erst nach "
            "der Einwilligung laden (§ 25 TDDDG, Art. 6 DSGVO). Läuft das Skript "
            "schon beim Seitenaufruf, ist der Banner wirkungslos, egal wie er "
            "gestaltet ist. Das ist der häufigste technische Befund hinter "
            "Cookie-Bußgeldern und Abmahnungen, weil er sich im Browser in "
            "Sekunden nachweisen lässt."
        ),
        "rule_id": "ttdsg_cookie_consent",
        "scan_pillar": "cookies",
        "stichwoerter": [
            "vor consent", "vor einwilligung", "ohne einwilligung", "google analytics",
            "meta pixel", "facebook pixel", "tracking", "social-media-inhalte ohne consent",
        ],
        "art": ART_BEIDES,
        "wer_fordert": "Datenschutzaufsicht (Bußgeld); Mitbewerber und Verbände (Abmahnung)",
        "typische_forderung_euro": [300, 1300],
        "forderung_quelle": (
            "Wie beim Cookie-Banner: Verbandspauschale bzw. RVG-Gebühr bei "
            "Gegenstandswerten von 10.000 bis 30.000 €."
        ),
        "seit": "2020-05",
        "quelle_url": "https://www.datenschutzkonferenz-de.de/",
    },
    {
        "id": "drittanbieter_einbindungen",
        "titel": "YouTube, Google Maps, reCAPTCHA ohne Einwilligung eingebunden",
        "beschreibung": (
            "Eingebettete Videos, Karten und Captchas übertragen wie Google Fonts "
            "die IP-Adresse des Besuchers an den Anbieter, bevor er etwas "
            "angeklickt hat. Seit dem Google-Fonts-Urteil werden solche "
            "Einbindungen mit derselben Begründung angegriffen; eine gefestigte "
            "Praxis mit belegbaren Beträgen gibt es dafür noch nicht. "
            "Zwei-Klick-Lösungen oder das Laden erst nach Einwilligung schließen "
            "die Lücke."
        ),
        "rule_id": "dsgvo_datenschutzerklaerung",
        "scan_pillar": "gdpr",
        "stichwoerter": [
            "youtube", "google maps", "recaptcha", "drittanbieter", "extern eingebunden",
            "extern geladen", "externe ressource",
        ],
        "art": ART_ABMAHNUNG,
        "wer_fordert": "Betroffene über Anwälte (Schadensersatz), vereinzelt Mitbewerber",
        "typische_forderung_euro": None,
        "forderung_quelle": (
            "Keine belastbare Spanne: die Schreiben orientieren sich an den "
            "Google-Fonts-Beträgen, gerichtlich bestätigt ist das für diese "
            "Dienste nicht."
        ),
        "seit": "2022-06",
        "quelle_url": None,
    },
    {
        "id": "datenschutzerklaerung",
        "titel": "Datenschutzerklärung fehlt oder ist unvollständig",
        "beschreibung": (
            "Art. 13 DSGVO verlangt eine Datenschutzerklärung, die jede "
            "eingesetzte Technik nennt: Hosting, Analyse, Formulare, Newsletter. "
            "Der EuGH (C-21/23, 04.10.2024) und der BGH (I ZR 223/19, 27.03.2025) "
            "haben bestätigt, dass Mitbewerber DSGVO-Verstöße über das UWG "
            "abmahnen dürfen. Für Unternehmen unter 250 Beschäftigten können "
            "Mitbewerber die Abmahnkosten allerdings nicht ersetzt verlangen "
            "(§ 13 Abs. 4 Nr. 2 UWG); Verbände können es, und die Aufsicht kann "
            "ein Bußgeld verhängen."
        ),
        "rule_id": "dsgvo_datenschutzerklaerung",
        "scan_pillar": "gdpr",
        "stichwoerter": ["datenschutzerklärung", "datenschutzerklaerung", "datenschutz"],
        "art": ART_BEIDES,
        "wer_fordert": "Verbände und Mitbewerber (Abmahnung); Datenschutzaufsicht (Bußgeld)",
        "typische_forderung_euro": [200, 1000],
        "forderung_quelle": (
            "Verbandspauschale ca. 200 bis 400 €; Anwaltskosten bei "
            "Gegenstandswert 10.000 € ca. 820 € netto. Mitbewerber-Abmahnungen "
            "an Unternehmen unter 250 Beschäftigten sind ohne Kostenersatz "
            "(§ 13 Abs. 4 Nr. 2 UWG)."
        ),
        "seit": "2018-05",
        "quelle_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    },
    {
        "id": "impressum",
        "titel": "Impressum fehlt oder ist lückenhaft",
        "beschreibung": (
            "§ 5 DDG verlangt Name, Anschrift, Kontakt, Register- und "
            "Umsatzsteuer-Angaben, leicht erkennbar von jeder Seite aus. Fehlende "
            "oder versteckte Angaben gehören seit Jahren zu den häufigsten "
            "Abmahngründen. Mitbewerber können dafür seit 2020 keine "
            "Abmahnkosten mehr verlangen (§ 13 Abs. 4 Nr. 1 UWG), Verbände wie "
            "die Wettbewerbszentrale oder der IDO schon; außerdem droht ein "
            "Bußgeld nach § 32 DDG."
        ),
        "rule_id": "impressum",
        "scan_pillar": "legal",
        "stichwoerter": ["impressum", "anbieterkennzeichnung"],
        "art": ART_BEIDES,
        "wer_fordert": "Wettbewerbsverbände (Abmahnung mit Kostenpauschale); Mitbewerber (nur Unterlassung); Behörde (Bußgeld)",
        "typische_forderung_euro": [200, 1000],
        "forderung_quelle": (
            "Verbandspauschale ca. 200 bis 400 €; Anwaltskosten bei "
            "Gegenstandswert 10.000 € ca. 820 € netto, für Mitbewerber bei "
            "Informationspflichten im Internet ausgeschlossen (§ 13 Abs. 4 Nr. 1 UWG)."
        ),
        "seit": "2007-03",
        "quelle_url": "https://www.gesetze-im-internet.de/ddg/__5.html",
    },
    {
        "id": "widerruf_shop",
        "titel": "Widerrufsbelehrung im Shop fehlt oder ist veraltet",
        "beschreibung": (
            "Verbraucher müssen vor der Bestellung über ihr Widerrufsrecht "
            "belehrt werden und das Muster-Widerrufsformular erhalten "
            "(§§ 312g, 355 BGB, Art. 246a EGBGB). Fehlt die Belehrung oder ist "
            "sie veraltet, läuft die Widerrufsfrist bis zu zwölf Monate länger, "
            "und Verbände mahnen den Verstoß regelmäßig ab. Für Mitbewerber gilt "
            "auch hier: Unterlassung ja, Kostenersatz nein (§ 13 Abs. 4 Nr. 1 UWG)."
        ),
        "rule_id": "widerruf_shop",
        "scan_pillar": "legal",
        "stichwoerter": ["widerrufsbelehrung", "widerrufsformular", "widerrufsrecht", "online-shop erkannt"],
        "art": ART_ABMAHNUNG,
        "wer_fordert": "Wettbewerbsverbände (mit Kostenpauschale); Mitbewerber (nur Unterlassung)",
        "typische_forderung_euro": [200, 1000],
        "forderung_quelle": (
            "Verbandspauschale ca. 200 bis 400 €; Anwaltskosten bei "
            "Gegenstandswert 10.000 € ca. 820 € netto."
        ),
        "seit": "2014-06",
        "quelle_url": "https://www.gesetze-im-internet.de/bgb/__355.html",
    },
    {
        "id": "bfsg_barrierefreiheit",
        "titel": "Barrierefreiheit nach BFSG (Marktüberwachung und Verbandsklage)",
        "beschreibung": (
            "Seit dem 28.06.2025 müssen verbrauchergerichtete Online-Shops und "
            "digitale Dienstleistungen barrierefrei sein (§§ 3, 14 BFSG). "
            "Zuständig ist die Marktüberwachung der Länder, die Verstöße mit "
            "Bußgeld bis 100.000 € ahnden kann (§ 37 BFSG); qualifizierte "
            "Einrichtungen können auf Unterlassung klagen (§ 34 BFSG). Ob "
            "Mitbewerber über das UWG abmahnen können, ist noch nicht "
            "höchstrichterlich geklärt. Der Scan misst Alt-Texte, Kontraste, "
            "Tastaturbedienung und Überschriften-Struktur."
        ),
        "rule_id": "bfsg",
        "scan_pillar": "accessibility",
        "stichwoerter": [
            "alt-text", "alternativtext", "kontrast", "tastatur", "überschrift",
            "wcag", "barrierefrei", "h1",
        ],
        "art": ART_BUSSGELD,
        "wer_fordert": "Marktüberwachungsbehörde (Bußgeld); Verbände (Unterlassungsklage)",
        "typische_forderung_euro": None,
        "forderung_quelle": (
            "Noch keine veröffentlichten Bußgelder oder Abmahnpraxis mit "
            "belegbaren Beträgen; der gesetzliche Rahmen reicht bis 100.000 €."
        ),
        "seit": "2025-06",
        "quelle_url": "https://www.gesetze-im-internet.de/bfsg/",
    },
    {
        "id": "newsletter_ohne_double_opt_in",
        "titel": "Newsletter ohne nachweisbare Einwilligung (Double-Opt-in)",
        "beschreibung": (
            "Werbe-Mails ohne vorherige ausdrückliche Einwilligung sind unzumutbare "
            "Belästigung (§ 7 Abs. 2 Nr. 2 UWG). Der Versender muss die "
            "Einwilligung beweisen; ohne dokumentiertes Double-Opt-in gelingt das "
            "vor Gericht praktisch nie. Abgemahnt wird sowohl vom Empfänger "
            "(Unterlassung nach §§ 823, 1004 BGB) als auch von Mitbewerbern, und "
            "hier gilt der Kostenausschluss des § 13 Abs. 4 UWG nicht."
        ),
        "rule_id": "uwg_newsletter",
        "scan_pillar": None,
        "stichwoerter": ["newsletter", "double-opt-in", "double opt-in", "e-mail-marketing"],
        "art": ART_ABMAHNUNG,
        "wer_fordert": "Empfänger und Mitbewerber über Anwälte",
        "typische_forderung_euro": [300, 850],
        "forderung_quelle": (
            "Anwaltskosten nach RVG bei den üblichen Gegenstandswerten von "
            "3.000 bis 10.000 € je unerlaubter Mail (ca. 310 bis 820 € netto)."
        ),
        "seit": "2009-01",
        "quelle_url": "https://www.gesetze-im-internet.de/uwg_2004/__7.html",
    },
]

HINWEIS = (
    "Information, keine Rechtsberatung. Die Beträge sind typische Spannen aus "
    "veröffentlichten Entscheidungen und Gebührentabellen, keine Vorhersage für "
    "Ihren Fall. Die Betroffenheit ist eine Einschätzung aus Ihrem Firmenprofil "
    "und dem letzten Scan, kein Rechtsurteil."
)

HINWEIS_OHNE_PROFIL = (
    "Ohne Firmenprofil lässt sich nicht einschätzen, welche Wellen Sie treffen "
    "können. Bitte zuerst den Fragebogen im Pflichten-Report ausfüllen."
)

_ORDNUNG = {WAHRSCHEINLICH: 0, PRUEFEN: 1, UNBEKANNT: 2, UNWAHRSCHEINLICH: 3}


def betroffenheit_bestimmen(rule_status: Optional[str], pillar_score: Optional[float]) -> str:
    """
    Einschätzung je Welle aus Profil-Status der Pflicht und Säulenwert des Scans.

    - wahrscheinlich: Pflicht trifft laut Profil zu UND die Säule ist unter 80.
      Erst beide Indizien zusammen tragen die stärkste Aussage.
    - pruefen: Pflicht trifft zu oder ist zu prüfen, die Säule ist unauffällig
      oder gar nicht gemessen. Auch „prüfen“ plus niedriger Säulenwert landet
      hier: wenn schon das Profil unklar ist, darf der Scan allein kein
      „wahrscheinlich“ erzeugen (Selbst-Check-Design, kein Rechtsurteil).
    - unwahrscheinlich: Pflicht laut Profil nicht indiziert. Nie „ausgeschlossen“.
    - unbekannt: kein Profil.
    """
    if rule_status is None:
        return UNBEKANNT
    if rule_status == NOT_INDICATED:
        return UNWAHRSCHEINLICH
    if rule_status == APPLIES and pillar_score is not None and pillar_score < SAEULE_UNAUFFAELLIG_AB:
        return WAHRSCHEINLICH
    return PRUEFEN


def wellen_anreichern(
    report_items: Optional[List[Dict[str, Any]]],
    scan: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Verknüpft jede Welle mit Profil (report_items aus evaluate_pflichten) und
    letztem Scan (Form wie _latest_scan_pillars: url, scan_date, pillars).
    Ohne Profil ist report_items None: dann gibt es keine Relevanz, nur
    „unbekannt“. Sortiert nach Betroffenheit, damit der Teaser im Free-Tarif
    die wichtigsten Wellen zeigt.
    """
    by_rule = {i["id"]: i for i in (report_items or [])}
    ergebnis: List[Dict[str, Any]] = []
    for welle in ABMAHNWELLEN:
        eintrag = dict(welle)
        rule = by_rule.get(welle["rule_id"]) if report_items is not None else None
        rule_status = rule["status"] if rule else None
        pillar = welle["scan_pillar"]
        pillar_score = None
        if scan and pillar and scan.get("pillars", {}).get(pillar) is not None:
            pillar_score = scan["pillars"][pillar]
        eintrag["relevanz"] = {
            "rule_status": rule_status,
            "rule_title": rule["title"] if rule else None,
            "rule_evidence": rule["evidence"] if rule else [],
            "pillar_score": pillar_score,
            "scan_date": scan.get("scan_date") if scan and pillar_score is not None else None,
            "scanned_url": scan.get("url") if scan and pillar_score is not None else None,
        }
        eintrag["betroffenheit"] = betroffenheit_bestimmen(rule_status, pillar_score)
        eintrag["locked"] = False
        ergebnis.append(eintrag)
    ergebnis.sort(key=lambda w: _ORDNUNG[w["betroffenheit"]])
    return ergebnis


def teaser_anwenden(wellen: List[Dict[str, Any]], sichtbar: int = 2) -> List[Dict[str, Any]]:
    """
    Free-Tarif: alle Wellen bleiben sichtbar, die Betroffenheit aber nur für
    die ersten `sichtbar`. Der Rest trägt locked=True und keine Relevanz, damit
    das Dashboard nichts anzeigen kann, was der Server nicht freigegeben hat.
    """
    for idx, w in enumerate(wellen):
        if idx >= sichtbar:
            w["locked"] = True
            w["betroffenheit"] = None
            w["relevanz"] = None
    return wellen
