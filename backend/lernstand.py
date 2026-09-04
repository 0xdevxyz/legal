"""Lernstand: was hat complyo aus den Entscheidungen der Kunden gelernt?

Je Befundtyp: wie viele Vorschläge, wie viele angenommen, wie viele abgelehnt —
und woran die Ablehnungen lagen.

**Warum das der wichtigste Baustein ist.** Ohne diese Auswertung ist ein
Ablehnungsgrund nur eine Textspalte. Erst wenn dreißig davon nebeneinander
stehen, wird sichtbar, ob ein Verfahren systematisch danebenliegt oder ob
zwei Kunden Geschmacksfragen hatten. Genau das ist die Grundlage, auf der
später ein Skill überhaupt Belege haben kann (Roadmap Phase 3).

**Die Auswertung meldet ihre eigenen blinden Flecken.** Ablehnungsgründe gibt
es heute nur bei Alt-Texten; `accessibility_link_fixes` und
`accessibility_document_fixes` haben die Spalte nicht. Stünde das nirgends,
sähe eine Ablehnungsquote ohne Gründe aus wie „niemand hatte einen Grund"
statt wie „hier kann keiner erfasst werden". Deshalb trägt jeder Eintrag
`gruende_erfassbar`.

**Und sie sagt, wann ihre Zahlen nichts wert sind.** Unter
`BELEGE_MINDESTENS` Entscheidungen ist eine Quote Rauschen. Der Wert steht
bewusst hier und nicht in der Oberfläche: eine Zahl, die nicht trägt, soll
schon an der Quelle als solche gekennzeichnet sein.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Ab wie vielen Entscheidungen eine Quote überhaupt etwas aussagt.
# Dieselbe Schwelle, die später ein Skill braucht, um `aktiv` werden zu dürfen.
BELEGE_MINDESTENS = 30

# Wie viele Ablehnungsgründe je Typ ausgewiesen werden.
GRUENDE_ANZAHL = 5


# Die drei Fix-Tabellen. `typ_spalte` ist None, wenn die Tabelle selbst der
# Befundtyp ist — bei Dokumentfixes steckt der Typ dagegen in einer Spalte.
QUELLEN = [
    {
        "tabelle": "accessibility_alt_text_fixes",
        "befundtyp": "bild-ohne-alt-text",
        "typ_spalte": None,
        "grund_spalte": "rejected_reason",
    },
    {
        "tabelle": "accessibility_link_fixes",
        "befundtyp": "linktext-ohne-bedeutung",
        "typ_spalte": None,
        "grund_spalte": None,
    },
    {
        "tabelle": "accessibility_document_fixes",
        "befundtyp": None,
        "typ_spalte": "fix_type",
        "grund_spalte": None,
    },
]


def _quote(angenommen: int, abgelehnt: int) -> Optional[float]:
    """Annahmequote — None, wenn es nichts zu teilen gibt.

    Bewusst None statt 0.0 oder 1.0: „keine Entscheidung" ist nicht dasselbe
    wie „alles abgelehnt", und eine 100 %-Quote aus drei Zustimmungen ist
    keine 100 %.
    """
    entschieden = angenommen + abgelehnt
    if entschieden == 0:
        return None
    return round(angenommen / entschieden, 3)


async def _eine_quelle(conn, quelle: Dict[str, Any], tage: int) -> List[Dict[str, Any]]:
    """Zahlen einer Tabelle, gegebenenfalls nach Typ aufgeteilt."""
    tabelle = quelle["tabelle"]
    typ_spalte = quelle["typ_spalte"]
    gruppierung = typ_spalte or "'x'"

    rows = await conn.fetch(
        f"""
        SELECT {gruppierung} AS typ,
               count(*)                                              AS vorgeschlagen,
               count(*) FILTER (WHERE status = 'approved')           AS angenommen,
               count(*) FILTER (WHERE status = 'rejected')           AS abgelehnt,
               count(*) FILTER (WHERE status = 'pending')            AS offen,
               count(*) FILTER (WHERE status = 'deployed')           AS ausgeliefert,
               avg(confidence) FILTER (WHERE status = 'approved')    AS konfidenz_angenommen,
               avg(confidence) FILTER (WHERE status = 'rejected')    AS konfidenz_abgelehnt,
               max(created_at)                                       AS zuletzt
        FROM {tabelle}
        WHERE created_at > NOW() - ($1 || ' days')::interval
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        str(tage),
    )

    ergebnis = []
    for r in rows:
        befundtyp = quelle["befundtyp"] or f"dokument:{r['typ']}"
        eintrag = {
            "befundtyp": befundtyp,
            "quelle": tabelle,
            "vorgeschlagen": r["vorgeschlagen"],
            "angenommen": r["angenommen"],
            "abgelehnt": r["abgelehnt"],
            "offen": r["offen"],
            "ausgeliefert": r["ausgeliefert"],
            "annahmequote": _quote(r["angenommen"], r["abgelehnt"]),
            "zuletzt": r["zuletzt"].isoformat() if r["zuletzt"] else None,
            # Trennt die Konfidenz Zustimmung von Ablehnung? Wenn nicht, ist
            # der Wert als Vorfilter wertlos — eine Aussage, die man nur mit
            # beiden Zahlen nebeneinander treffen kann.
            "konfidenz_angenommen": (
                round(float(r["konfidenz_angenommen"]), 3)
                if r["konfidenz_angenommen"] is not None else None
            ),
            "konfidenz_abgelehnt": (
                round(float(r["konfidenz_abgelehnt"]), 3)
                if r["konfidenz_abgelehnt"] is not None else None
            ),
            "gruende_erfassbar": quelle["grund_spalte"] is not None,
            "ablehngruende": [],
        }
        eintrag["belege_reichen"] = (
            eintrag["angenommen"] + eintrag["abgelehnt"] >= BELEGE_MINDESTENS
        )
        ergebnis.append(eintrag)

    # Ablehnungsgründe nur, wo die Spalte existiert.
    if quelle["grund_spalte"]:
        gruende = await conn.fetch(
            f"""
            SELECT {quelle['grund_spalte']} AS grund, count(*) AS anzahl
            FROM {tabelle}
            WHERE status = 'rejected'
              AND {quelle['grund_spalte']} IS NOT NULL
              AND {quelle['grund_spalte']} <> ''
              AND created_at > NOW() - ($1 || ' days')::interval
            GROUP BY 1 ORDER BY 2 DESC LIMIT {GRUENDE_ANZAHL}
            """,
            str(tage),
        )
        liste = [{"grund": g["grund"], "anzahl": g["anzahl"]} for g in gruende]
        for e in ergebnis:
            e["ablehngruende"] = liste

    return ergebnis


async def _pruefregeln(conn, tage: int) -> Dict[str, Any]:
    """Die automatisch erzeugten Prüfregeln — der zweite Lernweg.

    Von 159 automatisch erzeugten Checks waren am 04.09.2026 **124
    abgeschaltet**. Ohne diese Zahl neben den Fix-Quoten sieht die
    Regelerzeugung erfolgreicher aus, als sie ist.
    """
    r = await conn.fetchrow(
        """
        SELECT count(*) FILTER (WHERE auto_generated)                              AS erzeugt,
               count(*) FILTER (WHERE auto_generated AND status = 'active')        AS aktiv,
               count(*) FILTER (WHERE auto_generated AND status = 'disabled')      AS abgeschaltet,
               count(*) FILTER (WHERE auto_generated AND status = 'pending_review') AS wartet,
               count(*) FILTER (WHERE auto_generated AND status = 'disabled'
                                AND coalesce(generation_notes, '') ILIKE '%%abgelehnt%%') AS mit_grund
        FROM compliance_checks
        """
    )
    erzeugt = r["erzeugt"] or 0
    entschieden = (r["aktiv"] or 0) + (r["abgeschaltet"] or 0)
    return {
        "erzeugt": erzeugt,
        "aktiv": r["aktiv"],
        "abgeschaltet": r["abgeschaltet"],
        "wartet_auf_freigabe": r["wartet"],
        "annahmequote": _quote(r["aktiv"] or 0, r["abgeschaltet"] or 0),
        "abschaltungen_mit_grund": r["mit_grund"],
        "belege_reichen": entschieden >= BELEGE_MINDESTENS,
    }


async def erhebe_lernstand(db_pool, tage: int = 90) -> Dict[str, Any]:
    """Vollständiger Lernstand. Wirft nicht — ein Teilausfall verliert nur
    diesen Teil, nicht die ganze Auswertung."""
    befunde: List[Dict[str, Any]] = []
    fehler: List[str] = []

    async with db_pool.acquire() as conn:
        for quelle in QUELLEN:
            try:
                befunde.extend(await _eine_quelle(conn, quelle, tage))
            except Exception as e:
                logger.warning(f"Lernstand: {quelle['tabelle']} nicht lesbar: {e}")
                fehler.append(f"{quelle['tabelle']}: {type(e).__name__}")

        try:
            regeln = await _pruefregeln(conn, tage)
        except Exception as e:
            logger.warning(f"Lernstand: Pruefregeln nicht lesbar: {e}")
            regeln = None
            fehler.append(f"compliance_checks: {type(e).__name__}")

    befunde.sort(key=lambda e: e["vorgeschlagen"], reverse=True)

    entschieden_gesamt = sum(e["angenommen"] + e["abgelehnt"] for e in befunde)
    mit_belegen = [e["befundtyp"] for e in befunde if e["belege_reichen"]]
    ohne_grunderfassung = sorted(
        {e["befundtyp"] for e in befunde if not e["gruende_erfassbar"]}
    )
    ablehnungen_gesamt = sum(e["abgelehnt"] for e in befunde)

    return {
        "zeitraum_tage": tage,
        "befundtypen": befunde,
        "pruefregeln": regeln,
        "entscheidungen_gesamt": entschieden_gesamt,
        "ablehnungen_gesamt": ablehnungen_gesamt,
        "belege_mindestens": BELEGE_MINDESTENS,
        "typen_mit_belegen": mit_belegen,
        # Aussagekraeftig ist der Lernstand erst, wenn WENIGSTENS EIN Befundtyp
        # fuer sich genug Entscheidungen hat.
        #
        # Vorher stand hier `entschieden_gesamt >= BELEGE_MINDESTENS`. Beim
        # ersten Lauf gegen echte Daten meldete die Auswertung damit
        # "aussagekraeftig: True" bei 42 Entscheidungen — waehrend jede einzelne
        # Zeile "Belege reichen nicht" sagte, weil keine Art fuer sich auch nur
        # 24 erreichte. Eine Quote entsteht je Befundtyp, nicht ueber alle
        # zusammen; 30 Entscheidungen aus sechs verschiedenen Verfahren sagen
        # ueber keines davon etwas.
        "aussagekraeftig": bool(mit_belegen),
        # Zweiter Vorbehalt: ohne eine einzige Ablehnung ist jede Quote 100 %,
        # und daraus laesst sich nichts lernen. Erst die Ablehnung sagt, WO ein
        # Verfahren danebenliegt.
        "ablehnungen_vorhanden": ablehnungen_gesamt > 0,
        "ohne_grunderfassung": ohne_grunderfassung,
        "fehler": fehler,
    }
