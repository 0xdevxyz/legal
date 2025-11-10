"""
AI Document Generator für Complyo Expert Plan
Generiert vollständige rechtssichere Dokumente mit OpenRouter/Claude
"""

import aiohttp
import asyncpg
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AIDocumentGenerator:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet"  # Best model for legal documents
        
        if not self.openrouter_api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY not set - AI document generation disabled")
    
    async def generate_impressum_document(
        self, 
        user_id: int,
        company_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generiert vollständiges Impressum gemäß §5 TMG
        
        Args:
            user_id: User ID für Audit-Trail
            company_data: Firmendaten (Name, Adresse, USt-ID, etc.)
        
        Returns:
            Dict mit HTML, Audit-Trail und Metadaten
        """
        prompt = self._build_impressum_prompt(company_data)
        
        try:
            ai_response = await self._call_openrouter(prompt)
            
            html_content = ai_response['content']
            
            # Audit-Trail erstellen
            audit_trail = {
                'generated_at': datetime.now().isoformat(),
                'user_id': user_id,
                'document_type': 'impressum',
                'legal_basis': '§5 TMG',
                'ai_model': self.model,
                'version': '1.0',
                'company_data_hash': self._hash_company_data(company_data)
            }
            
            # Speichere in Datenbank
            doc_id = await self._save_document(
                user_id=user_id,
                doc_type='impressum',
                content=html_content,
                audit_trail=audit_trail
            )
            
            return {
                'type': 'full_document',
                'format': 'html',
                'html': html_content,
                'document_id': doc_id,
                'audit_trail': audit_trail,
                'download_url': f'/api/v2/documents/{doc_id}/download',
                'legal_note': 'Dieses Impressum wurde KI-gestützt generiert und basiert auf §5 TMG. Bitte prüfen Sie alle Angaben auf Richtigkeit.'
            }
            
        except Exception as e:
            logger.error(f"Error generating impressum: {e}")
            # Fallback zu Template
            return self._get_impressum_template(company_data)
    
    async def generate_datenschutz_document(
        self,
        user_id: int,
        company_data: Dict[str, str],
        services_used: list
    ) -> Dict[str, Any]:
        """
        Generiert vollständige Datenschutzerklärung gemäß DSGVO Art. 13-14
        """
        prompt = self._build_datenschutz_prompt(company_data, services_used)
        
        try:
            ai_response = await self._call_openrouter(prompt)
            
            html_content = ai_response['content']
            
            audit_trail = {
                'generated_at': datetime.now().isoformat(),
                'user_id': user_id,
                'document_type': 'datenschutz',
                'legal_basis': 'DSGVO Art. 13-14',
                'ai_model': self.model,
                'version': '1.0',
                'services': services_used
            }
            
            doc_id = await self._save_document(
                user_id=user_id,
                doc_type='datenschutz',
                content=html_content,
                audit_trail=audit_trail
            )
            
            return {
                'type': 'full_document',
                'format': 'html',
                'html': html_content,
                'document_id': doc_id,
                'audit_trail': audit_trail,
                'download_url': f'/api/v2/documents/{doc_id}/download',
                'legal_note': 'Diese Datenschutzerklärung wurde KI-gestützt generiert gemäß DSGVO. Bei Änderungen an Diensten muss das Dokument aktualisiert werden.'
            }
            
        except Exception as e:
            logger.error(f"Error generating datenschutz: {e}")
            return self._get_datenschutz_template(company_data)
    
    async def _call_openrouter(self, prompt: str) -> Dict[str, Any]:
        """Ruft OpenRouter API auf"""
        if not self.openrouter_api_key:
            raise Exception("OpenRouter API Key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://complyo.tech",
            "X-Title": "Complyo Compliance Platform"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Experte für deutsches Compliance-Recht. Generiere vollständige, rechtssichere Dokumente in HTML-Format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Niedrig für konsistente rechtliche Texte
            "max_tokens": 4000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.openrouter_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API Error: {response.status} - {error_text}")
                
                data = await response.json()
                
                return {
                    'content': data['choices'][0]['message']['content'],
                    'model': data['model'],
                    'tokens_used': data.get('usage', {})
                }
    
    def _build_impressum_prompt(self, company_data: Dict[str, str]) -> str:
        """Erstellt Prompt für Impressum-Generierung"""
        return f"""
Generiere ein vollständiges, rechtssicheres Impressum gemäß §5 TMG für folgende Firma:

Firmendaten:
- Name: {company_data.get('company_name', '[FIRMENNAME]')}
- Rechtsform: {company_data.get('legal_form', 'Einzelunternehmen')}
- Straße: {company_data.get('street', '[STRASSE]')}
- PLZ/Ort: {company_data.get('zip_city', '[PLZ ORT]')}
- Telefon: {company_data.get('phone', '[TELEFON]')}
- E-Mail: {company_data.get('email', '[E-MAIL]')}
- USt-IdNr.: {company_data.get('vat_id', '[UST-IDNR]')}
- Vertreten durch: {company_data.get('represented_by', '[INHABER]')}

Anforderungen:
1. Vollständiges HTML-Dokument mit semantischen Tags
2. Alle Pflichtangaben nach §5 TMG müssen enthalten sein
3. Professionelles, sauberes Layout
4. Barrierefreie Struktur (h1, h2, p Tags)
5. Keine Platzhalter - nutze die angegebenen Daten

Formatierung:
- Nutze <h1> für "Impressum"
- Nutze <h2> für Abschnitte (z.B. "Angaben gemäß § 5 TMG")
- Nutze <p> für Absätze
- Keine CSS-Styles inline

Beginne direkt mit dem HTML-Code (ohne Markdown).
"""
    
    def _build_datenschutz_prompt(
        self, 
        company_data: Dict[str, str],
        services_used: list
    ) -> str:
        """Erstellt Prompt für Datenschutzerklärung"""
        services_str = ", ".join(services_used) if services_used else "Keine externen Dienste"
        
        return f"""
Generiere eine vollständige, rechtssichere Datenschutzerklärung gemäß DSGVO Art. 13-14 für:

Firmendaten:
- Name: {company_data.get('company_name', '[FIRMENNAME]')}
- Adresse: {company_data.get('street', '[STRASSE]')}, {company_data.get('zip_city', '[PLZ ORT]')}
- E-Mail: {company_data.get('email', '[E-MAIL]')}

Genutzte Dienste: {services_str}

Anforderungen:
1. Vollständiges HTML-Dokument
2. Alle DSGVO-Pflichtangaben (Art. 13-14)
3. Abschnitte:
   - Verantwortlicher
   - Art der verarbeiteten Daten
   - Zweck der Datenverarbeitung
   - Rechtsgrundlage
   - Speicherdauer
   - Betroffenenrechte
   - Widerrufsrecht
   - Beschwerderecht
   - Datenübermittlung Drittländer (falls zutreffend)
4. Für jeden genutzten Dienst separate Erklärung
5. Barrierefreie Struktur

Formatierung wie Impressum.
Beginne direkt mit dem HTML-Code.
"""
    
    def _hash_company_data(self, data: Dict[str, str]) -> str:
        """Erstellt Hash der Firmendaten für Audit-Trail"""
        import hashlib
        import json
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def _save_document(
        self,
        user_id: int,
        doc_type: str,
        content: str,
        audit_trail: Dict[str, Any]
    ) -> int:
        """Speichert generiertes Dokument in Datenbank"""
        import json
        
        async with self.db_pool.acquire() as conn:
            doc_id = await conn.fetchval(
                """
                INSERT INTO generated_documents 
                (user_id, doc_type, content, audit_trail, created_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                user_id,
                doc_type,
                content,
                json.dumps(audit_trail)
            )
            
            return doc_id
    
    def _get_impressum_template(self, company_data: Dict[str, str]) -> Dict[str, Any]:
        """Fallback Template wenn KI nicht verfügbar"""
        html = f"""
<h1>Impressum</h1>

<h2>Angaben gemäß § 5 TMG</h2>
<p>
  {company_data.get('company_name', '[Ihr Firmenname]')}<br>
  {company_data.get('street', '[Straße und Hausnummer]')}<br>
  {company_data.get('zip_city', '[PLZ und Ort]')}
</p>

<h2>Kontakt</h2>
<p>
  Telefon: {company_data.get('phone', '[Ihre Telefonnummer]')}<br>
  E-Mail: {company_data.get('email', '[Ihre E-Mail-Adresse]')}
</p>

<h2>Umsatzsteuer-ID</h2>
<p>
  Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br>
  {company_data.get('vat_id', '[Ihre USt-IdNr.]')}
</p>

<h2>Vertreten durch</h2>
<p>{company_data.get('represented_by', '[Name des Inhabers/Geschäftsführers]')}</p>
"""
        
        return {
            'type': 'full_document',
            'format': 'html',
            'html': html,
            'document_id': None,
            'audit_trail': {
                'generated_at': datetime.now().isoformat(),
                'type': 'template_fallback',
                'note': 'KI-Generierung nicht verfügbar - Template verwendet'
            },
            'legal_note': 'Dies ist ein Basis-Template. Bitte ergänzen Sie alle fehlenden Angaben.'
        }
    
    def _get_datenschutz_template(self, company_data: Dict[str, str]) -> Dict[str, Any]:
        """Fallback Template für Datenschutzerklärung"""
        html = f"""
<h1>Datenschutzerklärung</h1>

<h2>1. Datenschutz auf einen Blick</h2>
<p>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen.</p>

<h2>2. Verantwortlicher</h2>
<p>
  Verantwortlich für die Datenverarbeitung auf dieser Website ist:<br><br>
  {company_data.get('company_name', '[Ihr Firmenname]')}<br>
  {company_data.get('street', '[Ihre Adresse]')}<br>
  {company_data.get('zip_city', '[PLZ Ort]')}<br>
  E-Mail: {company_data.get('email', '[Ihre E-Mail]')}
</p>

<h2>3. Erfassung von Daten</h2>
<h3>Server-Log-Dateien</h3>
<p>Der Provider der Seiten erhebt und speichert automatisch Informationen in Server-Log-Dateien.</p>

<h2>4. Ihre Rechte</h2>
<p>Sie haben jederzeit das Recht auf Auskunft, Berichtigung, Löschung oder Einschränkung der Verarbeitung Ihrer gespeicherten Daten.</p>
"""
        
        return {
            'type': 'full_document',
            'format': 'html',
            'html': html,
            'document_id': None,
            'audit_trail': {
                'generated_at': datetime.now().isoformat(),
                'type': 'template_fallback'
            },
            'legal_note': 'Basis-Template. Bitte vollständig anpassen.'
        }

