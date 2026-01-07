"""
AI Act Documentation Generator
Generiert erforderliche Dokumentation für EU AI Act Compliance
"""

import os
from typing import Dict, Any, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import pdfkit


class AIActDocumentationGenerator:
    """
    Generiert AI Act konforme Dokumentation
    """
    
    def __init__(self):
        # Setup Jinja2 Environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def generate_risk_assessment_report(self, ai_system: Dict[str, Any], classification: Dict[str, Any]) -> str:
        """
        Generiert Risk Assessment Report (Art. 9 AI Act)
        """
        
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Risk Assessment Report - {{ ai_system.name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .header { background: #ecf0f1; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
        .risk-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
        .requirement { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 3px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #3498db; color: white; }
        .footer { margin-top: 50px; font-size: 0.9em; color: #7f8c8d; border-top: 1px solid #bdc3c7; padding-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Risk Assessment Report</h1>
        <p><strong>KI-System:</strong> {{ ai_system.name }}</p>
        <p><strong>Datum:</strong> {{ generated_date }}</p>
        <p><strong>Risikokategorie:</strong> {{ classification.risk_category|upper }}</p>
    </div>
    
    <h2>1. Systemübersicht</h2>
    <p><strong>Bezeichnung:</strong> {{ ai_system.name }}</p>
    <p><strong>Anbieter:</strong> {{ ai_system.vendor or 'Nicht spezifiziert' }}</p>
    <p><strong>Verwendungszweck:</strong> {{ ai_system.purpose }}</p>
    <p><strong>Einsatzbereich:</strong> {{ ai_system.domain or 'Nicht spezifiziert' }}</p>
    <p><strong>Beschreibung:</strong> {{ ai_system.description }}</p>
    
    <h2>2. Risikoklassifizierung</h2>
    <div class="risk-box">
        <p><strong>Risikokategorie:</strong> {{ classification.risk_category|upper }}</p>
        <p><strong>Konfidenz:</strong> {{ (classification.confidence * 100)|round|int }}%</p>
        <p><strong>Begründung:</strong> {{ classification.reasoning }}</p>
    </div>
    
    <h2>3. Relevante Artikel des EU AI Act</h2>
    <ul>
    {% for article in classification.relevant_articles %}
        <li>{{ article }}</li>
    {% endfor %}
    </ul>
    
    <h2>4. Identifizierte Risiken</h2>
    {% if classification.key_concerns %}
    <table>
        <thead>
            <tr>
                <th>Nr.</th>
                <th>Risiko / Concern</th>
            </tr>
        </thead>
        <tbody>
        {% for concern in classification.key_concerns %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ concern }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>Keine spezifischen Risiken identifiziert.</p>
    {% endif %}
    
    <h2>5. Erforderliche Maßnahmen</h2>
    {% if classification.risk_category == 'prohibited' %}
    <div class="risk-box" style="background: #f8d7da; border-left-color: #dc3545;">
        <p><strong>⚠️ WARNUNG:</strong> Dieses System fällt möglicherweise unter Art. 5 AI Act (Verbotene Systeme).</p>
        <p>Das System darf <strong>NICHT</strong> in der EU in Verkehr gebracht oder betrieben werden.</p>
        <p><strong>Sofortige Maßnahmen:</strong></p>
        <ul>
            <li>Rechtliche Prüfung durch Fachanwalt</li>
            <li>Betrieb sofort einstellen</li>
            <li>Alternative Lösungen evaluieren</li>
        </ul>
    </div>
    {% elif classification.risk_category == 'high' %}
    <div class="requirement">
        <h3>Hochrisiko-System Requirements (Art. 6-15):</h3>
        <ul>
            <li>✓ Risikomanagementsystem etablieren (Art. 9)</li>
            <li>✓ Data Governance implementieren (Art. 10)</li>
            <li>✓ Technische Dokumentation erstellen (Art. 11)</li>
            <li>✓ Logging-System einrichten (Art. 12)</li>
            <li>✓ Transparenzinformationen bereitstellen (Art. 13)</li>
            <li>✓ Menschliche Aufsicht gewährleisten (Art. 14)</li>
            <li>✓ Accuracy & Robustness testen (Art. 15)</li>
            <li>✓ Konformitätsbewertung durchführen (Art. 43)</li>
            <li>✓ CE-Kennzeichnung anbringen (Art. 49)</li>
            <li>✓ In EU-Datenbank registrieren (Art. 71)</li>
        </ul>
    </div>
    {% elif classification.risk_category == 'limited' %}
    <div class="requirement">
        <h3>Limited Risk Requirements (Art. 52):</h3>
        <ul>
            <li>✓ Transparenzpflichten erfüllen</li>
            <li>✓ Nutzer über KI-Nutzung informieren</li>
            <li>✓ KI-generierter Content kennzeichnen</li>
        </ul>
    </div>
    {% else %}
    <p>Für Minimal-Risk-Systeme gelten keine speziellen regulatorischen Anforderungen. Best Practices empfohlen.</p>
    {% endif %}
    
    <div class="footer">
        <p>Generiert von <strong>Complyo.tech</strong> - EU AI Act Compliance Platform</p>
        <p>Dieses Dokument ist eine automatisch generierte Ersteinschätzung. Für rechtssichere Compliance-Prüfung konsultieren Sie bitte einen Fachanwalt.</p>
        <p><strong>Haftungsausschluss:</strong> Complyo übernimmt keine Haftung für die Richtigkeit und Vollständigkeit dieser Einschätzung.</p>
    </div>
</body>
</html>
        """
        
        template = self.jinja_env.from_string(template_content)
        
        html = template.render(
            ai_system=ai_system,
            classification=classification,
            generated_date=datetime.now().strftime("%d.%m.%Y %H:%M")
        )
        
        return html
    
    def generate_technical_documentation_template(self, ai_system: Dict[str, Any]) -> str:
        """
        Generiert Technical Documentation Template (Art. 11 AI Act)
        """
        
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Technische Dokumentation - {{ ai_system.name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
        h1 { color: #2c3e50; }
        h2 { color: #34495e; margin-top: 30px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
        .section { background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .requirement { background: #e3f2fd; padding: 10px; margin: 10px 0; border-left: 4px solid #2196f3; }
        ul { line-height: 2; }
    </style>
</head>
<body>
    <h1>Technische Dokumentation gemäß Art. 11 EU AI Act</h1>
    <p><strong>KI-System:</strong> {{ ai_system.name }}</p>
    <p><strong>Datum:</strong> {{ generated_date }}</p>
    
    <h2>1. Allgemeine Beschreibung</h2>
    <div class="section">
        <p><strong>Systemname:</strong> {{ ai_system.name }}</p>
        <p><strong>Anbieter:</strong> [TODO: Firmennamen eintragen]</p>
        <p><strong>Version:</strong> [TODO: Versionsnummer]</p>
        <p><strong>Verwendungszweck:</strong> {{ ai_system.purpose }}</p>
        <p><strong>Beschreibung:</strong> {{ ai_system.description }}</p>
    </div>
    
    <h2>2. Systemarchitektur</h2>
    <div class="requirement">
        <p><strong>Erforderliche Angaben:</strong></p>
        <ul>
            <li>[ ] Diagramm der Systemarchitektur</li>
            <li>[ ] Beschreibung der Komponenten und Module</li>
            <li>[ ] Schnittstellen zu anderen Systemen</li>
            <li>[ ] Hardware-Requirements</li>
            <li>[ ] Software-Stack und Dependencies</li>
        </ul>
    </div>
    <p>[TODO: Architektur-Beschreibung einfügen]</p>
    
    <h2>3. Entwicklungsprozess</h2>
    <div class="requirement">
        <p><strong>Erforderliche Angaben:</strong></p>
        <ul>
            <li>[ ] Entwicklungsmethodik (Agile, Waterfall, etc.)</li>
            <li>[ ] Verwendete Tools und Frameworks</li>
            <li>[ ] Versionskontrolle und Deployment-Prozess</li>
            <li>[ ] Qualitätssicherungsmaßnahmen</li>
        </ul>
    </div>
    <p>[TODO: Entwicklungsprozess dokumentieren]</p>
    
    <h2>4. Daten und Training</h2>
    <div class="requirement">
        <p><strong>Erforderliche Angaben (Art. 10):</strong></p>
        <ul>
            <li>[ ] Beschreibung der Trainingsdaten</li>
            <li>[ ] Datenquellen und -herkunft</li>
            <li>[ ] Datenaufbereitungs-Pipeline</li>
            <li>[ ] Bias-Analyse durchgeführt</li>
            <li>[ ] Datenqualitätsmetriken</li>
            <li>[ ] Datenschutzmaßnahmen</li>
        </ul>
    </div>
    <p>[TODO: Daten-Dokumentation einfügen]</p>
    
    <h2>5. Modell-Spezifikationen</h2>
    <div class="section">
        <p><strong>Modell-Typ:</strong> [TODO: z.B. CNN, Transformer, etc.]</p>
        <p><strong>Architektur:</strong> [TODO: Layer-Beschreibung]</p>
        <p><strong>Parameter-Anzahl:</strong> [TODO: Anzahl]</p>
        <p><strong>Training-Hyperparameter:</strong> [TODO: Learning Rate, etc.]</p>
    </div>
    
    <h2>6. Testing und Validierung</h2>
    <div class="requirement">
        <p><strong>Erforderliche Angaben (Art. 15):</strong></p>
        <ul>
            <li>[ ] Test-Strategie beschrieben</li>
            <li>[ ] Validierungs-Datensätze dokumentiert</li>
            <li>[ ] Accuracy-Metriken (Precision, Recall, F1, etc.)</li>
            <li>[ ] Robustness-Tests durchgeführt</li>
            <li>[ ] Adversarial Testing</li>
            <li>[ ] Edge-Case-Testing</li>
        </ul>
    </div>
    <p>[TODO: Test-Ergebnisse einfügen]</p>
    
    <h2>7. Sicherheit und Datenschutz</h2>
    <div class="section">
        <p><strong>Cybersicherheitsmaßnahmen:</strong></p>
        <ul>
            <li>[ ] Zugriffskontrolle</li>
            <li>[ ] Datenverschlüsselung</li>
            <li>[ ] Penetration Testing</li>
            <li>[ ] Incident Response Plan</li>
        </ul>
        <p><strong>Datenschutz (DSGVO):</strong></p>
        <ul>
            <li>[ ] DPIA durchgeführt</li>
            <li>[ ] Privacy by Design implementiert</li>
            <li>[ ] Betroffenenrechte gewährleistet</li>
        </ul>
    </div>
    
    <h2>8. Menschliche Aufsicht (Art. 14)</h2>
    <div class="requirement">
        <p><strong>Erforderliche Angaben:</strong></p>
        <ul>
            <li>[ ] Beschreibung der Oversight-Mechanismen</li>
            <li>[ ] Rollen und Verantwortlichkeiten</li>
            <li>[ ] Eingriffsmöglichkeiten dokumentiert</li>
            <li>[ ] Schulungskonzept für Oversight-Personal</li>
        </ul>
    </div>
    <p>[TODO: Oversight-Konzept einfügen]</p>
    
    <h2>9. Änderungshistorie</h2>
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="background: #3498db; color: white;">
                <th style="border: 1px solid #ddd; padding: 8px;">Version</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Datum</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Änderungen</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Autor</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">1.0</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{ generated_date }}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">Initiale Version</td>
                <td style="border: 1px solid #ddd; padding: 8px;">[TODO]</td>
            </tr>
        </tbody>
    </table>
    
    <div style="margin-top: 50px; font-size: 0.9em; color: #7f8c8d; border-top: 1px solid #bdc3c7; padding-top: 20px;">
        <p>Generiert von <strong>Complyo.tech</strong> - EU AI Act Compliance Platform</p>
        <p>Dies ist ein Template. Bitte ergänzen Sie alle [TODO] Felder mit den spezifischen Informationen Ihres Systems.</p>
    </div>
</body>
</html>
        """
        
        template = self.jinja_env.from_string(template_content)
        
        html = template.render(
            ai_system=ai_system,
            generated_date=datetime.now().strftime("%d.%m.%Y %H:%M")
        )
        
        return html
    
    def generate_conformity_declaration(self, ai_system: Dict[str, Any]) -> str:
        """
        Generiert EU-Konformitätserklärung Template (Art. 47 AI Act)
        """
        
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>EU-Konformitätserklärung - {{ ai_system.name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.8; margin: 40px; max-width: 800px; }
        h1 { text-align: center; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; }
        .declaration { background: #f8f9fa; padding: 20px; margin: 20px 0; border: 2px solid #3498db; }
        .signature-box { margin-top: 50px; border-top: 2px solid #000; padding-top: 30px; }
        .footer { margin-top: 30px; font-size: 0.85em; color: #7f8c8d; }
    </style>
</head>
<body>
    <h1>EU-Konformitätserklärung</h1>
    <p style="text-align: center;"><em>gemäß Artikel 47 der Verordnung (EU) 2024/1689 (EU AI Act)</em></p>
    
    <div class="declaration">
        <h2>Erklärung</h2>
        <p>Hiermit erklären wir in alleiniger Verantwortung, dass das nachfolgend beschriebene Hochrisiko-KI-System den Anforderungen der Verordnung (EU) 2024/1689 (EU AI Act) entspricht.</p>
        
        <h3>1. Anbieter</h3>
        <p><strong>Name:</strong> [TODO: Firmenname]</p>
        <p><strong>Adresse:</strong> [TODO: Vollständige Adresse]</p>
        <p><strong>Kontakt:</strong> [TODO: Email, Telefon]</p>
        
        <h3>2. KI-System</h3>
        <p><strong>Bezeichnung:</strong> {{ ai_system.name }}</p>
        <p><strong>Version:</strong> [TODO: Version]</p>
        <p><strong>Verwendungszweck:</strong> {{ ai_system.purpose }}</p>
        <p><strong>Risikokategorie:</strong> Hochrisiko-System (High-Risk AI System)</p>
        
        <h3>3. Anwendbare Rechtsvorschriften</h3>
        <ul>
            <li>Verordnung (EU) 2024/1689 des Europäischen Parlaments und des Rates (EU AI Act)</li>
            <li>Insbesondere Artikel 6-15 (Anforderungen an Hochrisiko-KI-Systeme)</li>
            <li>Verordnung (EU) 2016/679 (DSGVO)</li>
        </ul>
        
        <h3>4. Harmonisierte Normen und technische Spezifikationen</h3>
        <p>[TODO: Hier anwendbare harmonisierte Normen auflisten]</p>
        
        <h3>5. Konformitätsbewertungsverfahren</h3>
        <p>Das KI-System wurde folgendem Konformitätsbewertungsverfahren unterzogen:</p>
        <ul>
            <li>[ ] Interne Kontrolle (Artikel 43 Absatz 2)</li>
            <li>[ ] Konformitätsbewertung durch benannte Stelle (Artikel 43 Absatz 3)</li>
        </ul>
        <p><strong>Benannte Stelle (falls zutreffend):</strong> [TODO: Name und Kennnummer]</p>
        
        <h3>6. Erfüllte Anforderungen</h3>
        <ul>
            <li>✓ Risikomanagementsystem (Art. 9)</li>
            <li>✓ Data Governance (Art. 10)</li>
            <li>✓ Technische Dokumentation (Art. 11)</li>
            <li>✓ Aufzeichnungspflichten (Art. 12)</li>
            <li>✓ Transparenz (Art. 13)</li>
            <li>✓ Menschliche Aufsicht (Art. 14)</li>
            <li>✓ Genauigkeit, Robustheit, Cybersicherheit (Art. 15)</li>
        </ul>
        
        <h3>7. Registrierung</h3>
        <p><strong>EU-Datenbank-Registrierung:</strong> [TODO: Registrierungsnummer]</p>
        <p><strong>Registrierungsdatum:</strong> [TODO: Datum]</p>
    </div>
    
    <div class="signature-box">
        <p><strong>Ort, Datum:</strong> ________________________, {{ generated_date }}</p>
        <br><br>
        <p><strong>Unterschrift:</strong> ______________________________________</p>
        <p><strong>Name (in Druckbuchstaben):</strong> [TODO: Name]</p>
        <p><strong>Funktion:</strong> [TODO: Position]</p>
    </div>
    
    <div class="footer">
        <p><strong>Hinweis:</strong> Diese Konformitätserklärung muss zusammen mit der technischen Dokumentation 10 Jahre lang aufbewahrt werden.</p>
        <p>Generiert von Complyo.tech - EU AI Act Compliance Platform</p>
    </div>
</body>
</html>
        """
        
        template = self.jinja_env.from_string(template_content)
        
        html = template.render(
            ai_system=ai_system,
            generated_date=datetime.now().strftime("%d.%m.%Y")
        )
        
        return html
    
    def generate_pdf(self, html_content: str, output_path: str) -> bool:
        """
        Konvertiert HTML zu PDF
        """
        try:
            pdfkit.from_string(html_content, output_path)
            return True
        except Exception as e:
            print(f"PDF generation failed: {e}")
            return False


# Singleton Instance
ai_act_doc_generator = AIActDocumentationGenerator()

