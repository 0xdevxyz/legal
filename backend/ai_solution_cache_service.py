"""
AI Solution Cache Service
Intelligentes Caching-System für AI-generierte Lösungen

Funktionen:
- Exact Matching via SHA256 Fingerprint
- Fuzzy Matching via Similarity Score
- Automatisches Learning durch Usage Metrics
- 70-85% Reduktion der API-Calls

Author: Complyo Team
Date: 2025-11-17
"""

import hashlib
import logging
from typing import Optional, List, Dict, Tuple
from difflib import SequenceMatcher
import asyncpg

logger = logging.getLogger(__name__)

class AISolutionCache:
    """Intelligentes Caching-System für AI-Lösungen"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.similarity_threshold = 0.85  # 85% Ähnlichkeit für Cache-Hit
        self.min_success_rate = 0.6  # Nur Lösungen mit >60% Success Rate nutzen
        
        logger.info("🎯 AI Solution Cache initialisiert")
    
    def _generate_fingerprint(self, category: str, title: str, description: str) -> str:
        """
        Generiert eindeutigen SHA256-Fingerprint für ein Issue
        
        Args:
            category: Issue-Kategorie (z.B. 'datenschutz')
            title: Issue-Titel
            description: Issue-Beschreibung
            
        Returns:
            64-stelliger Hex-String (SHA256)
        """
        # Normalisiere Input für konsistente Hashes
        content = f"{category.lower().strip()}|{title.lower().strip()}|{description.lower().strip()}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Berechnet Ähnlichkeit zwischen zwei Texten
        
        Args:
            text1: Erster Text
            text2: Zweiter Text
            
        Returns:
            Similarity Score (0.0 - 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # SequenceMatcher für Token-basierte Similarity
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    async def get_cached_solution(
        self, 
        category: str, 
        title: str, 
        description: str,
        use_fuzzy: bool = True
    ) -> Optional[Dict[str, any]]:
        """
        Versucht gecachte Lösung zu finden
        
        Strategie:
        1. Exact Match via Fingerprint (schnell, O(1))
        2. Fuzzy Match via Similarity (intelligent, O(n))
        
        Args:
            category: Issue-Kategorie
            title: Issue-Titel
            description: Issue-Beschreibung
            use_fuzzy: Ob Fuzzy Matching verwendet werden soll
            
        Returns:
            Dict mit 'solution', 'usage_count', 'success_rate' oder None
        """
        fingerprint = self._generate_fingerprint(category, title, description)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1️⃣ EXACT MATCH (Fingerprint)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        try:
            async with self.db_pool.acquire() as conn:
                exact_match = await conn.fetchrow("""
                    SELECT 
                        ai_solution,
                        usage_count,
                        success_rate,
                        id
                    FROM ai_solution_cache
                    WHERE issue_fingerprint = $1
                      AND success_rate >= $2
                    LIMIT 1
                """, fingerprint, self.min_success_rate)
                
                if exact_match:
                    # Update usage stats
                    await conn.execute("""
                        UPDATE ai_solution_cache
                        SET usage_count = usage_count + 1,
                            last_used_at = NOW(),
                            updated_at = NOW()
                        WHERE id = $1
                    """, exact_match['id'])
                    
                    logger.info(
                        f"✅ CACHE HIT (Exact) [{exact_match['usage_count']} uses, "
                        f"{exact_match['success_rate']:.0%} success]: {title[:50]}..."
                    )
                    
                    return {
                        'solution': exact_match['ai_solution'],
                        'usage_count': exact_match['usage_count'] + 1,
                        'success_rate': exact_match['success_rate'],
                        'match_type': 'exact'
                    }
        except Exception as e:
            logger.error(f"❌ Exact match lookup failed: {e}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2️⃣ FUZZY MATCH (Similarity Search)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if use_fuzzy:
            try:
                async with self.db_pool.acquire() as conn:
                    # Hole potenzielle Kandidaten aus gleicher Kategorie
                    similar_issues = await conn.fetch("""
                        SELECT 
                            id,
                            issue_title,
                            issue_description,
                            ai_solution,
                            usage_count,
                            success_rate
                        FROM ai_solution_cache
                        WHERE category = $1
                          AND success_rate >= $2
                        ORDER BY usage_count DESC, success_rate DESC
                        LIMIT 30
                    """, category, self.min_success_rate)
                    
                    if not similar_issues:
                        logger.info(f"ℹ️ No cached solutions in category '{category}'")
                        return None
                    
                    # Finde beste Übereinstimmung
                    best_match = None
                    best_similarity = 0.0
                    
                    for issue in similar_issues:
                        # Berechne Similarity für Titel und Beschreibung
                        title_sim = self._calculate_similarity(title, issue['issue_title'])
                        desc_sim = self._calculate_similarity(description, issue['issue_description'])
                        
                        # Gewichtete Similarity: 70% Titel, 30% Beschreibung
                        combined_sim = (title_sim * 0.7) + (desc_sim * 0.3)
                        
                        # Bonus für hohe Success Rate
                        success_bonus = issue['success_rate'] * 0.05
                        final_sim = min(combined_sim + success_bonus, 1.0)
                        
                        if final_sim > best_similarity:
                            best_similarity = final_sim
                            best_match = issue
                    
                    # Prüfe ob Similarity-Threshold erreicht
                    if best_match and best_similarity >= self.similarity_threshold:
                        # Update usage
                        await conn.execute("""
                            UPDATE ai_solution_cache
                            SET usage_count = usage_count + 1,
                                last_used_at = NOW(),
                                updated_at = NOW()
                            WHERE id = $1
                        """, best_match['id'])
                        
                        logger.info(
                            f"✅ CACHE HIT (Fuzzy {best_similarity:.0%}) "
                            f"[{best_match['usage_count']} uses, "
                            f"{best_match['success_rate']:.0%} success]: {title[:50]}..."
                        )
                        
                        return {
                            'solution': best_match['ai_solution'],
                            'usage_count': best_match['usage_count'] + 1,
                            'success_rate': best_match['success_rate'],
                            'match_type': 'fuzzy',
                            'similarity': best_similarity
                        }
                    else:
                        logger.info(
                            f"ℹ️ Best similarity {best_similarity:.0%} below threshold "
                            f"{self.similarity_threshold:.0%}"
                        )
            except Exception as e:
                logger.error(f"❌ Fuzzy match lookup failed: {e}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3️⃣ CACHE MISS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info(f"❌ CACHE MISS: {title[:50]}... - Will use OpenRouter API")
        return None
    
    async def store_solution(
        self,
        category: str,
        title: str,
        description: str,
        solution: str,
        model: str = 'moonshotai/kimi-k2-thinking'
    ) -> bool:
        """
        Speichert neue AI-Lösung im Cache
        
        Args:
            category: Issue-Kategorie
            title: Issue-Titel
            description: Issue-Beschreibung
            solution: Generierte AI-Lösung
            model: Verwendetes AI-Modell
            
        Returns:
            True wenn erfolgreich gespeichert
        """
        fingerprint = self._generate_fingerprint(category, title, description)
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO ai_solution_cache (
                        category,
                        issue_title,
                        issue_description,
                        issue_fingerprint,
                        ai_solution,
                        model_used,
                        usage_count,
                        success_rate
                    ) VALUES ($1, $2, $3, $4, $5, $6, 1, 0.8)
                    ON CONFLICT (issue_fingerprint) DO UPDATE SET
                        ai_solution = EXCLUDED.ai_solution,
                        model_used = EXCLUDED.model_used,
                        updated_at = NOW()
                """, category, title, description, fingerprint, solution, model)
                
            logger.info(f"💾 Solution cached: {title[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cache solution: {e}")
            return False
    
    async def update_success_rate(
        self, 
        category: str, 
        title: str, 
        description: str, 
        success: bool
    ):
        """
        Update Success Rate basierend auf User-Feedback
        
        Args:
            category: Issue-Kategorie
            title: Issue-Titel
            description: Issue-Beschreibung
            success: True = positives Feedback, False = negatives Feedback
        """
        fingerprint = self._generate_fingerprint(category, title, description)
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE ai_solution_cache
                    SET success_rate = (
                        CASE 
                            WHEN $2 THEN LEAST(success_rate + 0.1, 1.0)
                            ELSE GREATEST(success_rate - 0.2, 0.0)
                        END
                    ),
                    updated_at = NOW()
                    WHERE issue_fingerprint = $1
                """, fingerprint, success)
                
            logger.info(
                f"📊 Success rate updated: {title[:50]}... "
                f"({'👍 positive' if success else '👎 negative'})"
            )
        except Exception as e:
            logger.error(f"❌ Failed to update success rate: {e}")
    
    async def get_cache_stats(self) -> Dict[str, any]:
        """
        Hole Cache-Statistiken
        
        Returns:
            Dict mit Statistiken (total_cached, total_hits, avg_success_rate, etc.)
        """
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_cached_solutions,
                        SUM(usage_count) as total_cache_hits,
                        AVG(success_rate) as avg_success_rate,
                        MAX(last_used_at) as last_cache_hit
                    FROM ai_solution_cache
                """)
                
                category_stats = await conn.fetch("""
                    SELECT * FROM ai_cache_stats
                """)
                
                return {
                    'total_cached_solutions': stats['total_cached_solutions'] or 0,
                    'total_cache_hits': stats['total_cache_hits'] or 0,
                    'avg_success_rate': float(stats['avg_success_rate'] or 0.0),
                    'last_cache_hit': stats['last_cache_hit'],
                    'by_category': [dict(row) for row in category_stats]
                }
        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {}

