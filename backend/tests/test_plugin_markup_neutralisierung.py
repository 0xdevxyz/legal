"""
Beide Plugins neutralisieren fest eingebaute Tracker im Markup, mit denselben Mustern.

Befund 09./10.11.2026 (reinhardt.coffee, loqal.io): Der Vorlade-Scanner des
Browsers holt statische `<script src>`, `<iframe src>` und Google-Fonts-`<link>`,
bevor der Blocker im Browser greift. Nur Markup ohne src/href verhindert den
Abruf vor der Einwilligung. WordPress kann das seit 2.7.0, Joomla seit 2.2.0.

Die Musterlisten stehen in zwei PHP-Dateien. Damit sie nicht auseinanderlaufen,
vergleicht dieser Waechter sie. Die PHP-Logik selbst prueft
tests/php/joomla_markup_probe.php (braucht PHP-CLI, laeuft nicht in dieser Suite).
"""

import os
import re

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BACKEND)
WP = os.path.join(REPO, "wordpress-plugin", "complyo-compliance")
JOOMLA = os.path.join(REPO, "joomla-plugin", "plg_system_complyo")


def _lies(*teile):
    pfad = os.path.join(*teile)
    if not os.path.exists(pfad):
        pytest.skip(f"{pfad} nicht eingehaengt (Test braucht das ganze Repo, siehe scripts/tests-lokal.sh)")
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


def _muster(quelle: str, funktion: str) -> set:
    """Alle Regex-Literale im Rumpf einer PHP-Funktion."""
    start = quelle.index("function " + funktion)
    ende = quelle.index("\n    }\n", start)
    rumpf = quelle[start:ende]
    gefunden = set(re.findall(r"'([#/].+?[#/]i)',", rumpf))
    assert len(gefunden) >= 3, f"In {funktion} wurden nur {len(gefunden)} Muster gefunden: Waechter liest falsch."
    return gefunden


@pytest.mark.parametrize("wp_funktion, joomla_funktion", [
    ("external_script_patterns", "scriptPatterns"),
    ("external_iframe_patterns", "iframePatterns"),
    ("patterns", "inlinePatterns"),
])
def test_joomla_und_wordpress_fuehren_dieselben_muster(wp_funktion, joomla_funktion):
    wp = _lies(WP, "includes", "class-complyo-inline-blocker.php")
    joomla = _lies(JOOMLA, "ComplyoMarkup.php")
    a, b = _muster(wp, wp_funktion), _muster(joomla, joomla_funktion)
    assert a == b, (
        f"Muster laufen auseinander. Nur WordPress: {sorted(a - b)}. Nur Joomla: {sorted(b - a)}."
    )


def test_joomla_plugin_ruft_die_neutralisierung_vor_dem_banner():
    quelle = _lies(JOOMLA, "complyo.php")
    assert "ComplyoMarkup::rewrite(" in quelle
    rumpf = quelle[quelle.index("function onAfterRender"):]
    assert rumpf.index("ComplyoMarkup::rewrite(") < rumpf.index("strripos($body, '</body>')"), (
        "Die Neutralisierung muss vor dem Einhaengen der eigenen Skripte laufen."
    )
    assert "enable_markup_blocker', 1)" in quelle, "Die Neutralisierung muss ohne Zutun an sein."


def test_joomla_manifest_nennt_jede_php_datei():
    manifest = _lies(JOOMLA, "complyo.xml")
    for name in os.listdir(JOOMLA):
        if name.endswith(".php"):
            assert f">{name}</filename>" in manifest, (
                f"{name} fehlt im Manifest: Joomla installiert die Datei dann nicht, "
                "und das Plugin bricht beim ersten Seitenaufruf."
            )
    assert 'name="enable_markup_blocker"' in manifest


def test_wordpress_neuinstallation_startet_mit_neutralisierung():
    quelle = _lies(WP, "complyo-compliance.php")
    block = quelle[quelle.index("public function activate()"):quelle.index("public function deactivate()")]
    assert "update_option(COMPLYO_OPTION_INLINE_BLOCKER, '1')" in block, (
        "Eine Neuinstallation ohne Neutralisierung im Markup laedt fest eingebaute "
        "Tracker vor der Einwilligung."
    )


def test_anleitung_im_dashboard_nutzt_die_attribute_die_der_blocker_freigibt():
    """Ein Beispiel in der Einbau-Anleitung, das der Blocker nie freigibt, waere
    schlimmer als keins: der Kunde baut es ein und sein Video kommt nie wieder."""
    blocker = _lies(BACKEND, "public", "cookie-blocker.js")
    for selektor in ('script[type="text/plain"][data-complyo-consent]',
                     'iframe[data-complyo-src][data-complyo-blocked="true"]',
                     'link[data-complyo-href][data-complyo-blocked="true"]'):
        assert selektor in blocker, f"Der Blocker sammelt {selektor} nicht mehr ein: Anleitung und Plugins anpassen."

    dashboard = os.path.abspath(os.getenv("COMPLYO_DASHBOARD_SRC")
                                or os.path.join(REPO, "dashboard-react", "src"))
    hinweis = _lies(dashboard, "components", "cookie-compliance", "TrackerUmschreiben.tsx")
    assert 'type="text/plain" data-complyo-consent="analytics"' in hinweis
    iframe = hinweis[hinweis.index("<iframe"):hinweis.index("</iframe>")]
    assert "data-complyo-src=" in iframe and 'data-complyo-blocked="true"' in iframe and " src=" not in iframe
    link = hinweis[hinweis.index("<link rel"):hinweis.index("`;", hinweis.index("<link rel"))]
    assert "data-complyo-href=" in link and 'data-complyo-blocked="true"' in link and " href=" not in link

    for datei in ("IntegrationGuide.tsx", "CookieSetupWizard.tsx"):
        assert "<TrackerUmschreiben" in _lies(dashboard, "components", "cookie-compliance", datei), (
            f"{datei} zeigt den Hinweis zu fest eingebauten Trackern nicht mehr."
        )
