"""Der Schema-Waechter muss in die Unterverzeichnisse schauen.

Bis zum 03.09.2026 las test_schema_completeness nur glob("backend/*.py") -
87 von 201 Dateien. Alles unter cronjobs/, compliance_engine/, payment/,
ai_fix_engine/ und knowledge/ war unsichtbar. Genau dort sassen saemtliche
stillen Schema-Ausfaelle: scan_issues, knowledge_rule_review_queue, die
Zahlungstabellen. Der Waechter war gruen, waehrend im Cron-Log woechentlich
"relation does not exist" stand.

Ein Waechter, der nur die oberste Ebene prueft, gibt Sicherheit vor, die er
nicht hat. Dieser Test haelt die Tiefe fest.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_schema_completeness import _quelldateien

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_waechter_sieht_unterverzeichnisse():
    dateien = _quelldateien()
    relativ = {os.path.relpath(p, BACKEND) for p in dateien}
    unterverzeichnisse = {p.split(os.sep)[0] for p in relativ if os.sep in p}

    for erwartet in ("cronjobs", "compliance_engine", "knowledge"):
        assert erwartet in unterverzeichnisse, (
            f"{erwartet}/ wird nicht durchsucht - genau dort sassen die stillen Ausfaelle"
        )


def test_waechter_prueft_mehr_als_die_oberste_ebene():
    import glob

    flach = glob.glob(os.path.join(BACKEND, "*.py"))
    tief = _quelldateien()
    assert len(tief) > len(flach) * 1.5, (
        f"Nur {len(tief)} Dateien gegen {len(flach)} auf oberster Ebene - "
        "der Waechter ist wieder flach"
    )


def test_alembic_und_tests_bleiben_aussen_vor():
    """Dort steht SQL, das Schema beschreibt oder erfindet - nicht Code, der es nutzt."""
    for pfad in _quelldateien():
        assert f"{os.sep}alembic{os.sep}" not in pfad
        assert f"{os.sep}tests{os.sep}" not in pfad
