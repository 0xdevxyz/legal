"""
Knowledge-Vault-Anbindung des Rechtstext-Generators
===================================================

Hintergrund (2026-07-17): `TEMPLATES_DIR`/`LAWS_DIR` waren repo-relativ
(`backend/../knowledge`) verdrahtet. Im Container liegt der Code aber in `/app`,
also lösten sie zu `/knowledge` auf — nicht vorhanden; der Vault ist read-only
nach `/data/knowledge` gemountet (`KNOWLEDGE_VAULT_PATH`). Zusätzlich kollidiert
der Name mit dem Python-Paket `/app/knowledge`.

Wirkung: `_load_template()` lieferte einen 51-Zeichen-Stub statt der Vorlage,
`_load_laws_context()` 47 Zeichen statt ~2000 Zeichen Gesetzestext — **jeder**
Rechtstext entstand ohne Vorlage und ohne Gesetzeskontext, ohne sichtbaren Fehler.

Diese Tests laufen im Backend-Container (`docker exec complyo-backend python -m pytest`)
und prüfen die Verdrahtung dort, wo sie kaputt war: zur Laufzeit.
"""
import os

import pytest

ltg = pytest.importorskip("legal_text_generator")


class TestVaultPfade:
    def test_templates_dir_existiert(self):
        assert os.path.isdir(ltg.TEMPLATES_DIR), (
            f"TEMPLATES_DIR zeigt ins Leere: {ltg.TEMPLATES_DIR}. "
            f"Ohne Templates werden Rechtstexte frei improvisiert."
        )

    def test_laws_dir_existiert(self):
        assert os.path.isdir(ltg.LAWS_DIR), f"LAWS_DIR zeigt ins Leere: {ltg.LAWS_DIR}"

    def test_env_wird_beachtet(self):
        """Der Container setzt KNOWLEDGE_VAULT_PATH — der Generator muss sie nutzen."""
        env = os.getenv("KNOWLEDGE_VAULT_PATH")
        if not env:
            pytest.skip("KNOWLEDGE_VAULT_PATH nicht gesetzt (Host-Lauf)")
        assert ltg.KNOWLEDGE_DIR == env


class TestTemplatesGeladen:
    @pytest.mark.parametrize(
        "doc_type",
        [
            ltg.DocumentType.IMPRINT,
            ltg.DocumentType.PRIVACY,
            ltg.DocumentType.TOS,
            ltg.DocumentType.COOKIE_POLICY,
            ltg.DocumentType.WITHDRAWAL,
        ],
    )
    def test_jedes_template_wird_gefunden(self, doc_type):
        gen = ltg.LegalTextGenerator(None)
        text = gen._load_template(doc_type, "de")
        # Der Stub-Fallback ist ~51 Zeichen. Eine echte Vorlage ist um Grössenordnungen länger.
        assert len(text) > 200, (
            f"Template für {doc_type.value} nicht geladen (nur {len(text)} Zeichen) — "
            f"das ist der Stub-Fallback, keine Vorlage."
        )
        assert not text.startswith("Erstelle "), "Stub-Fallback statt echter Vorlage"


class TestGesetzeskontext:
    @pytest.mark.parametrize("gesetz", ["DSGVO", "TTDSG", "Impressumspflicht", "AGB-Recht", "UWG"])
    def test_gesetz_liefert_kontext(self, gesetz):
        gen = ltg.LegalTextGenerator(None)
        ctx = gen._load_laws_context([gesetz], "de")
        assert len(ctx) > 200, (
            f"Kein Gesetzeskontext für {gesetz} (nur {len(ctx)} Zeichen) — "
            f"die KI generiert dann ohne Rechtsgrundlage."
        )

    def test_fehlende_gesetze_sind_bekannt(self):
        """`generate_withdrawal` fordert Widerrufsrecht + Verbraucherrecht an — beide fehlen.

        Dokumentiert in data/features/legal-text-generator.md. Schlägt der Test um,
        weil die Dateien angelegt wurden: erwartete Liste leeren und den Doku-Eintrag
        streichen.
        """
        fehlend = [
            name
            for name in ("Widerrufsrecht", "Verbraucherrecht")
            if not os.path.exists(os.path.join(ltg.LAWS_DIR, f"{name}.md"))
            and not os.path.exists(os.path.join(ltg.LAWS_DIR, "de", f"{name}.md"))
        ]
        assert fehlend == ["Widerrufsrecht", "Verbraucherrecht"], (
            f"Erwarteter Ist-Zustand geändert — fehlend: {fehlend}. "
            f"Doku data/features/legal-text-generator.md nachziehen."
        )
