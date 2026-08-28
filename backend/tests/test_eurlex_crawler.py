"""
Tests fuer den EUR-Lex-Korpus-Updater (Audit 2026-08).

Realer Prod-Fall: der Crawler schnitt die ersten 5.000 Zeichen des gestrippten
HTML heraus. Bei EUR-Lex ist das der JavaScript-Kopf der Seite. Alle 25 Dateien
im Vault trugen damit denselben jQuery- und Tracking-Schnipsel als
"Gesetzestext", monatelang und ohne Fehlermeldung.
"""

import pytest

from cronjobs.eurlex_crawler import (
    parse_artikel,
    qualitaet_ok,
    schreibe_artikel,
    _artikel_nummer,
    _sortier_key,
    MIN_ARTIKEL,
)

# Aufbau wie im Cellar-XHTML der Publications Office
CELLAR_XHTML = """
<html><body>
  <div class="eli-container">
    <p class="oj-normal">Erwaegungsgrund ohne Artikelstruktur, faellt heraus.</p>
    {artikel}
  </div>
</body></html>
"""

ARTIKEL_TMPL = """
    <div class="eli-subdivision" id="art_{n}">
      <p id="d1e{n}" class="oj-ti-art">Artikel {n}</p>
      <div class="eli-title" id="art_{n}.tit_1"><p class="oj-sti-art">{titel}</p></div>
      <div id="00{n}"><p class="oj-normal">{text}</p></div>
    </div>
"""


def _dokument(anzahl=12, text=None):
    text = text or ("Die Anbieter stellen sicher, dass KI-Systeme, die fuer die direkte "
                    "Interaktion mit natuerlichen Personen bestimmt sind, entsprechend "
                    "gekennzeichnet werden und die Personen informiert werden.")
    artikel = "".join(
        ARTIKEL_TMPL.format(n=i, titel=f"Ueberschrift {i}", text=text)
        for i in range(1, anzahl + 1)
    )
    return CELLAR_XHTML.format(artikel=artikel)


# Der echte Muell aus knowledge/laws/de/AI_ACT.md vom 2026-08-24
GERUEST_MUELL = CELLAR_XHTML.format(artikel=ARTIKEL_TMPL.format(
    n=1, titel="EUR-Lex",
    text=('$(function(){ var lang = localStorage.getItem("lang") || "en"; '
          '$("#legislation-0").load("legislation-0.html", function(response, status, xhr) '
          '{ if (status === "success") { document.getElementById("x"); } });'),
))


def test_artikel_werden_erkannt():
    artikel = parse_artikel(_dokument(anzahl=12))
    assert len(artikel) == 12
    assert artikel[0]["nummer"] == "1"
    assert artikel[0]["ueberschrift"] == "Ueberschrift 1"
    assert "KI-Systeme" in artikel[0]["text"]


def test_erwaegungsgruende_fallen_heraus():
    artikel = parse_artikel(_dokument(anzahl=12))
    assert not any("faellt heraus" in a["text"] for a in artikel)


def test_qualitaet_ok_bei_echtem_text():
    ok, grund = qualitaet_ok(parse_artikel(_dokument(anzahl=12)))
    assert ok is True, grund


def test_seitengeruest_wird_verworfen():
    """Der Fall, der monatelang unbemerkt blieb."""
    ok, grund = qualitaet_ok(parse_artikel(GERUEST_MUELL))
    assert ok is False
    assert "Artikel" in grund or "Seitengeruest" in grund


def test_zu_wenige_artikel_werden_verworfen():
    ok, grund = qualitaet_ok(parse_artikel(_dokument(anzahl=MIN_ARTIKEL - 1)))
    assert ok is False and "Artikel" in grund


def test_kurze_artikel_fallen_heraus():
    artikel = parse_artikel(_dokument(anzahl=12, text="zu kurz"))
    assert artikel == []


@pytest.mark.parametrize("label,erwartet", [
    ("Artikel 50", "50"),
    ("Article 6", "6"),
    ("Articolo 113", "113"),
    ("Artikel 6a", "6a"),
    # Das franzoesische Amtsblatt schreibt den ersten Artikel aus. Ohne diese
    # Zuordnung fehlte Artikel 1 in jedem franzoesischen Rechtsakt (98 statt 99
    # Artikel bei der DSGVO, 112 statt 113 beim AI Act).
    ("Article premier", "1"),
    ("Articolo primo", "1"),
    ("Anhang III", None),
    ("", None),
])
def test_artikelnummer_aus_label(label, erwartet):
    assert _artikel_nummer(label) == erwartet


def test_sortierung_ist_numerisch():
    keys = [_sortier_key(n) for n in ["1", "2", "10", "50", "113"]]
    assert keys == sorted(keys)


def test_schreibt_datei_je_artikel(tmp_path, monkeypatch):
    from cronjobs import eurlex_crawler
    monkeypatch.setattr(eurlex_crawler, "LAWS_DIR", tmp_path)
    n = schreibe_artikel("AI_ACT", "DE", "32024R1689", parse_artikel(_dokument(anzahl=12)))
    assert n == 12
    art = tmp_path / "de" / "AI_ACT" / "art-001.md"
    assert art.exists()
    inhalt = art.read_text(encoding="utf-8")
    assert "law_id: AI_ACT" in inhalt
    assert "language: de" in inhalt
    assert "KI-Systeme" in inhalt
    # Uebersicht liegt IM Aktenverzeichnis, nicht auf dem kuratierten Stammwissen
    assert (tmp_path / "de" / "AI_ACT" / "00-uebersicht.md").exists()


def test_entfallene_artikel_bleiben_nicht_liegen(tmp_path, monkeypatch):
    from cronjobs import eurlex_crawler
    monkeypatch.setattr(eurlex_crawler, "LAWS_DIR", tmp_path)
    schreibe_artikel("AI_ACT", "DE", "32024R1689", parse_artikel(_dokument(anzahl=12)))
    schreibe_artikel("AI_ACT", "DE", "32024R1689", parse_artikel(_dokument(anzahl=11)))
    assert not (tmp_path / "de" / "AI_ACT" / "art-012.md").exists()


# ---------------- Der Vault muss die Artikel auch finden ----------------
# Zweiter Teil desselben Befunds: der Retriever globbte nur "laws/*.md" und
# liess damit alles liegen, was der Crawler in die Sprachordner schreibt.

def test_retriever_findet_artikeldateien(tmp_path, monkeypatch):
    from cronjobs import eurlex_crawler
    from knowledge import knowledge_retriever as kr

    monkeypatch.setattr(eurlex_crawler, "LAWS_DIR", tmp_path / "laws")
    schreibe_artikel("AI_ACT", "DE", "32024R1689", parse_artikel(_dokument(anzahl=12)))

    monkeypatch.setattr(kr, "META_DIR", tmp_path / "_meta")
    monkeypatch.setattr(kr, "EMBEDDINGS_CACHE_FILE", tmp_path / "_meta" / "embeddings.json")
    retriever = kr.KnowledgeRetriever(vault_root=tmp_path)
    docs = retriever._load_documents()

    pfade = [d["path"] for d in docs]
    assert any("AI_ACT/art-050.md" in p or "AI_ACT/art-001.md" in p for p in pfade), pfade
    assert any(d["frontmatter"].get("law_id") == "AI_ACT" for d in docs)
    # Sprache im Frontmatter, sonst filtert search_hybrid die Treffer weg
    assert all(
        d["frontmatter"].get("language") == "de"
        for d in docs if "AI_ACT" in d["path"]
    )


def test_retriever_cache_liest_unveraenderte_dateien_nicht_neu(tmp_path, monkeypatch):
    from cronjobs import eurlex_crawler
    from knowledge import knowledge_retriever as kr

    monkeypatch.setattr(eurlex_crawler, "LAWS_DIR", tmp_path / "laws")
    schreibe_artikel("AI_ACT", "DE", "32024R1689", parse_artikel(_dokument(anzahl=12)))

    monkeypatch.setattr(kr, "META_DIR", tmp_path / "_meta")
    monkeypatch.setattr(kr, "EMBEDDINGS_CACHE_FILE", tmp_path / "_meta" / "embeddings.json")
    retriever = kr.KnowledgeRetriever(vault_root=tmp_path)

    erste = retriever._load_documents()
    aufrufe = {"n": 0}
    echtes_parse = kr._parse_md_file

    def zaehlend(pfad):
        aufrufe["n"] += 1
        return echtes_parse(pfad)

    monkeypatch.setattr(kr, "_parse_md_file", zaehlend)
    zweite = retriever._load_documents()

    assert len(zweite) == len(erste) > 0
    assert aufrufe["n"] == 0


def test_kuratiertes_stammwissen_wird_nicht_ueberschrieben(tmp_path, monkeypatch):
    """
    Der Crawler hatte laws/en/AI_ACT.md, DSA.md und GDPR.md in Produktion
    ueberschrieben: handgeschriebene Zusammenfassungen, ersetzt durch den
    JavaScript-Kopf der EUR-Lex-Seite.
    """
    from cronjobs import eurlex_crawler
    monkeypatch.setattr(eurlex_crawler, "LAWS_DIR", tmp_path)
    stammwissen = tmp_path / "de" / "AI_ACT.md"
    stammwissen.parent.mkdir(parents=True, exist_ok=True)
    stammwissen.write_text("# Von Hand gepflegt\n", encoding="utf-8")

    schreibe_artikel("AI_ACT", "DE", "32024R1689", parse_artikel(_dokument(anzahl=12)))

    assert stammwissen.read_text(encoding="utf-8") == "# Von Hand gepflegt\n"
