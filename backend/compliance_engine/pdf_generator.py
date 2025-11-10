"""
Professional PDF Report Generator for Complyo Compliance Analysis
Creates branded, professional compliance reports with charts and recommendations
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import io
from typing import Dict, Any, List

class ComplianceReportGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.styles = self._create_custom_styles()
        
    def _create_custom_styles(self):
        styles = getSampleStyleSheet()
        complyo_blue = colors.Color(102/255, 126/255, 234/255)
        styles.add(ParagraphStyle(name='ComplyoTitle', parent=styles['Title'], fontSize=24, textColor=complyo_blue, alignment=TA_CENTER, spaceAfter=20, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='ComplyoHeading', parent=styles['h1'], fontSize=16, textColor=complyo_blue, spaceAfter=12, spaceBefore=12, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='ComplianceScore', parent=styles['Normal'], fontSize=48, textColor=complyo_blue, alignment=TA_CENTER, spaceAfter=10, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='RiskLevel', parent=styles['Normal'], fontSize=18, textColor=colors.red, alignment=TA_CENTER, spaceAfter=15, fontName='Helvetica-Bold'))
        return styles
    
    def generate_compliance_report(self, analysis_data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        story = []
        
        story.extend(self._create_cover_page(analysis_data))
        story.append(PageBreak())
        story.extend(self._create_detailed_findings(analysis_data))
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    
    def _create_cover_page(self, analysis_data: Dict[str, Any]) -> List:
        content = []
        content.append(Paragraph("🛡️ Complyo", self.styles['ComplyoTitle']))
        content.append(Paragraph("Website Compliance Report", self.styles['ComplyoHeading']))
        content.append(Spacer(1, 0.5*cm))
        
        url = analysis_data.get('url', 'N/A')
        content.append(Paragraph(f"<b>Analysierte Website:</b> {url}", self.styles['Normal']))
        content.append(Spacer(1, 0.2*cm))
        
        score = analysis_data.get('compliance_score', 0)
        content.append(Paragraph("Compliance-Score", self.styles['ComplyoHeading']))
        content.append(Paragraph(f"{score}%", self.styles['ComplianceScore']))
        
        risk = analysis_data.get('total_risk_euro', 0)
        content.append(Paragraph("Geschätztes Risiko", self.styles['ComplyoHeading']))
        content.append(Paragraph(f"{risk} EUR", self.styles['RiskLevel']))
        content.append(Spacer(1, 0.5*cm))
        
        report_data = [
            ['Erstellungsdatum:', datetime.now().strftime('%d.%m.%Y')],
            ['Report-Version:', '2.1']
        ]
        report_table = Table(report_data, colWidths=[4*cm, 8*cm])
        report_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        content.append(report_table)
        return content
    
    def _create_detailed_findings(self, analysis_data: Dict[str, Any]) -> List:
        content = []
        content.append(Paragraph("Detaillierte Analyse-Ergebnisse", self.styles['ComplyoTitle']))
        
        issues = analysis_data.get('issues', [])
        if not issues:
            content.append(Paragraph("Keine spezifischen Probleme gefunden.", self.styles['Normal']))
            return content
            
        for issue in issues:
            severity_color = 'red' if issue['severity'] == 'critical' else 'orange'
            content.append(Paragraph(f"<b>{issue['title']}</b> <font color='{severity_color}'>({issue['severity'].upper()})</font>", self.styles['ComplyoHeading']))
            content.append(Paragraph(issue['description'], self.styles['Normal']))
            content.append(Paragraph(f"<b>Empfehlung:</b> {issue['recommendation']}", self.styles['Normal']))
            content.append(Spacer(1, 0.2*cm))
            
        return content

pdf_generator = ComplianceReportGenerator()