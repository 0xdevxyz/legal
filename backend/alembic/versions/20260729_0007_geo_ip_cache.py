"""Geo-IP-Cache anlegen — Ländererkennung für die Geo-Restriction des Banners.

Revision ID: 0007_geo_ip_cache
Revises: 0006_rule_versioning_schema

Hintergrund: `GET /api/cookie-compliance/geo-check` liest und schreibt
`geo_ip_cache`. Die Tabelle fehlte, die Cache-Abfrage warf deshalb sofort, und
der umschliessende `except` lieferte pauschal `country_code: "EU"` zurück — die
eigentliche Auswertung des `CF-IPCountry`-Headers wurde nie erreicht.

Folge: Geo-Restriction ist im Dashboard einstellbar (GeoRestriction.tsx im
Tab „Erweitert"), lieferte aber für jeden Besucher „EU". Eine Einstellung wie
„Banner nur für Besucher aus DE" konnte nie greifen.

Gespeichert wird nur ein gekürzter SHA-256-Hash der IP (16 Zeichen, siehe
cookie_compliance_routes.py), nicht die IP selbst.

Rein additiv (`CREATE TABLE IF NOT EXISTS`).
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0007_geo_ip_cache'
down_revision: Union[str, None] = '0006_rule_versioning_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS geo_ip_cache (
            ip_hash       VARCHAR(64) PRIMARY KEY,
            country_code  VARCHAR(8) NOT NULL,
            cached_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    # Der Lesepfad filtert auf cached_at > NOW() - 24h; ausserdem braucht ein
    # Aufraeumlauf den Index, um alte Eintraege nicht per Seq-Scan zu finden.
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_ip_cache_cached_at ON geo_ip_cache (cached_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS geo_ip_cache")
