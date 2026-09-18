"""Der Wiederholungsscan loeschte den Vermerk 'automatik'.

Migration 0024b hat am 07.09.2026 achtzehn Zeilen als 'automatik' vermerkt:
freigegeben, ohne dass je jemand gefragt wurde. Der Vermerk sollte den
Unterschied festhalten, auf dem die ganze Produktzusage steht — "freigeben
muss ein Mensch, nicht die Maschine".

Am 17.09.2026 standen davon nur noch acht auf 'automatik'. Fuenf trugen zu
Recht 'mensch' (jemand hat inzwischen entschieden). **Fuenf aber standen
wieder auf NULL**, obwohl niemand sie beurteilt hatte:

    38, 39      panoart360-de  (skip-link, landmark-main)          15.09.
    21, 22, 24  zua-zwickau-de (skip-link, landmark-main, struktur) 17.09.

Die Ursache stand im ON CONFLICT von `accessibility_fix_saver.py`. Geschuetzt
war dort nur 'mensch', sonst galt `EXCLUDED.entscheidung_quelle` — und das ist
NULL, sobald der Scan 'pending' liefert, was er seit dem 05.09. immer tut.
Jeder Wiederholungsscan loeschte damit den Vermerk.

Der Schaden ist leise: der Status blieb 'approved', die Reparatur blieb live,
die Zeile blieb in der Worklist zur Bestaetigung. Verloren ging nur die
Antwort auf die Frage, WARUM sie live ist. Im Lernstand wanderten die fuenf
von `automatisch_uebernommen` nach `herkunft_unbekannt` — aus "die Maschine
hat sich selbst freigegeben" wurde "wir wissen es nicht mehr". Das ist keine
Luecke, die entsteht, sondern eine, die gemacht wird.

Der Code ist im selben Commit repariert (COALESCE statt CASE auf 'mensch').
Diese Revision holt nach, was bereits geloescht wurde.

**Nichts wird erfunden.** Nachgetragen wird nur, was sich aus denselben Daten
herleitet, aus denen 0024b es hergeleitet hat:

  - `status = 'approved'` und `fix_type <> 'kontrast-css'` — wie in 0024b.
  - `entscheidung_quelle IS NULL` — wer 'mensch' traegt, hat entschieden.
  - `created_at < FREIGABEWEG_SEIT` — die Freigaberoute gab es noch nicht.
    0024b sah auf `COALESCE(updated_at, created_at)`; genau dieses Feld hat
    der Wiederholungsscan verstellt, deshalb hier `created_at`.
  - `approved_at = created_at` — die Signatur der Auto-Freigabe. Die
    Freigaberoute setzt `approved_at = NOW()`, also spaeter als die Anlage.
    Eine von Hand erteilte Freigabe faellt hier heraus.

Gegen die Produktion gerechnet trifft das genau die fuenf oben genannten
Zeilen und keine weitere.

Revision ID: 0033_herkunft_ueberlebt_scan
Revises: 0032_kontosicherheit
Create Date: 2026-09-17
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0033_herkunft_ueberlebt_scan"
down_revision: Union[str, None] = "0032_kontosicherheit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Dasselbe Datum wie in 0024b: Deploy von 0dd3425. Vorher gab es
# POST /api/accessibility/approve-dokument nicht, eine Freigabe konnte also
# gar nicht von einem Menschen stammen.
FREIGABEWEG_SEIT = "2026-09-05 03:55:00"


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE accessibility_document_fixes
           SET entscheidung_quelle = 'automatik'
         WHERE status = 'approved'
           AND fix_type <> 'kontrast-css'
           AND entscheidung_quelle IS NULL
           AND created_at < TIMESTAMP '{FREIGABEWEG_SEIT}'
           AND approved_at = created_at
        """
    )


def downgrade() -> None:
    """Bewusst leer.

    Ein Zurueck hiesse, den Vermerk erneut zu loeschen — also genau den
    Fehler noch einmal zu machen, den diese Revision behebt. Die Spalte
    selbst legt 0024b an, die nimmt ihr Downgrade zurueck.
    """
