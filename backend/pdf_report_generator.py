"""
Professional PDF Report Generator for Complyo Compliance Analysis
Creates branded, professional compliance reports with charts and recommendations
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from datetime import datetime
import io
import base64
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ComplianceReportGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.styles = self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Create custom styles for the report"""
        styles = getSampleStyleSheet()
        
        # Complyo brand colors
        complyo_blue = colors.Color(102/255, 126/255, 234/255)  # #667eea
        complyo_purple = colors.Color(118/255, 75/255, 162/255)  # #764ba2
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='ComplyoTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=complyo_blue,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='ComplyoHeading',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=complyo_blue,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='ComplyoSubheading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=complyo_purple,
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='ComplianceScore',
            parent=styles['Normal'],
            fontSize=48,
            textColor=complyo_blue,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='RiskLevel',
            parent=styles['Normal'],
            fontSize=18,
            textColor=colors.red,
            alignment=TA_CENTER,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='RecommendationBox',
            parent=styles['Normal'],
            fontSize=11,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=10,
            borderColor=complyo_blue,
            borderWidth=1,
            borderPadding=10
        ))
        
        return styles
    
    def generate_compliance_report(self, analysis_data: Dict[str, Any], lead_data: Dict[str, Any]) -> bytes:
        """
        Generate a complete compliance PDF report
        """
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Build report content
            story = []
            
            # Cover page
            story.extend(self._create_cover_page(analysis_data, lead_data))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._create_executive_summary(analysis_data))
            story.append(PageBreak())
            
            # Detailed findings
            story.extend(self._create_detailed_findings(analysis_data))
            story.append(PageBreak())
            
            # Recommendations
            story.extend(self._create_recommendations(analysis_data))
            story.append(PageBreak())
            
            # Appendix
            story.extend(self._create_appendix(analysis_data, lead_data))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated compliance report: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _create_cover_page(self, analysis_data: Dict[str, Any], lead_data: Dict[str, Any]) -> List:
        """Create the report cover page"""
        content = []
        
        # Title
        content.append(Paragraph("🛡️ Complyo", self.styles['ComplyoTitle']))
        content.append(Paragraph("Website Compliance Report", self.styles['ComplyoHeading']))
        content.append(Spacer(1, 0.5*inch))
        
        # Website info
        url = analysis_data.get('url', 'N/A')
        content.append(Paragraph(f"<b>Analysierte Website:</b> {url}", self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Compliance score - large and prominent
        score = analysis_data.get('compliance_score', 0)
        content.append(Paragraph("Compliance-Score", self.styles['ComplyoHeading']))
        content.append(Paragraph(f"{score}%", self.styles['ComplianceScore']))
        
        # Risk assessment
        risk = analysis_data.get('estimated_risk_euro', 'Unbekannt')
        content.append(Paragraph("Geschätztes Risiko", self.styles['ComplyoHeading']))
        content.append(Paragraph(f"{risk} EUR", self.styles['RiskLevel']))
        content.append(Spacer(1, 0.5*inch))
        
        # Report details
        report_data = [
            ['Erstellt für:', lead_data.get('name', 'N/A')],
            ['Unternehmen:', lead_data.get('company', 'N/A')],
            ['E-Mail:', lead_data.get('email', 'N/A')],
            ['Erstellungsdatum:', datetime.now().strftime('%d.%m.%Y')],
            ['Report-Version:', '2.0']
        ]
        
        report_table = Table(report_data, colWidths=[3*cm, 8*cm])
        report_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(102/255, 126/255, 234/255, alpha=0.1)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        content.append(report_table)
        content.append(Spacer(1, 1*inch))
        
        # Footer disclaimer
        disclaimer = """
        <b>Wichtiger Hinweis:</b> Dieser Report basiert auf einer automatisierten Analyse 
        und stellt eine erste Einschätzung dar. Für eine vollständige rechtliche Bewertung 
        empfehlen wir die Konsultation eines Fachanwalts.
        """
        content.append(Paragraph(disclaimer, self.styles['Normal']))
        
        return content
    
    def _create_executive_summary(self, analysis_data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        content = []
        
        content.append(Paragraph("Executive Summary", self.styles['ComplyoTitle']))
        content.append(Spacer(1, 0.3*inch))
        
        # Key metrics table
        score = analysis_data.get('compliance_score', 0)
        risk = analysis_data.get('estimated_risk_euro', 'Unbekannt')
        findings = analysis_data.get('findings', {})
        critical_issues = len([f for f in findings.values() if f.get('severity') == 'critical'])
        total_issues = len(findings)
        
        summary_data = [
            ['Metrik', 'Wert', 'Bewertung'],
            ['Compliance-Score', f'{score}%', self._get_score_assessment(score)],
            ['Kritische Probleme', str(critical_issues), self._get_critical_assessment(critical_issues)],
            ['Gesamte Probleme', str(total_issues), self._get_total_assessment(total_issues)],
            ['Geschätztes Risiko', f'{risk} EUR', self._get_risk_assessment(risk)]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 3*cm, 5*cm])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(102/255, 126/255, 234/255)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ]))
        content.append(summary_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Summary text
        summary_text = self._generate_summary_text(analysis_data)
        content.append(Paragraph("Zusammenfassung", self.styles['ComplyoHeading']))
        content.append(Paragraph(summary_text, self.styles['Normal']))
        
        return content
    
    def _create_detailed_findings(self, analysis_data: Dict[str, Any]) -> List:
        """Create detailed findings section"""
        content = []
        
        content.append(Paragraph("Detaillierte Analyse-Ergebnisse", self.styles['ComplyoTitle']))
        content.append(Spacer(1, 0.3*inch))
        
        findings = analysis_data.get('findings', {})
        
        if not findings:
            content.append(Paragraph("Keine spezifischen Probleme gefunden.", self.styles['Normal']))
            return content
        
        # Group findings by category
        categories = {
            'DSGVO/GDPR': [],
            'TMG': [],
            'TTDSG': [],
            'Accessibility': [],
            'Other': []
        }
        
        for finding_key, finding_data in findings.items():
            category = finding_data.get('category', 'Other')
            if category not in categories:
                categories['Other'].append((finding_key, finding_data))
            else:
                categories[category].append((finding_key, finding_data))
        
        # Create sections for each category
        for category, category_findings in categories.items():
            if not category_findings:
                continue
                
            content.append(Paragraph(f"{category}", self.styles['ComplyoHeading']))
            
            for finding_key, finding_data in category_findings:
                # Finding title
                title = finding_data.get('title', finding_key.replace('_', ' ').title())
                severity = finding_data.get('severity', 'medium')
                severity_color = self._get_severity_color(severity)
                
                content.append(Paragraph(
                    f"<b>{title}</b> <font color='{severity_color}'>({severity.upper()})</font>",
                    self.styles['ComplyoSubheading']
                ))
                
                # Description
                description = finding_data.get('description', 'Keine Beschreibung verfügbar.')
                content.append(Paragraph(description, self.styles['Normal']))
                
                # Recommendation
                recommendation = finding_data.get('recommendation', 'Keine spezifische Empfehlung verfügbar.')
                content.append(Paragraph(f"<b>Empfehlung:</b> {recommendation}", self.styles['RecommendationBox']))
                
                content.append(Spacer(1, 0.2*inch))
        
        return content
    
    def _create_recommendations(self, analysis_data: Dict[str, Any]) -> List:
        """Create recommendations section"""
        content = []
        
        content.append(Paragraph("Handlungsempfehlungen", self.styles['ComplyoTitle']))
        content.append(Spacer(1, 0.3*inch))
        
        # Priority-based recommendations
        content.append(Paragraph("Sofortige Maßnahmen (Hoch Priorität)", self.styles['ComplyoHeading']))
        high_priority = self._get_priority_recommendations(analysis_data, 'high')
        for rec in high_priority:
            content.append(Paragraph(f"• {rec}", self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        content.append(Paragraph("Mittelfristige Maßnahmen (Medium Priorität)", self.styles['ComplyoHeading']))
        medium_priority = self._get_priority_recommendations(analysis_data, 'medium')
        for rec in medium_priority:
            content.append(Paragraph(f"• {rec}", self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        content.append(Paragraph("Langfristige Optimierungen (Niedrig Priorität)", self.styles['ComplyoHeading']))
        low_priority = self._get_priority_recommendations(analysis_data, 'low')
        for rec in low_priority:
            content.append(Paragraph(f"• {rec}", self.styles['Normal']))
        
        # Next steps
        content.append(Spacer(1, 0.3*inch))
        content.append(Paragraph("Nächste Schritte", self.styles['ComplyoHeading']))
        next_steps = """
        1. <b>Sofortige Maßnahmen umsetzen:</b> Beginnen Sie mit den kritischen Problemen
        2. <b>Rechtliche Beratung:</b> Konsultieren Sie einen Fachanwalt für komplexe Fälle
        3. <b>Monitoring einrichten:</b> Regelmäßige Compliance-Überprüfungen planen
        4. <b>Team schulen:</b> Mitarbeiter über Compliance-Anforderungen informieren
        5. <b>Dokumentation:</b> Alle Maßnahmen dokumentieren und archivieren
        """
        content.append(Paragraph(next_steps, self.styles['Normal']))
        
        return content
    
    def _create_appendix(self, analysis_data: Dict[str, Any], lead_data: Dict[str, Any]) -> List:
        """Create appendix with technical details"""
        content = []
        
        content.append(Paragraph("Anhang", self.styles['ComplyoTitle']))
        content.append(Spacer(1, 0.3*inch))
        
        # Technical details
        content.append(Paragraph("Technische Details", self.styles['ComplyoHeading']))
        
        tech_data = [
            ['Parameter', 'Wert'],
            ['Analyse-URL', analysis_data.get('url', 'N/A')],
            ['Analyse-Datum', datetime.now().strftime('%d.%m.%Y %H:%M')],
            ['Report-Version', '2.0'],
            ['Analysierte Bereiche', 'DSGVO, TMG, TTDSG, Accessibility'],
            ['Compliance-Engine', 'Complyo AI v2.2.0']
        ]
        
        tech_table = Table(tech_data, colWidths=[5*cm, 7*cm])
        tech_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(102/255, 126/255, 234/255, alpha=0.2)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        content.append(tech_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Legal disclaimer
        content.append(Paragraph("Rechtlicher Hinweis", self.styles['ComplyoHeading']))
        disclaimer = """
        Dieser Report wurde automatisiert durch die Complyo AI-Engine erstellt und basiert auf einer 
        technischen Analyse der Website. Die Ergebnisse stellen eine erste Einschätzung dar und 
        ersetzen nicht die Beratung durch einen qualifizierten Rechtsanwalt.
        
        Complyo GmbH übernimmt keine Haftung für die Vollständigkeit oder Richtigkeit der Analyse. 
        Rechtliche Änderungen und individuelle Umstände können die Bewertung beeinflussen.
        
        Für eine umfassende rechtliche Beratung empfehlen wir die Konsultation eines Fachanwalts 
        für IT-Recht und Datenschutz.
        """
        content.append(Paragraph(disclaimer, self.styles['Normal']))
        
        # Contact information
        content.append(Spacer(1, 0.3*inch))
        content.append(Paragraph("Kontakt", self.styles['ComplyoHeading']))
        contact = """
        <b>Complyo GmbH</b><br/>
        E-Mail: support@complyo.tech<br/>
        Website: https://complyo.tech<br/>
        Datenschutz: datenschutz@complyo.tech
        """
        content.append(Paragraph(contact, self.styles['Normal']))
        
        return content
    
    # Helper methods
    def _get_score_assessment(self, score: int) -> str:
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Moderate"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"
    
    def _get_critical_assessment(self, critical_count: int) -> str:
        if critical_count == 0:
            return "None"
        elif critical_count <= 2:
            return "Few"
        elif critical_count <= 5:
            return "Several"
        else:
            return "Many"
    
    def _get_total_assessment(self, total_count: int) -> str:
        if total_count <= 5:
            return "Minimal"
        elif total_count <= 10:
            return "Moderate"
        elif total_count <= 20:
            return "Extensive"
        else:
            return "Comprehensive"
    
    def _get_risk_assessment(self, risk: str) -> str:
        if "0-1000" in str(risk):
            return "Low Risk"
        elif "1000-5000" in str(risk):
            return "Medium Risk"
        elif "5000-15000" in str(risk):
            return "High Risk"
        else:
            return "Critical Risk"
    
    def _get_severity_color(self, severity: str) -> str:
        colors_map = {
            'critical': 'red',
            'high': 'orange',
            'medium': 'blue',
            'low': 'green'
        }
        return colors_map.get(severity.lower(), 'black')
    
    def _generate_summary_text(self, analysis_data: Dict[str, Any]) -> str:
        score = analysis_data.get('compliance_score', 0)
        findings = analysis_data.get('findings', {})
        critical_count = len([f for f in findings.values() if f.get('severity') == 'critical'])
        
        if score >= 90:
            return f"""
            Ihre Website zeigt eine hervorragende Compliance-Bewertung von {score}%. 
            Die meisten rechtlichen Anforderungen werden erfüllt. Nur geringfügige 
            Optimierungen sind erforderlich, um eine vollständige Compliance zu erreichen.
            """
        elif score >= 75:
            return f"""
            Ihre Website hat eine gute Compliance-Bewertung von {score}%. 
            Die grundlegenden rechtlichen Anforderungen werden größtenteils erfüllt. 
            Einige Verbesserungen in spezifischen Bereichen werden empfohlen.
            """
        elif score >= 60:
            return f"""
            Ihre Website zeigt eine moderate Compliance-Bewertung von {score}%. 
            Mehrere wichtige rechtliche Aspekte benötigen Aufmerksamkeit. 
            Eine systematische Überarbeitung wird empfohlen.
            """
        else:
            return f"""
            Ihre Website hat eine niedrige Compliance-Bewertung von {score}% mit 
            {critical_count} kritischen Problemen. Sofortige Maßnahmen sind erforderlich, 
            um rechtliche Risiken zu minimieren.
            """
    
    def _get_priority_recommendations(self, analysis_data: Dict[str, Any], priority: str) -> List[str]:
        """Get recommendations based on priority level"""
        findings = analysis_data.get('findings', {})
        recommendations = []
        
        priority_map = {
            'high': ['critical'],
            'medium': ['high', 'medium'],
            'low': ['low']
        }
        
        target_severities = priority_map.get(priority, [])
        
        for finding_data in findings.values():
            if finding_data.get('severity') in target_severities:
                rec = finding_data.get('recommendation', '')
                if rec and rec not in recommendations:
                    recommendations.append(rec)
        
        # Add generic recommendations if no specific ones found
        if not recommendations:
            generic_recommendations = {
                'high': [
                    "Datenschutzerklärung aktualisieren und rechtssicher gestalten",
                    "Cookie-Banner implementieren und DSGVO-konform konfigurieren",
                    "Impressum vollständig und aktuell halten"
                ],
                'medium': [
                    "Kontaktformulare mit Einwilligungserklärungen versehen",
                    "SSL-Verschlüsselung auf der gesamten Website sicherstellen",
                    "Barrierefreiheit verbessern"
                ],
                'low': [
                    "SEO-Optimierung für bessere Auffindbarkeit",
                    "Performance-Optimierung durchführen",
                    "Regelmäßige Compliance-Überprüfungen einrichten"
                ]
            }
            recommendations = generic_recommendations.get(priority, [])
        
        return recommendations[:5]  # Limit to 5 recommendations per priority

# Global PDF generator instance
pdf_generator = ComplianceReportGenerator()