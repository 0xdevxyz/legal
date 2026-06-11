import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'EU Compliance Vergleich | Complyo',
};

interface CountryInfo {
  code: string;
  name: string;
  authority: string;
  framework: string;
  specifics: string[];
}

const countries: CountryInfo[] = [
  {
    code: 'DE',
    name: 'Deutschland',
    authority: 'DSK / Landesbehörden',
    framework: 'DSGVO + TTDSG',
    specifics: [
      'Opt-in erforderlich für nicht-essentielle Cookies (§ 25 TTDSG).',
      'Cookie-Consent muss vor dem Setzen von Tracking-Cookies eingeholt werden.',
      'Dark Patterns (vorausgewählte Checkboxen) sind unzulässig.',
      'Widerruf muss genauso einfach sein wie die Einwilligung.',
      'Aufbewahrungspflicht für Einwilligungsnachweise (Rechenschaftspflicht).',
    ],
  },
  {
    code: 'AT',
    name: 'Österreich',
    authority: 'Datenschutzbehörde (DSB)',
    framework: 'DSGVO + TKG 2021',
    specifics: [
      'Opt-in für alle nicht technisch notwendigen Cookies (§ 165 TKG 2021).',
      'Kein "Consent via scrolling" akzeptiert.',
      'Abonnement-Modelle ("Pay or OK") unter verstärkter Beobachtung.',
      'DSB folgt weitgehend EDPB-Leitlinien zu Cookie-Bannern.',
    ],
  },
  {
    code: 'CH',
    name: 'Schweiz',
    authority: 'EDÖB',
    framework: 'revDSG + FMG',
    specifics: [
      'Neues revDSG seit 1. September 2023 in Kraft.',
      'Opt-in für Tracking-Cookies nach Art. 45c FMG erforderlich.',
      'Schweizer Recht gilt für in der Schweiz ansässige Nutzer.',
      'Datenschutzerklärung muss über Cookie-Nutzung informieren.',
    ],
  },
  {
    code: 'FR',
    name: 'Frankreich',
    authority: 'CNIL',
    framework: 'DSGVO + Loi Informatique et Libertés',
    specifics: [
      'CNIL verlangt gleichwertigen "Alles ablehnen"-Button neben "Alles akzeptieren".',
      'Cookie-Walls nur unter strengen Bedingungen erlaubt.',
      'Consent-Management muss CNIL-Referenzrahmen für CMPs entsprechen.',
      'Bußgelder bei Verstößen besonders aktiv durchgesetzt (z. B. Google, Facebook).',
      'Statistik-Cookies können unter bestimmten Bedingungen ohne Consent gesetzt werden.',
    ],
  },
  {
    code: 'IT',
    name: 'Italien',
    authority: 'Garante',
    framework: 'DSGVO + Codice Privacy',
    specifics: [
      'Garante-Leitlinien 2021: klare Hierarchie zwischen primären und sekundären Cookies.',
      '"X"-Schaltfläche zum Schließen des Banners gilt als Ablehnung.',
      'Cookie-Walls grundsätzlich unzulässig.',
      'Scroll- oder Klick-Consent ist nicht ausreichend.',
      'Jährliche Erneuerung der Einwilligung empfohlen.',
    ],
  },
  {
    code: 'NL',
    name: 'Niederlande',
    authority: 'Autoriteit Persoonsgegevens (AP)',
    framework: 'DSGVO + Telecommunicatiewet',
    specifics: [
      'Opt-in für Tracking- und Analyse-Cookies vorgeschrieben.',
      'AP hat mehrfach hohe Bußgelder für Cookie-Walls verhängt.',
      'Einwilligung muss granular pro Zweck eingeholt werden.',
      'Fingerprinting fällt ebenfalls unter Einwilligungspflicht.',
    ],
  },
];

export default function ComplianceCountriesPage() {
  return (
    <div className="px-4 sm:px-6 py-6">
      <h1 className="text-2xl font-bold mb-2 dark:text-white text-gray-900">EU Compliance Vergleich</h1>
      <p className="dark:text-gray-400 text-gray-600 mb-8 text-sm">
        Cookie- und DSGVO-Anforderungen nach Land — Stand 2024/2025.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {countries.map((country) => (
          <div key={country.code} className="dark:bg-zinc-800 bg-gray-100 rounded-lg p-6 flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold dark:text-white text-gray-900">{country.code}</span>
              <div>
                <p className="dark:text-white text-gray-900 font-semibold leading-tight">{country.name}</p>
                <p className="dark:text-gray-400 text-gray-600 text-xs">{country.authority}</p>
              </div>
            </div>

            <span className="inline-block self-start bg-zinc-700 dark:text-gray-300 text-gray-700 text-xs px-2 py-0.5 rounded">
              {country.framework}
            </span>

            <ul className="space-y-2 mt-1">
              {country.specifics.map((point, i) => (
                <li key={i} className="flex gap-2 text-sm dark:text-gray-300 text-gray-700">
                  <span className="mt-0.5 text-gray-500 shrink-0">&#8250;</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
