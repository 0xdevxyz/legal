"""Der gespeicherte Scan bekommt seine Saeulenwerte und seinen Rechtsraum.

Gemessen am 25.09.2026 auf der Produktionsdatenbank:

    zeilen | mit_overall | mit_compliance | mit_a11y | mit_legal | mit_cookie
    -------+-------------+----------------+----------+-----------+-----------
        51 |           0 |             51 |        0 |         0 |          0

Die Spalten `overall_score`, `accessibility_score`, `legal_score`,
`cookie_score` und `privacy_score` gibt es seit dem Anfang und sie sind in
jeder der 51 Zeilen leer. Kein INSERT hat sie je beschrieben; geschrieben
wurde nur `compliance_score`.

Gelesen werden sie trotzdem: `_latest_scan_pillars` in
pflichten_report_routes.py holt genau diese fuenf Spalten, um den Ist-Zustand
der Website an die passenden Pflichten zu haengen. Der Aufrufer prueft
`is not None` und laesst die Angabe deshalb sauber weg, statt eine Null zu
behaupten. Das ist der Grund, warum es niemandem auffiel: die Funktion ist
nie sichtbar gescheitert, sie hat nur nie etwas geliefert.

Die Werte waren die ganze Zeit da, eine Ebene tiefer, in `scan_data` als
`pillar_scores` (50 von 51 Zeilen). Diese Migration holt sie nach oben. Sie
erfindet nichts: wo `scan_data` die Saeule nicht nennt, bleibt die Spalte
leer.

Dazu die neue Spalte `jurisdiction`. Seit der Rechtsraum die Wertung
bestimmt, welche Saeulen ueberhaupt in den Punktestand eingehen, ist eine
gespeicherte Zahl ohne ihren Rechtsraum nicht mehr deutbar: 50 Punkte im
Profil "de" und 34 im Profil "eu" bezeichnen denselben Zustand derselben
Website. Die 51 Altzeilen bekommen 'de', und das ist keine Annahme, sondern
der Umstand, dass es bis zum 24.09.2026 keinen Weg gab, einen Scan in einem
anderen Profil zu starten. Neue Zeilen bleiben ohne Vorbelegung: ein
kuenftiger INSERT, der den Rechtsraum vergisst, soll NULL hinterlassen und
damit "unbekannt" sagen, nicht stillschweigend "de" behaupten.

Revision ID: 0035_scan_saeulen_rechtsraum
Revises: 0034_wirkung_plausibel
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0035_scan_saeulen_rechtsraum"
down_revision: Union[str, None] = "0034_wirkung_plausibel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Saeulenname im Scanergebnis -> Spalte in scan_history. Die Namen gehen
# auseinander: die Saeule heisst "gdpr", die Spalte "privacy_score". Genau
# solche Paare gehoeren an eine Stelle, sonst verliert der naechste Leser eine
# davon.
SAEULE_ZU_SPALTE = {
    "accessibility": "accessibility_score",
    "gdpr": "privacy_score",
    "legal": "legal_score",
    "cookies": "cookie_score",
}


def upgrade() -> None:
    op.execute(
        "ALTER TABLE scan_history ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(8)"
    )
    op.execute(
        """
        COMMENT ON COLUMN scan_history.jurisdiction IS
        'Rechtsraum-Profil, unter dem dieser Scan gewertet wurde (compliance_engine/jurisdictions.py). NULL heisst unbekannt. Ohne diesen Wert ist der Punktestand nicht deutbar, weil der Rechtsraum bestimmt, welche Saeulen eingehen.'
        """
    )

    # Altbestand: bis zum 24.09.2026 war das deutsche Profil das einzige
    # erreichbare. Der Wert ist damit belegt, nicht geschaetzt.
    op.execute(
        "UPDATE scan_history SET jurisdiction = 'de' WHERE jurisdiction IS NULL"
    )

    # Saeulenwerte aus scan_data nachtragen. Nur dort, wo die Spalte leer ist
    # und scan_data die Saeule wirklich nennt: ein spaeterer, richtig
    # geschriebener Wert darf nicht von einem alten JSONB ueberschrieben
    # werden, und eine fehlende Saeule bleibt fehlend.
    for saeule, spalte in SAEULE_ZU_SPALTE.items():
        op.execute(
            f"""
            UPDATE scan_history AS s
            SET {spalte} = q.wert
            FROM (
                SELECT h.id,
                       (e->>'score')::double precision AS wert
                FROM scan_history AS h
                CROSS JOIN LATERAL jsonb_array_elements(h.scan_data->'pillar_scores') AS e
                WHERE jsonb_typeof(h.scan_data->'pillar_scores') = 'array'
                  AND e->>'pillar' = '{saeule}'
                  AND e->>'score' IS NOT NULL
            ) AS q
            WHERE s.id = q.id AND s.{spalte} IS NULL
            """
        )

    # Der Gesamtwert stand als compliance_score schon in der Zeile. Er ist
    # dieselbe Groesse unter einem zweiten Namen, und der Report liest den
    # zweiten.
    op.execute(
        """
        UPDATE scan_history
        SET overall_score = compliance_score
        WHERE overall_score IS NULL AND compliance_score IS NOT NULL
        """
    )


def downgrade() -> None:
    # Die nachgetragenen Saeulenwerte werden NICHT wieder geleert. Sie sind aus
    # scan_data abgeleitet, stehen dort unveraendert weiter und waren vorher
    # nur deshalb leer, weil sie niemand geschrieben hat. Ein Downgrade, das
    # sie loescht, wuerde einen Fehler wiederherstellen, keinen Zustand.
    op.execute("ALTER TABLE scan_history DROP COLUMN IF EXISTS jurisdiction")
