"""
Widerrufsrecht und Kuendigungsknopf nur gegenueber Verbrauchern.

Der Shop-Check verlangte beides von jedem Abo-Anbieter. §§ 312g, 355 BGB
(Widerruf) und § 312k BGB (Kuendigungsknopf) setzen aber einen
Verbrauchervertrag voraus — ein reiner B2B-Anbieter bekam zwei kritische
Befunde fuer Pflichten, die ihn nicht treffen.

Die Erkennung muss in beide Richtungen sitzen: sie darf die Klarstellung nicht
uebersehen, und sie darf sie nicht in Seiten hineinlesen, die nur Nettopreise
ausweisen oder sich "fuer Unternehmen" nennen. Im Zweifel gilt
Verbrauchergeschaeft — das ist die sichere Richtung.
"""

import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.shop_check import erkenne_reines_b2b


def suppe(text: str) -> BeautifulSoup:
    return BeautifulSoup(f"<html><body><main>{text}</main></body></html>", 'html.parser')


ERKENNT = [
    "Unser Angebot richtet sich ausschließlich an Unternehmer im Sinne des § 14 BGB.",
    "Unsere Angebote richten sich ausschliesslich an Unternehmer im Sinne des § 14 BGB.",
    "Ein Vertragsschluss mit Verbrauchern im Sinne des § 13 BGB ist ausgeschlossen.",
    "Wir verkaufen nur an Unternehmer und juristische Personen des öffentlichen Rechts.",
    "Das Angebot richtet sich an gewerbliche Kunden.",
    "Verkauf nicht an Verbraucher.",
]

ERKENNT_NICHT = [
    # Nettopreise sind ein Indiz, kein Ausschluss von Verbrauchern
    "Alle Preise verstehen sich zzgl. gesetzlicher MwSt.",
    # Zielgruppenwerbung ist keine Rechtsklarstellung
    "Die Compliance-Plattform für Unternehmen jeder Größe.",
    "Business-Tarif für professionelle Websites.",
    "Tausende Unternehmer vertrauen uns.",
    # Der umgekehrte Fall darf erst recht nicht anschlagen
    "Als Verbraucher haben Sie ein Widerrufsrecht von 14 Tagen.",
    "",
]


class TestB2BWirdErkannt:
    @pytest.mark.parametrize("text", ERKENNT)
    def test_klarstellung_wird_gefunden(self, text):
        assert erkenne_reines_b2b(suppe(text)), f"nicht erkannt: {text!r}"


class TestKeinFalschesB2B:
    @pytest.mark.parametrize("text", ERKENNT_NICHT)
    def test_ohne_klarstellung_bleibt_verbrauchergeschaeft(self, text):
        assert not erkenne_reines_b2b(suppe(text)), (
            f"faelschlich als B2B eingestuft: {text!r} — damit entfielen "
            f"Widerrufsbelehrung und Kuendigungsknopf zu Unrecht"
        )


class TestShopAblauf:
    """Bei erkanntem B2B entfallen die beiden Verbraucherbefunde, und an ihre
    Stelle tritt ein sichtbarer Hinweis auf die getroffene Einstufung."""

    @pytest.mark.asyncio
    async def test_b2b_ersetzt_verbraucherbefunde_durch_hinweis(self):
        from compliance_engine.checks.shop_check import check_shop_compliance

        seite = suppe(
            "<h1>Preise</h1>"
            "<p>Pro-Tarif 49 EUR im Monat im Abo, monatlich kündbar. "
            "Jetzt abonnieren und Tarif buchen.</p>"
            "<p>Unser Angebot richtet sich ausschließlich an Unternehmer "
            "im Sinne des § 14 BGB.</p>"
        )
        befunde = await check_shop_compliance("https://example.test", seite, None)
        titel = [b["title"] for b in befunde]

        assert not any("Widerrufsbelehrung" in t for t in titel), (
            f"Widerrufsbelehrung trotz B2B verlangt: {titel}"
        )
        assert not any("Kündigungsbutton" in t for t in titel), (
            f"Kuendigungsknopf trotz B2B verlangt: {titel}"
        )
        assert any("B2B" in t for t in titel), (
            f"die Einstufung muss sichtbar sein, sonst ist nicht nachvollziehbar, "
            f"warum zwei Pflichten nicht geprueft wurden: {titel}"
        )
