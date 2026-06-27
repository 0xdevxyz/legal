"""
Rule Versioning Service
Verwaltet Versionshistorie der Compliance-Regeln und triggert Updates
bei neuen Gesetzesänderungen.

Task 1 — Quality Process Implementation
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

CATEGORY_TO_RULE_KEYWORDS = {
    "cookie_compliance": ["cookie", "tracking", "consent", "einwilligung", "ttdsg", "eprivacy"],
    "datenschutz": ["dsgvo", "datenschutz", "privacy", "gdpr", "art. 13", "art. 14"],
    "impressum": ["impressum", "tmg", "anbieterkennzeichnung"],
    "barrierefreiheit": ["barrierefreiheit", "accessibility", "wcag", "bfsg", "aria"],
    "wettbewerbsrecht": ["uwg", "wettbewerb", "werbung", "abmahnung"],
    "verbraucherschutz": ["verbraucherschutz", "pangv", "preisangabe", "widerrufsrecht"],
    "ai_act": ["ai act", "ki-verordnung", "artificial intelligence"],
}


class RuleVersioningService:
    """
    Verwaltet die Versionierung von Compliance-Regeln.

    - Erhöht Rule-Version wenn ein Legal-Update eine Kategorie betrifft
    - Loggt alle Änderungen in rule_changelog
    - Liefert Snapshots für Scan-Protokollierung
    - Deprecates Regeln bei Ablauf
    """

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def bump_rule_version(
        self,
        rule_id: int,
        change_description: str,
        legal_update_id: Optional[int] = None,
        legal_basis_ref: Optional[str] = None,
        changed_by: str = "system",
    ) -> bool:
        """
        Erhöht die Version einer Regel um 1 und schreibt einen Changelog-Eintrag.

        Returns:
            True bei Erfolg
        """
        try:
            async with self.db_pool.acquire() as conn:
                new_version = await conn.fetchval(
                    """
                    UPDATE compliance_risk_matrix
                    SET rule_version = COALESCE(rule_version, 1) + 1,
                        valid_from   = CURRENT_DATE
                    WHERE id = $1
                    RETURNING rule_version
                    """,
                    rule_id,
                )

                if new_version is None:
                    logger.warning(f"Regel {rule_id} nicht gefunden — kein Version-Bump")
                    return False

                await conn.execute(
                    """
                    INSERT INTO rule_changelog
                      (rule_id, rule_version, change_type, change_description,
                       legal_basis_ref, triggered_by_legal_update_id, changed_by)
                    VALUES ($1, $2, 'updated', $3, $4, $5, $6)
                    """,
                    rule_id,
                    new_version,
                    change_description,
                    legal_basis_ref,
                    legal_update_id,
                    changed_by,
                )

                logger.info(
                    f"Rule {rule_id} bumped to version {new_version} "
                    f"(triggered by legal_update #{legal_update_id})"
                )
                return True

        except Exception as e:
            logger.error(f"bump_rule_version failed for rule {rule_id}: {e}", exc_info=True)
            return False

    async def deprecate_rule(
        self,
        rule_id: int,
        reason: str,
        legal_update_id: Optional[int] = None,
    ) -> bool:
        """
        Markiert eine Regel als deprecated (valid_until = today, is_active = false).

        Returns:
            True bei Erfolg
        """
        try:
            async with self.db_pool.acquire() as conn:
                updated = await conn.fetchval(
                    """
                    UPDATE compliance_risk_matrix
                    SET is_active   = FALSE,
                        valid_until = CURRENT_DATE
                    WHERE id = $1
                    RETURNING id
                    """,
                    rule_id,
                )

                if updated is None:
                    return False

                current_version = await conn.fetchval(
                    "SELECT COALESCE(rule_version, 1) FROM compliance_risk_matrix WHERE id = $1",
                    rule_id,
                )

                await conn.execute(
                    """
                    INSERT INTO rule_changelog
                      (rule_id, rule_version, change_type, change_description,
                       triggered_by_legal_update_id)
                    VALUES ($1, $2, 'deprecated', $3, $4)
                    """,
                    rule_id,
                    current_version,
                    reason,
                    legal_update_id,
                )

                logger.info(f"Rule {rule_id} deprecated: {reason}")
                return True

        except Exception as e:
            logger.error(f"deprecate_rule failed for rule {rule_id}: {e}", exc_info=True)
            return False

    async def get_rule_history(self, rule_id: int) -> List[Dict]:
        """
        Gibt die vollständige Versionshistorie einer Regel zurück.
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        rc.id,
                        rc.rule_version,
                        rc.change_type,
                        rc.change_description,
                        rc.legal_basis_ref,
                        rc.triggered_by_legal_update_id,
                        rc.changed_at,
                        rc.changed_by,
                        lu.title AS legal_update_title
                    FROM rule_changelog rc
                    LEFT JOIN legal_updates lu ON rc.triggered_by_legal_update_id = lu.id
                    WHERE rc.rule_id = $1
                    ORDER BY rc.changed_at DESC
                    """,
                    rule_id,
                )
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"get_rule_history failed for rule {rule_id}: {e}", exc_info=True)
            return []

    async def get_active_ruleset_snapshot(self) -> Dict:
        """
        Erzeugt einen Snapshot aller aktiven Regeln für die Scan-Protokollierung.

        Returns:
            Dict mit version_hash, generated_at, rules[]
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        id,
                        issue_category,
                        severity,
                        market,
                        legal_basis,
                        COALESCE(rule_version, 1) AS rule_version,
                        valid_from,
                        effective_date
                    FROM compliance_risk_matrix
                    WHERE (is_active IS NULL OR is_active = TRUE)
                      AND effective_date <= CURRENT_DATE
                    ORDER BY issue_category
                    """
                )

                rules = [dict(r) for r in rows]

                # Simple version fingerprint: max rule_version sum
                version_sum = sum(r["rule_version"] for r in rules)

                return {
                    "generated_at": datetime.utcnow().isoformat(),
                    "ruleset_version": version_sum,
                    "rule_count": len(rules),
                    "rules": rules,
                }
        except Exception as e:
            logger.error(f"get_active_ruleset_snapshot failed: {e}", exc_info=True)
            return {"generated_at": datetime.utcnow().isoformat(), "ruleset_version": 0, "rules": []}

    async def find_rules_affected_by_legal_update(
        self, legal_update: Dict
    ) -> List[Dict]:
        """
        Identifiziert Compliance-Regeln, die von einem Legal-Update betroffen sind.

        Matching-Logik: Keywords aus Titel + update_type + affected_areas
        """
        try:
            async with self.db_pool.acquire() as conn:
                all_rules = await conn.fetch(
                    """
                    SELECT id, issue_category, legal_basis, description
                    FROM compliance_risk_matrix
                    WHERE (is_active IS NULL OR is_active = TRUE)
                    """
                )

            title_desc = (
                f"{legal_update.get('title', '')} "
                f"{legal_update.get('description', '')} "
                f"{legal_update.get('update_type', '')}"
            ).lower()

            affected = []
            for rule in all_rules:
                category = (rule["issue_category"] or "").lower()
                keywords = CATEGORY_TO_RULE_KEYWORDS.get(category, [])

                if any(kw in title_desc for kw in keywords):
                    affected.append(dict(rule))
                    continue

                # Also match if rule's legal_basis is referenced
                legal_basis = (rule["legal_basis"] or "").lower()
                if any(kw in legal_basis for kw in title_desc.split()):
                    affected.append(dict(rule))

            return affected

        except Exception as e:
            logger.error(f"find_rules_affected_by_legal_update failed: {e}", exc_info=True)
            return []

    async def process_knowledge_update(
        self,
        knowledge_item_title: str,
        knowledge_item_slug: str,
        law_areas: List[str],
        impact: str,
        affected_checks: List[str],
    ) -> Dict[str, Any]:
        """
        Verarbeitet ein neues Knowledge-Update und löst bei High-Impact ein Rule-Review aus.
        Wird vom knowledge_updater.py Cronjob aufgerufen.
        """
        result = {"processed": True, "rules_flagged": 0, "rule_review_created": False}

        if impact != "high":
            return result

        try:
            mock_update = {
                "title": knowledge_item_title,
                "description": f"Knowledge Vault Update: {', '.join(law_areas)}",
                "affected_areas": law_areas,
            }

            affected_rules = await self.find_rules_affected_by_legal_update(mock_update)
            result["rules_flagged"] = len(affected_rules)

            if affected_rules and self.db_pool:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO knowledge_rule_review_queue
                        (check_name, knowledge_file, title, law_areas, impact, created_at)
                        VALUES ($1, $2, $3, $4, $5, NOW())
                        ON CONFLICT (check_name, knowledge_file) DO NOTHING
                        """,
                        ",".join(affected_checks),
                        f"{knowledge_item_slug}.md",
                        knowledge_item_title,
                        law_areas,
                        impact,
                    )
                    result["rule_review_created"] = True
                    logger.info(
                        f"Rule-Review-Queue: {len(affected_rules)} Regeln für '{knowledge_item_title}' markiert"
                    )

        except Exception as e:
            logger.warning(f"process_knowledge_update non-critical error: {e}")

        return result
