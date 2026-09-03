import type { Metadata } from 'next';
import CheckPage from '@/components/landing/CheckPage';

export const metadata: Metadata = {
  title: 'Barrierefreiheit der Website testen – kostenlos | Complyo',
  description:
    'Website auf Barrierefreiheit testen: kostenloser Test nach WCAG 2.1 AA. Ergebnis in unter einer Minute, ohne Anmeldung – inklusive Checkliste der wichtigsten Kriterien.',
  keywords:
    'Barrierefreiheit Website testen, Barrierefreiheit Website Test, Website Barrierefreiheit testen, Website auf Barrierefreiheit testen, Barrierefreiheit Website Checkliste',
  alternates: { canonical: '/barrierefreiheit-website-testen/' },
  openGraph: {
    title: 'Barrierefreiheit der Website testen – kostenlos',
    description:
      'Kostenloser Test Ihrer Website auf Barrierefreiheit nach WCAG 2.1 AA. Ergebnis in unter einer Minute.',
    url: 'https://complyo.de/barrierefreiheit-website-testen',
    type: 'website',
  },
};

export default function Page() {
  return (
    <CheckPage
      h1="Barrierefreiheit der Website testen"
      lead="Testen Sie Ihre Website kostenlos auf Barrierefreiheit. Der Test orientiert sich an den WCAG 2.1 auf Stufe AA und zeigt in unter einer Minute, welche Kriterien Ihre Seite noch nicht erfüllt – ohne Anmeldung."
      bullets={[
        'Farbkontraste von Text und Bedienelementen',
        'Alternativtexte für Bilder',
        'Tastaturbedienbarkeit und Fokus-Sichtbarkeit',
        'Überschriftenstruktur und Formularbeschriftungen',
      ]}
      sections={[
        {
          heading: 'Checkliste: Die wichtigsten Kriterien für eine barrierefreie Website',
          body: [
            'Kontrast: Normaler Text braucht ein Kontrastverhältnis von mindestens 4,5:1 zum Hintergrund, großer Text mindestens 3:1. Hellgraue Schrift auf Weiß ist der häufigste Verstoß überhaupt.',
            'Alternativtexte: Jedes Bild, das Information transportiert, braucht eine Beschreibung. Rein dekorative Bilder bekommen ein leeres alt-Attribut, damit Screenreader sie überspringen.',
            'Tastaturbedienung: Jede Funktion muss ohne Maus erreichbar sein, und es muss jederzeit sichtbar sein, wo der Fokus gerade steht. Menüs, die nur auf Hover reagieren, fallen hier durch.',
            'Struktur: Überschriften müssen der Hierarchie nach aufgebaut sein – eine H1, darunter H2, darunter H3. Überschriften nur als optische Formatierung zu verwenden, macht die Seite unnavigierbar.',
            'Formulare: Jedes Eingabefeld braucht eine dauerhaft sichtbare Beschriftung. Ein Platzhaltertext im Feld reicht nicht, weil er beim Tippen verschwindet.',
            'Verständliche Links: „Hier klicken" sagt außerhalb des Kontexts nichts. Der Linktext sollte allein stehend erklären, wohin er führt.',
          ],
        },
        {
          heading: 'Was ein automatischer Test leisten kann – und was nicht',
          body: [
            'Wenn Sie eine Website auf Barrierefreiheit testen, deckt ein automatisierter Test die messbaren Kriterien zuverlässig ab: Kontrastwerte, fehlende Attribute, technische Strukturfehler. Das ist der schnellste Weg zu einer Prioritätenliste und findet erfahrungsgemäß einen erheblichen Teil der Probleme.',
            'Die andere Hälfte braucht ein menschliches Urteil. Ob ein Alternativtext das Bild sinnvoll beschreibt, ob die Reihenfolge beim Durchtabben logisch ist, ob eine Fehlermeldung verständlich formuliert ist – das kann keine Software bewerten. Wer Konformität nachweisen muss, kommt um eine manuelle Prüfung nicht herum.',
            'Für den Einstieg gilt trotzdem: Die technisch messbaren Fehler sind meist auch die, die am schnellsten behoben sind und am meisten bewirken.',
          ],
        },
      ]}
      faq={[
        {
          q: 'Wie teste ich meine Website auf Barrierefreiheit?',
          a: 'Geben Sie die Adresse Ihrer Website oben ein. Die Seite wird aufgerufen und gegen die technisch prüfbaren Kriterien der WCAG 2.1 AA getestet. Sie erhalten in unter einer Minute einen Überblick über die betroffenen Bereiche.',
        },
        {
          q: 'Ist der Barrierefreiheits-Test kostenlos?',
          a: 'Ja, der Test ist kostenlos und ohne Anmeldung nutzbar. Die vollständige Auflistung aller Fundstellen mit Handlungsempfehlungen gehört zum kostenpflichtigen Bericht.',
        },
        {
          q: 'Nach welchem Standard wird geprüft?',
          a: 'Nach den WCAG 2.1 auf Konformitätsstufe AA – dem Standard, auf den sich auch die europäische Norm EN 301 549 und das deutsche Barrierefreiheitsstärkungsgesetz stützen.',
        },
        {
          q: 'Muss meine Website barrierefrei sein?',
          a: 'Seit dem 28. Juni 2025 verpflichtet das Barrierefreiheitsstärkungsgesetz viele Unternehmen im Verbrauchergeschäft dazu. Für Dienstleistungen gibt es eine Ausnahme für Kleinstunternehmen. Ob die Pflicht für Sie gilt, hängt vom Einzelfall ab.',
        },
      ]}
      related={[
        { href: '/bfsg-check', label: 'BFSG-Check: Barrierefreiheitsstärkungsgesetz prüfen' },
        { href: '/dsgvo-website-check', label: 'DSGVO-Website-Check' },
      ]}
    />
  );
}
