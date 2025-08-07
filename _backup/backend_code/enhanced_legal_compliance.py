import re
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class EnhancedLegalComplianceEngine:
    def __init__(self):
        self.current_year = datetime.now().year
        logger.info("Enhanced Legal Compliance Engine initialized with Google Fonts focus")
        
    async def analyze_website_detailed(self, url: str) -> Dict[str, Any]:
        """Detaillierte Compliance-Analyse mit Google Fonts als höchste Priorität"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    content = await response.text()
            
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text().lower()
            
            # Google Fonts Analyse - KRITISCHE PRIORITÄT!
            google_fonts_analysis = await self._analyze_google_fonts_comprehensive(url, content, soup)
            
            # Weitere Analysen
            is_shop = self._detect_shop_advanced(text, soup)
            impressum_analysis = self._analyze_impressum_enhanced(text)
            datenschutz_analysis = self._analyze_datenschutz_enhanced(text)
            cookie_analysis = self._analyze_cookies_basic(soup)
            
            # Score-Berechnung: Google Fonts haben 40% Gewichtung!
            overall_score = self._calculate_weighted_score(
                google_fonts_analysis, impressum_analysis, 
                datenschutz_analysis, cookie_analysis, is_shop
            )
            
            # eRecht24 Compatibility - wird durch Google Fonts blockiert
            erecht24_compat = self._check_erecht24_compatibility_with_fonts(
                google_fonts_analysis, impressum_analysis, datenschutz_analysis
            )
            
            result = {
                "url": url,
                "scan_timestamp": datetime.now().isoformat(),
                "is_shop": is_shop,
                "overall_score": overall_score,
                "analysis_engine": "enhanced_v2.1",
                
                # Google Fonts als erste und wichtigste Kategorie
                "google_fonts": google_fonts_analysis,
                "impressum": impressum_analysis,
                "datenschutz": datenschutz_analysis,
                "cookie_tracking": cookie_analysis,
                "shop_compliance": {"detected": is_shop} if is_shop else None,
                "erecht24_compatible": erecht24_compat
            }
            
            # Priority Warning bei Google Fonts
            if google_fonts_analysis.get("total_violations", 0) > 0:
                result["critical_alert"] = {
                    "type": "google_fonts_dsgvo_violation",
                    "severity": "critical",
                    "message": f"🚨 {google_fonts_analysis['total_violations']} Google Fonts DSGVO-Verstöße erkannt",
                    "immediate_action": "Alle Google Fonts Verbindungen sofort entfernen",
                    "legal_consequence": f"Abmahnrisiko: {google_fonts_analysis['abmahn_risk']}",
                    "estimated_costs": google_fonts_analysis.get("potential_costs", {}).get("range", "500-2.000€")
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced analysis failed for {url}: {str(e)}")
            return {"error": f"Enhanced analysis failed: {str(e)}", "fallback_available": True}

    async def _analyze_google_fonts_comprehensive(self, url: str, content: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Umfassende Google Fonts DSGVO-Compliance-Analyse"""
        violations = []
        fonts_found = []
        violation_details = []
        total_violations = 0
        
        # 1. Link-Tags Analyse (häufigste Einbindung)
        link_violations = 0
        for link in soup.find_all('link', href=True):
            href = link.get('href', '')
            if any(domain in href for domain in ['fonts.googleapis.com', 'fonts.gstatic.com']):
                link_violations += 1
                total_violations += 1
                
                # Font-Namen extrahieren
                font_families = []
                family_match = re.search(r'family=([^&]+)', href)
                if family_match:
                    families_raw = family_match.group(1)
                    # Multiple families: "Roboto:300,400|Open+Sans:400,600"
                    for family in families_raw.split('|'):
                        font_name = family.split(':')[0].replace('+', ' ')
                        font_families.append(font_name)
                        fonts_found.append(font_name)
                
                violation_details.append({
                    "type": "link_tag",
                    "fonts": font_families,
                    "url": href,
                    "severity": "critical",
                    "description": f"<link> Tag lädt {len(font_families)} Google Font(s) von Google Servern"
                })
                
                violations.append(f"Link-Tag lädt Google Fonts: {', '.join(font_families)}")
        
        # 2. CSS @import Statements
        import_violations = 0
        for style_tag in soup.find_all('style'):
            css_content = style_tag.get_text()
            import_matches = re.findall(r'@import\s+url\(["\']?(https://fonts\.googleapis\.com[^"\']+)["\']?\)', css_content)
            for import_url in import_matches:
                import_violations += 1
                total_violations += 1
                violations.append("CSS @import lädt Google Fonts")
                violation_details.append({
                    "type": "css_import",
                    "url": import_url,
                    "severity": "critical",
                    "description": "CSS @import Statement lädt Google Fonts"
                })
        
        # 3. JavaScript Font-Loader
        js_violations = 0
        js_patterns = [
            r'WebFont\.load',
            r'fonts\.googleapis\.com',
            r'GoogleFonts',
            r'loadGoogleFonts'
        ]
        
        for script in soup.find_all('script'):
            script_content = script.get_text()
            for pattern in js_patterns:
                if re.search(pattern, script_content, re.IGNORECASE):
                    js_violations += 1
                    total_violations += 1
                    violations.append(f"JavaScript lädt Google Fonts ({pattern})")
                    violation_details.append({
                        "type": "javascript_loader",
                        "pattern": pattern,
                        "severity": "critical",
                        "description": f"JavaScript Font-Loader erkannt: {pattern}"
                    })
                    break
        
        # 4. Web Fonts API Calls (aus Script src)
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            if 'fonts.googleapis.com' in src:
                total_violations += 1
                violations.append("Script lädt Google Fonts API")
        
        # Rechtliche Bewertung
        if total_violations == 0:
            return {
                "status": "pass",
                "score": 100,
                "message": "✅ Keine Google Fonts gefunden - DSGVO-konform",
                "total_violations": 0,
                "fonts_found": [],
                "violations": [],
                "violation_details": [],
                "abmahn_risk": "Niedrig",
                "legal_status": "DSGVO-konform",
                "compliance_recommendation": "Weiterhin auf lokale Fonts oder System-Fonts setzen"
            }
        
        # Bei Verstößen: Detaillierte Risikobewertung
        risk_level = self._calculate_google_fonts_risk(total_violations, len(set(fonts_found)))
        cost_estimate = self._estimate_google_fonts_costs(total_violations, risk_level)
        
        return {
            "status": "critical",
            "score": 0,  # Google Fonts = automatisch 0 Punkte
            "message": f"🚨 {total_violations} Google Fonts DSGVO-Verstöße - Kritisches Abmahnrisiko!",
            "total_violations": total_violations,
            "fonts_found": list(set(fonts_found)),
            "violations": violations,
            "violation_details": violation_details,
            "violation_breakdown": {
                "link_tags": link_violations,
                "css_imports": import_violations,
                "javascript_loaders": js_violations
            },
            "abmahn_risk": risk_level,
            "legal_status": "DSGVO-Verstoß durch unerlaubte Datenübermittlung an Google",
            "legal_basis": [
                "Art. 6 DSGVO - Rechtmäßigkeit der Verarbeitung",
                "Art. 44 ff. DSGVO - Übermittlung personenbezogener Daten in Drittländer",
                "§ 25 TTDSG - Speicherung von Informationen in der Endeinrichtung"
            ],
            "case_law": {
                "primary": "LG München I, Urt. v. 20.01.2022 - 3 O 17493/20",
                "description": "Google Fonts ohne Einwilligung = DSGVO-Verstoß",
                "precedent": "IP-Adresse ist personenbezogenes Datum"
            },
            "potential_costs": cost_estimate,
            "immediate_actions": [
                "🚨 SOFORT: Alle Google Fonts <link> Tags aus HTML entfernen",
                "💾 Schriften lokal herunterladen von fonts.google.com",
                "📁 Fonts in /assets/fonts/ oder /static/fonts/ speichern",
                "🔧 @font-face CSS-Regeln für lokale Fonts erstellen",
                "📄 Datenschutzerklärung: Google Fonts Abschnitt komplett entfernen",
                "✅ Nach Änderungen: Sofortige erneute Compliance-Prüfung"
            ],
            "alternatives": [
                "System-Fonts verwenden (Arial, Georgia, Verdana, sans-serif)",
                "Lokale Font-Hosting mit @font-face",
                "Font-Display: swap für bessere Performance",
                "Preload lokaler Font-Dateien für Speed"
            ]
        }

    def _calculate_google_fonts_risk(self, violations: int, unique_fonts: int) -> str:
        """Berechnet Risiko-Level basierend auf Verstößen"""
        if violations == 0:
            return "Niedrig"
        elif violations <= 2 and unique_fonts <= 2:
            return "Mittel"
        elif violations <= 5:
            return "Hoch"
        else:
            return "Sehr Hoch"

    def _estimate_google_fonts_costs(self, violations: int, risk_level: str) -> Dict[str, Any]:
        """Schätzt Abmahnkosten basierend auf aktueller Rechtsprechung"""
        if violations == 0:
            return {"range": "0€", "description": "Keine Verstöße"}
        
        base_costs = {
            "Mittel": {"min": 500, "max": 1500, "typical": 800},
            "Hoch": {"min": 1000, "max": 3000, "typical": 1800},
            "Sehr Hoch": {"min": 2000, "max": 5000, "typical": 3500}
        }
        
        costs = base_costs.get(risk_level, base_costs["Mittel"])
        
        return {
            "range": f"{costs['min']}-{costs['max']}€",
            "typical_case": f"{costs['typical']}€",
            "description": f"Abmahnkosten bei {risk_level.lower()}em Risiko",
            "breakdown": {
                "anwaltskosten": f"{int(costs['typical'] * 0.4)}€",
                "schadensersatz": f"{int(costs['typical'] * 0.3)}€",
                "verfahrenskosten": f"{int(costs['typical'] * 0.3)}€"
            },
            "additional_risks": [
                "DSGVO-Bußgeld durch Aufsichtsbehörde möglich",
                "Weitere Abmahnungen bei wiederholten Verstößen",
                "Reputationsschaden bei öffentlicher Berichterstattung"
            ]
        }

    def _detect_shop_advanced(self, text: str, soup: BeautifulSoup) -> bool:
        """Erweiterte Shop-System-Erkennung"""
        # Text-basierte Erkennung
        shop_keywords = [
            'shop', 'store', 'kaufen', 'bestellen', 'warenkorb', 'cart',
            'versand', 'lieferung', 'agb', 'widerruf', 'rückgabe'
        ]
        text_score = sum(1 for keyword in shop_keywords if keyword in text)
        
        # HTML-Element-basierte Erkennung
        shop_elements = [
            'add-to-cart', 'buy-now', 'checkout', 'payment',
            'product-', 'shop-', 'cart-', 'order-'
        ]
        element_score = 0
        for element in soup.find_all(attrs={'class': True, 'id': True}):
            classes_ids = ' '.join(element.get('class', []) + [element.get('id', '')])
            element_score += sum(1 for shop_elem in shop_elements if shop_elem in classes_ids.lower())
        
        return text_score >= 3 or element_score >= 2

    def _analyze_impressum_enhanced(self, text: str) -> Dict[str, Any]:
        """Erweiterte Impressum-Analyse"""
        required_elements = {
            'impressum': ['impressum', 'imprint'],
            'name': ['name', 'inhaber', 'geschäftsführer'],
            'adresse': ['adresse', 'anschrift', 'straße', 'str.'],
            'kontakt': ['telefon', 'tel.', 'mail', 'email'],
            'ust_id': ['ust-id', 'umsatzsteuer', 'de\\d{9}']
        }
        
        found_elements = {}
        score = 0
        
        for element, patterns in required_elements.items():
            found = False
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    found = True
                    break
            found_elements[element] = found
            if found:
                score += 20
        
        # TMG/TTDSG Check
        tmg_outdated = bool(re.search(r'telemediengesetz', text, re.IGNORECASE))
        if tmg_outdated:
            score = max(score - 15, 0)
        
        issues = []
        if not found_elements.get('impressum'):
            issues.append("Impressum-Seite nicht gefunden")
        if not found_elements.get('name'):
            issues.append("Name/Inhaber fehlt")
        if not found_elements.get('adresse'):
            issues.append("Vollständige Adresse fehlt")
        if not found_elements.get('kontakt'):
            issues.append("Kontaktangaben unvollständig")
        if tmg_outdated:
            issues.append("⚠️ Veralteter TMG-Verweis - TTDSG seit 01.12.2021 erforderlich")
        
        return {
            "status": "pass" if score >= 80 else "warning" if score >= 60 else "fail",
            "score": score,
            "found_elements": found_elements,
            "issues": issues,
            "tmg_outdated": tmg_outdated,
            "erecht24_compliant": score >= 80 and not tmg_outdated
        }

    def _analyze_datenschutz_enhanced(self, text: str) -> Dict[str, Any]:
        """Erweiterte Datenschutz-Analyse"""
        required_sections = {
            'datenschutz': ['datenschutz', 'privacy'],
            'dsgvo': ['dsgvo', 'gdpr'],
            'verantwortlicher': ['verantwortlich', 'controller'],
            'zweck': ['zweck', 'purpose'],
            'rechtsgrundlage': ['rechtsgrundlage', 'art. 6'],
            'betroffenenrechte': ['auskunft', 'berichtigung', 'löschung'],
            'cookies': ['cookie', 'tracking']
        }
        
        found_sections = {}
        score = 0
        
        for section, patterns in required_sections.items():
            found = False
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    found = True
                    break
            found_sections[section] = found
            if found:
                score += 14  # ~100/7 sections
        
        issues = []
        for section, found in found_sections.items():
            if not found:
                issues.append(f"{section.replace('_', ' ').title()} fehlt")
        
        return {
            "status": "pass" if score >= 85 else "warning" if score >= 65 else "fail",
            "score": score,
            "found_sections": found_sections,
            "issues": issues,
            "erecht24_compliant": score >= 85
        }

    def _analyze_cookies_basic(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Basis Cookie-Analyse"""
        # Cookie-Banner erkennen
        cookie_selectors = [
            '[class*="cookie"]', '[id*="cookie"]',
            '[class*="consent"]', '[id*="consent"]'
        ]
        
        cookie_banner_found = False
        for selector in cookie_selectors:
            if soup.select(selector):
                cookie_banner_found = True
                break
        
        # Tracking-Scripts
        tracking_scripts = []
        for script in soup.find_all('script'):
            script_content = script.get_text() + (script.get('src') or '')
            if 'google-analytics' in script_content.lower():
                tracking_scripts.append('Google Analytics')
            if 'gtag' in script_content.lower():
                tracking_scripts.append('Google Tag Manager')
            if 'fbq' in script_content.lower():
                tracking_scripts.append('Facebook Pixel')
        
        compliance_score = 50
        if cookie_banner_found:
            compliance_score += 30
        if not tracking_scripts:
            compliance_score += 20
        
        return {
            "cookie_banner_found": cookie_banner_found,
            "tracking_scripts": list(set(tracking_scripts)),
            "score": compliance_score,
            "status": "pass" if compliance_score >= 80 else "warning"
        }

    def _calculate_weighted_score(self, google_fonts: Dict, impressum: Dict, 
                                 datenschutz: Dict, cookies: Dict, is_shop: bool) -> int:
        """Berechnet gewichteten Gesamtscore mit Google Fonts Fokus"""
        # Google Fonts haben 40% Gewichtung - bei Verstößen = massive Penalty
        google_fonts_score = google_fonts.get("score", 0)
        impressum_score = impressum.get("score", 0)
        datenschutz_score = datenschutz.get("score", 0)
        cookies_score = cookies.get("score", 50)
        
        if is_shop:
            weights = {
                "google_fonts": 0.40,
                "impressum": 0.25,
                "datenschutz": 0.25,
                "cookies": 0.10
            }
        else:
            weights = {
                "google_fonts": 0.40,
                "impressum": 0.30,
                "datenschutz": 0.25,
                "cookies": 0.05
            }
        
        weighted_score = (
            google_fonts_score * weights["google_fonts"] +
            impressum_score * weights["impressum"] +
            datenschutz_score * weights["datenschutz"] +
            cookies_score * weights["cookies"]
        )
        
        return int(weighted_score)

    def _check_erecht24_compatibility_with_fonts(self, google_fonts: Dict, 
                                               impressum: Dict, datenschutz: Dict) -> Dict[str, Any]:
        """eRecht24-Kompatibilität mit Google Fonts Fokus"""
        google_fonts_compliant = google_fonts.get("total_violations", 1) == 0
        impressum_compliant = impressum.get("erecht24_compliant", False)
        datenschutz_compliant = datenschutz.get("erecht24_compliant", False)
        
        overall_compliant = google_fonts_compliant and impressum_compliant and datenschutz_compliant
        
        blocking_issues = []
        if not google_fonts_compliant:
            blocking_issues.append(f"🚨 Google Fonts Verstöße: {google_fonts.get('total_violations', 0)} (KRITISCH)")
        if not impressum_compliant:
            blocking_issues.append("Impressum nicht eRecht24-konform")
        if not datenschutz_compliant:
            blocking_issues.append("Datenschutzerklärung nicht eRecht24-konform")
        
        return {
            "erecht24_compliant": overall_compliant,
            "abmahnschutz_status": "Aktiv (bis 10.000€)" if overall_compliant else "NICHT VERFÜGBAR",
            "abmahnschutz_summe": "bis 10.000€" if overall_compliant else "0€",
            "blocking_issues": blocking_issues,
            "priority_fix": "Google Fonts entfernen" if not google_fonts_compliant else "Weitere Issues beheben",
            "recommendations": [
                "🚨 HÖCHSTE PRIORITÄT: Google Fonts vollständig entfernen" if not google_fonts_compliant else "✅ Google Fonts: OK",
                "eRecht24 Premium für rechtssichere Texte nutzen",
                "Nach Google Fonts Fix: Sofortige Re-Analyse durchführen",
                "Regelmäßige Überwachung auf neue Font-Einbindungen"
            ]
        }

class ComplianceAPIExtended:
    def __init__(self):
        self.engine = EnhancedLegalComplianceEngine()
        logger.info("Compliance API Extended initialized successfully")
    
    async def analyze_website_comprehensive(self, url: str) -> Dict[str, Any]:
        return await self.engine.analyze_website_detailed(url)
