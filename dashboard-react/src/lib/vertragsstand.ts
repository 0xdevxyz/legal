/**
 * Fassungen der Vertragstexte. Eine Quelle im Dashboard.
 *
 * Bis zum 11.09.2026 standen die Fassungen in register/page.tsx. Seitdem
 * braucht sie auch das Gate fuer Bestandskonten (components/auth/VertragsGate),
 * das die 16 Konten von vor dem 10.09.2026 um die AVV-Zustimmung bittet.
 * Zwei Kopien laufen auseinander, und eine protokollierte Annahme fuer eine
 * Fassung, die nie angezeigt wurde, ist kein Nachweis.
 *
 * Das Backend fuehrt dieselben Werte in backend/vertragsstand.py; der Test
 * backend/tests/test_vertragsstand.py vergleicht beide. Die Landing hat ihre
 * eigene Kopie in landing-react/src/lib/vertragsstand.ts (eigenes Paket).
 */
export const AGB_VERSION = '2026-09-01';
export const AVV_VERSION = '2026-09-10';
