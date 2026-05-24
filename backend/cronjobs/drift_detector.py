"""
AP3: Wöchentlicher Drift-Detection-Job für Klassifikations-Verteilung.
Vergleicht aktuelle Klassifikations-Verteilung gegen Baseline via KL-Divergenz.
Sendet Alert wenn KL-Divergenz > 0.1 (signifikante Verteilungsverschiebung).
"""
import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncpg
import os

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

def kl_divergence(p: Dict[str, float], q: Dict[str, float]) -> float:
    """
    Berechnet KL-Divergenz KL(P||Q) zwischen zwei Wahrscheinlichkeitsverteilungen.
    Epsilon-Smoothing um Division durch 0 zu vermeiden.
    """
    epsilon = 1e-10
    all_keys = set(p.keys()) | set(q.keys())
    result = 0.0
    for key in all_keys:
        p_val = p.get(key, 0.0) + epsilon
        q_val = q.get(key, 0.0) + epsilon
        result += p_val * math.log(p_val / q_val)
    return result

async def get_distribution(conn: asyncpg.Connection, days: int, offset_days: int = 0) -> Dict[str, float]:
    """Holt Klassifikations-Verteilung für ein Zeitfenster."""
    end = datetime.utcnow() - timedelta(days=offset_days)
    start = end - timedelta(days=days)
    rows = await conn.fetch(
        """
        SELECT risk_category, COUNT(*) AS cnt
        FROM ai_compliance_logs
        WHERE created_at BETWEEN $1 AND $2
        AND risk_category IS NOT NULL
        GROUP BY risk_category
        """,
        start, end
    )
    if not rows:
        return {}
    total = sum(r['cnt'] for r in rows)
    return {r['risk_category']: r['cnt'] / total for r in rows}

async def run_drift_detection() -> Optional[float]:
    """Hauptlogik: vergleicht aktuelle 7-Tage-Verteilung gegen 30-Tage-Baseline."""
    logger.info("🔍 Drift-Detection gestartet")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        current = await get_distribution(conn, days=7)
        baseline = await get_distribution(conn, days=30, offset_days=7)
        if not current or not baseline:
            logger.info("Nicht genug Daten für Drift-Detection")
            return None
        kl = kl_divergence(current, baseline)
        drift_detected = kl > 0.1
        await conn.execute(
            """
            INSERT INTO classification_drift_log
                (kl_divergence, distribution_current, distribution_baseline, drift_detected)
            VALUES ($1, $2::jsonb, $3::jsonb, $4)
            """,
            kl,
            str(current).replace("'", '"'),
            str(baseline).replace("'", '"'),
            drift_detected
        )
        if drift_detected:
            logger.warning(
                f"⚠️ DRIFT ERKANNT: KL-Divergenz = {kl:.4f} > 0.1 — "
                f"Klassifikations-Verteilung hat sich signifikant verändert!"
            )
        else:
            logger.info(f"✅ Kein Drift: KL-Divergenz = {kl:.4f}")
        return kl
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_drift_detection())
