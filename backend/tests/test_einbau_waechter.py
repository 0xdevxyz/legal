"""
Einbau-Waechter (18.09.2026): meldet freigegebene Reparaturen, deren Seite
das Widget gar nicht einbindet.

Anlass: panoart360.de und osteopathie-limbach.de fuehrten seit August
freigegebene dokumentweite Fixes in der Datenbank und im Manifest. Im
Browser gemessen erreichte keine einzige ihre Seite, weil dort nie ein
complyo-Skript eingebaut war. Der vorhandene Wirkungs-Herzschlag konnte das
nicht finden: er vermisst Meldungen, die frueher kamen.

Geprueft wird hier die Entscheidungslogik, nicht die Datenbank. Die Abfrage
selbst laeuft nur produktiv.
"""
import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MIT_WIDGET = (
    '<html><body><p>Inhalt</p>'
    '<script src="https://api.complyo.de/api/widgets/accessibility.js" '
    'data-site-id="panoart360-de" data-auto-fix="true" async></script>'
    '</body></html>'
)
OHNE_WIDGET = '<html><body><p>Inhalt</p></body></html>'
FREMDE_KENNUNG = MIT_WIDGET.replace('panoart360-de', 'spedition-mahn-de')

# So sieht der Einbau aus, wenn eine Next.js-Seite ihn ueber next/script
# vornimmt: die Adresse steht als preload-Link, die Kennung nur maskiert in
# der RSC-Nutzlast. Genau daran meldete der Waechter beim ersten Lauf gegen
# die Produktion einen Ausfall auf complyo.de, den es nicht gab.
NEXT_MASKIERT = (
    '<html><head><link rel="preload" '
    'href="https://api.complyo.de/api/widgets/accessibility.js?version=6" '
    'as="script"/></head><body><script>self.__next_f.push([1,'
    '"...\\"data-site-id\\":\\"complyo-de\\",\\"data-auto-fix\\":\\"true\\"..."'
    '])</script></body></html>'
)


@pytest.fixture()
def waechter(tmp_path, monkeypatch):
    monkeypatch.setenv("WAECHTER_STATE_PFAD", str(tmp_path / "state.json"))
    import cronjobs.betriebswaechter as m
    importlib.reload(m)
    return m


class TestEinbauBewertung:
    def test_seite_ohne_widget_ist_befund(self, waechter):
        text, grund = waechter.bewerte_einbau(
            "panoart360-de", "https://panoart360.de", 200, OHNE_WIDGET)
        assert grund is None
        assert text and "panoart360-de" in text
        assert "erreichen die Seite nie" in text

    def test_seite_mit_passendem_widget_ist_still(self, waechter):
        assert waechter.bewerte_einbau(
            "panoart360-de", "https://panoart360.de", 200, MIT_WIDGET) == (None, None)

    def test_fremde_kennung_ist_befund(self, waechter):
        """Das haeufigste Copy-Paste-Versehen: Schnipsel der Nachbarsite
        uebernommen. Das Skript laedt, das Manifest ist ein fremdes."""
        text, grund = waechter.bewerte_einbau(
            "panoart360-de", "https://panoart360.de", 200, FREMDE_KENNUNG)
        assert grund is None
        assert text and "data-site-id" in text

    def test_einfache_anfuehrungszeichen_zaehlen_auch(self, waechter):
        html = MIT_WIDGET.replace('data-site-id="panoart360-de"',
                                  "data-site-id='panoart360-de'")
        assert waechter.bewerte_einbau(
            "panoart360-de", "https://panoart360.de", 200, html) == (None, None)

    def test_maskierte_kennung_aus_next_zaehlt_auch(self, waechter):
        """Sonst meldet der Waechter jede Next.js-Seite als Ausfall: dort
        steht die Kennung nicht als Attribut, sondern maskiert in der
        RSC-Nutzlast. Ein Waechter, der falsch Alarm schlaegt, wird
        abgeschaltet und bewacht dann gar nichts mehr."""
        assert waechter.bewerte_einbau(
            "complyo-de", "https://complyo.de", 200, NEXT_MASKIERT) == (None, None)

    def test_naehe_zaehlt_nur_direkt_hinter_dem_attribut(self, waechter):
        """Die Kennung irgendwo auf der Seite (im Impressum, in einem Link)
        darf nicht als Einbau durchgehen."""
        html = OHNE_WIDGET.replace(
            "<p>Inhalt</p>",
            '<p>panoart360-de</p>'
            '<script src="https://api.complyo.de/api/widgets/accessibility.js" '
            'data-site-id="spedition-mahn-de"></script>')
        text, _ = waechter.bewerte_einbau(
            "panoart360-de", "https://panoart360.de", 200, html)
        assert text and "data-site-id" in text

    def test_unerreichbare_seite_ist_kein_einbaubefund(self, waechter):
        """Sonst meldet der Waechter bei jedem Netzhaenger einen Ausfall,
        den es nicht gibt, und wird zum Rauschen."""
        text, grund = waechter.bewerte_einbau(
            "panoart360-de", "https://panoart360.de", None, "")
        assert text is None and grund == "nicht erreichbar"

    def test_fehlerseite_ist_kein_einbaubefund(self, waechter):
        text, grund = waechter.bewerte_einbau(
            "panoart360-de", "https://panoart360.de", 503, "Service Unavailable")
        assert text is None and grund == "HTTP 503"


class TestEinbauTaktung:
    @pytest.mark.asyncio
    async def test_laeuft_nur_zur_pruefstunde(self, waechter, monkeypatch):
        """Stuendlich alle Kundenseiten abzurufen waere unhoeflich und
        brauchte niemand: der Einbau aendert sich nicht im Stundentakt."""
        class Uhr:
            @staticmethod
            def now():
                class T:
                    hour = (waechter.EINBAU_PRUEFSTUNDE + 1) % 24
                return T()
        monkeypatch.setattr(waechter, "datetime", Uhr)
        assert await waechter.pruefe_einbau() == []


class TestVerdrahtung:
    def test_einbaupruefung_haengt_in_main(self, waechter):
        import inspect
        quelle = inspect.getsource(waechter.main)
        assert "pruefe_einbau" in quelle, \
            "Der Check existiert, wird aber nie aufgerufen."
