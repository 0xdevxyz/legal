import type { Metadata } from 'next';
import ArticlePage from '@/components/landing/ArticlePage';

export const metadata: Metadata = {
  title: 'WordPress Cookie-Banner richtig einrichten | Complyo',
  description:
    'WordPress Cookie-Banner: Welche Plugins taugen, warum die Installation allein nicht reicht und wie Sie prüfen, ob Ihr Banner Skripte wirklich blockiert.',
  keywords:
    'WordPress Cookie Banner, Cookie Banner WordPress, Cookie Banner WordPress kostenlos, WordPress DSGVO Cookies',
  alternates: { canonical: '/ratgeber/wordpress-cookie-banner/' },
  openGraph: {
    title: 'WordPress Cookie-Banner richtig einrichten',
    description:
      'Welche Plugins taugen, warum die Installation allein nicht reicht – und wie Sie es überprüfen.',
    url: 'https://complyo.de/ratgeber/wordpress-cookie-banner/',
    type: 'article',
  },
};

export default function Page() {
  return (
    <ArticlePage
      slug="wordpress-cookie-banner"
      h1="WordPress Cookie-Banner richtig einrichten"
      lead="Ein Cookie-Plugin zu installieren dauert fünf Minuten. Dass es danach tatsächlich das tut, wofür es da ist, ist der seltenere Fall. Dieser Beitrag zeigt, worauf es bei der Einrichtung ankommt und wie Sie das Ergebnis überprüfen."
      updated="27. Juli 2026"
      readingMinutes={8}
      sections={[
        {
          heading: 'Warum das Plugin allein nichts löst',
          body: [
            'Der entscheidende Punkt ist nicht der Banner, sondern was hinter ihm passiert. Ein Cookie-Banner erfüllt seinen Zweck ausschließlich dann, wenn er einwilligungspflichtige Skripte blockiert, bis eine Zustimmung vorliegt. Wird der Banner angezeigt, während Analytics längst lädt und das Meta-Pixel bereits gefeuert hat, ist er wirkungslos.',
            'Genau hier liegt bei WordPress das typische Problem. Tracking-Codes stecken oft an mehreren Stellen gleichzeitig: im Theme, in der functions.php, in einem separaten Header-Skript-Plugin, in einem Page-Builder-Element oder in einem Marketing-Plugin. Das Cookie-Plugin kennt diese Stellen nicht automatisch – es blockiert nur, was ihm bekannt ist.',
          ],
        },
        {
          heading: 'Die gängigen Plugins im Überblick',
          body: [
            'Für WordPress haben sich einige Lösungen etabliert, die technisches Blockieren beherrschen statt nur einen Hinweis einzublenden.',
          ],
          list: [
            'Real Cookie Banner – deutschsprachig, umfangreiche Dienste-Vorlagen, blockiert bekannte Skripte automatisch. Kostenlose Variante mit begrenztem Funktionsumfang, Vollversion kostenpflichtig.',
            'Borlabs Cookie – aus Deutschland, verbreitet in Agenturprojekten, gute Kontrolle über Content-Blocker für eingebettete Inhalte. Kostenpflichtig.',
            'Complianz – niederländisch, mit Assistent zur Ersteinrichtung und Generator für Datenschutzerklärungen. Kostenlose Basisversion vorhanden.',
            'CookieYes – international verbreitet, kostenloser Einstieg. Beim Blockieren im deutschen Kontext genauer prüfen, ob alle Dienste erfasst werden.',
          ],
        },
        {
          heading: 'Einrichtung Schritt für Schritt',
          ordered: true,
          list: [
            'Bestandsaufnahme: Notieren Sie zuerst, welche externen Dienste die Seite tatsächlich lädt – Analytics, Pixel, Videos, Karten, Schriften, Chat. Ohne diese Liste können Sie nicht beurteilen, ob das Plugin vollständig konfiguriert ist.',
            'Plugin installieren und Dienste anlegen: Jeden gefundenen Dienst im Plugin mit Zweck, Anbieter und Speicherdauer eintragen. Vorlagen erleichtern das, ersetzen aber die Prüfung nicht.',
            'Blockierung aktivieren: Für jeden Dienst festlegen, welches Skript blockiert wird. Bei selbst eingefügten Codes im Theme müssen Sie das Skript-Tag manuell kennzeichnen, damit das Plugin es zurückhalten kann.',
            'Eingebettete Inhalte umstellen: YouTube-Videos und Google Maps über den Content-Blocker des Plugins ausliefern, sodass sie erst nach Zustimmung nachgeladen werden.',
            'Google Fonts lokal einbinden: Damit entfällt eine ganze Einwilligungskategorie. Die Schriften werden einmal heruntergeladen und vom eigenen Server ausgeliefert.',
            'Ablehnung gleichwertig gestalten: „Ablehnen" gehört auf die erste Ebene, gleich sichtbar neben „Akzeptieren" – nicht hinter „Einstellungen" versteckt.',
            'Caching leeren und prüfen: Caching-Plugins liefern häufig noch die alte Seitenversion aus. Ohne Leeren des Caches testen Sie den Zustand von gestern.',
          ],
        },
        {
          heading: 'So überprüfen Sie das Ergebnis selbst',
          body: [
            'Der Test ist einfach und braucht kein Werkzeug: Öffnen Sie Ihre Website in einem privaten Fenster, klicken Sie im Banner nichts an, und sehen Sie in den Entwicklerwerkzeugen des Browsers nach – unter „Anwendung" bei den Cookies, und unter „Netzwerk" bei den geladenen Verbindungen.',
            'Finden Sie dort bereits Einträge von Google, Meta oder anderen Drittanbietern, blockiert Ihr Banner nicht. Technisch notwendige Cookies des Systems und des Cookie-Plugins selbst dürfen vorhanden sein – alles andere nicht.',
            'Prüfen Sie zusätzlich den Widerruf: Es muss einen dauerhaft erreichbaren Weg geben, die Einwilligung zu ändern, üblicherweise einen Link im Footer.',
          ],
        },
        {
          heading: 'Was viele übersehen',
          body: [
            'Die Datenschutzerklärung muss zum Banner passen. Wird im Banner ein Dienst abgefragt, der in der Erklärung nicht auftaucht – oder umgekehrt –, fällt das bei jeder genaueren Prüfung auf.',
            'Und die Konfiguration ist kein einmaliger Vorgang. Jedes neu installierte Plugin, jedes eingebettete Video, jedes zusätzliche Marketing-Werkzeug kann neue Dienste mitbringen, die im Banner nicht erfasst sind. Eine Website, die vor einem Jahr sauber konfiguriert war, ist es heute womöglich nicht mehr.',
          ],
        },
      ]}
      faq={[
        {
          q: 'Gibt es ein kostenloses Cookie-Banner-Plugin für WordPress?',
          a: 'Ja, mehrere Lösungen bieten kostenlose Basisversionen an, darunter Complianz, CookieYes und Real Cookie Banner. Entscheidend ist weniger der Preis als die Frage, ob die Version das automatische Blockieren der von Ihnen genutzten Dienste beherrscht.',
        },
        {
          q: 'Warum setzt meine Seite trotz Banner Cookies?',
          a: 'Meist, weil das Tracking-Skript an einer Stelle eingebunden ist, die das Plugin nicht kennt – etwa direkt im Theme, in der functions.php oder in einem Page-Builder-Element. Solche Einbindungen müssen manuell für die Blockierung gekennzeichnet werden.',
        },
        {
          q: 'Muss der Ablehnen-Knopf auf der ersten Ebene stehen?',
          a: 'Die Ablehnung muss mit vergleichbar geringem Aufwand möglich sein wie die Zustimmung. Die Aufsichtsbehörden haben mehrfach beanstandet, wenn Ablehnen erst über einen zusätzlichen Zwischenschritt erreichbar ist.',
        },
        {
          q: 'Muss ich das Banner nach Änderungen an der Website neu prüfen?',
          a: 'Ja. Neue Plugins, eingebettete Inhalte oder Marketing-Werkzeuge bringen häufig zusätzliche Dienste mit, die im Banner noch nicht erfasst sind. Eine Prüfung nach größeren Änderungen ist sinnvoll.',
        },
      ]}
      cta={{
        heading: 'Ihren WordPress-Banner überprüfen lassen',
        text: 'Der kostenlose Check ruft Ihre Seite auf, ohne den Banner zu bedienen, und listet auf, welche Cookies und externen Dienste trotzdem schon geladen wurden.',
        href: '/dsgvo-website-check/',
        label: 'Website kostenlos prüfen',
      }}
      related={[
        { href: '/ratgeber/cookie-banner-pflicht/', label: 'Cookie-Banner-Pflicht: Was wirklich gilt' },
        { href: '/dsgvo-website-check/', label: 'DSGVO-Website-Check' },
      ]}
    />
  );
}
