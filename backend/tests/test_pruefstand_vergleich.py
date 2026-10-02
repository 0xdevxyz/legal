"""
Der Pruefstand-Vergleich: zwei Laeufe, die Haeufigkeit je Befundart.

Der Pruefstand misst seit dem 09.09.2026 nicht mehr den Einzelbefund, sondern
seine Haeufigkeit ueber den Bestand echter Seiten. Dieser Vergleich macht aus
zwei Laeufen eine Aussage, und er soll dabei die Fehler nicht wiederholen, die
der Pruefstand selbst aufgedeckt hat:

- Ein Mittelwert ueber verschiedene Seitenmengen ist keiner. Verglichen wird nur,
  was in BEIDEN Laeufen gemessen wurde.
- axe ist die Referenz. Dass color-contrast auf drei Viertel der Seiten steht, ist
  ein Befund ueber den Bestand und kein Verdacht gegen den Scanner.
- Hinweise ohne Eurobetrag kosten den Kunden nichts und stehen nicht auf der
  Verdachtsliste.
- Ein "gruener" Vergleich ohne gemeinsam gemessene Seite ist kein gruener
  Vergleich (so war der Pruefstand vom 09. bis 16.09. tot und meldete "0
  Befunde", was wie bestanden aussah).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import pruefstand_vergleich as pv  # noqa: E402

WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def issue(titel, kategorie="security", euro=500, severity="warning", axe=None):
    return {"category": kategorie, "severity": severity, "title": titel,
            "risk_euro": euro, "slug": None, "quelle": None, "axe_rule": axe}


def seite(url, score, *issues):
    return {"url": url, "score": score, "issues": list(issues)}


def lauf(*seiten):
    return {"gemessen": "2026-10-02T03:30:00", "seiten": list(seiten)}


def bestand(n, mit):
    """n Seiten; die ersten `mit` tragen den HSTS-Befund."""
    seiten = []
    for i in range(n):
        iss = [issue("HSTS-Header fehlt")] if i < mit else []
        seiten.append(seite(f"https://s{i}.test", 60, *iss))
    return lauf(*seiten)


class TestBefundart:
    def test_zahlen_sind_eine_art(self):
        a = pv.befundart(issue("12 Bilder ohne Alt-Text", "barrierefreiheit"))
        b = pv.befundart(issue("3 Bilder ohne Alt-Text", "barrierefreiheit"))
        assert a == b

    def test_satzzeichen_und_schreibweise_zaehlen_nicht(self):
        """Aus "Google Fonts (extern geladen) - Drittlandtransfer" wurde am
        02.10.2026 "...: Drittlandtransfer". Als Rohtext verglichen zeigte der
        Pruefstand dafuer ein Minus von 10 und ein Plus von 10."""
        alt = pv.befundart(issue("Google Fonts (extern geladen) \u2014 Drittlandtransfer", "datenschutz"))
        neu = pv.befundart(issue("Google Fonts (extern geladen): Drittlandtransfer", "datenschutz"))
        assert alt == neu

    def test_umbenennung_ist_keine_bewegung(self):
        def l(titel):
            return lauf(*[seite(f"https://s{i}.test", 50, issue(titel, "datenschutz"))
                          for i in range(10)])
        v = pv.vergleiche(l("Google Fonts \u2014 Drittlandtransfer"),
                          l("Google Fonts: Drittlandtransfer"))
        assert [z for z in v["arten"] if z["diff"] != 0] == []
        assert len(v["arten"]) == 1

    def test_kategorie_trennt_gleiche_titel(self):
        assert pv.befundart(issue("Fehlt", "agb")) != pv.befundart(issue("Fehlt", "avv"))


class TestMessbare:
    def test_nicht_scanbare_seiten_zaehlen_nicht(self):
        l = lauf(seite("https://a.test", 50), {"url": "https://b.test", "fehler": "SSL"})
        assert list(pv.messbare(l)) == ["https://a.test"]


class TestVerdacht:
    def test_haeufiger_befund_mit_euro_steht_auf_der_liste(self):
        seiten = pv.messbare(bestand(10, 9))
        assert [t[0] for t in pv.verdacht(seiten)] == ["security: HSTS-Header fehlt"]

    def test_seltener_befund_nicht(self):
        assert pv.verdacht(pv.messbare(bestand(10, 3))) == []

    def test_axe_ist_die_referenz(self):
        seiten = {f"https://s{i}.test": seite(f"https://s{i}.test", 50,
                  issue("Zu geringer Farbkontrast", "barrierefreiheit", axe="color-contrast"))
                  for i in range(10)}
        assert pv.verdacht(seiten) == []

    def test_hinweise_ohne_euro_nicht(self):
        seiten = {f"https://s{i}.test": seite(f"https://s{i}.test", 50,
                  issue("Kein Assistenz-Widget", "barrierefreiheit", euro=0, severity="info"))
                  for i in range(10)}
        assert pv.verdacht(seiten) == []

    def test_zu_kleiner_bestand_sagt_nichts(self):
        """Drei Seiten, alle mit Befund: 100 %, aber keine Aussage."""
        assert pv.verdacht(pv.messbare(bestand(3, 3))) == []

    def test_schwelle_ist_einstellbar(self):
        seiten = pv.messbare(bestand(10, 5))
        assert pv.verdacht(seiten, schwelle=0.75) == []
        assert len(pv.verdacht(seiten, schwelle=0.5)) == 1


class TestVergleich:
    def test_nur_gemeinsam_gemessene_seiten(self):
        alt = lauf(seite("https://a.test", 40), seite("https://b.test", 40))
        neu = lauf(seite("https://a.test", 60), {"url": "https://b.test", "fehler": "x"},
                   seite("https://c.test", 90))
        v = pv.vergleiche(alt, neu)
        assert v["gemeinsam"] == 1
        assert v["kennzahlen_alt"]["score_mittel"] == 40
        assert v["kennzahlen_neu"]["score_mittel"] == 60, (
            "Der neue Mittelwert enthaelt eine Seite, die im alten Lauf fehlt.")
        assert v["nur_alt"] == ["https://b.test"]
        assert v["nur_neu"] == ["https://c.test"]

    def test_bewegung_je_art(self):
        v = pv.vergleiche(bestand(10, 8), bestand(10, 2))
        z = [z for z in v["arten"] if z["art"] == "security: HSTS-Header fehlt"][0]
        assert (z["alt"], z["neu"], z["diff"]) == (8, 2, -6)

    def test_verdacht_neu_und_weg(self):
        v = pv.vergleiche(bestand(10, 2), bestand(10, 9))
        assert v["verdacht_neu"] == ["security: HSTS-Header fehlt"]
        v = pv.vergleiche(bestand(10, 9), bestand(10, 2))
        assert v["verdacht_weg"] == ["security: HSTS-Header fehlt"]


class TestStreng:
    def _lauf(self, tmp_path, alt, neu, *extra):
        a, b = tmp_path / "alt.json", tmp_path / "neu.json"
        a.write_text(json.dumps(alt)), b.write_text(json.dumps(neu))
        return pv.main([str(a), str(b), *extra])

    def test_gleiche_laeufe_sind_gruen(self, tmp_path, capsys):
        assert self._lauf(tmp_path, bestand(10, 2), bestand(10, 2), "--streng") == 0

    def test_neue_verdachtsart_ist_rot(self, tmp_path, capsys):
        assert self._lauf(tmp_path, bestand(10, 2), bestand(10, 9), "--streng") == 1
        assert "neue Verdachtsart" in capsys.readouterr().err

    def test_score_absturz_ist_rot(self, tmp_path, capsys):
        alt = lauf(*[seite(f"https://s{i}.test", 70) for i in range(10)])
        neu = lauf(*[seite(f"https://s{i}.test", 50) for i in range(10)])
        assert self._lauf(tmp_path, alt, neu, "--streng") == 1

    def test_ohne_gemeinsame_seite_ist_nicht_gruen(self, tmp_path, capsys):
        """Ein Vergleich, der nichts verglichen hat, darf nicht bestehen."""
        alt = lauf(seite("https://a.test", 70))
        neu = lauf(seite("https://b.test", 70))
        assert self._lauf(tmp_path, alt, neu, "--streng") == 1

    def test_ohne_streng_nie_rot(self, tmp_path, capsys):
        assert self._lauf(tmp_path, bestand(10, 2), bestand(10, 9)) == 0


class TestDerEchteBestand:
    """Der Lauf vom 09.09.2026, gegen den die Linie gezogen wurde.

    Die Datei liegt nicht im Repo (es sind Kundendomains). Wo sie fehlt, laeuft
    der Test nicht: ein uebersprungener Test bewacht nichts, deshalb steht der
    Grund in der Meldung.
    """

    BASIS = os.environ.get("PRUEFSTAND_BASIS", "")

    def test_gemessene_verdachtsarten_vom_09_09(self):
        import pytest
        if not (self.BASIS and os.path.exists(self.BASIS)):
            pytest.skip("PRUEFSTAND_BASIS zeigt auf keinen Lauf; Kundendaten "
                        "gehoeren nicht ins Repo")
        seiten = pv.messbare(pv.lade(self.BASIS))
        arten = {t[0] for t in pv.verdacht(seiten)}
        assert "security: Content-Security-Policy-Header fehlt" in arten


class TestLaufSkript:
    SKRIPT = os.path.join(WURZEL, "scripts", "pruefstand-lauf.sh")

    def test_syntax(self):
        r = subprocess.run(["sh", "-n", self.SKRIPT], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr

    def test_ist_ausfuehrbar(self):
        assert os.access(self.SKRIPT, os.X_OK)

    def test_fehlende_liste_bricht_mit_2_ab(self, tmp_path):
        env = dict(os.environ, PRUEFSTAND_DIR=str(tmp_path))
        r = subprocess.run(["sh", self.SKRIPT], capture_output=True, text=True, env=env)
        assert r.returncode == 2
        assert "Seitenliste" in r.stderr

    def test_umgebung_beruehrt_keine_platte(self):
        """Die Werte kommen per Pipe aus dem laufenden Container."""
        quelle = open(self.SKRIPT, encoding="utf-8").read()
        assert "--env-file /dev/stdin" in quelle
        assert "docker inspect -f" in quelle
        assert "--env-file /home/clawd/saas/legal/.env" not in quelle, (
            "Die .env-Datei kennt die Quotes nicht, die docker-compose entfernt: "
            "das Passwort kommt falsch an (Falle vom SMTP-Livegang am 11.08.).")

    def test_misst_das_ausgelieferte_image_nicht_den_arbeitsbaum(self):
        quelle = open(self.SKRIPT, encoding="utf-8").read()
        assert 'ARBEITSVERZEICHNIS="/app"' in quelle
        assert ":/src:ro" in quelle and "-v $PRUEFSTAND_CODE:/app" not in quelle, (
            "Ein Mount auf /app verdeckt die Playwright-Browser unter "
            "/app/.cache, der Scan faellt still auf Heuristik zurueck.")

    def test_keine_kundenliste_im_repo(self):
        """Die Seitenliste sind die Domains der Hosting-Kunden."""
        import re
        domain = re.compile(r"^(https?://)?(www\.)?[a-z0-9-]+\.(de|com|eu|net|org|cafe|info)/?$", re.I)
        funde = []
        for ordner in ("scripts", os.path.join("backend", "tools")):
            for name in os.listdir(os.path.join(WURZEL, ordner)):
                if not name.endswith(".txt"):
                    continue
                with open(os.path.join(WURZEL, ordner, name), encoding="utf-8") as fh:
                    zeilen = [z.strip() for z in fh if z.strip() and not z.startswith("#")]
                if sum(1 for z in zeilen if domain.match(z)) >= 5:
                    funde.append(os.path.join(ordner, name))
        assert not funde, f"Kundendomains im Repo: {funde}"


class TestLaufSkriptMitAttrappe:
    """Das Skript gegen ein vorgetaeuschtes docker, ohne Server.

    Der erste echte Lauf am 02.10.2026 scheiterte nach acht Sekunden:
    `docker run --env-file` lehnte die Umgebung des Backend-Containers ab, weil
    sie einen mehrzeiligen privaten Schluessel traegt. Kein Test hatte das
    Skript je durchlaufen, nur seine Syntax geprueft.
    """

    SKRIPT = os.path.join(WURZEL, "scripts", "pruefstand-lauf.sh")

    ATTRAPPE = """#!/bin/sh
# Vorgetaeuschtes docker: inspect liefert eine Umgebung mit mehrzeiligem Wert,
# run liest die Umgebung von stdin und legt ein Ergebnis in den Ausgabeordner.
case "$1" in
  inspect)
    if [ "$2" = "-f" ]; then
      printf '%s' '["DATABASE_URL=postgresql://u:p@db/x","SCHLUESSEL=-----BEGIN KEY-----\\nabc\\n-----END KEY-----","REDIS_URL=redis://r"]'
    fi
    exit 0 ;;
  run)
    cat > "$FAKE/env.txt"
    out=""
    for a in "$@"; do case "$a" in *:/out) out="${a%:/out}" ;; esac; done
    cp "$FAKE/ergebnis.json" "$out/pruefstand.json"
    echo "24/26 Seiten gescannt"
    exit 0 ;;
esac
exit 1
"""

    def _vorbereiten(self, tmp_path):
        fake = tmp_path / "fake"
        fake.mkdir()
        docker = fake / "docker"
        docker.write_text(self.ATTRAPPE)
        docker.chmod(0o755)
        basis = tmp_path / "pruefstand"
        basis.mkdir()
        (basis / "sites.txt").write_text("# Liste\nbeispiel.test\n")
        env = dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}", FAKE=str(fake),
                   PRUEFSTAND_DIR=str(basis))
        return fake, basis, env

    def _lauf(self, env, stand):
        return subprocess.run(["sh", self.SKRIPT], capture_output=True, text=True,
                              env=dict(env, PRUEFSTAND_STAND=stand))

    def test_mehrzeilige_werte_erreichen_den_container_nicht(self, tmp_path):
        fake, basis, env = self._vorbereiten(tmp_path)
        (fake / "ergebnis.json").write_text(json.dumps(bestand(10, 2)))
        r = self._lauf(env, "2026-10-02-100000")
        assert r.returncode == 0, r.stdout + r.stderr
        umgebung = (fake / "env.txt").read_text()
        assert "DATABASE_URL=postgresql://u:p@db/x" in umgebung
        assert "REDIS_URL=redis://r" in umgebung
        assert "BEGIN KEY" not in umgebung and "SCHLUESSEL" not in umgebung, (
            "Ein mehrzeiliger Wert (privater Schluessel) landet im Scan-Container "
            "oder bricht `--env-file`.")

    def test_erster_lauf_legt_ablage_und_verweis_an(self, tmp_path):
        fake, basis, env = self._vorbereiten(tmp_path)
        (fake / "ergebnis.json").write_text(json.dumps(bestand(10, 2)))
        r = self._lauf(env, "2026-10-02-100000")
        assert r.returncode == 0
        assert (basis / "laeufe" / "2026-10-02-100000" / "pruefstand.json").exists()
        assert (basis / "laeufe" / "2026-10-02-100000" / "vergleich.txt").exists()
        assert os.path.realpath(basis / "letzter") == os.path.realpath(
            basis / "laeufe" / "2026-10-02-100000")
        assert "Erster Lauf" in r.stdout

    def test_zweiter_lauf_vergleicht_und_schlaegt_bei_neuer_verdachtsart_an(self, tmp_path):
        fake, basis, env = self._vorbereiten(tmp_path)
        (fake / "ergebnis.json").write_text(json.dumps(bestand(10, 2)))
        assert self._lauf(env, "2026-10-02-100000").returncode == 0

        (fake / "ergebnis.json").write_text(json.dumps(bestand(10, 9)))
        r = self._lauf(env, "2026-10-09-100000")
        assert r.returncode == 1, r.stdout + r.stderr
        assert "Vergleich mit" in r.stdout and "neue Verdachtsart" in r.stdout + r.stderr

    def test_abgebrochener_lauf_ist_kein_vergleichswert(self, tmp_path):
        """Ein Ordner ohne Ergebnisdatei darf nicht als voriger Lauf gelten."""
        fake, basis, env = self._vorbereiten(tmp_path)
        (basis / "laeufe" / "2026-10-01-000000").mkdir(parents=True)
        (fake / "ergebnis.json").write_text(json.dumps(bestand(10, 2)))
        r = self._lauf(env, "2026-10-02-100000")
        assert r.returncode == 0
        assert "Erster Lauf" in r.stdout
