'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, ShieldCheck } from 'lucide-react';
import { ANBIETER, ANBIETER_VERTRAGSPARTEI } from '@/lib/anbieter';
import AnbieterUnvollstaendig from '@/components/legal/AnbieterUnvollstaendig';

/**
 * Auftragsverarbeitungsvertrag nach Art. 28 DSGVO.
 *
 * Warum es ihn gibt: sobald complyo auf einer Kundenwebsite laeuft, verarbeiten
 * wir Daten der Besucher DIESER Website — Einwilligungsprotokolle, die
 * IP-Adressen, mit denen das Widget unsere API aufruft, und die Inhalte der
 * geprueften Seiten. Das ist Auftragsverarbeitung. Ohne einen Vertrag mit dem
 * Inhalt des Art. 28 Abs. 3 DSGVO handelt der Kunde rechtswidrig, und wir als
 * Auftragsverarbeiter haften daneben (Art. 83 Abs. 4 lit. a DSGVO).
 *
 * Bis zum 10.09.2026 gab es diesen Vertrag nicht — weder als Seite noch im
 * Onboarding. Die AGB nannten unter "Datenschutz" nur die Verarbeitung der
 * KUNDENDATEN durch uns als Verantwortliche, also den kleineren Teil.
 *
 * VOR VEROEFFENTLICHUNG ANWALTLICH PRUEFEN LASSEN. Der Text folgt dem
 * Pflichtenkatalog des Art. 28 Abs. 3 und ist bewusst schlicht gehalten;
 * geprueft ist er nicht.
 */

// Next.js erlaubt in einer page.tsx nur bestimmte Exporte; die Fassung steht
// deshalb in lib/vertragsstand.ts und wird auch von der Registrierung genutzt.
const STAND = '10. September 2026';

export default function AVVPage() {
  return (
    <main id="inhalt" tabIndex={-1} className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-akzent-50">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <Link href="/" className="inline-flex items-center gap-2 text-akzent-700 hover:text-akzent-800 mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Zurück zur Startseite
          </Link>

          <AnbieterUnvollstaendig seite="Die Parteien dieses Vertrages" />

          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <ShieldCheck className="w-8 h-8 text-akzent-700" />
              <h1 className="text-4xl font-bold text-gray-900">Auftragsverarbeitungsvertrag</h1>
            </div>
            <p className="text-gray-600">Nach Art. 28 DSGVO · Stand: {STAND}</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 space-y-8 text-sm leading-relaxed text-gray-700">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Parteien</h2>
              <p>
                Dieser Vertrag gilt zwischen dem Kunden (nachfolgend "Verantwortlicher") und {ANBIETER_VERTRAGSPARTEI} (nachfolgend "Auftragsverarbeiter"). Er wird mit der Registrierung eines Kundenkontos in Textform geschlossen (Art. 28 Abs. 9 DSGVO) und gilt für die gesamte Dauer der Nutzung der Plattform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 1 Gegenstand und Dauer</h2>
              <p>
                (1) Der Auftragsverarbeiter erbringt für den Verantwortlichen Leistungen zur Prüfung, Reparatur und Dokumentation der Website-Compliance. Dabei verarbeitet er personenbezogene Daten im Auftrag. Einzelheiten stehen in Anlage 1.
              </p>
              <p>
                (2) Die Verarbeitung beginnt mit der Nutzung der Plattform und endet mit dem Ende des Hauptvertrages. Eine gesonderte Kündigung dieses Vertrages ist nicht möglich; er teilt das Schicksal des Hauptvertrages.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 2 Weisungsrecht</h2>
              <p>
                (1) Der Auftragsverarbeiter verarbeitet personenbezogene Daten ausschließlich auf dokumentierte Weisung des Verantwortlichen. Die Nutzung der Plattform und ihrer Einstellungen gilt als Weisung; darüber hinausgehende Weisungen sind in Textform an {ANBIETER.datenschutzEmail} zu richten.
              </p>
              <p>
                (2) Hält der Auftragsverarbeiter eine Weisung für rechtswidrig, teilt er dies unverzüglich mit und darf ihre Ausführung bis zur Bestätigung aussetzen (Art. 28 Abs. 3 Satz 3 DSGVO).
              </p>
              <p>
                (3) Eine Übermittlung in ein Drittland erfolgt nur nach Maßgabe von Anlage 3 oder auf Weisung des Verantwortlichen.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 3 Vertraulichkeit</h2>
              <p>
                Der Auftragsverarbeiter setzt zur Verarbeitung nur Personen ein, die zur Vertraulichkeit verpflichtet sind oder einer angemessenen gesetzlichen Verschwiegenheitspflicht unterliegen (Art. 28 Abs. 3 lit. b DSGVO), und macht sie mit den einschlägigen Vorgaben vertraut.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 4 Technische und organisatorische Maßnahmen</h2>
              <p>
                (1) Der Auftragsverarbeiter trifft die Maßnahmen nach Art. 32 DSGVO. Der Stand ist in Anlage 2 beschrieben.
              </p>
              <p>
                (2) Die Maßnahmen unterliegen dem technischen Fortschritt. Der Auftragsverarbeiter darf sie ändern, solange das Schutzniveau nicht unterschritten wird.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 5 Unterauftragsverarbeiter</h2>
              <p>
                (1) Der Verantwortliche erteilt die allgemeine schriftliche Genehmigung zum Einsatz der in Anlage 3 genannten weiteren Auftragsverarbeiter (Art. 28 Abs. 2 Satz 2 DSGVO).
              </p>
              <p>
                (2) Beabsichtigte Änderungen teilt der Auftragsverarbeiter mindestens vier Wochen vorher in Textform mit. Der Verantwortliche kann binnen zwei Wochen aus wichtigem datenschutzrechtlichem Grund widersprechen; kommt keine Einigung zustande, kann er den Hauptvertrag zum Zeitpunkt der Änderung außerordentlich kündigen.
              </p>
              <p>
                (3) Der Auftragsverarbeiter erlegt jedem weiteren Auftragsverarbeiter dieselben Datenschutzpflichten auf, die ihn selbst treffen.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 6 Unterstützung des Verantwortlichen</h2>
              <p>
                (1) Der Auftragsverarbeiter unterstützt den Verantwortlichen bei der Beantwortung von Anträgen betroffener Personen (Art. 12 bis 23 DSGVO). Auskunft, Export und Löschung der im Auftrag verarbeiteten Daten sind über die Plattform selbst auslösbar.
              </p>
              <p>
                (2) Er unterstützt bei der Einhaltung der Art. 32 bis 36 DSGVO, insbesondere bei Sicherheit der Verarbeitung, Meldung von Verletzungen und Datenschutz-Folgenabschätzung.
              </p>
              <p>
                (3) Eine Verletzung des Schutzes personenbezogener Daten meldet der Auftragsverarbeiter dem Verantwortlichen unverzüglich, spätestens innerhalb von 24 Stunden nach Kenntnis, mit den Angaben nach Art. 33 Abs. 3 DSGVO, soweit sie ihm vorliegen.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 7 Löschung und Rückgabe</h2>
              <p>
                (1) Nach Ende des Hauptvertrages löscht der Auftragsverarbeiter die im Auftrag verarbeiteten Daten binnen 90 Tagen, soweit keine gesetzliche Aufbewahrungspflicht besteht. Der Verantwortliche kann innerhalb dieser Frist die Herausgabe in einem gängigen Format verlangen.
              </p>
              <p>
                (2) Einwilligungsprotokolle werden unabhängig davon 24 Monate nach ihrer Entstehung gelöscht; sie dienen dem Nachweis nach Art. 7 Abs. 1 DSGVO.
              </p>
              <p>
                (3) Sicherungskopien werden nach ihrem regulären Zyklus überschrieben, längstens innerhalb von 30 Tagen.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 8 Nachweise und Kontrollen</h2>
              <p>
                (1) Der Auftragsverarbeiter stellt dem Verantwortlichen auf Anfrage die Informationen zur Verfügung, die zum Nachweis der Einhaltung der Pflichten aus Art. 28 DSGVO erforderlich sind, und ermöglicht Überprüfungen (Art. 28 Abs. 3 lit. h DSGVO).
              </p>
              <p>
                (2) Vor-Ort-Prüfungen sind mit angemessener Vorlaufzeit von mindestens zwei Wochen, während der üblichen Geschäftszeiten und ohne Störung des Betriebsablaufs anzukündigen. Der Auftragsverarbeiter kann sie durch geeignete Nachweise ersetzen, soweit diese die Kontrollzwecke erfüllen.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">§ 9 Schlussbestimmungen</h2>
              <p>
                (1) Bei Widersprüchen zwischen diesem Vertrag und dem Hauptvertrag gehen die Regelungen dieses Vertrages vor, soweit es die Verarbeitung personenbezogener Daten im Auftrag betrifft.
              </p>
              <p>
                (2) Die Haftung richtet sich nach Art. 82 DSGVO und im Übrigen nach den Regelungen des Hauptvertrages.
              </p>
              <p>
                (3) Änderungen bedürfen der Textform.
              </p>
            </section>

            <hr className="border-gray-200" />

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Anlage 1 — Gegenstand der Verarbeitung</h2>
              <div className="space-y-3">
                <p><strong>Art und Zweck:</strong> Prüfung von Websites auf Barrierefreiheit, Datenschutz und Cookie-Einwilligung; Erzeugung und Auslieferung von Reparaturen und Rechtstexten; Protokollierung von Einwilligungen zum Nachweis nach Art. 7 Abs. 1 DSGVO; Betrieb der Widgets auf der Website des Verantwortlichen.</p>
                <p><strong>Kategorien betroffener Personen:</strong> Besucher der Website des Verantwortlichen; Beschäftigte und Ansprechpartner des Verantwortlichen, soweit ihre Angaben auf der geprüften Website stehen oder für Rechtstexte eingegeben werden.</p>
                <p><strong>Arten personenbezogener Daten:</strong></p>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Einwilligungsprotokolle: pseudonyme Besucherkennung, gekürzter Hashwert der IP-Adresse, Browserkennung, Zeitpunkt, gewählte Kategorien und Dienste, Sprache, Fassung des Banners.</li>
                  <li>Verbindungsdaten: IP-Adresse und Zeitpunkt, wenn der Browser eines Besuchers das Widget von api.complyo.de lädt.</li>
                  <li>Inhalte der geprüften Website, soweit dort personenbezogene Daten stehen (etwa Impressum, Ansprechpartner, Bilder von Personen).</li>
                  <li>Angaben, die der Verantwortliche für die Erzeugung von Rechtstexten selbst einträgt.</li>
                  <li>Meldungen des Widgets über angewendete Reparaturen je Seitenaufruf (Pfad und Zähler, ohne Besucherbezug).</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Anlage 2 — Technische und organisatorische Maßnahmen</h2>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>Vertraulichkeit (Zutritt, Zugang, Zugriff):</strong> Server in einem Rechenzentrum in Deutschland mit Zutrittskontrolle des Betreibers. Zugang zur Verwaltung ausschließlich über SSH mit Schlüssel; keine Passwortanmeldung. Getrennte Konten je Anwendung, Container ohne Systemrechte.</li>
                <li><strong>Trennung:</strong> Die Daten sind je Kundenkonto getrennt; jeder Zugriff auf eine Website-Kennung wird gegen die Websites des Kontos geprüft.</li>
                <li><strong>Verschlüsselung:</strong> Transportverschlüsselung (TLS) auf allen öffentlichen Wegen, HSTS mit Vorladeliste. Passwörter als bcrypt-Hash. IP-Adressen in Einwilligungsprotokollen nur als Hashwert.</li>
                <li><strong>Integrität:</strong> Schutz gegen Anfragefälschung (CSRF), Begrenzung der Anfragezahl je Besucher-IP, Sperre für Abrufe in interne Netze, Prüfung jeder Adressauflösung beim Verbindungsaufbau.</li>
                <li><strong>Verfügbarkeit:</strong> Tägliche Sicherung um 02:30 Uhr mit anschließender Wiederherstellungsprobe. Überwachung des Betriebs mit stündlichen Prüfungen der Geschäftsfunktionen.</li>
                <li><strong>Belastbarkeit:</strong> Getrennte Prozesse für Scan und Auslieferung, Speicher- und Laufzeitgrenzen je Prüfung.</li>
                <li><strong>Überprüfung:</strong> Automatisierte Testsuite mit über 2.000 Prüfungen, darunter Wächter für Mandantentrennung, öffentliche Endpunkte und Abrufsperren. Regelmäßige Prüfung der eingesetzten Fremdbibliotheken auf bekannte Schwachstellen.</li>
              </ul>
              <p className="mt-3 text-gray-500">
                Der Stand dieser Maßnahmen wird fortgeschrieben. Maßgeblich ist die jeweils veröffentlichte Fassung.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Anlage 3 — Weitere Auftragsverarbeiter</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="border border-gray-200 p-2">Dienstleister</th>
                      <th className="border border-gray-200 p-2">Leistung</th>
                      <th className="border border-gray-200 p-2">Ort der Verarbeitung</th>
                      <th className="border border-gray-200 p-2">Grundlage</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-gray-200 p-2">IONOS SE, Montabaur</td>
                      <td className="border border-gray-200 p-2">Betrieb der Server</td>
                      <td className="border border-gray-200 p-2">Deutschland</td>
                      <td className="border border-gray-200 p-2">Art. 28 DSGVO</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-200 p-2">OpenRouter, Inc.</td>
                      <td className="border border-gray-200 p-2">Vermittlung der Sprachmodell-Anfragen</td>
                      <td className="border border-gray-200 p-2">USA</td>
                      <td className="border border-gray-200 p-2">Standardvertragsklauseln, Art. 46 Abs. 2 lit. c DSGVO</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-200 p-2">Anthropic PBC</td>
                      <td className="border border-gray-200 p-2">Sprachmodell für Analyse und Textvorschläge</td>
                      <td className="border border-gray-200 p-2">USA</td>
                      <td className="border border-gray-200 p-2">Standardvertragsklauseln, Art. 46 Abs. 2 lit. c DSGVO</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-200 p-2">OpenAI, L.L.C.</td>
                      <td className="border border-gray-200 p-2">Sprachmodell für Analyse und Textvorschläge</td>
                      <td className="border border-gray-200 p-2">USA</td>
                      <td className="border border-gray-200 p-2">Standardvertragsklauseln, Art. 46 Abs. 2 lit. c DSGVO</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="mt-3">
                An die Sprachmodelle werden ausschließlich Inhalte der geprüften Website und die für Rechtstexte eingegebenen Angaben übermittelt. Einwilligungsprotokolle, Zugangsdaten und Zahlungsdaten werden nicht übermittelt. Die Zahlungsabwicklung für den Hauptvertrag ist keine Auftragsverarbeitung für den Verantwortlichen und deshalb hier nicht aufgeführt; sie steht in der <Link href="/datenschutz" className="text-akzent-700 underline">Datenschutzerklärung</Link>.
              </p>
            </section>

            <section className="border-t border-gray-200 pt-6">
              <p className="text-gray-500">
                Fragen zu diesem Vertrag: <a href={`mailto:${ANBIETER.datenschutzEmail}`} className="text-akzent-700 underline">{ANBIETER.datenschutzEmail}</a>
              </p>
            </section>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
