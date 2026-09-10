# -*- coding: utf-8 -*-
"""
Anbieterdaten. Eine Quelle fuer alles, was das Backend nach aussen schreibt.

Das Gegenstueck zu `landing-react/src/lib/anbieter.ts`, das am 01.09.2026
angelegt wurde, um die erfundenen Angaben von den Rechtsseiten zu nehmen. Im
Backend blieb der alte Stand stehen — gemessen am 10.09.2026 an dreizehn
Stellen in fuenf Dateien:

  * `complyo_privacy_clause.py` schrieb "Complyo GmbH, Koburger Strasse 198,
    04416 Markkleeberg" in die Datenschutzerklaerungen DER KUNDEN. Der Kunde
    nennt damit in seiner eigenen Erklaerung einen Auftragsverarbeiter, den es
    unter diesem Namen nicht gibt (Art. 13 DSGVO).
  * Die E-Mail-Fusszeilen, die Benachrichtigungen und die PDF-Berichte nannten
    dieselbe "GmbH" — der Haftungsausschluss im Bericht lautete woertlich
    "Complyo GmbH uebernimmt keine Haftung".
  * `gdpr_api.py` nannte einer betroffenen Person als Verantwortlichen die
    "Complyo GmbH" und einen Datenschutzbeauftragten unter dpo@complyo.de.

complyo wird als Einzelunternehmen von Yvonne Weishar betrieben. Es gibt keine
GmbH. Wer ohne existierende GmbH als "GmbH" auftritt, loest Rechtsscheinhaftung
aus: der Handelnde haftet dann persoenlich — also genau umgekehrt zur Absicht
einer Haftungsbeschraenkung. Und ein Haftungsausschluss im Namen einer
Gesellschaft, die es nicht gibt, schuetzt niemanden.

Wer die Anbieterdaten aendert, aendert sie hier. `tests/test_anbieterdaten.py`
haelt fest, dass keine erfundene Rechtsform zurueckkommt.
"""

from __future__ import annotations

# Pflichtangaben nach § 5 DDG. Deckungsgleich mit dem Impressum.
NAME = "Yvonne Weishar"
GESCHAEFTSBEZEICHNUNG = "Complyo"
STRASSE = "Pappelallee 64"
PLZ = "10437"
ORT = "Berlin"
LAND = "Deutschland"
EMAIL = "info@complyo.de"
SUPPORT_EMAIL = "support@complyo.de"
DATENSCHUTZ_EMAIL = "datenschutz@complyo.de"
TELEFON = "+49 173 8448941"
UST_ID = "DE405368946"

#: "Pappelallee 64, 10437 Berlin"
ANSCHRIFT_EINZEILIG = f"{STRASSE}, {PLZ} {ORT}"

#: "Yvonne Weishar · Complyo" — kurze Nennung, etwa in einer E-Mail-Fusszeile.
ABSENDER = f"{NAME} · {GESCHAEFTSBEZEICHNUNG}"

#: Vollstaendige Nennung mit Anschrift. Fuer Fusszeilen und Berichte.
ABSENDER_MIT_ANSCHRIFT = f"{ABSENDER}, {ANSCHRIFT_EINZEILIG}"

#: Die Vertragspartei, wie sie in Vertragstexten steht.
VERTRAGSPARTEI = (
    f'{NAME}, handelnd unter der Geschäftsbezeichnung "{GESCHAEFTSBEZEICHNUNG}", '
    f"{ANSCHRIFT_EINZEILIG}"
)

#: Der Verantwortliche im Sinne des Art. 4 Nr. 7 DSGVO.
VERANTWORTLICHER = ABSENDER_MIT_ANSCHRIFT

# Es gibt keinen bestellten Datenschutzbeauftragten. Die Bestellpflicht nach
# § 38 BDSG greift erst ab 20 staendig mit der Verarbeitung beschaeftigten
# Personen. Eine erfundene Adresse dpo@complyo.de zu nennen, an die niemand
# antwortet, verletzt Art. 12 Abs. 2 DSGVO — Anfragen muessen ankommen.
DATENSCHUTZBEAUFTRAGTER: str | None = None
