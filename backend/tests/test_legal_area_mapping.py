"""
Regressionstests für die Auflösung Rechtsbereich -> Dokumenttyp.

Hintergrund (Bug): legal_change_monitor übergab LegalArea-Werte
("datenschutz", "cookie_compliance", ...), legal_text_generator erwartete
aber Gesetzesnamen ("DSGVO", "TTDSG", ...). Der Substring-Vergleich traf für
KEINEN der 7 Werte -> es wurde nie ein Rechtstext automatisch regeneriert.

Diese Tests prüfen jeden LegalArea-Wert einzeln und enthalten einen Wächter,
der anschlägt, sobald ein neuer LegalArea-Wert ohne Mapping hinzukommt.
"""

import pytest

from legal_change_monitor import LegalArea
from legal_text_generator import (
    DocumentType,
    LEGAL_AREA_TO_DOCUMENT_TYPES,
    resolve_document_types,
)


# Erwartete Zuordnung — bewusst hier dupliziert, damit der Test eine eigene
# Aussage trifft und nicht nur die Implementierung gegen sich selbst prüft.
EXPECTED = {
    LegalArea.DATENSCHUTZ: {DocumentType.PRIVACY, DocumentType.COOKIE_POLICY},
    LegalArea.COOKIE_COMPLIANCE: {DocumentType.PRIVACY, DocumentType.COOKIE_POLICY},
    LegalArea.IMPRESSUM: {DocumentType.IMPRINT},
    LegalArea.BARRIEREFREIHEIT: {DocumentType.IMPRINT},
    LegalArea.WETTBEWERBSRECHT: {DocumentType.TOS},
    LegalArea.VERBRAUCHERSCHUTZ: {DocumentType.TOS, DocumentType.WITHDRAWAL},
    LegalArea.AI_ACT: set(),  # kein generierter Rechtstext-Typ
}


@pytest.mark.parametrize("area,expected", list(EXPECTED.items()), ids=lambda v: getattr(v, "value", ""))
def test_each_legal_area_resolves_to_expected_document_types(area, expected):
    """Jeder einzelne LegalArea-Wert muss die erwarteten Dokumenttypen liefern."""
    assert set(resolve_document_types([area.value])) == expected


def test_all_legal_areas_except_ai_act_resolve_to_something():
    """Der ursprüngliche Bug: ALLE Bereiche lösten zu einer leeren Menge auf."""
    resolvable = [
        area.value for area in LegalArea
        if resolve_document_types([area.value])
    ]
    # 6 von 7 müssen auflösen (ai_act hat bewusst keinen Rechtstext-Typ)
    assert len(resolvable) == 6, f"Nur {resolvable} lösen auf"
    assert LegalArea.AI_ACT.value not in resolvable


def test_guard_every_legal_area_has_an_explicit_mapping():
    """
    Wächter: Ein neu hinzugefügter LegalArea-Wert MUSS in
    LEGAL_AREA_TO_DOCUMENT_TYPES eingetragen werden. Genau dieser Test hätte
    den ursprünglichen Bug verhindert.
    """
    missing = [
        area.value for area in LegalArea
        if area.value not in LEGAL_AREA_TO_DOCUMENT_TYPES
    ]
    assert missing == [], (
        f"LegalArea-Werte ohne Mapping: {missing} — bitte in "
        f"legal_text_generator.LEGAL_AREA_TO_DOCUMENT_TYPES ergänzen."
    )


def test_guard_no_stale_keys_in_mapping():
    """Umgekehrter Wächter: keine verwaisten Schlüssel ohne LegalArea."""
    valid = {area.value for area in LegalArea}
    stale = [key for key in LEGAL_AREA_TO_DOCUMENT_TYPES if key not in valid]
    assert stale == [], f"Mapping enthält unbekannte Rechtsbereiche: {stale}"


def test_mapping_values_are_real_document_types():
    valid = set(DocumentType)
    for area, types in LEGAL_AREA_TO_DOCUMENT_TYPES.items():
        for t in types:
            assert t in valid, f"{area} -> {t} ist kein DocumentType"


def test_multiple_areas_are_merged_without_duplicates():
    result = resolve_document_types(["datenschutz", "cookie_compliance", "impressum"])
    assert len(result) == len(set(result)), "Dokumenttypen dürfen nicht doppelt vorkommen"
    assert set(result) == {DocumentType.PRIVACY, DocumentType.COOKIE_POLICY, DocumentType.IMPRINT}


def test_unknown_area_is_ignored_but_others_still_resolve():
    result = resolve_document_types(["voellig_unbekannt", "impressum"])
    assert set(result) == {DocumentType.IMPRINT}


def test_unknown_area_alone_resolves_to_empty():
    assert resolve_document_types(["voellig_unbekannt"]) == []


def test_empty_input_resolves_to_empty():
    assert resolve_document_types([]) == []


# --- Alias-Pfad: Gesetzesnamen -----------------------------------------------

@pytest.mark.parametrize("law,expected", [
    ("DSGVO", {DocumentType.PRIVACY, DocumentType.COOKIE_POLICY}),
    ("TTDSG", {DocumentType.PRIVACY, DocumentType.COOKIE_POLICY}),
    ("Impressumspflicht", {DocumentType.IMPRINT}),
    ("BFSG", {DocumentType.IMPRINT}),
    ("UWG", {DocumentType.TOS}),
    ("Widerrufsrecht", {DocumentType.TOS, DocumentType.WITHDRAWAL}),
])
def test_law_names_still_resolve_via_alias(law, expected):
    """Gesetzesnamen (Alt-Aufrufform) müssen ebenfalls auflösen."""
    assert set(resolve_document_types([law])) == expected


def test_law_name_substring_resolves():
    """Freitext wie 'DSGVO-Novelle 2026' soll noch auflösen."""
    assert set(resolve_document_types(["DSGVO-Novelle 2026"])) == {
        DocumentType.PRIVACY,
        DocumentType.COOKIE_POLICY,
    }
