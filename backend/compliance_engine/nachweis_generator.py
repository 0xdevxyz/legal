"""
Der Prüfnachweis — was complyo hat und sonst niemand.

Die Idee
--------
Jeder Anbieter am Markt behauptet etwas. Scanner behaupten, sie hätten alles
gefunden. Overlays behaupten, sie hätten alles behoben. Agenturen behaupten es
einmal, in einem PDF, das am nächsten Tag veraltet ist.

complyo behauptet nichts. Es legt ein Protokoll vor: Was wurde geprüft, mit
welchem Regelsatz, wann. Was war vorher da. Was wurde geändert, mit welcher
Begründung und mit welchem gemessenen Ergebnis. **Und was wurde nicht behoben,
und warum nicht.**

Der letzte Punkt ist der eigentliche Unterschied. Ein Konformitätssiegel, das
nur Erfolge zeigt, ist wertlos — jeder kann eins malen. Ein Protokoll, das die
eigenen Lücken benennt, ist überprüfbar. Und Überprüfbarkeit ist genau das,
was ein Compliance-Käufer kauft.

Warum das den Preis trägt
-------------------------
Das BFSG verlangt von betroffenen Anbietern eine **Barrierefreiheitserklärung**
mit Angaben zum Konformitätsstatus, den bekannten Ausnahmen und dem Datum der
Bewertung. Heute wird sie von Hand geschrieben, selbst erklärt, von niemandem
geprüft — und ist nach dem nächsten Theme-Update falsch.

Hier entsteht sie aus der Messung. Jede Zahl darin ist auf ein Protokoll
zurückführbar, das jederzeit neu erzeugt werden kann. Eine Agentur berechnet
für Prüfung plus Erklärung üblicherweise einen vierstelligen Betrag, einmalig.

Nur wer repariert, kann so ein Protokoll überhaupt schreiben: ein Scanner hat
kein Nachher, ein Overlay hat keine ehrlichen Zahlen.
"""
import hashlib
import json
import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Regeln, deren Behebung complyo aus Prinzip nicht mechanisch versucht — mit
# dem Grund, der im Nachweis steht. Ein Protokoll, das Luecken verschweigt,
# waere dasselbe wie ein Siegel.
NICHT_MECHANISCH: Dict[str, str] = {
    "nested-interactive": (
        "Ein Bedienelement in einem Bedienelement ist ein Strukturfehler; die "
        "Auflösung baut Inhalt um und gehört in die Hand des Entwicklers."
    ),
    "aria-required-parent": (
        "Die Rolle ist meist doppelt vergeben, nicht fehlend. Die Reparatur "
        "wäre ein Entfernen — das kann die Skripte des Themes brechen."
    ),
    "heading-order": (
        "Welche Zeile welche Überschriftenebene ist, ist eine redaktionelle "
        "Entscheidung."
    ),
    "page-has-heading-one": (
        "Welcher Text die Hauptüberschrift der Seite ist, kann nur der "
        "Betreiber sagen."
    ),
    "image-alt": (
        "Wird über den Alt-Text-Weg behoben: KI-Vorschlag, menschliche "
        "Freigabe. Kein Bild bekommt ungeprüft eine Beschreibung."
    ),
    "color-contrast": (
        "Einzelne Farbpaare erreichen die Vorgabe nur über eine Änderung des "
        "Hintergrunds — die geht über eine Textfarbe hinaus."
    ),
    "link-name": (
        "Ein Link mit `href=\"#\"` ohne Klasse, Ziel oder Inhalt gibt nichts "
        "her, woraus sich eine Beschriftung ableiten ließe."
    ),
    "label": (
        "Manche Felder tragen weder Namen noch Platzhalter noch sichtbaren "
        "Text davor. Eine erfundene Beschriftung schickt Nutzer in die Irre."
    ),
    "region": (
        "Restliche Inhalte liegen ausserhalb des Hauptbereichs — etwa "
        "Schieberegler oder Einblendungen, die das Theme neben den Inhalt "
        "setzt. Sie einem Bereich zuzuordnen waere eine Aussage ueber den "
        "Aufbau der Seite, die nur der Betreiber treffen kann."
    ),
    "landmark-unique": (
        "Mehrere gleichartige Bereiche brauchen unterscheidende Namen. Wie sie "
        "heissen sollen, ergibt sich aus dem Inhalt, nicht aus dem Markup."
    ),
    "landmark-complementary-is-top-level": (
        "Ein verschachtelter Randbereich laesst sich nur durch Verschieben im "
        "Dokument aufloesen — das ist ein Umbau, keine Ergaenzung."
    ),
    "select-name": (
        "Ohne Name, Platzhalter oder Text davor gibt das Auswahlfeld nichts "
        "her, woraus sich eine Beschriftung ableiten liesse."
    ),
    "document-title": (
        "Die Seite traegt weder Ueberschrift noch og:title, aus dem sich ein "
        "Seitentitel ableiten liesse."
    ),
}


def nachweis_token(site_id: str, geheimnis: str) -> str:
    """
    Unrat-barer, stabiler Zugriffsschluessel fuer die oeffentliche Seite.

    Stabil, damit der Link in der Barrierefreiheitserklaerung stehen bleiben
    kann; abgeleitet, damit er nicht in einer weiteren Tabelle gepflegt werden
    muss. Ohne konfiguriertes Geheimnis gibt es keinen Token — dann bleibt der
    Nachweis intern, statt mit einem ratbaren Schluessel oeffentlich zu sein.
    """
    if not geheimnis:
        return ""
    roh = f"{site_id}|{geheimnis}".encode("utf-8")
    return hashlib.sha256(roh).hexdigest()[:32]


def _regel_zeilen(vorher: Dict[str, int], nachher: Dict[str, int]) -> List[Dict[str, Any]]:
    zeilen = []
    for regel in sorted(set(vorher) | set(nachher), key=lambda r: -vorher.get(r, 0)):
        v, n = vorher.get(regel, 0), nachher.get(regel, 0)
        zeilen.append({
            "regel": regel,
            "vorher": v,
            "nachher": n,
            "behoben": max(0, v - n),
            "grund_offen": NICHT_MECHANISCH.get(regel) if n > 0 else None,
        })
    return zeilen


def baue_nachweis(
    site_id: str,
    site_url: str,
    messung_vorher: Dict[str, int],
    messung_nachher: Dict[str, int],
    fixes: List[Dict[str, Any]],
    alt_texte_live: int = 0,
    alt_texte_offen: int = 0,
    vorbereitet: Optional[List[Dict[str, Any]]] = None,
    gemessen_am: Optional[str] = None,
    axe_version: str = "4.11.4",
    regelsatz: str = "WCAG 2.1 AA + best-practice",
) -> Dict[str, Any]:
    """
    Baut das Prüfprotokoll.

    Args:
        messung_vorher/-nachher: {axe_regel: fundstellen}, aus demselben Lauf.
        fixes: die ausgelieferten Reparaturen mit ihrer Begründung.
        alt_texte_live: freigegebene Bildbeschreibungen (axe sieht sie nicht).
        alt_texte_offen: vorgeschlagen, aber noch nicht freigegeben — gehoert
            in den Nachweis, weil ein Protokoll, das nur die erledigte Arbeit
            zeigt, wieder ein Siegel waere.

    Returns:
        Ein Protokoll, das ohne weitere Erklärung lesbar ist — auch von
        jemandem, der complyo nicht kennt.
    """
    zeilen = _regel_zeilen(messung_vorher, messung_nachher)
    v_gesamt = sum(messung_vorher.values())
    n_gesamt = sum(messung_nachher.values())

    offen = [z for z in zeilen if z["nachher"] > 0]
    return {
        "site_id": site_id,
        "site_url": site_url,
        "gemessen_am": gemessen_am or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "pruefwerkzeug": f"axe-core {axe_version}",
        "regelsatz": regelsatz,
        "methode": (
            "Die Seite wurde im Browser geladen und geprüft. Anschließend wurden "
            "die Reparaturen eingespielt und dieselbe Prüfung erneut ausgeführt. "
            "Ausgeliefert wurde nur, was in der zweiten Messung bestanden hat."
        ),
        "summe": {
            "vorher": v_gesamt,
            "nachher": n_gesamt,
            "behoben": max(0, v_gesamt - n_gesamt),
            "quote": round(100 * (v_gesamt - n_gesamt) / v_gesamt) if v_gesamt else 0,
        },
        "je_regel": zeilen,
        "reparaturen": [
            {
                "regel": f.get("regel"),
                "was": f.get("attribut") or f.get("art"),
                "wo": f.get("selector"),
                "warum": f.get("begruendung"),
            }
            for f in fixes
        ],
        "bildbeschreibungen_live": alt_texte_live,
        "bildbeschreibungen_offen": alt_texte_offen,
        # Geprueft, nachgemessen, aber vom Betreiber noch nicht freigegeben.
        # Diese Zeilen zaehlen NICHT als behoben — sie stehen weiter oben unter
        # "offen". Sie hier zu nennen ist trotzdem richtig: sie belegen, dass
        # die Methode auch fuer den Rest greift, und sie machen sichtbar, dass
        # die verbleibende Arbeit eine Entscheidung ist, kein Aufwand.
        "vorbereitet": [
            {
                "regel": v.get("regel"),
                "fundstellen": v.get("fundstellen"),
                "nach_reparatur_gemessen": v.get("nachgemessen"),
                "stand": "nicht freigegeben — nicht ausgeliefert",
            }
            for v in (vorbereitet or [])
        ],
        "offen": [
            {
                "regel": z["regel"],
                "fundstellen": z["nachher"],
                # Ohne hinterlegten Grund keine leere Zeile: "wir wissen es
                # nicht" ist ehrlicher als gar nichts zu schreiben.
                "grund": z["grund_offen"] or (
                    "Keine mechanisch sichere Reparatur bekannt — die Behebung "
                    "verlangt eine Entscheidung am Inhalt."
                ),
            }
            for z in offen
        ],
        "hinweis": (
            "Eine automatisierte Prüfung deckt einen Teil der WCAG-Kriterien ab. "
            "Kriterien, die menschliches Urteil verlangen (Verständlichkeit, "
            "sinnvolle Reihenfolge, Angemessenheit von Alternativtexten), sind "
            "damit nicht bewertet. Dieses Protokoll behauptet keine vollständige "
            "Konformität, sondern zeigt, was gemessen wurde."
        ),
    }


def erklaerung_aus_nachweis(nachweis: Dict[str, Any], anbieter: str,
                            kontakt: str, nachweis_url: str = "") -> str:
    """
    Die Barrierefreiheitserklärung — aus der Messung, nicht aus der Vorlage.

    Enthält die vom BFSG geforderten Angaben (Geltungsbereich,
    Konformitätsstatus, nicht barrierefreie Inhalte mit Begründung, Datum der
    Bewertung, Kontakt) und belegt jede Zahl mit dem Protokoll.

    Bewusst KEINE Konformitätsbehauptung: eine automatisierte Prüfung kann sie
    nicht tragen, und eine falsche Erklärung ist bei einem Compliance-Anbieter
    der teuerste Fehler überhaupt.
    """
    s = nachweis["summe"]
    zeilen = [
        f"# Erklärung zur Barrierefreiheit",
        "",
        f"**Geltungsbereich:** {nachweis['site_url']}",
        f"**Anbieter:** {anbieter}",
        f"**Stand der Bewertung:** {nachweis['gemessen_am']}",
        "",
        "## Stand der Vereinbarkeit mit den Anforderungen",
        "",
        "Diese Website wurde automatisiert nach WCAG 2.1 Stufe AA geprüft "
        f"({nachweis['pruefwerkzeug']}, Regelsatz {nachweis['regelsatz']}). "
        f"Dabei wurden **{s['vorher']} Abweichungen** festgestellt; "
        f"**{s['behoben']} davon sind behoben** ({s['quote']} %). "
        f"Die Behebung wurde im Browser nachgemessen — ausgeliefert wurde nur, "
        f"was die erneute Prüfung bestanden hat.",
        "",
        "Diese Erklärung beruht auf einer **automatisierten Bewertung**. "
        "Kriterien, die menschliches Urteil verlangen, sind darin nicht "
        "enthalten; eine vollständige Konformität wird deshalb nicht erklärt.",
        "",
    ]

    if nachweis["bildbeschreibungen_live"]:
        zeilen += [
            f"Zusätzlich sind **{nachweis['bildbeschreibungen_live']} "
            f"Bildbeschreibungen** hinterlegt und freigegeben. Automatische "
            f"Prüfwerkzeuge erfassen diese nicht, weil ein leeres "
            f"`alt`-Attribut als gültig gilt.",
            "",
        ]

    # Noch nicht freigegebene Bildbeschreibungen sind nicht barrierefreier
    # Inhalt — und zwar bekannter. Das BFSG verlangt genau diese Angabe. Sie
    # wegzulassen, weil sie unfertig aussieht, waere der teuerste Fehler:
    # eine Erklaerung, die eine bekannte Luecke verschweigt, ist falsch.
    if nachweis.get("bildbeschreibungen_offen"):
        zeilen += [
            f"Für **{nachweis['bildbeschreibungen_offen']} weitere Bilder** "
            f"liegt ein Beschreibungsvorschlag vor, der noch nicht freigegeben "
            f"ist. Bis zur Freigabe sind diese Bilder für Screenreader nicht "
            f"beschrieben.",
            "",
        ]

    betrieb = nachweis.get("im_betrieb") or {}
    if betrieb.get("seiten_beobachtet"):
        zeilen += [
            f"Die Wirksamkeit wird laufend im Betrieb geprüft: auf "
            f"**{betrieb['seiten_beobachtet']} Seiten** dieser Website wurden bei "
            f"echten Aufrufen **{betrieb['reparaturen_angewendet']} Reparaturen** "
            f"angewendet; zuletzt bestätigt am {betrieb['zuletzt_bestaetigt']}."
            + (f" Bei **{betrieb['ziele_verfehlt']}** Reparaturen wurde das Ziel "
               f"nicht mehr gefunden — das deutet auf eine Änderung an der "
               f"Website hin und wird geprüft."
               if betrieb.get("ziele_verfehlt") else ""),
            "",
        ]

    if nachweis["offen"]:
        zeilen += ["## Nicht barrierefreie Inhalte", "",
                   "Die folgenden Abweichungen bestehen fort. Für jede ist "
                   "angegeben, warum sie nicht automatisch behoben wurde:", ""]
        for o in nachweis["offen"]:
            zeilen.append(f"- **{o['regel']}** ({o['fundstellen']} Fundstellen): {o['grund']}")
        zeilen.append("")
    else:
        zeilen += ["## Nicht barrierefreie Inhalte", "",
                   "In der automatisierten Prüfung wurden keine offenen "
                   "Abweichungen festgestellt.", ""]

    zeilen += [
        "## Feedback und Kontakt",
        "",
        f"Sie können uns Barrieren melden: {kontakt}",
        "",
    ]

    if nachweis_url:
        zeilen += [
            "## Nachprüfbarkeit",
            "",
            f"Das vollständige Prüfprotokoll zu dieser Erklärung — mit "
            f"Regelsatz, Messzeitpunkt und jeder einzelnen Reparatur samt "
            f"Begründung — ist öffentlich einsehbar: {nachweis_url}",
            "",
        ]

    zeilen += [
        "---",
        "",
        f"Erstellt am {datetime.now().strftime('%d.%m.%Y')} aus einer Messung, "
        f"nicht aus einer Vorlage.",
    ]
    return "\n".join(zeilen)
