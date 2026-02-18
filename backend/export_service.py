"""
Export Service für Complyo
Generiert PDF- und HTML-Exporte von Fixes
"""

import asyncpg
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.export_dir = "/tmp/complyo_exports"
        os.makedirs(self.export_dir, exist_ok=True)
    
    async def export_fix(
        self,
        fix_id: int,
        user_id: int,
        export_format: str = 'html'
    ) -> Dict[str, Any]:
        """
        Exportiert einen Fix als HTML oder PDF
        
        Args:
            fix_id: ID des Fixes
            user_id: User ID (für Permission-Check)
            export_format: 'html' oder 'pdf'
        
        Returns:
            Dict mit download_url und export_info
        """
        try:
            # Hole Fix-Daten
            async with self.db_pool.acquire() as conn:
                fix = await conn.fetchrow(
                    """
                    SELECT 
                        gf.*,
                        COALESCE(ul.plan_type, 'expert') as plan_type,
                        COALESCE(ul.exports_this_month, 0) as exports_this_month,
                        COALESCE(ul.exports_max, 999) as exports_max
                    FROM generated_fixes gf
                    LEFT JOIN user_limits ul ON gf.user_id = ul.user_id
                    WHERE gf.id = $1 AND gf.user_id = $2
                    """,
                    fix_id,
                    user_id
                )
                
                if not fix:
                    raise Exception("Fix not found or access denied")
                
                # Check Export-Limit (nur für AI Plan)
                if fix['plan_type'] == 'ai':
                    if fix['exports_this_month'] >= fix['exports_max']:
                        raise Exception(f"Export-Limit erreicht: {fix['exports_max']}/Monat")
                
                # Generiere Export
                if export_format == 'html':
                    file_path, file_name = await self._export_as_html(fix)
                elif export_format == 'pdf':
                    file_path, file_name = await self._export_as_pdf(fix)
                else:
                    raise Exception(f"Unsupported format: {export_format}")
                
                # Update DB: Markiere als exportiert
                await conn.execute(
                    """
                    UPDATE generated_fixes
                    SET exported = TRUE, exported_at = CURRENT_TIMESTAMP, export_format = $1
                    WHERE id = $2
                    """,
                    export_format,
                    fix_id
                )
                
                # Increment Export-Counter (nur für AI Plan)
                if fix['plan_type'] == 'ai':
                    await conn.execute(
                        """
                        UPDATE user_limits
                        SET exports_this_month = exports_this_month + 1
                        WHERE user_id = $1
                        """,
                        user_id
                    )
                
                # Speichere in export_history
                await conn.execute(
                    """
                    INSERT INTO export_history (user_id, fix_id, export_format)
                    VALUES ($1, $2, $3)
                    """,
                    user_id,
                    fix_id,
                    export_format
                )
                
                logger.info(f"✅ Exported fix {fix_id} as {export_format}")
                
                return {
                    'success': True,
                    'download_url': f"/api/v2/fixes/{fix_id}/download/{file_name}",
                    'file_name': file_name,
                    'format': export_format,
                    'file_size_bytes': os.path.getsize(file_path),
                    'exported_at': datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Export error: {e}", exc_info=True)
            raise
    
    async def _export_as_html(self, fix: asyncpg.Record) -> tuple[str, str]:
        """Generiert HTML-Export"""
        # Parse fix content (stored as JSON string in DB)
        import json
        
        # Try to parse content_hash column which might contain the actual fix data
        # For now, create a simple HTML template
        fix_category = fix['issue_category']
        fix_type = fix['fix_type']
        generated_at = fix['generated_at']
        
        html_content = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complyo Fix Export - {fix_category}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            color: #3b82f6;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6b7280;
            font-size: 14px;
        }}
        .category {{
            display: inline-block;
            background: #dbeafe;
            color: #1e40af;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            margin-bottom: 20px;
        }}
        h1 {{
            font-size: 28px;
            margin: 20px 0;
            color: #1f2937;
        }}
        .meta {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 30px;
            font-size: 14px;
            color: #6b7280;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .code-block {{
            background: #1f2937;
            color: #10b981;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
        }}
        .step {{
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .step-number {{
            display: inline-block;
            background: #3b82f6;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            text-align: center;
            line-height: 28px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #9ca3af;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Complyo</div>
            <div class="subtitle">KI-gestützte Website-Compliance</div>
        </div>
        
        <span class="category">{fix_category.upper()}</span>
        
        <h1>Compliance-Fix Export</h1>
        
        <div class="meta">
            <strong>Fix-Typ:</strong> {fix_type}<br>
            <strong>Generiert am:</strong> {generated_at.strftime('%d.%m.%Y um %H:%M Uhr')}<br>
            <strong>Fix-ID:</strong> #{fix['id']}
        </div>
        
        <div class="section">
            <div class="section-title">📝 Beschreibung</div>
            <p>Dieser Fix behebt Compliance-Probleme im Bereich <strong>{fix_category}</strong> auf Ihrer Website.</p>
        </div>
        
        <div class="warning">
            <strong>⚠️ Wichtiger Hinweis:</strong> Bitte überprüfen Sie alle Angaben sorgfältig und passen Sie die Platzhalter an Ihre spezifischen Daten an.
        </div>
        
        <div class="section">
            <div class="section-title">🔧 Umsetzung</div>
            <p>Folgen Sie den Schritten unten, um die Compliance-Probleme zu beheben:</p>
            
            <div class="step">
                <span class="step-number">1</span>
                <strong>Code einfügen</strong><br>
                Kopieren Sie den unten stehenden Code und fügen Sie ihn in Ihre Website ein.
            </div>
            
            <div class="step">
                <span class="step-number">2</span>
                <strong>Platzhalter ersetzen</strong><br>
                Ersetzen Sie alle Platzhalter [in eckigen Klammern] mit Ihren eigenen Daten.
            </div>
            
            <div class="step">
                <span class="step-number">3</span>
                <strong>Testen</strong><br>
                Überprüfen Sie die Funktionalität auf Ihrer Live-Website.
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">💻 Code</div>
            <div class="code-block">
                <!-- Code wird hier eingefügt -->
                Hier würde der generierte Code stehen.
                In der finalen Version wird dieser aus der Datenbank geladen.
            </div>
        </div>
        
        <div class="footer">
            <p>Exportiert von Complyo.tech | © 2025 Complyo</p>
            <p>Diese Datei wurde automatisch generiert und dient als Dokumentation Ihrer Compliance-Maßnahmen.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Save to file
        file_name = f"complyo_fix_{fix['id']}_{fix_category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        file_path = os.path.join(self.export_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✅ HTML export saved: {file_path}")
        return file_path, file_name
    
    async def _export_as_pdf(self, fix: asyncpg.Record) -> tuple[str, str]:
        """Generiert PDF-Export mit ReportLab"""
        fix_category = fix['issue_category']
        fix_type = fix['fix_type']
        generated_at = fix['generated_at']
        
        file_name = f"complyo_fix_{fix['id']}_{fix_category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(self.export_dir, file_name)
        
        # Create PDF
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12
        )
        
        # Build PDF content
        content = []
        
        # Title
        content.append(Paragraph("Complyo Compliance-Fix", title_style))
        content.append(Spacer(1, 0.5*cm))
        
        # Metadata Table
        meta_data = [
            ['Fix-ID:', f"#{fix['id']}"],
            ['Kategorie:', fix_category],
            ['Fix-Typ:', fix_type],
            ['Generiert am:', generated_at.strftime('%d.%m.%Y um %H:%M Uhr')],
        ]
        
        meta_table = Table(meta_data, colWidths=[4*cm, 12*cm])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f9ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        content.append(meta_table)
        content.append(Spacer(1, 1*cm))
        
        # Description
        content.append(Paragraph("Beschreibung", heading_style))
        content.append(Paragraph(
            f"Dieser Fix behebt Compliance-Probleme im Bereich <b>{fix_category}</b> auf Ihrer Website.",
            styles['BodyText']
        ))
        content.append(Spacer(1, 0.5*cm))
        
        # Warning
        content.append(Paragraph("⚠️ Wichtiger Hinweis", heading_style))
        content.append(Paragraph(
            "Bitte überprüfen Sie alle Angaben sorgfältig und passen Sie die Platzhalter an Ihre spezifischen Daten an.",
            styles['BodyText']
        ))
        content.append(Spacer(1, 0.5*cm))
        
        # Steps
        content.append(Paragraph("Umsetzungsschritte", heading_style))
        content.append(Paragraph(
            "1. Kopieren Sie den generierten Code<br/>"
            "2. Fügen Sie ihn in Ihre Website ein<br/>"
            "3. Ersetzen Sie alle Platzhalter [in eckigen Klammern]<br/>"
            "4. Testen Sie die Funktionalität",
            styles['BodyText']
        ))
        content.append(Spacer(1, 1*cm))
        
        # Footer
        content.append(Spacer(1, 2*cm))
        content.append(Paragraph(
            "_" * 80,
            styles['Normal']
        ))
        content.append(Paragraph(
            "Exportiert von Complyo.tech | © 2025 Complyo",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        ))
        
        # Build PDF
        doc.build(content)
        
        logger.info(f"✅ PDF export saved: {file_path}")
        return file_path, file_name

