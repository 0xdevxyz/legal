"""
ScanContext — zentrales Kontext-Objekt für jurisdiction-aware Scans (Stufe 1).

Wird von der Engine erzeugt und durch alle Checks gereicht, statt einzelne
Parameter (url, session, ...) zu verteilen. Stufe 1 unterstützt die Profile
"de" (Status quo) und "eu" (generisch, EN, GDPR) — siehe jurisdictions.py.
"""

from dataclasses import dataclass, field
from typing import Optional

import aiohttp

from compliance_engine.jurisdictions import (
    DEFAULT_JURISDICTION,
    normalize_jurisdiction,
    profile_language,
)


@dataclass
class ScanContext:
    """Kontext eines einzelnen Compliance-Scans.

    Attributes:
        url: Ziel-URL des Scans (normalisiert, mit Schema).
        jurisdiction: Rechtsraum-Profil, z.B. "de" | "eu" (Stufe 1).
        language: Ausgabesprache der Issue-Texte ("de" | "en").
        session: Geteilte aiohttp-Session des Scanners (optional).
    """

    url: str
    jurisdiction: str = DEFAULT_JURISDICTION
    language: str = ""  # leer = aus Jurisdiction-Profil ableiten
    session: Optional[aiohttp.ClientSession] = field(default=None, repr=False)

    def __post_init__(self):
        self.jurisdiction = normalize_jurisdiction(self.jurisdiction)
        if not self.language:
            self.language = profile_language(self.jurisdiction)
