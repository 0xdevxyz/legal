# -*- coding: utf-8 -*-
"""
Weitere Wege zur Rechtsseite, wenn kein Link da ist: Pfadvarianten und Sitemap.

Die Seiten der Bestandskunden liegen unter `/impressum.html`, `/datenschutz.html`,
`/datenschutzerklaerung/`, `/rechtliches/...`. Der alte Rueckfall kannte nur
`/impressum` und `/datenschutz`. Auf den 24 Bestandsseiten vom 08.10.2026 braucht
ihn keine (jede Rechtsseite war verlinkt): die Tests sichern die Faelle, die der
Bestand nicht enthaelt, und die Gegenproben, damit mehr Wege nicht mehr
Fehltreffer heissen.
"""
import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.checks import rechtsseiten_wege as w

BASIS = "https://beispiel.test"

IMPRESSUM = ("<html><body><h1>Impressum</h1><p>Angaben gemäß § 5 DDG: Muster GmbH, Musterweg 1, "
             "04109 Leipzig, E-Mail: info@beispiel.test</p></body></html>")
KEIN_IMPRESSUM = "<html><body><h1>Willkommen</h1><p>" + "Wir freuen uns auf Sie. " * 30 + "</p></body></html>"


def sieht_aus_wie_impressum(text):
    low = text.lower()
    return "impressum" in low and "@" in low


class Seiten:
    """Ersetzt den Abruf: Adresse -> (Status, Text); alles andere 404."""

    def __init__(self, seiten, verzoegerung=0.0):
        self.seiten, self.abgerufen, self.verzoegerung = seiten, [], verzoegerung

    async def __call__(self, adresse):
        self.abgerufen.append(adresse)
        if self.verzoegerung:
            await asyncio.sleep(self.verzoegerung)
        if adresse in self.seiten:
            return 200, self.seiten[adresse]
        return 404, ""


def suche(seiten, art="impressum", bewerte=sieht_aus_wie_impressum, verzoegerung=0.0):
    hole = Seiten(seiten, verzoegerung)
    return asyncio.run(w.finde_rechtsseite(BASIS + "/", art, hole, bewerte)), hole


def sitemap(*pfade):
    eintraege = "".join(f"<url><loc>{BASIS}{p}</loc></url>" for p in pfade)
    return f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{eintraege}</urlset>'


# --- Pfadvarianten ------------------------------------------------------------------

@pytest.mark.parametrize("pfad", ["/impressum", "/impressum.html", "/impressum.php", "/rechtliches/impressum",
                                  "/de/impressum", "/anbieterkennzeichnung"])
def test_impressum_unter_ueblichen_pfaden(pfad):
    fund, _ = suche({BASIS + pfad: IMPRESSUM})
    assert fund == BASIS + pfad


@pytest.mark.parametrize("pfad", ["/datenschutz", "/datenschutz.html", "/datenschutzerklaerung/",
                                  "/datenschutzerklaerung.html", "/rechtliches/datenschutz"])
def test_datenschutz_unter_ueblichen_pfaden(pfad):
    seite = "<html><body><h1>Datenschutz</h1><p>Datenschutzerklärung</p></body></html>"
    fund, _ = suche({BASIS + pfad: seite}, art="datenschutz", bewerte=lambda t: "datenschutz" in t.lower())
    assert fund == BASIS + pfad


def test_nichts_da_nichts_gefunden():
    fund, _ = suche({})
    assert fund is None


# --- Soft-404 und Catch-all ---------------------------------------------------------

def test_200_ohne_impressum_ist_kein_fund():
    fund, _ = suche({BASIS + "/impressum": KEIN_IMPRESSUM})
    assert fund is None


def test_catch_all_domain_liefert_fuer_jeden_pfad_dieselbe_seite():
    """Die Seite enthaelt zufaellig 'Impressum' und eine Adresse, ist aber nur der Platzhalter."""
    platzhalter = ("<html><body>" + "Bald mehr. " * 40 + "Impressum: info@beispiel.test</body></html>")
    seiten = {BASIS + "/__complyo_probe_404__": platzhalter}
    seiten.update({BASIS + p: platzhalter for p in w.PFADE["impressum"]})
    fund, _ = suche(seiten)
    assert fund is None, "Eine Catch-all-Seite gilt nicht als Impressum."


def test_echtes_impressum_auf_catch_all_domain_wird_trotzdem_gefunden():
    platzhalter = "<html><body>" + "Bald mehr. " * 40 + "</body></html>"
    seiten = {BASIS + "/__complyo_probe_404__": platzhalter, BASIS + "/impressum.html": IMPRESSUM}
    fund, _ = suche(seiten)
    assert fund == BASIS + "/impressum.html"


# --- Sitemap ------------------------------------------------------------------------

def test_sitemap_nennt_die_seite_unter_unueblichem_pfad():
    seiten = {BASIS + "/sitemap.xml": sitemap("/", "/leistungen", "/rechtliches/impressum-angaben"),
              BASIS + "/rechtliches/impressum-angaben": IMPRESSUM}
    fund, _ = suche(seiten)
    assert fund == BASIS + "/rechtliches/impressum-angaben"


def test_sitemap_blogartikel_und_werkzeuge_werden_nicht_abgerufen():
    seiten = {BASIS + "/sitemap.xml": sitemap("/blog/impressumspflicht-fuer-handwerker",
                                              "/tools/impressum-generator", "/ratgeber/impressum-check"),
              BASIS + "/blog/impressumspflicht-fuer-handwerker": IMPRESSUM}
    fund, hole = suche(seiten)
    assert fund is None
    assert not any("/blog/" in a or "generator" in a or "/ratgeber/" in a for a in hole.abgerufen), (
        "Der Ratgeber ueber Impressumspflichten ist nicht das Impressum.")


def test_sitemap_fremder_host_wird_ignoriert():
    xml = '<urlset><url><loc>https://fremd.test/impressum</loc></url></urlset>'
    assert w.sitemap_kandidaten(xml, BASIS, "impressum") == []


def test_sitemap_index_folgt_nur_der_seiten_sitemap():
    index = (f'<sitemapindex><sitemap><loc>{BASIS}/post-sitemap.xml</loc></sitemap>'
             f'<sitemap><loc>{BASIS}/page-sitemap.xml</loc></sitemap></sitemapindex>')
    seiten = {BASIS + "/sitemap_index.xml": index,
              BASIS + "/page-sitemap.xml": sitemap("/rechtliches/impressum-hinweise"),
              BASIS + "/rechtliches/impressum-hinweise": IMPRESSUM}
    fund, hole = suche(seiten)
    assert fund == BASIS + "/rechtliches/impressum-hinweise"
    assert BASIS + "/post-sitemap.xml" not in hole.abgerufen


def test_sitemap_kandidaten_kuerzere_pfade_zuerst_und_begrenzt():
    xml = sitemap("/a/b/c/impressum-lang", "/impressum", "/x/impressum", "/y/z/impressum", "/q/r/s/t/impressum")
    k = w.sitemap_kandidaten(xml, BASIS, "impressum", limit=3)
    assert k[0] == BASIS + "/impressum" and len(k) == 3


def test_sitemap_xml_entities_werden_aufgeloest():
    xml = f"<urlset><url><loc>{BASIS}/impressum?a=1&amp;b=2</loc></url></urlset>"
    assert w.sitemap_kandidaten(xml, BASIS, "impressum") == [BASIS + "/impressum?a=1&b=2"]


# --- Laufzeit -----------------------------------------------------------------------

def test_die_wege_laufen_parallel_nicht_nacheinander():
    """Eine Seite ohne Rechtsseiten darf nicht laenger brauchen als vorher: ~7 Abrufe nacheinander."""
    start = time.monotonic()
    fund, hole = suche({}, verzoegerung=0.1)
    dauer = time.monotonic() - start
    assert fund is None and len(hole.abgerufen) > 20
    assert dauer < 1.5, f"{len(hole.abgerufen)} Abrufe in {dauer:.1f} s: nicht parallel"
