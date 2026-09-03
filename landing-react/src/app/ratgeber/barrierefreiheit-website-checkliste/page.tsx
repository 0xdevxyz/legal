import type { Metadata } from 'next';
import ArticlePage from '@/components/landing/ArticlePage';

export const metadata: Metadata = {
  title: 'Barrierefreiheit Website: Checkliste mit 12 Punkten | Complyo',
  description:
    'Checkliste Barrierefreiheit für Websites: die 12 wichtigsten Kriterien nach WCAG 2.1 AA – verständlich erklärt, mit Prüfhinweis und typischen Fehlern.',
  keywords:
    'Barrierefreiheit Website Checkliste, Checkliste barrierefreie Website, WCAG Checkliste, BFSG Checkliste',
  alternates: { canonical: '/ratgeber/barrierefreiheit-website-checkliste/' },
  openGraph: {
    title: 'Barrierefreiheit Website: Checkliste mit 12 Punkten',
    description:
      'Die 12 wichtigsten Kriterien nach WCAG 2.1 AA – verständlich erklärt, mit typischen Fehlern.',
    url: 'https://complyo.de/ratgeber/barrierefreiheit-website-checkliste/',
    type: 'article',
  },
};

export default function Page() {
  return (
    <ArticlePage
      slug="barrierefreiheit-website-checkliste"
      h1="Barrierefreiheit Website: Checkliste mit 12 Punkten"
      lead="Diese Checkliste führt durch die zwölf Kriterien, an denen Websites in der Praxis am häufigsten scheitern. Alle beziehen sich auf die WCAG 2.1 Stufe AA – den Standard, auf den sich auch das Barrierefreiheitsstärkungsgesetz stützt."
      updated="27. Juli 2026"
      readingMinutes={9}
      sections={[
        {
          heading: 'Wofür diese Checkliste gilt',
          body: [
            'Die Web Content Accessibility Guidelines (WCAG) 2.1 sind der international anerkannte Standard für barrierefreie Webinhalte. Sie kennen drei Konformitätsstufen: A, AA und AAA. Maßgeblich ist in Europa die Stufe AA – über die Norm EN 301 549 ist sie auch der Bezugspunkt für das deutsche Barrierefreiheitsstärkungsgesetz, das seit dem 28. Juni 2025 gilt.',
            'Die WCAG gliedern sich in vier Prinzipien: Inhalte müssen wahrnehmbar, bedienbar, verständlich und robust sein. Die folgenden zwölf Punkte sind daraus die, die in Prüfungen am häufigsten auffallen – nicht die vollständige Norm, aber der Teil mit dem größten Hebel.',
          ],
        },
        {
          heading: 'Die Checkliste',
          ordered: true,
          list: [
            'Farbkontrast bei Text: Normaler Text braucht mindestens 4,5:1 zum Hintergrund, großer Text (ab 18,66 px fett oder 24 px) mindestens 3:1. Hellgraue Schrift auf Weiß ist der mit Abstand häufigste Verstoß.',
            'Farbkontrast bei Bedienelementen: Ränder von Eingabefeldern, Icons und Schaltflächen brauchen mindestens 3:1 – sonst ist nicht erkennbar, wo man klicken kann.',
            'Farbe als alleiniger Bedeutungsträger: Ein rot markiertes Pflichtfeld ist für farbenblinde Nutzer unsichtbar. Es braucht zusätzlich ein Symbol oder Text.',
            'Alternativtexte: Jedes informationstragende Bild braucht eine Beschreibung im alt-Attribut. Rein dekorative Bilder bekommen ein leeres alt="" – dann überspringt der Screenreader sie, statt den Dateinamen vorzulesen.',
            'Überschriftenhierarchie: Genau eine H1 pro Seite, darunter H2, darunter H3 – ohne Ebenen zu überspringen. Überschriften dürfen nicht als reine Schriftvergrößerung missbraucht werden.',
            'Formularbeschriftungen: Jedes Eingabefeld braucht ein verknüpftes label-Element. Ein Platzhaltertext genügt nicht, weil er beim Tippen verschwindet.',
            'Fehlermeldungen: Sie müssen benennen, welches Feld betroffen ist und was zu tun ist. „Eingabe ungültig" erfüllt das nicht.',
            'Tastaturbedienung: Jede Funktion muss ohne Maus erreichbar sein. Menüs, die nur auf Hover reagieren, und Elemente, die per Tastatur nicht ansteuerbar sind, fallen durch.',
            'Sichtbarer Fokus: Es muss jederzeit erkennbar sein, wo der Tastaturfokus steht. Das verbreitete outline: none im CSS entfernt genau diese Anzeige.',
            'Logische Fokusreihenfolge: Beim Durchtabben muss die Reihenfolge dem visuellen Aufbau folgen. Positionierung per CSS kann sie unbemerkt durcheinanderbringen.',
            'Sprachauszeichnung: Das html-Element braucht lang="de". Ohne diese Angabe liest ein Screenreader deutschen Text mit englischer Aussprache vor.',
            'Verständliche Linktexte: „Hier klicken" oder „mehr" sagen ohne Kontext nichts. Screenreader-Nutzer lassen sich häufig nur die Linkliste ausgeben – dort muss jeder Eintrag für sich verständlich sein.',
          ],
        },
        {
          heading: 'Was sich automatisch prüfen lässt – und was nicht',
          body: [
            'Von diesen zwölf Punkten sind etwa die Hälfte maschinell zuverlässig messbar: Kontrastwerte, fehlende Alternativtexte, fehlende Labels, Überschriftenstruktur, Sprachauszeichnung, fehlender Fokusindikator. Ein automatischer Test findet sie in Sekunden.',
            'Die andere Hälfte braucht ein menschliches Urteil. Ob ein Alternativtext das Bild sinnvoll beschreibt, ob die Fokusreihenfolge logisch ist, ob eine Fehlermeldung wirklich weiterhilft – das kann Software nicht bewerten. Untersuchungen gehen davon aus, dass automatisierte Tests rund ein Drittel bis die Hälfte aller Barrieren erfassen.',
            'Praktisch heißt das: Der automatische Test ist der richtige erste Schritt, weil er die schnell behebbaren Fehler zutage fördert. Wer Konformität nachweisen muss, ergänzt ihn um eine manuelle Prüfung.',
          ],
        },
        {
          heading: 'In welcher Reihenfolge vorgehen',
          body: [
            'Beginnen Sie mit den Kontrasten. Sie betreffen meist die gesamte Website auf einen Schlag, sind zentral im Stylesheet zu beheben und wirken sofort für alle Seiten.',
            'Danach folgen Formulare und Fokusindikator – das sind die Punkte, an denen Nutzer konkret hängenbleiben und abspringen. Alternativtexte und Überschriftenstruktur sind Fleißarbeit pro Seite und lassen sich gut nach und nach abarbeiten.',
          ],
        },
      ]}
      faq={[
        {
          q: 'Welche WCAG-Stufe muss meine Website erfüllen?',
          a: 'Maßgeblich ist Stufe AA. Sie ist über die Norm EN 301 549 der Bezugspunkt für das Barrierefreiheitsstärkungsgesetz. Stufe AAA gilt als Ziel für einzelne Inhalte, wird aber nicht flächendeckend verlangt.',
        },
        {
          q: 'Gilt das Barrierefreiheitsstärkungsgesetz für meinen Betrieb?',
          a: 'Das BFSG gilt seit dem 28. Juni 2025 für viele Unternehmen, die Produkte oder Dienstleistungen für Verbraucher anbieten – darunter der elektronische Geschäftsverkehr. Für Dienstleistungen gibt es eine Ausnahme für Kleinstunternehmen mit weniger als zehn Beschäftigten und höchstens zwei Millionen Euro Jahresumsatz. Für Produkte gilt diese Ausnahme nicht.',
        },
        {
          q: 'Wie prüfe ich den Farbkontrast?',
          a: 'Mit einem Kontrastrechner, in den Sie Vorder- und Hintergrundfarbe eingeben, oder direkt über einen automatischen Website-Test, der alle Textelemente auf einmal misst.',
        },
        {
          q: 'Reicht ein Barrierefreiheits-Plugin aus?',
          a: 'Nein. Overlay-Werkzeuge, die per Skript eine Bedienleiste einblenden, beheben die zugrunde liegenden Probleme im Quelltext nicht und stehen in der Fachwelt in der Kritik. Barrierefreiheit entsteht im Markup, nicht in einer Zusatzschicht darüber.',
        },
      ]}
      cta={{
        heading: 'Checkliste automatisch abarbeiten',
        text: 'Der kostenlose Test prüft Ihre Website auf die maschinell messbaren Punkte dieser Liste und zeigt in unter einer Minute, wo es hakt.',
        href: '/barrierefreiheit-website-testen/',
        label: 'Website jetzt testen',
      }}
      related={[
        { href: '/bfsg-check/', label: 'BFSG-Check: Barrierefreiheitsstärkungsgesetz prüfen' },
        { href: '/ratgeber/cookie-banner-pflicht/', label: 'Cookie-Banner-Pflicht: Was gilt wirklich?' },
      ]}
    />
  );
}
