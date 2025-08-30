"""
Complyo Hybrid AI Assistant - Smart Automation with User Control
KI analysiert + generiert + previewed, User bestätigt, KI implementiert
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
import json
import uuid
import hashlib
from enum import Enum
import tempfile
import os
import shutil

logger = logging.getLogger(__name__)

class FixType(Enum):
    SAFE_OVERLAY = "safe_overlay"          # JavaScript/CSS Overlays - 100% safe
    CSS_ADDITION = "css_addition"          # CSS hinzufügen - reversible
    HTML_MODIFICATION = "html_modification" # HTML ändern - needs backup
    CONTENT_UPDATE = "content_update"      # Text ändern - needs approval
    SCRIPT_INJECTION = "script_injection"  # JavaScript hinzufügen - monitored

class RiskLevel(Enum):
    ZERO_RISK = "zero_risk"        # Keine Website-Änderung
    LOW_RISK = "low_risk"         # Nur Ergänzungen
    MEDIUM_RISK = "medium_risk"   # Änderungen mit Backup  
    HIGH_RISK = "high_risk"       # Strukturelle Änderungen

@dataclass
class FixPreview:
    """Preview einer geplanten Compliance-Fix"""
    fix_id: str
    issue_id: str
    fix_type: FixType
    risk_level: RiskLevel
    title: str
    description: str
    before_code: str
    after_code: str
    files_affected: List[str]
    backup_created: bool
    estimated_time: int
    rollback_possible: bool
    preview_url: Optional[str] = None
    safety_score: float = 0.0

@dataclass
class ImplementationPlan:
    """Vollständiger Implementation Plan für Website"""
    plan_id: str
    website_url: str
    total_fixes: int
    safe_fixes: List[FixPreview]
    risky_fixes: List[FixPreview] 
    estimated_total_time: int
    compliance_improvement: float
    safety_analysis: Dict[str, Any]
    preview_environment: Optional[str] = None

class HybridAIAssistant:
    """
    Hybrid AI Assistant für sichere Compliance-Automatisierung
    
    Workflow:
    1. 🤖 KI analysiert Website (automatisch)
    2. 🎯 KI generiert Fix-Plan (automatisch)  
    3. 🎭 KI erstellt Preview/Sandbox (automatisch)
    4. 👤 User reviewed und bestätigt (manuell)
    5. 🚀 KI implementiert bestätigte Fixes (automatisch)
    6. 📊 Kontinuierliches Monitoring (automatisch)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Safety thresholds
        self.safety_thresholds = {
            "max_files_per_fix": 5,
            "max_css_changes": 10,
            "max_html_modifications": 3,
            "backup_required_above": RiskLevel.LOW_RISK
        }
        
        # Fix templates für verschiedene Compliance-Probleme
        self.fix_templates = {
            "missing_alt_texts": {
                "type": FixType.SAFE_OVERLAY,
                "risk": RiskLevel.ZERO_RISK,
                "method": "javascript_overlay",
                "rollback": True,
                "safety_score": 1.0
            },
            "missing_cookie_consent": {
                "type": FixType.SCRIPT_INJECTION, 
                "risk": RiskLevel.LOW_RISK,
                "method": "script_injection",
                "rollback": True,
                "safety_score": 0.9
            },
            "missing_skip_links": {
                "type": FixType.HTML_MODIFICATION,
                "risk": RiskLevel.MEDIUM_RISK,
                "method": "html_addition",
                "rollback": True,
                "safety_score": 0.8
            },
            "poor_color_contrast": {
                "type": FixType.CSS_ADDITION,
                "risk": RiskLevel.LOW_RISK, 
                "method": "css_override",
                "rollback": True,
                "safety_score": 0.85
            },
            "missing_privacy_policy": {
                "type": FixType.CONTENT_UPDATE,
                "risk": RiskLevel.HIGH_RISK,
                "method": "page_creation",
                "rollback": False,
                "safety_score": 0.6
            }
        }

    async def analyze_and_create_plan(self, website_url: str, user_preferences: Dict[str, Any]) -> ImplementationPlan:
        """
        Schritt 1-3: Analysiert Website und erstellt vollständigen Implementation Plan
        """
        try:
            self.logger.info(f"🤖 Starting hybrid analysis for {website_url}")
            
            # 1. Website Analysis (from existing AI engine)
            from ai_compliance_engine import ai_compliance_engine, UserExpertiseLevel
            user_level = UserExpertiseLevel(user_preferences.get("expertise", "beginner"))
            
            analysis_result = await ai_compliance_engine.analyze_website_with_ai(website_url, user_level)
            detected_issues = analysis_result["detected_issues"]
            
            # 2. Generate Fix Previews
            fix_previews = []
            for issue in detected_issues:
                preview = await self._generate_fix_preview(issue, website_url)
                if preview:
                    fix_previews.append(preview)
            
            # 3. Categorize by Risk Level
            safe_fixes = [f for f in fix_previews if f.risk_level in [RiskLevel.ZERO_RISK, RiskLevel.LOW_RISK]]
            risky_fixes = [f for f in fix_previews if f.risk_level in [RiskLevel.MEDIUM_RISK, RiskLevel.HIGH_RISK]]
            
            # 4. Safety Analysis
            safety_analysis = await self._perform_safety_analysis(website_url, fix_previews)
            
            # 5. Create Preview Environment
            preview_environment = await self._create_preview_environment(website_url, safe_fixes)
            
            # 6. Calculate Impact
            total_improvement = sum(self._calculate_fix_impact(f) for f in fix_previews)
            
            plan = ImplementationPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:8]}",
                website_url=website_url,
                total_fixes=len(fix_previews),
                safe_fixes=safe_fixes,
                risky_fixes=risky_fixes,
                estimated_total_time=sum(f.estimated_time for f in fix_previews),
                compliance_improvement=min(total_improvement, 100.0),
                safety_analysis=safety_analysis,
                preview_environment=preview_environment
            )
            
            self.logger.info(f"✅ Created implementation plan: {len(safe_fixes)} safe fixes, {len(risky_fixes)} risky fixes")
            return plan
            
        except Exception as e:
            self.logger.error(f"Error creating implementation plan: {e}")
            raise

    async def _generate_fix_preview(self, issue: Dict[str, Any], website_url: str) -> Optional[FixPreview]:
        """Generiert Preview für einzelnen Compliance-Fix"""
        
        try:
            issue_type = issue.get("id", "unknown")
            template = self.fix_templates.get(issue_type)
            
            if not template:
                self.logger.warning(f"No template found for issue: {issue_type}")
                return None
            
            # Generate before/after code
            before_code, after_code = await self._generate_code_diff(issue, template)
            
            # Determine affected files
            files_affected = await self._analyze_affected_files(issue, template)
            
            preview = FixPreview(
                fix_id=f"fix_{uuid.uuid4().hex[:8]}",
                issue_id=issue_type,
                fix_type=template["type"],
                risk_level=template["risk"],
                title=issue.get("title", "Compliance Fix"),
                description=await self._generate_fix_description(issue, template),
                before_code=before_code,
                after_code=after_code,
                files_affected=files_affected,
                backup_created=template["risk"] != RiskLevel.ZERO_RISK,
                estimated_time=issue.get("estimated_time", 15),
                rollback_possible=template["rollback"],
                safety_score=template["safety_score"]
            )
            
            return preview
            
        except Exception as e:
            self.logger.error(f"Error generating fix preview for {issue_type}: {e}")
            return None

    async def _generate_code_diff(self, issue: Dict[str, Any], template: Dict[str, Any]) -> Tuple[str, str]:
        """Generiert Before/After Code für Preview"""
        
        issue_type = issue.get("id", "")
        
        if issue_type == "missing_alt_texts":
            before = '<img src="image.jpg">'
            after = '<img src="image.jpg" alt="Beschreibung des Bildes">'
            
        elif issue_type == "missing_cookie_consent":
            before = '<head>\n  <title>Website</title>\n</head>'
            after = '''<head>
  <title>Website</title>
  <script src="complyo-cookie-consent.js"></script>
</head>'''
            
        elif issue_type == "missing_skip_links":
            before = '<body>\n  <nav>...</nav>\n  <main>...</main>'
            after = '''<body>
  <a href="#main-content" class="skip-link">Zum Hauptinhalt</a>
  <nav>...</nav>
  <main id="main-content">...</main>'''
            
        elif issue_type == "poor_color_contrast":
            before = '.button { color: #999; background: #ccc; }'
            after = '.button { color: #000; background: #fff; /* WCAG AA compliant */ }'
            
        elif issue_type == "missing_privacy_policy":
            before = '<!-- Keine Datenschutzerklärung vorhanden -->'
            after = '''<footer>
  <a href="/datenschutz">Datenschutz</a>
</footer>

<!-- Neue Datenschutz-Seite wird erstellt -->'''
            
        else:
            before = "<!-- Originaler Code -->"
            after = "<!-- Verbesserter Code -->"
        
        return before, after

    async def _generate_fix_description(self, issue: Dict[str, Any], template: Dict[str, Any]) -> str:
        """Generiert verständliche Beschreibung für Fix"""
        
        risk_descriptions = {
            RiskLevel.ZERO_RISK: "🟢 Vollkommen sicher - nur JavaScript-Overlay, keine Website-Änderung",
            RiskLevel.LOW_RISK: "🟡 Sehr sicher - nur Ergänzungen, vollständig rückgängig machbar",
            RiskLevel.MEDIUM_RISK: "🟠 Sichere Änderung - mit automatischem Backup, einfach rückgängig machbar", 
            RiskLevel.HIGH_RISK: "🔴 Strukturelle Änderung - Backup empfohlen, manuelle Prüfung erforderlich"
        }
        
        method_descriptions = {
            "javascript_overlay": "Fügt unsichtbare JavaScript-Verbesserungen hinzu",
            "script_injection": "Ergänzt optimierte JavaScript-Bibliotheken",
            "html_addition": "Fügt barrierefreie HTML-Elemente hinzu",
            "css_override": "Verbessert Farben und Layout für bessere Lesbarkeit", 
            "page_creation": "Erstellt neue rechtssichere Seiten"
        }
        
        fix_type = template.get("type", FixType.SAFE_OVERLAY)
        risk_level = template.get("risk", RiskLevel.ZERO_RISK)
        method = template.get("method", "unknown")
        
        description = f"""
{risk_descriptions.get(risk_level, "")}

**Was wird gemacht:**
{method_descriptions.get(method, "Compliance-Optimierung")}

**Betroffene Bereiche:**
{issue.get('description', 'Website-Verbesserung')}

**Sicherheit:**
- Automatisches Backup: {'✅ Ja' if template.get('rollback') else '❌ Nein'}  
- Rückgängig machbar: {'✅ Ja' if template.get('rollback') else '⚠️ Schwierig'}
- Risiko-Score: {template.get('safety_score', 0.5) * 100:.0f}%
        """
        
        return description.strip()

    async def _analyze_affected_files(self, issue: Dict[str, Any], template: Dict[str, Any]) -> List[str]:
        """Analysiert welche Dateien von Fix betroffen sind"""
        
        issue_type = issue.get("id", "")
        fix_type = template.get("type")
        
        if fix_type == FixType.SAFE_OVERLAY:
            return []  # Keine Dateien geändert
            
        elif fix_type == FixType.SCRIPT_INJECTION:
            return ["index.html", "complyo-additions.js"]
            
        elif fix_type == FixType.CSS_ADDITION:
            return ["styles.css", "complyo-accessibility.css"]
            
        elif fix_type == FixType.HTML_MODIFICATION:
            return ["index.html", "template.html"]
            
        elif fix_type == FixType.CONTENT_UPDATE:
            if issue_type == "missing_privacy_policy":
                return ["datenschutz.html", "footer.html"]
            return ["content.html"]
        
        return ["unknown.html"]

    async def _perform_safety_analysis(self, website_url: str, fixes: List[FixPreview]) -> Dict[str, Any]:
        """Führt umfassende Sicherheitsanalyse durch"""
        
        # Risk distribution
        risk_counts = {level.value: 0 for level in RiskLevel}
        for fix in fixes:
            risk_counts[fix.risk_level.value] += 1
        
        # File impact analysis
        all_affected_files = set()
        for fix in fixes:
            all_affected_files.update(fix.files_affected)
        
        # Calculate overall safety score
        if fixes:
            avg_safety = sum(fix.safety_score for fix in fixes) / len(fixes)
        else:
            avg_safety = 1.0
        
        # Recommendations
        recommendations = []
        
        if risk_counts["high_risk"] > 0:
            recommendations.append("⚠️ Manuelle Prüfung für High-Risk Änderungen empfohlen")
            
        if len(all_affected_files) > 10:
            recommendations.append("📄 Viele Dateien betroffen - schrittweise Implementation empfohlen")
            
        if avg_safety < 0.7:
            recommendations.append("🔒 Backup der kompletten Website vor Implementation erstellen")
        
        return {
            "overall_safety_score": avg_safety,
            "risk_distribution": risk_counts,
            "total_files_affected": len(all_affected_files),
            "affected_files": list(all_affected_files),
            "recommendations": recommendations,
            "backup_recommended": avg_safety < 0.8 or risk_counts["high_risk"] > 0,
            "estimated_downtime": self._estimate_downtime(fixes)
        }

    def _estimate_downtime(self, fixes: List[FixPreview]) -> str:
        """Schätzt potentielle Downtime"""
        
        high_risk_fixes = [f for f in fixes if f.risk_level == RiskLevel.HIGH_RISK]
        
        if not high_risk_fixes:
            return "Keine - Zero-Downtime Deployment"
        elif len(high_risk_fixes) <= 2:
            return "< 5 Minuten - Minimale Unterbrechung"
        else:
            return "5-15 Minuten - Backup-Window empfohlen"

    async def _create_preview_environment(self, website_url: str, safe_fixes: List[FixPreview]) -> Optional[str]:
        """Erstellt Sandbox/Preview-Environment für sichere Fixes"""
        
        try:
            # In production: Create actual preview environment
            # For demo: Return simulated preview URL
            
            preview_id = f"preview_{uuid.uuid4().hex[:8]}"
            
            # Simulate creating preview with safe fixes applied
            preview_url = f"https://preview-{preview_id}.complyo.dev"
            
            self.logger.info(f"Created preview environment: {preview_url}")
            
            return preview_url
            
        except Exception as e:
            self.logger.error(f"Error creating preview environment: {e}")
            return None

    def _calculate_fix_impact(self, fix: FixPreview) -> float:
        """Kalkuliert Impact eines Fixes auf Compliance Score"""
        
        impact_weights = {
            "missing_alt_texts": 15.0,
            "missing_cookie_consent": 25.0,
            "missing_skip_links": 10.0, 
            "poor_color_contrast": 20.0,
            "missing_privacy_policy": 30.0
        }
        
        return impact_weights.get(fix.issue_id, 5.0)

    async def implement_approved_fixes(self, plan_id: str, approved_fix_ids: List[str], user_id: str) -> Dict[str, Any]:
        """
        Schritt 5: Implementiert von User bestätigte Fixes
        """
        try:
            self.logger.info(f"🚀 Implementing {len(approved_fix_ids)} approved fixes for plan {plan_id}")
            
            # Get implementation plan
            plan = await self._get_implementation_plan(plan_id)
            if not plan:
                raise ValueError(f"Implementation plan {plan_id} not found")
            
            # Filter approved fixes
            approved_fixes = [f for f in (plan.safe_fixes + plan.risky_fixes) if f.fix_id in approved_fix_ids]
            
            implementation_results = []
            
            for fix in approved_fixes:
                try:
                    # Create backup if needed
                    backup_info = None
                    if fix.backup_created:
                        backup_info = await self._create_backup(fix)
                    
                    # Implement fix
                    result = await self._implement_single_fix(fix, plan.website_url)
                    
                    # Verify implementation
                    verification = await self._verify_fix_implementation(fix, plan.website_url)
                    
                    implementation_results.append({
                        "fix_id": fix.fix_id,
                        "status": "success" if result else "failed",
                        "backup_created": backup_info,
                        "verification": verification,
                        "implemented_at": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error implementing fix {fix.fix_id}: {e}")
                    implementation_results.append({
                        "fix_id": fix.fix_id,
                        "status": "error",
                        "error": str(e),
                        "attempted_at": datetime.now().isoformat()
                    })
            
            # Update progress tracking
            await self._update_implementation_progress(user_id, plan_id, implementation_results)
            
            # Start monitoring
            await self._start_post_implementation_monitoring(plan.website_url, approved_fixes)
            
            success_count = len([r for r in implementation_results if r["status"] == "success"])
            
            return {
                "plan_id": plan_id,
                "total_fixes_attempted": len(approved_fixes),
                "successful_implementations": success_count,
                "implementation_results": implementation_results,
                "compliance_improvement": self._calculate_actual_improvement(implementation_results),
                "next_steps": await self._generate_next_steps(plan, implementation_results),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in implementation process: {e}")
            raise

    async def _implement_single_fix(self, fix: FixPreview, website_url: str) -> bool:
        """Implementiert einzelnen Fix"""
        
        try:
            if fix.fix_type == FixType.SAFE_OVERLAY:
                return await self._implement_javascript_overlay(fix, website_url)
                
            elif fix.fix_type == FixType.SCRIPT_INJECTION:
                return await self._implement_script_injection(fix, website_url)
                
            elif fix.fix_type == FixType.CSS_ADDITION:
                return await self._implement_css_addition(fix, website_url)
                
            elif fix.fix_type == FixType.HTML_MODIFICATION:
                return await self._implement_html_modification(fix, website_url)
                
            elif fix.fix_type == FixType.CONTENT_UPDATE:
                return await self._implement_content_update(fix, website_url)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error implementing fix {fix.fix_id}: {e}")
            return False

    async def _implement_javascript_overlay(self, fix: FixPreview, website_url: str) -> bool:
        """Implementiert JavaScript Overlay Fix"""
        
        # Generate JavaScript code for fix
        if fix.issue_id == "missing_alt_texts":
            js_code = """
// Complyo Auto Alt-Text Enhancement
(function() {
    'use strict';
    
    // Find images without alt text
    const images = document.querySelectorAll('img:not([alt])');
    
    images.forEach(img => {
        // Generate descriptive alt text based on src or context
        const filename = img.src.split('/').pop().split('.')[0];
        const altText = filename.replace(/[-_]/g, ' ') || 'Bild';
        img.setAttribute('alt', altText);
        
        // Mark as auto-enhanced
        img.setAttribute('data-complyo-enhanced', 'true');
    });
    
    console.log(`Complyo: Enhanced ${images.length} images with alt text`);
})();
            """
            
            # In production: Inject this JavaScript into website
            # For demo: Simulate successful injection
            self.logger.info(f"Implemented JavaScript overlay for {fix.issue_id}")
            return True
            
        return False

    async def _implement_script_injection(self, fix: FixPreview, website_url: str) -> bool:
        """Implementiert Script Injection Fix"""
        
        if fix.issue_id == "missing_cookie_consent":
            # Generate cookie consent script
            script_content = """
<script src="https://cdn.complyo.de/cookie-consent-v2.js"></script>
<script>
  ComplyoCookieConsent.init({
    position: 'bottom',
    theme: 'light',
    categories: ['essential', 'analytics', 'marketing'],
    language: 'de',
    privacyPolicyUrl: '/datenschutz'
  });
</script>
            """
            
            # In production: Add to website head section  
            self.logger.info(f"Implemented script injection for {fix.issue_id}")
            return True
            
        return False

    async def _implement_css_addition(self, fix: FixPreview, website_url: str) -> bool:
        """Implementiert CSS Addition Fix"""
        
        if fix.issue_id == "poor_color_contrast":
            css_content = """
/* Complyo Accessibility Enhancements */
.complyo-high-contrast {
    color: #000000 !important;
    background-color: #ffffff !important;
    border: 1px solid #333333 !important;
}

/* Auto-enhance poor contrast elements */
button, .btn, .button {
    color: #000000 !important;  
    background-color: #ffffff !important;
    border: 2px solid #0066cc !important;
}

button:hover, .btn:hover, .button:hover {
    background-color: #0066cc !important;
    color: #ffffff !important;
}
            """
            
            # In production: Add CSS file or inject into existing CSS
            self.logger.info(f"Implemented CSS addition for {fix.issue_id}")
            return True
            
        return False

    async def _implement_html_modification(self, fix: FixPreview, website_url: str) -> bool:
        """Implementiert HTML Modification Fix"""
        
        if fix.issue_id == "missing_skip_links":
            # In production: Modify HTML to add skip links
            self.logger.info(f"Implemented HTML modification for {fix.issue_id}")
            return True
            
        return False

    async def _implement_content_update(self, fix: FixPreview, website_url: str) -> bool:
        """Implementiert Content Update Fix"""
        
        if fix.issue_id == "missing_privacy_policy":
            # In production: Create privacy policy page
            self.logger.info(f"Implemented content update for {fix.issue_id}")
            return True
            
        return False

    async def rollback_implementation(self, plan_id: str, fix_ids: List[str]) -> Dict[str, Any]:
        """Macht Implementation rückgängig"""
        
        try:
            rollback_results = []
            
            for fix_id in fix_ids:
                # Get backup info
                backup_info = await self._get_backup_info(fix_id)
                
                if backup_info:
                    # Restore from backup
                    success = await self._restore_from_backup(backup_info)
                    rollback_results.append({
                        "fix_id": fix_id,
                        "status": "success" if success else "failed", 
                        "restored_at": datetime.now().isoformat()
                    })
                else:
                    rollback_results.append({
                        "fix_id": fix_id,
                        "status": "no_backup",
                        "message": "No backup available for rollback"
                    })
            
            return {
                "plan_id": plan_id,
                "rollback_results": rollback_results,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")
            raise

    # Helper methods (simplified for demo)
    async def _get_implementation_plan(self, plan_id: str) -> Optional[ImplementationPlan]:
        # In production: Load from database
        return None
        
    async def _create_backup(self, fix: FixPreview) -> Dict[str, Any]:
        # In production: Create actual backup
        return {"backup_id": f"backup_{uuid.uuid4().hex[:8]}", "created_at": datetime.now()}
        
    async def _verify_fix_implementation(self, fix: FixPreview, website_url: str) -> Dict[str, Any]:
        # In production: Verify fix is working
        return {"verified": True, "score_improvement": 5.0}
        
    async def _update_implementation_progress(self, user_id: str, plan_id: str, results: List[Dict]) -> None:
        # In production: Update database
        pass
        
    async def _start_post_implementation_monitoring(self, website_url: str, fixes: List[FixPreview]) -> None:
        # In production: Start monitoring
        pass
        
    def _calculate_actual_improvement(self, results: List[Dict]) -> float:
        # Calculate actual compliance improvement
        return len([r for r in results if r["status"] == "success"]) * 5.0
        
    async def _generate_next_steps(self, plan: ImplementationPlan, results: List[Dict]) -> List[str]:
        return [
            "Monitor website for 24 hours",
            "Run compliance re-scan",
            "Review user feedback"
        ]

# Global Hybrid AI Assistant Instance
hybrid_ai_assistant = HybridAIAssistant()