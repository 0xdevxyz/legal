import type { Metadata } from 'next';
import ArticlePage from '@/components/landing/ArticlePage';

export const metadata: Metadata = {
  title: 'Cookie-Banner-Pflicht: Was 2026 wirklich gilt | Complyo',
  description:
    'Cookie-Banner Pflicht: Wann ein Banner nötig ist, wann nicht – und welche Anforderungen ein rechtssicherer Banner nach TDDDG und DSGVO erfüllen muss.',
  keywords: 'Cookie Banner Pflicht, Cookie-Banner Pflicht, Cookie Banner rechtssicher, TDDDG Cookies',
  alternates: { canonical: '/ratgeber/cookie-banner-pflicht/' },
  openGraph: {
    title: 'Cookie-Banner-Pflicht: Was 2026 wirklich gilt',
    description:
      'Wann ein Cookie-Banner Pflicht ist, wann nicht – und welche Anforderungen er erfüllen muss.',
    url: 'https://complyo.de/ratgeber/cookie-banner-pflicht/',
    type: 'article',
  },
};

export default function Page() {
  return (
    <ArticlePage
      slug="cookie-banner-pflicht"
      h1="Cookie-Banner-Pflicht: Was wirklich gilt"
      lead="Nicht jede Website braucht ein Cookie-Banner – aber die meisten haben eines, das den Anforderungen nicht genügt. Dieser Beitrag klärt, wann die Pflicht greift und woran rechtssichere Banner in der Praxis scheitern."
      updated="27. Juli 2026"
      readingMinutes={8}
      sections={[
        {
          heading: 'Die Rechtsgrundlage: TDDDG und DSGVO',
          body: [
            'Maßgeblich ist § 25 des Telekommunikation-Digitale-Dienste-Datenschutz-Gesetzes (TDDDG) – bis Mai 2024 hieß es TTDSG. Die Vorschrift setzt die europäische ePrivacy-Richtlinie um und regelt einen eng umrissenen Vorgang: das Speichern von Informationen auf dem Endgerät der Nutzer und den Zugriff darauf.',
            'Wichtig ist die Reichweite. § 25 TDDDG gilt nicht nur für Cookies im technischen Sinn, sondern für jeden Zugriff auf Endgeräte-Informationen – auch für Local Storage, Session Storage oder Fingerprinting-Verfahren. Ein Banner, das nur Cookies abfragt, während im Hintergrund Local Storage beschrieben wird, greift zu kurz.',
            'Davon zu trennen ist die anschließende Verarbeitung der Daten. Für sie gilt die DSGVO und es braucht eine eigene Rechtsgrundlage nach Art. 6. Zwei Ebenen also: Der Zugriff aufs Endgerät richtet sich nach TDDDG, was danach mit den Daten geschieht, nach der DSGVO.',
          ],
        },
        {
          heading: 'Wann Sie kein Banner brauchen',
          body: [
            'Die Einwilligungspflicht entfällt, wenn der Zugriff unbedingt erforderlich ist, damit ein vom Nutzer ausdrücklich gewünschter Dienst funktioniert. Der Maßstab ist eng: Es geht um technische Notwendigkeit, nicht um betriebswirtschaftliche Nützlichkeit.',
          ],
          list: [
            'Warenkorb-Cookies in einem Onlineshop',
            'Session-Cookies zur Aufrechterhaltung eines Logins',
            'Cookies, die die Spracheinstellung speichern',
            'Sicherheitsmechanismen wie Schutz vor Cross-Site-Request-Forgery',
            'Lastverteilung zwischen Servern',
          ],
        },
        {
          heading: 'Wann ein Banner Pflicht ist',
          body: [
            'Sobald etwas geladen wird, das über die technische Notwendigkeit hinausgeht, braucht es eine vorherige Einwilligung. Das betrifft in der Praxis fast jede Website, die mehr tut als Inhalte auszuliefern.',
          ],
          list: [
            'Analyse-Werkzeuge wie Google Analytics oder Matomo mit Cookies',
            'Marketing- und Retargeting-Pixel, etwa von Meta oder LinkedIn',
            'Eingebettete Videos von YouTube oder Vimeo, die beim Laden Cookies setzen',
            'Google Fonts, die von externen Servern nachgeladen werden',
            'Kartendienste wie Google Maps',
            'Chat-Widgets und Bewertungs-Einbindungen',
          ],
        },
        {
          heading: 'Anforderungen an einen wirksamen Banner',
          body: [
            'Der Europäische Gerichtshof hat 2019 in der Entscheidung Planet49 (C-673/17) klargestellt, dass vorangekreuzte Kästchen keine wirksame Einwilligung darstellen. Der Bundesgerichtshof hat das 2020 für Deutschland bestätigt. Daraus und aus den Leitlinien der Aufsichtsbehörden ergeben sich klare Anforderungen.',
          ],
          list: [
            'Aktive Handlung: Keine Voranklickung, kein Weitersurfen als Zustimmung, kein Scrollen als Einwilligung.',
            'Gleichwertige Ablehnung: Ablehnen muss auf derselben Ebene und mit vergleichbarem Aufwand möglich sein wie Zustimmen. Ein „Alle akzeptieren"-Knopf neben einem versteckten Textlink genügt nicht.',
            'Keine irreführende Gestaltung: Gleichwertige Optionen dürfen nicht durch Farbe, Größe oder Kontrast so gestaltet sein, dass die Zustimmung faktisch alternativlos wirkt.',
            'Granularität: Nutzer müssen einzelnen Zwecken zustimmen können, statt nur pauschal allem.',
            'Information vor der Entscheidung: Welche Dienste, welche Zwecke, welche Speicherdauer, welche Empfänger – erkennbar, bevor geklickt wird.',
            'Widerruf jederzeit: Der Widerruf muss so einfach sein wie die Erteilung, üblicherweise über einen dauerhaft erreichbaren Link.',
            'Dokumentation: Die Einwilligung muss nachweisbar sein – wer, wann, wofür, in welcher Bannerversion.',
          ],
        },
        {
          heading: 'Der häufigste Fehler in der Praxis',
          body: [
            'Der mit Abstand häufigste Mangel ist technischer Natur: Der Banner wird angezeigt, aber die Skripte laufen längst. Analytics lädt, das Meta-Pixel feuert, YouTube setzt Cookies – alles, bevor irgendjemand geklickt hat. Der Banner ist dann reine Dekoration.',
            'Ein Banner erfüllt seinen Zweck nur, wenn er einwilligungspflichtige Skripte tatsächlich blockiert, bis die Zustimmung vorliegt. Genau das lässt sich objektiv nachmessen: Man ruft die Seite auf, klickt nichts an und schaut, was gesetzt und geladen wurde.',
            'Der zweite verbreitete Fehler betrifft die Ablehnung. Viele Banner bieten „Alle akzeptieren" als großen Knopf und verstecken die Ablehnung hinter „Einstellungen" – zwei Klicks tiefer. Die Aufsichtsbehörden haben dazu wiederholt Stellung bezogen.',
          ],
        },
      ]}
      faq={[
        {
          q: 'Braucht jede Website ein Cookie-Banner?',
          a: 'Nein. Wenn eine Website ausschließlich technisch notwendige Cookies verwendet, ist kein Einwilligungsbanner erforderlich. Über die Verarbeitung ist in der Datenschutzerklärung dennoch zu informieren.',
        },
        {
          q: 'Sind Google Fonts einwilligungspflichtig?',
          a: 'Wenn sie von externen Servern nachgeladen werden, wird dabei die IP-Adresse übertragen – dann braucht es eine Einwilligung. Werden die Schriften lokal auf dem eigenen Server eingebunden, entfällt das Problem.',
        },
        {
          q: 'Reicht ein „Cookie-Hinweis" ohne Auswahl?',
          a: 'Nein. Ein reiner Hinweis mit einem „OK"-Knopf ist keine Einwilligung, weil er keine echte Wahl lässt. Sobald einwilligungspflichtige Dienste im Spiel sind, muss die Ablehnung gleichwertig möglich sein.',
        },
        {
          q: 'Was droht bei einem fehlerhaften Banner?',
          a: 'In Betracht kommen Beschwerden bei der Aufsichtsbehörde, aufsichtsbehördliche Anordnungen und Bußgelder sowie wettbewerbsrechtliche Abmahnungen. In der Praxis ist die Aufforderung zur Abstellung häufiger als ein Bußgeld – die Kosten entstehen dann durch die kurzfristige Nachbesserung.',
        },
      ]}
      cta={{
        heading: 'Prüfen, was Ihr Banner wirklich tut',
        text: 'Der kostenlose Check ruft Ihre Website auf, ohne etwas anzuklicken, und protokolliert, welche Cookies und Dienste bereits vor jeder Einwilligung geladen werden.',
        href: '/dsgvo-website-check/',
        label: 'Website kostenlos prüfen',
      }}
      related={[
        { href: '/ratgeber/wordpress-cookie-banner/', label: 'Cookie-Banner in WordPress richtig einrichten' },
        { href: '/dsgvo-website-check/', label: 'DSGVO-Website-Check' },
      ]}
    />
  );
}
