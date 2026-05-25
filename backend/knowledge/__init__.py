from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class RawContentItem:
    title: str
    content: str
    source_url: str
    source_type: str
    published_at: datetime
    content_hash: str


@dataclass
class KnowledgeItem:
    title: str
    content: str
    summary: str
    date: str
    category: str
    law_areas: List[str]
    relevance_score: float
    impact: str
    source_url: str
    source_type: str
    affected_checks: List[str]
    tags: List[str]
    obsidian_links: List[str]
    action_items: List[str]
    status: str = "active"
    slug: str = ""
    content_hash: str = ""


@dataclass
class LawDefinition:
    name: str
    slug: str
    full_name: str
    description: str
    relevant_articles: List[dict] = field(default_factory=list)
    affected_checks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
