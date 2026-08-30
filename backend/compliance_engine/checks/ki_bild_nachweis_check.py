"""
Nachweis KI-generierter Bilder (Art. 50 KI-VO, VO (EU) 2024/1689)

Grundregel dieses Checks: gemeldet wird NUR, was die Bilddatei selbst bezeugt.
Kein Bildklassifikator, keine Dateinamen-Heuristik, kein "sieht KI-generiert
aus". Ein Verdacht, den der Kunde nicht nachvollziehen kann, kostet Vertrauen
und ist mehr wert als der Fund.

Als Nachweis gilt nur eine Selbstauskunft des Erzeugers in der Datei:

1. IPTC `DigitalSourceType: trainedAlgorithmicMedia` — der standardisierte
   Marker fuer "von einem trainierten Modell erzeugt". Er steht im XMP-Block
   und ebenso im C2PA-Manifest. Gesetzt u.a. von OpenAI, Google und Adobe.
2. Der Parameterblock von Stable Diffusion / Automatic1111 im PNG-Textchunk
   (Prompt, Sampler, Steps). Den schreibt nur die Erzeugung selbst.
3. Ein eindeutiger Erzeugername in Software/CreatorTool (Midjourney, DALL-E,
   Firefly ...). Bildbearbeiter wie Photoshop zaehlen ausdruecklich nicht.

WICHTIG, und der Grund fuer die Trennung: ein C2PA-Manifest allein ist KEIN
KI-Nachweis. Leica, Sony und Nikon schreiben Content Credentials auch in echte
Kamerafotos. Ein Manifest ohne KI-Marker wird deshalb vermerkt, aber nicht
gemeldet.

Umgekehrt gilt: das FEHLEN eines Markers beweist nichts. WordPress rechnet
beim Upload Vorschaubilder neu und wirft die Metadaten dabei weg. Der Check
sagt darum nie "keine KI-Bilder vorhanden", sondern nur, was er belegen kann.
"""
import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

# Vorhandene Projektschranke gegen SSRF, dieselbe wie in website_crawler.py.
# Ohne sie waere dieser Check ein Werkzeug, um aus dem internen Docker-Netz
# heraus beliebige Adressen abzurufen: die Bild-URLs stammen aus dem HTML der
# GEPRUEFTEN Seite, also von jemandem, der sie frei setzen kann.
from ssrf_protection import validate_url, SSRFError

logger = logging.getLogger(__name__)

# Metadaten stehen am Dateianfang (vor den Bilddaten). Mehr zu laden bringt
# keinen weiteren Marker, kostet aber fremde Bandbreite.
MAX_BYTES = 512 * 1024
MAX_BILDER_PRO_SEITE = 25
BILD_TIMEOUT = 5
PARALLEL = 8
# Harte Obergrenze fuer die gesamte Bildpruefung EINER Seite. Der Multi-Page-
# Scan laeuft unter asyncio.wait_for(300 s); ohne dieses Budget koennte ein
# langsames CDN den kompletten Scan ins Timeout ziehen und der Kunde verloere
# auch Impressum, Cookies und Barrierefreiheit.
SEITEN_ZEITBUDGET = 20
# Umleitungen werden einzeln nachverfolgt, damit jede Station geprueft wird.
MAX_UMLEITUNGEN = 3

# Kein Positivfilter auf Endungen: was in einem <img> steht, IST ein Bild, und
# moderne Ausspielwege tragen keine Endung mehr (Next.js liefert
# /_next/image?url=...). Ausgeschlossen wird nur, was sicher keine Metadaten
# traegt oder kein Bild ist. Der endgueltige Abgleich passiert ueber den
# Content-Type der Antwort.
KEINE_BILDER = (".svg", ".js", ".css", ".json", ".woff", ".woff2", ".ttf", ".ico")

# IPTC-Werte, die eine Erzeugung durch ein trainiertes Modell bezeugen.
# Bewusst OHNE das blosse "algorithmicMedia": das meint prozedural erzeugte
# Grafik (Diagramme, Fraktale) und ist kein KI-Nachweis.
IPTC_KI_MARKER = (
    b"trainedalgorithmicmedia",
    b"compositewithtrainedalgorithmicmedia",
)

# Erzeugernamen, die ausschliesslich in generierten Dateien stehen.
# Photoshop, Lightroom, GIMP und Kamerahersteller gehoeren hier NICHT hin.
#
# Diese Namen zaehlen NUR als Wert eines Werkzeugfeldes (CreatorTool, Software,
# Tool). Eine freie Suche in der Datei waere unsauber: ein Foto von
# Gluehwuermchen mit der Bildbeschreibung "fireflies at night" traegt das Wort
# "firefly" in den Metadaten, ohne je durch eine KI gelaufen zu sein.
ERZEUGER_SIGNATUREN = (
    ("midjourney", "Midjourney"),
    ("dall-e", "DALL-E"),
    ("dall\u00b7e", "DALL-E"),
    ("openai", "OpenAI"),
    ("stable diffusion", "Stable Diffusion"),
    ("stablediffusion", "Stable Diffusion"),
    ("firefly", "Adobe Firefly"),
    ("novelai", "NovelAI"),
    ("leonardo.ai", "Leonardo.Ai"),
    ("ideogram", "Ideogram"),
    ("black forest labs", "FLUX"),
    ("google deepmind", "Google DeepMind"),
)

# Felder, deren WERT das erzeugende Werkzeug benennt.
# Nur Felder, die das WERKZEUG benennen. dc:creator (der Urheber) und
# photoshop:History gehoeren nicht dazu: ein Fotograf namens "Gemini Studios"
# oder eine Bearbeitungsspur waeren sonst ein KI-Nachweis.
WERKZEUG_FELDER = re.compile(
    rb"""(?:xmp:CreatorTool|CreatorTool|tiff:Software|exif:Software|Software)
         \s*(?:=\s*["']|>)([^"'<]{1,160})""",
    re.I | re.X,
)

# Der Parameterblock von Automatic1111 / ComfyUI im PNG-Textchunk.
SD_PARAMETER = re.compile(rb"parameters\x00.{0,4000}?(steps:|sampler:|cfg scale:)", re.I | re.S)

# Kennzeichnungen auf der Seite. Findet sich eine, ist die Pflicht erkennbar
# erfuellt und der Fund faellt auf "info" zurueck.
SEITEN_KENNZEICHNUNG = (
    r"ki[- ]?generiert", r"ki[- ]?erzeugt", r"mit ki erstellt", r"ai[- ]?generated",
    r"generated (by|with) ai", r"k(ue|ü)nstliche[rn]? intelligenz erstellt",
    r"synthetische[rs]? (bild|inhalt|medien)", r"bildquelle:?\s*ki",
)

# C2PA-Manifest, ohne Aussage ueber KI. Nur fuer die interne Notiz.
C2PA_SPUREN = (b"c2pa.claim", b"c2pa.assertions", b"jumbc2pa")


def _absolut(basis: str, quelle: str) -> Optional[str]:
    quelle = (quelle or "").strip()
    if not quelle or quelle.startswith(("data:", "blob:", "javascript:")):
        return None
    try:
        voll = urljoin(basis, quelle)
        return voll if urlparse(voll).scheme in ("http", "https") else None
    except Exception:
        return None


def sammle_bilder(basis_url: str, soup: BeautifulSoup) -> List[str]:
    """Bildquellen der Seite, entdoppelt und in Dokumentreihenfolge."""
    gefunden: List[str] = []
    gesehen: Set[str] = set()

    def merke(quelle: Optional[str]) -> None:
        voll = _absolut(basis_url, quelle or "")
        if voll and voll not in gesehen:
            gesehen.add(voll)
            gefunden.append(voll)

    for tag in soup.find_all(["img", "source"]):
        merke(tag.get("src"))
        merke(tag.get("data-src"))
        # srcset: "bild-480.jpg 480w, bild-960.jpg 960w"
        for satz in (tag.get("srcset") or "").split(","):
            merke(satz.strip().split(" ")[0] if satz.strip() else None)

    for meta in soup.find_all("meta", property=["og:image", "twitter:image"]):
        merke(meta.get("content"))

    ergebnis: List[str] = []
    for u in gefunden:
        if urlparse(u).path.lower().endswith(KEINE_BILDER):
            continue
        ergebnis.append(u)
        # Bildoptimierer liefern eine neu berechnete Datei OHNE Metadaten.
        # Das Original dahinter traegt sie noch, also pruefen wir beide.
        original = _original_hinter_optimierer(u)
        if original and original not in gesehen:
            gesehen.add(original)
            ergebnis.append(original)

    return ergebnis[:MAX_BILDER_PRO_SEITE]


def _original_hinter_optimierer(bild_url: str) -> Optional[str]:
    """
    Holt die Ursprungsdatei aus einer Optimierer-URL.

    Next.js (/_next/image?url=%2Flogo.png) und aehnliche Dienste rechnen das
    Bild neu und werfen dabei genau die Metadaten weg, die wir brauchen. Auf
    complyo.de selbst waren dadurch von drei Bildern nur eines pruefbar.
    """
    try:
        zerlegt = urlparse(bild_url)
        if "/_next/image" not in zerlegt.path and "/cdn-cgi/image" not in zerlegt.path:
            return None
        quelle = parse_qs(zerlegt.query).get("url", [None])[0]
        if not quelle:
            return None
        return _absolut(bild_url, unquote(quelle))
    except Exception:
        return None


async def lade_kopf(url: str, session: Optional[aiohttp.ClientSession]) -> Optional[bytes]:
    """
    Laedt den Dateianfang, moeglichst per Range-Anfrage.

    Umleitungen werden bewusst selbst verfolgt statt von aiohttp: nur so laeuft
    JEDE Station durch validate_url. Mit allow_redirects=True koennte ein
    Angreifer auf seiner eigenen Seite ein Bild einbinden, dessen Server per 302
    auf 169.254.169.254 zeigt, und die Eingangspruefung liefe ins Leere.
    """
    kopf = {"Range": f"bytes=0-{MAX_BYTES - 1}"}
    eigene = session is None
    if eigene:
        session = aiohttp.ClientSession()
    try:
        for _ in range(MAX_UMLEITUNGEN + 1):
            try:
                validate_url(url)
            except SSRFError as e:
                logger.info(f"Bildabruf geblockt ({e}): {url}")
                return None

            async with session.get(
                url, headers=kopf, timeout=aiohttp.ClientTimeout(total=BILD_TIMEOUT),
                allow_redirects=False,
            ) as antwort:
                ziel = antwort.headers.get("Location")
                if antwort.status in (301, 302, 303, 307, 308) and ziel:
                    url = urljoin(url, ziel)
                    continue
                if antwort.status >= 400:
                    return None
                # Endgueltiger Abgleich: nur echte Bilder lesen. Ohne diese
                # Pruefung laedt der Check bei endungslosen URLs auch
                # HTML-Fehlerseiten.
                if not (antwort.content_type or "").lower().startswith("image/"):
                    return None
                # Server ohne Range-Unterstuetzung liefern die ganze Datei; wir
                # brechen nach MAX_BYTES ab, statt sie vollstaendig zu lesen.
                return await antwort.content.read(MAX_BYTES)
        return None
    except Exception as e:
        logger.debug(f"Bild nicht ladbar {url}: {e}")
        return None
    finally:
        if eigene:
            await session.close()


def pruefe_bytes(rohdaten: bytes) -> Optional[Dict[str, Any]]:
    """
    Sucht die Selbstauskunft des Erzeugers.

    Rueckgabe: None, wenn kein Nachweis vorliegt. Sonst ein Dict mit `art`
    (welcher Nachweis), `fundstelle` (der Bytes-Ausschnitt als Beleg) und
    optional `erzeuger`.
    """
    if not rohdaten:
        return None
    klein = rohdaten.lower()

    for marker in IPTC_KI_MARKER:
        pos = klein.find(marker)
        if pos >= 0:
            return {
                "art": "iptc_digitalsourcetype",
                "nachweis": "IPTC DigitalSourceType: trainedAlgorithmicMedia",
                "fundstelle": _ausschnitt(rohdaten, pos, len(marker)),
                "erzeuger": _erzeuger_aus(rohdaten),
            }

    treffer = SD_PARAMETER.search(rohdaten)
    if treffer:
        return {
            "art": "generator_parameter",
            "nachweis": "Parameterblock der Bilderzeugung im PNG-Textchunk",
            "fundstelle": _ausschnitt(rohdaten, treffer.start(), 40),
            "erzeuger": _erzeuger_aus(rohdaten) or "Stable Diffusion (Automatic1111/ComfyUI)",
        }

    werkzeug = _werkzeug_feld(rohdaten)
    if werkzeug:
        wert, name = werkzeug
        return {
            "art": "erzeuger_signatur",
            "nachweis": f"Erzeugendes Werkzeug im Metadatenfeld der Datei: {name}",
            "fundstelle": wert[:160],
            "erzeuger": name,
        }

    return None


def hat_c2pa_ohne_ki_marker(rohdaten: bytes) -> bool:
    """
    C2PA-Manifest vorhanden, aber ohne KI-Marker.

    Das ist der Normalfall bei signierten Kamerafotos (Leica, Sony, Nikon) und
    darf gerade NICHT als KI gemeldet werden.
    """
    if not rohdaten:
        return False
    klein = rohdaten.lower()
    if any(marker in klein for marker in IPTC_KI_MARKER):
        return False
    return any(spur in klein for spur in C2PA_SPUREN)


def _ausschnitt(rohdaten: bytes, pos: int, laenge: int) -> str:
    """Lesbarer Beleg um die Fundstelle herum, damit der Kunde nachsehen kann."""
    start = max(0, pos - 40)
    ende = min(len(rohdaten), pos + laenge + 40)
    text = rohdaten[start:ende].decode("utf-8", errors="replace")
    return re.sub(r"[^\x20-\x7eÀ-ɏ]+", " ", text).strip()[:160]


def _werkzeug_feld(rohdaten: bytes) -> Optional[Tuple[str, str]]:
    """
    Sucht den Erzeuger als WERT eines Werkzeugfeldes.

    Rueckgabe: (Feldwert, erkannter Name) oder None. Ein Treffer irgendwo sonst
    in der Datei zaehlt bewusst nicht, siehe Kommentar bei ERZEUGER_SIGNATUREN.
    """
    for treffer in WERKZEUG_FELDER.finditer(rohdaten):
        wert = treffer.group(1).decode("utf-8", errors="replace").strip()
        klein = wert.lower()
        for signatur, name in ERZEUGER_SIGNATUREN:
            if signatur in klein:
                return wert, name
    return None


def _erzeuger_aus(rohdaten: bytes) -> Optional[str]:
    """Erzeugername fuer die Beschriftung eines bereits belegten Fundes."""
    werkzeug = _werkzeug_feld(rohdaten)
    return werkzeug[1] if werkzeug else None


# ---------------------------------------------------------------------------
# Befundtexte: einmal formuliert, nicht je Zweig wiederholt
# ---------------------------------------------------------------------------
LEGAL_BASIS = "Art. 50 Abs. 4 KI-VO (VO (EU) 2024/1689)"

BESCHREIBUNG_OHNE_HINWEIS = (
    "Die Datei {datei} trägt einen Nachweis, dass sie von einer KI erzeugt wurde "
    "({nachweis}), und auf der Seite ist keine Kennzeichnung erkennbar. "
    "Art. 50 Abs. 4 KI-VO verlangt eine Offenlegung für KI-erzeugte oder "
    "manipulierte Bilder, die reale Personen, Orte oder Ereignisse darstellen "
    "(Deepfake). Prüfen Sie, ob dieses Bild darunter fällt; bei rein dekorativen "
    "Motiven ohne Bezug zur Wirklichkeit greift die Pflicht nicht. Die Pflicht "
    "gilt seit dem 02.08.2026."
)
BESCHREIBUNG_MIT_HINWEIS = (
    "Die Datei {datei} weist sich selbst als KI-erzeugt aus ({nachweis}). Die "
    "Seite enthält einen Hinweis auf KI-Inhalte. Empfehlung: den Hinweis direkt "
    "am Bild führen (Bildunterschrift oder alt-Text), nicht nur im Fließtext."
)
EMPFEHLUNG_OHNE_HINWEIS = (
    "Bild als KI-generiert kennzeichnen, zum Beispiel in der Bildunterschrift "
    "(„KI-generiertes Bild\") oder im alt-Text. Alternativ ein Bild ohne "
    "KI-Ursprung verwenden. Zuständig ist der Betreiber der Website (Deployer)."
)
EMPFEHLUNG_MIT_HINWEIS = (
    "Kennzeichnung unmittelbar beim Bild anbringen, damit sie beim Betrachten "
    "des Bildes sichtbar ist."
)


def _issue(bild_url: str, seiten_url: str, fund: Dict[str, Any], gekennzeichnet: bool) -> Dict[str, Any]:
    """
    Baut den Befund zu EINEM nachgewiesenen Bild.

    Ein Zweig statt zwei: die beiden Faelle unterscheiden sich nur in Schwere,
    Text und Risiko. Rechtsgrundlage, Kategorie und Belegfelder waren vorher
    Wort fuer Wort doppelt und haetten bei jeder Korrektur auseinanderlaufen
    koennen.
    """
    erzeuger = fund.get("erzeuger")
    zusatz = f" ({erzeuger})" if erzeuger else ""
    datei = urlparse(bild_url).path.rsplit("/", 1)[-1] or bild_url
    texte = {"datei": datei, "nachweis": fund["nachweis"]}

    return {
        "category": "ai_act_transparency",
        "severity": "info" if gekennzeichnet else "warning",
        "title": (
            f"KI-generiertes Bild nachgewiesen{zusatz}: {datei}" if gekennzeichnet
            else f"KI-generiertes Bild ohne Kennzeichnung{zusatz}: {datei}"
        ),
        "description": (
            BESCHREIBUNG_MIT_HINWEIS if gekennzeichnet else BESCHREIBUNG_OHNE_HINWEIS
        ).format(**texte),
        "recommendation": EMPFEHLUNG_MIT_HINWEIS if gekennzeichnet else EMPFEHLUNG_OHNE_HINWEIS,
        # Kein Risiko, wo die Pflicht erkennbar erfuellt ist.
        "risk_euro": 0 if gekennzeichnet else 5000,
        "legal_basis": LEGAL_BASIS,
        "auto_fixable": False,
        "is_missing": False,
        # Der Beleg gehoert an den Befund: ohne Fundstelle kann der Kunde nicht
        # nachvollziehen, warum sein Bild als KI-erzeugt gilt.
        "metadata": {
            "check": "ki_bild_nachweis",
            "image_url": bild_url,
            "nachweis_art": fund["art"],
            "fundstelle": fund["fundstelle"],
            "erzeuger": erzeuger,
            "page_url": seiten_url,
        },
    }


# ---------------------------------------------------------------------------
# Einstiegspunkt fuer den Scanner
# ---------------------------------------------------------------------------
async def check_ki_bild_nachweis(
    url: str,
    soup: BeautifulSoup,
    session: Optional[aiohttp.ClientSession] = None,
    bereits_geprueft: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Meldet Bilder, die sich selbst als KI-erzeugt ausweisen und auf der Seite
    nicht gekennzeichnet sind.

    bereits_geprueft: URL-Menge, die ueber mehrere Seiten hinweg mitgefuehrt
    wird. Dasselbe Logo auf zehn Unterseiten ist ein Befund, nicht zehn.
    Bewertet wird ein Bild dadurch anhand der Seite, auf der es zuerst
    auftaucht: liegt es dort gekennzeichnet und im Blog ungekennzeichnet, zaehlt
    die erste Seite. Der Preis fuer diese Entdopplung ist bewusst gewaehlt.
    """
    issues: List[Dict[str, Any]] = []
    try:
        # --- Bilder der Seite bestimmen, seitenuebergreifend entdoppelt ---
        bilder = sammle_bilder(url, soup)
        if bereits_geprueft is not None:
            bilder = [b for b in bilder if b not in bereits_geprueft]
            # Sofort vormerken, damit parallel laufende Unterseiten dasselbe Bild
            # nicht doppelt melden. Nicht erreichbare Bilder werden unten wieder
            # freigegeben, sonst gilt ein einmaliger 503 als "geprueft".
            bereits_geprueft.update(bilder)
        if not bilder:
            return issues

        # --- Kennzeichnet die Seite KI-Inhalte ueberhaupt? ---
        seitentext = soup.get_text(" ", strip=True).lower()[:40000]
        gekennzeichnet = any(re.search(p, seitentext) for p in SEITEN_KENNZEICHNUNG)

        # --- Dateikoepfe laden, gedrosselt und mit hartem Zeitbudget ---
        semaphor = asyncio.Semaphore(PARALLEL)

        async def eines(bild_url: str) -> Tuple[str, Optional[bytes]]:
            async with semaphor:
                return bild_url, await lade_kopf(bild_url, session)

        try:
            ergebnisse = await asyncio.wait_for(
                asyncio.gather(*[eines(b) for b in bilder], return_exceptions=True),
                timeout=SEITEN_ZEITBUDGET,
            )
        except asyncio.TimeoutError:
            if bereits_geprueft is not None:
                bereits_geprueft.difference_update(bilder)
            logger.info(
                f"KI-Bildnachweis {url}: Zeitbudget von {SEITEN_ZEITBUDGET}s "
                f"erschoepft, Seite uebersprungen"
            )
            return issues

        # --- Auswerten: nur belegte Funde werden zu Befunden ---
        geprueft = 0
        c2pa_ohne_ki = 0
        for erg in ergebnisse:
            if isinstance(erg, Exception):
                continue
            bild_url, rohdaten = erg
            if rohdaten is None:
                # Nicht erreichbar: Vormerkung zuruecknehmen, damit eine spaetere
                # Seite dasselbe Bild erneut versuchen darf.
                if bereits_geprueft is not None:
                    bereits_geprueft.discard(bild_url)
                continue
            geprueft += 1

            fund = pruefe_bytes(rohdaten)
            if not fund:
                # Nur hier interessant: Herkunftsdaten ohne KI-Aussage, also der
                # signierte Kamerafall. Zaehlt fuers Log, erzeugt keinen Befund.
                if hat_c2pa_ohne_ki_marker(rohdaten):
                    c2pa_ohne_ki += 1
                continue

            issues.append(_issue(bild_url, url, fund, gekennzeichnet))

        logger.info(
            f"KI-Bildnachweis {url}: {geprueft}/{len(bilder)} Bilder gelesen, "
            f"{len(issues)} mit Nachweis, {c2pa_ohne_ki} mit C2PA ohne KI-Marker"
        )
    except Exception as e:
        logger.warning(f"KI-Bildnachweis fehlgeschlagen (non-fatal): {e}")
    return issues
