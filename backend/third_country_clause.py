"""
Drittland-Datenschutz-Passus — deterministischer Baustein-Generator.

Werden auf der Website Dienste eingesetzt, die personenbezogene Daten in
unsicheren Drittländern (außerhalb EU/EWR, ohne EU-Angemessenheitsbeschluss)
verarbeiten, muss die Datenschutzerklärung des Betreibers darüber gemäß
Art. 13 Abs. 1 lit. f DSGVO informieren und die Rechtsgrundlage der
Übermittlung (Art. 44 ff., bei Einwilligung Art. 49 Abs. 1 lit. a DSGVO)
benennen.

Wie der Complyo-Passus wird dieser Abschnitt NICHT von der KI generiert,
sondern deterministisch aus festem Wortlaut und der Drittländer-SSOT
(compliance_engine/data_processing_countries) zusammengesetzt — die konkrete
Länderliste und die Rechtsgrundlage dürfen nicht durch ein Sprachmodell
umformuliert oder weggelassen werden.

Modular: ausgegeben wird nur, wenn mindestens ein tatsächlich genutzter Dienst
in einem unsicheren Drittland verarbeitet. Eingebunden in
legal_text_generator.generate_privacy_policy(), injiziert vor dem Disclaimer.
"""

from __future__ import annotations

import html as _html
from typing import List, Optional

from compliance_engine.data_processing_countries import third_country_breakdown


def build_third_country_clause(services_used: Optional[List[str]]) -> str:
    """
    Baut den Drittland-Abschnitt aus der Liste der genutzten Service-Namen.
    Leerer String, wenn kein genutzter Dienst in ein unsicheres Drittland
    übermittelt.
    """
    if not services_used:
        return ""

    breakdown = third_country_breakdown(services_used)
    if not breakdown:
        return ""

    rows = "\n".join(
        "  <li><strong>{name}</strong> — Datenverarbeitung u.&nbsp;a. in: {countries}</li>".format(
            name=_html.escape(item["name"]),
            countries=_html.escape(", ".join(item["unsafe_country_names"])),
        )
        for item in breakdown
    )

    return (
        "\n<h2>Datenübermittlung in Drittländer</h2>\n"
        "<p>Einige der auf dieser Website eingesetzten Dienste verarbeiten "
        "personenbezogene Daten (z.&nbsp;B. Ihre IP-Adresse) in Ländern außerhalb "
        "der Europäischen Union bzw. des Europäischen Wirtschaftsraums, für die "
        "kein Angemessenheitsbeschluss der EU-Kommission im Sinne des Art.&nbsp;45 "
        "DSGVO vorliegt (unsichere Drittländer). Dies betrifft insbesondere:</p>\n"
        "<ul>\n"
        f"{rows}\n"
        "</ul>\n"
        "<p>In diesen Ländern besteht ggf. kein dem europäischen Recht "
        "vergleichbares Datenschutzniveau; insbesondere können staatliche Stellen "
        "auf die Daten zugreifen, ohne dass hiergegen wirksame Rechtsbehelfe "
        "bestehen. Die Übermittlung erfolgt auf Grundlage Ihrer ausdrücklichen "
        "Einwilligung gemäß <strong>Art.&nbsp;49 Abs.&nbsp;1 lit.&nbsp;a DSGVO</strong>, "
        "soweit für die jeweilige Verarbeitung keine geeigneten Garantien nach "
        "Art.&nbsp;46 DSGVO (z.&nbsp;B. Standardvertragsklauseln) bestehen. Sie "
        "erteilen diese Einwilligung über das Cookie-Banner; ohne Ihre Einwilligung "
        "werden die betreffenden Dienste nicht geladen.</p>\n"
        "<p>Ihre Einwilligung ist freiwillig und kann jederzeit mit Wirkung für "
        "die Zukunft widerrufen werden, indem Sie Ihre Cookie-Einstellungen "
        "anpassen.</p>\n"
    )
