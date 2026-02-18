"""
Professional PDF Report Generator for Complyo Compliance Analysis
Creates branded, professional compliance reports with charts, scores and detailed findings
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from datetime import datetime
import io
from typing import Dict, Any, List

class ComplianceReportGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.complyo_blue = colors.HexColor('#3B82F6')
        self.complyo_dark = colors.HexColor('#1E293B')
        self.success_green = colors.HexColor('#10B981')
        self.warning_orange = colors.HexColor('#F59E0B')
        self.danger_red = colors.HexColor('#EF4444')
        self.light_gray = colors.HexColor('#F1F5F9')
        self.styles = self._create_custom_styles()
        
    def _create_custom_styles(self):
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            name='ComplyoTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=self.complyo_dark,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='ComplyoSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#64748B'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['h1'],
            fontSize=18,
            textColor=self.complyo_dark,
            spaceAfter=15,
            spaceBefore=25,
            fontName='Helvetica-Bold',
            borderPadding=5,
            leftIndent=0
        ))
        
        styles.add(ParagraphStyle(
            name='SubHeading',
            parent=styles['h2'],
            fontSize=14,
            textColor=self.complyo_blue,
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='ScoreDisplay',
            parent=styles['Normal'],
            fontSize=72,
            textColor=self.complyo_blue,
            alignment=TA_CENTER,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='ScoreLabel',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#64748B'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        styles.add(ParagraphStyle(
            name='RiskAmount',
            parent=styles['Normal'],
            fontSize=36,
            textColor=self.danger_red,
            alignment=TA_CENTER,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        ))
        
        if 'BodyText' not in styles:
            styles.add(ParagraphStyle(
                name='BodyText',
                parent=styles['Normal'],
                fontSize=10,
                textColor=self.complyo_dark,
                spaceAfter=8,
                leading=14
            ))
        else:
            styles['BodyText'].fontSize = 10
            styles['BodyText'].textColor = self.complyo_dark
            styles['BodyText'].spaceAfter = 8
            styles['BodyText'].leading = 14
        
        styles.add(ParagraphStyle(
            name='IssueTitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=self.complyo_dark,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#94A3B8'),
            alignment=TA_CENTER
        ))
        
        return styles
    
    def _get_score_color(self, score: float) -> colors.Color:
        if score >= 80:
            return self.success_green
        elif score >= 50:
            return self.warning_orange
        else:
            return self.danger_red
    
    def _get_severity_color(self, severity: str) -> colors.Color:
        severity_lower = severity.lower() if severity else 'warning'
        if severity_lower in ['critical', 'error', 'high']:
            return self.danger_red
        elif severity_lower in ['warning', 'medium']:
            return self.warning_orange
        else:
            return self.success_green
    
    def _format_euro(self, amount) -> str:
        try:
            num = float(amount) if amount else 0
            return f"{num:,.0f} EUR".replace(',', '.')
        except:
            return "0 EUR"
    
    def generate_compliance_report(self, analysis_data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm
        )
        story = []
        
        story.extend(self._create_header())
        story.extend(self._create_summary_section(analysis_data))
        story.extend(self._create_pillar_scores(analysis_data))
        story.append(PageBreak())
        story.extend(self._create_detailed_findings(analysis_data))
        story.extend(self._create_recommendations(analysis_data))
        story.extend(self._create_footer())
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    
    def _create_header(self) -> List:
        content = []
        
        content.append(Paragraph("COMPLYO", self.styles['ComplyoTitle']))
        content.append(Paragraph("Website Compliance Report", self.styles['ComplyoSubtitle']))
        
        content.append(HRFlowable(
            width="100%",
            thickness=2,
            color=self.complyo_blue,
            spaceAfter=20
        ))
        
        return content
    
    def _create_summary_section(self, analysis_data: Dict[str, Any]) -> List:
        content = []
        
        url = analysis_data.get('url', analysis_data.get('website_url', 'Unbekannt'))
        scan_date = analysis_data.get('scanned_at', analysis_data.get('created_at', datetime.now()))
        if isinstance(scan_date, str):
            try:
                scan_date = datetime.fromisoformat(scan_date.replace('Z', '+00:00'))
            except:
                scan_date = datetime.now()
        
        meta_data = [
            ['Analysierte Website:', str(url)],
            ['Analyse-Datum:', scan_date.strftime('%d.%m.%Y um %H:%M Uhr')],
            ['Report-ID:', str(analysis_data.get('scan_id', analysis_data.get('id', 'N/A')))],
        ]
        
        meta_table = Table(meta_data, colWidths=[5*cm, 11*cm])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.light_gray),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.complyo_dark),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        content.append(meta_table)
        content.append(Spacer(1, 1*cm))
        
        score = analysis_data.get('compliance_score', analysis_data.get('score', 0))
        try:
            score = float(score) if score else 0
        except:
            score = 0
        
        risk = analysis_data.get('total_risk_euro', analysis_data.get('risk_euro', 0))
        
        score_color = self._get_score_color(score)
        
        score_style = ParagraphStyle(
            'DynamicScore',
            parent=self.styles['ScoreDisplay'],
            textColor=score_color
        )
        
        score_data = [
            [
                Paragraph("Compliance-Score", self.styles['SubHeading']),
                Paragraph("Geschätztes Bußgeld-Risiko", self.styles['SubHeading'])
            ],
            [
                Paragraph(f"{score:.0f}%", score_style),
                Paragraph(self._format_euro(risk), self.styles['RiskAmount'])
            ],
            [
                Paragraph(self._get_score_label(score), self.styles['ScoreLabel']),
                Paragraph("bei Nicht-Compliance", self.styles['ScoreLabel'])
            ]
        ]
        
        score_table = Table(score_data, colWidths=[8*cm, 8*cm])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0FDF4') if score >= 80 else (colors.HexColor('#FEF3C7') if score >= 50 else colors.HexColor('#FEF2F2'))),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#FEF2F2')),
            ('BOX', (0, 0), (0, -1), 1, colors.HexColor('#E2E8F0')),
            ('BOX', (1, 0), (1, -1), 1, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        content.append(score_table)
        content.append(Spacer(1, 0.5*cm))
        
        return content
    
    def _get_score_label(self, score: float) -> str:
        if score >= 90:
            return "Hervorragend - Minimales Risiko"
        elif score >= 80:
            return "Gut - Geringes Risiko"
        elif score >= 60:
            return "Verbesserungsbedarf - Mittleres Risiko"
        elif score >= 40:
            return "Kritisch - Hohes Risiko"
        else:
            return "Sehr kritisch - Akuter Handlungsbedarf"
    
    def _create_pillar_scores(self, analysis_data: Dict[str, Any]) -> List:
        content = []
        
        content.append(Paragraph("Compliance nach Kategorien", self.styles['SectionHeading']))
        
        pillars = analysis_data.get('pillar_scores', analysis_data.get('pillars', {}))
        
        if not pillars:
            issues = analysis_data.get('issues', [])
            pillars = self._calculate_pillar_scores(issues)
        
        pillar_names = {
            'dsgvo': 'DSGVO & Datenschutz',
            'datenschutz': 'DSGVO & Datenschutz',
            'cookies': 'Cookie-Compliance',
            'ttdsg': 'Cookie-Compliance',
            'barrierefreiheit': 'Barrierefreiheit (BFSG)',
            'accessibility': 'Barrierefreiheit (BFSG)',
            'impressum': 'Rechtliche Texte',
            'legal': 'Rechtliche Texte'
        }
        
        pillar_data = [['Kategorie', 'Score', 'Status', 'Issues']]
        
        for key, data in pillars.items():
            if isinstance(data, dict):
                score = data.get('score', 0)
                issues_count = data.get('issues', data.get('issue_count', 0))
            else:
                score = data
                issues_count = 0
            
            name = pillar_names.get(key.lower(), key.title())
            score_text = f"{score}%"
            
            if score >= 80:
                status = "Gut"
                status_color = self.success_green
            elif score >= 50:
                status = "Warnung"
                status_color = self.warning_orange
            else:
                status = "Kritisch"
                status_color = self.danger_red
            
            pillar_data.append([name, score_text, status, str(issues_count)])
        
        if len(pillar_data) > 1:
            pillar_table = Table(pillar_data, colWidths=[6*cm, 3*cm, 4*cm, 3*cm])
            pillar_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.complyo_blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_gray]),
            ]))
            content.append(pillar_table)
        
        content.append(Spacer(1, 0.5*cm))
        return content
    
    def _calculate_pillar_scores(self, issues: List[Dict]) -> Dict:
        pillars = {
            'dsgvo': {'score': 100, 'issues': 0},
            'cookies': {'score': 100, 'issues': 0},
            'barrierefreiheit': {'score': 100, 'issues': 0},
            'impressum': {'score': 100, 'issues': 0}
        }
        
        for issue in issues:
            category = issue.get('category', '').lower()
            severity = issue.get('severity', 'warning').lower()
            
            penalty = 15 if severity in ['critical', 'error'] else 8
            
            if 'dsgvo' in category or 'datenschutz' in category or 'privacy' in category:
                pillars['dsgvo']['score'] = max(0, pillars['dsgvo']['score'] - penalty)
                pillars['dsgvo']['issues'] += 1
            elif 'cookie' in category or 'ttdsg' in category:
                pillars['cookies']['score'] = max(0, pillars['cookies']['score'] - penalty)
                pillars['cookies']['issues'] += 1
            elif 'barriere' in category or 'accessibility' in category or 'wcag' in category:
                pillars['barrierefreiheit']['score'] = max(0, pillars['barrierefreiheit']['score'] - penalty)
                pillars['barrierefreiheit']['issues'] += 1
            elif 'impressum' in category or 'legal' in category:
                pillars['impressum']['score'] = max(0, pillars['impressum']['score'] - penalty)
                pillars['impressum']['issues'] += 1
        
        return pillars
    
    def _create_detailed_findings(self, analysis_data: Dict[str, Any]) -> List:
        content = []
        
        content.append(Paragraph("Detaillierte Analyse-Ergebnisse", self.styles['SectionHeading']))
        
        issues = analysis_data.get('issues', [])
        
        if not issues:
            content.append(Paragraph(
                "Keine kritischen Compliance-Probleme gefunden. Ihre Website erfüllt die grundlegenden Anforderungen.",
                self.styles['BodyText']
            ))
            return content
        
        critical_issues = [i for i in issues if i.get('severity', '').lower() in ['critical', 'error', 'high']]
        warning_issues = [i for i in issues if i.get('severity', '').lower() in ['warning', 'medium']]
        info_issues = [i for i in issues if i.get('severity', '').lower() in ['info', 'low']]
        
        if critical_issues:
            content.append(Paragraph("Kritische Probleme", self.styles['SubHeading']))
            content.extend(self._format_issues(critical_issues, self.danger_red))
        
        if warning_issues:
            content.append(Paragraph("Warnungen", self.styles['SubHeading']))
            content.extend(self._format_issues(warning_issues, self.warning_orange))
        
        if info_issues:
            content.append(Paragraph("Hinweise", self.styles['SubHeading']))
            content.extend(self._format_issues(info_issues, self.complyo_blue))
        
        return content
    
    def _format_issues(self, issues: List[Dict], color: colors.Color) -> List:
        content = []
        
        for idx, issue in enumerate(issues[:10], 1):
            title = issue.get('title', 'Unbekanntes Problem')
            description = issue.get('description', '')
            recommendation = issue.get('recommendation', '')
            risk = issue.get('risk_euro', 0)
            
            issue_data = [
                [Paragraph(f"<font color='#{color.hexval()[2:]}'>{idx}.</font> {title}", self.styles['IssueTitle'])],
                [Paragraph(description[:300] + ('...' if len(description) > 300 else ''), self.styles['BodyText'])],
            ]
            
            if recommendation:
                issue_data.append([Paragraph(f"<b>Empfehlung:</b> {recommendation[:200]}", self.styles['BodyText'])])
            
            if risk:
                issue_data.append([Paragraph(f"<b>Risiko:</b> {self._format_euro(risk)}", self.styles['BodyText'])])
            
            issue_table = Table(issue_data, colWidths=[16*cm])
            issue_table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, -1), self.light_gray),
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ]))
            content.append(issue_table)
            content.append(Spacer(1, 0.3*cm))
        
        if len(issues) > 10:
            content.append(Paragraph(
                f"... und {len(issues) - 10} weitere Probleme. Vollständige Liste im Dashboard verfügbar.",
                self.styles['BodyText']
            ))
        
        return content
    
    def _create_recommendations(self, analysis_data: Dict[str, Any]) -> List:
        content = []
        
        content.append(Paragraph("Handlungsempfehlungen", self.styles['SectionHeading']))
        
        score = analysis_data.get('compliance_score', analysis_data.get('score', 0))
        try:
            score = float(score) if score else 0
        except:
            score = 0
        
        if score >= 90:
            recommendations = [
                "Regelmäßige Überprüfung beibehalten (monatlich empfohlen)",
                "Dokumentation der Compliance-Maßnahmen aktualisieren",
                "Mitarbeiter-Schulungen zu Datenschutz durchführen"
            ]
        elif score >= 70:
            recommendations = [
                "Identifizierte Warnungen zeitnah beheben",
                "Cookie-Banner Konfiguration überprüfen",
                "Barrierefreiheit der Website verbessern",
                "Regelmäßige Scans einrichten (wöchentlich empfohlen)"
            ]
        else:
            recommendations = [
                "SOFORTIGE MASSNAHMEN erforderlich",
                "Kritische Compliance-Lücken priorisiert schließen",
                "Rechtliche Beratung in Erwägung ziehen",
                "Alle Datenschutzerklärungen aktualisieren",
                "Cookie-Consent-Management implementieren/überarbeiten",
                "Barrierefreiheits-Anforderungen (BFSG) umsetzen"
            ]
        
        for idx, rec in enumerate(recommendations, 1):
            content.append(Paragraph(f"{idx}. {rec}", self.styles['BodyText']))
        
        content.append(Spacer(1, 1*cm))
        return content
    
    def _create_footer(self) -> List:
        content = []
        
        content.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#E2E8F0'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        content.append(Paragraph(
            f"Generiert von Complyo.tech am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}",
            self.styles['Footer']
        ))
        content.append(Paragraph(
            "Dieser Report dient als Dokumentation und ersetzt keine rechtliche Beratung.",
            self.styles['Footer']
        ))
        content.append(Paragraph(
            "© 2025 Complyo - KI-gestützte Website-Compliance | www.complyo.tech",
            self.styles['Footer']
        ))
        
        return content

pdf_generator = ComplianceReportGenerator()
