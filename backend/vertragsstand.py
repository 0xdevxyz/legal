"""
Die aktuellen Fassungen der Vertragstexte. Eine Quelle im Backend.

Die Registrierung protokolliert seit dem 10.09.2026, welche AGB- und
AVV-Fassung ein Kunde angenommen hat (vertragsannahmen). Bis dahin stand die
Fassung nur im Dashboard (register/page.tsx) und in der Landing
(lib/vertragsstand.ts). Das Backend konnte deshalb nicht sagen, ob eine
protokollierte Annahme noch die aktuelle Fassung betrifft, und genau das
braucht das Gate fuer die Bestandskonten: 16 Konten haben den AVV nie
angenommen, ohne ihn darf complyo fuer sie keine Besucherdaten verarbeiten.

Wer eine Fassung aendert, aendert sie hier UND in
dashboard-react/src/lib/vertragsstand.ts UND in
landing-react/src/lib/vertragsstand.ts. Der Waechter in
tests/test_vertragsstand.py vergleicht die drei.
"""

AGB_VERSION = "2026-09-01"
AVV_VERSION = "2026-09-10"
