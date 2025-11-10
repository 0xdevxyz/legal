"""
Complyo Live Validator
Validates if fixes have been implemented correctly via targeted re-scans
"""

from typing import Dict, Any, Optional
from compliance_engine.scanner import ComplianceScanner


class LiveValidator:
    """
    Performs targeted validation of specific compliance fixes
    """
    
    async def validate_fix(self, issue_id: str, website_url: str, issue_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate if a specific issue has been resolved
        
        Args:
            issue_id: Unique identifier for the issue
            website_url: Website to validate
            issue_data: Original issue data for context
            
        Returns:
            Validation result with status, message, and suggestions
        """
        try:
            # Perform targeted scan
            async with ComplianceScanner() as scanner:
                scan_result = await scanner.scan_website(website_url)
            
            # Get issue category for matching
            if issue_data:
                category = issue_data.get("category", "").lower()
                title = issue_data.get("title", "").lower()
            else:
                # Try to infer from issue_id
                category = self._infer_category_from_id(issue_id)
                title = ""
            
            # Check if issue is resolved
            is_resolved = self._check_issue_resolved(scan_result, category, title)
            
            if is_resolved:
                return {
                    "status": "resolved",
                    "message": "Problem erfolgreich behoben! ✅",
                    "details": "Die Compliance-Prüfung zeigt, dass das Problem nicht mehr vorhanden ist.",
                    "new_compliance_score": scan_result.get("compliance_score", 0)
                }
            else:
                # Find suggestions based on remaining issues
                suggestions = self._generate_suggestions(scan_result, category)
                
                return {
                    "status": "pending",
                    "message": "Problem noch nicht vollständig behoben",
                    "details": "Die Implementierung scheint noch nicht abgeschlossen zu sein.",
                    "suggestions": suggestions,
                    "current_compliance_score": scan_result.get("compliance_score", 0)
                }
        
        except Exception as e:
            print(f"Error in validate_fix: {e}")
            return {
                "status": "error",
                "message": "Validierung fehlgeschlagen",
                "details": f"Es gab einen Fehler bei der Überprüfung: {str(e)}",
                "suggestions": [
                    "Versuchen Sie es in einigen Minuten erneut",
                    "Stellen Sie sicher, dass die Website erreichbar ist"
                ]
            }
    
    def _check_issue_resolved(self, scan_result: Dict[str, Any], category: str, title: str) -> bool:
        """
        Check if a specific issue category/type is resolved
        """
        issues = scan_result.get("issues", [])
        
        # Check if any issue matches the category
        for issue in issues:
            if isinstance(issue, dict):
                issue_cat = issue.get("category", "").lower()
                issue_title = issue.get("title", "").lower()
                
                # Match by category
                if category and category in issue_cat:
                    return False
                
                # Match by title keywords
                if title:
                    title_words = title.split()
                    if any(word in issue_title for word in title_words if len(word) > 3):
                        return False
        
        return True
    
    def _infer_category_from_id(self, issue_id: str) -> str:
        """
        Try to infer category from issue_id
        """
        issue_id_lower = issue_id.lower()
        
        if "impressum" in issue_id_lower or "imprint" in issue_id_lower:
            return "impressum"
        elif "datenschutz" in issue_id_lower or "privacy" in issue_id_lower or "dsgvo" in issue_id_lower:
            return "datenschutz"
        elif "cookie" in issue_id_lower:
            return "cookie"
        elif "barriere" in issue_id_lower or "accessibility" in issue_id_lower or "wcag" in issue_id_lower:
            return "barrierefreiheit"
        elif "agb" in issue_id_lower or "terms" in issue_id_lower:
            return "legal"
        else:
            return ""
    
    def _generate_suggestions(self, scan_result: Dict[str, Any], category: str) -> list:
        """
        Generate helpful suggestions based on scan results and category
        """
        suggestions = []
        
        if category == "impressum":
            suggestions = [
                "Stellen Sie sicher, dass die Impressum-Seite unter /impressum oder /imprint erreichbar ist",
                "Der Link zum Impressum muss im Footer auf jeder Seite sichtbar sein",
                "Überprüfen Sie, ob alle Pflichtangaben enthalten sind (Name, Adresse, Kontakt)"
            ]
        elif category == "datenschutz":
            suggestions = [
                "Die Datenschutzerklärung sollte unter /datenschutz oder /privacy erreichbar sein",
                "Verlinken Sie die Datenschutzerklärung im Footer",
                "Stellen Sie sicher, dass alle Datenverarbeitungen beschrieben sind"
            ]
        elif "cookie" in category:
            suggestions = [
                "Der Cookie-Banner muss BEVOR Cookies gesetzt werden angezeigt werden",
                "Nutzer müssen Cookies ablehnen können",
                "Alle gesetzten Cookies müssen in der Datenschutzerklärung erklärt werden"
            ]
        elif "barriere" in category or "accessibility" in category:
            suggestions = [
                "Überprüfen Sie, ob der Code korrekt in die HTML-Datei eingefügt wurde",
                "Leeren Sie den Browser-Cache und testen Sie erneut",
                "Verwenden Sie Browser-Developer-Tools um zu prüfen, ob der Code geladen wird"
            ]
        else:
            suggestions = [
                "Leeren Sie den Browser-Cache (Ctrl+Shift+R oder Cmd+Shift+R)",
                "Warten Sie einige Minuten - manche Änderungen brauchen Zeit",
                "Überprüfen Sie die Implementierung nochmals anhand der Anleitung"
            ]
        
        return suggestions
    
    async def batch_validate(self, fix_ids: list, website_url: str, issues_data: Optional[Dict[str, Dict]] = None) -> Dict[str, Any]:
        """
        Validate multiple fixes at once
        
        Args:
            fix_ids: List of issue IDs to validate
            website_url: Website to check
            issues_data: Dict mapping issue_id to issue data
            
        Returns:
            Dict with validation results for each fix
        """
        results = {}
        
        # Single scan for efficiency
        async with ComplianceScanner() as scanner:
            scan_result = await scanner.scan_website(website_url)
        
        # Check each fix
        for fix_id in fix_ids:
            issue_data = issues_data.get(fix_id) if issues_data else None
            
            # Reuse scan result
            if issue_data:
                category = issue_data.get("category", "").lower()
                title = issue_data.get("title", "").lower()
            else:
                category = self._infer_category_from_id(fix_id)
                title = ""
            
            is_resolved = self._check_issue_resolved(scan_result, category, title)
            
            results[fix_id] = {
                "resolved": is_resolved,
                "status": "resolved" if is_resolved else "pending"
            }
        
        # Calculate overall progress
        total = len(fix_ids)
        resolved_count = sum(1 for r in results.values() if r["resolved"])
        
        return {
            "results": results,
            "summary": {
                "total": total,
                "resolved": resolved_count,
                "pending": total - resolved_count,
                "progress_percent": int((resolved_count / total) * 100) if total > 0 else 0
            },
            "new_compliance_score": scan_result.get("compliance_score", 0)
        }

