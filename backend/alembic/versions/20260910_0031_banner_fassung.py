"""Banner-Fassung im Einwilligungsprotokoll festhalten

Art. 7 Abs. 1 DSGVO verlangt den Nachweis, dass eine Einwilligung erteilt
wurde — und zwar wofuer. Das Protokoll speicherte in `revision_id` aber die ID
der Konfigurationszeile, nicht die Fassung des Banners. Die Zeile wird bei
jeder Aenderung ueberschrieben; die ID bleibt dieselbe. Damit liess sich zu
keiner Einwilligung sagen, welcher Banner dem Besucher tatsaechlich vorlag.

Die Fassungen selbst gibt es: der Trigger `trigger_banner_revision` legt bei
jeder inhaltlichen Aenderung einen Schnappschuss in `cookie_banner_revisions`
ab und zaehlt `cookie_banner_configs.revision` hoch. Diese Zahl fehlte nur im
Protokoll.

Neue Spalte statt Umdeutung der alten: die 1.151 bereits erfassten
Einwilligungen tragen in `revision_id` die Konfigurations-ID. Sie
nachtraeglich als Fassung zu lesen, waere ein erfundener Nachweis. Sie bleiben
deshalb NULL — das sagt ehrlich "nicht erfasst".
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0031_banner_fassung_im_protokoll"
down_revision: Union[str, None] = "0030_avv_fassung"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE cookie_consent_logs "
        "ADD COLUMN IF NOT EXISTS banner_revision INTEGER"
    )
    op.execute(
        "COMMENT ON COLUMN cookie_consent_logs.banner_revision IS "
        "'Fassung des Banners (cookie_banner_configs.revision) zum Zeitpunkt der "
        "Einwilligung. NULL = vor dem 10.09.2026 erfasst, Fassung nicht protokolliert.'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_consent_logs_revision "
        "ON cookie_consent_logs (site_id, banner_revision)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_consent_logs_revision")
    op.execute("ALTER TABLE cookie_consent_logs DROP COLUMN IF EXISTS banner_revision")
