import type { Metadata } from 'next';
import CheckPage from '@/components/landing/CheckPage';

export const metadata: Metadata = {
  title: 'DSGVO-Website-Check: Website kostenlos prüfen | Complyo',
  description:
    'DSGVO-Website-Check kostenlos: Prüfen Sie Ihre Website in unter einer Minute auf Datenschutz-Verstöße. Ohne Anmeldung, mit sofortigem Ergebnis.',
  keywords:
    'DSGVO Website-Check, DSGVO Website Checker, Website DSGVO Check, DSGVO-Check Website, DSGVO Website Check kostenlos',
  alternates: { canonical: '/dsgvo-website-check/' },
  openGraph: {
    title: 'DSGVO-Website-Check: Website kostenlos prüfen',
    description:
      'Prüfen Sie Ihre Website in unter einer Minute auf DSGVO-Verstöße. Kostenlos, ohne Anmeldung.',
    url: 'https://complyo.de/dsgvo-website-check',
    type: 'website',
  },
};

export default function Page() {
  return (
    <CheckPage
      h1="DSGVO-Website-Check"
      lead="Prüfen Sie Ihre Website kostenlos auf Datenschutz-Verstöße. Der DSGVO-Check analysiert Ihre Seite in unter einer Minute und zeigt, in welchen Bereichen Handlungsbedarf besteht – ohne Anmeldung, ohne Installation."
      bullets={[
        'Cookies und Tracking-Dienste vor Einwilligung',
        'Datenschutzerklärung und Pflichtangaben',
        'Einbindung externer Dienste und Schriftarten',
        'Kontaktformulare und Datenübermittlung',
      ]}
      sections={[
        {
          heading: 'Was der DSGVO-Check Ihrer Website prüft',
          body: [
            'Der Website-DSGVO-Check ruft Ihre Seite so auf, wie es ein Besucher tun würde, und protokolliert dabei, was im Hintergrund passiert: Welche Cookies werden gesetzt, bevor jemand zugestimmt hat? Welche externen Dienste werden geladen? Werden dabei IP-Adressen an Server außerhalb der EU übertragen?',
            'Genau diese Punkte sind es, die in Abmahnungen und bei Prüfungen durch Aufsichtsbehörden auftauchen. Sie sind technisch messbar – anders als etwa die Frage, ob eine Datenschutzerklärung inhaltlich vollständig ist.',
            'Das Ergebnis zeigt Ihnen pro Bereich, ob Auffälligkeiten gefunden wurden und wie viele. Die vollständige Auflistung der einzelnen Fundstellen samt Handlungsempfehlung erhalten Sie im Detailbericht.',
          ],
        },
        {
          heading: 'Warum ein kostenloser DSGVO-Checker sinnvoll ist – und wo seine Grenzen liegen',
          body: [
            'Ein automatischer DSGVO-Checker für Websites findet zuverlässig, was sich technisch auslesen lässt: gesetzte Cookies, geladene Skripte, Verbindungen zu Drittanbietern, fehlende Pflichtseiten. Das deckt einen großen Teil der typischen Verstöße ab und kostet Sie eine Minute.',
            'Was ein automatisierter Check nicht leisten kann, ist die rechtliche Bewertung Ihres Einzelfalls. Ob eine bestimmte Datenverarbeitung in Ihrem Unternehmen zulässig ist, hängt von Ihrem Geschäftsmodell, Ihren Verträgen und Ihrer Dokumentation ab. Der Check ersetzt keine Rechtsberatung – er zeigt Ihnen, wo Sie hinschauen sollten.',
          ],
        },
      ]}
      faq={[
        {
          q: 'Ist der DSGVO-Website-Check wirklich kostenlos?',
          a: 'Ja. Der Check Ihrer Website ist kostenlos und ohne Anmeldung nutzbar. Sie erhalten den Compliance-Score und die betroffenen Bereiche. Die detaillierte Auflistung aller Fundstellen mit Handlungsempfehlungen ist Teil des kostenpflichtigen Berichts.',
        },
        {
          q: 'Wie lange dauert der DSGVO-Check?',
          a: 'In der Regel unter einer Minute. Die Seite wird aufgerufen, das Verhalten im Hintergrund protokolliert und ausgewertet.',
        },
        {
          q: 'Werden meine Daten gespeichert?',
          a: 'Für den Check wird die eingegebene Adresse verarbeitet, um Ihre Website aufzurufen. Details zur Verarbeitung finden Sie in unserer Datenschutzerklärung.',
        },
        {
          q: 'Ersetzt der Check eine Rechtsberatung?',
          a: 'Nein. Der Check prüft technisch messbare Punkte und liefert Ihnen eine belastbare Ausgangslage. Die rechtliche Bewertung Ihres Einzelfalls gehört in die Hände einer Anwältin oder eines Anwalts.',
        },
      ]}
      related={[
        { href: '/bfsg-check', label: 'BFSG-Check: Barrierefreiheitsstärkungsgesetz prüfen' },
        {
          href: '/barrierefreiheit-website-testen',
          label: 'Barrierefreiheit der Website testen',
        },
      ]}
    />
  );
}
