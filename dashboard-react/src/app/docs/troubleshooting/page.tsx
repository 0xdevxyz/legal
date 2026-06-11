import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Troubleshooting | Complyo',
};

const items = [
  {
    number: 1,
    title: 'Script-URL falsch',
    description:
      'Prüfen Sie ob data-site-id korrekt gesetzt ist. Die Site-ID finden Sie im Complyo-Dashboard unter Ihrem Website-Eintrag.',
  },
  {
    number: 2,
    title: 'Cache',
    description:
      'Browser-Cache leeren (Ctrl+Shift+R) und CDN-Cache purgen. Gecachte Seiten liefern möglicherweise eine alte Version ohne das Script.',
  },
  {
    number: 3,
    title: 'Adblocker',
    description:
      'Adblocker oder Browser-Erweiterungen können das Banner blockieren. Testen Sie die Seite im Inkognito-Modus ohne Erweiterungen.',
  },
  {
    number: 4,
    title: 'localStorage',
    description:
      'Wenn der Nutzer schon Consent gegeben hat, erscheint das Banner nicht erneut. Im DevTools → Application → localStorage → complyo_cookie_consent löschen zum Testen.',
  },
  {
    number: 5,
    title: 'Script-Reihenfolge',
    description:
      'Das Complyo-Script muss vor anderen Analytics-Scripts geladen werden, damit es deren Ausführung korrekt steuern kann.',
  },
  {
    number: 6,
    title: 'CSP (Content Security Policy)',
    description:
      'api.complyo.de muss in script-src und connect-src erlaubt sein. Prüfen Sie den HTTP-Header Content-Security-Policy Ihrer Website.',
  },
  {
    number: 7,
    title: 'HTTPS',
    description:
      'Das Widget funktioniert nur auf HTTPS-Seiten (nicht auf http://). Stellen Sie sicher, dass Ihre Website über ein gültiges SSL-Zertifikat verfügt.',
  },
  {
    number: 8,
    title: 'Domain nicht registriert',
    description:
      'Die Domain muss im Complyo-Dashboard unter "Websites" registriert sein. Nicht registrierte Domains werden vom Widget abgewiesen.',
  },
];

export default function TroubleshootingPage() {
  return (
    <div className="px-4 sm:px-6 py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold dark:text-white text-gray-900 mb-4">
            Troubleshooting — Banner nicht sichtbar?
          </h1>
          <p className="dark:text-zinc-400 text-gray-600 text-lg">
            Wenn das Cookie-Banner auf Ihrer Website nicht erscheint, prüfen Sie die folgenden
            häufigen Ursachen der Reihe nach.
          </p>
        </div>

        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.number}
              className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-gray-200 rounded-2xl p-6 flex gap-5 items-start"
            >
              {/* Number badge */}
              <span className="flex-shrink-0 w-10 h-10 rounded-full dark:bg-zinc-800 bg-gray-100 border dark:border-zinc-700 border-gray-200 flex items-center justify-center dark:text-white text-gray-900 font-bold text-lg">
                {item.number}
              </span>

              <div>
                <h2 className="text-lg font-semibold dark:text-white text-gray-900 mb-1">{item.title}</h2>
                <p className="dark:text-zinc-400 text-gray-600 text-sm leading-relaxed">{item.description}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-6 border-t dark:border-zinc-800 border-gray-200 text-center dark:text-zinc-500 text-gray-500 text-sm">
          <a href="/dashboard" className="text-blue-400 hover:text-blue-300">
            ← Zurück zum Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
