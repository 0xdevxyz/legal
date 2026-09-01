/**
 * Anbieterdaten nach § 5 DDG. Eine Quelle für alle Rechtsseiten.
 *
 * Bis zum 01.09.2026 trugen /impressum, /agb und /datenschutz drei getrennte
 * Sätze erfundener Angaben: "Complyo GmbH", "Musterstraße 123, 10115 Berlin",
 * "Max Mustermann", eine erfundene Handelsregisternummer, eine erfundene
 * USt-IdNr. und die Telefonnummer "+49 (0) 30 1234567". Das Impressum wurde
 * zuerst entgiftet, AGB und Datenschutzerklärung behielten die Platzhalter.
 * Drei Quellen, von denen eine gepflegt wurde, sind der Grund dafür.
 *
 * Deshalb steht alles hier. Wer die Anbieterdaten ändert, ändert sie damit für
 * alle drei Seiten gleichzeitig.
 *
 * complyo wird als Einzelunternehmen betrieben. Vor- und Nachname der
 * natürlichen Person sind Pflichtangabe (§ 5 Abs. 1 Nr. 1 DDG), die
 * Geschäftsbezeichnung "Complyo" allein genügt nicht. Eine Firmierung als
 * "GmbH" ohne existierende GmbH löst Rechtsscheinhaftung aus: der Handelnde
 * haftet dann persönlich, also genau umgekehrt zur Absicht einer
 * Haftungsbeschränkung.
 *
 * NICHT VERÖFFENTLICHEN, solange Pflichtfelder leer sind. Alle drei Seiten
 * weisen sichtbar darauf hin, statt still etwas Falsches zu behaupten.
 */

type Anbieterangaben = {
  /** Vor- und Nachname der natürlichen Person. Pflichtangabe. */
  name: string;
  geschaeftsbezeichnung: string;
  strasse: string;
  plz: string;
  ort: string;
  land: string;
  email: string;
  /** Postfach für Datenschutzanfragen. Muss erreichbar sein, Art. 12 Abs. 2 DSGVO. */
  datenschutzEmail: string;
  /** Zweiter Kommunikationsweg neben der E-Mail. Optional, aber üblich. */
  telefon: string;
  /** Pflichtangabe, sobald vorhanden (§ 5 Abs. 1 Nr. 6 DDG). */
  ustIdNr: string;
};

export const ANBIETER: Anbieterangaben = {
  name: '',
  geschaeftsbezeichnung: 'Complyo',
  strasse: 'Pappelallee 64',
  plz: '10437',
  ort: 'Berlin',
  land: 'Deutschland',
  email: 'info@complyo.de',
  datenschutzEmail: 'datenschutz@complyo.de',
  telefon: '',
  ustIdNr: 'DE405368946',
};

/** "10437 Berlin" */
export const ANBIETER_ANSCHRIFT = ANBIETER.plz + ' ' + ANBIETER.ort;

/** "Pappelallee 64, 10437 Berlin" — für Fließtext, etwa den Geltungsbereich der AGB. */
export const ANBIETER_ANSCHRIFT_EINZEILIG = ANBIETER.strasse + ', ' + ANBIETER_ANSCHRIFT;

/**
 * Die Vertragspartei, wie sie in den AGB steht. Ohne Namen bleibt nur die
 * Geschäftsbezeichnung; der Warnhinweis auf der Seite sagt dann, dass die
 * Angabe unvollständig ist.
 */
export const ANBIETER_VERTRAGSPARTEI = ANBIETER.name
  ? ANBIETER.name + ', handelnd unter der Geschäftsbezeichnung "' +
    ANBIETER.geschaeftsbezeichnung + '", ' + ANBIETER_ANSCHRIFT_EINZEILIG
  : ANBIETER.geschaeftsbezeichnung + ', ' + ANBIETER_ANSCHRIFT_EINZEILIG;

/** Was noch fehlt, im Klartext und mit Norm. Leer heißt vollständig. */
export const ANBIETER_FEHLENDE_PFLICHTFELDER: string[] = [
  ANBIETER.name ? null : 'Vor- und Nachname des Anbieters (§ 5 Abs. 1 Nr. 1 DDG)',
  ANBIETER.ustIdNr ? null : 'Umsatzsteuer-Identifikationsnummer (§ 5 Abs. 1 Nr. 6 DDG)',
].filter((feld): feld is string => feld !== null);

export const ANBIETER_UNVOLLSTAENDIG = ANBIETER_FEHLENDE_PFLICHTFELDER.length > 0;
