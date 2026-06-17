"""
Complyo AI Review Engine
Prüft und verfeinert jeden Ausgabeaspekt des Scans mit KI:
- Issue-Titel, Beschreibung, Empfehlung
- Severity-Kalibrierung
- Individuelle ai_solution für ALLE Issues (priorisiert)
- Positive Checks auf Basis echter Scan-Daten
"""

import asyncio
import aiohttp
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# v4.0: Umstellung auf Claude — moonshotai/kimi-k2-thinking lieferte über OpenRouter
# leeren Inhalt (content=None) → KI-Review/Lösungen liefen ins Leere. Claude Haiku 4.5
# ist schnell, günstig und auf dem vorhandenen OpenRouter-Key verfügbar. Per ENV override.
REVIEW_MODEL = os.getenv("COMPLYO_REVIEW_MODEL", "anthropic/claude-haiku-4.5")
SOLUTION_MODEL = os.getenv("COMPLYO_SOLUTION_MODEL", "anthropic/claude-haiku-4.5")
# Verifikationsmodell (v4.0): schnell/günstig, empfohlen Claude Haiku 4.5 via OpenRouter.
# Override per ENV; Fallback auf das bereits konfigurierte REVIEW_MODEL, falls das
# Anthropic-Modell über den OpenRouter-Key nicht verfügbar ist.
VERIFY_MODEL = os.getenv("COMPLYO_VERIFY_MODEL", "anthropic/claude-haiku-4.5")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://complyo.tech",
    "X-Title": "Complyo AI Review Engine",
}


async def _call_ai(prompt: str, model: str, max_tokens: int = 600, temperature: float = 0.2) -> Optional[str]:
    if not OPENROUTER_API_KEY:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_URL,
                headers=_HEADERS,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=aiohttp.ClientTimeout(total=18),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                logger.warning(f"AI call {model} status {resp.status}")
                return None
    except Exception as e:
        logger.warning(f"AI call failed ({model}): {e}")
        return None


async def _call_ai_json(prompt: str, model: str, max_tokens: int = 800) -> Optional[Dict]:
    raw = await _call_ai(prompt, model, max_tokens=max_tokens, temperature=0.1)
    if not raw:
        return None
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except Exception:
        # Try to extract JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass
    return None


# ─────────────────────────────────────────────
# 0. Säulen-Verifikation (v4.0) — nur bei UNVERIFIED
# ─────────────────────────────────────────────

# Was muss pro Säule am realen Seiteninhalt nachweisbar sein?
_PILLAR_VERIFY_CRITERIA = {
    "legal": (
        "ein gültiges Impressum nach DDG §5 (vollständiger Name/Firma, ladungsfähige "
        "Anschrift mit PLZ und Ort, schnelle Kontaktmöglichkeit wie E-Mail)"
    ),
    "gdpr": (
        "eine gültige Datenschutzerklärung nach DSGVO (Verantwortlicher, Zwecke und "
        "Rechtsgrundlagen der Verarbeitung, Betroffenenrechte, Speicherdauer)"
    ),
    "cookies": (
        "ein funktionsfähiges Cookie-Consent-Banner mit echter Ablehnen-Option "
        "(Opt-In, kein reines 'OK'), sofern nicht-notwendige Cookies/Tracking genutzt werden"
    ),
    "accessibility": (
        "grundlegende Barrierefreiheit (Barrierefreiheitserklärung nach BFSG bzw. "
        "ein Barrierefreiheits-/Accessibility-Widget oder klare WCAG-Konformität)"
    ),
}


async def ai_verify_pillar(
    pillar: str,
    page_text: str,
    evidence: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Verifiziert per KI, ob eine NICHT eindeutig prüfbare Säule am realen
    Seiteninhalt erfüllt ist. Wird nur bei Status UNVERIFIED / niedriger
    Confidence aufgerufen (Kostenkontrolle).

    Returns striktes JSON-Dict oder None (kein Key / Fehler / Modell nicht verfügbar):
        {"compliant": bool, "missing": [str, ...], "reason": str, "confidence": float}

    Bei None bleibt die Säule UNVERIFIED — der Scan funktioniert ohne KI weiter.
    """
    if not OPENROUTER_API_KEY:
        return None
    criteria = _PILLAR_VERIFY_CRITERIA.get(pillar)
    if not criteria:
        return None

    text = (page_text or "").strip()[:6000]
    if not text:
        return None

    prompt = f"""Du bist ein deutscher Compliance-Experte. Prüfe ausschließlich anhand des unten stehenden Seiteninhalts, ob folgende Anforderung erfüllt ist:

ANFORDERUNG ({pillar}): {criteria}

Beurteile nur, was im Text tatsächlich belegbar ist. Wenn der relevante Inhalt nicht enthalten ist, gilt die Anforderung als NICHT erfüllt.

Seiteninhalt:
\"\"\"
{text}
\"\"\"

Antworte AUSSCHLIESSLICH mit JSON in genau diesem Schema:
{{"compliant": true|false, "missing": ["..."], "reason": "kurze Begründung auf Deutsch", "confidence": 0.0-1.0}}"""

    result = await _call_ai_json(prompt, VERIFY_MODEL, max_tokens=500)
    if not result or "compliant" not in result:
        # Fallback auf das bereits konfigurierte Review-Modell, falls das
        # Verifikationsmodell (z.B. Claude via OpenRouter) nicht erreichbar ist.
        if VERIFY_MODEL != REVIEW_MODEL:
            result = await _call_ai_json(prompt, REVIEW_MODEL, max_tokens=500)
    if not result or "compliant" not in result:
        return None
    return {
        "compliant": bool(result.get("compliant")),
        "missing": result.get("missing") or [],
        "reason": str(result.get("reason") or ""),
        "confidence": float(result.get("confidence") or 0.0),
    }


# ─────────────────────────────────────────────
# 1. Issue-Level Review
# ─────────────────────────────────────────────

async def review_issue(
    issue: Dict[str, Any],
    scan_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Prüft einen einzelnen Issue auf Korrektheit und Individualität.
    Gibt ein korrigiertes Issue-Dict zurück (nur geänderte Felder).
    """
    url = scan_context.get("url", "")
    cms = scan_context.get("cms", "Unbekannt")
    tracking = ", ".join(scan_context.get("tracking_services", [])) or "keine"

    prompt = f"""Du bist ein deutscher Compliance-Experte und prüfst automatisch generierte Scan-Ergebnisse.

WEBSITE: {url}
CMS: {cms}
Erkannte Tracking-Dienste: {tracking}

GESCANNTES ISSUE:
- Titel: {issue.get('title', '')}
- Kategorie: {issue.get('category', '')}
- Severity: {issue.get('severity', '')}
- Beschreibung: {issue.get('description', '')}
- Empfehlung: {issue.get('recommendation', '')}
- Risiko (€): {issue.get('risk_euro_max', 0)}
- Rechtsgrundlage: {issue.get('legal_basis', '')}

AUFGABE:
Prüfe jeden Aspekt dieses Issues auf:
1. Ist der Titel präzise und spezifisch für diese Website? (kein generisches "Problem gefunden")
2. Ist die Beschreibung verständlich und konkret?
3. Ist die Severity korrekt kalibriert? (critical = Bußgeld/Abmahnung direkt möglich, warning = potenziell, info = Empfehlung)
4. Ist das Risiko (€) realistisch für das konkrete Problem?
5. Ist die Empfehlung umsetzbar und spezifisch für {url}?

Antworte NUR mit diesem JSON (ändere nur Felder die wirklich falsch/zu generisch sind, behalte gut formulierte Felder unverändert):
{{
  "title": "...",
  "description": "...",
  "recommendation": "...",
  "severity": "critical|warning|info",
  "risk_euro_max": <Zahl>,
  "legal_basis": "...",
  "review_note": "Kurze interne Notiz was du geändert hast (max 1 Satz)"
}}"""

    reviewed = await _call_ai_json(prompt, REVIEW_MODEL, max_tokens=700)
    if not reviewed:
        return {}

    # Only return fields that actually differ from original
    changes = {}
    for field in ["title", "description", "recommendation", "severity", "risk_euro_max", "legal_basis"]:
        if field in reviewed:
            original = issue.get(field)
            new_val = reviewed[field]
            if new_val and new_val != original:
                changes[field] = new_val

    if reviewed.get("review_note"):
        changes["_review_note"] = reviewed["review_note"]

    return changes


# ─────────────────────────────────────────────
# 2. Individual AI Solution for every issue
# ─────────────────────────────────────────────

async def generate_individual_solution(
    issue: Dict[str, Any],
    scan_context: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Generiert eine individuelle, website-spezifische Lösung für ein Issue.
    Gibt strukturiertes Dict zurück: {ai_solution, steps, code_snippet}
    """
    url = scan_context.get("url", "")
    cms = scan_context.get("cms", "Unbekannt")
    tracking = ", ".join(scan_context.get("tracking_services", [])) or "keine"
    cookies = ", ".join(scan_context.get("cookies", [])) or "keine"
    all_issue_titles = scan_context.get("all_issue_titles", [])
    other_issues = "\n".join(f"  - {t}" for t in all_issue_titles[:8]) or "  - (keine weiteren)"
    category = issue.get('category', '')
    title = issue.get('title', '')

    prompt = f"""Du bist ein Experte für Website-Compliance (deutsches Recht, DSGVO, WCAG 2.1).

WEBSITE: {url}
CMS / Technologie: {cms}
Erkannte Tracking-Dienste: {tracking}
Erkannte Cookies: {cookies}

PROBLEM:
- Titel: {title}
- Kategorie: {category}
- Beschreibung: {issue.get('description', '')}
- Rechtsgrundlage: {issue.get('legal_basis', '')}
- Empfehlung des Scanners: {issue.get('recommendation', '')}

WEITERE OFFENE ISSUES DIESER WEBSITE:
{other_issues}

AUFGABE:
Erstelle eine VOLLSTÄNDIG INDIVIDUELLE Lösung speziell für {url} (CMS: {cms}).
Beziehe dich auf erkannte Dienste ({tracking}) und das konkrete CMS.

Antworte NUR mit folgendem JSON (kein Zusatztext):
{{
  "ai_solution": "Kurze Analyse: Warum ist das Problem relevant für {url}? (2-3 Sätze, Deutsch)",
  "steps": [
    "1. [CMS-spezifischer Schritt für {cms}]: genaue Beschreibung",
    "2. Nächster konkreter Schritt",
    "3. Weiterer Schritt",
    "4. Test: Wie prüfen ob erfolgreich?"
  ],
  "code_snippet": "Fertiger, produktionsreifer Code passend zu {cms} und den erkannten Diensten ({tracking}). Kein Platzhalter-Code."
}}

WICHTIG für code_snippet:
- WordPress → PHP/functions.php oder .htaccess
- Shopify → theme.liquid oder Shopify CDN
- Nginx → server{{}} Block
- Apache → .htaccess
- Für Cookies/Tracking: Echte Dienste ({tracking}) einbauen, nicht generische Platzhalter
- Bei UWG/Bewertungen: HTML-Snippet mit echtem Domain-Bezug zu {url}
- Mindestens 3 steps, maximal 6"""

    result = await _call_ai_json(prompt, SOLUTION_MODEL, max_tokens=1200)
    if not result:
        # Fallback: plain text solution
        plain = await _call_ai(
            f"Website: {url} | CMS: {cms} | Problem: {title}\nErstelle 4 konkrete Lösungsschritte auf Deutsch.",
            SOLUTION_MODEL, max_tokens=400, temperature=0.4
        )
        return {"ai_solution": plain} if plain else None
    return result


# ─────────────────────────────────────────────
# 3. Full Review Pass
# ─────────────────────────────────────────────

async def run_ai_review_pass(
    issues: List[Any],
    scan_result: Dict[str, Any],
    max_reviews: int = 20,
    max_solutions: int = 15,
) -> List[Any]:
    """
    Hauptfunktion: Führt einen vollständigen KI-Review-Pass über alle Issues durch.

    - Prüft und korrigiert Issue-Felder (Titel, Beschreibung, Severity, Risiko)
    - Generiert individuelle Lösungen für alle Issues (bis max_solutions)
    - Läuft parallel für Performance

    Args:
        issues:        Liste von ComplianceIssue-Objekten (Pydantic oder dict)
        scan_result:   Vollständiges Scan-Ergebnis für Kontext
        max_reviews:   Maximale Anzahl zu reviewender Issues
        max_solutions: Maximale Anzahl zu generierender Lösungen

    Returns:
        Aktualisierte Issues-Liste
    """
    if not OPENROUTER_API_KEY or not issues:
        return issues

    # Build scan context
    tech_stack = scan_result.get("tech_stack", {})
    tracking = scan_result.get("tracking_services", [])
    detected_cookies = scan_result.get("detected_cookies", [])
    if isinstance(detected_cookies, list) and detected_cookies and isinstance(detected_cookies[0], dict):
        cookie_names = [c.get("name", "") for c in detected_cookies[:10]]
    else:
        cookie_names = [str(c) for c in detected_cookies[:10]]

    all_issue_titles = []
    for iss in issues:
        t = iss.get("title") if isinstance(iss, dict) else getattr(iss, "title", "")
        if t:
            all_issue_titles.append(t)

    scan_context = {
        "url": scan_result.get("url", ""),
        "cms": ", ".join(tech_stack.get("cms", [])) or "Unbekannt",
        "tracking_services": tracking,
        "cookies": cookie_names,
        "all_issue_titles": all_issue_titles,
    }

    # Sort: critical first, then warning
    def _severity_order(iss):
        sev = iss.get("severity") if isinstance(iss, dict) else getattr(iss, "severity", "info")
        return {"critical": 0, "warning": 1, "info": 2}.get(sev, 3)

    sorted_issues = sorted(issues, key=_severity_order)

    # --- Phase 1: Review (correct fields) ---
    review_tasks = []
    for iss in sorted_issues[:max_reviews]:
        iss_dict = iss if isinstance(iss, dict) else _issue_to_dict(iss)
        review_tasks.append(review_issue(iss_dict, scan_context))

    try:
        review_results = await asyncio.wait_for(
            asyncio.gather(*review_tasks, return_exceptions=True),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        logger.warning("⚠️ AI Review Pass Timeout (Phase 1)")
        review_results = [{}] * len(review_tasks)

    # Apply review changes
    for i, iss in enumerate(sorted_issues[:max_reviews]):
        if i < len(review_results):
            changes = review_results[i]
            if isinstance(changes, dict) and changes:
                _apply_changes(iss, changes)

    # --- Phase 2: Individual solutions for all issues ---
    solution_tasks = []
    for iss in sorted_issues[:max_solutions]:
        iss_dict = iss if isinstance(iss, dict) else _issue_to_dict(iss)
        solution_tasks.append(generate_individual_solution(iss_dict, scan_context))

    try:
        solution_results = await asyncio.wait_for(
            asyncio.gather(*solution_tasks, return_exceptions=True),
            timeout=45.0
        )
    except asyncio.TimeoutError:
        logger.warning("⚠️ AI Review Pass Timeout (Phase 2)")
        solution_results = [None] * len(solution_tasks)

    # Assign solutions
    for i, iss in enumerate(sorted_issues[:max_solutions]):
        if i < len(solution_results):
            sol = solution_results[i]
            if sol and not isinstance(sol, Exception):
                if isinstance(sol, dict):
                    # Set ai_solution text
                    if sol.get("ai_solution"):
                        _set_field(iss, "ai_solution", sol["ai_solution"])
                    # Overwrite solution.steps and solution.code_snippet with AI-generated content
                    new_steps = sol.get("steps")
                    new_code = sol.get("code_snippet")
                    if new_steps or new_code:
                        existing_solution = getattr(iss, "solution", None) if not isinstance(iss, dict) else iss.get("solution")
                        if existing_solution is not None:
                            if new_steps and isinstance(new_steps, list) and len(new_steps) >= 2:
                                try:
                                    if isinstance(iss, dict):
                                        iss["solution"]["steps"] = new_steps
                                    else:
                                        existing_solution.steps = new_steps
                                except Exception:
                                    pass
                            if new_code and len(str(new_code).strip()) > 20:
                                try:
                                    if isinstance(iss, dict):
                                        iss["solution"]["code_snippet"] = new_code
                                    else:
                                        existing_solution.code_snippet = new_code
                                except Exception:
                                    pass
                else:
                    # Legacy: plain string solution
                    _set_field(iss, "ai_solution", sol)

    successful_reviews = sum(
        1 for r in review_results if isinstance(r, dict) and r and not r.get("_review_note", "").startswith("Keine")
    )
    successful_solutions = sum(1 for s in solution_results if s and not isinstance(s, Exception))
    logger.info(
        f"✅ AI Review Pass: {successful_reviews}/{min(len(issues), max_reviews)} reviews, "
        f"{successful_solutions}/{min(len(issues), max_solutions)} solutions"
    )

    return issues


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _issue_to_dict(iss: Any) -> Dict[str, Any]:
    fields = ["id", "title", "description", "recommendation", "category",
              "severity", "risk_euro_max", "risk_euro_min", "legal_basis", "ai_solution"]
    return {f: getattr(iss, f, None) for f in fields}


def _apply_changes(iss: Any, changes: Dict[str, Any]):
    for key, val in changes.items():
        if key.startswith("_"):
            continue
        if isinstance(iss, dict):
            iss[key] = val
        else:
            try:
                setattr(iss, key, val)
            except Exception:
                pass


def _set_field(iss: Any, field: str, value: Any):
    if isinstance(iss, dict):
        iss[field] = value
    else:
        try:
            setattr(iss, field, value)
        except Exception:
            pass
