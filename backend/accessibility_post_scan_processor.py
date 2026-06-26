"""
Complyo Accessibility Post-Scan Processor
==========================================
Verarbeitet Barrierefreiheits-Issues nach einem Scan und generiert Alt-Texte
"""

import asyncpg
import json
import logging
from typing import List, Dict, Any
from accessibility_fix_saver import AccessibilityFixSaver
from site_id_utils import derive_site_id

logger = logging.getLogger(__name__)


class AccessibilityPostScanProcessor:
    """
    Verarbeitet Accessibility-Issues nach einem Scan
    und generiert automatisch AI Alt-Texte
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.fix_saver = AccessibilityFixSaver(db_pool)
    
    async def process_scan_results(
        self,
        scan_id: str,
        user_id: str,
        scan_data: Dict[str, Any],
        site_url: str
    ) -> Dict[str, Any]:
        """
        Verarbeitet Scan-Ergebnisse und generiert Alt-Texte
        
        Args:
            scan_id: Scan-ID aus scan_history
            user_id: User UUID
            scan_data: Komplette Scan-Daten
            site_url: Website-URL
            
        Returns:
            Statistik über generierte Fixes
        """
        try:
            logger.info(f"🔍 Processing accessibility scan for {site_url}")

            # Stabile, domain-abgeleitete Site-ID. WICHTIG: Die Channels (WP-Plugin,
            # HTML-CLI, SPA-Runtime) fragen Fixes mit GENAU dieser ID ab. Früher wurde
            # unter scan_id gespeichert → Channel-Lookup lief ins Leere (stiller No-Op).
            stable_site_id = derive_site_id(site_url)

            # 1. Extrahiere Barrierefreiheits-Issues
            accessibility_issues = self._extract_accessibility_issues(scan_data)

            # Brücke zur Barrierefreiheitserklärung: Stand immer aktualisieren —
            # auch bei 0 Befunden, damit die Erklärung den aktuellen Scan widerspiegelt.
            await self._save_statement_package(user_id, site_url, accessibility_issues)

            # Auto-sichere, dokumentweite Fixes (Stufe 1) ableiten & persistieren —
            # Teil des vereinheitlichten Fix-Manifests. Unabhängig von Alt-Texten.
            document_fixes = self._derive_document_fixes(accessibility_issues, site_url)
            doc_saved = 0
            if document_fixes:
                doc_saved = await self.fix_saver.save_document_fixes(
                    site_id=stable_site_id,
                    scan_id=scan_id,
                    user_id=user_id,
                    fixes=document_fixes,
                )
                logger.info(f"🧩 Persisted {doc_saved} document-level fixes for {stable_site_id}")

            if not accessibility_issues:
                logger.info(f"✅ No accessibility issues found for {site_url}")
                return {
                    "success": True,
                    "alt_texts_generated": 0,
                    "document_fixes_generated": doc_saved,
                    "message": "Keine Barrierefreiheits-Issues gefunden"
                }
            
            logger.info(f"📋 Found {len(accessibility_issues)} accessibility issues")
            
            # 2. Filtere Alt-Text-bezogene Issues
            alt_text_issues = self._filter_alt_text_issues(accessibility_issues)
            
            if not alt_text_issues:
                logger.info(f"✅ No alt-text issues found")
                return {
                    "success": True,
                    "alt_texts_generated": 0,
                    "message": "Keine Alt-Text-Issues gefunden"
                }
            
            logger.info(f"🖼️ Found {len(alt_text_issues)} alt-text issues")
            
            # 3. Generiere AI Alt-Texte
            alt_text_fixes = await self._generate_alt_text_fixes(
                alt_text_issues,
                site_url
            )
            
            if not alt_text_fixes:
                logger.warning(f"⚠️ No alt-text fixes generated")
                return {
                    "success": False,
                    "alt_texts_generated": 0,
                    "message": "Keine Alt-Texte generiert"
                }
            
            logger.info(f"✨ Generated {len(alt_text_fixes)} AI alt-texts")
            
            # 4. Speichere in Datenbank — unter der STABILEN site_id (nicht scan_id!),
            #    damit die Channels die Fixes per Domain-site_id wiederfinden.
            saved_count = await self.fix_saver.save_alt_text_fixes(
                site_id=stable_site_id,
                scan_id=scan_id,
                user_id=user_id,
                fixes=alt_text_fixes
            )
            
            logger.info(f"✅ Saved {saved_count} alt-text fixes to database")
            
            return {
                "success": True,
                "alt_texts_generated": saved_count,
                "issues_found": len(accessibility_issues),
                "alt_text_issues": len(alt_text_issues),
                "message": f"{saved_count} Alt-Texte generiert und gespeichert"
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing accessibility scan: {e}")
            return {
                "success": False,
                "alt_texts_generated": 0,
                "error": str(e)
            }
    
    async def _save_statement_package(
        self,
        user_id: str,
        site_url: str,
        accessibility_issues: List[Dict[str, Any]]
    ) -> None:
        """
        Schreibt eine Zusammenfassung der gefundenen Barrierefreiheits-Issues nach
        accessibility_fix_packages. Die Barrierefreiheitserklärung liest genau diese
        Zeile (über site_id + user_id) und stellt so den echten Scan-Stand dar.

        fix_package-Format entspricht dem, was generate_statement erwartet:
        summary.total_issues + Issue-Beschreibungen in manual_guides.
        """
        site_id = derive_site_id(site_url)
        guides = []
        for issue in accessibility_issues:
            desc = (issue.get('description') or issue.get('title') or '').strip()
            if desc:
                guides.append({'description': desc})

        fix_package = {
            'summary': {'total_issues': len(accessibility_issues)},
            'manual_guides': guides,
            'source': 'scan',
        }

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO accessibility_fix_packages
                        (user_id, site_id, site_url, fix_package, created_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (user_id, site_id) DO UPDATE
                        SET fix_package = EXCLUDED.fix_package,
                            site_url    = EXCLUDED.site_url,
                            updated_at  = NOW()
                    """,
                    str(user_id), site_id, site_url, json.dumps(fix_package),
                )
            logger.info(
                f"📝 Statement-Paket gespeichert: {site_url} "
                f"(site_id={site_id}, {len(accessibility_issues)} Issues)"
            )
        except Exception as e:
            logger.error(f"❌ Statement-Paket konnte nicht gespeichert werden: {e}")

    def _derive_document_fixes(
        self,
        accessibility_issues: List[Dict[str, Any]],
        site_url: str
    ) -> List[Dict[str, Any]]:
        """
        Leitet AUTO-SICHERE, dokumentweite Fixes (Stufe 1) deterministisch aus den
        erkannten Issues ab. Bewusst konservativ: nur Fixes, die ohne menschliches
        Urteil unbedenklich anwendbar sind und von den Channels guarded angewendet
        werden (nur setzen, wenn am Ziel noch nicht vorhanden).

        Mapping Issue-Signal -> Fix:
          - fehlendes <html lang>      (WCAG 3.1.1) -> html-lang   {value: 'de'}
          - fehlender Skip-Link        (WCAG 2.4.1) -> skip-link   {target, label}
          - fehlende <main>-Landmark   (WCAG 1.3.1) -> landmark-main
          - nicht sichtbarer Fokus     (WCAG 2.4.7) -> css-rule    (:focus outline)

        Jeder Typ wird maximal EINMAL erzeugt (dokumentweit, nicht je Element).
        """
        # Sprache aus der Domain/Markt ableiten: Default 'de' (Komplyo = DE-Markt).
        lang_value = 'de'

        # Alle Issue-Texte zu einem durchsuchbaren Blob zusammenfassen.
        def _text(issue: Dict[str, Any]) -> str:
            return ' '.join([
                str(issue.get('title', '')),
                str(issue.get('description', '')),
                str(issue.get('type', '')),
                str(issue.get('id', '')),
                ' '.join(str(w) for w in (issue.get('wcag_criteria') or [])),
            ]).lower()

        blob = ' \n '.join(_text(i) for i in accessibility_issues)

        fixes: List[Dict[str, Any]] = []

        def has(*needles: str) -> bool:
            return any(n in blob for n in needles)

        # 3.1.1 Sprache der Seite — fehlendes/leeres lang-Attribut
        if has('lang-attribut', 'lang attribute', 'html-lang', 'html lang',
               'sprache der seite', 'language of page', 'wcag311', '3.1.1'):
            fixes.append({
                'fix_type': 'html-lang',
                'payload': {'value': lang_value},
                'wcag_criterion': '3.1.1',
                'confidence': 1.0,
                'page_url': site_url,
                'source': 'scan',
            })

        # 2.4.1 Blöcke umgehen — fehlender Skip-Link
        if has('skip-link', 'skip link', 'sprunglink', 'zum inhalt springen',
               'bypass blocks', 'blöcke umgehen', 'wcag241', '2.4.1'):
            fixes.append({
                'fix_type': 'skip-link',
                'payload': {'target': '#main', 'label': 'Zum Inhalt springen'},
                'wcag_criterion': '2.4.1',
                'confidence': 1.0,
                'page_url': site_url,
                'source': 'scan',
            })

        # 1.3.1 Info & Beziehungen — fehlende <main>-Landmark
        if has('landmark', 'main-landmark', 'hauptinhalt-bereich', 'region',
               'main region', '<main>'):
            fixes.append({
                'fix_type': 'landmark-main',
                'payload': {'target': '#main'},
                'wcag_criterion': '1.3.1',
                'confidence': 0.9,
                'page_url': site_url,
                'source': 'scan',
            })

        # 2.4.7 Fokus sichtbar — kein sichtbarer Fokus-Indikator
        if has('fokus', 'focus visible', 'focus-visible', 'sichtbarer fokus',
               'fokus-indikator', 'outline', 'wcag247', '2.4.7'):
            fixes.append({
                'fix_type': 'css-rule',
                'payload': {
                    'selector': 'a:focus, button:focus, input:focus, select:focus, textarea:focus, [tabindex]:focus',
                    'declarations': 'outline: 2px solid #1a73e8 !important; outline-offset: 2px !important;',
                },
                'wcag_criterion': '2.4.7',
                'confidence': 0.85,
                'page_url': site_url,
                'source': 'scan',
            })

        return fixes

    def _extract_accessibility_issues(
        self,
        scan_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extrahiert Barrierefreiheits-Issues aus Scan-Daten
        """
        issues = []
        
        # Verschiedene mögliche Daten-Strukturen supporten
        if isinstance(scan_data, dict):
            # Option 1: scan_data.issues
            if 'issues' in scan_data:
                all_issues = scan_data['issues']
                if isinstance(all_issues, list):
                    for issue in all_issues:
                        if isinstance(issue, dict):
                            category = issue.get('category', '').lower()
                            if 'accessibility' in category or 'barrierefreiheit' in category:
                                issues.append(issue)
            
            # Option 2: scan_data.pillars.accessibility
            if 'pillars' in scan_data and isinstance(scan_data['pillars'], dict):
                accessibility = scan_data['pillars'].get('accessibility', {})
                if isinstance(accessibility, dict) and 'issues' in accessibility:
                    issues.extend(accessibility['issues'])
        
        return issues
    
    def _filter_alt_text_issues(
        self,
        accessibility_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filtert nur Alt-Text-bezogene Issues
        """
        alt_text_issues = []
        
        keywords = ['alt', 'bild', 'image', 'img', 'grafik', 'foto']
        
        for issue in accessibility_issues:
            title = str(issue.get('title', '')).lower()
            description = str(issue.get('description', '')).lower()
            issue_type = str(issue.get('type', '')).lower()
            
            # Check if issue is about alt-texts
            if any(keyword in title or keyword in description or keyword in issue_type 
                   for keyword in keywords):
                alt_text_issues.append(issue)
        
        return alt_text_issues
    
    async def _generate_alt_text_fixes(
        self,
        alt_text_issues: List[Dict[str, Any]],
        site_url: str
    ) -> List[Dict[str, Any]]:
        """
        Generiert AI Alt-Text-Fixes
        
        Für jetzt: Simple Demo-Generierung
        TODO: Echte AI-Integration später
        """
        fixes = []
        
        for idx, issue in enumerate(alt_text_issues):
            # Extrahiere Bild-Informationen aus Issue
            image_src = issue.get('element', {}).get('src', '') or \
                       issue.get('image_src', '') or \
                       f'/image-{idx + 1}.jpg'
            
            # Generiere Filename
            filename = image_src.split('/')[-1] if '/' in image_src else image_src
            
            # Extrahiere Kontext
            page_url = issue.get('page_url', site_url)
            page_title = issue.get('page_title', '') or \
                        self._extract_page_title_from_url(page_url)
            
            surrounding_text = issue.get('surrounding_text', '') or \
                             issue.get('context', '') or \
                             ''
            
            element_html = issue.get('element_html', '') or \
                          issue.get('html', '') or \
                          f'<img src="{image_src}">'
            
            # Generiere Alt-Text (Simple Heuristik für jetzt)
            suggested_alt = self._generate_simple_alt_text(
                filename=filename,
                page_title=page_title,
                surrounding_text=surrounding_text,
                image_src=image_src
            )
            
            # Confidence basierend auf verfügbarem Kontext
            confidence = self._calculate_confidence(
                page_title=page_title,
                surrounding_text=surrounding_text,
                filename=filename
            )
            
            fixes.append({
                "page_url": page_url,
                "image_src": image_src,
                "image_filename": filename,
                "suggested_alt": suggested_alt,
                "confidence": confidence,
                "page_title": page_title,
                "surrounding_text": surrounding_text[:500],  # Limit length
                "element_html": element_html[:1000]  # Limit length
            })
        
        return fixes
    
    def _extract_page_title_from_url(self, url: str) -> str:
        """Extrahiert einen sinnvollen Titel aus der URL"""
        parts = url.rstrip('/').split('/')
        if parts:
            last_part = parts[-1]
            if last_part:
                return last_part.replace('-', ' ').replace('_', ' ').title()
        return "Website"
    
    def _generate_simple_alt_text(
        self,
        filename: str,
        page_title: str,
        surrounding_text: str,
        image_src: str
    ) -> str:
        """
        Generiert einen einfachen Alt-Text basierend auf Kontext
        
        TODO: Später durch echte AI ersetzen!
        """
        # Bereinige Filename
        clean_filename = filename.replace('.jpg', '').replace('.png', '') \
                                 .replace('.gif', '').replace('.webp', '') \
                                 .replace('-', ' ').replace('_', ' ')
        
        # Heuristiken für häufige Fälle
        if 'logo' in clean_filename.lower() or 'logo' in image_src.lower():
            return f"Logo - {page_title}" if page_title else "Firmenlogo"
        
        if 'hero' in clean_filename.lower() or 'banner' in clean_filename.lower():
            return f"Titelbild - {page_title}" if page_title else "Titelbild der Seite"
        
        if 'team' in clean_filename.lower():
            return "Team-Foto" + (f" - {page_title}" if page_title else "")
        
        if 'product' in clean_filename.lower():
            return "Produktabbildung" + (f" - {page_title}" if page_title else "")
        
        if 'icon' in clean_filename.lower():
            return f"Icon - {clean_filename.title()}"
        
        # Fallback: Nutze Kontext
        if surrounding_text:
            # Nimm die ersten Worte des umgebenden Textes
            words = surrounding_text.split()[:5]
            context = ' '.join(words)
            return f"Bild: {context}..."
        
        # Letzter Fallback: Filename
        return f"Bild: {clean_filename.title()}"
    
    def _calculate_confidence(
        self,
        page_title: str,
        surrounding_text: str,
        filename: str
    ) -> float:
        """
        Berechnet Confidence-Score für generierten Alt-Text
        
        0.0 - 1.0 wobei höher = besser
        """
        confidence = 0.5  # Base confidence
        
        # Bonus für verfügbaren Kontext
        if page_title:
            confidence += 0.1
        
        if surrounding_text and len(surrounding_text) > 20:
            confidence += 0.2
        
        if filename and len(filename) > 5:
            confidence += 0.1
        
        # Bonus für aussagekräftige Keywords
        keywords = ['logo', 'team', 'product', 'hero', 'banner']
        if any(kw in filename.lower() for kw in keywords):
            confidence += 0.1
        
        return min(confidence, 1.0)  # Cap at 1.0

