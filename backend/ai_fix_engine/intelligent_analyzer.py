"""
Complyo Intelligent Analyzer
Context-aware AI analysis for generating personalized compliance fixes
"""

import os
import json
from typing import Dict, List, Any, Optional
import aiohttp


class IntelligentAnalyzer:
    """
    Analyzes compliance issues with full website context and generates smart fixes
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet"
    
    async def analyze_and_generate_fixes(self, scan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze scan results and generate personalized fixes using AI
        
        Args:
            scan_result: Complete scan result with issues, website_data, tech_stack, etc.
        
        Returns:
            List of smart fixes with type, content, priority, etc.
        """
        # Build comprehensive context
        context = self.build_comprehensive_context(scan_result)
        
        # Get issues to fix
        issues = scan_result.get("issues", [])
        
        if not issues:
            return []
        
        # Generate fixes for all issues
        smart_fixes = []
        
        # Group issues by category for more efficient AI calls
        categorized_issues = self._categorize_issues(issues)
        
        for category, category_issues in categorized_issues.items():
            try:
                category_fixes = await self._generate_fixes_for_category(
                    category,
                    category_issues,
                    context
                )
                smart_fixes.extend(category_fixes)
            except Exception as e:
                print(f"Error generating fixes for category {category}: {e}")
                # Fallback to basic fixes
                smart_fixes.extend(self._generate_fallback_fixes(category_issues))
        
        # Prioritize fixes
        smart_fixes = self._prioritize_fixes(smart_fixes)
        
        return smart_fixes
    
    def build_comprehensive_context(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build complete context for AI analysis
        """
        website_data = scan_result.get("website_data", {})
        seo_data = scan_result.get("seo_data", {})
        tech_stack = scan_result.get("tech_stack", {})
        structure = scan_result.get("structure", {})
        
        return {
            "url": scan_result.get("url", ""),
            "company": {
                "name": website_data.get("company_name"),
                "address": website_data.get("address"),
                "email": website_data.get("email"),
                "phone": website_data.get("phone"),
                "has_impressum": website_data.get("has_impressum", False),
                "has_datenschutz": website_data.get("has_datenschutz", False)
            },
            "shop_system": website_data.get("shop_system"),
            "technology": {
                "cms": tech_stack.get("cms", []),
                "frameworks": tech_stack.get("frameworks", []),
                "analytics": tech_stack.get("analytics", [])
            },
            "seo": {
                "title": seo_data.get("title"),
                "description": seo_data.get("description"),
                "img_without_alt": seo_data.get("img_without_alt", 0)
            },
            "structure": {
                "has_navigation": structure.get("has_navigation", False),
                "has_footer": structure.get("has_footer", False),
                "page_count": structure.get("page_count_estimate", 0)
            },
            "cookies": scan_result.get("detected_cookies", []),
            "compliance_score": scan_result.get("compliance_score", 0)
        }
    
    def _categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group issues by category
        """
        categorized = {
            "legal_texts": [],  # Impressum, Datenschutz
            "cookies": [],       # Cookie-Compliance
            "accessibility": [], # Barrierefreiheit
            "seo": [],          # SEO/Meta-Tags
            "other": []
        }
        
        for issue in issues:
            category = issue.get("category", "").lower()
            title = issue.get("title", "").lower()
            
            if any(keyword in category or keyword in title for keyword in ["impressum", "datenschutz", "agb", "widerruf", "legal", "rechtstext"]):
                categorized["legal_texts"].append(issue)
            elif any(keyword in category or keyword in title for keyword in ["cookie", "tracking", "consent"]):
                categorized["cookies"].append(issue)
            elif any(keyword in category or keyword in title for keyword in ["barriere", "accessibility", "wcag", "alt", "aria", "kontrast"]):
                categorized["accessibility"].append(issue)
            elif any(keyword in category or keyword in title for keyword in ["seo", "meta", "title", "description"]):
                categorized["seo"].append(issue)
            else:
                categorized["other"].append(issue)
        
        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}
    
    async def _generate_fixes_for_category(
        self, 
        category: str, 
        issues: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered fixes for a category of issues
        """
        # Build category-specific prompt
        prompt = self._build_prompt(category, issues, context)
        
        # Call AI
        if not self.api_key:
            print("Warning: No OPENROUTER_API_KEY - using fallback fixes")
            return self._generate_fallback_fixes(issues)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        
                        # Parse AI response
                        fixes = self._parse_ai_response(content, issues, category)
                        return fixes
                    else:
                        print(f"AI API error: {response.status}")
                        return self._generate_fallback_fixes(issues)
        
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._generate_fallback_fixes(issues)
    
    def _build_prompt(self, category: str, issues: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Build category-specific prompt for AI
        """
        prompts = {
            "legal_texts": self._build_legal_text_prompt(issues, context),
            "cookies": self._build_cookie_prompt(issues, context),
            "accessibility": self._build_accessibility_prompt(issues, context),
            "seo": self._build_seo_prompt(issues, context),
            "other": self._build_generic_prompt(issues, context)
        }
        
        return prompts.get(category, prompts["other"])
    
    def _build_legal_text_prompt(self, issues: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Prompt for legal text issues (Impressum, Datenschutz)
        """
        company_name = context["company"]["name"] or "[FIRMENNAME]"
        address = context["company"]["address"] or "[ADRESSE]"
        email = context["company"]["email"] or "[EMAIL]"
        shop_system = context["shop_system"]
        
        issues_text = "\n".join([f"- {issue['title']}: {issue['description']}" for issue in issues])
        
        return f"""Du bist ein Experte für deutsches Internetrecht.

WEBSITE-KONTEXT:
- URL: {context["url"]}
- Firma: {company_name}
- Adresse: {address}
- Email: {email}
- Shop-System: {shop_system or "Kein E-Commerce"}
- Cookies: {len(context["cookies"])} erkannt

GEFUNDENE PROBLEME:
{issues_text}

AUFGABE:
Erstelle für jedes Problem eine KONKRETE Lösung im JSON-Format:

{{
  "fixes": [
    {{
      "issue_id": "issue_id_hier",
      "fix_type": "text",
      "title": "Kurze Beschreibung",
      "content": "Der fertige rechtssichere Text (mit echten Firmendaten gefüllt)",
      "instructions": "Schritt-für-Schritt Anleitung zur Umsetzung",
      "estimated_time": "5 Minuten"
    }}
  ]
}}

WICHTIG:
- Nutze die ECHTEN Firmendaten aus dem Kontext
- Bei fehlenden Daten: Verwende Platzhalter wie [IHRE FIRMA]
- Texte müssen DSGVO/TMG-konform sein
- Gib konkrete, kopierbare Lösungen"""
    
    def _build_cookie_prompt(self, issues: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Prompt for cookie compliance issues
        """
        cookies = context["cookies"]
        cookies_text = ", ".join([c.get("name", "Unknown") for c in cookies]) if cookies else "Keine Cookies erkannt"
        
        issues_text = "\n".join([f"- {issue['title']}: {issue['description']}" for issue in issues])
        
        return f"""Du bist ein Experte für Cookie-Compliance (TTDSG).

WEBSITE-KONTEXT:
- URL: {context["url"]}
- Erkannte Cookies: {cookies_text}
- Analytics-Tools: {", ".join(context["technology"]["analytics"])}

GEFUNDENE PROBLEME:
{issues_text}

AUFGABE:
Erstelle Lösungen als JSON:

{{
  "fixes": [
    {{
      "issue_id": "issue_id_hier",
      "fix_type": "code" | "guide" | "widget",
      "title": "Lösung Beschreibung",
      "content": "Code-Snippet ODER Anleitung",
      "integration_guide": "Wo und wie einfügen",
      "estimated_time": "10 Minuten"
    }}
  ]
}}

WICHTIG:
- Für Cookie-Banner: Erstelle Widget-Integration
- Liste alle erkannten Cookies
- DSGVO & TTDSG konform"""
    
    def _build_accessibility_prompt(self, issues: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Prompt for accessibility issues
        """
        tech = context["technology"]
        cms = ", ".join(tech["cms"]) if tech["cms"] else "Unbekannt"
        frameworks = ", ".join(tech["frameworks"]) if tech["frameworks"] else "Keine"
        
        issues_text = "\n".join([f"- {issue['title']}: {issue['description']}" for issue in issues])
        
        return f"""Du bist ein Barrierefreiheits-Experte (WCAG 2.1 Level AA).

WEBSITE-KONTEXT:
- URL: {context["url"]}
- CMS: {cms}
- Framework: {frameworks}
- Bilder ohne Alt: {context["seo"]["img_without_alt"]}

GEFUNDENE PROBLEME:
{issues_text}

AUFGABE:
Erstelle CODE-LÖSUNGEN als JSON:

{{
  "fixes": [
    {{
      "issue_id": "issue_id_hier",
      "fix_type": "code",
      "title": "Was wird gefixt",
      "content": "Fertiger HTML/CSS Code zum Einbauen",
      "file": "Datei/Seite wo einfügen",
      "line_number": "Wenn bekannt",
      "before_code": "Alter Code (falls ersetzt wird)",
      "after_code": "Neuer Code",
      "explanation": "Was macht der Code",
      "estimated_time": "5 Minuten"
    }}
  ]
}}

WICHTIG:
- Code muss DIREKT funktionieren
- Kein Overlay, echter Code
- WCAG 2.1 AA konform
- Spezifisch für erkanntes CMS/Framework"""
    
    def _build_seo_prompt(self, issues: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Prompt for SEO issues
        """
        title = context["seo"]["title"] or "Kein Title"
        description = context["seo"]["description"] or "Keine Description"
        
        issues_text = "\n".join([f"- {issue['title']}" for issue in issues])
        
        return f"""Du bist ein SEO-Experte.

WEBSITE-KONTEXT:
- URL: {context["url"]}
- Aktueller Title: {title}
- Aktuelle Description: {description}

GEFUNDENE PROBLEME:
{issues_text}

AUFGABE:
Erstelle Meta-Tag Fixes als JSON:

{{
  "fixes": [
    {{
      "issue_id": "issue_id_hier",
      "fix_type": "code",
      "title": "Meta-Tag hinzufügen/ändern",
      "content": "<meta ...> Code",
      "instructions": "Wo im <head> einfügen",
      "estimated_time": "2 Minuten"
    }}
  ]
}}"""
    
    def _build_generic_prompt(self, issues: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Generic prompt for other issues
        """
        issues_text = "\n".join([f"- {issue['title']}: {issue['description']}" for issue in issues])
        
        return f"""Du bist ein Compliance-Experte.

WEBSITE: {context["url"]}

PROBLEME:
{issues_text}

Erstelle Lösungen als JSON mit: issue_id, fix_type, title, content, instructions"""
    
    def _parse_ai_response(self, ai_content: str, issues: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
        """
        Parse AI response and structure it
        """
        try:
            # Try to extract JSON from response
            # Look for JSON block
            if "```json" in ai_content:
                json_start = ai_content.find("```json") + 7
                json_end = ai_content.find("```", json_start)
                json_str = ai_content[json_start:json_end].strip()
            elif "{" in ai_content:
                json_start = ai_content.find("{")
                json_end = ai_content.rfind("}") + 1
                json_str = ai_content[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            parsed = json.loads(json_str)
            fixes = parsed.get("fixes", [])
            
            # Add metadata
            for fix in fixes:
                fix["generated_by"] = "ai"
                fix["category"] = category
                if "priority" not in fix:
                    fix["priority"] = "medium"
            
            return fixes
        
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._generate_fallback_fixes(issues)
    
    def _generate_fallback_fixes(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate basic fixes if AI fails
        """
        fallback_fixes = []
        
        for issue in issues:
            fallback_fixes.append({
                "issue_id": issue.get("id", "unknown"),
                "fix_type": "guide",
                "title": f"Anleitung: {issue.get('title', 'Problem beheben')}",
                "content": issue.get("recommendation", "Bitte beheben Sie dieses Problem gemäß den Empfehlungen."),
                "instructions": "Folgen Sie der Empfehlung und prüfen Sie die Umsetzung.",
                "estimated_time": "15 Minuten",
                "generated_by": "fallback",
                "category": issue.get("category", "other"),
                "priority": "medium"
            })
        
        return fallback_fixes
    
    def _prioritize_fixes(self, fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize fixes by severity, impact, and ease
        """
        priority_order = {"high": 3, "medium": 2, "low": 1}
        
        # Sort by priority
        fixes.sort(key=lambda f: priority_order.get(f.get("priority", "medium"), 2), reverse=True)
        
        return fixes

