"""
Complyo Accessibility Fix Saver
================================
Speichert AI-generierte Barrierefreiheits-Fixes in die Datenbank
"""

import asyncpg
import hashlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def _als_user_id(wert) -> "Optional[int]":
    """
    Bringt user_id auf den Spaltentyp integer.

    Die accessibility_*-Tabellen trugen bis zur Migration am 2026-08-04 eine
    uuid-Spalte, obwohl users.id integer ist — jeder Insert scheiterte still.
    Seither ist die Spalte integer, die Aufrufer reichen den Wert aber weiterhin
    als String durch (`str(user_id)` in public_routes). Leere Werte und
    Unkonvertierbares werden zu None: ein fehlender Nutzerbezug ist besser als
    ein abgebrochener Insert, denn die Fixes haengen fachlich an site_id.
    """
    if wert is None:
        return None
    if isinstance(wert, int):
        return wert
    text = str(wert).strip()
    if not text:
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        logger.warning(f"user_id '{text}' ist keine Zahl — Fix wird ohne Nutzerbezug gespeichert")
        return None


def _pruefe_site_zugehoerigkeit(row, erlaubte_sites) -> None:
    """
    Gehoert dieser Fix zu einer Website, die der Aufrufer betreuen darf?

    Vorher wurde stattdessen `row['user_id']` mit dem angemeldeten Nutzer
    verglichen — also gefragt: "hast DU diese Zeile erzeugt?". Das ist die
    falsche Frage. Ein Fix gehoert zu einer WEBSITE, nicht zu dem Konto, unter
    dem zufaellig der Scan lief.

    Die Folgen waren im Durchlauf sofort da: eine Seite wechselt den Betreuer —
    Agenturwechsel, Uebergabe an den Kunden, ein Kollege hat gescannt — und
    niemand kann mehr etwas freigeben. Der Endpunkt antwortete mit 403, die
    Oberflaeche zeigte davon nichts, der Knopf tat einfach nichts mehr.

    `erlaubte_sites` ist die Menge der site_ids, die der Aufrufer schon
    autorisiert hat (require_site_ownership). None bedeutet: der Aufrufer hat
    nicht autorisiert — dann wird nichts durchgelassen, denn "keine Angabe"
    darf nie "darf alles" heissen.
    """
    if erlaubte_sites is None:
        raise PermissionError("keine autorisierten Sites uebergeben")
    if row["site_id"] not in erlaubte_sites:
        raise PermissionError("fix gehoert zu einer fremden website")


class AccessibilityFixSaver:
    """
    Speichert AI-generierte Alt-Texte und andere Accessibility-Fixes
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def save_alt_text_fixes(
        self,
        site_id: str,
        scan_id: str,
        user_id,  # int oder String — wird normalisiert
        fixes: List[Dict[str, Any]],
        status: str = 'pending'  # Human-in-the-loop: NICHT mehr Auto-Approve
    ) -> int:
        """
        Speichert AI-generierte Alt-Texte in die Datenbank
        
        Args:
            site_id: Site-Identifier (z.B. "scan-91778ad450e1")
            scan_id: Scan-ID aus scan_history
            user_id: User UUID
            fixes: Liste von Alt-Text-Fixes
                   Format: [{
                       "page_url": "https://...",
                       "image_src": "/images/logo.png",
                       "image_filename": "logo.png",
                       "suggested_alt": "Firmenlogo...",
                       "confidence": 0.95,
                       "page_title": "Startseite",
                       "surrounding_text": "Text um das Bild",
                       "element_html": "<img src=...>"
                   }]
        
        Returns:
            Anzahl gespeicherter Fixes
        """
        if not fixes:
            logger.warning(f"No alt-text fixes to save for site_id={site_id}")
            return 0
        
        saved_count = 0
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for fix in fixes:
                    try:
                        # Generiere Hash für eindeutiges Image-Matching
                        image_hash = hashlib.sha256(
                            f"{site_id}:{fix['image_src']}".encode()
                        ).hexdigest()
                        
                        # Insert or Update (UPSERT)
                        await conn.execute(
                            """
                            INSERT INTO accessibility_alt_text_fixes (
                                site_id,
                                scan_id,
                                user_id,
                                page_url,
                                image_src,
                                image_filename,
                                image_url_hash,
                                suggested_alt,
                                confidence,
                                page_title,
                                surrounding_text,
                                element_html,
                                status,
                                created_at,
                                updated_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
                            ON CONFLICT (site_id, image_src)
                            DO UPDATE SET
                                -- Der Vorschlag wird NUR ersetzt, solange
                                -- niemand ueber ihn entschieden hat.
                                --
                                -- Vorher galt das unbedingt. Ein Kunde gab
                                -- "Firmengebaeude der Spedition in Zwickau"
                                -- frei; der naechste Scan formulierte
                                -- "Ein LKW steht vor einer Halle", und weil
                                -- der Status unangetastet blieb, ging der neue
                                -- Text ALS FREIGEGEBEN auf die Website. Der
                                -- Kunde hatte ihn nie gesehen.
                                --
                                -- Damit war die zentrale Zusage des Produkts
                                -- ausgehebelt: kein Bild bekommt ungeprueft
                                -- eine Beschreibung. Nachgewiesen an einem
                                -- Durchstich, nicht vermutet.
                                --
                                -- Eine abweichende Neuformulierung geht nicht
                                -- verloren, sie wandert nach image_context.
                                -- Wenn sich das Bild hinter der Adresse
                                -- geaendert hat, ist das dort auffindbar —
                                -- aber es aendert nichts, ohne dass ein Mensch
                                -- es entscheidet.
                                suggested_alt = CASE
                                    WHEN accessibility_alt_text_fixes.status = 'pending'
                                    THEN EXCLUDED.suggested_alt
                                    ELSE accessibility_alt_text_fixes.suggested_alt
                                END,
                                confidence = CASE
                                    WHEN accessibility_alt_text_fixes.status = 'pending'
                                    THEN EXCLUDED.confidence
                                    ELSE accessibility_alt_text_fixes.confidence
                                END,
                                image_context = CASE
                                    WHEN accessibility_alt_text_fixes.status <> 'pending'
                                     AND EXCLUDED.suggested_alt IS DISTINCT FROM
                                         accessibility_alt_text_fixes.suggested_alt
                                    THEN COALESCE(accessibility_alt_text_fixes.image_context,
                                                  '{}'::jsonb)
                                         || jsonb_build_object(
                                                'abweichender_vorschlag',
                                                EXCLUDED.suggested_alt,
                                                'bemerkt_am', NOW()::text,
                                                'scan_id', EXCLUDED.scan_id)
                                    ELSE accessibility_alt_text_fixes.image_context
                                END,
                                scan_id = EXCLUDED.scan_id,
                                page_title = EXCLUDED.page_title,
                                surrounding_text = EXCLUDED.surrounding_text,
                                element_html = EXCLUDED.element_html,
                                updated_at = NOW()
                            """,
                            site_id,
                            scan_id,
                            _als_user_id(user_id),
                            fix.get('page_url', ''),
                            fix['image_src'],
                            fix.get('image_filename', ''),
                            image_hash,
                            fix['suggested_alt'],
                            fix.get('confidence', 0.0),
                            fix.get('page_title', ''),
                            fix.get('surrounding_text', ''),
                            fix.get('element_html', ''),
                            status  # Standard: 'pending' → erst nach Review live
                        )
                        
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving alt-text fix for {fix.get('image_src')}: {e}")
                        # Continue mit nächstem Fix
                        continue
        
        if fixes and saved_count == 0:
            # Totalausfall ist immer ein Defekt (Schema, Typen, Rechte) — nie
            # ein Einzelfall. Genau das blieb hier einen Monat unbemerkt.
            logger.error(
                f"❌ KEIN einziger Alt-Text-Fix gespeichert ({len(fixes)} versucht, "
                f"site_id={site_id}) — Speicherpfad defekt, siehe Fehler oben"
            )
        else:
            logger.info(f"✅ Saved {saved_count}/{len(fixes)} alt-text fixes for site_id={site_id}")
        return saved_count
    
    async def get_fixes_for_site(
        self,
        site_id: str,
        status: Optional[str] = 'approved'
    ) -> List[Dict[str, Any]]:
        """
        Lädt Alt-Text-Fixes für eine Site (für Widget)
        
        Args:
            site_id: Site-Identifier
            status: Filter nach Status (approved, pending, etc.)
        
        Returns:
            Liste von Alt-Text-Fixes
        """
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    image_src,
                    image_filename,
                    suggested_alt,
                    page_url,
                    confidence,
                    page_title,
                    status,
                    created_at
                FROM accessibility_alt_text_fixes
                WHERE site_id = $1
            """
            
            params = [site_id]
            
            if status:
                query += " AND status = $2"
                params.append(status)
            
            query += " ORDER BY confidence DESC, created_at DESC"
            
            rows = await conn.fetch(query, *params)
            
            fixes = [
                {
                    "image_src": row['image_src'],
                    "image_filename": row['image_filename'],
                    "suggested_alt": row['suggested_alt'],
                    "page_url": row['page_url'],
                    "confidence": float(row['confidence']) if row['confidence'] else 0.0,
                    "page_title": row['page_title'],
                    "status": row['status']
                }
                for row in rows
            ]
            
            logger.info(f"📦 Loaded {len(fixes)} alt-text fixes for site_id={site_id}")
            return fixes
    
    async def set_status(
        self,
        fix_id: int,
        status: str,
        custom_alt: Optional[str] = None,
        erlaubte_sites: Optional[set] = None
    ) -> bool:
        """
        Setzt den Status eines Fixes (approve/reject/deploy).

        `erlaubte_sites` sind die site_ids, die der Aufrufer bereits autorisiert
        hat. Frueher stand hier ein user_id-Vergleich gegen den Erzeuger der
        Zeile — siehe _pruefe_site_zugehoerigkeit().
        status ∈ ('pending','approved','rejected','deployed').
        Gibt True zurück, wenn eine Zeile aktualisiert wurde.
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, user_id, site_id FROM accessibility_alt_text_fixes WHERE id = $1",
                fix_id
            )
            if not row:
                return False
            _pruefe_site_zugehoerigkeit(row, erlaubte_sites)

            approved_at = "NOW()" if status == 'approved' else "approved_at"
            if custom_alt is not None:
                await conn.execute(
                    f"""
                    UPDATE accessibility_alt_text_fixes
                    SET status = $1, suggested_alt = $2, approved_at = {approved_at}, updated_at = NOW()
                    WHERE id = $3
                    """,
                    status, custom_alt, fix_id
                )
            else:
                await conn.execute(
                    f"""
                    UPDATE accessibility_alt_text_fixes
                    SET status = $1, approved_at = {approved_at}, updated_at = NOW()
                    WHERE id = $2
                    """,
                    status, fix_id
                )
            return True

    async def get_review_queue(
        self,
        site_id: str,
        status: str = 'pending'
    ) -> List[Dict[str, Any]]:
        """Alt-Text-Fixes für die Review-Ansicht (Dashboard)."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, page_url, image_src, image_filename, suggested_alt,
                       confidence, surrounding_text, status, created_at
                FROM accessibility_alt_text_fixes
                WHERE site_id = $1 AND status = $2
                ORDER BY confidence DESC, created_at DESC
                """,
                site_id, status
            )
            return [
                {
                    "id": r['id'],
                    "page_url": r['page_url'],
                    "image_src": r['image_src'],
                    "image_filename": r['image_filename'],
                    "suggested_alt": r['suggested_alt'],
                    "confidence": float(r['confidence']) if r['confidence'] else 0.0,
                    "surrounding_text": r['surrounding_text'],
                    "status": r['status'],
                }
                for r in rows
            ]

    # =========================================================================
    # Dokumentweite Fixes (Fix-Manifest) — lang / skip-link / landmarks / css
    # =========================================================================

    async def save_document_fixes(
        self,
        site_id: str,
        scan_id: str,
        user_id: str,
        fixes: List[Dict[str, Any]],
        status: str = 'approved'
    ) -> int:
        """
        Speichert auto-sichere, dokumentweite Fixes (Stufe 1).

        Args:
            site_id: STABILE, domain-abgeleitete Site-ID (derive_site_id) – muss
                     identisch zu der sein, mit der die Channels das Manifest abfragen.
            fixes: Liste von Dicts mit:
                   {"fix_type": "html-lang", "payload": {"value": "de"},
                    "wcag_criterion": "3.1.1", "confidence": 1.0,
                    "page_url": "...", "source": "scan"}

        Returns:
            Anzahl gespeicherter/aktualisierter Fixes.
        """
        if not fixes:
            return 0

        import json as _json
        saved = 0
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for fix in fixes:
                    fix_type = fix.get('fix_type')
                    if not fix_type:
                        continue
                    try:
                        await conn.execute(
                            """
                            INSERT INTO accessibility_document_fixes (
                                site_id, scan_id, user_id, page_url,
                                fix_type, payload, wcag_criterion, confidence,
                                source, status, approved_at, created_at, updated_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::varchar,
                                      CASE WHEN $10::varchar = 'approved' THEN NOW() ELSE NULL END,
                                      NOW(), NOW())
                            ON CONFLICT (site_id, fix_type)
                            DO UPDATE SET
                                -- Eine erteilte Freigabe ueberlebt den
                                -- naechsten Scan.
                                --
                                -- Vorher stand hier `status = EXCLUDED.status`.
                                -- Kontrast-Fixes werden immer als 'pending'
                                -- gespeichert, also setzte JEDER Wiederholungs-
                                -- scan eine erteilte Farbfreigabe zurueck — die
                                -- Reparatur verschwand still von der Kunden-
                                -- website. Bei woechentlichem Scan haelt so
                                -- keine Freigabe eine Woche, und niemand
                                -- bekommt es mit: die Farben sehen wieder aus
                                -- wie vorher, das Dashboard zeigt "offen".
                                --
                                -- Der neue Vorschlag geht nicht verloren; er
                                -- liegt unter `neuer_vorschlag` im Payload und
                                -- wartet auf eine Entscheidung. Bis dahin
                                -- bleibt die alte, freigegebene Reparatur
                                -- aktiv — sie war einmal nachgemessen, und
                                -- veraltete Selektoren melden sich ohnehin
                                -- ueber die Wirkungsueberwachung.
                                status = CASE
                                    WHEN accessibility_document_fixes.status = 'approved'
                                    THEN 'approved'
                                    ELSE EXCLUDED.status
                                END,
                                payload = CASE
                                    WHEN accessibility_document_fixes.status = 'approved'
                                     AND EXCLUDED.status <> 'approved'
                                    THEN accessibility_document_fixes.payload
                                         || jsonb_build_object(
                                                'neuer_vorschlag', EXCLUDED.payload,
                                                'bemerkt_am', NOW()::text)
                                    ELSE EXCLUDED.payload
                                END,
                                wcag_criterion = EXCLUDED.wcag_criterion,
                                confidence = EXCLUDED.confidence,
                                scan_id = EXCLUDED.scan_id,
                                page_url = EXCLUDED.page_url,
                                source = EXCLUDED.source,
                                approved_at = CASE
                                    WHEN accessibility_document_fixes.status = 'approved'
                                      OR EXCLUDED.status = 'approved'
                                    THEN COALESCE(accessibility_document_fixes.approved_at, NOW())
                                    ELSE NULL END,
                                updated_at = NOW()
                            """,
                            site_id,
                            scan_id,
                            _als_user_id(user_id),
                            fix.get('page_url', ''),
                            fix_type,
                            _json.dumps(fix.get('payload', {})),
                            fix.get('wcag_criterion'),
                            fix.get('confidence', 1.0),
                            fix.get('source', 'scan'),
                            # Ein Fix darf seinen Status selbst bestimmen. Der
                            # Parameter bleibt die Vorgabe fuer alle uebrigen.
                            # Grund: `kontrast-css` aendert das Aussehen der
                            # Kundenseite und darf nicht wie ein Skip-Link
                            # stillschweigend live gehen — der Betreiber sieht
                            # eine geaenderte Linkfarbe sofort.
                            fix.get('status') or status,
                        )
                        saved += 1
                    except Exception as e:
                        logger.error(f"Error saving document fix {fix_type} for {site_id}: {e}")
                        continue

        logger.info(f"✅ Saved {saved}/{len(fixes)} document fixes for site_id={site_id}")
        return saved

    async def get_document_fixes_for_site(
        self,
        site_id: str,
        status: Optional[str] = 'approved'
    ) -> List[Dict[str, Any]]:
        """Lädt dokumentweite Fixes für das Manifest."""
        import json as _json
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT fix_type, payload, wcag_criterion, confidence, source, status, page_url
                FROM accessibility_document_fixes
                WHERE site_id = $1
            """
            params = [site_id]
            if status:
                query += " AND status = $2"
                params.append(status)
            query += " ORDER BY fix_type"
            rows = await conn.fetch(query, *params)

            result = []
            for r in rows:
                payload = r['payload']
                if isinstance(payload, str):
                    try:
                        payload = _json.loads(payload)
                    except Exception:
                        payload = {}
                result.append({
                    "fix_type": r['fix_type'],
                    "payload": payload or {},
                    "wcag_criterion": r['wcag_criterion'],
                    "confidence": float(r['confidence']) if r['confidence'] is not None else 1.0,
                    "source": r['source'],
                    "status": r['status'],
                    "page_url": r['page_url'],
                })
            logger.info(f"📦 Loaded {len(result)} document fixes for site_id={site_id}")
            return result

    # =========================================================================
    # Link-Zweck-Fixes (WCAG 2.4.4) — aria-label-Vorschläge, HITL
    # =========================================================================

    @staticmethod
    def link_key(href: str, text: str) -> str:
        """Stabiler Matching-Key für einen Link: SHA256(href|normalisierter_text)."""
        norm_text = ' '.join((text or '').split()).strip().lower()
        return hashlib.sha256(f"{(href or '').strip()}|{norm_text}".encode()).hexdigest()

    async def save_link_fixes(
        self,
        site_id: str,
        scan_id: str,
        user_id: str,
        fixes: List[Dict[str, Any]],
        status: str = 'pending'  # Stufe 2: erst nach Review live
    ) -> int:
        """
        Speichert aria-label-Vorschläge für nichtssagende Links.

        fixes: [{
            "page_url", "link_href", "link_text", "suggested_label",
            "confidence", "surrounding_text", "source"
        }]
        """
        if not fixes:
            return 0
        saved = 0
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for fix in fixes:
                    href = fix.get('link_href', '')
                    text = fix.get('link_text', '')
                    label = (fix.get('suggested_label') or '').strip()
                    if not label or (not href and not text):
                        continue
                    try:
                        await conn.execute(
                            """
                            INSERT INTO accessibility_link_fixes (
                                site_id, scan_id, user_id, page_url,
                                link_href, link_text, link_key,
                                suggested_label, confidence, surrounding_text,
                                source, status, created_at, updated_at
                            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,NOW(),NOW())
                            ON CONFLICT (site_id, link_key)
                            DO UPDATE SET
                                -- Wie bei den Bildbeschreibungen: eine bereits
                                -- entschiedene Beschriftung wird nicht durch
                                -- eine neue ersetzt. Sonst traegt die Freigabe
                                -- des Kunden einen Text, den er nie gesehen
                                -- hat — und der Link sagt Besuchern etwas
                                -- anderes, als jemand geprueft hat.
                                suggested_label = CASE
                                    WHEN accessibility_link_fixes.status = 'pending'
                                    THEN EXCLUDED.suggested_label
                                    ELSE accessibility_link_fixes.suggested_label
                                END,
                                confidence = CASE
                                    WHEN accessibility_link_fixes.status = 'pending'
                                    THEN EXCLUDED.confidence
                                    ELSE accessibility_link_fixes.confidence
                                END,
                                surrounding_text = EXCLUDED.surrounding_text,
                                scan_id = EXCLUDED.scan_id,
                                page_url = EXCLUDED.page_url,
                                updated_at = NOW()
                            """,
                            site_id, scan_id, _als_user_id(user_id), fix.get('page_url', ''),
                            href, text, self.link_key(href, text),
                            label, fix.get('confidence', 0.0),
                            fix.get('surrounding_text', ''),
                            fix.get('source', 'scan'), status,
                        )
                        saved += 1
                    except Exception as e:
                        logger.error(f"Error saving link fix ({text!r}) for {site_id}: {e}")
                        continue
        logger.info(f"✅ Saved {saved}/{len(fixes)} link fixes for site_id={site_id}")
        return saved

    async def get_link_fixes_for_site(
        self,
        site_id: str,
        status: Optional[str] = 'approved'
    ) -> List[Dict[str, Any]]:
        """Lädt Link-Fixes (für Manifest oder Review-Queue)."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT id, page_url, link_href, link_text, link_key,
                       suggested_label, confidence, surrounding_text, status
                FROM accessibility_link_fixes
                WHERE site_id = $1
            """
            params = [site_id]
            if status:
                query += " AND status = $2"
                params.append(status)
            query += " ORDER BY confidence DESC, created_at DESC"
            rows = await conn.fetch(query, *params)
            return [
                {
                    "id": r['id'],
                    "page_url": r['page_url'],
                    "link_href": r['link_href'],
                    "link_text": r['link_text'],
                    "link_key": r['link_key'],
                    "suggested_label": r['suggested_label'],
                    "confidence": float(r['confidence']) if r['confidence'] else 0.0,
                    "surrounding_text": r['surrounding_text'],
                    "status": r['status'],
                }
                for r in rows
            ]

    async def set_link_status(
        self,
        fix_id: int,
        status: str,
        custom_label: Optional[str] = None,
        erlaubte_sites: Optional[set] = None
    ) -> bool:
        """Approve/Reject eines Link-Fixes; autorisiert ueber die Website."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, user_id, site_id FROM accessibility_link_fixes WHERE id = $1", fix_id
            )
            if not row:
                return False
            _pruefe_site_zugehoerigkeit(row, erlaubte_sites)
            approved_at = "NOW()" if status == 'approved' else "approved_at"
            if custom_label is not None:
                await conn.execute(
                    f"""UPDATE accessibility_link_fixes
                        SET status=$1, suggested_label=$2, approved_at={approved_at}, updated_at=NOW()
                        WHERE id=$3""",
                    status, custom_label, fix_id
                )
            else:
                await conn.execute(
                    f"""UPDATE accessibility_link_fixes
                        SET status=$1, approved_at={approved_at}, updated_at=NOW()
                        WHERE id=$2""",
                    status, fix_id
                )
            return True

    async def set_kontrast_freigabe(
        self,
        site_id: str,
        index: int,
        status: str,
        eigene_farbe: Optional[str] = None,
        erlaubte_sites: Optional[set] = None,
    ) -> Dict[str, Any]:
        """
        Gibt EINE Farbentscheidung frei oder lehnt sie ab.

        Warum je Entscheidung und nicht je Zeile: die Tabelle haelt genau eine
        Zeile je (site_id, fix_type), aber darin stecken mehrere Farbpaare. Ein
        Betreiber will seine Linkfarbe vielleicht aendern und die Schriftfarbe
        im Footer nicht — alles-oder-nichts waere hier die falsche Frage.

        Ausgeliefert wird immer nur, was freigegeben ist: `payload["rules"]`
        wird bei jeder Freigabe aus den zugestimmten Entscheidungen neu
        gebaut, und die Zeile bleibt 'pending', solange keine einzige zugestimmt
        ist. Das Manifest liefert nur 'approved' aus — solange also niemand
        klickt, aendert sich auf der Kundenseite nichts.

        `eigene_farbe` erlaubt einen abweichenden Ton. Er wird NICHT blind
        uebernommen: erreicht er die geforderte Ratio nicht, wird die Freigabe
        abgelehnt. Eine Zusage "erfuellt WCAG" darf nicht daran scheitern, dass
        jemand eine huebschere Farbe eingetippt hat.

        Returns:
            {"ok": bool, "fehler": str|None, "entscheidung": dict|None,
             "freigegeben": int}
        """
        from compliance_engine.kontrast_fixes import (
            als_css_regeln, kontrast as _kontrast, _hex_zu_rgb,
        )
        import json as _json

        if status not in ("approved", "rejected", "pending"):
            return {"ok": False, "fehler": f"Unbekannter Status: {status}"}

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT id, user_id, site_id, payload
                   FROM accessibility_document_fixes
                   WHERE site_id = $1 AND fix_type = 'kontrast-css'""",
                site_id,
            )
            if not row:
                return {"ok": False, "fehler": "Keine Kontrast-Entscheidungen für diese Site."}
            _pruefe_site_zugehoerigkeit(row, erlaubte_sites)

            payload = row["payload"]
            if isinstance(payload, str):
                payload = _json.loads(payload)
            entscheidungen = payload.get("entscheidungen") or []
            if not 0 <= index < len(entscheidungen):
                return {"ok": False, "fehler": "Diese Entscheidung gibt es nicht."}

            eintrag = entscheidungen[index]

            if eigene_farbe and status == "approved":
                vg = _hex_zu_rgb(eigene_farbe)
                hg = _hex_zu_rgb(eintrag.get("hintergrund", ""))
                if not vg or not hg:
                    return {"ok": False, "fehler": "Farbe nicht lesbar (erwartet z. B. #3a5f8a)."}
                erreicht = round(_kontrast(vg, hg), 2)
                ziel = float(eintrag.get("ziel_ratio") or 4.5)
                if erreicht < ziel:
                    return {
                        "ok": False,
                        "fehler": (
                            f"{eigene_farbe} erreicht auf {eintrag.get('hintergrund')} nur "
                            f"{erreicht}:1 — gefordert sind {ziel}:1. Nicht übernommen."
                        ),
                    }
                eintrag["vorschlag"] = eigene_farbe
                eintrag["neue_ratio"] = erreicht
                eintrag["quelle_farbe"] = "vom Betreiber gewählt"

            eintrag["freigabe"] = status

            # Nur Zugestimmtes wird ausgeliefert.
            freigegeben = [e for e in entscheidungen if e.get("freigabe") == "approved"]
            payload["entscheidungen"] = entscheidungen
            payload["rules"] = als_css_regeln(
                [dict(e, bestaetigt=True) for e in freigegeben]
            )

            zeilen_status = "approved" if freigegeben else "pending"
            await conn.execute(
                # $2 wird zweimal gebraucht — einmal als Spaltenwert (varchar),
                # einmal im Vergleich (text). Ohne die Angabe kann Postgres den
                # Typ nicht eindeutig herleiten und lehnt die Anweisung ab.
                """UPDATE accessibility_document_fixes
                   SET payload = $1, status = $2::varchar,
                       approved_at = CASE WHEN $2::varchar = 'approved'
                                          THEN NOW() ELSE NULL END,
                       updated_at = NOW()
                   WHERE id = $3""",
                _json.dumps(payload), zeilen_status, row["id"],
            )

        logger.info(
            f"Kontrast-Freigabe site={site_id} #{index} -> {status}; "
            f"{len(freigegeben)} von {len(entscheidungen)} live"
        )
        return {"ok": True, "fehler": None, "entscheidung": eintrag,
                "freigegeben": len(freigegeben)}

    async def get_kontrast_entscheidungen(self, site_id: str) -> List[Dict[str, Any]]:
        """Alle Farbentscheidungen einer Site — unabhaengig vom Freigabestand.

        Bewusst ohne Status-Filter: die Worklist muss auch das Offene zeigen,
        sonst gaebe es nichts zu entscheiden.
        """
        import json as _json
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT payload FROM accessibility_document_fixes
                   WHERE site_id = $1 AND fix_type = 'kontrast-css'""",
                site_id,
            )
        if not row:
            return []
        payload = row["payload"]
        if isinstance(payload, str):
            payload = _json.loads(payload)
        entscheidungen = payload.get("entscheidungen") or []
        for i, e in enumerate(entscheidungen):
            e.setdefault("freigabe", "pending")
            e["index"] = i
        return entscheidungen

    async def get_stats_for_site(
        self,
        site_id: str
    ) -> Dict[str, Any]:
        """
        Statistiken für Dashboard
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_fixes,
                    COUNT(*) FILTER (WHERE status = 'approved') as approved_fixes,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending_fixes,
                    AVG(confidence) as avg_confidence,
                    COUNT(DISTINCT page_url) as pages_with_fixes
                FROM accessibility_alt_text_fixes
                WHERE site_id = $1
                """,
                site_id
            )
            
            if not row:
                return {
                    "total_fixes": 0,
                    "approved_fixes": 0,
                    "pending_fixes": 0,
                    "avg_confidence": 0.0,
                    "pages_with_fixes": 0
                }
            
            return {
                "total_fixes": row['total_fixes'],
                "approved_fixes": row['approved_fixes'],
                "pending_fixes": row['pending_fixes'],
                "avg_confidence": float(row['avg_confidence']) if row['avg_confidence'] else 0.0,
                "pages_with_fixes": row['pages_with_fixes']
            }

