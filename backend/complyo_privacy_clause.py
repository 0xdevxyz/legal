"""
Complyo-Datenschutz-Passus — deterministischer Baustein-Generator.

Sobald ein Kunde Complyo auf seiner Website einsetzt (Cookie-Consent-Banner,
Barrierefreiheits-Widget), wird Complyo zum verarbeitenden Dienst und muss in
der *eigenen* Datenschutzerklärung des Kunden gemäß Art. 13 DSGVO genannt werden.

Dieser Baustein wird NICHT von der KI generiert, sondern deterministisch aus
festem, juristisch geprüftem Wortlaut zusammengesetzt — die Rechtsgrundlage,
der Drittland-Hinweis und die Nachweispflicht (§ 25 TDDDG) dürfen nicht durch
ein Sprachmodell umformuliert oder weggelassen werden.

Der Passus ist MODULAR: es werden ausschließlich Abschnitte für tatsächlich
aktive Dienste ausgegeben (keine Beschreibung einer Verarbeitung, die beim
Kunden nicht stattfindet).

Eingebunden in legal_text_generator.generate_privacy_policy() und nach der
KI-Generierung in das HTML injiziert (vor dem Disclaimer).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Betreiber-Stammdaten. Zentral pflegbar; bei Änderung der Rechtsform/Anschrift
# hier anpassen. Quelle: bestehende Nennung in email_service.py / gdpr_api.py.
# ─────────────────────────────────────────────────────────────────────────────
COMPLYO_PROVIDER_NAME = "Complyo GmbH"
COMPLYO_PROVIDER_ADDRESS = "Koburger Straße 198, 04416 Markkleeberg"
COMPLYO_PROVIDER_CONTACT = "datenschutz@complyo.de"
COMPLYO_API_HOST = "api.complyo.de"
# Verweis auf den im Dashboard generierbaren Auftragsverarbeitungsvertrag (Art. 28).
# Bewusst neutral formuliert: der AVV wird bereitgestellt und ist abzuschließen —
# es wird NICHT behauptet, dass bereits einer geschlossen wurde (das hängt vom
# Onboarding-Stand des jeweiligen Kunden ab). Siehe planning/AVV_ONBOARDING_PLAN.md.
COMPLYO_AVV_HINT = (
    "Für diese Auftragsverarbeitung stellt die {provider} einen "
    "Auftragsverarbeitungsvertrag (AVV) gemäß Art. 28 DSGVO bereit, der zwischen "
    "dem Betreiber dieser Website und der {provider} abzuschließen ist."
).format(provider=COMPLYO_PROVIDER_NAME)


@dataclass
class ComplyoServiceContext:
    """Beschreibt, welche Complyo-Dienste beim Kunden aktiv sind.

    Wird aus `cookie_banner_configs` (autoritative Quelle) abgeleitet.
    """

    cookie_banner_active: bool = False
    cookie_lifetime_days: int = 365
    a11y_widget_active: bool = False
    # True, sobald über das Consent-Tool Dienste mit Drittlandbezug (Art. 49)
    # angeboten werden — dann gilt das Drittland-Gating (gesonderte Einwilligung).
    third_country_services_enabled: bool = False

    def any_active(self) -> bool:
        return self.cookie_banner_active or self.a11y_widget_active

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ComplyoServiceContext":
        if not data:
            return cls()
        return cls(
            cookie_banner_active=bool(data.get("cookie_banner_active", False)),
            cookie_lifetime_days=int(data.get("cookie_lifetime_days", 365) or 365),
            a11y_widget_active=bool(data.get("a11y_widget_active", False)),
            third_country_services_enabled=bool(
                data.get("third_country_services_enabled", False)
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Persistierbar in metadata.user_data, damit das Auto-Update
        (legal_change_monitor → regenerate_affected_users) den Passus
        bei Gesetzesänderungen identisch reproduziert."""
        return {
            "cookie_banner_active": self.cookie_banner_active,
            "cookie_lifetime_days": self.cookie_lifetime_days,
            "a11y_widget_active": self.a11y_widget_active,
            "third_country_services_enabled": self.third_country_services_enabled,
        }


def _header_block() -> str:
    return (
        "<h2>Einsatz von Complyo (Einwilligungs- und Barrierefreiheits-Dienst)</h2>\n"
        "<p>Diese Website nutzt Dienste der "
        f"<strong>{COMPLYO_PROVIDER_NAME}</strong>, {COMPLYO_PROVIDER_ADDRESS} "
        "(„Complyo“), um gesetzliche "
        "Pflichten im Bereich Datenschutz und digitale Barrierefreiheit zu erfüllen. "
        "Complyo handelt dabei als Auftragsverarbeiter des Betreibers dieser Website "
        f"im Sinne des Art. 28 DSGVO. {COMPLYO_AVV_HINT}</p>\n"
        "<p>Complyo wird ausschließlich auf Servern innerhalb der Europäischen Union "
        f"(<code>{COMPLYO_API_HOST}</code>) betrieben. Eine Übermittlung "
        "personenbezogener Daten durch Complyo selbst in ein Drittland außerhalb der "
        "EU/des EWR findet nicht statt.</p>"
    )


def _cookie_banner_block(ctx: ComplyoServiceContext) -> str:
    days = ctx.cookie_lifetime_days
    third_country = ""
    if ctx.third_country_services_enabled:
        third_country = (
            "<p>Werden über das Einwilligungs-Tool Dienste eingebunden, die "
            "personenbezogene Daten in ein Drittland ohne Angemessenheitsbeschluss "
            "(insbesondere die USA) übermitteln, werden diese erst nach Ihrer "
            "gesonderten, ausdrücklichen Einwilligung gemäß Art. 49 Abs. 1 lit. a "
            "DSGVO geladen. Ohne diese Einwilligung unterbleibt die Einbindung.</p>\n"
        )
    return (
        "<h3>Cookie-Einwilligungsverwaltung (Consent-Management)</h3>\n"
        "<p>Zur Einholung und Dokumentation Ihrer Einwilligung in nicht zwingend "
        "erforderliche Cookies und vergleichbare Technologien setzen wir das "
        "Consent-Management von Complyo ein. Dabei werden folgende Daten "
        "verarbeitet:</p>\n"
        "<ul>\n"
        "  <li>eine pseudonyme Besucher-Kennung (zufällig erzeugte ID, lokal in "
        "Ihrem Browser gespeichert)</li>\n"
        "  <li>Ihre Einwilligungsentscheidung je Cookie-Kategorie "
        "(notwendig, funktional, Statistik, Marketing)</li>\n"
        "  <li>Zeitpunkt der Einwilligung sowie die Version des Einwilligungs-Banners</li>\n"
        "  <li>technische Angaben wie Browser-Sprache zur korrekten Anzeige</li>\n"
        "</ul>\n"
        "<p><strong>Rechtsgrundlage</strong> für das Speichern und Auslesen der "
        "Einwilligungsdaten auf Ihrem Endgerät ist § 25 Abs. 2 Nr. 2 TDDDG (vormals "
        "TTDSG); die nachgelagerte Verarbeitung zur Erfüllung unserer Nachweispflicht "
        "über erteilte Einwilligungen stützt sich auf Art. 6 Abs. 1 lit. c DSGVO "
        "i.V.m. Art. 7 Abs. 1 DSGVO (rechtliche Verpflichtung / Rechenschaftspflicht).</p>\n"
        f"<p><strong>Speicherdauer:</strong> Ihre Einwilligungsentscheidung wird für "
        f"{days} Tage gespeichert; danach werden Sie erneut um Ihre Einwilligung "
        "gebeten.</p>\n"
        "<p><strong>Widerruf:</strong> Sie können Ihre Cookie-Einstellungen jederzeit "
        "mit Wirkung für die Zukunft ändern oder widerrufen, indem Sie das "
        "Einwilligungs-Banner erneut über die entsprechende Schaltfläche auf dieser "
        "Website aufrufen.</p>\n"
        f"{third_country}"
    )


def _a11y_block() -> str:
    return (
        "<h3>Barrierefreiheits-Assistent</h3>\n"
        "<p>Zur Verbesserung der Zugänglichkeit bindet diese Website den "
        "Barrierefreiheits-Assistenten von Complyo ein. Das hierfür erforderliche "
        f"Skript wird zur Laufzeit von den EU-Servern von Complyo "
        f"(<code>{COMPLYO_API_HOST}</code>) geladen; dabei wird technisch bedingt "
        "Ihre IP-Adresse übertragen. Von Ihnen vorgenommene Anzeige-Einstellungen "
        "(z.&nbsp;B. Kontrast, Schriftgröße) werden ausschließlich lokal in Ihrem "
        "Browser gespeichert und nicht an Complyo übermittelt.</p>\n"
        "<p><strong>Rechtsgrundlage</strong> ist Art. 6 Abs. 1 lit. c DSGVO "
        "i.V.m. dem Barrierefreiheitsstärkungsgesetz (BFSG) sowie unser berechtigtes "
        "Interesse an einer barrierefreien Website gemäß Art. 6 Abs. 1 lit. f DSGVO.</p>"
    )


def build_complyo_privacy_clause(context: Optional[Dict[str, Any]]) -> str:
    """Baut den Complyo-Datenschutz-Passus als HTML.

    Gibt einen leeren String zurück, wenn kein Complyo-Dienst aktiv ist —
    dann erscheint der Abschnitt nicht in der Datenschutzerklärung.
    """
    ctx = ComplyoServiceContext.from_dict(context)
    if not ctx.any_active():
        return ""

    blocks = [_header_block()]
    if ctx.cookie_banner_active:
        blocks.append(_cookie_banner_block(ctx))
    if ctx.a11y_widget_active:
        blocks.append(_a11y_block())

    return "\n" + "\n".join(blocks) + "\n"
