/**
 * Gesetzesbezug je Prüfbereich des Scanners.
 *
 * Grundsatz (seit 10.11.2026): Die Ergebnisseite nennt zu jedem Bereich mit
 * Befunden, welche Norm die Pflicht trägt, wer sie durchsetzen kann und was
 * das Gesetz als Rahmen vorsieht. Sie nennt NICHT, was diese Website im
 * Einzelfall kostet. Der Unterschied ist die Grenze zu § 5 UWG, an der die
 * Vorschau schon zweimal stand (Summe 91.800 EUR bis 03.09.2026, Spanne
 * "typische Abmahnkosten" bis 07.10.2026):
 *
 *   - Eine Norm zu zitieren ist eine Tatsachenaussage über das Gesetz.
 *   - Einen Betrag an den Scan zu hängen ist eine Prognose über Rechtsfolgen,
 *     die der Scan nicht belegen kann.
 *
 * Darum steht der gesetzliche Rahmen hier als Zitat mit Fundstelle und wird in
 * der Anzeige ausdrücklich als Rahmen, nicht als Prognose, beschriftet.
 *
 * Die Schlüssel sind die Bereichskennungen aus dem Backend
 * (public_routes._aggregate_risk_categories), nicht die internen Pillar-Keys
 * der Landing. Fundstellen wurden beim Schreiben aus dem Gedächtnis gesetzt
 * und sind vor einem Release von einem Anwalt gegenzulesen; wo eine Zahl
 * zweifelhaft ist, gehört sie raus, nicht geraten.
 */
export interface Gesetzesbezug {
  /** Bereichskennung des Backends. */
  id: string;
  /** Die Norm, die die Pflicht trägt. */
  norm: string;
  /** Was die Pflicht verlangt, in einem Satz. */
  pflicht: string;
  /** Wer sie durchsetzen kann. */
  durchsetzung: string;
  /** Rahmen laut Gesetz, mit Fundstelle. Kein Bezug auf diese Website. */
  rahmen: string;
  /** Was in der Praxis typischerweise zuerst kommt. Ehrlich, auch wenn es entlastet. */
  praxis: string;
  /** Gerichtsentscheidung oder Fundstelle, die den Punkt trägt. Optional. */
  entscheidung?: string;
}

export const GESETZESBEZUG: Record<string, Gesetzesbezug> = {
  barrierefreiheit: {
    id: 'barrierefreiheit',
    norm: 'Barrierefreiheitsstärkungsgesetz (BFSG), § 3 Abs. 1 mit § 2 Nr. 26',
    pflicht:
      'Dienstleistungen im elektronischen Geschäftsverkehr für Verbraucher müssen seit dem 28. Juni 2025 barrierefrei sein. Der technische Maßstab ist die EN 301 549, die auf WCAG 2.1 AA verweist.',
    durchsetzung:
      'Marktüberwachungsbehörden der Länder. Verbraucher und qualifizierte Verbände können ein Verfahren anstoßen.',
    rahmen: 'Geldbuße bis 100.000 Euro, § 37 BFSG.',
    praxis:
      'Kleinstunternehmen mit unter zehn Beschäftigten und höchstens zwei Millionen Euro Jahresumsatz sind bei Dienstleistungen ausgenommen (§ 3 Abs. 3 BFSG). Ob Ihr Angebot unter das Gesetz fällt, ist eine Rechtsfrage. Der Scan misst nur, ob die Seite den Maßstab erfüllt.',
  },
  cookies: {
    id: 'cookies',
    norm: '§ 25 Abs. 1 TDDDG, Art. 6 und 7 DSGVO',
    pflicht:
      'Vor dem Speichern oder Auslesen von Informationen auf dem Endgerät braucht es eine aktive, informierte Einwilligung. Vorangekreuzte Kästchen und Weitersurfen genügen nicht.',
    durchsetzung:
      'Datenschutzaufsichtsbehörden. Seit dem EuGH-Urteil Lindenapotheke auch Mitbewerber über das UWG.',
    rahmen:
      'Geldbuße bis 300.000 Euro nach § 28 TDDDG; für die Verarbeitung dahinter der Rahmen des Art. 83 Abs. 5 DSGVO.',
    praxis:
      'Der häufigste Anlass ist nicht die Behörde, sondern ein Dienst, der vor dem Klick auf „Akzeptieren“ bereits lädt. Genau das ist technisch messbar, und genau das zählt der Scan.',
    entscheidung:
      'EuGH, Urteil vom 01.10.2019, C-673/17 (Planet49); BGH, Urteil vom 28.05.2020, I ZR 7/16 (Cookie-Einwilligung II); EuGH, Urteil vom 04.10.2024, C-21/23 (Lindenapotheke).',
  },
  dsgvo: {
    id: 'dsgvo',
    norm: 'Art. 5, 6, 13 und 44 ff. DSGVO',
    pflicht:
      'Jeder eingebundene Drittdienst (Schriften, Karten, Videos, Analyse) ist eine Datenübermittlung, die eine Rechtsgrundlage braucht und in der Datenschutzerklärung stehen muss.',
    durchsetzung:
      'Aufsichtsbehörden (Art. 58 DSGVO), Betroffene mit Schadensersatz (Art. 82 DSGVO), Mitbewerber über das UWG.',
    rahmen:
      'Geldbuße bis 10 Millionen Euro oder 2 Prozent des Jahresumsatzes (Art. 83 Abs. 4 DSGVO), bei Verstößen gegen die Grundsätze bis 20 Millionen Euro oder 4 Prozent (Art. 83 Abs. 5 DSGVO).',
    praxis:
      'Gegen Unternehmen mit weniger als 250 Beschäftigten können Mitbewerber die Kosten einer DSGVO-Abmahnung nicht ersetzt verlangen (§ 13 Abs. 4 Nr. 2 UWG). Der Unterlassungsanspruch bleibt; eine Vertragsstrafe darf bei einer ersten Abmahnung von Unternehmen unter 100 Beschäftigten nicht verlangt werden (§ 13a Abs. 2 UWG). Die Google-Fonts-Welle 2022 lief über Betroffene, nicht über Mitbewerber.',
    entscheidung:
      'LG München I, Urteil vom 20.01.2022, 3 O 17493/20 (Google Fonts, 100 Euro Schadensersatz je Aufruf ohne Einwilligung).',
  },
  rechtstexte: {
    id: 'rechtstexte',
    norm: '§ 5 DDG (Impressum), Art. 13 DSGVO (Datenschutzerklärung), § 312d BGB mit Art. 246a EGBGB (Widerruf), § 36 VSBG',
    pflicht:
      'Anbieterkennzeichnung, Datenschutzerklärung und, bei Verbraucherverträgen, Widerrufsbelehrung müssen vollständig, leicht erkennbar und unmittelbar erreichbar sein.',
    durchsetzung: 'Mitbewerber und Verbände nach § 8 Abs. 3 UWG, Behörden nach DDG.',
    rahmen: 'Geldbuße bis 50.000 Euro nach § 19 DDG.',
    praxis:
      'Für Mitbewerber sind seit 2020 die Abmahnkosten bei reinen Informationspflichten nicht mehr erstattungsfähig (§ 13 Abs. 4 Nr. 1 UWG). Für Verbände gilt diese Grenze nicht. Die Unterlassungserklärung bleibt in jedem Fall; die Vertragsstrafe darin ist bei einer ersten Mitbewerber-Abmahnung von Unternehmen unter 100 Beschäftigten ausgeschlossen (§ 13a Abs. 2 UWG).',
  },
  shop: {
    id: 'shop',
    norm: '§ 312j BGB (Bestellknopf), § 312d BGB, Art. 246a EGBGB',
    pflicht:
      'Der Bestellknopf muss eindeutig auf die Zahlungspflicht hinweisen, Widerrufsbelehrung und Muster-Widerrufsformular müssen vor der Bestellung erreichbar sein.',
    durchsetzung: 'Mitbewerber und Verbände nach § 8 Abs. 3 UWG.',
    rahmen:
      'Ein Vertrag ohne korrekte Beschriftung des Bestellknopfs kommt nicht zustande (§ 312j Abs. 4 BGB). Fehlende Widerrufsbelehrung verlängert die Frist auf zwölf Monate und 14 Tage (§ 356 Abs. 3 BGB).',
    praxis:
      'Shops stehen im Fokus der Verbände, weil jeder Fehler reproduzierbar ist. Die Folgen sind hier zivilrechtlich: Rückabwicklung, nicht Bußgeld.',
  },
  preise: {
    id: 'preise',
    norm: 'Preisangabenverordnung (PAngV), §§ 3, 4 und 11',
    pflicht:
      'Gesamtpreis mit Umsatzsteuer, Grundpreis bei Mengenware, und bei Streichpreisen der niedrigste Preis der letzten 30 Tage.',
    durchsetzung: 'Mitbewerber und Verbände nach § 8 Abs. 3 UWG, Ordnungsbehörden.',
    rahmen: 'Geldbuße bis 25.000 Euro (§ 20 PAngV mit § 3 WiStG).',
    praxis:
      'Die 30-Tage-Regel bei Rabatten ist seit Mai 2022 der häufigste neue Abmahngrund im Handel.',
  },
  wettbewerb: {
    id: 'wettbewerb',
    norm: 'UWG, §§ 5 und 5a',
    pflicht:
      'Werbeaussagen müssen wahr und belegbar sein; wesentliche Informationen dürfen nicht fehlen.',
    durchsetzung: 'Mitbewerber und Verbände nach § 8 Abs. 3 UWG.',
    rahmen:
      'Unterlassung, Beseitigung und Schadensersatz (§§ 8, 9 UWG); bei Wiederholung Vertragsstrafe aus der Unterlassungserklärung.',
    praxis:
      'Das trifft auch uns: Alles, was auf dieser Seite über Rechtsfolgen steht, ist deshalb mit Fundstelle versehen.',
  },
  sicherheit: {
    id: 'sicherheit',
    norm: 'Art. 32 DSGVO (Sicherheit der Verarbeitung)',
    pflicht:
      'Personenbezogene Daten müssen dem Risiko angemessen geschützt werden; eine Verbindung ohne Verschlüsselung bei Formularen ist das Gegenteil davon.',
    durchsetzung: 'Aufsichtsbehörden (Art. 58 DSGVO).',
    rahmen: 'Geldbuße bis 10 Millionen Euro oder 2 Prozent des Jahresumsatzes (Art. 83 Abs. 4 DSGVO).',
    praxis:
      'Fehlendes HTTPS und fehlende Sicherheitsheader sind Punkte, die jede Aufsichtsbehörde zuerst prüft, weil sie von außen sichtbar sind.',
  },
};

/** Die Backend-Kennung zu einem internen Pillar-Key der Landing. */
export const PILLAR_ZU_BEREICH: Record<string, string> = {
  accessibility: 'barrierefreiheit',
  gdpr: 'dsgvo',
  cookies: 'cookies',
  legal: 'rechtstexte',
  security: 'sicherheit',
  competition: 'wettbewerb',
  shop: 'shop',
  prices: 'preise',
};
