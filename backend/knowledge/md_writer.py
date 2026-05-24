import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

from knowledge import KnowledgeItem, LawDefinition

logger = logging.getLogger(__name__)

VAULT_ROOT = Path(os.getenv("KNOWLEDGE_VAULT_PATH", "/home/clawd/saas/legal/knowledge"))

UPDATES_DIR = VAULT_ROOT / "updates"
LAWS_DIR = VAULT_ROOT / "laws"
PATTERNS_DIR = VAULT_ROOT / "patterns"
INDEX_DIR = VAULT_ROOT / "index"


def _build_frontmatter(item: KnowledgeItem) -> str:
    fm = {
        "title": item.title,
        "date": item.date,
        "category": item.category,
        "law_areas": item.law_areas,
        "relevance_score": item.relevance_score,
        "impact": item.impact,
        "source_url": item.source_url,
        "source_type": item.source_type,
        "affected_checks": item.affected_checks,
        "tags": item.tags,
        "obsidian_links": item.obsidian_links,
        "status": item.status,
        "embedding_hash": "",
        "last_embedded": "",
    }
    return "---\n" + yaml.dump(fm, allow_unicode=True, default_flow_style=False) + "---\n"


def _build_update_body(item: KnowledgeItem) -> str:
    parts = [f"# {item.title}\n"]

    parts.append("## Zusammenfassung\n")
    parts.append(item.summary + "\n")

    if item.action_items:
        parts.append("\n## Handlungsempfehlungen für complyo\n")
        for ai in item.action_items:
            parts.append(f"- {ai}\n")

    if item.affected_checks:
        parts.append("\n## Betroffene complyo-Checks\n")
        for check in item.affected_checks:
            parts.append(f"- [[{check}]]\n")

    if item.obsidian_links:
        parts.append("\n## Verwandte Gesetze\n")
        parts.append(" | ".join(item.obsidian_links) + "\n")

    parts.append("\n## Vollständiger Inhalt\n")
    parts.append(item.content + "\n")

    if item.source_url:
        parts.append(f"\n## Quelle\n- [{item.source_url}]({item.source_url})\n")

    parts.append(f"\n---\n*Automatisch generiert am {datetime.now().strftime('%Y-%m-%d %H:%M')} durch complyo Knowledge Engine*\n")

    return "".join(parts)


class MDWriter:
    def __init__(self, vault_root: Optional[Path] = None):
        self.vault_root = vault_root or VAULT_ROOT
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [UPDATES_DIR, LAWS_DIR, PATTERNS_DIR, INDEX_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def write_update(self, item: KnowledgeItem) -> str:
        filename = f"{item.date}-{item.slug}.md"
        filepath = UPDATES_DIR / filename

        if filepath.exists():
            logger.debug(f"Update file already exists: {filename}")
            return str(filepath)

        content = _build_frontmatter(item) + "\n" + _build_update_body(item)
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Written update: {filename}")
        return str(filepath)

    def write_law_page(self, law: LawDefinition) -> str:
        filepath = LAWS_DIR / f"{law.slug}.md"

        if filepath.exists():
            existing = filepath.read_text(encoding="utf-8")
            if f"## Update-Historie" not in existing:
                existing += "\n## Update-Historie\n\n| Datum | Update | Link |\n|-------|--------|------|\n"
            filepath.write_text(existing, encoding="utf-8")
            return str(filepath)

        fm = {
            "title": law.full_name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": "law",
            "law_areas": [law.name],
            "relevance_score": 1.0,
            "impact": "high",
            "source_url": "",
            "source_type": "internal",
            "affected_checks": law.affected_checks,
            "tags": [law.name] + law.tags,
            "obsidian_links": [],
            "status": "active",
            "embedding_hash": "",
            "last_embedded": "",
        }

        frontmatter = "---\n" + yaml.dump(fm, allow_unicode=True, default_flow_style=False) + "---\n"

        body_parts = [
            f"# {law.full_name}\n\n",
            f"{law.description}\n\n",
            "## Überblick\n\n",
            "[Wird automatisch durch den Knowledge Updater ergänzt]\n\n",
        ]

        if law.relevant_articles:
            body_parts.append("## Für complyo relevante Artikel\n\n")
            body_parts.append("| Artikel | Titel | Relevanz |\n|---------|-------|----------|\n")
            for art in law.relevant_articles:
                body_parts.append(f"| {art.get('nr', '')} | {art.get('title', '')} | {art.get('relevance', '')} |\n")
            body_parts.append("\n")

        if law.affected_checks:
            body_parts.append("## complyo-Checks die dieses Gesetz prüfen\n\n")
            for check in law.affected_checks:
                body_parts.append(f"- [[{check}]]\n")
            body_parts.append("\n")

        body_parts.append("## Update-Historie\n\n| Datum | Update | Link |\n|-------|--------|------|\n\n")
        body_parts.append(f"---\n*Erstellt am {datetime.now().strftime('%Y-%m-%d')} durch complyo Knowledge Engine*\n")

        content = frontmatter + "\n" + "".join(body_parts)
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Written law page: {law.slug}.md")
        return str(filepath)

    def update_index(self, category: str = "updates") -> None:
        if category == "updates":
            self._rebuild_updates_index()
        elif category == "laws":
            self._rebuild_laws_index()
        elif category == "all":
            self._rebuild_updates_index()
            self._rebuild_laws_index()
            self._rebuild_main_index()

    def _rebuild_updates_index(self):
        filepath = INDEX_DIR / "updates-index.md"
        content = (
            "---\n"
            "title: Updates Index\n"
            "category: index\n"
            "tags: [index, updates]\n"
            "---\n\n"
            "# Compliance Updates Index\n\n"
            "> Automatisch generiert. Zeigt alle Compliance-Updates nach Relevanz sortiert.\n\n"
            "## High-Impact Updates\n\n"
            "```dataview\n"
            "TABLE date, relevance_score, law_areas, source_type\n"
            'FROM "updates"\n'
            'WHERE impact = "high"\n'
            "SORT date DESC\n"
            "LIMIT 20\n"
            "```\n\n"
            "## Alle Updates\n\n"
            "```dataview\n"
            "TABLE date, impact, relevance_score, law_areas\n"
            'FROM "updates"\n'
            "SORT date DESC\n"
            "LIMIT 50\n"
            "```\n\n"
            "## Nach Rechtsgebiet\n\n"
            "```dataview\n"
            "TABLE date, title, impact\n"
            'FROM "updates"\n'
            "FLATTEN law_areas as area\n"
            "SORT area ASC, date DESC\n"
            "```\n"
        )
        filepath.write_text(content, encoding="utf-8")
        logger.info("Rebuilt updates-index.md")

    def _rebuild_laws_index(self):
        filepath = INDEX_DIR / "laws-index.md"
        content = (
            "---\n"
            "title: Gesetze Index\n"
            "category: index\n"
            "tags: [index, laws]\n"
            "---\n\n"
            "# Rechtsgebiete Index\n\n"
            "```dataview\n"
            "TABLE law_areas, affected_checks\n"
            'FROM "laws"\n'
            "SORT title ASC\n"
            "```\n\n"
            "## Schnellzugriff\n\n"
            "- [[DSGVO]] – Datenschutz-Grundverordnung\n"
            "- [[BFSG]] – Barrierefreiheitsstärkungsgesetz\n"
            "- [[NIS2]] – Netz- und Informationssicherheitsrichtlinie\n"
            "- [[TTDSG]] – Telekommunikations-Telemedien-Datenschutz-Gesetz\n"
            "- [[UWG]] – Gesetz gegen unlauteren Wettbewerb\n"
            "- [[AGB-Recht]] – §§ 305 ff. BGB\n"
            "- [[Impressumspflicht]] – § 5 TMG / § 18 MStV\n"
        )
        filepath.write_text(content, encoding="utf-8")
        logger.info("Rebuilt laws-index.md")

    def _rebuild_main_index(self):
        filepath = INDEX_DIR / "README.md"
        content = (
            "---\n"
            "title: complyo Knowledge Vault\n"
            "category: index\n"
            "tags: [index, root]\n"
            "---\n\n"
            "# complyo Knowledge Vault\n\n"
            "> Selbstlernendes Compliance-Wissenssystem – automatisch aktualisiert täglich um 07:00 Uhr\n\n"
            "## Bereiche\n\n"
            "| Bereich | Beschreibung | Link |\n"
            "|---------|-------------|------|\n"
            "| Updates | Täglich neue Rechtsänderungen | [[updates-index]] |\n"
            "| Gesetze | Stammwissen je Gesetz | [[laws-index]] |\n"
            "| Muster | Gelernte Compliance-Fehler | `patterns/` |\n\n"
            "## Vault-Statistiken\n\n"
            "```dataview\n"
            "TABLE length(rows) as Anzahl\n"
            'FROM "updates" OR "laws" OR "patterns"\n'
            "GROUP BY category\n"
            "```\n\n"
            "## Letzte High-Impact Updates\n\n"
            "```dataview\n"
            "TABLE date, title, law_areas\n"
            'FROM "updates"\n'
            'WHERE impact = "high"\n'
            "SORT date DESC\n"
            "LIMIT 5\n"
            "```\n"
        )
        filepath.write_text(content, encoding="utf-8")
        logger.info("Rebuilt main README.md index")

    def write_batch(self, items: List[KnowledgeItem]) -> List[str]:
        paths = []
        for item in items:
            if item.category in ("law-update", "court-ruling"):
                path = self.write_update(item)
            else:
                path = self.write_update(item)
            paths.append(path)

        if items:
            self.update_index("all")

        return paths
