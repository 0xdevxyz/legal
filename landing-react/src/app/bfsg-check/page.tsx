import type { Metadata } from 'next';
import CheckPage from '@/components/landing/CheckPage';

export const metadata: Metadata = {
  title: 'BFSG-Check: Website auf Barrierefreiheitsstärkungsgesetz prüfen | Complyo',
  description:
    'BFSG-Check kostenlos: Prüfen Sie, ob Ihre Website die Anforderungen des Barrierefreiheitsstärkungsgesetzes erfüllt. Ergebnis in unter einer Minute, ohne Anmeldung.',
  keywords: 'BFSG-Check, BFSG Checker, BFSG Check, Barrierefreiheitsstärkungsgesetz Website',
  alternates: { canonical: '/bfsg-check/' },
  openGraph: {
    title: 'BFSG-Check: Website auf Barrierefreiheitsstärkungsgesetz prüfen',
    description:
      'Prüfen Sie kostenlos, ob Ihre Website die BFSG-Anforderungen erfüllt. Ergebnis in unter einer Minute.',
    url: 'https://complyo.de/bfsg-check',
    type: 'website',
  },
};

export default function Page() {
  return (
    <CheckPage
      h1="BFSG-Check für Ihre Website"
      lead="Das Barrierefreiheitsstärkungsgesetz (BFSG) gilt seit dem 28. Juni 2025. Mit dem BFSG-Checker prüfen Sie kostenlos, wo Ihre Website die technischen Anforderungen an Barrierefreiheit noch nicht erfüllt."
      bullets={[
        'Kontraste und Lesbarkeit von Texten',
        'Alternativtexte für Bilder und Grafiken',
        'Bedienbarkeit per Tastatur',
        'Struktur, Überschriften und Formularbeschriftungen',
      ]}
      sections={[
        {
          heading: 'Wen betrifft das BFSG?',
          body: [
            'Das Barrierefreiheitsstärkungsgesetz setzt die EU-Richtlinie 2019/882 in deutsches Recht um. Es verpflichtet Unternehmen, bestimmte Produkte und Dienstleistungen für Verbraucherinnen und Verbraucher barrierefrei anzubieten. Dazu gehört ausdrücklich der elektronische Geschäftsverkehr – also Onlineshops und Websites, über die Dienstleistungen für Verbraucher angeboten werden.',
            'Ausgenommen sind Kleinstunternehmen, die Dienstleistungen anbieten: weniger als zehn Beschäftigte und höchstens zwei Millionen Euro Jahresumsatz oder Jahresbilanzsumme. Für Produkte gilt diese Ausnahme nicht. Ob Ihr Unternehmen konkret unter die Pflicht fällt, hängt vom Einzelfall ab – der Check bewertet die technische Seite Ihrer Website, nicht Ihren rechtlichen Status.',
          ],
        },
        {
          heading: 'Was der BFSG-Check technisch prüft',
          body: [
            'Grundlage der Prüfung sind die Erfolgskriterien der WCAG 2.1 auf Stufe AA, auf die sich die europäische Norm EN 301 549 und damit auch die deutsche Umsetzung stützt.',
            'Automatisch messbar sind zum Beispiel: Kontrastverhältnisse zwischen Text und Hintergrund, fehlende Alternativtexte, nicht beschriftete Formularfelder, eine unlogische Überschriftenhierarchie oder Elemente, die sich nicht per Tastatur erreichen lassen.',
            'Ehrlich gesagt: Ein automatischer Test findet je nach Studie rund ein Drittel bis die Hälfte aller Barrieren. Ob eine Bildbeschreibung inhaltlich sinnvoll ist oder ob sich eine Seite mit einem Screenreader tatsächlich gut bedienen lässt, muss ein Mensch beurteilen. Der Check verschafft Ihnen den schnellen Überblick und die Prioritäten – die vollständige Konformitätsbewertung braucht eine manuelle Prüfung.',
          ],
        },
      ]}
      faq={[
        {
          q: 'Seit wann gilt das BFSG?',
          a: 'Das Barrierefreiheitsstärkungsgesetz gilt seit dem 28. Juni 2025.',
        },
        {
          q: 'Ist der BFSG-Check kostenlos?',
          a: 'Ja. Sie erhalten kostenlos und ohne Anmeldung den Score und die betroffenen Bereiche. Die Einzelauflistung aller Fundstellen mit Handlungsempfehlungen ist Teil des kostenpflichtigen Berichts.',
        },
        {
          q: 'Reicht ein automatischer BFSG-Checker für die Konformität aus?',
          a: 'Nein. Automatisierte Tests decken einen Teil der Kriterien zuverlässig ab und sind der schnellste Weg zu einer Prioritätenliste. Eine vollständige Bewertung nach WCAG 2.1 AA erfordert zusätzlich eine manuelle Prüfung.',
        },
        {
          q: 'Welche Norm liegt der Prüfung zugrunde?',
          a: 'Die WCAG 2.1 auf Konformitätsstufe AA, wie sie über die EN 301 549 in den europäischen und deutschen Rechtsrahmen eingebunden ist.',
        },
      ]}
      related={[
        {
          href: '/barrierefreiheit-website-testen',
          label: 'Barrierefreiheit der Website testen',
        },
        { href: '/dsgvo-website-check', label: 'DSGVO-Website-Check' },
      ]}
    />
  );
}
