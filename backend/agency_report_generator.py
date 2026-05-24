"""
Agency Report Generator (Phase 10 / AGENCY-03)

Produces a branded PDF report for one agency client, embedding:
- Agency logo (PNG, optional)
- Client name + generation date
- Per-site rows: URL + compliance_score + top-3 issues

Pure class — no FastAPI/db dependencies. Callable from any route handler.
"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus import Image as RLImage

logger = logging.getLogger(__name__)


class AgencyReportGenerator:
    """Generates branded per-client compliance PDF reports."""

    TOP_ISSUES_LIMIT = 3  # per AGENCY-03: top 3 issues per site

    def __init__(self):
        self.page_width, self.page_height = A4
        self.styles = self._create_styles()

    def _create_styles(self):
        styles = getSampleStyleSheet()
        agency_blue = colors.Color(102 / 255, 126 / 255, 234 / 255)
        agency_grey = colors.Color(60 / 255, 60 / 255, 60 / 255)

        styles.add(ParagraphStyle(
            name='AgencyTitle', parent=styles['Title'],
            fontSize=22, textColor=agency_blue, alignment=TA_CENTER,
            spaceAfter=12, fontName='Helvetica-Bold',
        ))
        styles.add(ParagraphStyle(
            name='AgencySubtitle', parent=styles['Normal'],
            fontSize=12, textColor=agency_grey, alignment=TA_CENTER,
            spaceAfter=18, fontName='Helvetica',
        ))
        styles.add(ParagraphStyle(
            name='AgencyH1', parent=styles['Heading1'],
            fontSize=16, textColor=agency_blue, fontName='Helvetica-Bold',
            spaceBefore=12, spaceAfter=8,
        ))
        styles.add(ParagraphStyle(
            name='AgencyBody', parent=styles['Normal'],
            fontSize=10, textColor=agency_grey, alignment=TA_LEFT,
            spaceAfter=4,
        ))
        return styles

    def _normalize_logo(self, logo_bytes: bytes) -> io.BytesIO:
        """Convert logo bytes to RGB PNG BytesIO for safe ReportLab embedding.

        ReportLab's ImageReader.getRGBData() calls im.split() on RGBA images,
        which can fail on small/compressed PNGs. Converting to RGB with
        LOAD_TRUNCATED_IMAGES=True avoids this issue.
        """
        try:
            from PIL import Image as PILImage, ImageFile
            # Allow loading truncated/minimal PNGs (e.g. 1x1 test images)
            ImageFile.LOAD_TRUNCATED_IMAGES = True
            img = PILImage.open(io.BytesIO(logo_bytes))
            # Convert to RGB to avoid ReportLab RGBA split() failures
            img = img.convert('RGB')
            out = io.BytesIO()
            img.save(out, format='PNG')
            out.seek(0)
            return out
        except Exception:
            # Pillow not available or conversion failed — use raw bytes
            return io.BytesIO(logo_bytes)

    def generate(
        self,
        client_name: str,
        sites: List[Dict[str, Any]],
        agency_logo_bytes: Optional[bytes] = None,
        generated_at: str = "",
    ) -> bytes:
        """Build the PDF and return its bytes.

        Args:
            client_name: Display name of the agency's client.
            sites: List of {"url": str, "compliance_score": int|None,
                            "top_issues": List[str]} dicts.
            agency_logo_bytes: Optional PNG file content. Embedded at top of report.
            generated_at: Optional date string. Defaults to today (DE format).
        Returns:
            PDF file bytes (starts with b"%PDF-").
        """
        if not generated_at:
            generated_at = datetime.now().strftime("%d.%m.%Y")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm, leftMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
            title=f"Compliance-Report {client_name}",
            author="Complyo Agency Report",
            pageCompression=0,
        )

        story: List[Any] = []

        # Logo (if provided)
        if agency_logo_bytes:
            try:
                logo_buf = self._normalize_logo(agency_logo_bytes)
                logo = RLImage(
                    logo_buf,
                    width=4 * cm, height=2 * cm, kind='proportional',
                )
                story.append(logo)
                story.append(Spacer(1, 0.5 * cm))
            except Exception as e:
                logger.warning(f"Agency logo embed failed (skipped): {e}")

        # Title block
        story.append(Paragraph(f"Compliance-Report: {client_name}", self.styles['AgencyTitle']))
        story.append(Paragraph(f"Erstellt am {generated_at}", self.styles['AgencySubtitle']))

        # Per-site table
        story.append(Paragraph("Websites im Überblick", self.styles['AgencyH1']))

        if not sites:
            story.append(Paragraph(
                "Keine Websites diesem Kunden zugeordnet.", self.styles['AgencyBody']
            ))
        else:
            table_data: List[List[Any]] = [
                ["Website", "Score", "Top 3 Issues"],
            ]
            for site in sites:
                url = site.get("url") or "—"
                score = site.get("compliance_score")
                score_str = f"{score}/100" if isinstance(score, int) else "—"
                issues = site.get("top_issues") or []
                # AGENCY-03: top-3 truncation
                top_3 = issues[:self.TOP_ISSUES_LIMIT]
                issues_str = "\n".join(f"• {i}" for i in top_3) if top_3 else "—"
                table_data.append([
                    Paragraph(url, self.styles['AgencyBody']),
                    Paragraph(score_str, self.styles['AgencyBody']),
                    Paragraph(issues_str.replace("\n", "<br/>"), self.styles['AgencyBody']),
                ])

            table = Table(table_data, colWidths=[6 * cm, 2 * cm, 8 * cm], repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]))
            story.append(table)

        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(
            "Powered by Complyo — DSGVO-, BFSG- und Rechtstext-Compliance.",
            self.styles['AgencySubtitle'],
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
