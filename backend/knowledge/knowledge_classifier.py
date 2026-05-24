import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from knowledge import KnowledgeItem, RawContentItem

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

LAW_AREAS_MAP = {
    "dsgvo": "DSGVO", "gdpr": "DSGVO", "datenschutz": "DSGVO",
    "personenbezogen": "DSGVO", "art. 13": "DSGVO", "art. 14": "DSGVO",
    "cookie": "TTDSG", "ttdsg": "TTDSG", "einwilligung": "TTDSG",
    "consent": "TTDSG", "eprivacy": "TTDSG",
    "barrierefreiheit": "BFSG", "wcag": "BFSG", "bfsg": "BFSG",
    "accessibility": "BFSG", "aria": "BFSG",
    "nis2": "NIS2", "cybersicherheit": "NIS2", "meldepflicht": "NIS2",
    "impressum": "TMG", "tmg": "TMG", "anbieterkennzeichnung": "TMG",
    "uwg": "UWG", "wettbewerb": "UWG", "abmahnung": "UWG",
    "widerrufsrecht": "BGB", "agb": "BGB", "pangv": "PAngV",
    "ai act": "AI-Act", "ki-verordnung": "AI-Act",
}

CHECK_KEYWORD_MAP = {
    "datenschutz_check": ["dsgvo", "datenschutz", "privacy", "personenbezogen"],
    "cookie_check": ["cookie", "ttdsg", "consent", "einwilligung"],
    "impressum_check": ["impressum", "tmg", "anbieterkennzeichnung"],
    "barrierefreiheit_check": ["wcag", "bfsg", "barrierefreiheit", "aria", "accessibility"],
    "agb_check": ["agb", "widerrufsrecht", "§ 305", "allgemeine geschäftsbedingungen"],
    "pangv_check": ["pangv", "preisangabe", "preisinformation"],
    "uwg_check": ["uwg", "wettbewerb", "irreführung", "werbung"],
    "nis2_check": ["nis2", "cybersicherheit", "meldepflicht"],
}

CLASSIFICATION_PROMPT = """Du bist ein deutsches Compliance-Experten-System. Analysiere den folgenden Rechtstext und gib ein JSON-Objekt zurück.

Text:
{content}

Gib NUR ein JSON-Objekt zurück (kein Markdown, kein Text drumherum):
{{
  "relevance_score": 0.0-1.0,
  "category": "law-update|court-ruling|pattern|law",
  "law_areas": ["DSGVO", "BFSG", ...],
  "impact": "high|medium|low",
  "affected_checks": ["datenschutz_check", ...],
  "summary": "2-3 Sätze Zusammenfassung auf Deutsch",
  "action_items": ["Konkrete Handlungsempfehlung 1", "..."],
  "tags": ["Tag1", "Tag2", ...],
  "obsidian_links": ["[[DSGVO]]", "[[BFSG]]", ...]
}}

Bewertungsregeln:
- relevance_score >= 0.85: Direkte Gesetzesänderung oder Gerichtsurteil mit konkreten Pflichten
- relevance_score 0.70-0.84: Behördliche Stellungnahme oder relevante Branchennews
- relevance_score 0.60-0.69: Hintergrundinformation mit indirekter Relevanz
- relevance_score < 0.60: Nicht relevant für Compliance-Prüfung
"""


class KnowledgeClassifier:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            except ImportError:
                logger.warning("openai package not installed, using rule-based fallback")
        return self._client

    def _rule_based_classify(self, item: RawContentItem) -> Dict[str, Any]:
        text = f"{item.title} {item.content}".lower()

        law_areas = list({v for k, v in LAW_AREAS_MAP.items() if k in text})
        affected_checks = [
            check for check, keywords in CHECK_KEYWORD_MAP.items()
            if any(kw in text for kw in keywords)
        ]

        score = 0.3
        if law_areas:
            score += 0.2
        if affected_checks:
            score += 0.15
        urgent_words = ["urteil", "bußgeld", "pflicht", "ab sofort", "neue regel", "eugh", "bgh"]
        if any(w in text for w in urgent_words):
            score += 0.25
        score = min(score, 0.95)

        if score >= 0.85:
            impact = "high"
        elif score >= 0.70:
            impact = "medium"
        else:
            impact = "low"

        category = "law-update"
        if any(w in text for w in ["urteil", "entscheidung", "beschluss", "eugh", "bgh", "olg"]):
            category = "court-ruling"

        obsidian_links = [f"[[{area}]]" for area in law_areas]

        tags = law_areas + [item.source_type]
        if impact == "high":
            tags.append("high-impact")

        return {
            "relevance_score": round(score, 2),
            "category": category,
            "law_areas": law_areas,
            "impact": impact,
            "affected_checks": affected_checks,
            "summary": item.content[:200] + "..." if len(item.content) > 200 else item.content,
            "action_items": ["Compliance-Team informieren", "Betroffene Regeln prüfen"] if impact == "high" else [],
            "tags": list(set(tags)),
            "obsidian_links": obsidian_links,
        }

    async def classify(self, item: RawContentItem) -> Optional[KnowledgeItem]:
        client = self._get_client()

        classification: Dict[str, Any] = {}

        if client and OPENAI_API_KEY:
            try:
                prompt = CLASSIFICATION_PROMPT.format(
                    content=f"Titel: {item.title}\n\n{item.content[:1500]}"
                )
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=800,
                )
                raw = response.choices[0].message.content or ""
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = re.sub(r"```[a-z]*\n?", "", raw).strip("`").strip()
                classification = json.loads(raw)
            except Exception as e:
                logger.warning(f"OpenAI classification failed, using fallback: {e}")
                classification = self._rule_based_classify(item)
        else:
            classification = self._rule_based_classify(item)

        relevance_score = float(classification.get("relevance_score", 0.0))
        if relevance_score < 0.6:
            logger.debug(f"Skipping '{item.title}' (score={relevance_score})")
            return None

        slug = re.sub(r"[^a-z0-9]+", "-", item.title.lower())[:60].strip("-")

        return KnowledgeItem(
            title=item.title,
            content=item.content,
            summary=classification.get("summary", item.content[:200]),
            date=item.published_at.strftime("%Y-%m-%d"),
            category=classification.get("category", "law-update"),
            law_areas=classification.get("law_areas", []),
            relevance_score=relevance_score,
            impact=classification.get("impact", "low"),
            source_url=item.source_url,
            source_type=item.source_type,
            affected_checks=classification.get("affected_checks", []),
            tags=classification.get("tags", []),
            obsidian_links=classification.get("obsidian_links", []),
            action_items=classification.get("action_items", []),
            status="active",
            slug=slug,
            content_hash=item.content_hash,
        )

    async def classify_batch(self, items: List[RawContentItem]) -> List[KnowledgeItem]:
        results: List[KnowledgeItem] = []
        for item in items:
            classified = await self.classify(item)
            if classified:
                results.append(classified)
        logger.info(f"Classified {len(items)} items → {len(results)} passed threshold")
        return results
