"""
Deterministischer Patch-Builder: freigegebene Fixes -> Unified Diffs.

Die fehlende Bruecke im "Fix ohne LLM"-Weg. Bisher galt: die KI erzeugt
Vorschlaege (einmal, mit Review), das Fix-Manifest liefert sie aus — aber wer
daraus einen Pull Request machen wollte, brauchte einen externen LLM-Agenten
via MCP, der das Repo liest und Patches formuliert. Dieses Modul ersetzt den
Agenten fuer den Anwendungs-Schritt durch Mechanik:

    KI schlaegt vor (einmal)  ->  Mensch gibt frei  ->  MASCHINE wendet an.

Warum kein LLM beim Anwenden: Ein freigegebener Alt-Text ist ein Datum, keine
Ermessensfrage. `<img src="team.jpg">` um `alt="..."` zu ergaenzen ist eine
Textoperation — dieselbe Eingabe muss denselben PR ergeben, sonst ist weder
Review noch Revert verlaesslich. Nebeneffekt: keine Token-Kosten pro Anwendung,
und der Satz "keine KI schreibt ungeprueft in Ihren Code" stimmt woertlich.

Warum String-Chirurgie statt BeautifulSoup: BS parst und serialisiert das
ganze Dokument neu — Attributreihenfolge, Einrueckung und Entities aendern
sich, der Diff wird zur Tapete und der Kunde kann im PR nicht mehr sehen, was
wirklich passiert. Hier wird nur die eine Stelle angefasst; alles andere
bleibt byte-identisch.

Alle Transformationen sind GUARDED: nur setzen, wenn am Ziel nichts steht.
Ein vorhandenes alt="" (bewusst dekorativ markiert) wird nie ueberschrieben —
dieselbe Regel, die auch WordPress-Plugin und Runtime-Widget befolgen.
"""
import difflib
import hashlib
import logging
import posixpath
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Dateitypen, in denen HTML woertlich im Repo liegt. Bewusst konservativ:
# JSX/TSX rendern Attribute zur Laufzeit (alt={...}) — dort wuerde die
# Textoperation Falsches treffen. Solche Repos bleiben dem MCP-Agenten.
KANDIDATEN_ENDUNGEN = (".html", ".htm", ".php", ".twig", ".liquid", ".njk", ".hbs")

# Pfade, die nie angefasst werden.
AUSGESCHLOSSENE_PFADE = re.compile(
    r"(^|/)(node_modules|vendor|dist|build|\.next|\.git|cache|uploads)(/|$)", re.I
)

MAX_DATEIEN = 200          # Schutz gegen Monorepos
MAX_DATEI_BYTES = 400_000  # Templates sind klein; alles darueber ist Asset/Generat

# Welche dokumentweiten Fix-Typen dieser Builder wirklich in eine Datei
# schreiben kann. css-rule und landmark-main stehen bewusst NICHT hier (siehe
# baue_patches) — sie werden ueber Widget/Plugin ausgeliefert, nicht per PR.
#
# Diese Menge ist die einzige Quelle der Wahrheit dafuer, was der PR-Knopf
# verspricht. Sie wird ueber `zaehle_pr_faehig` bis in die Worklist
# durchgereicht, damit der Knopf nie mehr ankuendigt, als er liefern kann.
PR_FAEHIGE_DOKUMENT_FIXES = frozenset({"html-lang", "skip-link"})

_IMG_TAG = re.compile(r"<img\b[^>]*?/?>", re.I | re.S)
# (?<![\w-]) haelt data-alt / data-src von den echten Attributen fern. Ohne die
# Sperre galt ein Bild mit data-alt="…" faelschlich als versorgt.
_SRC_ATTR = re.compile(r"""(?<![\w-])src\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_ALT_ATTR = re.compile(r"""(?<![\w-])alt\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_HTML_TAG = re.compile(r"<html\b[^>]*>", re.I)
_HAS_LANG = re.compile(r"(?<![\w-])lang\s*=", re.I)
_BODY_TAG = re.compile(r"<body\b[^>]*>", re.I)

# Vorschlaege, die ein Attribut fuellen und nichts erklaeren ("Bild: Image 20").
# Sie bestehen axe, weil axe nur die Existenz des Attributs prueft — und sind
# fuer einen Screenreader-Nutzer trotzdem wertlos. Im echten Bestand waren 5
# von 14 Vorschlaegen fuer spedition-mahn.de von dieser Sorte (06.08.2026);
# ungefiltert waeren sie als "Barrierefreiheit hergestellt" in einen
# Kunden-Pull-Request gewandert.
_NICHTSSAGEND = re.compile(
    r"^\s*(bild|image|foto|photo|grafik)?\s*[:\-]?\s*"
    r"(bild|image|foto|photo|img)?\s*[_\-]?\d*\s*$",
    re.I,
)


def ist_nichtssagend(alt: str) -> bool:
    """Fuellt das Attribut, erklaert aber nichts — gehoert in keinen PR."""
    return bool(_NICHTSSAGEND.match(alt or ""))


def ist_kandidat(pfad: str, groesse: Optional[int] = None) -> bool:
    """Lohnt es, diese Repo-Datei zu holen und zu untersuchen?"""
    if AUSGESCHLOSSENE_PFADE.search(pfad):
        return False
    if not pfad.lower().endswith(KANDIDATEN_ENDUNGEN):
        return False
    if groesse is not None and groesse > MAX_DATEI_BYTES:
        return False
    return True


def zaehle_pr_faehig(
    alt_texte: List[Dict[str, Any]],
    link_fixes: List[Dict[str, Any]],
    dokument_fixes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Teilt freigegebene Fixes in "kann der PR-Weg ausliefern" und "kann er nicht".

    Der Grund fuer diese Funktion ist ein Fehler, der ohne sie unvermeidlich
    ist: die Worklist zaehlte alle freigegebenen Fixes zusammen und schrieb die
    Summe auf den PR-Knopf. Wer nur Link-Zwecke freigegeben hatte, sah "3
    freigegebene Fixes als PR vorschlagen", klickte — und bekam "Keine
    freigegebenen Fixes vorhanden". Der Knopf hat etwas versprochen, das dieser
    Weg nie liefern konnte.

    Was der PR-Weg NICHT kann und warum:
      - link_fixes (WCAG 2.4.4): Ein besserer Linktext ist redaktionell. Ihn
        als aria-label zu setzen, wuerde den sichtbaren Text vom zugaenglichen
        Namen trennen und WCAG 2.5.3 (Label in Name) verletzen — ein Fix, der
        einen neuen Fehler baut. Auslieferung erfolgt ueber Widget/Plugin.
      - css-rule: wirkt erst mit einer Include-Aenderung, deren Ort je Projekt
        verschieden ist (Ermessen).
      - landmark-main: Inhalte in <main> zu wickeln ist Strukturchirurgie.

    Returns:
        {"deliverable": int, "manifest_only": int, "by_type": {...}}
        `deliverable` ist die Zahl, die auf dem Knopf stehen darf.
    """
    doc_faehig = [
        f for f in dokument_fixes
        if f.get("fix_type") in PR_FAEHIGE_DOKUMENT_FIXES
    ]
    doc_rest = len(dokument_fixes) - len(doc_faehig)

    return {
        "deliverable": len(alt_texte) + len(doc_faehig),
        "manifest_only": len(link_fixes) + doc_rest,
        "by_type": {
            "alt_texts": len(alt_texte),
            "document_fixes": len(doc_faehig),
            "link_fixes_manifest_only": len(link_fixes),
            "document_fixes_manifest_only": doc_rest,
        },
    }


def inhalt_hash(inhalt: str) -> str:
    """Fingerabdruck der Datei, auf der ein Patch beruht.

    Der Committer prueft damit, dass die Datei zwischen Lesen und Schreiben
    unveraendert geblieben ist. Ohne diese Pruefung koennte ein Patch, der auf
    einem alten Stand berechnet wurde, fremde Aenderungen ueberschreiben.
    """
    return hashlib.sha256(inhalt.encode("utf-8")).hexdigest()


def _basename(src: str) -> str:
    """Dateiname eines Bildpfads — ohne Query, ohne Verzeichnis."""
    pfad = urlparse(src).path or src
    return posixpath.basename(pfad).strip().lower()


def _escape_attr(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def _setze_alt_texte(inhalt: str, alt_texte: List[Dict[str, Any]]) -> "tuple[str, list[str]]":
    """
    Setzt alt="..." an <img>-Tags, deren src-Dateiname zu einem freigegebenen
    Fix passt und die noch keinen echten Alt-Text tragen.

    Der Abgleich laeuft ueber den Dateinamen, nicht die volle URL: im Manifest
    steht "https://kunde.de/wp-content/uploads/team.jpg", im Template
    "/assets/img/team.jpg" oder "{{ base }}/team.jpg". Der Dateiname ist die
    stabile Schnittmenge. Kollisionsrisiko (gleicher Name, anderes Bild) ist
    akzeptiert — der Kunde sieht jede Zeile im PR-Diff.

    Zur Regel "was gilt als versorgt":
        alt="Gelber Sattelzug"  ->  nie anfassen. Eine getroffene Entscheidung.
        alt=""                  ->  fuellen, wenn ein freigegebener Fix vorliegt.
        kein alt                ->  ergaenzen.

    Das leere alt war frueher ebenfalls tabu, mit der Begruendung "bewusst als
    dekorativ markiert". Fuer handgeschriebenes HTML stimmt das; fuer den
    tatsaechlichen Bestand nicht: WordPress schreibt alt="" an JEDES Bild, dem
    in der Mediathek kein Alt-Text hinterlegt ist. Auf spedition-mahn.de trugen
    20 von 37 Bildern ein leeres alt — der mechanische Fix hat dort deshalb
    nichts veraendert, obwohl neun gepruefte Alt-Texte bereitlagen.

    Ausschlaggebend fuer die Aenderung ist aber nicht die Haeufigkeit, sondern
    die Konsistenz: das Laufzeit-Widget (widgets/accessibility-v6.js,
    `if (img && !img.alt)`) fuellt leere alt-Attribute seit jeher — auf
    Kundenseiten, die live sind. PR-Weg und Widget lieferten damit fuer
    dieselben freigegebenen Fixes verschiedene Ergebnisse. Zwei Kanaele, eine
    Regel; die menschliche Freigabe in der Worklist ist der Schutz, den der
    pauschale Guard ersetzen sollte.
    """
    nach_name: Dict[str, str] = {}
    for fix in alt_texte:
        name = _basename(fix.get("image_src") or fix.get("image_filename") or "")
        text = (fix.get("suggested_alt") or "").strip()
        # Nichtssagende Vorschlaege gar nicht erst einsammeln: ein PR, der
        # alt="Bild: Image 20" einbaut, behauptet eine Reparatur, die keine ist.
        if name and text and not ist_nichtssagend(text):
            nach_name.setdefault(name, text)

    if not nach_name:
        return inhalt, []

    angewendet: List[str] = []

    def ersetze(match: "re.Match[str]") -> str:
        tag = match.group(0)
        alt_match = _ALT_ATTR.search(tag)
        if alt_match and (alt_match.group(1) or alt_match.group(2) or "").strip():
            return tag  # echter Alt-Text: eine Entscheidung, die bleibt

        src_match = _SRC_ATTR.search(tag)
        if not src_match:
            return tag
        name = _basename(src_match.group(1) or src_match.group(2) or "")
        text = nach_name.get(name)
        if not text:
            return tag

        angewendet.append(name)
        if alt_match:
            # Leeres alt vorhanden -> nur dessen Wert ersetzen, die Position im
            # Tag bleibt, damit der Diff eine Zeile bleibt. Immer in doppelten
            # Anfuehrungszeichen: _escape_attr maskiert genau die.
            anfang, ende = alt_match.span()
            return tag[:anfang] + f'alt="{_escape_attr(text)}"' + tag[ende:]

        einschub = f' alt="{_escape_attr(text)}"'
        if tag.endswith("/>"):
            return tag[:-2].rstrip() + einschub + " />"
        return tag[:-1] + einschub + ">"

    return _IMG_TAG.sub(ersetze, inhalt), angewendet


def _setze_html_lang(inhalt: str, wert: str) -> "tuple[str, bool]":
    """lang-Attribut am <html>-Tag — nur wenn keines da ist."""
    match = _HTML_TAG.search(inhalt)
    if not match:
        return inhalt, False
    tag = match.group(0)
    if _HAS_LANG.search(tag):
        return inhalt, False
    neu = tag[:-1] + f' lang="{_escape_attr(wert)}">'
    return inhalt[: match.start()] + neu + inhalt[match.end():], True


def _setze_skip_link(inhalt: str, label: str, ziel: str) -> "tuple[str, bool]":
    """
    Sprunglink als erstes Element nach <body> — nur wenn keiner existiert
    und das Ziel im Dokument vorhanden ist. Ein Link auf ein nicht
    existierendes Ziel waere selbst ein Barrierefreiheits-Fehler.
    """
    if "skip-link" in inhalt or f'href="{ziel}"' in inhalt:
        return inhalt, False
    ziel_id = ziel.lstrip("#")
    if not ziel_id:
        return inhalt, False
    hat_ziel = (
        re.search(rf"""\bid\s*=\s*["']{re.escape(ziel_id)}["']""", inhalt)
        or (ziel_id == "main" and re.search(r"<main\b", inhalt, re.I))
    )
    if not hat_ziel:
        return inhalt, False
    match = _BODY_TAG.search(inhalt)
    if not match:
        return inhalt, False
    snippet = (
        f'\n<a class="skip-link" href="{_escape_attr(ziel)}" '
        f'style="position:absolute;left:-9999px;top:auto;" '
        f'onfocus="this.style.left=\'8px\';this.style.top=\'8px\';" '
        f'onblur="this.style.left=\'-9999px\';">{_escape_attr(label)}</a>'
    )
    return inhalt[: match.end()] + snippet + inhalt[match.end():], True


def baue_patches(
    manifest: Dict[str, Any],
    dateien: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Wendet die freigegebenen Fixes des Manifests auf Repo-Dateien an.

    Pure Funktion: Manifest + {pfad: inhalt} rein, Patch-Liste raus — kein
    Netz, kein LLM, keine Uhr. Dieselbe Eingabe ergibt immer denselben PR.

    Bewusst NICHT umgesetzt:
      - css_rules: eine neue CSS-Datei wirkt erst mit Include-Aenderung —
        wo die hingehoert, ist je Projekt verschieden (Ermessen -> MCP-Agent).
      - landmark-main: Inhalte in <main> zu wickeln ist Strukturchirurgie,
        kein Attribut — zu riskant fuer eine blinde Textoperation.

    Returns:
        Patches im Format von create_accessibility_pr:
        {file_path, unified_diff, feature_id, description}
    """
    alt_texte = manifest.get("alt_texts") or []
    dokument_fixes = manifest.get("document_fixes") or []

    lang_wert = None
    skip_link = None
    for fix in dokument_fixes:
        payload = fix.get("payload") or {}
        if isinstance(payload, str):
            try:
                import json as _json
                payload = _json.loads(payload)
            except Exception:
                payload = {}
        if fix.get("fix_type") == "html-lang" and payload.get("value"):
            lang_wert = payload["value"]
        elif fix.get("fix_type") == "skip-link" and payload.get("target"):
            skip_link = (payload.get("label") or "Zum Inhalt springen", payload["target"])

    patches: List[Dict[str, Any]] = []

    for pfad in sorted(dateien):
        original = dateien[pfad]
        inhalt = original
        beschreibungen: List[str] = []
        feature = "A11Y"

        inhalt, bilder = _setze_alt_texte(inhalt, alt_texte)
        if bilder:
            feature = "ALT_TEXT"
            beschreibungen.append(f"Alt-Texte für {len(bilder)} Bild(er)")

        if lang_wert:
            inhalt, gesetzt = _setze_html_lang(inhalt, lang_wert)
            if gesetzt:
                beschreibungen.append(f'lang="{lang_wert}" am <html>-Tag')

        if skip_link:
            inhalt, gesetzt = _setze_skip_link(inhalt, skip_link[0], skip_link[1])
            if gesetzt:
                beschreibungen.append("Sprunglink zum Hauptinhalt")

        if inhalt == original:
            continue  # guarded: nichts zu tun -> kein Patch, kein Rauschen im PR

        diff = "\n".join(
            difflib.unified_diff(
                original.splitlines(),
                inhalt.splitlines(),
                fromfile=f"a/{pfad}",
                tofile=f"b/{pfad}",
                lineterm="",
            )
        )
        patches.append({
            "file_path": pfad,
            "unified_diff": diff,           # fuer Anzeige/Review — nicht zum Wiederanwenden
            "new_content": inhalt,          # das ist der massgebliche Zielzustand
            "base_sha256": inhalt_hash(original),
            "feature_id": feature,
            "description": "; ".join(beschreibungen),
        })

    logger.info(f"Patch-Builder: {len(patches)} Datei(en) geändert aus {len(dateien)} Kandidaten")
    return patches
