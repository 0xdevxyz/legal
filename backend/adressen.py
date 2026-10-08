"""
Wohin Links zeigen, die das Backend in Mails und Weiterleitungen baut.

Zwei Oberflaechen, zwei Adressen:

* ``FRONTEND_URL`` ist die Startseite (https://complyo.de): Warteliste,
  Lead-Verifizierung, Preise. Derselbe Wert ist der JWT-Aussteller
  (auth_service, dependencies). Ihn zu aendern meldet jeden ab.
* ``DASHBOARD_URL`` ist das Dashboard (https://app.complyo.de): Anmeldung,
  Konto, Passwort, Add-ons, KI-Systeme, Einstellungen.

Bis zum 29.09.2026 gab es nur ``FRONTEND_URL``, und beide Seiten lasen sie.
docker-compose setzte sie im Backend zweimal, einmal auf das Dashboard und
darunter hart auf die Startseite; der spaetere Eintrag gewann. Gemessen am
29.09.2026 endeten dadurch auf https://complyo.de in 404:
/konto/passwort-neu (Passwortmail), /konto/email-bestaetigen
(Kontobestaetigung), /auth/callback (Google- und Apple-Anmeldung),
/dashboard/addons (Stripe-Ruecksprung nach dem Add-on-Kauf), /login
(Loeschankuendigung) und die Links der KI-Compliance- und Rechtsaenderungs-
Mails. Auf app.complyo.de antworten dieselben Pfade mit 200.

Wer einen Link ins Dashboard baut, nimmt ``dashboard_url()``.
tests/test_adressen.py haelt fest, dass FRONTEND_URL nur noch dort gelesen
wird, wo die Startseite gemeint ist.
"""

import os


def dashboard_url() -> str:
    return os.getenv("DASHBOARD_URL", "https://app.complyo.de").rstrip("/")


def startseite_url() -> str:
    return os.getenv("FRONTEND_URL", "https://complyo.de").rstrip("/")


def api_url() -> str:
    """Links, die das Backend selbst beantwortet (Bestaetigen, Verwerfen).

    complyo.de gibt /api/ an die Landing weiter und endet dort in 404.
    """
    return os.getenv("PUBLIC_API_BASE", "https://api.complyo.de").rstrip("/")
