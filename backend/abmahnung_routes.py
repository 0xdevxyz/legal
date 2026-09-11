"""Abmahnung prüfen: das Schreiben gegen die eigene Messung halten.

Der Tag, an dem ein kleines Unternehmen wirklich nach einem Werkzeug wie
complyo sucht, ist der Tag, an dem eine Abmahnung im Briefkasten liegt. Der
Kunde lädt das Schreiben hoch (PDF oder eingefügter Text), complyo zieht die
Vorwürfe heraus und legt jeden neben die Befunde des Scanners: Sehen wir das
auch? Sehen wir es nicht? Oder können wir es gar nicht messen (Fotos ohne
Lizenz zum Beispiel)?

Das ist Messung, keine Rechtsberatung. Die Oberfläche sagt das ausdrücklich,
und die Antwort trägt die Hinweise (Frist, Anwalt, nicht ignorieren) mit, damit
kein Aufrufer sie weglassen kann.

Bewusst wird NICHTS gespeichert: das Schreiben nennt Abmahner, Anwälte und
Aktenzeichen, also Daten Dritter. Es wird gelesen, ausgewertet, beantwortet und
vergessen. Ein Wächtertest (tests/test_abmahnung.py) hält fest, dass diese
Datei keine Schreibanweisung an die Datenbank enthält. Der Text geht für die
Auswertung an den KI-Dienst (OpenRouter), wie jede andere KI-Auswertung im
Haus; fällt der aus oder ist das Budget erschöpft, übernimmt eine Heuristik.
"""

import io
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from dependencies import get_current_user, get_db, rate_limit
from site_id_utils import derive_site_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/abmahnung", tags=["abmahnung"])

# pypdf ist im Test-Image nicht installiert und in Produktion erst nach dem
# nächsten Image-Bau. Ohne das Paket antwortet die Route bei PDF mit 503 und
# einer klaren Meldung; eingefügter Text geht weiterhin.
try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_TEXT_ZEICHEN = 60_000
MAX_PDF_SEITEN = 40
# Was an die KI geht: ein Abmahnschreiben hat selten mehr als zehn Seiten;
# alles darüber sind Anlagen. Deckel, damit ein 60.000-Zeichen-Text nicht
# das Monatsbudget eines Einzelplans in einem Aufruf verbraucht.
MAX_KI_ZEICHEN = 40_000
KI_KOSTEN_SCHAETZUNG_EUR = 0.03

# Feste Kategorien, passend zu den Säulen des Scanners. Die KI darf nur diese
# vergeben; alles andere fällt auf "sonstiges".
KATEGORIEN = (
    "cookies",
    "datenschutz",
    "impressum",
    "agb_widerruf",
    "barrierefreiheit",
    "werbung_uwg",
    "urheberrecht",
    "sonstiges",
)

# Zuordnung Vorwurf-Kategorie -> Befund-Kategorien des Scanners (siehe
# `category=` in compliance_engine/checks und quick_scanner) plus Stichworte
# in Titel/Beschreibung, für Befunde, die unter einer Nachbarsäule liegen
# (Google Fonts steht z. B. unter "datenschutz", der Vorwurf lautet aber oft
# "Cookies/Tracking ohne Einwilligung"). None heißt: außerhalb der Messung.
ZUORDNUNG: Dict[str, Optional[Dict[str, Any]]] = {
    "cookies": {
        "kategorien": {"cookies"},
        "stichworte": ("cookie", "consent", "einwilligung", "tracking", "analytics",
                       "tag manager", "pixel"),
    },
    "datenschutz": {
        # "security" gehoert nicht dazu: fehlende HSTS- oder CSP-Kopfzeilen
        # sind kein Abmahnthema und standen als "verwandt" neben einem
        # Google-Fonts-Vorwurf, mit dem sie nichts zu tun haben.
        "kategorien": {"datenschutz", "avv"},
        "stichworte": ("datenschutz", "google fonts", "dsgvo", "drittland", "https",
                       "ssl", "tls", "auftragsverarbeit", "kontaktformular"),
    },
    "impressum": {
        "kategorien": {"impressum", "contact"},
        "stichworte": ("impressum", "anbieterkennzeichnung", "ddg", "tmg"),
    },
    "agb_widerruf": {
        "kategorien": {"agb", "shop"},
        "stichworte": ("agb", "widerruf", "versandkosten", "preisangabe",
                       "bestellbutton", "grundpreis", "lieferzeit"),
    },
    "barrierefreiheit": {
        "kategorien": {"barrierefreiheit", "accessibility", "kontraste",
                       "tastaturbedienung"},
        "stichworte": ("alt-text", "alternativtext", "kontrast", "barriere", "wcag",
                       "bfsg", "tastatur", "screenreader"),
    },
    "werbung_uwg": {
        "kategorien": {"uwg", "social_media"},
        "stichworte": ("irreführ", "werbung", "uwg", "garantie", "bewertung",
                       "streichpreis", "gütesiegel"),
    },
    "urheberrecht": None,
    "sonstiges": None,
}

# Schlüsselwörter der Heuristik: welche Begriffe im Schreiben auf welche
# Kategorie deuten. Kleinbuchstaben, Teilwort reicht ("cookie" trifft auch
# "Cookies" und "Cookie-Banner").
HEURISTIK_STICHWORTE: Dict[str, Tuple[str, ...]] = {
    "cookies": ("cookie", "einwilligung", "consent", "tracking", "google analytics",
                "tag manager", "einwilligungsbanner", "ttdsg", "tddg"),
    "datenschutz": ("google fonts", "datenschutzerklärung", "datenschutzerklaerung",
                    "datenschutzhinweis", "dsgvo", "art. 13", "art. 6", "drittland",
                    "ip-adresse", "auftragsverarbeit", "verschlüsselung"),
    "impressum": ("impressum", "anbieterkennzeichnung", "§ 5 ddg", "§ 5 tmg",
                  "§5 ddg", "§5 tmg", "ladungsfähige anschrift"),
    "agb_widerruf": ("widerruf", "agb", "allgemeine geschäftsbedingungen",
                     "widerrufsbelehrung", "muster-widerrufsformular",
                     "button-lösung", "preisangabenverordnung", "pangv",
                     "versandkosten", "grundpreis"),
    "barrierefreiheit": ("barrierefrei", "bfsg", "wcag", "alternativtext",
                         "alt-text", "kontrast", "screenreader",
                         "barrierefreiheitserklärung"),
    "werbung_uwg": ("irreführ", "unlauter", "uwg", "werbung", "wettbewerbsverstoß",
                    "wettbewerbsverstoss", "garantiewerbung", "streichpreis",
                    "kundenbewertung", "gütesiegel"),
    "urheberrecht": ("urheber", "lichtbild", "foto", "bild", "lizenz", "nutzungsrecht",
                     "urhg", "§ 97", "§97", "abbildung"),
}

# Abmahnungen sind zu 90 % Textbausteine. Diese Absätze sind Rahmen, keine
# Vorwürfe, und sollen nicht als "sonstiges" durchrutschen.
_RAHMEN_MARKER = (
    "mit freundlichen grüßen",
    "rechtsanwalt",
    "vollmacht",
    "unterlassungserklärung liegt bei",
    "anlage",
)

# Feste Hinweise. Sie gehören in die ANTWORT, nicht nur in die Oberfläche,
# damit sie kein Aufrufer verlieren kann.
HINWEISE = (
    "Frist prüfen: Abmahnungen setzen kurze Fristen, oft nur wenige Tage. "
    "Das Datum steht im Schreiben.",
    "Nicht ignorieren: Ohne Reaktion folgt meist eine einstweilige Verfügung, "
    "und die kostet deutlich mehr.",
    "Unterlassungserklärung nicht ungeprüft unterschreiben: Sie gilt lebenslang "
    "und enthält Vertragsstrafen. Eine modifizierte Fassung ist oft möglich.",
    "Anwalt einschalten: Eine Fachanwältin oder ein Fachanwalt für IT- oder "
    "Wettbewerbsrecht prüft Berechtigung, Höhe und Reichweite.",
    "Dieses Ergebnis ist eine technische Messung Ihrer Website und keine "
    "rechtliche Bewertung. Ob ein Vorwurf rechtlich trägt, kann nur eine "
    "juristische Prüfung klären.",
)

STATUS_BESTAETIGT = "bestaetigt"
STATUS_NICHT_GEFUNDEN = "nicht_gefunden"
STATUS_NICHT_PRUEFBAR = "nicht_pruefbar"
STATUS_OHNE_MESSUNG = "ohne_messung"

_EURO_RE = re.compile(
    r"(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:,\d{1,2})?)\s*(?:€|EUR\b|Euro\b)",
    re.IGNORECASE,
)
_FRIST_RE = re.compile(
    r"(bis\s+(?:zum\s+|spätestens\s+(?:zum\s+)?)?\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}"
    r"|innerhalb\s+von\s+\d+\s+(?:tagen|werktagen|wochen)"
    r"|binnen\s+\d+\s+(?:tagen|werktagen|wochen))",
    re.IGNORECASE,
)
_RECHTSGRUNDLAGE_RE = re.compile(
    r"(?:§§?\s*\d+[a-z]?(?:\s*Abs\.\s*\d+)?(?:\s*(?:Nr\.|S\.)\s*\d+)?\s*[A-ZÄÖÜ][A-Za-zÄÖÜäöü]{1,12}"
    r"|Art\.\s*\d+[a-z]?(?:\s*Abs\.\s*\d+)?\s*(?:lit\.\s*[a-z]\s*)?[A-Z][A-Za-z\-]{2,12})"
)


# ---------------------------------------------------------------------------
# Textgewinnung
# ---------------------------------------------------------------------------

def text_aus_pdf(rohdaten: bytes) -> str:
    """Nur Text, keine Bilder. Wirft HTTPException mit sprechender Meldung."""
    if PdfReader is None:
        raise HTTPException(
            status_code=503,
            detail="PDF-Auswertung nicht verfügbar, bitte Text einfügen.",
        )
    try:
        leser = PdfReader(io.BytesIO(rohdaten))
    except Exception:
        raise HTTPException(status_code=400, detail="Die PDF-Datei ist nicht lesbar.")

    if getattr(leser, "is_encrypted", False):
        raise HTTPException(
            status_code=400,
            detail="Die PDF-Datei ist verschlüsselt. Bitte entsperren oder den Text einfügen.",
        )

    teile: List[str] = []
    try:
        for seite in list(leser.pages)[:MAX_PDF_SEITEN]:
            teile.append(seite.extract_text() or "")
    except Exception:
        raise HTTPException(status_code=400, detail="Die PDF-Datei ist nicht lesbar.")

    text = "\n".join(teile).strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="Im PDF steht kein auswertbarer Text (vermutlich ein Scan als Bild). "
                   "Bitte den Text einfügen.",
        )
    return text[:MAX_TEXT_ZEICHEN]


# ---------------------------------------------------------------------------
# Vorwürfe herausziehen: KI, sonst Heuristik
# ---------------------------------------------------------------------------

def _euro(text: str) -> Optional[float]:
    """Größter Betrag im Absatz, als Zahl. None, wenn keiner drinsteht."""
    beste = None
    for treffer in _EURO_RE.finditer(text):
        roh = treffer.group(1).replace(".", "").replace(",", ".")
        try:
            wert = float(roh)
        except ValueError:
            continue
        if beste is None or wert > beste:
            beste = wert
    return beste


def betraege_im_text(text: str) -> List[float]:
    """Alle Beträge im Schreiben, eindeutig und absteigend. Für die Übersicht."""
    werte = set()
    for treffer in _EURO_RE.finditer(text):
        roh = treffer.group(1).replace(".", "").replace(",", ".")
        try:
            werte.add(float(roh))
        except ValueError:
            continue
    return sorted(werte, reverse=True)


def _frist(text: str) -> Optional[str]:
    treffer = _FRIST_RE.search(text)
    return treffer.group(1).strip() if treffer else None


def _rechtsgrundlage(text: str) -> Optional[str]:
    gefunden = []
    for treffer in _RECHTSGRUNDLAGE_RE.finditer(text):
        wert = re.sub(r"\s+", " ", treffer.group(0)).strip()
        if wert not in gefunden:
            gefunden.append(wert)
    return ", ".join(gefunden[:3]) if gefunden else None


def _absaetze(text: str) -> List[str]:
    """Absätze des Schreibens: Leerzeile trennt, sonst Zeilenumbruch."""
    roh = re.split(r"\n\s*\n", text)
    if len(roh) < 3:
        roh = text.split("\n")
    return [re.sub(r"\s+", " ", a).strip() for a in roh if len(a.strip()) >= 20]


def _kurz(text: str, laenge: int = 320) -> str:
    return text if len(text) <= laenge else text[:laenge - 1].rstrip() + "…"


def heuristik_vorwuerfe(text: str) -> List[Dict[str, Any]]:
    """Ordnet Absätze über Schlüsselwörter den Kategorien zu.

    Ein Eintrag je Kategorie, nicht je Absatz: ein Abmahnschreiben nennt
    "Datenschutzerklärung" in fünf Absätzen, meint aber einen Vorwurf. Der
    erste treffende Absatz wird der Vorwurfstext, die weiteren liefern nur
    Betrag, Frist und Rechtsgrundlage nach, wenn der erste sie nicht hat.
    """
    gefunden: Dict[str, Dict[str, Any]] = {}
    for absatz in _absaetze(text):
        klein = absatz.lower()
        if any(m in klein for m in _RAHMEN_MARKER) and not any(
            s in klein for worte in HEURISTIK_STICHWORTE.values() for s in worte
        ):
            continue
        # Ein Absatz gehoert zu der Kategorie, die er am haeufigsten nennt.
        # "Einwilligung" steht auch im Google-Fonts-Absatz; frueher bekam die
        # Kategorie cookies deshalb den Fonts-Absatz als Vorwurfstext, und der
        # eigentliche Cookie-Absatz lieferte nur noch Betrag und Frist nach.
        # Gegen den Cookie-Befund verglichen fand sich dann nichts.
        treffer = {kat: sum(1 for w in worte if w in klein)
                   for kat, worte in HEURISTIK_STICHWORTE.items()}
        beste = max(treffer.values()) if treffer else 0
        for kategorie, worte in HEURISTIK_STICHWORTE.items():
            anzahl = treffer[kategorie]
            if not anzahl:
                continue
            eintrag = gefunden.get(kategorie)
            # Nur die bestpassende Kategorie bekommt den Absatz als
            # Vorwurfstext; die anderen duerfen Betrag, Frist und Norm
            # nachliefern, wenn ihnen die noch fehlen.
            if eintrag is None and anzahl < beste:
                continue
            if eintrag is None:
                gefunden[kategorie] = {
                    "vorwurf": _kurz(absatz),
                    "rechtsgrundlage": _rechtsgrundlage(absatz),
                    "kategorie": kategorie,
                    "forderung_euro": _euro(absatz),
                    "frist": _frist(absatz),
                }
            else:
                if eintrag["rechtsgrundlage"] is None:
                    eintrag["rechtsgrundlage"] = _rechtsgrundlage(absatz)
                if eintrag["forderung_euro"] is None:
                    eintrag["forderung_euro"] = _euro(absatz)
                if eintrag["frist"] is None:
                    eintrag["frist"] = _frist(absatz)

    # "bild"/"foto" tauchen auch in Barrierefreiheits-Vorwürfen auf (Alt-Text
    # für Bilder). Steht im Urheberrechts-Absatz nur das, ohne Urheber, Lizenz
    # oder Lichtbild, ist es kein eigener Vorwurf.
    urheber = gefunden.get("urheberrecht")
    if urheber is not None:
        klein = urheber["vorwurf"].lower()
        if not any(w in klein for w in ("urheber", "lichtbild", "lizenz",
                                        "nutzungsrecht", "urhg", "§ 97", "§97")):
            del gefunden["urheberrecht"]

    reihenfolge = [k for k in KATEGORIEN if k in gefunden]
    return [gefunden[k] for k in reihenfolge]


def _json_aus_text(roh: str) -> Optional[Any]:
    """Wie ai_review_engine._call_ai_json: Zäune weg, dann das erste Objekt."""
    text = (roh or "").strip()
    if text.startswith("```"):
        zeilen = text.split("\n")
        text = "\n".join(zeilen[1:-1] if zeilen[-1].strip() == "```" else zeilen[1:])
    try:
        return json.loads(text)
    except Exception:
        pass
    start, ende = text.find("{"), text.rfind("}")
    if start != -1 and ende != -1:
        try:
            return json.loads(text[start:ende + 1])
        except Exception:
            return None
    return None


def _ki_prompt(text: str) -> str:
    return (
        "Du liest ein deutsches Abmahnschreiben an einen Website-Betreiber. "
        "Ziehe jeden einzelnen Vorwurf heraus. Antworte NUR mit JSON in dieser Form:\n"
        '{"vorwuerfe": [{"vorwurf": "<ein Satz, was konkret vorgeworfen wird>", '
        '"rechtsgrundlage": "<Norm, z. B. Art. 6 Abs. 1 DSGVO, oder null>", '
        '"kategorie": "<eine aus: ' + ", ".join(KATEGORIEN) + '>", '
        '"forderung_euro": <Zahl oder null>, "frist": "<Datum oder Frist als Text oder null>"}]}\n'
        "Regeln: kategorie nur aus der Liste. cookies = Tracking/Cookies ohne Einwilligung; "
        "datenschutz = Datenschutzerklärung, Google Fonts, Drittlandtransfer, Kontaktformular; "
        "impressum = Anbieterkennzeichnung; agb_widerruf = AGB, Widerruf, Preisangaben, Shop; "
        "barrierefreiheit = BFSG/WCAG; werbung_uwg = irreführende Werbung, Wettbewerbsrecht; "
        "urheberrecht = Fotos, Texte, Lizenzen; sonst sonstiges. "
        "forderung_euro ist der Betrag, der für diesen Vorwurf verlangt wird (Kosten, "
        "Schadensersatz), sonst null. Keine Erklärungen, kein Text außerhalb des JSON.\n\n"
        "SCHREIBEN:\n" + text[:MAX_KI_ZEICHEN]
    )


async def _ki_rohantwort(prompt: str, modell: str) -> Tuple[Optional[str], Dict[str, int]]:
    """Ein Aufruf, Inhalt plus Token-Verbrauch. Wirft nie.

    Eigener Aufruf statt ai_review_engine._call_ai, weil der den `usage`-Block
    verwirft und die Kosten dann nicht gebucht werden könnten.
    """
    from ai_review_engine import OPENROUTER_API_KEY, OPENROUTER_URL, _HEADERS
    if not OPENROUTER_API_KEY:
        return None, {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_URL,
                headers=_HEADERS,
                json={
                    "model": modell,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1500,
                    "temperature": 0.1,
                },
                timeout=aiohttp.ClientTimeout(total=40),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Abmahnung: KI-Aufruf {modell} Status {resp.status}")
                    return None, {}
                daten = await resp.json()
                inhalt = (daten.get("choices") or [{}])[0].get("message", {}).get("content")
                return (inhalt or None), (daten.get("usage") or {})
    except Exception as e:
        logger.warning(f"Abmahnung: KI-Aufruf fehlgeschlagen ({e})")
        return None, {}


def _vorwurf_bereinigen(roh: Any) -> Optional[Dict[str, Any]]:
    """Bringt einen KI-Eintrag in die feste Form. None, wenn unbrauchbar."""
    if not isinstance(roh, dict):
        return None
    vorwurf = str(roh.get("vorwurf") or "").strip()
    if not vorwurf:
        return None
    kategorie = str(roh.get("kategorie") or "sonstiges").strip().lower()
    if kategorie not in KATEGORIEN:
        kategorie = "sonstiges"
    forderung = roh.get("forderung_euro")
    if isinstance(forderung, str):
        forderung = _euro(forderung + " €")
    if not isinstance(forderung, (int, float)) or forderung < 0:
        forderung = None
    rechtsgrundlage = roh.get("rechtsgrundlage")
    frist = roh.get("frist")
    return {
        "vorwurf": _kurz(vorwurf, 500),
        "rechtsgrundlage": str(rechtsgrundlage).strip() if rechtsgrundlage else None,
        "kategorie": kategorie,
        "forderung_euro": float(forderung) if forderung is not None else None,
        "frist": str(frist).strip() if frist else None,
    }


async def ki_vorwuerfe(text: str, user_id, plan_type: str) -> Optional[List[Dict[str, Any]]]:
    """Vorwürfe per KI. None, wenn Budget, Dienst oder Antwort nicht taugen."""
    from compliance_engine import ai_budget
    try:
        from ai_review_engine import REVIEW_MODEL as modell
    except Exception:
        return None

    if not await ai_budget.budget_frei(user_id, plan_type,
                                       voraussichtliche_kosten_eur=KI_KOSTEN_SCHAETZUNG_EUR):
        logger.info("Abmahnung: KI-Budget erschöpft, Heuristik übernimmt")
        return None

    roh, nutzung = await _ki_rohantwort(_ki_prompt(text), modell)
    if nutzung:
        await ai_budget.kosten_buchen(
            user_id,
            ai_budget.kosten_eur(modell, int(nutzung.get("prompt_tokens") or 0),
                                 int(nutzung.get("completion_tokens") or 0)),
        )
    if not roh:
        return None
    daten = _json_aus_text(roh)
    liste = daten.get("vorwuerfe") if isinstance(daten, dict) else daten
    if not isinstance(liste, list):
        return None
    bereinigt = [v for v in (_vorwurf_bereinigen(e) for e in liste) if v]
    return bereinigt or None


async def vorwuerfe_ermitteln(text: str, user_id, plan_type: str) -> Tuple[List[Dict[str, Any]], str]:
    """Liste der Vorwürfe und woher sie stammt: "ki" oder "heuristik"."""
    per_ki = await ki_vorwuerfe(text, user_id, plan_type)
    if per_ki:
        return per_ki, "ki"
    return heuristik_vorwuerfe(text), "heuristik"


# ---------------------------------------------------------------------------
# Zuordnung zu den Messbefunden
# ---------------------------------------------------------------------------

# Nur Befunde mit Gewicht duerfen einen Vorwurf bestaetigen. Ein "info"-Befund
# ist oft ein Hinweis oder sogar eine Entwarnung. Beim ersten Live-Durchlauf am
# 11.09.2026 bestaetigte "Kein Cookie-Banner erforderlich" (info) fuenf von
# fuenf Vorwuerfen gegen complyo.de, darunter zwei zum Impressum, weil das
# Stichwort "ddg" in "TDDDG" steckt. Eine falsche Bestaetigung ist der teuerste
# Fehler dieser Seite: sie sagt dem Kunden, der Abmahner habe recht.
_BESTAETIGENDE_STUFEN = {"critical", "warning", "error", "high", "serious",
                         "moderate", "medium"}

_FUELLWOERTER = {"ihrer", "ihrem", "ihren", "unter", "sowie", "durch", "wurde",
                 "werden", "haben", "einer", "eines", "seite", "website",
                 "internetseite", "unserer", "unseres", "keine", "keinen",
                 "nicht", "ohne", "damit", "bereits", "diese", "dieser",
                 "dieses", "wird", "welche", "sowohl", "gegen", "ihres"}


def _inhaltsworte(vorwurf_text: str) -> List[str]:
    """Die tragenden Woerter eines Vorwurfs (ab fuenf Buchstaben, ohne Fuellwoerter)."""
    return [w for w in re.findall(r"[a-zäöüß]{5,}", (vorwurf_text or "").lower())
            if w not in _FUELLWOERTER]


# Woerter, die nur das Thema benennen, nicht den konkreten Vorwurf. "Cookie",
# "Banner" und "Einwilligung" stehen in JEDEM Cookie-Vorwurf und in jedem
# Cookie-Befund; sie unterscheiden "Ablehnen-Knopf fehlt" nicht von "Banner
# nennt die Laufzeit nicht".
_THEMENWOERTER = {"cookie", "cookies", "banner", "einwilligung", "einwilligen",
                  "consent", "tracking", "impressum", "anbieterkennzeichnung",
                  "angabe", "angaben", "enthält", "enthaelt", "datenschutz",
                  "datenschutzerklärung", "datenschutzerklaerung", "besucher",
                  "personenbezogen", "personenbezogene", "daten", "barrierefrei",
                  "barrierefreiheit", "widerruf", "werbung", "verstoß", "verstoss",
                  "verstößt", "fehlen", "fehlt", "fehlende", "fehlender"}


def _beruehrt(worte: List[str], text: str) -> bool:
    """Kommt eines der tragenden Woerter als GANZES Wort im Befund vor?

    Erst hiess es: ab sechs Buchstaben reicht ein gemeinsames Sechserstueck.
    Live am 11.09.2026 bestaetigte damit "Telefonnummer fehlt im Impressum"
    den Vorwurf "keine Umsatzsteuer-Identifikationsnummer", weil beide
    "nummer" enthalten. Wortformen wie "abzulehnen" gegen "Ablehnen-Knopf"
    faengt _UNTERSCHEIDER ab; hier zaehlt nur das ganze Wort.
    """
    return any(re.search(r"(?<![a-zäöüß])" + re.escape(w) + r"(?![a-zäöüß])", text)
               for w in worte)


def _thema_passt(issue: Dict[str, Any], regel: Dict[str, Any]) -> bool:
    """Liegt der Befund thematisch beim Vorwurf und hat er Gewicht?

    Kategorie oder Stichwort im TITEL, mit Wortgrenze links, damit "ddg"
    nicht "TDDDG" trifft. Befunde der Stufe info zaehlen nie: das sind
    Hinweise oder Entwarnungen.
    """
    if str(issue.get("severity") or "info").lower() not in _BESTAETIGENDE_STUFEN:
        return False
    kategorie = str(issue.get("category") or "").lower()
    titel = str(issue.get("title") or "").lower()
    return kategorie in regel["kategorien"] or any(
        re.search(r"(?<![a-zäöüß])" + re.escape(st), titel) for st in regel["stichworte"]
    )


# Was einen Vorwurf von seinem Nachbarn unterscheidet. Jede Gruppe sind
# Schreibweisen desselben Mechanismus; ein Befund bestaetigt einen Vorwurf,
# wenn beide dieselbe Gruppe beruehren. "Cookie" und "Einwilligung" stehen
# bewusst nicht drin: die stehen in jedem Cookie-Vorwurf und jedem
# Cookie-Befund und unterscheiden nichts. Als Teilzeichenketten gedacht:
# "lehnen" trifft "ablehnen", "abzulehnen" und "Ablehnen-Knopf".
_UNTERSCHEIDER: Tuple[Tuple[str, ...], ...] = (
    ("lehnen", "ablehn", "reject", "gleichwertig", "widerspruch"),
    ("vor einwilligung", "vor einer einwilligung", "vor der einwilligung", "vor consent",
     "ohne einwilligung", "bereits vor", "vor zustimmung", "pre-consent", "vor dem klick"),
    ("google fonts", "fonts.googleapis", "google-fonts", "schriftarten von google"),
    ("google analytics", "analytics", "_ga", "tag manager", "gtm", "matomo", "facebook pixel",
     "meta pixel"),
    ("ust-id", "umsatzsteuer", "ust.-id", "ustid", "steuernummer"),
    ("registergericht", "handelsregister", "registernummer", "register"),
    ("anschrift", "adresse", "ladungsfähig", "ladungsfaehig"),
    ("e-mail", "email", "elektronische kontakt"),
    ("gültigkeitsdauer", "gueltigkeitsdauer", "laufzeit", "speicherdauer"),
    ("widerrufsbelehrung", "widerruf", "muster-widerrufsformular"),
    ("alternativtext", "alt-text", "alt-attribut", "bildbeschreibung", "alt="),
    ("kontrast",),
    ("tastatur", "keyboard", "fokus"),
    ("barrierefreiheitserklärung", "barrierefreiheitserklaerung", "erklärung zur barrierefreiheit"),
    ("double-opt-in", "double opt-in", "newsletter", "opt-in"),
    ("https", "ssl", "tls", "verschlüsselung", "verschluesselung"),
    ("datenschutzerklärung", "datenschutzerklaerung", "datenschutzhinweis"),
    ("drittland", "usa", "us-server", "übermittl", "uebermittl", "drittstaat"),
    ("kontaktformular", "formular"),
    ("streichpreis", "uvp", "statt-preis"),
    ("versandkosten", "lieferzeit", "grundpreis"),
)


def _gruppen(text: str) -> set:
    t = (text or "").lower()
    return {i for i, gruppe in enumerate(_UNTERSCHEIDER) if any(g in t for g in gruppe)}


def _passt(issue: Dict[str, Any], regel: Dict[str, Any],
           inhaltsworte: Optional[List[str]] = None,
           vorwurf_text: str = "") -> bool:
    """Bestaetigt dieser Befund den Vorwurf?

    Drei Huerden, alle noetig: (1) Gewicht, (2) Thema (siehe _thema_passt),
    (3) er beruehrt den konkreten Vorwurf. Das heisst: beide nennen denselben
    Mechanismus (_UNTERSCHEIDER), oder ein tragendes, nicht bloss
    themenbenennendes Wort des Vorwurfs kommt im Befund vor. Die dritte Huerde
    gilt erst, wenn der Vorwurf ueberhaupt Substanz hat (eine Gruppe oder zwei
    tragende Woerter); ein Vorwurf ohne Substanz kann nichts beruehren.
    """
    if not _thema_passt(issue, regel):
        return False
    text = f"{str(issue.get('title') or '').lower()} {str(issue.get('description') or '').lower()}"
    gruppen_vorwurf = _gruppen(vorwurf_text)
    if gruppen_vorwurf & _gruppen(text):
        return True
    worte = [w for w in (inhaltsworte or []) if w not in _THEMENWOERTER]
    if not gruppen_vorwurf and len(worte) < 2:
        return True
    return _beruehrt(worte, text)


def _befund_kurz(issue: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": issue.get("title") or "",
        "severity": issue.get("severity") or "info",
        "legal_basis": issue.get("legal_basis") or "",
        "category": issue.get("category") or "",
    }


def _datum_lesbar(gemessen_am: Optional[str]) -> str:
    if not gemessen_am:
        return "unbekanntem Datum"
    try:
        return datetime.fromisoformat(gemessen_am.replace("Z", "+00:00")).strftime("%d.%m.%Y")
    except Exception:
        return gemessen_am


def zuordnen(
    vorwuerfe: List[Dict[str, Any]],
    issues: Optional[List[Dict[str, Any]]],
    gemessen_am: Optional[str],
) -> List[Dict[str, Any]]:
    """Jeder Vorwurf bekommt Status, passende Befunde und einen Hinweis.

    `issues` None heißt: keine Messung übergeben. Dann gibt es keine
    Zuordnung, und der Status sagt das, statt "nicht gefunden" vorzutäuschen.
    """
    ergebnis: List[Dict[str, Any]] = []
    for vorwurf in vorwuerfe:
        eintrag = dict(vorwurf)
        regel = ZUORDNUNG.get(vorwurf.get("kategorie") or "sonstiges")
        eintrag["befunde"] = []
        eintrag["verwandt"] = []

        if regel is None:
            eintrag["status"] = STATUS_NICHT_PRUEFBAR
            eintrag["hinweis"] = (
                "Dieser Punkt liegt außerhalb unserer Messung (etwa Rechte an "
                "Fotos oder Texten). Bitte anwaltlich prüfen lassen."
            )
        elif issues is None:
            eintrag["status"] = STATUS_OHNE_MESSUNG
            eintrag["hinweis"] = (
                "Ohne Messung keine Zuordnung. Starten Sie den Scan der Website, "
                "dann vergleichen wir den Vorwurf mit dem Befund."
            )
        else:
            worte = _inhaltsworte(vorwurf.get("vorwurf") or "")
            passende = [_befund_kurz(i) for i in issues
                        if isinstance(i, dict)
                        and _passt(i, regel, worte, vorwurf.get("vorwurf") or "")]
            # Befunde, die den Vorwurf wörtlich treffen, nach vorn: bei
            # "Google Fonts" soll der Fonts-Befund vor dem allgemeinen
            # Datenschutz-Befund stehen.
            def _treffer(b: Dict[str, Any]) -> int:
                t = f"{b['title']} {b['legal_basis']}".lower()
                return -sum(1 for w in worte if w in t)
            passende.sort(key=_treffer)
            eintrag["befunde"] = passende[:8]
            # Befunde derselben Saeule, die den Vorwurf nicht treffen, stehen
            # getrennt daneben: kein Beleg, aber der Kunde soll sehen, was die
            # Messung in diesem Bereich sonst gefunden hat. Ein Vorwurf
            # "USt-IdNr fehlt" trifft den Befund "USt-IdNr. fehlt" wegen der
            # Schreibweise nicht immer; daneben stehend ist er trotzdem sichtbar.
            gesehen = {b["title"] for b in passende}
            eintrag["verwandt"] = [
                _befund_kurz(i) for i in issues
                if isinstance(i, dict) and _thema_passt(i, regel)
                and (i.get("title") or "") not in gesehen
            ][:5]
            if passende:
                eintrag["status"] = STATUS_BESTAETIGT
                eintrag["hinweis"] = (
                    f"Unsere Messung vom {_datum_lesbar(gemessen_am)} findet "
                    f"{len(passende)} passende Befunde. Der Vorwurf ist technisch "
                    "nachvollziehbar; das sagt nichts über seine rechtliche Berechtigung."
                )
            else:
                eintrag["status"] = STATUS_NICHT_GEFUNDEN
                eintrag["hinweis"] = (
                    f"Unsere Messung vom {_datum_lesbar(gemessen_am)} findet dazu "
                    "nichts. Das heißt nicht, dass der Vorwurf falsch ist: er kann "
                    "sich auf eine Unterseite, einen früheren Stand oder etwas "
                    "beziehen, das wir nicht messen."
                    + (f" {len(eintrag['verwandt'])} Befunde aus demselben Bereich "
                       "stehen daneben, ohne den Vorwurf direkt zu treffen."
                       if eintrag["verwandt"] else "")
                )
        ergebnis.append(eintrag)
    return ergebnis


def zusammenfassen(zugeordnet: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
    zaehler = {
        STATUS_BESTAETIGT: 0,
        STATUS_NICHT_GEFUNDEN: 0,
        STATUS_NICHT_PRUEFBAR: 0,
        STATUS_OHNE_MESSUNG: 0,
    }
    summe = 0.0
    for v in zugeordnet:
        zaehler[v["status"]] = zaehler.get(v["status"], 0) + 1
        if isinstance(v.get("forderung_euro"), (int, float)):
            summe += float(v["forderung_euro"])
    return {
        "anzahl": len(zugeordnet),
        "je_status": zaehler,
        "forderung_summe_euro": round(summe, 2),
        # Beträge, die im Schreiben stehen, aber keinem Vorwurf zugeordnet
        # wurden (Streitwert, Anwaltskosten). Der Kunde soll sie sehen.
        "betraege_im_schreiben": betraege_im_text(text)[:10],
    }


# ---------------------------------------------------------------------------
# Beleg
# ---------------------------------------------------------------------------

async def beleg_url(site_id: str) -> Optional[str]:
    """Öffentlicher Prüfnachweis, wenn es einen gibt. Muster wie in
    accessibility_fix_routes._erklaerung_aus_pruefnachweis."""
    geheim = os.getenv("COMPLYO_NACHWEIS_SECRET", "")
    if not geheim:
        return None
    try:
        import nachweis_routes
        from compliance_engine.nachweis_generator import nachweis_token
        daten = await nachweis_routes._daten_fuer(site_id)
        if not daten:
            return None
        basis = os.getenv("COMPLYO_PUBLIC_URL", "https://complyo.de").rstrip("/")
        return f"{basis}/nachweis/{site_id}/{nachweis_token(site_id, geheim)}"
    except Exception as e:
        logger.warning(f"Abmahnung: Beleg für {site_id} nicht ermittelbar ({e})")
        return None


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

def _nutzer_id(user: Dict[str, Any]) -> Optional[int]:
    from accessibility_fix_saver import _als_user_id
    return _als_user_id(user.get("user_id") or user.get("id"))


async def _besitzt_website(db, user_id: Optional[int], website_url: str) -> bool:
    """Gehört die Website dem Konto? Vergleich über derive_site_id, damit
    "https://www.beispiel.de/" und "beispiel.de" dieselbe Site sind."""
    if db is None or user_id is None:
        return False
    ziel = derive_site_id(website_url)
    async with db.acquire() as conn:
        zeilen = await conn.fetch(
            "SELECT url FROM tracked_websites WHERE user_id = $1", user_id
        )
    return any(derive_site_id(z["url"]) == ziel for z in zeilen)


def _ergebnis_aus_auftrag(auftrag: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Befunde und Messzeitpunkt, wie sie der Abholweg in main_production liest:
    der v2-Scan liefert {success, data}, der Vorschau-Scan das Ergebnis direkt."""
    ergebnis = auftrag.get("ergebnis") or {}
    daten = ergebnis.get("data") if isinstance(ergebnis.get("data"), dict) else ergebnis
    issues = daten.get("issues") if isinstance(daten, dict) else None
    if not isinstance(issues, list):
        issues = []
    gemessen_am = daten.get("scan_timestamp") if isinstance(daten, dict) else None
    if not gemessen_am and auftrag.get("beendet"):
        try:
            gemessen_am = datetime.fromtimestamp(
                float(auftrag["beendet"]), tz=timezone.utc
            ).isoformat()
        except Exception:
            gemessen_am = None
    return issues, gemessen_am


@router.post("/pruefen", dependencies=[Depends(rate_limit("abmahnung", 5, 3600))])
async def abmahnung_pruefen(
    website_url: str = Form(...),
    text: Optional[str] = Form(None),
    kennung: Optional[str] = Form(None),
    datei: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> Dict[str, Any]:
    """Schreiben auswerten und gegen die Messung halten. Speichert nichts."""
    website_url = (website_url or "").strip()
    site_id = derive_site_id(website_url)
    if not website_url.lower().startswith(("http://", "https://")) or site_id == "unknown-site":
        raise HTTPException(status_code=400, detail="Bitte eine gültige Website-Adresse angeben.")

    user_id = _nutzer_id(user)
    if not await _besitzt_website(db, user_id, website_url):
        raise HTTPException(
            status_code=403,
            detail="Diese Website ist nicht in Ihrem Konto hinterlegt.",
        )

    # Text zusammentragen: PDF zuerst, eingefügter Text dahinter.
    teile: List[str] = []
    if datei is not None and (datei.filename or datei.size):
        if (datei.content_type or "").lower() != "application/pdf":
            raise HTTPException(status_code=400, detail="Nur PDF-Dateien werden angenommen.")
        rohdaten = await datei.read(MAX_PDF_BYTES + 1)
        if len(rohdaten) > MAX_PDF_BYTES:
            raise HTTPException(status_code=413, detail="Die PDF-Datei ist größer als 10 MB.")
        if not rohdaten.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Die Datei ist keine PDF-Datei.")
        teile.append(text_aus_pdf(rohdaten))

    if text:
        if len(text) > MAX_TEXT_ZEICHEN:
            raise HTTPException(
                status_code=413,
                detail=f"Der Text ist länger als {MAX_TEXT_ZEICHEN:,} Zeichen.".replace(",", "."),
            )
        teile.append(text.strip())

    schreiben = "\n\n".join(t for t in teile if t).strip()
    if len(schreiben) < 20:
        raise HTTPException(
            status_code=400,
            detail="Bitte das Schreiben als PDF hochladen oder den Text einfügen.",
        )

    # Messung holen, wenn eine Kennung mitkommt.
    issues: Optional[List[Dict[str, Any]]] = None
    gemessen_am: Optional[str] = None
    if kennung:
        from compliance_engine import scan_auftraege
        auftrag = await scan_auftraege.hole(kennung)
        if auftrag is None or not scan_auftraege.gehoert_zu(auftrag, user_id):
            raise HTTPException(status_code=404, detail="Diese Prüfung ist unbekannt oder abgelaufen.")
        if auftrag.get("zustand") != scan_auftraege.FERTIG:
            raise HTTPException(status_code=409, detail="Die Prüfung ist noch nicht fertig.")
        if derive_site_id(auftrag.get("url") or "") != site_id:
            raise HTTPException(status_code=400, detail="Die Prüfung gehört zu einer anderen Website.")
        issues, gemessen_am = _ergebnis_aus_auftrag(auftrag)

    vorwuerfe, quelle = await vorwuerfe_ermitteln(
        schreiben, user_id, str(user.get("plan_type") or "free")
    )
    zugeordnet = zuordnen(vorwuerfe, issues, gemessen_am)
    zusammenfassung = zusammenfassen(zugeordnet, schreiben)

    # Nur Zahlen ins Log. Kein Vorwurfstext, keine Namen, kein Aktenzeichen.
    logger.info(
        "Abmahnung geprüft: user=%s site=%s vorwuerfe=%d quelle=%s status=%s",
        user_id, site_id, len(zugeordnet), quelle, zusammenfassung["je_status"],
    )

    return {
        "website_url": website_url,
        "site_id": site_id,
        "quelle": quelle,
        "gemessen_am": gemessen_am,
        "mit_messung": issues is not None,
        "vorwuerfe": zugeordnet,
        "zusammenfassung": zusammenfassung,
        "beleg_url": await beleg_url(site_id),
        "hinweise": list(HINWEISE),
        "disclaimer": (
            "Technische Messung, keine Rechtsberatung. Das Schreiben wird nicht "
            "gespeichert; für die Auswertung wird der Text an den KI-Dienst übermittelt."
        ),
    }
