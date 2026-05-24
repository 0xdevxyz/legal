"""Unit tests for AgencyReportGenerator (AGENCY-03 PDF generation)."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from agency_report_generator import AgencyReportGenerator


# 1x1 transparent PNG (smallest valid PNG)
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f"
    b"\x00\x00\x01\x01\x00\x05\xdb\x9eN\xa9\x00\x00\x00\x00IEND\xaeB`\x82"
)

SAMPLE_SITES = [
    {"url": "https://kunde-a.de", "compliance_score": 85, "top_issues": ["Cookie banner missing", "Impressum incomplete", "No SSL"]},
    {"url": "https://kunde-b.de", "compliance_score": 60, "top_issues": ["Alt-Text fehlt"]},
]


class TestAgencyPDFGeneration:
    def setup_method(self):
        self.gen = AgencyReportGenerator()

    def test_pdf_generation_returns_bytes(self):
        result = self.gen.generate(client_name="Test", sites=SAMPLE_SITES)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_pdf_starts_with_pdf_header(self):
        result = self.gen.generate(client_name="Test", sites=SAMPLE_SITES)
        assert result[:5] == b"%PDF-"

    def test_pdf_generation_empty_sites(self):
        result = self.gen.generate(client_name="Acme", sites=[])
        assert result[:5] == b"%PDF-"

    def test_pdf_with_logo_embeds_without_error(self):
        result = self.gen.generate(client_name="Test", sites=SAMPLE_SITES, agency_logo_bytes=TINY_PNG)
        assert result[:5] == b"%PDF-"
        assert len(result) > 1000

    def test_pdf_contains_client_name(self):
        result = self.gen.generate(client_name="Mustermann GmbH", sites=SAMPLE_SITES)
        assert b"Mustermann GmbH" in result

    def test_pdf_handles_missing_compliance_score(self):
        sites = [{"url": "https://x.de", "compliance_score": None, "top_issues": []}]
        result = self.gen.generate(client_name="Test", sites=sites)
        assert result[:5] == b"%PDF-"

    def test_pdf_handles_top_issues_list_truncated(self):
        sites = [{"url": "https://x.de", "compliance_score": 75,
                  "top_issues": ["Issue 1", "Issue 2", "Issue 3", "Issue 4", "Issue 5"]}]
        result = self.gen.generate(client_name="Test", sites=sites)
        assert b"Issue 1" in result
        assert b"Issue 2" in result
        assert b"Issue 3" in result
        # 4th and 5th MUST NOT appear (top-3 truncation)
        assert b"Issue 4" not in result
        assert b"Issue 5" not in result
