# -*- coding: utf-8 -*-
"""Das Umschalt-Skript aendert die .env. Darin stehen alle Geheimnisse.

Eine Datei, die jeden Zugang des Systems enthaelt, wird nicht auf Zuruf
umgeschrieben. Diese Tests halten fest, was dabei gelten muss: jede fremde
Zeile bleibt Zeichen fuer Zeichen stehen, eine Kopie liegt vorher daneben,
und der alte Wert bleibt als Kommentar ablesbar.
"""
import importlib.util
import os
import stat

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
SKRIPT = os.path.join(WURZEL, "scripts", "stripe-live-umschalten.py")

BEISPIEL = """# complyo Umgebung
DATABASE_URL=postgresql://complyo_user:geheim@postgres:5432/complyo_db
JWT_SECRET=nicht-anfassen

# Stripe
STRIPE_SECRET_KEY=sk_test_alt
STRIPE_PRICE_PRO_MONTHLY=price_test_pro
# STRIPE_PRICE_PRO_YEARLY=price_auskommentiert
SMTP_PASSWORD=auch-geheim
"""


def _modul():
    spec = importlib.util.spec_from_file_location("umschalten", SKRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _vorbereiten(tmp_path):
    m = _modul()
    pfad = tmp_path / ".env"
    pfad.write_text(BEISPIEL, encoding="utf-8")
    m.ENV_PFAD = str(pfad)
    return m, pfad


def _werte(text):
    return dict(z.split("=", 1) for z in text.splitlines()
                if "=" in z and not z.lstrip().startswith("#"))


def test_fremde_zeilen_bleiben_unveraendert(tmp_path):
    m, pfad = _vorbereiten(tmp_path)
    m.env_schreiben({"STRIPE_SECRET_KEY": "sk_live_neu",
                     "STRIPE_PRICE_PRO_MONTHLY": "price_live_pro"})
    werte = _werte(pfad.read_text(encoding="utf-8"))
    assert werte["DATABASE_URL"] == "postgresql://complyo_user:geheim@postgres:5432/complyo_db"
    assert werte["JWT_SECRET"] == "nicht-anfassen"
    assert werte["SMTP_PASSWORD"] == "auch-geheim"


def test_zielzeilen_werden_ersetzt(tmp_path):
    m, pfad = _vorbereiten(tmp_path)
    m.env_schreiben({"STRIPE_SECRET_KEY": "sk_live_neu",
                     "STRIPE_PRICE_PRO_MONTHLY": "price_live_pro"})
    werte = _werte(pfad.read_text(encoding="utf-8"))
    assert werte["STRIPE_SECRET_KEY"] == "sk_live_neu"
    assert werte["STRIPE_PRICE_PRO_MONTHLY"] == "price_live_pro"


def test_unbekannte_namen_werden_angehaengt(tmp_path):
    m, pfad = _vorbereiten(tmp_path)
    m.env_schreiben({"STRIPE_PRICE_COMPLOAI_GUARD": "price_live_guard"})
    werte = _werte(pfad.read_text(encoding="utf-8"))
    assert werte["STRIPE_PRICE_COMPLOAI_GUARD"] == "price_live_guard"
    assert werte["JWT_SECRET"] == "nicht-anfassen"


def test_auskommentierte_zeile_bleibt_kommentar(tmp_path):
    """Sonst wuerde eine bewusst stillgelegte Zeile wieder scharf."""
    m, pfad = _vorbereiten(tmp_path)
    m.env_schreiben({"STRIPE_SECRET_KEY": "sk_live_neu"})
    text = pfad.read_text(encoding="utf-8")
    assert "# STRIPE_PRICE_PRO_YEARLY=price_auskommentiert" in text
    assert "\nSTRIPE_PRICE_PRO_YEARLY=" not in text


def test_alter_wert_bleibt_als_kommentar_lesbar(tmp_path):
    m, pfad = _vorbereiten(tmp_path)
    m.env_schreiben({"STRIPE_SECRET_KEY": "sk_live_neu"})
    text = pfad.read_text(encoding="utf-8")
    assert "STRIPE_SECRET_KEY=sk_test_alt" in text
    assert text.count("\nSTRIPE_SECRET_KEY=") == 1


def test_kopie_wird_vorher_angelegt(tmp_path):
    m, pfad = _vorbereiten(tmp_path)
    m.env_schreiben({"STRIPE_SECRET_KEY": "sk_live_neu"})
    kopien = [f for f in os.listdir(tmp_path) if "-vor-live" in f]
    assert len(kopien) == 1
    alt = (tmp_path / kopien[0]).read_text(encoding="utf-8")
    assert alt == BEISPIEL, "Die Kopie ist nicht der Stand von vorher"


def test_rechte_bleiben_eng(tmp_path):
    """Die Datei enthaelt jeden Zugang des Systems."""
    m, pfad = _vorbereiten(tmp_path)
    m.env_schreiben({"STRIPE_SECRET_KEY": "sk_live_neu"})
    for datei in [pfad] + [tmp_path / f for f in os.listdir(tmp_path) if "-vor-live" in f]:
        modus = stat.S_IMODE(os.stat(datei).st_mode)
        assert modus == 0o600, f"{datei} hat Rechte {oct(modus)}"
