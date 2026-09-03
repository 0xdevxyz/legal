"""
Tests fuer validate_document_content: prueft den generierten KI-Output auf
Pflicht-Marker. Schliesst den Befund "Generator-Inhalt wird nie geprueft".
"""

from legal_text_generator import validate_document_content, DocumentType


COMPLETE_IMPRINT = """
<h1>Impressum</h1>
<p>Angaben gemäß § 5 DDG</p>
<p>Muster GmbH, Musterweg 1, 04109 Leipzig</p>
<p>Kontakt: info@muster.de</p>
<p>Verantwortlich für den Inhalt: Max Mustermann</p>
<p>USt-ID: DE123456789</p>
<p>Handelsregister: Amtsgericht Leipzig, HRB 12345</p>
"""

# Am 03.09.2026 um vier Abschnitte ergaenzt. Das Beispiel hiess "COMPLETE",
# enthielt aber nur vier der acht Pflichtangaben aus Art. 13 DSGVO - es fehlten
# Zwecke, Speicherdauer, Beschwerderecht und Drittlanduebermittlung. Ein
# Vollstaendigkeitsbeispiel, das unvollstaendig ist, deckt die Luecke zu, die
# es aufdecken soll.
COMPLETE_PRIVACY = """
<h1>Datenschutzerklärung</h1>
<p>Verantwortlicher im Sinne der DSGVO ...</p>
<p>Wir verarbeiten personenbezogene Daten.</p>
<p>Der Zweck der Verarbeitung ist die Vertragserfüllung.</p>
<p>Rechtsgrundlage ist Art. 6 DSGVO.</p>
<p>Die Speicherdauer beträgt 24 Monate.</p>
<p>Ihre Betroffenenrechte: Auskunft, Löschung ...</p>
<p>Beschwerderecht bei der zuständigen Aufsichtsbehörde.</p>
<p>Eine Übermittlung in ein Drittland findet nicht statt.</p>
"""

COMPLETE_WITHDRAWAL = """
<h1>Widerrufsbelehrung</h1>
<p>Sie haben das Recht, binnen 14 Tagen ohne Angabe von Gründen zu widerrufen.</p>
<p>Die Widerrufsfrist beträgt vierzehn Tage.</p>
<h2>Muster-Widerrufsformular</h2>
"""


def test_complete_imprint_has_no_missing_markers():
    assert validate_document_content(DocumentType.IMPRINT, COMPLETE_IMPRINT) == []


def test_incomplete_imprint_flags_missing_contact_and_address():
    html = "<h1>Impressum</h1><p>Diensteanbieter: Muster GmbH</p>"
    missing = validate_document_content(DocumentType.IMPRINT, html)
    assert "Kontakt (E-Mail/Telefon)" in missing
    assert "Anschrift (PLZ + Ort)" in missing


def test_complete_privacy_has_no_missing_markers():
    assert validate_document_content(DocumentType.PRIVACY, COMPLETE_PRIVACY) == []


def test_incomplete_privacy_flags_legal_basis():
    html = "<h1>Datenschutz</h1><p>Verantwortlicher</p><p>personenbezogene daten</p><p>auskunft</p>"
    missing = validate_document_content(DocumentType.PRIVACY, html)
    assert "Rechtsgrundlage" in missing


def test_complete_withdrawal_has_no_missing_markers():
    assert validate_document_content(DocumentType.WITHDRAWAL, COMPLETE_WITHDRAWAL) == []


def test_empty_document_flags_all_markers():
    """Die Zahl wird aus der Markerliste abgeleitet, nicht festgeschrieben.

    Vorher stand hier eine fest verdrahtete 4. Wer die Pflichtangaben
    erweitert, laesst damit einen Test scheitern, der inhaltlich gar nichts
    dagegen hat - und wird verleitet, die Zahl statt der Sache anzupassen.
    """
    from legal_text_generator import _MANDATORY_MARKERS

    missing = validate_document_content(DocumentType.PRIVACY, "")
    assert len(missing) == len(_MANDATORY_MARKERS[DocumentType.PRIVACY])
    assert missing, "ein leeres Dokument muss Luecken melden"
