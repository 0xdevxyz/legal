"""Wächter: Jede Tabelle, die der Code INSERTet/liest, muss im Schema existieren.

Hintergrund (2026-07-17): Der Alembic-Baseline-Cut (pg_dump) hat Tabellen nicht
übernommen, die aktiver Code weiterhin beschreibt — `leads`, `lead_consents`,
`communication_log`, `email_verifications`, `fix_application_audit`, `fix_backups`.
Folge: `POST /api/leads/collect` und die Fix-Audit-Endpunkte liefen in 500, ohne
dass ein Test es bemerkte. Revision `0003_missing_tables` zieht sie nach.

Dieser Test prüft statisch, dass die Tabellen, die im Code per `INSERT INTO` /
`FROM` referenziert werden, entweder in der Baseline oder in einer Revision
angelegt werden. Er braucht keine laufende DB und hätte den Verlust gemeldet.
"""
import os
import re
import glob

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tabellen, die (noch) bewusst NICHT im Schema stehen — dazu steht eine
# Produktentscheidung aus (Feature behalten oder Router entfernen). Siehe
# data/features/00_FEATURES_INDEX.md, Abschnitt "Registrierte Router ohne Doku".
# Leer: die einzige Ausnahme war "expert_service_requests" aus dem am
# 2026-07-29 stillgelegten Expert-Router. Der Router ist am 2026-08-31
# geloescht worden, damit ist die offene Produktentscheidung entschieden und
# die Ausnahme gegenstandslos. Wer den Expert-Service reaktiviert, holt Router
# UND Tabelle aus der Historie.
BEKANNTE_AUSNAHMEN = set()

# Nicht-Tabellen bzw. CTEs/Aliasse, die dem Regex sonst ins Netz gehen.
IGNORIEREN = {"jsonb_to_recordset", "unnest", "json_array_elements"}


def _schema_tabellen() -> set:
    """Tabellennamen aus baseline_schema.sql + allen Alembic-Revisionen."""
    namen = set()
    quellen = [os.path.join(BACKEND, "alembic", "baseline_schema.sql")]
    quellen += glob.glob(os.path.join(BACKEND, "alembic", "versions", "*.py"))
    for pfad in quellen:
        if not os.path.exists(pfad):
            continue
        with open(pfad, encoding="utf-8") as fh:
            text = fh.read()
        for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?(?:public\.)?[\"']?(\w+)", text, re.I):
            namen.add(m.group(1).lower())
        # Revisionen, die op.create_table statt rohem SQL nutzen (z. B. 0014
        # gdpr_deletion_requests), zählen ebenfalls zum Schema.
        for m in re.finditer(r"op\.create_table\(\s*[\"'](\w+)[\"']", text):
            namen.add(m.group(1).lower())
    return namen


def _quelldateien() -> list:
    """Alle Anwendungsdateien - rekursiv.

    Bis zum 03.09.2026 stand hier glob("backend/*.py"), also nur die oberste
    Ebene: 87 von 201 Dateien. Alles unter cronjobs/, compliance_engine/,
    payment/, ai_fix_engine/ und knowledge/ war fuer diesen Waechter unsichtbar
    - und genau dort sassen saemtliche stillen Schema-Ausfaelle der letzten
    Wochen: scan_issues (knowledge/pattern_extractor.py),
    knowledge_rule_review_queue (cronjobs/knowledge_updater.py), die
    Zahlungstabellen unter payment/. Der Test war gruen, waehrend im Cron-Log
    woechentlich "relation does not exist" stand.

    alembic/ und tests/ bleiben aussen vor: dort steht SQL, das das Schema
    beschreibt oder erfindet, nicht Code, der es benutzt.
    """
    alle = glob.glob(os.path.join(BACKEND, "**", "*.py"), recursive=True)
    return [
        p for p in alle
        if f"{os.sep}alembic{os.sep}" not in p and f"{os.sep}tests{os.sep}" not in p
    ]


def _referenzierte_tabellen() -> dict:
    """Tabellen, die der Anwendungscode schreibt/liest → {tabelle: beispieldatei}."""
    treffer = {}
    muster = re.compile(r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|FROM|JOIN)\s+[\"']?(\w+)", re.I)
    for pfad in _quelldateien():
        with open(pfad, encoding="utf-8") as fh:
            text = fh.read()
        for m in muster.finditer(text):
            name = m.group(1).lower()
            treffer.setdefault(name, os.path.relpath(pfad, BACKEND))
    return treffer


def test_alle_referenzierten_tabellen_im_schema():
    schema = _schema_tabellen()
    referenziert = _referenzierte_tabellen()

    # Nur Namen prüfen, die plausibel Tabellen sind (im Schema ODER als Ausnahme bekannt
    # ODER eindeutig referenziert). SQL-Schlüsselwörter/Aliasse rausfiltern: ein Name
    # gilt als Tabellenkandidat, wenn er auch irgendwo im Schema steht — sonst könnte er
    # ein Alias sein. Fehlende Tabellen sind genau die, die referenziert werden, NICHT im
    # Schema stehen und NICHT als bekannte Ausnahme markiert sind.
    fehlend = {}
    for name, datei in referenziert.items():
        if name in schema or name in BEKANNTE_AUSNAHMEN or name in IGNORIEREN:
            continue
        # Heuristik gegen Aliasse/CTEs: nur melden, wenn der Name wie ein echter
        # Tabellenname aussieht (mind. ein "_" oder Plural) UND per INSERT/UPDATE
        # geschrieben wird — Schreibzugriffe sind eindeutig Tabellen.
        if _wird_geschrieben(name):
            fehlend[name] = datei

    assert not fehlend, (
        "Tabellen werden vom Code geschrieben, fehlen aber im Schema (Baseline + "
        "Revisionen). Entweder per neuer Alembic-Revision nachziehen oder in "
        f"BEKANNTE_AUSNAHMEN aufnehmen:\n"
        + "\n".join(f"  - {t} (z.B. in {d})" for t, d in sorted(fehlend.items()))
    )


def _wird_geschrieben(tabelle: str) -> bool:
    muster = re.compile(rf"\bINSERT\s+INTO\s+[\"']?{re.escape(tabelle)}\b", re.I)
    for pfad in _quelldateien():
        with open(pfad, encoding="utf-8") as fh:
            if muster.search(fh.read()):
                return True
    return False


def test_nachgezogene_tabellen_sind_da():
    """Die konkret beim Baseline-Cut verlorenen Tabellen (Regression-Fixpunkt)."""
    schema = _schema_tabellen()
    erwartet = {
        "leads",
        "lead_consents",
        "communication_log",
        "email_verifications",
        "fix_application_audit",
        "fix_backups",
    }
    fehlend = erwartet - schema
    assert not fehlend, f"Revision 0003 unvollständig — fehlend im Schema: {sorted(fehlend)}"
