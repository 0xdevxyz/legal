"""
Complyo Smart Fix Generator
Generates various types of fixes: Code, Text, Widget, Guided Setup
Integrates with erecht24 for legal texts (White-Label)
"""

import os
from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class SmartFixGenerator:
    """
    Generates different types of fixes based on issue category and context
    """
    
    def __init__(self):
        self.erecht24_service = None  # Will be injected
    
    def set_erecht24_service(self, service):
        """Inject erecht24 service for legal text generation"""
        self.erecht24_service = service
    
    async def generate(self, fix_id: str, fix_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete fix with all necessary content
        
        Args:
            fix_id: Unique fix identifier
            fix_data: Fix data from intelligent_analyzer
            context: Website context (company data, tech stack, etc.)
        
        Returns:
            Complete fix package ready for user
        """
        fix_type = fix_data.get("fix_type", "guide")
        
        generators = {
            "code": self._generate_code_fix,
            "text": self._generate_text_fix,
            "widget": self._generate_widget_fix,
            "guide": self._generate_guide_fix
        }
        
        generator = generators.get(fix_type, self._generate_guide_fix)
        
        return await generator(fix_id, fix_data, context)
    
    async def _generate_code_fix(self, fix_id: str, fix_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate code-based fix (HTML/CSS/JS)
        """
        return {
            "fix_id": fix_id,
            "type": "code",
            "title": fix_data.get("title", "Code-Fix"),
            "description": fix_data.get("content", ""),
            "code": {
                "language": self._detect_code_language(fix_data.get("content", "")),
                "content": fix_data.get("content", ""),
                "before": fix_data.get("before_code"),
                "after": fix_data.get("after_code")
            },
            "integration": {
                "file": fix_data.get("file", "Siehe Anleitung"),
                "line_number": fix_data.get("line_number"),
                "instructions": fix_data.get("integration_guide", fix_data.get("instructions", ""))
            },
            "explanation": fix_data.get("explanation", ""),
            "estimated_time": fix_data.get("estimated_time", "10 Minuten"),
            "video_tutorial": None,  # Can be added later
            "generated_at": datetime.now().isoformat(),
            "branding": "Erstellt von Complyo"
        }
    
    async def _generate_text_fix(self, fix_id: str, fix_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate text-based fix (Legal texts via erecht24, White-Label)
        """
        # Determine legal text type
        title = fix_data.get("title", "").lower()
        content = fix_data.get("content", "")
        
        legal_text_type = None
        if "impressum" in title or "imprint" in title:
            legal_text_type = "impressum"
        elif "datenschutz" in title or "privacy" in title:
            legal_text_type = "datenschutz"
        elif "agb" in title or "terms" in title:
            legal_text_type = "agb"
        elif "widerruf" in title:
            legal_text_type = "widerruf"
        
        # If legal text type detected and erecht24 available, use it
        final_text = content
        source = "AI-Generated"
        
        if legal_text_type and self.erecht24_service:
            try:
                # Get personalized legal text from erecht24
                # Note: This would need user's erecht24 project_id from context
                project_id = context.get("erecht24_project_id")
                if project_id:
                    erecht24_text = await self.erecht24_service.get_legal_text(
                        project_id=project_id,
                        text_type=legal_text_type,
                        language="de"
                    )
                    if erecht24_text:
                        final_text = erecht24_text
                        source = "eRecht24 (via Complyo)"
            except Exception as e:
                print(f"eRecht24 integration error: {e}")
        
        # Fill in company data placeholders
        final_text = self._fill_placeholders(final_text, context)
        
        return {
            "fix_id": fix_id,
            "type": "text",
            "title": fix_data.get("title", "Rechtssicherer Text"),
            "description": "Fertiger Text zum Kopieren und Einfügen",
            "text": {
                "content": final_text,
                "format": "html",
                "source": source
            },
            "integration": {
                "where": f"Erstellen Sie eine neue Seite '{legal_text_type or 'text'}.html'",
                "instructions": fix_data.get("instructions", self._get_default_text_instructions(legal_text_type))
            },
            "download_options": {
                "txt": True,
                "html": True,
                "pdf": False  # Can be implemented later
            },
            "estimated_time": fix_data.get("estimated_time", "5 Minuten"),
            "generated_at": datetime.now().isoformat(),
            "branding": "Erstellt von Complyo",
            "disclaimer": "Bitte überprüfen und ggf. an Ihre Bedürfnisse anpassen."
        }
    
    async def _generate_widget_fix(self, fix_id: str, fix_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate widget-based fix (Complyo Cookie Widget, Accessibility Tools)
        """
        # Determine widget type
        title = fix_data.get("title", "").lower()
        
        widget_type = "generic"
        widget_config = {}
        
        if "cookie" in title or "consent" in title:
            widget_type = "cookie-consent"
            widget_config = {
                "cookies": context.get("cookies", []),
                "detected_tools": context.get("technology", {}).get("analytics", [])
            }
        elif "barriere" in title or "accessibility" in title or "contrast" in title:
            widget_type = "accessibility-tools"
            widget_config = {
                "features": ["contrast", "fontsize", "screen-reader"]
            }
        
        # Generate widget URL and integration code
        site_id = context.get("site_id", "demo")
        widget_url = f"https://widget.complyo.tech/{widget_type}.js"
        
        integration_code = f'''<!-- Complyo {widget_type.title()} Widget -->
<script 
  src="{widget_url}" 
  data-site-id="{site_id}"
  data-config='{json.dumps(widget_config)}'
></script>
<!-- End Complyo Widget -->'''
        
        return {
            "fix_id": fix_id,
            "type": "widget",
            "title": fix_data.get("title", "Widget-Integration"),
            "description": "One-Line Integration eines Complyo Widgets",
            "widget": {
                "type": widget_type,
                "url": widget_url,
                "config": widget_config
            },
            "integration": {
                "code": integration_code,
                "where": "Vor dem schließenden </body>-Tag",
                "instructions": f"""
1. Kopieren Sie den Code unten
2. Öffnen Sie Ihre Haupt-HTML-Datei (z.B. index.html)
3. Fügen Sie den Code VOR dem </body>-Tag ein
4. Speichern und testen Sie die Website

Das Widget ist sofort funktionsbereit und DSGVO-konform konfiguriert.
""",
                "video_tutorial": f"https://complyo.tech/tutorials/{widget_type}"
            },
            "preview": f"https://widget.complyo.tech/preview/{widget_type}?site={site_id}",
            "estimated_time": fix_data.get("estimated_time", "3 Minuten"),
            "generated_at": datetime.now().isoformat(),
            "branding": "Powered by Complyo"
        }
    
    async def _generate_guide_fix(self, fix_id: str, fix_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate guided step-by-step fix
        """
        instructions = fix_data.get("instructions", fix_data.get("content", ""))
        
        # Try to parse instructions into steps
        steps = self._parse_instructions_to_steps(instructions)
        
        return {
            "fix_id": fix_id,
            "type": "guide",
            "title": fix_data.get("title", "Schritt-für-Schritt Anleitung"),
            "description": "Folgen Sie dieser Anleitung zur Umsetzung",
            "steps": steps,
            "resources": {
                "documentation": [],
                "video_tutorials": [],
                "external_tools": []
            },
            "estimated_time": fix_data.get("estimated_time", "15 Minuten"),
            "difficulty": "medium",
            "generated_at": datetime.now().isoformat(),
            "branding": "Erstellt von Complyo"
        }
    
    def _detect_code_language(self, code: str) -> str:
        """Detect programming language of code snippet"""
        code_lower = code.lower()
        
        if "<html" in code_lower or "<div" in code_lower or "<script" in code_lower:
            return "html"
        elif "function" in code_lower or "const" in code_lower or "=>" in code:
            return "javascript"
        elif "display:" in code_lower or "color:" in code_lower or "{" in code and "}" in code:
            return "css"
        elif "<?php" in code_lower:
            return "php"
        else:
            return "text"
    
    def _fill_placeholders(self, text: str, context: Dict[str, Any]) -> str:
        """Fill in company data placeholders in text"""
        company = context.get("company", {})
        
        replacements = {
            "[FIRMENNAME]": company.get("name", "[IHRE FIRMA]"),
            "[FIRMA]": company.get("name", "[IHRE FIRMA]"),
            "[COMPANY_NAME]": company.get("name", "[YOUR COMPANY]"),
            "[ADRESSE]": company.get("address", "[IHRE ADRESSE]"),
            "[ADDRESS]": company.get("address", "[YOUR ADDRESS]"),
            "[EMAIL]": company.get("email", "[IHRE@EMAIL.DE]"),
            "[TELEFON]": company.get("phone", "[IHRE TELEFONNUMMER]"),
            "[PHONE]": company.get("phone", "[YOUR PHONE]"),
            "[URL]": context.get("url", "[IHRE-WEBSITE.DE]")
        }
        
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        
        return text
    
    def _get_default_text_instructions(self, text_type: Optional[str]) -> str:
        """Get default instructions for text integration"""
        if text_type == "impressum":
            return """
1. Erstellen Sie eine neue Seite 'impressum.html' in Ihrem Website-Root
2. Kopieren Sie den Text in diese Datei
3. Verlinken Sie die Seite im Footer: <a href="/impressum.html">Impressum</a>
4. Der Link muss auf jeder Seite sichtbar sein
5. Testen Sie die Erreichbarkeit
"""
        elif text_type == "datenschutz":
            return """
1. Erstellen Sie eine neue Seite 'datenschutz.html' 
2. Kopieren Sie den Text in diese Datei
3. Verlinken Sie die Seite im Footer: <a href="/datenschutz.html">Datenschutz</a>
4. Der Link muss auf jeder Seite sichtbar sein
5. Aktualisieren Sie den Text bei Änderungen der Datenverarbeitung
"""
        else:
            return """
1. Erstellen Sie eine neue HTML-Seite
2. Kopieren Sie den Text in diese Datei
3. Verlinken Sie die Seite in Ihrem Footer
4. Prüfen Sie die Erreichbarkeit auf allen Seiten
"""
    
    def _parse_instructions_to_steps(self, instructions: str) -> List[Dict[str, Any]]:
        """Parse plain text instructions into structured steps"""
        steps = []
        
        # Try to split by numbers (1., 2., etc.) or dashes (-, •)
        lines = instructions.split("\n")
        
        current_step = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with number or bullet
            if re.match(r'^\d+\.', line) or line.startswith('-') or line.startswith('•'):
                if current_step:
                    steps.append(current_step)
                
                # Clean the line
                clean_line = re.sub(r'^\d+\.?\s*|^[-•]\s*', '', line)
                current_step = {
                    "title": clean_line[:50] + "..." if len(clean_line) > 50 else clean_line,
                    "description": clean_line,
                    "completed": False
                }
            elif current_step:
                # Add to current step description
                current_step["description"] += " " + line
        
        if current_step:
            steps.append(current_step)
        
        # If no steps found, create one generic step
        if not steps:
            steps.append({
                "title": "Anleitung folgen",
                "description": instructions,
                "completed": False
            })
        
        return steps


import re  # Import added for regex

