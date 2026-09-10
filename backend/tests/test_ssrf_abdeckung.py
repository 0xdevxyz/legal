# -*- coding: utf-8 -*-
"""
Die SSRF-Schranke gilt fuer ALLE Abrufe, nicht nur fuer den Hauptweg.

Hintergrund: der Sicherheitsreview vom 31.08.2026 hat `sicherer_abruf` gebaut
und vier Stellen umgezogen. Die Messung in der Nachtschicht vom 09.09.2026 ergab:
von 27 Abrufstellen mit fremdbestimmter Adresse hatten 21 keinerlei Pruefung.
Die Schranke stand, aber fast nichts ging hindurch.

Ein gruener Test ueber den Hauptweg allein haette das nie gezeigt. Deshalb
prueft dieser Test die ABDECKUNG: keine Datei im Scanpfad darf sich eine
ungepruefte aiohttp-Sitzung bauen.
"""

import ast
import os

import pytest

from compliance_engine.sicherer_abruf import sichere_session, GepruefterConnector
from ssrf_protection import SSRFError, validate_url, pruefe_adresse

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Jede Datei, die Adressen holt, die aus einer fremden Seite stammen koennen.
SCANPFAD = [
    "website_crawler.py",
    "website_routes.py",
    "post_deploy_verifier.py",
    "accessibility_post_scan_processor.py",
    "accessibility_patch_generator.py",
    "widget_routes.py",
    "cookie_compliance_routes.py",
    "cookie_scanner_service.py",
    "cronjobs/website_monitor.py",
    "compliance_engine/browser_renderer.py",
    "compliance_engine/page_discovery.py",
    "compliance_engine/quick_scanner.py",
    "compliance_engine/scanner.py",
    "compliance_engine/ai_alt_text_generator.py",
    "compliance_engine/checks/impressum_check.py",
    "compliance_engine/checks/agb_check.py",
    "compliance_engine/checks/barrierefreiheit_check.py",
    "compliance_engine/checks/datenschutz_check.py",
    "compliance_engine/checks/shop_check.py",
]

# Diese Dateien sprechen ausschliesslich mit festen Adressen (OpenRouter,
# GitHub, EUR-Lex, Slack). Sie stehen hier, damit die Ausnahme benannt ist und
# nicht stillschweigend gilt.
FESTE_ADRESSEN = {
    "ai_review_engine.py", "ai_document_generator.py", "legal_text_generator.py",
    "eulex_service.py", "public_routes.py", "compliance_engine/hybrid_validator.py",
    "compliance_engine/patch_service.py", "ai_fix_engine/intelligent_analyzer.py",
    "ai_fix_engine/unified_fix_engine.py", "git_service/git_service.py",
    "cronjobs/tcf_gvl_sync.py", "cronjobs/knowledge_updater.py",
    "cronjobs/betriebswaechter.py", "knowledge/knowledge_ingestion_service.py",
}


def _sitzungen(pfad):
    """Alle Stellen, die sich eine rohe aiohttp-Sitzung bauen."""
    quelle = open(pfad, encoding="utf-8").read()
    baum = ast.parse(quelle)
    treffer = []
    for knoten in ast.walk(baum):
        if not isinstance(knoten, ast.Call):
            continue
        f = knoten.func
        if isinstance(f, ast.Attribute) and f.attr == "ClientSession":
            treffer.append(knoten.lineno)
    return treffer


@pytest.mark.parametrize("rel", SCANPFAD)
def test_scanpfad_baut_keine_ungepruefte_sitzung(rel):
    pfad = os.path.join(BACKEND, rel)
    assert os.path.exists(pfad), f"{rel} fehlt — Liste veraltet?"
    roh = _sitzungen(pfad)
    assert not roh, (
        f"{rel} baut in Zeile(n) {roh} eine rohe aiohttp.ClientSession. "
        "Im Scanpfad gilt sichere_session() — sonst folgt aiohttp Umleitungen "
        "in interne Adressen, bevor sie jemand pruefen kann."
    )


def test_sichere_session_nutzt_den_pruefenden_connector():
    """Der Schutz haengt am Connector; eine Sitzung ohne ihn ist wirkungslos."""
    import asyncio

    async def lauf():
        sitzung = sichere_session()
        try:
            assert isinstance(sitzung.connector, GepruefterConnector)
        finally:
            await sitzung.close()

    asyncio.run(lauf())


@pytest.mark.parametrize("ziel", [
    "http://127.0.0.1:8002/health",
    "http://[::1]:8002/",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.1/",
    "http://192.168.1.1/",
])
def test_verbindung_in_interne_adressen_wird_abgelehnt(ziel):
    """
    Der entscheidende Fall: die Adresse steht als IP direkt in der URL. Genau so
    sieht ein Umleitungsziel aus, das eine gepruefte Seite setzt.
    """
    import asyncio
    import aiohttp

    async def lauf():
        async with sichere_session() as s:
            with pytest.raises(SSRFError):
                async with s.get(ziel, timeout=aiohttp.ClientTimeout(total=5)):
                    pass

    asyncio.run(lauf())


@pytest.mark.parametrize("adresse", [
    "255.255.255.255",   # Broadcast
    "224.0.0.1",         # Multicast
    "0.0.0.0",           # unspezifiziert
    "::ffff:127.0.0.1",  # IPv4 in IPv6-Kleid
    "198.18.0.1",        # Messbereich
])
def test_adresspruefer_kennt_die_randfaelle(adresse):
    with pytest.raises(SSRFError):
        pruefe_adresse(adresse)


def test_oeffentliche_adresse_bleibt_erlaubt():
    """Die Schranke darf den eigentlichen Zweck nicht erschlagen."""
    pruefe_adresse("93.184.216.34")   # example.com
    assert validate_url("https://complyo.de/impressum").startswith("https://")
