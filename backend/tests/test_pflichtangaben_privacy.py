"""Die Datenschutzerklärung wird gegen alle Pflichtangaben aus Art. 13 geprüft.

Am 01.09.2026 fehlten in complyos EIGENER Datenschutzerklärung vier
Pflichtangaben: Zwecke, Rechtsgrundlagen, Speicherdauer, Beschwerderecht. Sie
wurden nachgetragen. Die Prüfung, mit der complyo die Dokumente seiner KUNDEN
auf Vollständigkeit abklopft, kannte davon aber nur die Rechtsgrundlage - sie
listete vier von acht Pflichtangaben. Eine generierte Kundenerklärung ohne
Speicherdauer und ohne Beschwerderecht galt damit als vollständig.

Dazu kam die Vorlage: `privacy_de.md` hatte keinen Abschnitt zur
Drittlandübermittlung. Da die Vorlage den Prompt überstimmt, adressierte der
Generator das Thema gar nicht - und complyos eigener Scanner meldete
anschließend genau diese Lücke.

Kern dieser Tests ist die Gegenprobe: ein Marker, der auf jeden beliebigen
deutschen Text anschlägt, prüft nichts.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from legal_text_generator import DocumentType, validate_document_content


VOLLSTAENDIG = """
<h1>Datenschutzerklärung</h1>
<p>Verantwortlicher im Sinne der DSGVO ist die Muster GmbH.</p>
<p>Wir verarbeiten personenbezogene Daten.</p>
<h2>Zwecke der Verarbeitung und Rechtsgrundlage</h2>
<p>Der Zweck der Verarbeitung ist die Vertragserfüllung, Rechtsgrundlage ist
Art. 6 Abs. 1 lit. b DSGVO.</p>
<h2>Speicherdauer</h2>
<p>Die Speicherdauer beträgt 24 Monate; es gilt die Löschfrist nach § 147 AO.</p>
<h2>Betroffenenrechte</h2>
<p>Sie haben ein Auskunftsrecht sowie das Recht auf Berichtigung.</p>
<p>Ihnen steht ein Beschwerderecht bei der zuständigen Aufsichtsbehörde zu.</p>
<h2>Drittlandübermittlung</h2>
<p>Eine Übermittlung in ein Drittland findet nicht statt.</p>
"""


class TestVollstaendigesDokument:
    def test_vollstaendige_erklaerung_hat_keine_luecken(self):
        assert validate_document_content(DocumentType.PRIVACY, VOLLSTAENDIG) == []

    def test_alle_acht_pflichtangaben_werden_geprueft(self):
        from legal_text_generator import _MANDATORY_MARKERS

        labels = [m[0] for m in _MANDATORY_MARKERS[DocumentType.PRIVACY]]
        for erwartet in (
            "Zwecke der Verarbeitung",
            "Speicherdauer",
            "Beschwerderecht bei der Aufsichtsbehoerde",
            "Drittlanduebermittlung",
        ):
            assert erwartet in labels, f"{erwartet} wird nicht geprüft"


class TestGegenprobe:
    """Ein Marker, der immer anschlägt, prüft nichts."""

    @pytest.mark.parametrize(
        "fehlend,erwartet",
        [
            ("Zwecke der Verarbeitung", "Zwecke der Verarbeitung"),
            ("Speicherdauer", "Speicherdauer"),
            ("Beschwerderecht", "Beschwerderecht bei der Aufsichtsbehoerde"),
            ("Drittland", "Drittlanduebermittlung"),
        ],
    )
    def test_fehlender_abschnitt_wird_gemeldet(self, fehlend, erwartet):
        entfernen = {
            "Zwecke der Verarbeitung": ["Zwecke der Verarbeitung", "Der Zweck der Verarbeitung ist die Vertragserfüllung, Rechtsgrundlage ist"],
            "Speicherdauer": ["<h2>Speicherdauer</h2>", "Die Speicherdauer beträgt 24 Monate; es gilt die Löschfrist nach § 147 AO."],
            "Beschwerderecht": ["Ihnen steht ein Beschwerderecht bei der zuständigen Aufsichtsbehörde zu."],
            "Drittland": ["<h2>Drittlandübermittlung</h2>", "Eine Übermittlung in ein Drittland findet nicht statt."],
        }[fehlend]

        text = VOLLSTAENDIG
        for teil in entfernen:
            text = text.replace(teil, "")

        luecken = validate_document_content(DocumentType.PRIVACY, text)
        assert erwartet in luecken, (
            f"Abschnitt '{fehlend}' entfernt, wird aber nicht als Lücke gemeldet - "
            f"gemeldet wurde: {luecken}"
        )

    def test_beliebiger_text_besteht_die_pruefung_nicht(self):
        """Der Kernfall: irgendein Fließtext darf nicht als Erklärung durchgehen."""
        beliebig = (
            "<p>Willkommen auf unserer Seite. Wir backen zum Zwecke der Freude "
            "Brot und nehmen jede Beschwerde ernst. Unsere Öffnungszeiten "
            "stehen im Impressum.</p>"
        )
        luecken = validate_document_content(DocumentType.PRIVACY, beliebig)
        assert len(luecken) >= 7, f"Nur {len(luecken)} Lücken gemeldet: {luecken}"

    def test_leeres_dokument_meldet_alle_pflichtangaben(self):
        from legal_text_generator import _MANDATORY_MARKERS

        luecken = validate_document_content(DocumentType.PRIVACY, "")
        assert len(luecken) == len(_MANDATORY_MARKERS[DocumentType.PRIVACY])


def _vorlagen_verzeichnis():
    """Die Vorlagen liegen im Container unter KNOWLEDGE_VAULT_PATH, im Repo daneben."""
    kandidaten = [
        os.path.join(os.getenv("KNOWLEDGE_VAULT_PATH", "/data/knowledge"), "templates", "legal"),
        os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "knowledge", "templates", "legal"
        )),
    ]
    for k in kandidaten:
        if os.path.isdir(k):
            return k
    return None


class TestVorlage:
    """Die Vorlage überstimmt den Prompt - sie muss das Thema also enthalten."""

    @pytest.mark.parametrize("datei,begriffe", [
        ("privacy_de.md", ["Drittland", "Speicherdauer", "Aufsichtsbehörde", "Zweck"]),
        ("privacy_en.md", ["Third-country", "Retention", "supervisory authority", "purpose"]),
    ])
    def test_vorlage_spricht_alle_pflichtangaben_an(self, datei, begriffe):
        verzeichnis = _vorlagen_verzeichnis()
        assert verzeichnis, "Vorlagenverzeichnis nicht gefunden - KNOWLEDGE_VAULT_PATH pruefen"
        pfad = os.path.join(verzeichnis, datei)
        assert os.path.exists(pfad), f"{datei} fehlt in {verzeichnis}"
        text = open(pfad, encoding="utf-8").read()
        fehlend = [b for b in begriffe if b.lower() not in text.lower()]
        assert not fehlend, f"{datei} spricht nicht an: {fehlend}"

    def test_vorlage_fuehrt_keine_unbekannten_platzhalter_ein(self):
        """Unbekannte {{slots}} bleiben woertlich im Prompt stehen."""
        import re

        verzeichnis = _vorlagen_verzeichnis()
        assert verzeichnis, "Vorlagenverzeichnis nicht gefunden"
        pfad = os.path.join(verzeichnis, "privacy_de.md")
        bekannt = {
            "company_name", "address", "zip_city", "email", "phone",
            "dpo_name", "dpo_email", "services_used", "hosting_provider",
            "server_location", "uses_analytics", "uses_marketing",
            "third_party_cookies", "has_registration", "has_contact_form",
            "has_newsletter", "has_shop", "payment_providers", "generated_at",
        }
        gefunden = set(re.findall(r"\{\{(\w+)\}\}", open(pfad, encoding="utf-8").read()))
        assert gefunden <= bekannt, f"Unbekannte Platzhalter: {sorted(gefunden - bekannt)}"
