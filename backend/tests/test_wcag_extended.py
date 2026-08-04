"""
AUDIT-09 bis AUDIT-13: Extended WCAG Checks Tests
Tests für: Touch-Targets, WCAG AAA, Tabellen/SVG/Canvas, Video Captions, PDF-Links
"""
import sys
import os
sys.path.insert(0, '/app')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from compliance_engine.checks.barrierefreiheit_check import (
    _check_touch_targets,
    _check_wcag_aaa,
    _check_tables_svg_canvas,
    _check_video_captions,
    _check_pdf_links,
)


# =============================================================================
# AUDIT-09: Touch-Targets (WCAG 2.5.5)
# =============================================================================

def test_touch_target_too_small():
    html = '<button style="width:30px; height:30px;">OK</button>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_touch_targets(soup)
    assert len(issues) == 1
    assert '2.5.5' in issues[0]['title']
    assert issues[0]['severity'] == 'warning'


def test_touch_target_acceptable_size():
    html = '<button style="width:44px; height:44px;">OK</button>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_touch_targets(soup)
    assert len(issues) == 0


def test_touch_target_no_inline_style():
    html = '<button>Submit</button>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_touch_targets(soup)
    assert len(issues) == 0


# =============================================================================
# AUDIT-10: WCAG AAA Checks
# =============================================================================

def test_wcag_aaa_vague_links():
    html = '<a href="/foo">mehr</a><a href="/bar">hier</a>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_wcag_aaa(soup)
    titles = [i['title'] for i in issues]
    assert any('2.4.9' in t for t in titles)


def test_wcag_aaa_descriptive_links_no_issue():
    html = '<a href="/foo">Datenschutzerklärung lesen</a>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_wcag_aaa(soup)
    assert not any('2.4.9' in i['title'] for i in issues)


def test_wcag_aaa_low_line_height():
    html = '<body style="line-height: 1.2">text</body>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_wcag_aaa(soup)
    assert any('1.4.8' in i['title'] for i in issues)


# =============================================================================
# AUDIT-11: Tabellen / SVG / Canvas
# =============================================================================

def test_table_without_caption():
    html = '<table><tr><th>Name</th></tr><tr><td>Alice</td></tr></table>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert any('caption' in i['title'].lower() for i in issues)


def test_table_with_caption_no_issue():
    html = '<table><caption>Kundenliste</caption><tr><th scope="col">Name</th></tr></table>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('caption' in i['title'].lower() for i in issues)
    assert not any('scope' in i['title'].lower() for i in issues)


def test_th_without_scope():
    html = '<table><caption>T</caption><tr><th>Name</th><th>Age</th></tr></table>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert any('scope' in i['title'].lower() for i in issues)


def test_svg_mit_bildrolle_ohne_namen_wird_gemeldet():
    """role="img" sagt zu: hier steht ein Bild — dann ist ein Name Pflicht."""
    html = '<svg role="img" width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert any('SVG' in i['title'] for i in issues)


def test_icon_only_button_wird_gemeldet():
    """Ein Button, den nur ein Icon beschriftet, braucht einen Namen am SVG."""
    html = '<button><svg width="16" height="16"><path d="M0 0h4v4z"/></svg></button>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert any('SVG' in i['title'] for i in issues)


def test_nacktes_deko_icon_ist_kein_verstoss():
    """
    Regressionsschutz: Lucide-Icons ohne role wurden je einzeln gemeldet —
    59 Phantom-Issues auf complyo.de zogen die Säule von 100 auf 0.
    """
    html = '<svg width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('SVG' in i['title'] for i in issues)


def test_icon_neben_text_ist_deko():
    """Das Häkchen neben "24/7 Support" trägt keine eigene Information."""
    html = '<li><svg width="16" height="16"><path d="M0 0h4v4z"/></svg>24/7 Support</li>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('SVG' in i['title'] for i in issues)


def test_button_mit_text_macht_icon_zur_deko():
    html = '<button><svg width="16" height="16"></svg> Speichern</button>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('SVG' in i['title'] for i in issues)


def test_icon_button_mit_aria_label_ist_ok():
    html = '<button aria-label="Menü öffnen"><svg width="16" height="16"></svg></button>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('SVG' in i['title'] for i in issues)


def test_svg_mit_aria_label_ohne_title_ist_ok():
    """aria-label benennt die Grafik — ein <title> ist dann nicht zusätzlich nötig."""
    html = '<svg role="img" aria-label="Firmenlogo"></svg>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('SVG' in i['title'] for i in issues)


def test_svg_befunde_werden_zu_einem_issue_gebuendelt():
    """Viele betroffene Grafiken → ein Issue mit Anzahl, nicht N Issues."""
    html = '<div>' + '<svg role="img"></svg>' * 12 + '</div>'
    soup = BeautifulSoup(html, 'html.parser')
    svg_issues = [i for i in _check_tables_svg_canvas(soup) if 'SVG' in i['title']]
    assert len(svg_issues) == 1
    assert '12' in svg_issues[0]['title']


def test_svg_aria_hidden_ignored():
    html = '<svg aria-hidden="true" width="10" height="10"></svg>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('SVG' in i['title'] for i in issues)


def test_svg_mit_title_und_rolle_ist_ok():
    html = '<svg role="img"><title>Logo</title></svg>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('SVG' in i['title'] for i in issues)


def test_canvas_without_aria_label():
    html = '<canvas width="200" height="200"></canvas>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert any('canvas' in i['title'].lower() for i in issues)


def test_canvas_with_aria_label_no_issue():
    html = '<canvas aria-label="Statistik-Diagramm" width="200" height="200"></canvas>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('canvas' in i['title'].lower() for i in issues)


# =============================================================================
# AUDIT-12: Video Captions
# =============================================================================

def test_video_without_captions():
    """
    Titel ohne "WCAG 1.2.2:"-Präfix und Stufe 'critical' statt 'error'.

    Das Präfix machte den Fund für die Zusammenfassung unkenntlich — der
    Media-Check meldet denselben Mangel als "Video ohne Untertitel", beide
    standen doppelt im Report. Die Stufe 'error' kannte der ScoreCalculator
    nicht: der Befund kostete keinen einzigen Punkt. Der Normbezug steht
    weiterhin in legal_basis.
    """
    html = '<video src="film.mp4" controls></video>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_video_captions(soup)
    assert len(issues) == 1
    assert issues[0]['title'] == 'Video ohne Untertitel'
    assert issues[0]['severity'] == 'critical'
    assert '1.2.2' in issues[0]['legal_basis']


def test_video_with_captions_no_error():
    html = '<video src="film.mp4"><track kind="captions" src="sub.vtt" srclang="de" label="Deutsch"></video>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_video_captions(soup)
    assert len(issues) == 0


def test_video_caption_track_without_srclang():
    html = '<video src="film.mp4"><track kind="captions" src="sub.vtt"></video>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_video_captions(soup)
    assert any('srclang' in i['title'].lower() for i in issues)


def test_no_video_no_issues():
    html = '<div>Kein Video hier</div>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_video_captions(soup)
    assert len(issues) == 0


# =============================================================================
# AUDIT-13: PDF-Links
# =============================================================================

def test_pdf_link_detected():
    html = '<a href="/dokumente/anleitung.pdf">Anleitung herunterladen</a>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_pdf_links(soup)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'info'
    assert 'PDF' in issues[0]['title']


def test_pdf_link_in_text_detected():
    html = '<a href="/download">Broschüre als PDF</a>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_pdf_links(soup)
    assert len(issues) == 1


def test_no_pdf_no_issue():
    html = '<a href="/page">Normale Seite</a>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_pdf_links(soup)
    assert len(issues) == 0


def test_pdf_risk_euro_is_zero():
    html = '<a href="/doc.pdf">Dokument</a>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_pdf_links(soup)
    assert issues[0]['risk_euro'] == 0
