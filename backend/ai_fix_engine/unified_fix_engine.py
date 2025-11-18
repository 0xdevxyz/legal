"""
Complyo AI Fix Engine - Unified Fix Engine v2.0

Zentrale Engine für alle Fix-Typen mit:
- Handler-Routing
- AI-Call mit Retry-Logic
- Validation & Enrichment
- Fallback-Ketten

© 2025 Complyo.tech
"""

import os
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .prompts_v2 import PromptBuilder, FixType, AIModel, ContextBuilder
from .prompts_v2 import CODE_FIX_SCHEMA, TEXT_FIX_SCHEMA, WIDGET_FIX_SCHEMA, GUIDE_FIX_SCHEMA
from .validators import FixValidator, ValidationResult


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class FixResult:
    """Ergebnis eines Fix-Vorgangs"""
    fix_id: str
    fix_type: str
    status: str  # success, partial, failed
    data: Dict[str, Any]
    validation_result: Optional[ValidationResult]
    metadata: Dict[str, Any]
    generated_at: str
    ai_model_used: str
    generation_time_ms: int
    fallback_used: bool


@dataclass
class AICallResult:
    """Ergebnis eines AI-API-Calls"""
    success: bool
    content: Optional[str]
    model: str
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    error: Optional[str]
    response_time_ms: int


# =============================================================================
# AI API Client
# =============================================================================

class AIApiClient:
    """Client für AI-API-Calls mit Retry und Fallback"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.timeout = 60.0
        
        # Model pricing (USD per 1M tokens)
        self.pricing = {
            AIModel.CLAUDE_SONNET.value: {"input": 3.0, "output": 15.0},
            AIModel.GPT4.value: {"input": 30.0, "output": 60.0},
            AIModel.GPT4_TURBO.value: {"input": 10.0, "output": 30.0}
        }
    
    async def call_ai(
        self,
        prompt: str,
        system_message: str,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        retry_count: int = 3
    ) -> AICallResult:
        """
        Ruft AI-API mit Retry-Logic auf
        """
        if not self.api_key:
            return AICallResult(
                success=False,
                content=None,
                model=model,
                tokens_used=None,
                cost_usd=None,
                error="OPENROUTER_API_KEY nicht konfiguriert",
                response_time_ms=0
            )
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://complyo.tech",
                        "X-Title": "Complyo AI Fix Engine"
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
                            
                            # Calculate usage
                            usage = result.get("usage", {})
                            input_tokens = usage.get("prompt_tokens", 0)
                            output_tokens = usage.get("completion_tokens", 0)
                            total_tokens = input_tokens + output_tokens
                            
                            # Calculate cost
                            pricing = self.pricing.get(model, {"input": 5.0, "output": 15.0})
                            cost = (input_tokens * pricing["input"] / 1_000_000 + 
                                   output_tokens * pricing["output"] / 1_000_000)
                            
                            return AICallResult(
                                success=True,
                                content=content,
                                model=model,
                                tokens_used=total_tokens,
                                cost_usd=cost,
                                error=None,
                                response_time_ms=response_time
                            )
                        
                        elif response.status == 429:
                            # Rate limit - wait and retry
                            last_error = "Rate limit erreicht"
                            wait_time = 2 ** attempt  # Exponential backoff
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            error_text = await response.text()
                            last_error = f"API Error {response.status}: {error_text}"
                            
                            if response.status >= 500:
                                # Server error - retry
                                await asyncio.sleep(1)
                                continue
                            else:
                                # Client error - don't retry
                                break
            
            except asyncio.TimeoutError:
                last_error = "Timeout bei AI-API-Call"
                await asyncio.sleep(1)
                continue
            
            except Exception as e:
                last_error = f"Exception: {str(e)}"
                await asyncio.sleep(1)
                continue
        
        # All retries failed
        response_time = int((time.time() - start_time) * 1000)
        return AICallResult(
            success=False,
            content=None,
            model=model,
            tokens_used=None,
            cost_usd=None,
            error=last_error or "Unknown error",
            response_time_ms=response_time
        )


# =============================================================================
# Response Parser
# =============================================================================

class ResponseParser:
    """Parst AI-Responses"""
    
    @staticmethod
    def extract_json(response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extrahiert JSON aus AI-Response
        """
        if not response_text:
            return None
        
        # Try direct JSON parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON block with ```json
        json_block_pattern = r'```json\s*\n(.*?)\n```'
        import re
        match = re.search(json_block_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find any JSON-like structure
        brace_start = response_text.find('{')
        brace_end = response_text.rfind('}')
        
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            try:
                json_str = response_text[brace_start:brace_end + 1]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        return None


# =============================================================================
# Unified Fix Engine
# =============================================================================

class UnifiedFixEngine:
    """
    Zentrale Engine für alle Fix-Typen
    """
    
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.validator = FixValidator()
        self.ai_client = AIApiClient()
        self.parser = ResponseParser()
        self.context_builder = ContextBuilder()
        
        # Schema mapping
        self.schemas = {
            "code": CODE_FIX_SCHEMA,
            "text": TEXT_FIX_SCHEMA,
            "widget": WIDGET_FIX_SCHEMA,
            "guide": GUIDE_FIX_SCHEMA
        }
        
        # Fallback chain: Primary model -> Fallback model -> Template-based
        self.fallback_chain = [
            AIModel.CLAUDE_SONNET.value,
            AIModel.GPT4_TURBO.value
        ]
    
    async def generate_fix(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        fix_type: Optional[str] = None,
        user_skill: str = "intermediate"
    ) -> FixResult:
        """
        Hauptmethode: Generiert Fix für ein Issue
        
        Args:
            issue: Issue-Daten (title, description, category, etc.)
            context: Website-Context (url, company, tech_stack, etc.)
            fix_type: Optional - wenn nicht angegeben, wird automatisch bestimmt
            user_skill: User-Skill-Level (beginner, intermediate, advanced)
        
        Returns:
            FixResult mit generiertem Fix
        """
        start_time = time.time()
        
        # 1. Determine fix type if not provided
        if not fix_type:
            fix_type = self._determine_fix_type(issue)
        
        print(f"🔧 Generating {fix_type} fix for issue: {issue.get('title', 'Unknown')}")
        
        # 2. Build prompt
        prompt_data = self._build_prompt_for_type(fix_type, issue, context, user_skill)
        
        if not prompt_data:
            return self._create_error_result(
                issue.get("id", "unknown"),
                fix_type,
                "Could not build prompt for this fix type"
            )
        
        # 3. Get system message
        system_message = self.prompt_builder.get_system_message(FixType(fix_type))
        
        # 4. Call AI with fallback chain
        ai_result = None
        fallback_used = False
        
        for model in self.fallback_chain:
            print(f"  🤖 Trying model: {model}")
            
            ai_result = await self.ai_client.call_ai(
                prompt=prompt_data["prompt"],
                system_message=system_message,
                model=model,
                temperature=prompt_data.get("temperature", 0.3),
                max_tokens=prompt_data.get("max_tokens", 2000),
                retry_count=2
            )
            
            if ai_result.success:
                print(f"  ✅ Success with {model}")
                if model != self.fallback_chain[0]:
                    fallback_used = True
                break
            else:
                print(f"  ❌ Failed with {model}: {ai_result.error}")
                fallback_used = True
        
        # If all AI calls failed, use template-based fallback
        if not ai_result or not ai_result.success:
            print("  ⚠️ All AI models failed, using template-based fallback")
            return await self._generate_template_based_fix(issue, context, fix_type)
        
        # 5. Parse AI response
        parsed_data = self.parser.extract_json(ai_result.content)
        
        if not parsed_data:
            print("  ⚠️ Could not parse AI response, using template")
            return await self._generate_template_based_fix(issue, context, fix_type)
        
        # 6. Validate
        schema = self.schemas.get(fix_type)
        sanitized_data, validation_result = self.validator.validate_and_sanitize(
            parsed_data,
            fix_type,
            schema
        )
        
        if not validation_result.is_valid:
            print(f"  ⚠️ Validation failed: {validation_result.errors}")
        
        # 7. Enrich with metadata
        enriched_data = self._enrich_fix_data(sanitized_data, issue, context, fix_type)
        
        # 8. Calculate generation time
        generation_time = int((time.time() - start_time) * 1000)
        
        # 9. Create result
        result = FixResult(
            fix_id=enriched_data.get("fix_id", issue.get("id", "unknown")),
            fix_type=fix_type,
            status="success" if validation_result.is_valid else "partial",
            data=enriched_data,
            validation_result=validation_result,
            metadata={
                "ai_model": ai_result.model,
                "tokens_used": ai_result.tokens_used,
                "cost_usd": ai_result.cost_usd,
                "response_time_ms": ai_result.response_time_ms,
                "validation_warnings": validation_result.warnings,
                "user_skill": user_skill
            },
            generated_at=datetime.now().isoformat(),
            ai_model_used=ai_result.model,
            generation_time_ms=generation_time,
            fallback_used=fallback_used
        )
        
        print(f"  ✅ Fix generated successfully in {generation_time}ms")
        return result
    
    def _determine_fix_type(self, issue: Dict[str, Any]) -> str:
        """
        Bestimmt Fix-Typ basierend auf Issue-Kategorie und Titel
        """
        category = issue.get("category", "").lower()
        title = issue.get("title", "").lower()
        
        # TEXT: Legal texts
        if any(keyword in category or keyword in title for keyword in 
               ["impressum", "datenschutz", "agb", "widerruf", "legal", "rechtstext"]):
            return "text"
        
        # WIDGET: Cookie or Accessibility widgets
        if any(keyword in category or keyword in title for keyword in 
               ["cookie", "consent", "barrierefreiheit", "accessibility"]):
            # Check if can be fixed with widget
            if any(keyword in title for keyword in ["banner", "widget", "tool"]):
                return "widget"
            # Otherwise code fix
            return "code"
        
        # CODE: Technical implementations
        if any(keyword in category or keyword in title for keyword in 
               ["wcag", "alt", "aria", "meta", "html", "css"]):
            return "code"
        
        # GUIDE: Complex/strategic topics
        if any(keyword in category or keyword in title for keyword in 
               ["strategie", "konzept", "prozess", "compliance"]):
            return "guide"
        
        # Default: guide (safest option)
        return "guide"
    
    def _build_prompt_for_type(
        self,
        fix_type: str,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        user_skill: str
    ) -> Optional[Dict[str, Any]]:
        """
        Baut Prompt basierend auf Fix-Typ
        """
        if fix_type == "code":
            return self.prompt_builder.build_code_fix_prompt(issue, context, user_skill)
        
        elif fix_type == "text":
            # Determine text type from issue
            title_lower = issue.get("title", "").lower()
            if "impressum" in title_lower:
                text_type = "impressum"
            elif "datenschutz" in title_lower or "privacy" in title_lower:
                text_type = "datenschutz"
            else:
                text_type = "generic"
            
            return self.prompt_builder.build_legal_text_prompt(issue, context, text_type)
        
        elif fix_type == "widget":
            # Determine widget type
            title_lower = issue.get("title", "").lower()
            if "cookie" in title_lower or "consent" in title_lower:
                widget_type = "cookie-consent"
            elif "barriere" in title_lower or "accessibility" in title_lower:
                widget_type = "accessibility"
            else:
                widget_type = "cookie-consent"  # Default
            
            return self.prompt_builder.build_widget_fix_prompt(issue, context, widget_type)
        
        elif fix_type == "guide":
            return self.prompt_builder.build_guide_fix_prompt(issue, context, user_skill)
        
        return None
    
    def _enrich_fix_data(
        self,
        fix_data: Dict[str, Any],
        issue: Dict[str, Any],
        context: Dict[str, Any],
        fix_type: str
    ) -> Dict[str, Any]:
        """
        Reichert Fix-Daten mit zusätzlichen Metadaten an
        """
        enriched = fix_data.copy()
        
        # Add source issue info
        enriched["source_issue"] = {
            "id": issue.get("id"),
            "title": issue.get("title"),
            "category": issue.get("category"),
            "severity": issue.get("severity")
        }
        
        # Add context info
        enriched["context_info"] = {
            "url": context.get("url"),
            "cms": context.get("technology", {}).get("cms", []),
            "site_id": context.get("site_id")
        }
        
        # Add Complyo branding
        enriched["branding"] = {
            "powered_by": "Complyo.tech",
            "disclaimer": "Dieser Fix wurde automatisch generiert. Bitte prüfen Sie die Umsetzung.",
            "generated_at": datetime.now().isoformat()
        }
        
        return enriched
    
    async def _generate_template_based_fix(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        fix_type: str
    ) -> FixResult:
        """
        Fallback: Template-basierter Fix wenn AI fehlschlägt
        """
        print("  📝 Generating template-based fix")
        
        fix_data = {
            "fix_id": issue.get("id", "template_fix"),
            "title": f"Anleitung: {issue.get('title', 'Problem beheben')}",
            "description": issue.get("description", ""),
            "generated_by": "template"
        }
        
        if fix_type == "guide":
            fix_data["steps"] = [
                {
                    "step_number": 1,
                    "title": "Problem analysieren",
                    "description": issue.get("description", "Analysieren Sie das Problem"),
                    "validation": "Prüfen Sie die Situation"
                },
                {
                    "step_number": 2,
                    "title": "Empfehlung umsetzen",
                    "description": issue.get("recommendation", "Setzen Sie die Empfehlung um"),
                    "validation": "Testen Sie die Lösung"
                }
            ]
            fix_data["difficulty"] = "intermediate"
            fix_data["estimated_time"] = "15-20 Minuten"
        
        elif fix_type == "text":
            fix_data["text_content"] = f"<p>{issue.get('recommendation', 'Bitte ergänzen Sie den rechtssicheren Text.')}</p>"
            fix_data["text_type"] = "generic"
            fix_data["format"] = "html"
        
        elif fix_type == "code":
            fix_data["code"] = "<!-- Code-Lösung -->\n<!-- Bitte manuell ergänzen -->"
            fix_data["language"] = "html"
            fix_data["integration"] = {
                "instructions": "Bitte passen Sie den Code an Ihre Bedürfnisse an."
            }
        
        elif fix_type == "widget":
            fix_data["widget_type"] = "generic"
            fix_data["integration_code"] = "<!-- Widget-Code -->"
            fix_data["integration"] = {
                "instructions": "Bitte fügen Sie den Widget-Code ein."
            }
        
        return FixResult(
            fix_id=fix_data["fix_id"],
            fix_type=fix_type,
            status="partial",
            data=fix_data,
            validation_result=None,
            metadata={
                "fallback": "template",
                "reason": "AI generation failed"
            },
            generated_at=datetime.now().isoformat(),
            ai_model_used="template",
            generation_time_ms=0,
            fallback_used=True
        )
    
    def _create_error_result(
        self,
        fix_id: str,
        fix_type: str,
        error_message: str
    ) -> FixResult:
        """
        Erstellt Error-Result
        """
        return FixResult(
            fix_id=fix_id,
            fix_type=fix_type,
            status="failed",
            data={},
            validation_result=None,
            metadata={"error": error_message},
            generated_at=datetime.now().isoformat(),
            ai_model_used="none",
            generation_time_ms=0,
            fallback_used=False
        )
    
    def to_dict(self, fix_result: FixResult) -> Dict[str, Any]:
        """
        Konvertiert FixResult zu Dictionary für API-Response
        """
        return {
            "fix_id": fix_result.fix_id,
            "fix_type": fix_result.fix_type,
            "status": fix_result.status,
            "data": fix_result.data,
            "validation": {
                "is_valid": fix_result.validation_result.is_valid if fix_result.validation_result else None,
                "errors": fix_result.validation_result.errors if fix_result.validation_result else [],
                "warnings": fix_result.validation_result.warnings if fix_result.validation_result else []
            } if fix_result.validation_result else None,
            "metadata": fix_result.metadata,
            "generated_at": fix_result.generated_at,
            "generation_time_ms": fix_result.generation_time_ms,
            "fallback_used": fix_result.fallback_used
        }


