'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, FileText } from 'lucide-react';

export default function AGBPage() {
  return (
    <main id="inhalt" tabIndex={-1} className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Zurück zur Startseite
          </Link>

          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="w-8 h-8 text-blue-600" />
              <h1 className="text-4xl font-bold text-gray-900">Allgemeine Geschäftsbedingungen</h1>
            </div>
            <p className="text-gray-600">Stand: 1. September 2026</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Geltungsbereich</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Diese Allgemeinen Geschäftsbedingungen (nachfolgend "AGB") gelten für alle Verträge zwischen der Complyo GmbH, Musterstraße 123, 10115 Berlin (nachfolgend "Anbieter" oder "wir") und ihren Kunden (nachfolgend "Kunde" oder "Sie") über die Nutzung der von uns angebotenen Software-as-a-Service (SaaS) Leistungen zur Website-Compliance, Barrierefreiheit und Datenschutz.
                </p>
                <p>
                  (2) Abweichende, entgegenstehende oder ergänzende Allgemeine Geschäftsbedingungen des Kunden werden nicht Vertragsbestandteil, es sei denn, ihrer Geltung wird ausdrücklich schriftlich zugestimmt.
                </p>
                <p>
                  (3) Unsere Angebote richten sich ausschließlich an Unternehmer im Sinne des § 14 BGB, an
                  juristische Personen des öffentlichen Rechts und an öffentlich-rechtliche Sondervermögen. Ein
                  Vertragsschluss mit Verbrauchern im Sinne des § 13 BGB ist ausgeschlossen. Mit der Bestellung
                  bestätigt der Kunde, in Ausübung seiner gewerblichen oder selbständigen beruflichen Tätigkeit zu
                  handeln.
                </p>
                <p>
                  (4) Da ausschließlich Verträge mit Unternehmern geschlossen werden, bestehen kein
                  Verbraucherwiderrufsrecht nach §§ 312g, 355 BGB und keine Pflicht zur Bereitstellung eines
                  Kündigungsbuttons nach § 312k BGB. Die Kündigung richtet sich nach Ziffer 7 dieser AGB.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Vertragsgegenstand und Leistungen</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Anbieter stellt dem Kunden eine cloudbasierte Software-Plattform zur Verfügung, die folgende Leistungen umfasst:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Automatische Website-Scans zur Erkennung von Compliance-Problemen</li>
                  <li>KI-gestützte Analyse und Behebung von Barrierefreiheitsproblemen</li>
                  <li>Cookie-Compliance und DSGVO-Konformitätsprüfung</li>
                  <li>Automatische Fix-Generierung für erkannte Probleme</li>
                  <li>Monitoring und kontinuierliche Überwachung der Website-Compliance</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Vertragsschluss</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Die Darstellung der Leistungen auf unserer Website stellt kein rechtlich bindendes Angebot dar, sondern eine unverbindliche Aufforderung zur Abgabe eines Angebots.
                </p>
                <p>
                  (2) Durch Anklicken des Buttons "Jetzt starten" gibt der Kunde ein verbindliches Angebot auf Abschluss eines Nutzungsvertrages ab.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Preise und Zahlungsbedingungen</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Die Preise für die Nutzung der Plattform richten sich nach der jeweils gültigen Preisliste auf unserer Website zum Zeitpunkt des Vertragsschlusses.
                </p>
                <p>
                  (2) Alle Preise verstehen sich in Euro und enthalten die gesetzliche Mehrwertsteuer.
                </p>
                <p>
                  (3) Die Zahlung erfolgt im Voraus für den jeweils gebuchten Abrechnungszeitraum (monatlich oder jährlich).
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Nutzungsrechte und -pflichten</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Anbieter räumt dem Kunden das nicht-exklusive, nicht übertragbare, zeitlich auf die Vertragslaufzeit beschränkte Recht ein, die Plattform für die eigenen geschäftlichen Zwecke zu nutzen.
                </p>
                <p>
                  (2) Der Kunde verpflichtet sich, die Zugangsdaten geheim zu halten und Dritten keinen Zugang zu gewähren.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Datenschutz</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Anbieter verarbeitet personenbezogene Daten des Kunden im Rahmen der Vertragsdurchführung gemäß den Bestimmungen der Datenschutz-Grundverordnung (DSGVO).
                </p>
                <p>
                  (2) Die Datenerhebung und -verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO zur Erfüllung des Vertrages.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Kündigung</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Vertrag kann von beiden Seiten mit einer Frist von 30 Tagen zum Ende eines Abrechnungszeitraums gekündigt werden.
                </p>
                <p>
                  (2) Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt unberührt.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Mitwirkungspflichten des Kunden</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Kunde prüft von complyo erzeugte Texte, Befunde und Änderungsvorschläge vor
                  deren Veröffentlichung oder Übernahme auf inhaltliche Richtigkeit und Vollständigkeit.
                  Die Freigabe und die Veröffentlichung erfolgen durch den Kunden.
                </p>
                <p>
                  (2) Der Kunde stellt sicher, dass er berechtigt ist, die von ihm angegebenen Websites
                  prüfen und ändern zu lassen.
                </p>
                <p>
                  (3) Der Kunde hält die Angaben aktuell, auf deren Grundlage complyo Texte erzeugt,
                  insbesondere Unternehmens- und Kontaktdaten sowie die eingesetzten Dienste Dritter.
                </p>
                <p>
                  (4) Unterlässt der Kunde die Prüfung nach Absatz 1, ist ein hierauf beruhendes
                  Mitverschulden nach § 254 BGB zu berücksichtigen.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Beschaffenheit der Leistung, keine Rechtsberatung</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) complyo ist ein technisches Prüf- und Hinweissystem. Es misst Websites gegen
                  technisch prüfbare Kriterien, dokumentiert das Ergebnis und stellt Vorlagen und
                  Änderungsvorschläge bereit.
                </p>
                <p>
                  (2) complyo erbringt keine Rechtsdienstleistung im Sinne des § 2 RDG. Befunde,
                  Berichte und generierte Texte sind Informationen und Vorlagen auf Grundlage der
                  Angaben des Kunden. Sie ersetzen keine individuelle rechtliche Beratung.
                </p>
                <p>
                  (3) complyo schuldet keinen bestimmten rechtlichen Zustand der Website des Kunden.
                  Insbesondere werden Abmahnsicherheit, Bußgeldfreiheit oder die vollständige Erfüllung
                  gesetzlicher Anforderungen weder geschuldet noch zugesichert.
                </p>
                <p>
                  (4) Automatisierte Prüfungen können nicht alle Anforderungen abdecken. Im Bereich der
                  Barrierefreiheit erfassen automatisierte Verfahren branchenüblich nur einen Teil der
                  Kriterien der WCAG. complyo weist die nicht automatisiert prüfbaren Kriterien
                  gesondert als manuell zu prüfen aus.
                </p>
                <p>
                  (5) Eine Garantie im Rechtssinne übernimmt complyo nur, wenn sie ausdrücklich und in
                  Textform als Garantie bezeichnet ist.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Gewährleistung</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) complyo stellt die Software für die Dauer des Vertrages in dem Zustand bereit, der
                  sich aus der jeweils gültigen Leistungsbeschreibung ergibt. Eine ununterbrochene
                  Verfügbarkeit wird nicht geschuldet.
                </p>
                <p>
                  (2) Die verschuldensunabhängige Haftung für Mängel, die bereits bei Vertragsschluss
                  vorhanden waren, nach § 536a Absatz 1 Alternative 1 BGB ist ausgeschlossen.
                </p>
                <p>
                  (3) Der Kunde zeigt Mängel unverzüglich in Textform an und beschreibt sie so, dass sie
                  nachvollzogen werden können.
                </p>
              </div>
            </section>

            <section id="haftung">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Haftung</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) complyo haftet unbeschränkt für Vorsatz und grobe Fahrlässigkeit, für Schäden aus
                  der Verletzung des Lebens, des Körpers oder der Gesundheit, im Umfang einer
                  übernommenen Garantie sowie nach dem Produkthaftungsgesetz.
                </p>
                <p>
                  (2) Bei leicht fahrlässiger Verletzung einer Pflicht, deren Erfüllung die
                  ordnungsgemäße Durchführung des Vertrages überhaupt erst ermöglicht und auf deren
                  Einhaltung der Kunde regelmäßig vertrauen darf, haftet complyo begrenzt auf den bei
                  Vertragsschluss vorhersehbaren, vertragstypischen Schaden.
                </p>
                <p>
                  (3) Der vertragstypische Schaden nach Absatz 2 ist begrenzt auf das Entgelt, das der
                  Kunde in den zwölf Monaten vor dem schadenauslösenden Ereignis für die betroffene
                  Leistung gezahlt hat, mindestens jedoch auf 1.000 Euro. Bußgelder, Verwarnungsgelder
                  und Abmahnkosten, die gegen den Kunden festgesetzt oder geltend gemacht werden,
                  unterfallen dieser Begrenzung.
                </p>
                <p>
                  (4) Im Übrigen ist die Haftung bei leichter Fahrlässigkeit ausgeschlossen,
                  insbesondere für entgangenen Gewinn, ausgebliebene Einsparungen sowie mittelbare
                  Schäden und Folgeschäden.
                </p>
                <p>
                  (5) Die Beschränkungen dieser Ziffer gelten auch zugunsten der Mitarbeiter,
                  Erfüllungsgehilfen und gesetzlichen Vertreter von complyo.
                </p>
                <p>
                  (6) Mit den vorstehenden Regelungen ist keine Änderung der Beweislast zum Nachteil des
                  Kunden verbunden.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Verjährung</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  Ansprüche des Kunden gegen complyo verjähren in zwölf Monaten ab dem gesetzlichen
                  Verjährungsbeginn. Dies gilt nicht für Ansprüche aus Ziffer 11 Absatz 1; für diese
                  gelten die gesetzlichen Verjährungsfristen.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Schlussbestimmungen</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts.
                </p>
                <p>
                  (2) Ausschließlicher Gerichtsstand für alle Streitigkeiten aus und im Zusammenhang mit
                  diesem Vertrag ist Berlin, sofern der Kunde Kaufmann, juristische Person des
                  öffentlichen Rechts oder öffentlich-rechtliches Sondervermögen ist.
                </p>
                <p>
                  (3) Änderungen und Ergänzungen dieses Vertrages bedürfen der Textform. Das gilt auch
                  für die Aufhebung dieser Klausel.
                </p>
                <p>
                  (4) Sollte eine Bestimmung dieser AGB unwirksam sein, bleibt die Wirksamkeit der
                  übrigen Bestimmungen unberührt.
                </p>
              </div>
            </section>
          </div>

          <div className="mt-8 bg-blue-50 rounded-xl p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Fragen zu den AGB?</h3>
            <p className="text-gray-700 text-sm">
              <strong>E-Mail:</strong>{' '}
              <a href="mailto:info@complyo.de" className="text-blue-600 underline">
                info@complyo.de
              </a>
            </p>
          </div>

          <div className="mt-8 text-center text-sm text-gray-600">
            <div className="flex justify-center gap-6">
              <Link href="/impressum" className="hover:text-blue-600 transition-colors">
                Impressum
              </Link>
              <Link href="/datenschutz" className="hover:text-blue-600 transition-colors">
                Datenschutz
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
