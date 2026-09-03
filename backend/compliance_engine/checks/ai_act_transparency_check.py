"""
AI-Act-Transparenz-Check (Art. 50 KI-VO / VO (EU) 2024/1689)

Erkennt KI-Systeme mit direkter Nutzer-Interaktion auf der Website
(Chatbots / virtuelle Assistenten) und prüft, ob ein Transparenz-Hinweis
(„Sie interagieren mit einer KI") erkennbar ist.

Haftungs-Design (Pflicht aus Phase-7-Plan): JEDE Aussage trägt
confidence + evidence (welches Skript/Element die Erkennung ausgelöst hat).
Der Check behauptet nie „Sie sind betroffen/nicht betroffen", sondern
meldet nur belegte Funde als Prüf-Hinweis.
"""
import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Signatur-Katalog: Domain-/Objekt-Muster → (Anbieter, ist_ki_nativ)
# ist_ki_nativ=True: Produkt ist primär ein KI-Bot (Transparenzpflicht sehr
# wahrscheinlich). False: Chat-Plattform, KI-Modus möglich (Pflicht prüfen).
CHATBOT_SIGNATURES = [
    # (regex auf src/inline, Anbieter, ki_nativ, confidence)
    (r"chatbase\.co", "Chatbase", True, 0.95),
    (r"botpress\.(cloud|com)", "Botpress", True, 0.95),
    (r"voiceflow\.com", "Voiceflow", True, 0.95),
    (r"chatbot\.com", "ChatBot.com", True, 0.9),
    (r"landbot\.io", "Landbot", True, 0.9),
    (r"ada\.support|adasupport", "Ada", True, 0.9),
    (r"kommunicate\.io", "Kommunicate", True, 0.9),
    (r"dante-ai\.com", "Dante AI", True, 0.95),
    (r"writesonic\.com/botsonic|botsonic", "Botsonic", True, 0.95),
    (r"widget\.intercom\.io|intercomcdn|window\.intercomsettings", "Intercom (Fin AI möglich)", False, 0.85),
    (r"js\.driftt\.com|drift\.com/embed", "Drift", False, 0.85),
    (r"client\.crisp\.chat|\$crisp", "Crisp", False, 0.85),
    (r"code\.tidio\.co|tidiochatapi", "Tidio (Lyro AI möglich)", False, 0.85),
    (r"embed\.tawk\.to|tawk_api", "Tawk.to", False, 0.8),
    (r"userlike\.com/(widget|rtm)", "Userlike", False, 0.85),
    (r"zdassets\.com|zendesk.*(widget|chat)|zopim", "Zendesk Chat", False, 0.8),
    (r"js\.hs-scripts\.com|hubspot.*conversations", "HubSpot Chat (Breeze AI möglich)", False, 0.8),
    (r"livechatinc\.com|cdn\.livechat", "LiveChat", False, 0.8),
    (r"freshchat|freshworks.*chat", "Freshchat (Freddy AI möglich)", False, 0.8),
]

# Hinweise darauf, dass die Seite KI-Interaktion bereits offenlegt
DISCLOSURE_PATTERNS = [
    r"ki[\s-]?(assistent|chatbot|chat)", r"ai[\s-]?(assistant|chatbot|chat)",
    r"künstliche[rn]?\s+intelligenz", r"artificial\s+intelligence",
    r"virtueller\s+assistent", r"sie\s+(chatten|sprechen)\s+mit\s+einer?\s+(ki|maschine|bot)",
    r"powered\s+by\s+(ai|ki|gpt|openai)", r"chatbot",
]


def _collect_sources(soup: BeautifulSoup, request_urls: Optional[List[str]]) -> str:
    parts: List[str] = []
    for tag in soup.find_all(["script", "iframe"]):
        src = tag.get("src")
        if src:
            parts.append(src)
        elif tag.name == "script" and tag.string:
            parts.append(tag.string[:2000])
    for link in soup.find_all("link", href=True):
        parts.append(link["href"])
    if request_urls:
        parts.extend(request_urls)
    return "\n".join(parts).lower()


async def check_ai_act_transparency(
    url: str,
    soup: BeautifulSoup,
    request_urls: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Findet KI-Chat-Systeme und fehlende Art.-50-Transparenzhinweise."""
    issues: List[Dict[str, Any]] = []
    try:
        haystack = _collect_sources(soup, request_urls)
        page_text = soup.get_text(" ", strip=True).lower()[:20000]

        detected = []
        for pattern, provider, ki_nativ, confidence in CHATBOT_SIGNATURES:
            m = re.search(pattern, haystack)
            if m:
                # Evidenz: die konkrete Fundstelle (gekürzt), nie nur die Behauptung
                start = max(0, m.start() - 40)
                evidence = haystack[start:m.end() + 40].strip().replace("\n", " ")[:160]
                detected.append((provider, ki_nativ, confidence, evidence))

        if not detected:
            return issues

        has_disclosure = any(re.search(p, page_text) for p in DISCLOSURE_PATTERNS)

        for provider, ki_nativ, confidence, evidence in detected:
            if ki_nativ and not has_disclosure:
                severity = "warning"
                title = f"KI-Chatbot erkannt ({provider}) — Transparenzhinweis nach Art. 50 KI-VO fehlt offenbar"
                description = (
                    f"Auf der Seite wurde ein KI-Chat-System des Anbieters {provider} "
                    f"erkannt, aber kein für Nutzer erkennbarer Hinweis, dass sie mit "
                    f"einer KI interagieren. Art. 50 Abs. 1 KI-VO verlangt diese "
                    f"Information, sofern die KI-Interaktion nicht offensichtlich ist. "
                    f"Seit 02.08.2026 ist die Pflicht bußgeldbewehrt."
                )
                risk_euro = 5000
            elif ki_nativ:
                severity = "info"
                title = f"KI-Chatbot erkannt ({provider}) — Transparenzhinweis vorhanden"
                description = (
                    f"KI-Chat-System ({provider}) erkannt; die Seite enthält einen "
                    f"Hinweis auf KI-Interaktion. Empfehlung: Hinweis direkt im "
                    f"Chat-Fenster platzieren, nicht nur im Fließtext."
                )
                risk_euro = 0
            else:
                severity = "info"
                title = f"Chat-System erkannt ({provider}) — KI-Modus prüfen (Art. 50 KI-VO)"
                description = (
                    f"Chat-Plattform {provider} erkannt. Falls dort ein KI-Bot "
                    f"(z. B. AI-Antworten/Copilot-Modus) aktiv ist, greift die "
                    f"Transparenzpflicht nach Art. 50 Abs. 1 KI-VO. Bitte prüfen, "
                    f"ob der KI-Modus aktiv ist und ein Hinweis angezeigt wird."
                )
                risk_euro = 0

            issues.append({
                "category": "ai_act_transparency",
                "severity": severity,
                "title": title,
                "description": description,
                "risk_euro": risk_euro,
                "recommendation": (
                    "Im Chat-Widget einen deutlich sichtbaren Hinweis ergänzen, dass "
                    "Nutzer mit einer KI interagieren (z. B. Begrüßungsnachricht "
                    "„Ich bin der KI-Assistent von …\"). Zuständig ist der Betreiber "
                    "(Deployer) des Systems."
                ),
                "legal_basis": "Art. 50 Abs. 1 KI-VO (VO (EU) 2024/1689)",
                "auto_fixable": False,
                "is_missing": False,
                "metadata": {
                    "check": "ai_act_transparency",
                    "provider": provider,
                    "confidence": confidence,
                    "evidence": evidence,
                    "disclosure_found": has_disclosure,
                },
            })

        logger.info(
            f"AI-Act-Check: {len(detected)} Chat-System(e) erkannt auf {url}, "
            f"Disclosure: {has_disclosure}"
        )
    except Exception as e:
        logger.warning(f"AI-Act-Transparenz-Check fehlgeschlagen (non-fatal): {e}")
    return issues
