"""
AUDIT-09 bis AUDIT-13: Extended WCAG Checks Tests
Tests für: Touch-Targets, WCAG AAA, Tabellen/SVG/Canvas, Video Captions, PDF-Links
"""
import sys
import os
sys.path.insert(0, '/app')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
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


def test_svg_without_title_and_role():
    html = '<svg width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert any('SVG' in i['title'] for i in issues)


def test_svg_aria_hidden_ignored():
    html = '<svg aria-hidden="true" width="10" height="10"></svg>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_tables_svg_canvas(soup)
    assert not any('SVG' in i['title'] for i in issues)


def test_svg_with_title_and_role_no_issue():
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
    html = '<video src="film.mp4" controls></video>'
    soup = BeautifulSoup(html, 'html.parser')
    issues = _check_video_captions(soup)
    assert len(issues) == 1
    assert '1.2.2' in issues[0]['title']
    assert issues[0]['severity'] == 'error'


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
