from typing import Dict, List, Any, Optional
import requests
import json
from datetime import datetime, timedelta
import re
from dataclasses import dataclass

@dataclass
class LegalTemplate:
    """erecht24 Rechtstext-Template"""
    template_id: str
    title: str
    content: str
    last_updated: datetime
    legal_basis: List[str]
    compliance_level: str
    category: str

class Erecht24Service:
    """erecht24 Rechtsdatenbank Service für Guard4Web"""
    
    def __init__(self):
        self.legal_database = self._initialize_legal_database()
        self.compliance_rules = self._load_compliance_rules()
        self.legal_templates = self._load_legal_templates()
        self.abmahn_protection_db = self._load_abmahn_database()
        
    def _initialize_legal_database(self) -> Dict[str, Any]:
        """Initialisiert die erecht24 Rechtsdatenbank"""
        return {
            'dsgvo_requirements': {
                'cookie_consent': {
                    'required': True,
                    'legal_basis': 'Art. 6 Abs. 1 lit. a DSGVO',
                    'implementation': 'Opt-in Cookie-Banner mit granularer Auswahl',
                    'penalties': 'Bis zu 20 Mio. EUR oder 4% des Jahresumsatzes',
                    'erecht24_template': 'cookie_consent_2024'
                },
                'privacy_policy': {
                    'required': True,
                    'legal_basis': 'Art. 13, 14 DSGVO',
                    'content_requirements': [
                        'Verantwortlicher (Art. 13 Abs. 1 lit. a)',
                        'Kontaktdaten Datenschutzbeauftragter',
                        'Zwecke und Rechtsgrundlagen (Art. 13 Abs. 1 lit. c)',
                        'Berechtigte Interessen (Art. 13 Abs. 1 lit. d)',
                        'Empfänger oder Kategorien (Art. 13 Abs. 1 lit. e)',
                        'Drittlandübermittlung (Art. 13 Abs. 1 lit. f)',
                        'Speicherdauer (Art. 13 Abs. 2 lit. a)',
                        'Betroffenenrechte (Art. 13 Abs. 2 lit. b)',
                        'Widerrufsrecht (Art. 13 Abs. 2 lit. c)',
                        'Beschwerderecht (Art. 13 Abs. 2 lit. d)',
                        'Automatisierte Entscheidungsfindung (Art. 13 Abs. 2 lit. f)'
                    ],
                    'erecht24_template': 'privacy_policy_2024'
                },
                'imprint': {
                    'required': True,
                    'legal_basis': '§ 5 TMG, § 55 RStV',
                    'content_requirements': [
                        'Name und Anschrift des Diensteanbieters',
                        'Kontaktdaten (Telefon, E-Mail)',
                        'Handelsregister und Registernummer',
                        'Umsatzsteuer-ID',
                        'Aufsichtsbehörde',
                        'Berufsbezeichnung und Kammer',
                        'Berufsrechtliche Regelungen'
                    ],
                    'erecht24_template': 'imprint_2024'
                }
            },
            'tmg_requirements': {
                'hosting_liability': {
                    'legal_basis': '§ 7 TMG',
                    'description': 'Haftung für eigene Informationen',
                    'compliance_check': 'content_responsibility'
                },
                'caching_liability': {
                    'legal_basis': '§ 9 TMG',
                    'description': 'Haftung für zwischengespeicherte Informationen'
                }
            },
            'accessibility_requirements': {
                'bfsg_compliance': {
                    'legal_basis': 'BFSG (Barrierefreiheitsstärkungsgesetz)',
                    'effective_date': '2025-06-28',
                    'requirements': [
                        'WCAG 2.1 Level AA Konformität',
                        'Barrierefreiheitserklärung',
                        'Feedback-Mechanismus',
                        'Alternative Zugangswege'
                    ],
                    'penalties': 'Bis zu 100.000 EUR Bußgeld'
                }
            }
        }
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Lädt erecht24 Compliance-Regeln"""
        return {
            'website_types': {
                'e_commerce': {
                    'required_pages': ['imprint', 'privacy_policy', 'terms', 'cancellation_policy'],
                    'additional_requirements': ['price_indication', 'delivery_terms', 'payment_methods'],
                    'legal_basis': ['BGB', 'DSGVO', 'TMG', 'PAngV']
                },
                'corporate': {
                    'required_pages': ['imprint', 'privacy_policy'],
                    'additional_requirements': ['contact_form_consent'],
                    'legal_basis': ['DSGVO', 'TMG']
                },
                'blog': {
                    'required_pages': ['imprint', 'privacy_policy'],
                    'additional_requirements': ['comment_policy', 'social_media_plugins'],
                    'legal_basis': ['DSGVO', 'TMG', 'UrhG']
                }
            },
            'risk_assessment': {
                'high_risk': {
                    'criteria': ['payment_processing', 'user_data_collection', 'newsletter'],
                    'abmahn_probability': 0.8,
                    'recommended_protection': '5000_euro_package'
                },
                'medium_risk': {
                    'criteria': ['contact_forms', 'analytics', 'social_media'],
                    'abmahn_probability': 0.4,
                    'recommended_protection': '2500_euro_package'
                },
                'low_risk': {
                    'criteria': ['static_content', 'minimal_tracking'],
                    'abmahn_probability': 0.1,
                    'recommended_protection': '1000_euro_package'
                }
            }
        }
    
    def _load_legal_templates(self) -> Dict[str, LegalTemplate]:
        """Lädt erecht24 Rechtstext-Templates"""
        templates = {}
        
        # DSGVO-konforme Datenschutzerklärung
        templates['privacy_policy_2024'] = LegalTemplate(
            template_id='privacy_policy_2024',
            title='DSGVO-konforme Datenschutzerklärung',
            content=self._get_privacy_policy_template(),
            last_updated=datetime(2024, 1, 1),
            legal_basis=['Art. 13 DSGVO', 'Art. 14 DSGVO'],
            compliance_level='full',
            category='privacy'
        )
        
        # TMG-konformes Impressum
        templates['imprint_2024'] = LegalTemplate(
            template_id='imprint_2024',
            title='TMG-konformes Impressum',
            content=self._get_imprint_template(),
            last_updated=datetime(2024, 1, 1),
            legal_basis=['§ 5 TMG', '§ 55 RStV'],
            compliance_level='full',
            category='imprint'
        )
        
        # Cookie-Consent Template
        templates['cookie_consent_2024'] = LegalTemplate(
            template_id='cookie_consent_2024',
            title='DSGVO-konformer Cookie-Consent',
            content=self._get_cookie_consent_template(),
            last_updated=datetime(2024, 1, 1),
            legal_basis=['Art. 6 Abs. 1 lit. a DSGVO'],
            compliance_level='full',
            category='cookies'
        )
        
        return templates
    
    def _load_abmahn_database(self) -> Dict[str, Any]:
        """Lädt Abmahn-Schutz Datenbank"""
        return {
            'common_violations': {
                'missing_imprint': {
                    'frequency': 'sehr häufig',
                    'average_cost': 800,
                    'legal_basis': '§ 5 TMG',
                    'prevention': 'Vollständiges Impressum nach TMG'
                },
                'invalid_privacy_policy': {
                    'frequency': 'häufig',
                    'average_cost': 1200,
                    'legal_basis': 'Art. 13 DSGVO',
                    'prevention': 'DSGVO-konforme Datenschutzerklärung'
                },
                'missing_cookie_consent': {
                    'frequency': 'sehr häufig',
                    'average_cost': 1000,
                    'legal_basis': 'Art. 6 DSGVO',
                    'prevention': 'Opt-in Cookie-Banner'
                },
                'accessibility_violations': {
                    'frequency': 'zunehmend',
                    'average_cost': 2000,
                    'legal_basis': 'BFSG',
                    'prevention': 'WCAG 2.1 Konformität'
                }
            },
            'protection_packages': {
                'basic': {
                    'coverage': 1000,
                    'monthly_cost': 29,
                    'included_violations': ['imprint', 'basic_privacy']
                },
                'standard': {
                    'coverage': 2500,
                    'monthly_cost': 49,
                    'included_violations': ['imprint', 'privacy_policy', 'cookies']
                },
                'premium': {
                    'coverage': 5000,
                    'monthly_cost': 99,
                    'included_violations': ['all_violations', 'accessibility', 'e_commerce']
                }
            }
        }
    
    def analyze_legal_compliance(self, website_data: Dict[str, Any]) -> Dict[str, Any]:
        """Führt umfassende Rechtsanalyse durch"""
        
        compliance_report = {
            'overall_score': 0,
            'risk_level': 'unknown',
            'violations': [],
            'recommendations': [],
            'abmahn_risk': 0,
            'estimated_costs': 0,
            'legal_texts_needed': [],
            'erecht24_templates': []
        }
        
        # DSGVO Compliance prüfen
        dsgvo_score = self._check_dsgvo_compliance(website_data)
        compliance_report['dsgvo_score'] = dsgvo_score
        
        # TMG Compliance prüfen
        tmg_score = self._check_tmg_compliance(website_data)
        compliance_report['tmg_score'] = tmg_score
        
        # Barrierefreiheit prüfen
        accessibility_score = self._check_accessibility_compliance(website_data)
        compliance_report['accessibility_score'] = accessibility_score
        
        # Gesamtscore berechnen
        compliance_report['overall_score'] = (dsgvo_score + tmg_score + accessibility_score) / 3
        
        # Risikobewertung
        compliance_report['risk_level'] = self._assess_risk_level(compliance_report['overall_score'])
        compliance_report['abmahn_risk'] = self._calculate_abmahn_risk(website_data)
        
        # Empfehlungen generieren
        compliance_report['recommendations'] = self._generate_recommendations(website_data, compliance_report)
        
        return compliance_report
    
    def _check_dsgvo_compliance(self, website_data: Dict[str, Any]) -> float:
        """Prüft DSGVO-Konformität"""
        score = 0
        max_score = 100
        
        # Cookie-Consent prüfen
        cookie_data = website_data.get('CookieConsentCheck', {})
        if cookie_data.get('has_cookie_banner', False):
            score += 25
        if cookie_data.get('has_cmp', False):
            score += 15
        if cookie_data.get('granular_consent', False):
            score += 10
        
        # Datenschutzerklärung prüfen
        privacy_data = website_data.get('PrivacyPolicyCheck', {})
        if privacy_data.get('has_privacy_policy', False):
            score += 20
        if privacy_data.get('score', 0) >= 80:
            score += 20
        
        # Weitere DSGVO-Anforderungen
        if website_data.get('has_contact_form', False):
            if website_data.get('contact_form_consent', False):
                score += 10
        
        return min(score, max_score)
    
    def _check_tmg_compliance(self, website_data: Dict[str, Any]) -> float:
        """Prüft TMG-Konformität"""
        score = 0
        max_score = 100
        
        # Impressum prüfen
        if website_data.get('has_imprint', False):
            score += 50
            
            # Impressum-Qualität bewerten
            imprint_score = website_data.get('imprint_score', 0)
            score += (imprint_score / 100) * 50
        
        return min(score, max_score)
    
    def _check_accessibility_compliance(self, website_data: Dict[str, Any]) -> float:
        """Prüft Barrierefreiheit (BFSG/WCAG)"""
        accessibility_data = website_data.get('AccessibilityCheck', {})
        return accessibility_data.get('score', 0)
    
    def _assess_risk_level(self, overall_score: float) -> str:
        """Bewertet Risiko-Level"""
        if overall_score >= 90:
            return 'low'
        elif overall_score >= 70:
            return 'medium'
        elif overall_score >= 50:
            return 'high'
        else:
            return 'critical'
    
    def _calculate_abmahn_risk(self, website_data: Dict[str, Any]) -> float:
        """Berechnet Abmahnrisiko"""
        risk_factors = {
            'missing_imprint': 0.3,
            'invalid_privacy_policy': 0.25,
            'missing_cookie_consent': 0.2,
            'accessibility_issues': 0.15,
            'e_commerce_violations': 0.1
        }
        
        total_risk = 0
        
        # Impressum fehlt
        if not website_data.get('has_imprint', False):
            total_risk += risk_factors['missing_imprint']
        
        # Datenschutzerklärung mangelhaft
        privacy_score = website_data.get('PrivacyPolicyCheck', {}).get('score', 0)
        if privacy_score < 70:
            total_risk += risk_factors['invalid_privacy_policy']
        
        # Cookie-Consent fehlt
        if not website_data.get('CookieConsentCheck', {}).get('has_cookie_banner', False):
            total_risk += risk_factors['missing_cookie_consent']
        
        # Barrierefreiheit
        accessibility_score = website_data.get('AccessibilityCheck', {}).get('score', 0)
        if accessibility_score < 60:
            total_risk += risk_factors['accessibility_issues']
        
        return min(total_risk, 1.0)
    
    def _generate_recommendations(self, website_data: Dict[str, Any], compliance_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generiert erecht24-basierte Empfehlungen"""
        recommendations = []
        
        # Impressum-Empfehlungen
        if not website_data.get('has_imprint', False):
            recommendations.append({
                'priority': 'critical',
                'title': 'Impressum erstellen',
                'description': 'Rechtlich vollständiges Impressum nach § 5 TMG erforderlich',
                'legal_basis': '§ 5 TMG',
                'erecht24_template': 'imprint_2024',
                'estimated_cost_if_violated': 800,
                'implementation_effort': 'low'
            })
        
        # Datenschutz-Empfehlungen
        privacy_score = website_data.get('PrivacyPolicyCheck', {}).get('score', 0)
        if privacy_score < 80:
            recommendations.append({
                'priority': 'high',
                'title': 'Datenschutzerklärung optimieren',
                'description': 'DSGVO-konforme Datenschutzerklärung mit allen erforderlichen Angaben',
                'legal_basis': 'Art. 13, 14 DSGVO',
                'erecht24_template': 'privacy_policy_2024',
                'estimated_cost_if_violated': 1200,
                'implementation_effort': 'medium'
            })
        
        # Cookie-Consent Empfehlungen
        if not website_data.get('CookieConsentCheck', {}).get('has_cookie_banner', False):
            recommendations.append({
                'priority': 'high',
                'title': 'Cookie-Consent implementieren',
                'description': 'Opt-in Cookie-Banner mit granularer Auswahl erforderlich',
                'legal_basis': 'Art. 6 Abs. 1 lit. a DSGVO',
                'erecht24_template': 'cookie_consent_2024',
                'estimated_cost_if_violated': 1000,
                'implementation_effort': 'medium'
            })
        
        # Barrierefreiheit-Empfehlungen
        accessibility_score = website_data.get('AccessibilityCheck', {}).get('score', 0)
        if accessibility_score < 70:
            recommendations.append({
                'priority': 'medium',
                'title': 'Barrierefreiheit verbessern',
                'description': 'WCAG 2.1 Level AA Konformität für BFSG-Compliance',
                'legal_basis': 'BFSG',
                'erecht24_template': 'accessibility_statement_2024',
                'estimated_cost_if_violated': 2000,
                'implementation_effort': 'high'
            })
        
        return recommendations
    
    def _get_privacy_policy_template(self) -> str:
        """erecht24 Datenschutzerklärung Template"""
        return """
# Datenschutzerklärung

## 1. Datenschutz auf einen Blick

### Allgemeine Hinweise
Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen.

### Datenerfassung auf dieser Website
**Wer ist verantwortlich für die Datenerfassung auf dieser Website?**
Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber.

## 2. Hosting

### Externes Hosting
Diese Website wird bei einem externen Dienstleister gehostet (Hoster). Die personenbezogenen Daten, die auf dieser Website erfasst werden, werden auf den Servern des Hosters gespeichert.

## 3. Allgemeine Hinweise und Pflichtinformationen

### Datenschutz
Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Wir behandeln Ihre personenbezogenen Daten vertraulich und entsprechend den gesetzlichen Datenschutzvorschriften sowie dieser Datenschutzerklärung.

### Hinweis zur verantwortlichen Stelle
Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:

[UNTERNEHMEN]
[ADRESSE]
[KONTAKTDATEN]

### Speicherdauer
Soweit innerhalb dieser Datenschutzerklärung keine speziellere Speicherdauer genannt wurde, verbleiben Ihre personenbezogenen Daten bei uns, bis der Zweck für die Datenverarbeitung entfällt.

### Gesetzlich vorgeschriebene Datenverarbeitungen
Wir weisen darauf hin, dass die Datenübertragung im Internet (z. B. bei der Kommunikation per E-Mail) Sicherheitslücken aufweisen kann.

### Ihre Rechte
Sie haben jederzeit das Recht, unentgeltlich Auskunft über Herkunft, Empfänger und Zweck Ihrer gespeicherten personenbezogenen Daten zu erhalten.
"""
    
    def _get_imprint_template(self) -> str:
        """erecht24 Impressum Template"""
        return """
# Impressum

## Angaben gemäß § 5 TMG

[UNTERNEHMEN]
[ADRESSE]
[PLZ ORT]

## Kontakt
Telefon: [TELEFON]
E-Mail: [EMAIL]

## Umsatzsteuer-ID
Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:
[UST-ID]

## Redaktionell verantwortlich
[NAME]
[ADRESSE]

## EU-Streitschlichtung
Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: https://ec.europa.eu/consumers/odr/.
Unsere E-Mail-Adresse finden Sie oben im Impressum.

## Verbraucherstreitbeilegung/Universalschlichtungsstelle
Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.
"""
    
    def _get_cookie_consent_template(self) -> str:
        """erecht24 Cookie-Consent Template"""
        return """
// DSGVO-konformer Cookie-Consent
const cookieConsent = {
    essential: {
        name: 'Essentielle Cookies',
        description: 'Diese Cookies sind für die Grundfunktionen der Website erforderlich.',
        required: true,
        cookies: ['session', 'csrf_token']
    },
    analytics: {
        name: 'Analyse-Cookies',
        description: 'Diese Cookies helfen uns, die Website zu verbessern.',
        required: false,
        cookies: ['_ga', '_gid', '_gat']
    },
    marketing: {
        name: 'Marketing-Cookies',
        description: 'Diese Cookies werden für Werbezwecke verwendet.',
        required: false,
        cookies: ['_fbp', '_fbc']
    }
};
"""
    
    def get_legal_template(self, template_id: str, company_data: Dict[str, Any]) -> str:
        """Gibt personalisierten Rechtstext zurück"""
        if template_id not in self.legal_templates:
            raise ValueError(f"Template {template_id} nicht gefunden")
        
        template = self.legal_templates[template_id]
        content = template.content
        
        # Platzhalter ersetzen
        replacements = {
            '[UNTERNEHMEN]': company_data.get('company_name', '[UNTERNEHMEN]'),
            '[ADRESSE]': company_data.get('address', '[ADRESSE]'),
            '[PLZ ORT]': f"{company_data.get('postal_code', '[PLZ]')} {company_data.get('city', '[ORT]')}",
            '[TELEFON]': company_data.get('phone', '[TELEFON]'),
            '[EMAIL]': company_data.get('email', '[EMAIL]'),
            '[UST-ID]': company_data.get('vat_id', '[UST-ID]'),
            '[NAME]': company_data.get('responsible_person', '[NAME]')
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        return content
    
    def calculate_abmahn_protection_cost(self, risk_level: str, website_type: str) -> Dict[str, Any]:
        """Berechnet Abmahnschutz-Kosten"""
        base_costs = {
            'low': 29,
            'medium': 49,
            'high': 79,
            'critical': 99
        }
        
        website_multipliers = {
            'e_commerce': 1.5,
            'corporate': 1.0,
            'blog': 0.8,
            'portfolio': 0.6
        }
        
        monthly_cost = base_costs.get(risk_level, 49)
        multiplier = website_multipliers.get(website_type, 1.0)
        
        return {
            'monthly_cost': int(monthly_cost * multiplier),
            'coverage_amount': self._get_coverage_amount(risk_level),
            'included_services': self._get_included_services(risk_level),
            'legal_basis': 'erecht24 Abmahnschutz-Versicherung'
        }
    
    def _get_coverage_amount(self, risk_level: str) -> int:
        """Gibt Deckungssumme zurück"""
        coverage = {
            'low': 1000,
            'medium': 2500,
            'high': 5000,
            'critical': 10000
        }
        return coverage.get(risk_level, 2500)
    
    def _get_included_services(self, risk_level: str) -> List[str]:
        """Gibt enthaltene Services zurück"""
        services = {
            'low': ['Basis-Rechtstexte', 'E-Mail-Support'],
            'medium': ['Alle Rechtstexte', 'Telefon-Support', 'Updates'],
            'high': ['Premium-Rechtstexte', 'Priority-Support', 'Individuelle Beratung'],
            'critical': ['Vollservice', '24/7-Support', 'Anwaltliche Betreuung']
        }
        return services.get(risk_level, services['medium'])