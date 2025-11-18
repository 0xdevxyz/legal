"""
Guide Handler - Step-by-Step Instructions

Behandelt komplexe Fixes als Schritt-für-Schritt-Anleitungen
"""

from typing import Dict, Any, Optional, List


class GuideHandler:
    """Handler für Schritt-für-Schritt-Anleitungen"""
    
    async def handle(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        ai_generated_fix: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generiert Schritt-für-Schritt-Anleitung
        """
        # Use AI-generated guide if available
        if ai_generated_fix and ai_generated_fix.get("steps"):
            return self._enrich_ai_guide(ai_generated_fix, issue, context)
        
        # Fallback: Generate basic guide
        return self._generate_template_guide(issue, context)
    
    def _enrich_ai_guide(
        self,
        ai_guide: Dict[str, Any],
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reichert AI-generierte Anleitung an
        """
        enriched = ai_guide.copy()
        
        # Add progress tracking
        steps = enriched.get("steps", [])
        for i, step in enumerate(steps):
            step["completed"] = False
            step["step_id"] = f"step_{i+1}"
        
        enriched["steps"] = steps
        enriched["total_steps"] = len(steps)
        enriched["current_step"] = 1
        enriched["progress_percentage"] = 0
        
        # Add video tutorials if available
        enriched["video_tutorials"] = self._get_related_videos(issue)
        
        # Add external resources
        enriched["external_resources"] = self._get_external_resources(issue)
        
        # Add FAQ
        enriched["faq"] = self._get_faq_for_issue(issue)
        
        # Add CMS-specific tips
        cms_list = context.get("technology", {}).get("cms", [])
        if cms_list:
            enriched["cms_tips"] = self._get_cms_tips(cms_list[0], issue)
        
        return enriched
    
    def _generate_template_guide(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generiert Template-basierte Anleitung als Fallback
        """
        # Generate basic steps from issue data
        steps = self._generate_basic_steps(issue, context)
        
        return {
            "fix_id": issue.get("id", "guide_fix"),
            "title": f"Anleitung: {issue.get('title', 'Problem beheben')}",
            "description": issue.get("description", ""),
            "steps": steps,
            "difficulty": self._determine_difficulty(issue),
            "estimated_time": self._estimate_time(steps),
            "resources": {
                "documentation_links": self._get_relevant_docs(issue),
                "video_tutorials": self._get_related_videos(issue),
                "tools_needed": self._get_required_tools(issue, context)
            },
            "prerequisites": self._get_prerequisites(issue, context),
            "total_steps": len(steps),
            "current_step": 1,
            "progress_percentage": 0
        }
    
    def _generate_basic_steps(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generiert Basis-Schritte aus Issue-Daten
        """
        recommendation = issue.get("recommendation", "")
        
        steps = [
            {
                "step_number": 1,
                "step_id": "step_1",
                "title": "Problem analysieren",
                "description": f"{issue.get('description', 'Analysieren Sie das Problem.')}\n\n**Was ist das Problem?** {issue.get('title', '')}",
                "validation": "Verstehen Sie das Problem und seine Auswirkungen?",
                "completed": False
            },
            {
                "step_number": 2,
                "step_id": "step_2",
                "title": "Lösung vorbereiten",
                "description": f"Vorbereitung der Lösung:\n\n{recommendation}\n\nStellen Sie sicher, dass Sie Zugriff auf die benötigten Dateien/Systeme haben.",
                "validation": "Haben Sie alle benötigten Zugänge und Tools bereit?",
                "completed": False
            },
            {
                "step_number": 3,
                "step_id": "step_3",
                "title": "Backup erstellen",
                "description": "Erstellen Sie ein Backup der zu ändernden Dateien.\n\n- Bei WordPress: Theme-Dateien sichern\n- Bei Shopify: Theme exportieren\n- Bei Custom-Code: Git-Commit erstellen\n\n**Wichtig:** Niemals ohne Backup arbeiten!",
                "validation": "Backup erstellt und verifiziert?",
                "completed": False
            },
            {
                "step_number": 4,
                "step_id": "step_4",
                "title": "Lösung implementieren",
                "description": f"Implementieren Sie die Lösung:\n\n{recommendation}\n\nFolgen Sie dabei den Best Practices für Ihr System.",
                "code_example": self._get_example_code(issue),
                "validation": "Code wurde korrekt eingefügt?",
                "completed": False
            },
            {
                "step_number": 5,
                "step_id": "step_5",
                "title": "Testen und validieren",
                "description": "Testen Sie die Implementierung:\n\n" + "\n".join([
                    "1. Laden Sie die Website neu (Shift + F5 für harten Reload)",
                    "2. Testen Sie in verschiedenen Browsern",
                    "3. Prüfen Sie die Mobile-Ansicht",
                    "4. Validieren Sie mit entsprechenden Tools",
                    "5. Lassen Sie jemanden drüber schauen"
                ]),
                "validation": "Funktioniert alles wie erwartet? Keine Fehler in der Console?",
                "completed": False
            },
            {
                "step_number": 6,
                "step_id": "step_6",
                "title": "Dokumentieren",
                "description": "Dokumentieren Sie die Änderung:\n\n" + "\n".join([
                    "- Was wurde geändert?",
                    "- Warum wurde es geändert?",
                    "- Wann wurde es geändert?",
                    "- Von wem wurde es geändert?",
                    "",
                    "Dies hilft bei zukünftigen Wartungen und Updates."
                ]),
                "validation": "Änderung dokumentiert?",
                "completed": False
            }
        ]
        
        return steps
    
    def _get_example_code(self, issue: Dict[str, Any]) -> Optional[str]:
        """Generiert Beispiel-Code wenn möglich"""
        # Return None for now, would be generated by AI in real implementation
        return None
    
    def _determine_difficulty(self, issue: Dict[str, Any]) -> str:
        """Bestimmt Schwierigkeitsgrad"""
        category = issue.get("category", "").lower()
        
        # Simple issues
        if any(keyword in category for keyword in ["alt", "meta", "title"]):
            return "beginner"
        
        # Medium complexity
        if any(keyword in category for keyword in ["css", "cookie", "banner"]):
            return "intermediate"
        
        # Complex issues
        if any(keyword in category for keyword in ["javascript", "php", "api", "backend"]):
            return "advanced"
        
        return "intermediate"
    
    def _estimate_time(self, steps: List[Dict[str, Any]]) -> str:
        """Schätzt Zeit basierend auf Schritten"""
        num_steps = len(steps)
        
        if num_steps <= 3:
            return "10-15 Minuten"
        elif num_steps <= 5:
            return "15-30 Minuten"
        elif num_steps <= 8:
            return "30-45 Minuten"
        else:
            return "45-60 Minuten"
    
    def _get_relevant_docs(self, issue: Dict[str, Any]) -> List[str]:
        """Gibt relevante Dokumentations-Links"""
        docs = []
        
        category = issue.get("category", "").lower()
        title = issue.get("title", "").lower()
        
        # DSGVO/Legal
        if "datenschutz" in title or "dsgvo" in category:
            docs.extend([
                "https://dsgvo-gesetz.de/",
                "https://www.datenschutz.org/dsgvo/"
            ])
        
        # Impressum
        if "impressum" in title:
            docs.extend([
                "https://www.gesetze-im-internet.de/tmg/__5.html",
                "https://www.e-recht24.de/impressum-generator.html"
            ])
        
        # Accessibility
        if "barriere" in title or "wcag" in category:
            docs.extend([
                "https://www.w3.org/WAI/WCAG21/quickref/",
                "https://www.bitvtest.de/"
            ])
        
        # Cookie/TTDSG
        if "cookie" in title:
            docs.extend([
                "https://www.gesetze-im-internet.de/ttdsg/__25.html"
            ])
        
        return docs
    
    def _get_related_videos(self, issue: Dict[str, Any]) -> List[Dict[str, str]]:
        """Gibt verwandte Video-Tutorials"""
        # Placeholder - würde in echter Implementation YouTube-API nutzen
        return []
    
    def _get_required_tools(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Gibt benötigte Tools/Programme"""
        tools = ["Text-Editor (VS Code, Sublime Text, etc.)"]
        
        category = issue.get("category", "").lower()
        
        if "ftp" in issue.get("description", "").lower():
            tools.append("FTP-Client (FileZilla, WinSCP)")
        
        cms = context.get("technology", {}).get("cms", [])
        if cms:
            tools.append(f"{cms[0]}-Admin-Zugang")
        
        if "git" in issue.get("description", "").lower():
            tools.append("Git")
        
        return tools
    
    def _get_prerequisites(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Gibt Voraussetzungen"""
        prereqs = [
            "Zugang zur Website",
            "Grundkenntnisse in HTML/CSS"
        ]
        
        difficulty = self._determine_difficulty(issue)
        
        if difficulty == "advanced":
            prereqs.extend([
                "JavaScript-Kenntnisse",
                "Verständnis von Backend-Technologien"
            ])
        
        cms = context.get("technology", {}).get("cms", [])
        if cms:
            prereqs.append(f"{cms[0]}-Grundkenntnisse")
        
        return prereqs
    
    def _get_cms_tips(self, cms: str, issue: Dict[str, Any]) -> List[Dict[str, str]]:
        """CMS-spezifische Tipps"""
        cms_lower = cms.lower()
        
        tips = {
            "wordpress": [
                {
                    "title": "Child-Theme verwenden",
                    "description": "Ändern Sie niemals direkt das Parent-Theme. Nutzen Sie ein Child-Theme."
                },
                {
                    "title": "Plugin verwenden",
                    "description": "Für Code-Snippets nutzen Sie das 'Code Snippets' Plugin statt functions.php direkt zu bearbeiten."
                }
            ],
            "shopify": [
                {
                    "title": "Theme-Duplicate erstellen",
                    "description": "Erstellen Sie eine Kopie Ihres Themes vor Änderungen."
                },
                {
                    "title": "Liquid-Syntax",
                    "description": "Shopify nutzt Liquid-Templates. Beachten Sie die Syntax."
                }
            ],
            "wix": [
                {
                    "title": "Velo by Wix",
                    "description": "Für Custom-Code nutzen Sie die Velo-Entwicklungsumgebung."
                }
            ]
        }
        
        return tips.get(cms_lower, [])
    
    def _get_external_resources(self, issue: Dict[str, Any]) -> List[Dict[str, str]]:
        """Externe Ressourcen/Links"""
        resources = []
        
        category = issue.get("category", "").lower()
        
        if "dsgvo" in category or "datenschutz" in issue.get("title", "").lower():
            resources.append({
                "title": "DSGVO-Volltext",
                "url": "https://dsgvo-gesetz.de/",
                "type": "documentation"
            })
        
        if "barriere" in issue.get("title", "").lower():
            resources.append({
                "title": "WCAG 2.1 Quick Reference",
                "url": "https://www.w3.org/WAI/WCAG21/quickref/",
                "type": "documentation"
            })
        
        return resources
    
    def _get_faq_for_issue(self, issue: Dict[str, Any]) -> List[Dict[str, str]]:
        """FAQ für Issue-Typ"""
        faq = [
            {
                "question": "Was passiert, wenn ich einen Fehler mache?",
                "answer": "Deshalb ist das Backup in Schritt 3 so wichtig! Sie können jederzeit auf den vorherigen Zustand zurück."
            },
            {
                "question": "Kann ich Hilfe bekommen?",
                "answer": "Ja! Nutzen Sie den Complyo-Support oder konsultieren Sie einen Entwickler, wenn Sie unsicher sind."
            },
            {
                "question": "Muss ich das sofort umsetzen?",
                "answer": "Je nach Schweregrad. Kritische Probleme (DSGVO-Verstöße) sollten zeitnah behoben werden."
            }
        ]
        
        return faq


