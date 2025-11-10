"""
Complyo Data Validator
Validates scan completeness and triggers intelligent re-scans with specific parameters
"""

from typing import Dict, List, Any
import re


class DataValidator:
    """
    Validates if scan results contain all necessary data for intelligent fix generation
    """
    
    def validate_scan_completeness(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks if scan result is complete and identifies missing data
        
        Returns:
            {
                "complete": bool,
                "missing": List[dict] with missing fields and rescan parameters
            }
        """
        missing_data = []
        
        # Get website_data from scan
        website_data = scan_result.get("website_data", {})
        seo_data = scan_result.get("seo_data", {})
        tech_stack = scan_result.get("tech_stack", {})
        issues = scan_result.get("issues", [])
        
        # 1. Check Company Data (critical for legal texts)
        if not website_data.get("company_name"):
            # Check if we have legal issues that need company data
            has_legal_issues = any(
                issue.get("category", "").lower() in ["impressum", "datenschutz", "rechtssichere texte", "legal"]
                for issue in issues
            )
            
            if has_legal_issues or not website_data.get("has_impressum"):
                missing_data.append({
                    "field": "company_name",
                    "reason": "Firmenname nicht gefunden - nötig für rechtssichere Texte",
                    "priority": "high",
                    "rescan_with": {
                        "deep_impressum_scan": True,
                        "footer_analysis": True,
                        "extended_text_extraction": True
                    }
                })
        
        # 2. Check Contact Data
        if not website_data.get("email") and not website_data.get("phone"):
            missing_data.append({
                "field": "contact_data",
                "reason": "Keine Kontaktdaten gefunden - nötig für Impressum",
                "priority": "medium",
                "rescan_with": {
                    "contact_page_scan": True,
                    "footer_analysis": True
                }
            })
        
        # 3. Check Shop System (if commerce indicators exist)
        if self._has_shop_indicators(scan_result) and not website_data.get("shop_system"):
            missing_data.append({
                "field": "shop_system",
                "reason": "E-Commerce erkannt aber Shop-System unbekannt",
                "priority": "medium",
                "rescan_with": {
                    "deep_shop_detection": True,
                    "technology_analysis": True
                }
            })
        
        # 4. Check SEO/Meta Data (if missing and accessibility issues exist)
        if not seo_data.get("title") or not seo_data.get("description"):
            has_seo_issues = any(
                "seo" in issue.get("title", "").lower() or "meta" in issue.get("title", "").lower()
                for issue in issues
            )
            
            if has_seo_issues:
                missing_data.append({
                    "field": "seo_metadata",
                    "reason": "SEO Meta-Daten fehlen",
                    "priority": "low",
                    "rescan_with": {
                        "meta_tag_analysis": True
                    }
                })
        
        # 5. Check Technology Stack (if empty)
        if not tech_stack.get("cms") and not tech_stack.get("frameworks"):
            missing_data.append({
                "field": "tech_stack",
                "reason": "Technologie-Stack nicht erkannt - erschwert Fix-Generierung",
                "priority": "low",
                "rescan_with": {
                    "deep_technology_detection": True,
                    "html_pattern_analysis": True
                }
            })
        
        # 6. Check if Datenschutz page exists but not analyzed
        if not website_data.get("has_datenschutz"):
            has_dsgvo_issues = any(
                "dsgvo" in issue.get("category", "").lower() or 
                "datenschutz" in issue.get("title", "").lower()
                for issue in issues
            )
            
            if has_dsgvo_issues:
                missing_data.append({
                    "field": "datenschutz_page",
                    "reason": "Datenschutzerklärung nicht gefunden",
                    "priority": "high",
                    "rescan_with": {
                        "datenschutz_page_scan": True,
                        "privacy_link_detection": True
                    }
                })
        
        return {
            "complete": len(missing_data) == 0,
            "missing": missing_data,
            "missing_count": len(missing_data),
            "critical_count": sum(1 for item in missing_data if item["priority"] == "high")
        }
    
    def _has_shop_indicators(self, scan_result: Dict[str, Any]) -> bool:
        """
        Check if scan result indicates e-commerce functionality
        """
        # Check issues for shop-related problems
        issues = scan_result.get("issues", [])
        shop_keywords = ["warenkorb", "cart", "checkout", "bestell", "kauf", "shop", "produkt"]
        
        for issue in issues:
            title = issue.get("title", "").lower()
            desc = issue.get("description", "").lower()
            
            if any(keyword in title or keyword in desc for keyword in shop_keywords):
                return True
        
        # Check tech stack
        tech_stack = scan_result.get("tech_stack", {})
        if tech_stack.get("cms"):
            shop_cms = ["woocommerce", "shopify", "magento", "prestashop", "shopware"]
            if any(cms.lower() in str(tech_stack["cms"]).lower() for cms in shop_cms):
                return True
        
        return False
    
    def should_trigger_rescan(self, validation_result: Dict[str, Any]) -> bool:
        """
        Determines if a re-scan should be triggered based on validation result
        """
        # Only re-scan if:
        # 1. Not complete
        # 2. Has critical missing data
        # 3. Missing count is reasonable (< 4)
        
        if validation_result["complete"]:
            return False
        
        if validation_result["critical_count"] > 0:
            return True
        
        if validation_result["missing_count"] <= 3:
            return True
        
        return False
    
    def get_rescan_parameters(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate rescan parameters from missing data
        """
        rescan_params = {}
        
        for missing_item in validation_result.get("missing", []):
            rescan_with = missing_item.get("rescan_with", {})
            rescan_params.update(rescan_with)
        
        return rescan_params
    
    def generate_user_feedback(self, validation_result: Dict[str, Any]) -> str:
        """
        Generate user-friendly message about missing data
        """
        if validation_result["complete"]:
            return "✅ Alle Daten vollständig erfasst"
        
        missing = validation_result.get("missing", [])
        
        # Group by priority
        critical = [m for m in missing if m["priority"] == "high"]
        medium = [m for m in missing if m["priority"] == "medium"]
        low = [m for m in missing if m["priority"] == "low"]
        
        messages = []
        
        if critical:
            messages.append(f"⚠️ {len(critical)} wichtige Daten fehlen:")
            for item in critical:
                messages.append(f"  - {item['reason']}")
        
        if medium:
            messages.append(f"ℹ️ {len(medium)} zusätzliche Daten empfohlen:")
            for item in medium:
                messages.append(f"  - {item['reason']}")
        
        if low:
            messages.append(f"💡 {len(low)} optionale Verbesserungen möglich")
        
        if self.should_trigger_rescan(validation_result):
            messages.append("\n🔄 Complyo führt automatisch eine erweiterte Analyse durch...")
        
        return "\n".join(messages)

