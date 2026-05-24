"""
Legal Disclaimer — kanonischer Baustein für alle generierten Rechtstexte.

Alle Texte, die über legal_text_generator.py erzeugt werden, erhalten diesen Disclaimer.
NICHT entfernen oder abschwächen ohne Rücksprache.
"""

DISCLAIMER_SHORT = (
    "Hinweis: KI-generierte Vorlage auf Basis aktueller Rechtslage — "
    "kein Ersatz für individuelle Rechtsberatung."
)

DISCLAIMER_LONG = (
    "Diese Texte wurden KI-gestützt auf Basis aktueller Rechtsgrundlagen erzeugt "
    "und stellen keine Rechtsberatung dar. Complyo übernimmt keine Haftung für die "
    "rechtliche Vollständigkeit oder Abmahnsicherheit. Für eine rechtsverbindliche "
    "Prüfung empfehlen wir die Konsultation eines Rechtsanwalts."
)

DISCLAIMER_TOS = (
    "Complyo bietet ein Hinweis- und Frühwarnsystem für Compliance-Risiken. "
    "Wir geben KEINE Garantie auf Abmahnsicherheit. Die generierten Rechtstexte "
    "sind Vorlagen auf Basis der zum Zeitpunkt der Generierung geltenden Rechtslage "
    "und ersetzen keine individuelle Rechtsberatung."
)

DISCLAIMER_HTML = f"""
<div class="legal-disclaimer" style="
    border-left: 3px solid #f59e0b;
    background: #fffbeb;
    padding: 12px 16px;
    margin-top: 24px;
    font-size: 0.875rem;
    color: #92400e;
    border-radius: 0 4px 4px 0;
">
    <strong>Rechtlicher Hinweis:</strong> {DISCLAIMER_LONG}
</div>
"""


def get_disclaimer(variant: str = "short") -> str:
    """
    Gibt den Disclaimer-Text zurück.

    Args:
        variant: 'short' | 'long' | 'tos' | 'html'
    """
    mapping = {
        "short": DISCLAIMER_SHORT,
        "long": DISCLAIMER_LONG,
        "tos": DISCLAIMER_TOS,
        "html": DISCLAIMER_HTML,
    }
    return mapping.get(variant, DISCLAIMER_SHORT)
