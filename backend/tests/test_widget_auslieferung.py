"""
Waechter: was auf der Kundenseite ankommt, muss auch die Reparaturen enthalten.

Beim Ausrollen aufgefallen und beinahe uebersehen: `accessibility-v6.js` holt
ausschliesslich Alt-Texte ueber einen eigenen Endpunkt. Kontrast-, Struktur-
und Linkname-Reparaturen laufen ueber das Fix-Manifest, das nur
`a11y_remediation.js` liest — und die liegt unter einer ANDEREN Adresse
(`/api/widgets/a11y-fixes.js`).

Auf allen Kundenseiten steht `accessibility.js`. Alles ausser Alt-Texten
erreichte damit niemanden, ohne dass es auffiel: die Fixes waren gebaut,
verifiziert, freigegeben, im Manifest — und liefen ins Leere.

Diese Datei haelt fest, dass beide Teile aus derselben Adresse kommen.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


class TestAuslieferung:
    def test_accessibility_js_haengt_die_remediation_an(self):
        src = _lese("widget_routes.py")
        block = src[src.index("async def serve_accessibility_widget"):]
        block = block[:block.index("@router.get", 10)]
        assert "a11y_remediation.js" in block
        assert "content +=" in block

    def test_der_grund_steht_dabei(self):
        """Sonst entfernt es jemand als vermeintliche Doppelung."""
        src = _lese("widget_routes.py")
        block = src[src.index("async def serve_accessibility_widget"):]
        assert "Fix-Manifest" in block[:3000]

    def test_fehlende_datei_wird_nicht_verschwiegen(self):
        src = _lese("widget_routes.py")
        block = src[src.index("async def serve_accessibility_widget"):]
        assert "warning" in block[:3500]


class TestBeideTeileTunWasSieSollen:
    def test_v6_bringt_die_bedienleiste(self):
        v6 = _lese("widgets", "accessibility-v6.js")
        assert "loadAndApplyAltTexts" in v6

    def test_remediation_bringt_das_manifest(self):
        rem = _lese("widgets", "a11y_remediation.js")
        assert "fix-manifest" in rem
        for teil in ("cssRules", "strukturFixes", "linkFixes"):
            assert teil in rem, teil

    def test_remediation_findet_ihre_konfiguration_auch_ohne_eigenes_tag(self):
        """
        Zusammengehaengt laeuft sie unter dem accessibility.js-Tag. Ohne diesen
        Rueckfall auf `script[data-site-id]` wuerde sie dort abbrechen.
        """
        rem = _lese("widgets", "a11y_remediation.js")
        assert "script[data-site-id]" in rem

    def test_alt_texte_werden_nie_ueberschrieben(self):
        """
        Beide Wege setzen Alt-Texte. Das ist nur unbedenklich, solange keiner
        etwas Vorhandenes ueberschreibt — wer zuerst kommt, gewinnt.
        """
        rem = _lese("widgets", "a11y_remediation.js")
        assert "if (cur && cur.trim() !== '') continue" in rem
        v6 = _lese("widgets", "accessibility-v6.js")
        assert "if (img && !img.alt)" in v6


# ---------------------------------------------------------------------------
# Nachtrag 14.09.2026: die Adresse im Kundensnippet muss aufloesen.
#
# Der Einrichtungsassistent im Dashboard (CookieSetupWizard) gab Kunden zum
# Kopieren ein Snippet mit cdn.complyo.de/cookie-banner.js. Dieser Host hat
# keinen DNS-Eintrag, hatte also nie einen. Wer das Snippet einbaute, bekam
# kein Banner, keine Blockierung und keine Einwilligungsprotokolle - und hielt
# sich fuer abgedeckt. Genau die Klasse Fehler, die diese Datei bewacht: gebaut,
# freigegeben, und auf der Kundenseite kommt nichts an.
#
# Ausgeliefert wird ueber api.complyo.de/api/widgets/..., so wie es die
# Integrationsanleitung, die Landing und die CMS-Doku schon sagten. Der Wizard
# war die einzige abweichende Stelle.
TOTE_HOSTS = ("cdn.complyo.de", "cdn.complyo.tech")

_DASHBOARD_SRC = os.path.abspath(
    os.getenv("COMPLYO_DASHBOARD_SRC")
    or os.path.join(_BACKEND, "..", "dashboard-react", "src")
)


def _quelldateien(wurzel, endungen):
    for ordner, _, namen in os.walk(wurzel):
        if "node_modules" in ordner or "/.next" in ordner:
            continue
        for name in namen:
            if name.endswith(endungen) and ".bak" not in name:
                yield os.path.join(ordner, name)


class TestSnippetAdresse:
    def test_kein_kundensnippet_zeigt_auf_einen_host_ohne_dns(self):
        """Im Dashboard darf kein cdn.complyo.* stehen: beide loesen nicht auf."""
        import pytest

        if not os.path.isdir(_DASHBOARD_SRC):
            pytest.skip(
                f"dashboard-react/src nicht gefunden unter {_DASHBOARD_SRC}. "
                "Diese Pruefung braucht das Repo-Wurzelverzeichnis im Container "
                "(-v $(pwd):/repo -w /repo/backend), siehe scripts/tests-lokal.sh."
            )
        funde = []
        for pfad in _quelldateien(_DASHBOARD_SRC, (".tsx", ".ts")):
            with open(pfad, encoding="utf-8") as fh:
                for nr, zeile in enumerate(fh, 1):
                    # Kommentare ausnehmen: der Grund, WARUM der Host nicht mehr
                    # benutzt wird, muss im Code stehen duerfen. Sonst entfernt
                    # ihn jemand als vermeintliche Doppelung und baut es zurueck.
                    if zeile.lstrip().startswith(("//", "*", "/*")):
                        continue
                    for host in TOTE_HOSTS:
                        if host in zeile:
                            kurz = os.path.relpath(pfad, _DASHBOARD_SRC)
                            funde.append(f"{kurz}:{nr}: {zeile.strip()[:100]}")
        assert not funde, (
            "Host ohne DNS-Eintrag im Dashboard:\n  "
            + "\n  ".join(funde)
            + "\n\nAusgeliefert wird ueber https://api.complyo.de/api/widgets/..."
        )

    def test_backend_gibt_keinen_toten_host_aus(self):
        funde = []
        for pfad in _quelldateien(_BACKEND, (".py",)):
            if os.sep + "tests" + os.sep in pfad:
                continue
            with open(pfad, encoding="utf-8") as fh:
                for nr, zeile in enumerate(fh, 1):
                    if zeile.lstrip().startswith("#"):
                        continue
                    for host in TOTE_HOSTS:
                        if host in zeile:
                            kurz = os.path.relpath(pfad, _BACKEND)
                            funde.append(f"{kurz}:{nr}: {zeile.strip()[:100]}")
        assert not funde, (
            "Host ohne DNS-Eintrag in einer Antwort des Backends:\n  "
            + "\n  ".join(funde)
        )

    def test_assistent_und_anleitung_nennen_dieselbe_adresse(self):
        """Zwei Wege zur Einrichtung, ein Snippet. Sonst driften sie wieder."""
        import pytest

        wizard = os.path.join(
            _DASHBOARD_SRC, "components", "cookie-compliance", "CookieSetupWizard.tsx"
        )
        anleitung = os.path.join(
            _DASHBOARD_SRC, "components", "cookie-compliance", "IntegrationGuide.tsx"
        )
        if not (os.path.exists(wizard) and os.path.exists(anleitung)):
            pytest.skip(f"Dashboard-Quellen nicht gefunden unter {_DASHBOARD_SRC}")
        for pfad in (wizard, anleitung):
            with open(pfad, encoding="utf-8") as fh:
                src = fh.read()
            name = os.path.basename(pfad)
            assert "/api/widgets/cookie-compliance.js" in src, f"{name}: Banner fehlt"
            assert "/public/cookie-blocker.js" in src, f"{name}: Blocker fehlt"
            assert src.index("/public/cookie-blocker.js") < src.index(
                "/api/widgets/cookie-compliance.js"
            ), (
                f"{name}: Der Blocker muss VOR dem Banner stehen, sonst laufen "
                "fremde Skripte vor der Einwilligung an."
            )
