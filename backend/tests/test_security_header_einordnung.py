# -*- coding: utf-8 -*-
"""Die vier Security-Header-Befunde sind Stand der Technik, kein Verstoss.

Am 18.09.2026 gepruefte Ausgangslage: die vier Befunde traten als
DSGVO-Art.-32-Verstoss auf, drei davon mit 500 Euro Risiko, und beriefen sich
auf einen IT-Grundschutz-Baustein "TLS.1", den es nicht gibt. Die Bausteine
tragen die Praefixe ISMS, ORP, CON, OPS, DER, APP, SYS, IND, NET und INF.

Die richtige Quelle ist APP.3.1.A21 "Sichere HTTP-Konfiguration bei
Webanwendungen". Sie zaehlt genau Content-Security-Policy,
Strict-Transport-Security, Content-Type, X-Content-Type-Options und
Cache-Control auf und ist eine STANDARD-Anforderung ("SOLLTEN"). Das BSI
definiert Basis- und Standard-Anforderungen zusammen als Stand der Technik.
Art. 32 Abs. 1 DSGVO verlangt Massnahmen "unter Beruecksichtigung des Stands
der Technik", und nur, soweit personenbezogene Daten verarbeitet werden.

Daraus folgt beides, was dieser Waechter festhaelt: die Quelle muss stimmen,
und ein fehlender Header traegt keinen Eurobetrag. Ein Eurobetrag behauptet
ein bezifferbares Risiko; fuer einen fehlenden CSP-Header gibt es weder
Bussgeld noch Abmahnpraxis, auf die man sich berufen koennte. Mixed Content
steht bewusst anders da: APP.3.2.A11 ist eine Basis-Anforderung und sagt
"DARF NICHT".

Quellen, am 18.09.2026 aus den BSI-PDFs gelesen:
  APP.3.1 Webanwendungen und Webservices, Edition 2022, A21
  APP.3.2 Webserver, Edition 2023, A11
"""

import ast
import os

import pytest

SCANNER = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "compliance_engine", "scanner.py"))

HEADER_BEFUNDE = ("HSTS", "Content-Security-Policy", "X-Content-Type-Options",
                  "Clickjacking")


def _befunde():
    """Alle ComplianceIssue(...)-Aufrufe im Scanner als Woerterbuecher.

    Ueber den Syntaxbaum statt per Regex: ein Befund kann ueber mehrere
    Zeilen und ueber zusammengesetzte Zeichenketten gehen, und genau dort
    haette eine Regex den falschen Treffer geliefert.
    """
    baum = ast.parse(open(SCANNER, encoding="utf-8").read())
    raus = []
    for knoten in ast.walk(baum):
        if not isinstance(knoten, ast.Call):
            continue
        name = getattr(knoten.func, "id", None) or getattr(knoten.func, "attr", None)
        if name != "ComplianceIssue":
            continue
        eintrag = {}
        for kw in knoten.keywords:
            if isinstance(kw.value, ast.Constant):
                eintrag[kw.arg] = kw.value.value
            elif isinstance(kw.value, ast.JoinedStr):
                eintrag[kw.arg] = "".join(
                    t.value for t in kw.value.values if isinstance(t, ast.Constant))
        if eintrag.get("title"):
            raus.append(eintrag)
    return raus


def _mit_titel(teil):
    treffer = [b for b in _befunde() if teil in (b.get("title") or "")]
    assert treffer, f"Befund mit '{teil}' im Titel nicht gefunden"
    return treffer


class TestEinordnungHttpHeader:
    @pytest.mark.parametrize("teil", HEADER_BEFUNDE)
    def test_nennt_die_richtige_quelle(self, teil):
        for b in _mit_titel(teil):
            assert "APP.3.1.A21" in (b.get("legal_basis") or ""), (
                f"{teil}: Quelle ist APP.3.1.A21, nicht "
                f"{b.get('legal_basis')!r}"
            )

    @pytest.mark.parametrize("teil", HEADER_BEFUNDE)
    def test_traegt_keinen_eurobetrag(self, teil):
        for b in _mit_titel(teil):
            assert b.get("risk_euro") == 0, (
                f"{teil}: {b.get('risk_euro')} Euro behaupten ein bezifferbares "
                "Risiko. Fuer eine Abweichung vom Stand der Technik gibt es "
                "weder Bussgeld noch Abmahnpraxis, auf die sich das stuetzen "
                "liesse."
            )

    def test_kein_erfundener_baustein(self):
        # Geprueft werden die Quellenangaben, nicht der Dateitext: die
        # Begruendung im Kommentar nennt den falschen Baustein zu Recht.
        for b in _befunde():
            grundlage = b.get("legal_basis") or ""
            assert "TLS.1" not in grundlage, (
                f"{b.get('title')!r}: einen IT-Grundschutz-Baustein 'TLS.1' "
                "gibt es nicht. Die Bausteine tragen die Praefixe ISMS, ORP, "
                "CON, OPS, DER, APP, SYS, IND, NET und INF."
            )

    def test_verbandsliste_ist_keine_rechtsgrundlage(self):
        for b in _befunde():
            grundlage = b.get("legal_basis") or ""
            assert "OWASP" not in grundlage, (
                f"{b.get('title')!r}: Die OWASP Top 10 sind eine Verbandsliste. "
                "Neben einer Norm gelistet sehen beide gleich verbindlich aus."
            )

    def test_mixed_content_bleibt_basis_anforderung(self):
        for b in _mit_titel("Mixed Content"):
            assert "APP.3.2.A11" in (b.get("legal_basis") or ""), (
                "Mixed Content ist keine Empfehlung: APP.3.2.A11 sagt "
                "'DARF NICHT'. Das gehoert in die Quellenangabe."
            )
