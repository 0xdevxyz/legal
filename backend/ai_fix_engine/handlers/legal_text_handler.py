"""
Legal Text Handler - eRecht24 Integration + AI Fallback

Behandelt Impressum, Datenschutzerklärung, AGB, Widerrufsbelehrung
"""

from typing import Dict, Any, Optional
from datetime import datetime


class LegalTextHandler:
    """Handler für rechtssichere Texte"""
    
    def __init__(self, erecht24_integration=None):
        """
        Args:
            erecht24_integration: Optional eRecht24Integration instance
        """
        self.erecht24 = erecht24_integration
    
    async def handle(
        self,
        issue: Dict[str, Any],
        context: Dict[str, Any],
        ai_generated_fix: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Hauptmethode: Generiert rechtssicheren Text
        
        Priority:
        1. eRecht24 API (falls verfügbar)
        2. AI-generated text (als Fallback)
        3. Template-based text (als letzter Fallback)
        """
        text_type = self._determine_text_type(issue)
        
        # Try eRecht24 first if available
        if self.erecht24:
            erecht24_text = await self._fetch_from_erecht24(
                context.get("erecht24_project_id"),
                text_type,
                context
            )
            
            if erecht24_text:
                return self._build_erecht24_result(
                    erecht24_text,
                    text_type,
                    issue,
                    context
                )
        
        # Fallback to AI-generated
        if ai_generated_fix:
            return self._enrich_ai_fix(ai_generated_fix, text_type, context)
        
        # Last resort: Template
        return self._build_template_result(text_type, issue, context)
    
    def _determine_text_type(self, issue: Dict[str, Any]) -> str:
        """Bestimmt den Text-Typ aus dem Issue"""
        title_lower = issue.get("title", "").lower()
        
        if "impressum" in title_lower:
            return "impressum"
        elif "datenschutz" in title_lower or "privacy" in title_lower:
            return "datenschutz"
        elif "agb" in title_lower or "terms" in title_lower:
            return "agb"
        elif "widerruf" in title_lower:
            return "widerruf"
        else:
            return "generic"
    
    async def _fetch_from_erecht24(
        self,
        project_id: Optional[str],
        text_type: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Holt Text von eRecht24 API"""
        if not self.erecht24 or not project_id:
            return None
        
        try:
            text = await self.erecht24.get_legal_text_with_fallback(
                project_id=project_id,
                text_type=text_type,
                language="de"
            )
            return text
        except Exception as e:
            print(f"eRecht24 fetch failed: {e}")
            return None
    
    def _build_erecht24_result(
        self,
        erecht24_text: str,
        text_type: str,
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Baut Result aus eRecht24-Text"""
        return {
            "fix_id": issue.get("id", f"{text_type}_erecht24"),
            "title": f"Rechtssicherer {text_type.capitalize()} (eRecht24)",
            "description": f"Von eRecht24 generierter, anwaltlich geprüfter {text_type}",
            "text_content": erecht24_text,
            "text_type": text_type,
            "format": "html",
            "source": "erecht24",
            "placeholders": [],
            "integration": {
                "filename": f"{text_type}.html",
                "instructions": self._get_integration_instructions(text_type)
            },
            "estimated_time": "5 Minuten",
            "legal_references": self._get_legal_references(text_type),
            "quality_score": 1.0,  # eRecht24 = höchste Qualität
            "complyo_branding": True
        }
    
    def _enrich_ai_fix(
        self,
        ai_fix: Dict[str, Any],
        text_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reichert AI-generierten Fix an"""
        enriched = ai_fix.copy()
        
        # Add quality indicators
        enriched["source"] = "ai_generated"
        enriched["quality_score"] = 0.85  # AI = gute Qualität
        
        # Add legal disclaimer
        enriched["disclaimer"] = (
            "Dieser Text wurde KI-generiert und sollte von einem Anwalt geprüft werden. "
            "Für rechtssichere Texte empfehlen wir die Nutzung der eRecht24-Integration."
        )
        
        # Ensure legal references
        if "legal_references" not in enriched:
            enriched["legal_references"] = self._get_legal_references(text_type)
        
        # Ensure integration instructions
        if "integration" not in enriched or not enriched["integration"].get("instructions"):
            if "integration" not in enriched:
                enriched["integration"] = {}
            enriched["integration"]["instructions"] = self._get_integration_instructions(text_type)
        
        return enriched
    
    def _build_template_result(
        self,
        text_type: str,
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Baut Template-basierten Fallback"""
        company = context.get("company", {})
        
        templates = {
            "impressum": self._get_impressum_template(company),
            "datenschutz": self._get_datenschutz_template(company, context),
            "agb": self._get_agb_template(company),
            "widerruf": self._get_widerruf_template(company)
        }
        
        template_text = templates.get(text_type, "<p>Bitte ergänzen Sie den rechtssicheren Text.</p>")
        
        return {
            "fix_id": issue.get("id", f"{text_type}_template"),
            "title": f"Template: {text_type.capitalize()}",
            "description": f"Basis-Template für {text_type} - muss angepasst werden",
            "text_content": template_text,
            "text_type": text_type,
            "format": "html",
            "source": "template",
            "placeholders": self._extract_placeholders(template_text),
            "integration": {
                "filename": f"{text_type}.html",
                "instructions": self._get_integration_instructions(text_type)
            },
            "estimated_time": "15-20 Minuten",
            "legal_references": self._get_legal_references(text_type),
            "quality_score": 0.6,  # Template = Basis-Qualität
            "disclaimer": "Dies ist ein Basis-Template. Bitte passen Sie es an Ihre Bedürfnisse an und lassen Sie es rechtlich prüfen."
        }
    
    def _get_impressum_template(self, company: Dict[str, Any]) -> str:
        """Template für Impressum"""
        name = company.get("name") or "[FIRMENNAME]"
        address = company.get("address") or "[ADRESSE]"
        email = company.get("email") or "[EMAIL]"
        phone = company.get("phone") or "[TELEFON]"
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Impressum</title>
</head>
<body>
    <h1>Impressum</h1>
    
    <h2>Angaben gemäß § 5 TMG</h2>
    <p>
        <strong>{name}</strong><br>
        {address}<br>
    </p>
    
    <h2>Kontakt</h2>
    <p>
        Telefon: {phone}<br>
        E-Mail: {email}
    </p>
    
    <h2>Handelsregister</h2>
    <p>
        Registergericht: [REGISTERGERICHT]<br>
        Registernummer: [HRB/HRA NUMMER]
    </p>
    
    <h2>Umsatzsteuer-ID</h2>
    <p>
        Umsatzsteuer-Identifikationsnummer gemäß §27a Umsatzsteuergesetz:<br>
        [UST-ID]
    </p>
    
    <h2>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h2>
    <p>
        [VERANTWORTLICHE PERSON]<br>
        {address}
    </p>
    
    <p><small>Erstellt mit Complyo.tech</small></p>
</body>
</html>"""
    
    def _get_datenschutz_template(self, company: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Template für Datenschutzerklärung"""
        name = company.get("name") or "[FIRMENNAME]"
        email = company.get("email") or "[EMAIL]"
        url = context.get("url", "[IHRE-WEBSITE.DE]")
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Datenschutzerklärung</title>
</head>
<body>
    <h1>Datenschutzerklärung</h1>
    
    <h2>1. Datenschutz auf einen Blick</h2>
    <h3>Allgemeine Hinweise</h3>
    <p>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen.</p>
    
    <h3>Wer ist verantwortlich für die Datenerfassung auf dieser Website?</h3>
    <p>
        Verantwortlicher: {name}<br>
        E-Mail: {email}
    </p>
    
    <h2>2. Hosting</h2>
    <p>Diese Website wird bei [HOSTING-ANBIETER] gehostet.</p>
    
    <h2>3. Allgemeine Hinweise und Pflichtinformationen</h2>
    <h3>Datenschutz</h3>
    <p>Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Wir behandeln Ihre personenbezogenen Daten vertraulich und entsprechend den gesetzlichen Datenschutzvorschriften sowie dieser Datenschutzerklärung.</p>
    
    <h2>4. Datenerfassung auf dieser Website</h2>
    <h3>Server-Log-Dateien</h3>
    <p>Der Provider der Seiten erhebt und speichert automatisch Informationen in so genannten Server-Log-Dateien.</p>
    
    <h2>5. Ihre Rechte</h2>
    <p>Sie haben folgende Rechte:</p>
    <ul>
        <li>Recht auf Auskunft (Art. 15 DSGVO)</li>
        <li>Recht auf Berichtigung (Art. 16 DSGVO)</li>
        <li>Recht auf Löschung (Art. 17 DSGVO)</li>
        <li>Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO)</li>
        <li>Recht auf Datenübertragbarkeit (Art. 20 DSGVO)</li>
        <li>Widerspruchsrecht (Art. 21 DSGVO)</li>
        <li>Recht auf Beschwerde bei einer Aufsichtsbehörde (Art. 77 DSGVO)</li>
    </ul>
    
    <p><strong>Stand:</strong> {datetime.now().strftime("%d.%m.%Y")}</p>
    <p><small>Erstellt mit Complyo.tech</small></p>
</body>
</html>"""
    
    def _get_agb_template(self, company: Dict[str, Any]) -> str:
        """Template für AGB"""
        name = company.get("name") or "[FIRMENNAME]"
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Allgemeine Geschäftsbedingungen (AGB)</title>
</head>
<body>
    <h1>Allgemeine Geschäftsbedingungen (AGB)</h1>
    
    <h2>§ 1 Geltungsbereich</h2>
    <p>Diese Allgemeinen Geschäftsbedingungen gelten für alle Verträge zwischen {name} und dem Kunden.</p>
    
    <h2>§ 2 Vertragsschluss</h2>
    <p>[VERTRAGSSCHLUSS BESCHREIBEN]</p>
    
    <h2>§ 3 Preise und Zahlung</h2>
    <p>[PREISE UND ZAHLUNGSBEDINGUNGEN]</p>
    
    <h2>§ 4 Lieferung</h2>
    <p>[LIEFERBEDINGUNGEN]</p>
    
    <h2>§ 5 Widerrufsrecht</h2>
    <p>[WIDERRUFSRECHT FÜR VERBRAUCHER]</p>
    
    <p><strong>Stand:</strong> {datetime.now().strftime("%d.%m.%Y")}</p>
    <p><small>Erstellt mit Complyo.tech - Bitte rechtlich prüfen lassen!</small></p>
</body>
</html>"""
    
    def _get_widerruf_template(self, company: Dict[str, Any]) -> str:
        """Template für Widerrufsbelehrung"""
        name = company.get("name") or "[FIRMENNAME]"
        address = company.get("address") or "[ADRESSE]"
        email = company.get("email") or "[EMAIL]"
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Widerrufsbelehrung</title>
</head>
<body>
    <h1>Widerrufsbelehrung</h1>
    
    <h2>Widerrufsrecht</h2>
    <p>Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen.</p>
    
    <p>Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag, an dem Sie oder ein von Ihnen benannter Dritter, der nicht der Beförderer ist, die Waren in Besitz genommen haben bzw. hat.</p>
    
    <p>Um Ihr Widerrufsrecht auszuüben, müssen Sie uns:</p>
    <p>
        {name}<br>
        {address}<br>
        E-Mail: {email}
    </p>
    
    <p>mittels einer eindeutigen Erklärung (z.B. ein mit der Post versandter Brief oder E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren.</p>
    
    <h2>Folgen des Widerrufs</h2>
    <p>Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist.</p>
    
    <p><small>Erstellt mit Complyo.tech</small></p>
</body>
</html>"""
    
    def _get_integration_instructions(self, text_type: str) -> str:
        """Gibt Integrations-Anweisungen für Text-Typ"""
        instructions = {
            "impressum": """1. Datei 'impressum.html' im Root-Verzeichnis erstellen
2. Text einfügen und Platzhalter durch echte Daten ersetzen
3. Im Footer jeder Seite verlinken: <a href="/impressum.html">Impressum</a>
4. Link muss von jeder Seite aus erreichbar sein
5. Testen Sie die Erreichbarkeit""",
            
            "datenschutz": """1. Datei 'datenschutz.html' erstellen
2. Text einfügen und an Ihre Datenverarbeitung anpassen
3. Im Footer verlinken: <a href="/datenschutz.html">Datenschutz</a>
4. Bei Änderungen der Datenverarbeitung aktualisieren
5. Versionierung empfohlen (Datum der letzten Änderung)""",
            
            "agb": """1. Datei 'agb.html' erstellen
2. Text an Ihr Geschäftsmodell anpassen
3. Rechtlich prüfen lassen!
4. Im Footer und bei Bestellprozess verlinken
5. Kunde muss vor Vertragsschluss darauf hingewiesen werden""",
            
            "widerruf": """1. Datei 'widerruf.html' erstellen
2. Text anpassen (gilt nur für Verbraucher im Fernabsatz)
3. Im Footer und bei Bestellbestätigung verlinken
4. Muster-Widerrufsformular bereitstellen"""
        }
        
        return instructions.get(text_type, "Datei erstellen und im Footer verlinken")
    
    def _get_legal_references(self, text_type: str) -> List[str]:
        """Gibt rechtliche Referenzen für Text-Typ"""
        references = {
            "impressum": ["§ 5 TMG", "§ 55 RStV"],
            "datenschutz": ["Art. 13 DSGVO", "Art. 15 DSGVO", "§ 25 TTDSG"],
            "agb": ["§§ 305 ff. BGB"],
            "widerruf": ["§ 355 BGB", "Art. 246a § 1 EGBGB"]
        }
        
        return references.get(text_type, [])
    
    def _extract_placeholders(self, text: str) -> List[str]:
        """Extrahiert Platzhalter aus Text"""
        import re
        placeholders = []
        
        # Pattern für [PLATZHALTER]
        bracket_placeholders = re.findall(r'\[([A-ZÄÖÜ\s_-]+)\]', text)
        placeholders.extend([f"[{p}]" for p in bracket_placeholders])
        
        return list(set(placeholders))


