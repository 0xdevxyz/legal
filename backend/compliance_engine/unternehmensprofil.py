"""
Unternehmensprofil fuer den Scan laden.

Das Profil (company_profiles.answers, siehe pflichten_katalog.py) pflegt der
Kunde im Pflichten-Report. Der Scanner braucht daraus Beschaeftigte, Umsatz,
Verbraucherangebot und Online-Vertragsschluss fuer die BFSG-Einordnung
(bfsg_einordnung.py). Ein Lesefehler darf den Scan nie anhalten: dann laeuft
er ohne Profil, und die Einordnung bleibt offen.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def lade(db_pool, user_id: Any) -> Optional[Dict[str, Any]]:
    """Antworten des Profils oder None (kein Pool, kein Nutzer, kein Profil)."""
    if db_pool is None or user_id in (None, ""):
        return None
    try:
        nutzer = int(user_id)
    except (TypeError, ValueError):
        return None
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT answers FROM company_profiles WHERE user_id = $1", nutzer
            )
    except Exception as e:
        logger.warning("Unternehmensprofil nicht ladbar (user %s): %s", nutzer, e)
        return None
    if not row or not row["answers"]:
        return None
    answers = row["answers"]
    if isinstance(answers, str):
        try:
            answers = json.loads(answers)
        except ValueError:
            return None
    return answers if isinstance(answers, dict) else None
