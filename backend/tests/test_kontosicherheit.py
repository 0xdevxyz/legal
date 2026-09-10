"""
Tests für die Kontosicherheit: TOTP, Passwortrichtlinie, Wiederherstellungscodes.

Der TOTP-Teil prüft gegen die Testvektoren aus Anhang B von RFC 6238. Eine
selbstgeschriebene Krypto-Funktion ohne diesen Abgleich wäre eine Behauptung:
sie liefert sechs Ziffern, und ob es die richtigen sind, sieht man erst, wenn
ein Kunde sich nicht mehr anmelden kann.
"""

import base64
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import passwort_richtlinie
import zweiter_faktor


# ---------------------------------------------------------------------------
# TOTP gegen RFC 6238, Anhang B
# ---------------------------------------------------------------------------
# Das Geheimnis im RFC ist der ASCII-Text "12345678901234567890"; unsere
# Schnittstelle nimmt Base32, deshalb hier umgerechnet.
RFC_GEHEIMNIS = base64.b32encode(b"12345678901234567890").decode().rstrip("=")

# Nur die SHA-1-Zeilen der Tabelle — das ist der Algorithmus, den die
# Authenticator-Apps sprechen und den wir implementieren. Die Vektoren im RFC
# sind achtstellig; verglichen werden die letzten sechs Stellen, weil das
# genau die sechsstellige Ausgabe ist.
RFC_VEKTOREN = [
    (59, "94287082"),
    (1111111109, "07081804"),
    (1111111111, "14050471"),
    (1234567890, "89005924"),
    (2000000000, "69279037"),
    (20000000000, "65353130"),
]


@pytest.mark.parametrize("zeitpunkt,erwartet", RFC_VEKTOREN)
def test_totp_gegen_rfc6238(zeitpunkt, erwartet):
    assert zweiter_faktor.code_fuer(RFC_GEHEIMNIS, zeitpunkt) == erwartet[-6:]


def test_toleranzfenster_gilt_vorwaerts_und_rueckwaerts():
    geheimnis = zweiter_faktor.erzeuge_geheimnis()
    jetzt = 1_700_000_000
    schritt = zweiter_faktor.SCHRITT_SEKUNDEN

    vorher = zweiter_faktor.code_fuer(geheimnis, jetzt - schritt)
    nachher = zweiter_faktor.code_fuer(geheimnis, jetzt + schritt)

    assert zweiter_faktor.pruefe_code(geheimnis, vorher, jetzt) is not None
    assert zweiter_faktor.pruefe_code(geheimnis, nachher, jetzt) is not None


def test_ausserhalb_der_toleranz_wird_abgewiesen():
    geheimnis = zweiter_faktor.erzeuge_geheimnis()
    jetzt = 1_700_000_000
    zu_alt = zweiter_faktor.code_fuer(geheimnis, jetzt - 5 * zweiter_faktor.SCHRITT_SEKUNDEN)
    assert zweiter_faktor.pruefe_code(geheimnis, zu_alt, jetzt) is None


def test_prueffunktion_gibt_den_schritt_zurueck():
    """Der Rueckgabewert ist die Grundlage der Wiederverwendungssperre."""
    geheimnis = zweiter_faktor.erzeuge_geheimnis()
    jetzt = 1_700_000_000
    code = zweiter_faktor.code_fuer(geheimnis, jetzt)
    schritt = zweiter_faktor.pruefe_code(geheimnis, code, jetzt)
    assert schritt == jetzt // zweiter_faktor.SCHRITT_SEKUNDEN


@pytest.mark.parametrize("eingabe", ["", "12345", "1234567", "abcdef", None])
def test_unfug_wird_abgewiesen(eingabe):
    geheimnis = zweiter_faktor.erzeuge_geheimnis()
    assert zweiter_faktor.pruefe_code(geheimnis, eingabe) is None


def test_geheimnis_ist_gueltiges_base32():
    for _ in range(20):
        g = zweiter_faktor.erzeuge_geheimnis()
        assert zweiter_faktor._geheimnis_bytes(g)


def test_otpauth_uri_traegt_die_pflichtangaben():
    uri = zweiter_faktor.otpauth_uri("ABCDEFGHIJKLMNOP", "kunde@example.de")
    assert uri.startswith("otpauth://totp/")
    assert "secret=ABCDEFGHIJKLMNOP" in uri
    assert "issuer=complyo" in uri
    # Das @ der Adresse muss kodiert sein, sonst zerlegen manche Apps die Kennung.
    assert "%40" in uri


# ---------------------------------------------------------------------------
# Wiederherstellungscodes
# ---------------------------------------------------------------------------

def test_wiederherstellungscodes_sind_verschieden():
    codes = zweiter_faktor.erzeuge_wiederherstellungscodes()
    assert len(codes) == zweiter_faktor.ANZAHL_WIEDERHERSTELLUNGSCODES
    assert len(set(codes)) == len(codes)


def test_wiederherstellungscode_hash_und_pruefung():
    code = zweiter_faktor.erzeuge_wiederherstellungscodes(1)[0]
    h = zweiter_faktor.hashe_wiederherstellungscode(code)
    assert zweiter_faktor.pruefe_wiederherstellungscode(code, h)
    # Gross/klein und Bindestrich duerfen keine Rolle spielen — abgeschrieben
    # wird das von Papier.
    assert zweiter_faktor.pruefe_wiederherstellungscode(code.upper(), h)
    assert zweiter_faktor.pruefe_wiederherstellungscode(code.replace("-", " "), h)
    assert not zweiter_faktor.pruefe_wiederherstellungscode("falsch-falsch", h)


def test_codes_enthalten_keine_verwechselbaren_zeichen():
    for code in zweiter_faktor.erzeuge_wiederherstellungscodes(30):
        assert not set(code) & set("01loi")


# ---------------------------------------------------------------------------
# Passwortrichtlinie
# ---------------------------------------------------------------------------

def test_gutes_passwort_geht_durch():
    passwort_richtlinie.pruefe("pferd wagen keller lampe", email="a@b.de", name="Max Mustermann")


@pytest.mark.parametrize("schwach", [
    "kurz",                    # zu kurz
    "passwort123",             # Sperrliste plus Ziffern
    "1234567890123",           # Zahlenreihe
    "qwertzuiopas",            # Tastaturreihe
    "abcabcabcabc",            # Wiederholung
    "aaaaaaaaaaaaaa",          # zu wenige verschiedene Zeichen
    "  mitleerzeichen  ",      # Rand-Leerzeichen
])
def test_schwache_passwoerter_werden_abgewiesen(schwach):
    with pytest.raises(passwort_richtlinie.PasswortSchwach):
        passwort_richtlinie.pruefe(schwach)


def test_eigener_name_und_adresse_sind_kein_geheimnis():
    with pytest.raises(passwort_richtlinie.PasswortSchwach):
        passwort_richtlinie.pruefe("mustermann-2026-xyz", email="max.mustermann@firma.de")
    with pytest.raises(passwort_richtlinie.PasswortSchwach):
        passwort_richtlinie.pruefe("complyo-ist-toll", email="a@b.de")


def test_zu_langes_passwort_wird_abgewiesen():
    with pytest.raises(passwort_richtlinie.PasswortSchwach):
        passwort_richtlinie.pruefe("x" * (passwort_richtlinie.MAX_LAENGE + 1))


def test_mindestlaenge_ist_die_grenze():
    """Genau auf der Grenze muss es durchgehen, ein Zeichen darunter nicht."""
    gerade_so = "vogelhausdach"[:passwort_richtlinie.MIN_LAENGE]
    assert len(gerade_so) == passwort_richtlinie.MIN_LAENGE
    passwort_richtlinie.pruefe(gerade_so)
    with pytest.raises(passwort_richtlinie.PasswortSchwach):
        passwort_richtlinie.pruefe(gerade_so[:-1])


# ---------------------------------------------------------------------------
# CSRF-Ausnahmen der oeffentlichen Kontowege
# ---------------------------------------------------------------------------
# Dieser Waechter kommt aus einem Live-Fehlschlag vom 10.09.2026: alle Tests
# waren gruen, und der erste echte Aufruf von /passwort-vergessen antwortete
# "CSRF token missing or invalid". Der Grund steht in csrf_middleware.py sogar
# zweimal — wer nicht angemeldet ist, hat kein CSRF-Cookie, also kann der
# Double-Submit-Check nie aufgehen. Ein dritter Anlauf soll auffallen, bevor
# er live geht.

OEFFENTLICHE_KONTOWEGE = [
    "/api/auth/passwort-vergessen",
    "/api/auth/passwort-neu",
    "/api/auth/email-bestaetigen",
    "/api/auth/login/2fa",
]


@pytest.mark.parametrize("pfad", OEFFENTLICHE_KONTOWEGE)
def test_oeffentliche_kontowege_sind_vom_csrf_check_ausgenommen(pfad):
    from csrf_middleware import EXEMPT_PATHS
    assert pfad in EXEMPT_PATHS, (
        f"{pfad} wird ohne Sitzung aufgerufen und braucht deshalb eine "
        "CSRF-Ausnahme — sonst antwortet die Route jedem Nutzer mit 403."
    )


def test_angemeldete_2fa_wege_sind_NICHT_ausgenommen():
    """Die Gegenprobe: was hinter der Anmeldung liegt, behaelt den Schutz."""
    from csrf_middleware import EXEMPT_PATHS
    for pfad in ("/api/auth/2fa/einrichten", "/api/auth/2fa/bestaetigen",
                 "/api/auth/2fa/abschalten", "/api/auth/email-bestaetigung-erneut"):
        assert pfad not in EXEMPT_PATHS


# ---------------------------------------------------------------------------
# Oeffentliche Pfade des Dashboards: EINE Liste, nicht drei
# ---------------------------------------------------------------------------
# Am 10.09.2026 stand die Liste der ohne Anmeldung erreichbaren Seiten an DREI
# Stellen: im `authorized`-Rueckruf (auth.config.ts), in middleware.ts und als
# `AUTH_ROUTES` in SidebarLayout.tsx. Die drei laufen nacheinander, und jede
# konnte fuer sich umleiten. Beim Bau der Kontoseiten wurden zwei davon
# angepasst — die Seiten waren gebaut, ausgeliefert und serverseitig
# freigegeben, und der Browser schob sie trotzdem auf /login. Zweimal
# neugebaut, bis die dritte Kopie gefunden war.
#
# Dieser Waechter laesst die vierte Kopie nicht entstehen.

_DASHBOARD = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "dashboard-react", "src",
)

_WAECHTER_DATEIEN = [
    "auth.config.ts",
    "middleware.ts",
    os.path.join("components", "dashboard", "SidebarLayout.tsx"),
]


def _dashboard_quelle(relpfad: str) -> str:
    pfad = os.path.join(_DASHBOARD, relpfad)
    if not os.path.exists(pfad):
        pytest.skip(f"{relpfad} nicht gemountet — vollstaendiger Lauf: scripts/tests-lokal.sh")
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


@pytest.mark.parametrize("datei", _WAECHTER_DATEIEN)
def test_pfadwaechter_nutzen_die_gemeinsame_liste(datei):
    quelle = _dashboard_quelle(datei)
    assert "oeffentliche-pfade" in quelle, (
        f"{datei} entscheidet ueber den Zugang, importiert die Liste aber nicht "
        "aus lib/oeffentliche-pfade. Eine zweite Kopie faellt beim Aendern nicht "
        "auf — sie leitet einfach weiter um."
    )


@pytest.mark.parametrize("datei", _WAECHTER_DATEIEN)
def test_keine_eigene_pfadliste_mehr(datei):
    """Gegenprobe: kein fest eingetippter Pfad neben dem Import."""
    quelle = _dashboard_quelle(datei)
    verdaechtig = [
        z.strip() for z in quelle.splitlines()
        if '"/login"' in z or "'/login'" in z
    ]
    # `pages: { signIn: "/login" }` und die Umleitung selbst duerfen bleiben —
    # verboten ist eine LISTE mit mehreren Pfaden.
    listen = [z for z in verdaechtig if z.count("/") >= 3 and "[" in z]
    assert not listen, f"{datei}: eigene Pfadliste gefunden: {listen}"


def test_kontoseiten_stehen_in_der_gemeinsamen_liste():
    quelle = _dashboard_quelle(os.path.join("lib", "oeffentliche-pfade.ts"))
    for pfad in ("/passwort-vergessen", "/konto/passwort-neu", "/konto/email-bestaetigen"):
        assert pfad in quelle, (
            f"{pfad} fehlt in OEFFENTLICHE_PFADE — die Seite waere ohne Anmeldung "
            "nicht erreichbar, obwohl genau das ihr Zweck ist."
        )
