"""
BFSG Patch-Service
Generiert Unified Diffs für Barrierefreiheits-Fixes mittels LLM

Dieser Service ist Teil der anfängerfreundlichen Fix-Pipeline:
1. Empfängt strukturierte Issues von der Feature-Engine
2. Generiert Patches via LLM (OpenRouter)
3. Validiert und formatiert die Patches
4. Gibt strukturierte Fix-Objekte zurück
"""

import os
import re
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .feature_engine import (
    FeatureEngine, FeatureId, StructuredIssue, 
    AutoFixLevel, Difficulty, FixType, feature_engine
)
from .prompts.bfsg_prompts import (
    BFSGPromptBuilder, PromptTemplate, PromptContext,
    bfsg_prompt_builder
)

logger = logging.getLogger(__name__)


# =============================================================================
# Konfiguration
# =============================================================================

class AIModel(str, Enum):
    """Verfügbare AI-Modelle"""
    CLAUDE_SONNET = "anthropic/claude-sonnet-4-20250514"
    CLAUDE_HAIKU = "anthropic/claude-3-haiku"
    GPT4_TURBO = "openai/gpt-4-turbo-preview"
    GPT4O = "openai/gpt-4o"


# Model-Fallback-Kette (günstigere Modelle zuerst für einfache Tasks)
MODEL_FALLBACK_CHAIN = [
    AIModel.CLAUDE_SONNET.value,
    AIModel.GPT4O.value,
    AIModel.GPT4_TURBO.value,
]


# =============================================================================
# Datenstrukturen
# =============================================================================

@dataclass
class PatchResult:
    """Ergebnis einer Patch-Generierung"""
    success: bool
    feature_id: str
    file_path: str
    unified_diff: Optional[str]
    fix_type: FixType
    difficulty: Difficulty
    
    # Metadaten
    ai_model_used: str
    generation_time_ms: int
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    
    # Fehler
    error: Optional[str] = None
    
    # Zusätzliche Infos
    wcag_criteria: List[str] = field(default_factory=list)
    description: str = ""
    instructions: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "feature_id": self.feature_id,
            "file_path": self.file_path,
            "unified_diff": self.unified_diff,
            "fix_type": self.fix_type.value,
            "difficulty": self.difficulty.value,
            "ai_model_used": self.ai_model_used,
            "generation_time_ms": self.generation_time_ms,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "error": self.error,
            "wcag_criteria": self.wcag_criteria,
            "description": self.description,
            "instructions": self.instructions
        }


@dataclass
class FixPackage:
    """Komplettes Fix-Paket für eine Website"""
    site_url: str
    generated_at: str
    total_issues: int
    fixed_issues: int
    
    # Kategorisiert nach Fix-Typ
    widget_fixes: List[Dict[str, Any]]
    code_patches: List[PatchResult]
    manual_guides: List[Dict[str, Any]]
    
    # Zusammenfassung
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "site_url": self.site_url,
            "generated_at": self.generated_at,
            "total_issues": self.total_issues,
            "fixed_issues": self.fixed_issues,
            "widget_fixes": self.widget_fixes,
            "code_patches": [p.to_dict() for p in self.code_patches],
            "manual_guides": self.manual_guides,
            "summary": self.summary
        }


# =============================================================================
# AI API Client (Wiederverwendung aus unified_fix_engine)
# =============================================================================

class PatchAIClient:
    """Spezialisierter AI-Client für Patch-Generierung"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.timeout = 90.0  # Längerer Timeout für komplexe Patches
        
        # Pricing (USD per 1M tokens)
        self.pricing = {
            AIModel.CLAUDE_SONNET.value: {"input": 3.0, "output": 15.0},
            AIModel.CLAUDE_HAIKU.value: {"input": 0.25, "output": 1.25},
            AIModel.GPT4_TURBO.value: {"input": 10.0, "output": 30.0},
            AIModel.GPT4O.value: {"input": 5.0, "output": 15.0},
        }
    
    async def generate_patch(
        self,
        prompt: str,
        system_message: str,
        model: str = AIModel.CLAUDE_SONNET.value,
        temperature: float = 0.2,  # Niedrigere Temperatur für konsistente Patches
        max_tokens: int = 4000
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Generiert einen Patch via AI-API
        
        Args:
            prompt: Der vollständige Prompt
            system_message: System-Nachricht
            model: Zu verwendendes Model
            temperature: Kreativitäts-Parameter
            max_tokens: Maximale Token-Anzahl
            
        Returns:
            Tuple von (success, content, metadata)
        """
        if not self.api_key:
            return False, None, {"error": "OPENROUTER_API_KEY nicht konfiguriert"}
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://complyo.tech",
                        "X-Title": "Complyo BFSG Patch Service"
                    }
                    
                    data = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        response_time = int((time.time() - start_time) * 1000)
                        
                        if response.status == 200:
                            result = await response.json()
                            content = result["choices"][0]["message"]["content"]
                            
                            # Berechne Kosten
                            usage = result.get("usage", {})
                            input_tokens = usage.get("prompt_tokens", 0)
                            output_tokens = usage.get("completion_tokens", 0)
                            
                            pricing = self.pricing.get(model, {"input": 5.0, "output": 15.0})
                            cost = (input_tokens * pricing["input"] / 1_000_000 + 
                                   output_tokens * pricing["output"] / 1_000_000)
                            
                            return True, content, {
                                "model": model,
                                "tokens_used": input_tokens + output_tokens,
                                "cost_usd": cost,
                                "response_time_ms": response_time
                            }
                        
                        elif response.status == 429:
                            last_error = "Rate limit erreicht"
                            await asyncio.sleep(2 ** attempt)
                            continue
                        
                        else:
                            error_text = await response.text()
                            last_error = f"API Error {response.status}: {error_text[:200]}"
                            
                            if response.status >= 500:
                                await asyncio.sleep(1)
                                continue
                            break
            
            except asyncio.TimeoutError:
                last_error = "Timeout bei AI-API-Call"
                await asyncio.sleep(1)
                continue
            
            except Exception as e:
                last_error = f"Exception: {str(e)}"
                await asyncio.sleep(1)
                continue
        
        return False, None, {
            "error": last_error or "Unbekannter Fehler",
            "response_time_ms": int((time.time() - start_time) * 1000)
        }


# =============================================================================
# Patch-Parser
# =============================================================================

class PatchParser:
    """Parser für AI-generierte Patches"""
    
    @staticmethod
    def extract_unified_diff(response: str) -> Optional[str]:
        """
        Extrahiert Unified Diff aus AI-Response
        
        Args:
            response: Rohe AI-Response
            
        Returns:
            Bereinigter Unified Diff oder None
        """
        if not response:
            return None
        
        # Versuche <<<PATCH>>> Block zu finden
        patch_match = re.search(r'<<<PATCH\s*\n(.*?)\n>>>', response, re.DOTALL)
        if patch_match:
            return patch_match.group(1).strip()
        
        # Versuche ```diff Block zu finden
        diff_match = re.search(r'```(?:diff)?\s*\n(.*?)\n```', response, re.DOTALL)
        if diff_match:
            return diff_match.group(1).strip()
        
        # Versuche direkt Unified Diff zu finden
        if response.strip().startswith('---') or response.strip().startswith('diff --git'):
            return response.strip()
        
        # Suche nach --- a/ Pattern
        unified_match = re.search(r'(---\s+a/.*?(?:\n@@.*?)+)', response, re.DOTALL)
        if unified_match:
            return unified_match.group(1).strip()
        
        return None
    
    @staticmethod
    def validate_unified_diff(diff: str) -> Tuple[bool, str]:
        """
        Validiert einen Unified Diff
        
        Args:
            diff: Der zu validierende Diff
            
        Returns:
            Tuple von (is_valid, error_message)
        """
        if not diff:
            return False, "Diff ist leer"
        
        lines = diff.split('\n')
        
        # Prüfe auf --- und +++ Header
        has_minus_header = any(line.startswith('---') for line in lines)
        has_plus_header = any(line.startswith('+++') for line in lines)
        
        if not has_minus_header or not has_plus_header:
            return False, "Fehlender --- oder +++ Header"
        
        # Prüfe auf @@ Hunk-Header
        has_hunk = any(line.startswith('@@') for line in lines)
        if not has_hunk:
            return False, "Kein @@ Hunk-Header gefunden"
        
        # Prüfe auf tatsächliche Änderungen
        has_additions = any(line.startswith('+') and not line.startswith('+++') for line in lines)
        has_deletions = any(line.startswith('-') and not line.startswith('---') for line in lines)
        
        if not has_additions and not has_deletions:
            return False, "Keine Änderungen im Diff"
        
        return True, ""
    
    @staticmethod
    def extract_alt_text(response: str) -> Optional[str]:
        """Extrahiert generierten Alt-Text aus Response"""
        if not response:
            return None
        
        # Bereinige Response
        text = response.strip()
        
        # Entferne Anführungszeichen
        text = text.strip('"\'')
        
        # Prüfe auf DECORATIVE
        if text.upper() == 'DECORATIVE':
            return ""
        
        # Begrenze auf 125 Zeichen
        if len(text) > 125:
            text = text[:122] + "..."
        
        return text


# =============================================================================
# Hauptservice: PatchService
# =============================================================================

class PatchService:
    """
    Hauptservice für BFSG Patch-Generierung
    
    Orchestriert:
    1. Feature-Engine für Issue-Kategorisierung
    2. Prompt-Builder für LLM-Prompts
    3. AI-Client für Patch-Generierung
    4. Parser für Ergebnis-Validierung
    """
    
    def __init__(self):
        self.feature_engine = feature_engine
        self.prompt_builder = bfsg_prompt_builder
        self.ai_client = PatchAIClient()
        self.parser = PatchParser()
        
        logger.info("🔧 PatchService initialisiert")
    
    async def generate_fix_package(
        self,
        site_url: str,
        raw_issues: List[Dict[str, Any]],
        file_contents: Optional[Dict[str, str]] = None
    ) -> FixPackage:
        """
        Generiert ein komplettes Fix-Paket für eine Website
        
        Args:
            site_url: URL der Website
            raw_issues: Rohe Scanner-Issues
            file_contents: Optional - Datei-Inhalte für Code-Patches
            
        Returns:
            Vollständiges FixPackage
        """
        logger.info(f"📦 Generiere Fix-Paket für {site_url} mit {len(raw_issues)} Issues")
        
        # 1. Kategorisiere Issues
        structured_issues = self.feature_engine.categorize_issues(raw_issues)
        
        # 2. Gruppiere nach Fix-Typ
        widget_issues = []
        code_issues = []
        manual_issues = []
        
        for issue in structured_issues:
            if issue.recommended_fix_type == FixType.WIDGET:
                widget_issues.append(issue)
            elif issue.recommended_fix_type == FixType.CODE:
                code_issues.append(issue)
            else:
                manual_issues.append(issue)
        
        # 3. Generiere Widget-Fixes (einfach - nur Konfiguration)
        widget_fixes = self._generate_widget_fixes(widget_issues, site_url)
        
        # 4. Generiere Code-Patches (LLM-basiert)
        code_patches = []
        if file_contents and code_issues:
            code_patches = await self._generate_code_patches(code_issues, file_contents)
        
        # 5. Generiere manuelle Anleitungen
        manual_guides = self._generate_manual_guides(manual_issues)
        
        # 6. Erstelle Zusammenfassung
        summary = self.feature_engine.get_summary(structured_issues)
        
        return FixPackage(
            site_url=site_url,
            generated_at=datetime.now().isoformat(),
            total_issues=len(raw_issues),
            fixed_issues=len(widget_fixes) + len([p for p in code_patches if p.success]),
            widget_fixes=widget_fixes,
            code_patches=code_patches,
            manual_guides=manual_guides,
            summary=summary
        )
    
    async def generate_single_patch(
        self,
        issue: StructuredIssue,
        file_path: str,
        file_content: str
    ) -> PatchResult:
        """
        Generiert einen einzelnen Patch für ein Issue
        
        Args:
            issue: Strukturiertes Issue
            file_path: Pfad zur betroffenen Datei
            file_content: Inhalt der Datei
            
        Returns:
            PatchResult
        """
        start_time = time.time()
        
        # Ermittle Prompt-Template
        template_name = self.feature_engine.get_prompt_template_name(issue.feature_id)
        template = PromptTemplate(template_name) if template_name in [t.value for t in PromptTemplate] else PromptTemplate.GENERIC
        
        # Erstelle Kontext
        context = PromptContext(
            file_path=file_path,
            file_content=file_content,
            findings=[{
                "line": issue.metadata.get("line", "?"),
                "selector": issue.selector or "",
                "snippet": issue.element_html or "",
                "description": issue.description
            }]
        )
        
        # Baue Prompt
        prompt = self.prompt_builder.build_prompt(template, context)
        system_message = self.prompt_builder.get_system_message(for_code=True)
        
        # Generiere Patch via AI
        success, content, metadata = await self.ai_client.generate_patch(
            prompt=prompt,
            system_message=system_message
        )
        
        if not success:
            return PatchResult(
                success=False,
                feature_id=issue.feature_id.value,
                file_path=file_path,
                unified_diff=None,
                fix_type=FixType.CODE,
                difficulty=issue.difficulty,
                ai_model_used=metadata.get("model", "unknown"),
                generation_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=metadata.get("tokens_used"),
                cost_usd=metadata.get("cost_usd"),
                error=metadata.get("error"),
                wcag_criteria=issue.wcag_criteria
            )
        
        # Extrahiere und validiere Diff
        diff = self.parser.extract_unified_diff(content)
        is_valid, error = self.parser.validate_unified_diff(diff) if diff else (False, "Kein Diff extrahiert")
        
        return PatchResult(
            success=is_valid,
            feature_id=issue.feature_id.value,
            file_path=file_path,
            unified_diff=diff if is_valid else None,
            fix_type=FixType.CODE,
            difficulty=issue.difficulty,
            ai_model_used=metadata.get("model", "unknown"),
            generation_time_ms=int((time.time() - start_time) * 1000),
            tokens_used=metadata.get("tokens_used"),
            cost_usd=metadata.get("cost_usd"),
            error=None if is_valid else error,
            wcag_criteria=issue.wcag_criteria,
            description=issue.description,
            instructions=self._get_patch_instructions(issue)
        )
    
    async def generate_alt_text(
        self,
        image_src: str,
        page_context: str = "",
        surrounding_text: str = "",
        filename: str = ""
    ) -> Tuple[bool, str]:
        """
        Generiert einen Alt-Text für ein Bild
        
        Args:
            image_src: URL des Bildes
            page_context: Seiten-Kontext
            surrounding_text: Umgebender Text
            filename: Dateiname
            
        Returns:
            Tuple von (success, alt_text)
        """
        prompt = self.prompt_builder.build_alt_text_prompt(
            image_src=image_src,
            page_context=page_context,
            surrounding_text=surrounding_text,
            filename=filename or image_src.split('/')[-1]
        )
        
        success, content, _ = await self.ai_client.generate_patch(
            prompt=prompt,
            system_message="Du bist ein Experte für barrierefreie Alt-Texte.",
            temperature=0.3,
            max_tokens=200
        )
        
        if success:
            alt_text = self.parser.extract_alt_text(content)
            return True, alt_text or ""
        
        return False, ""
    
    def _generate_widget_fixes(
        self,
        issues: List[StructuredIssue],
        site_url: str
    ) -> List[Dict[str, Any]]:
        """Generiert Widget-basierte Fixes"""
        if not issues:
            return []
        
        # Gruppiere nach Feature
        by_feature = {}
        for issue in issues:
            if issue.feature_id not in by_feature:
                by_feature[issue.feature_id] = []
            by_feature[issue.feature_id].append(issue)
        
        fixes = []
        for feature_id, feature_issues in by_feature.items():
            fixes.append({
                "feature_id": feature_id.value,
                "issues_count": len(feature_issues),
                "fix_type": "widget",
                "difficulty": "easy",
                "integration_code": self._get_widget_code(site_url, feature_id),
                "description": f"{len(feature_issues)} Probleme werden automatisch behoben",
                "instructions": "Fügen Sie den Code vor </body> ein. Die Fixes werden sofort angewendet."
            })
        
        return fixes
    
    async def _generate_code_patches(
        self,
        issues: List[StructuredIssue],
        file_contents: Dict[str, str]
    ) -> List[PatchResult]:
        """Generiert Code-Patches für alle Issues"""
        patches = []
        
        # Gruppiere Issues nach Datei
        by_file: Dict[str, List[StructuredIssue]] = {}
        for issue in issues:
            # Versuche Datei zu ermitteln
            file_path = issue.metadata.get("file_path", "index.html")
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(issue)
        
        # Generiere Patches pro Datei
        for file_path, file_issues in by_file.items():
            file_content = file_contents.get(file_path, "")
            
            if not file_content:
                logger.warning(f"⚠️ Kein Inhalt für {file_path}")
                continue
            
            for issue in file_issues:
                try:
                    patch = await self.generate_single_patch(issue, file_path, file_content)
                    patches.append(patch)
                except Exception as e:
                    logger.error(f"❌ Fehler bei Patch-Generierung für {issue.id}: {e}")
                    patches.append(PatchResult(
                        success=False,
                        feature_id=issue.feature_id.value,
                        file_path=file_path,
                        unified_diff=None,
                        fix_type=FixType.CODE,
                        difficulty=issue.difficulty,
                        ai_model_used="none",
                        generation_time_ms=0,
                        tokens_used=None,
                        cost_usd=None,
                        error=str(e),
                        wcag_criteria=issue.wcag_criteria
                    ))
        
        return patches
    
    def _generate_manual_guides(
        self,
        issues: List[StructuredIssue]
    ) -> List[Dict[str, Any]]:
        """Generiert manuelle Anleitungen"""
        guides = []
        
        for issue in issues:
            guides.append({
                "feature_id": issue.feature_id.value,
                "title": issue.title,
                "description": issue.description,
                "wcag_criteria": issue.wcag_criteria,
                "legal_refs": issue.legal_refs,
                "difficulty": issue.difficulty.value,
                "steps": self._get_manual_steps(issue),
                "resources": self._get_resources(issue)
            })
        
        return guides
    
    def _get_widget_code(self, site_url: str, feature_id: FeatureId) -> str:
        """Gibt Widget-Integrationscode zurück"""
        site_id = site_url.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')
        
        return f'''<!-- Complyo Accessibility Widget -->
<script 
  src="https://api.complyo.tech/api/widgets/accessibility.js"
  data-site-id="{site_id}"
  data-auto-fix="true"
  data-features="{feature_id.value.lower()}"
></script>'''
    
    def _get_patch_instructions(self, issue: StructuredIssue) -> str:
        """Gibt Anweisungen für Patch-Anwendung zurück"""
        return f"""So wenden Sie diesen Patch an:

1. Öffnen Sie die Datei in Ihrem Editor
2. Suchen Sie die betroffene Stelle (siehe Diff)
3. Ersetzen Sie den alten Code durch den neuen
4. Speichern Sie die Datei
5. Testen Sie die Website im Browser

Betroffenes WCAG-Kriterium: {', '.join(issue.wcag_criteria)}"""
    
    def _get_manual_steps(self, issue: StructuredIssue) -> List[str]:
        """Gibt manuelle Schritte zurück"""
        # Basis-Schritte je nach Feature
        base_steps = {
            FeatureId.MEDIA: [
                "1. Identifizieren Sie alle Videos und Audios auf Ihrer Website",
                "2. Erstellen Sie Untertitel für Videos (z.B. mit YouTube oder Rev.com)",
                "3. Erstellen Sie Transkripte für Audios",
                "4. Fügen Sie die Untertitel als <track> Element hinzu",
                "5. Verlinken Sie Transkripte unter dem Media-Player"
            ],
            FeatureId.HEADINGS: [
                "1. Prüfen Sie die Überschriften-Hierarchie mit einem Browser-Tool",
                "2. Stellen Sie sicher, dass es genau eine H1 gibt",
                "3. Korrigieren Sie übersprungene Level (z.B. H1 → H3)",
                "4. Ersetzen Sie styled Divs durch echte Heading-Tags",
                "5. Testen Sie mit einem Screenreader"
            ]
        }
        
        return base_steps.get(issue.feature_id, [
            f"1. Lesen Sie die Beschreibung: {issue.description[:100]}...",
            f"2. Öffnen Sie die betroffene Seite: {issue.page_url or 'Ihre Website'}",
            "3. Suchen Sie das betroffene Element",
            f"4. Empfohlene Lösung: {issue.suggested_fix or 'Siehe WCAG-Dokumentation'}",
            "5. Testen Sie die Änderung"
        ])
    
    def _get_resources(self, issue: StructuredIssue) -> List[Dict[str, str]]:
        """Gibt hilfreiche Ressourcen zurück"""
        resources = []
        
        for criterion in issue.wcag_criteria:
            criterion_id = criterion.split()[0] if criterion else ""
            if criterion_id:
                resources.append({
                    "title": f"WCAG {criterion_id} - Verständlich erklärt",
                    "url": f"https://www.w3.org/WAI/WCAG21/Understanding/{criterion_id.replace('.', '')}"
                })
        
        resources.append({
            "title": "Complyo Barrierefreiheits-Guide",
            "url": "https://complyo.tech/guides/accessibility"
        })
        
        return resources


# Globale Instanz
patch_service = PatchService()

