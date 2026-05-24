"""
Enhanced Complyo Fixer - Integration Layer
Erweitert bestehende Fix-Engine um neue Features OHNE bestehende Strukturen zu überschreiben

Rechtstexte: interner KI-Generator hat Vorrang (knowledge/laws/ + Templates).
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedFixerIntegration:
    """
    Integration Layer für neue Features
    
    Prinzipien:
    1. ✅ Interner KI-Generator hat VORRANG bei Rechtstexten (Impressum, Datenschutz)
    2. ✅ Neue Module nur als Fallback/Enhancement
    3. ✅ Bestehende Strukturen werden NICHT überschrieben
    4. ✅ Optionale Features - können aktiviert/deaktiviert werden
    """
    
    def __init__(
        self,
        fix_generator=None,
        enable_preview: bool = True,
        enable_deployment: bool = False,
        enable_github: bool = False
    ):
        """
        Initialisiert Enhanced Fixer

        Args:
            fix_generator: Bestehender Fix Generator
            enable_preview: Preview-Engine aktivieren
            enable_deployment: Deployment-Engine aktivieren
            enable_github: GitHub-Integration aktivieren
        """
        self.fix_generator = fix_generator
        
        # Feature Flags
        self.enable_preview = enable_preview
        self.enable_deployment = enable_deployment
        self.enable_github = enable_github
        
        # Lazy-Load neue Module nur wenn aktiviert
        self.preview_engine = None
        self.deployment_engine = None
        self.github_integration = None
        self.aria_checker = None
        
        if enable_preview:
            self._init_preview_engine()
        
        if enable_deployment:
            self._init_deployment_engine()
        
        if enable_github:
            self._init_github_integration()
        
        logger.info(f"✅ Enhanced Fixer initialisiert (Preview: {enable_preview}, Deploy: {enable_deployment}, GitHub: {enable_github})")
    
    def _init_preview_engine(self):
        """Lazy-Load Preview Engine"""
        try:
            from compliance_engine.preview_engine import preview_engine
            self.preview_engine = preview_engine
            logger.info("✅ Preview Engine geladen")
        except Exception as e:
            logger.warning(f"⚠️ Preview Engine konnte nicht geladen werden: {e}")
    
    def _init_deployment_engine(self):
        """Lazy-Load Deployment Engine"""
        try:
            from compliance_engine.deployment_engine import deployment_engine
            self.deployment_engine = deployment_engine
            logger.info("✅ Deployment Engine geladen")
        except Exception as e:
            logger.warning(f"⚠️ Deployment Engine konnte nicht geladen werden: {e}")
    
    def _init_github_integration(self):
        """Lazy-Load GitHub Integration"""
        try:
            from compliance_engine.github_integration import github_integration
            self.github_integration = github_integration
            logger.info("✅ GitHub Integration geladen")
        except Exception as e:
            logger.warning(f"⚠️ GitHub Integration konnte nicht geladen werden: {e}")
    
    def load_aria_checker(self):
        """Lazy-Load ARIA Checker (on demand)"""
        if self.aria_checker is None:
            try:
                from compliance_engine.checks.aria_checker import aria_checker
                self.aria_checker = aria_checker
                logger.info("✅ ARIA Checker geladen")
            except Exception as e:
                logger.warning(f"⚠️ ARIA Checker konnte nicht geladen werden: {e}")
        return self.aria_checker
    
    async def generate_fix_with_priority(
        self,
        issue_category: str,
        issue_data: Dict[str, Any],
        company_info: Dict[str, str] = None,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generiert Fix mit korrekter Priorität.

        Hierarchie für Rechtstexte:
        1. Interner KI-Generator (knowledge/laws/ + Templates) — Risiko-Reduktion
        2. Bestehender Fix Generator (Fallback)
        3. Basis-Fallback (Notfall)
        """
        logger.info(f"Generiere Fix für Kategorie: {issue_category}")

        fix_result = {
            'category': issue_category,
            'source': None,
            'content': None,
            'metadata': {},
            'priority_used': None,
            'timestamp': datetime.now().isoformat()
        }

        if issue_category.lower() in ['impressum', 'datenschutz', 'datenschutzerklärung']:

            if self.fix_generator:
                try:
                    logger.info(f"Interner Generator für {issue_category}")
                    existing_fix = await self.fix_generator.generate_fix(
                        category=issue_category,
                        issue_data=issue_data,
                        company_info=company_info
                    )
                    if existing_fix:
                        fix_result['source'] = 'Complyo Internal Generator'
                        fix_result['content'] = existing_fix.get('content')
                        fix_result['priority_used'] = 1
                        fix_result['metadata'] = {
                            'risk_reduced': True,
                            'risk_note': 'KI-generierte Vorlage — juristische Prüfung empfohlen',
                            'provider': 'Complyo KI',
                        }
                        return fix_result
                except Exception as e:
                    logger.warning(f"Fix Generator Fehler: {e}")

            fix_result['source'] = 'KI-Fallback'
            fix_result['content'] = self._generate_basic_fallback(issue_category, company_info)
            fix_result['priority_used'] = 2
            fix_result['metadata'] = {
                'risk_reduced': False,
                'risk_note': 'Basis-Template — bitte vollständig ausfüllen und juristisch prüfen lassen',
                'provider': 'Complyo AI Fallback',
            }
            return fix_result

        else:
            if self.fix_generator:
                try:
                    existing_fix = await self.fix_generator.generate_fix(
                        category=issue_category,
                        issue_data=issue_data,
                        company_info=company_info
                    )
                    if existing_fix:
                        fix_result['source'] = 'Complyo Fix Generator'
                        fix_result['content'] = existing_fix.get('content')
                        fix_result['priority_used'] = 1
                        return fix_result
                except Exception as e:
                    logger.warning(f"Fix Generator Fehler: {e}")

            fix_result['source'] = 'Basic Fallback'
            fix_result['content'] = self._generate_basic_fallback(issue_category, company_info)
            fix_result['priority_used'] = 2
            return fix_result
    
    def _generate_basic_fallback(self, category: str, company_info: Dict = None) -> str:
        """Einfacher Fallback wenn alles andere fehlschlägt"""
        return (
            f"<!-- Complyo Fallback: {category} -->\n"
            "<p><strong>Hinweis:</strong> Dies ist ein Basis-Template.</p>\n"
            "<p>Bitte vollständig ausfüllen. KI-Generierung unter Einstellungen &gt; Rechtstexte.</p>\n"
            f"<!-- TODO: Ergänzen Sie hier Ihre {category}-Daten -->\n"
        )
    
    async def create_preview(
        self,
        original_content: str,
        fix_content: str,
        fix_type: str,
        fix_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Erstellt Preview (nur wenn aktiviert)
        
        Returns:
            Preview-Daten oder None wenn deaktiviert
        """
        if not self.enable_preview or not self.preview_engine:
            logger.info("⚠️ Preview Engine nicht aktiviert")
            return None
        
        try:
            preview_result = await self.preview_engine.generate_preview(
                original_content=original_content,
                fix_content=fix_content,
                fix_type=fix_type,
                fix_id=fix_id
            )
            
            return {
                'preview_id': preview_result.preview_id,
                'preview_url': preview_result.preview_url,
                'changes_summary': preview_result.changes_summary
            }
            
        except Exception as e:
            logger.error(f"❌ Preview-Generierung fehlgeschlagen: {e}")
            return None
    
    async def deploy_fix(
        self,
        deployment_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Deployed Fix (nur wenn aktiviert)
        
        Returns:
            Deployment-Result oder None wenn deaktiviert
        """
        if not self.enable_deployment or not self.deployment_engine:
            logger.info("⚠️ Deployment Engine nicht aktiviert")
            return None
        
        try:
            from compliance_engine.deployment_engine import DeploymentConfig
            
            config = DeploymentConfig(**deployment_config)
            result = await self.deployment_engine.deploy(config)
            
            return {
                'success': result.success,
                'deployment_id': result.deployment_id,
                'files_deployed': result.files_deployed,
                'error': result.error
            }
            
        except Exception as e:
            logger.error(f"❌ Deployment fehlgeschlagen: {e}")
            return None
    
    async def create_github_pr(
        self,
        repository: str,
        github_token: str,
        fix_id: str,
        fix_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Erstellt GitHub PR (nur wenn aktiviert)
        
        Returns:
            PR-Daten oder None wenn deaktiviert
        """
        if not self.enable_github or not self.github_integration:
            logger.info("⚠️ GitHub Integration nicht aktiviert")
            return None
        
        try:
            result = await self.github_integration.create_pr_for_fix(
                repository=repository,
                github_token=github_token,
                fix_id=fix_id,
                fix_data=fix_data
            )
            
            return {
                'success': result.success,
                'pr_url': result.pr_url,
                'pr_number': result.pr_number,
                'branch_name': result.branch_name
            }
            
        except Exception as e:
            logger.error(f"❌ GitHub PR-Erstellung fehlgeschlagen: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Gibt Status der Integration zurück
        
        Returns:
            Status-Dict mit allen Feature-Flags
        """
        return {
            'enhanced_fixer_active': True,
            'features': {
                'preview': {
                    'enabled': self.enable_preview,
                    'loaded': self.preview_engine is not None
                },
                'deployment': {
                    'enabled': self.enable_deployment,
                    'loaded': self.deployment_engine is not None
                },
                'github': {
                    'enabled': self.enable_github,
                    'loaded': self.github_integration is not None
                },
                'aria_checker': {
                    'loaded': self.aria_checker is not None
                }
            },
            'priority_system': {
                'rechtstexte': {
                    '1_priority': 'Complyo Internal Generator (knowledge/laws/)',
                    '2_fallback': 'Complyo Templates',
                    '3_emergency': 'KI-Fallback'
                },
                'other_categories': {
                    '1_priority': 'Complyo Fix Generator',
                    '2_fallback': 'Basic Fallback'
                }
            },
            'integrations': {
                'fix_generator': self.fix_generator is not None
            }
        }


# Global instance (wird in main_production.py initialisiert)
enhanced_fixer = None


def initialize_enhanced_fixer(
    fix_generator=None,
    enable_preview: bool = True,
    enable_deployment: bool = False,
    enable_github: bool = False
):
    """Initialisiert Enhanced Fixer (ohne eRecht24-Abhängigkeit)."""
    global enhanced_fixer
    enhanced_fixer = EnhancedFixerIntegration(
        fix_generator=fix_generator,
        enable_preview=enable_preview,
        enable_deployment=enable_deployment,
        enable_github=enable_github
    )
    logger.info("Enhanced Fixer global initialisiert")
    return enhanced_fixer

