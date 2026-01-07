'use client';

import React from 'react';
import { Shield, Cookie, Database, Globe, Lock, FileText, Mail } from 'lucide-react';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-900 via-zinc-800 to-zinc-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-blue-500/20 rounded-xl">
              <Shield className="w-8 h-8 text-blue-400" />
            </div>
            <h1 className="text-4xl font-bold text-white">Datenschutzerklärung</h1>
          </div>
          <p className="text-zinc-400 text-lg">
            Wir nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Hier erfahren Sie, welche Daten wir erheben, wie wir sie verwenden und welche Rechte Sie haben.
          </p>
          <p className="text-zinc-500 text-sm mt-2">
            Stand: 23. November 2025 | Version 1.0
          </p>
        </div>

        {/* Content Sections */}
        <div className="space-y-8">
          {/* Section 1: Verantwortlicher */}
          <section className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="w-6 h-6 text-purple-400" />
              <h2 className="text-2xl font-bold text-white">1. Verantwortlicher</h2>
            </div>
            <div className="text-zinc-300 space-y-2">
              <p><strong className="text-white">Complyo.tech</strong></p>
              <p>[Adresse wird ergänzt]</p>
              <p>E-Mail: <a href="mailto:contact@complyo.tech" className="text-blue-400 hover:text-blue-300">contact@complyo.tech</a></p>
              <p className="text-sm text-zinc-500 mt-4">
                Datenschutz-Anfragen: <a href="mailto:privacy@complyo.tech" className="text-blue-400 hover:text-blue-300">privacy@complyo.tech</a>
              </p>
            </div>
          </section>

          {/* Section 2: Gespeicherte Daten */}
          <section className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Database className="w-6 h-6 text-green-400" />
              <h2 className="text-2xl font-bold text-white">2. Welche Daten werden gespeichert?</h2>
            </div>
            
            <div className="space-y-6">
              {/* Account-Daten */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Account-Daten</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-zinc-300">
                    <thead className="bg-zinc-800/50 text-white">
                      <tr>
                        <th className="text-left p-3">Datentyp</th>
                        <th className="text-left p-3">Zweck</th>
                        <th className="text-left p-3">Speicherdauer</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-700">
                      <tr>
                        <td className="p-3">E-Mail-Adresse</td>
                        <td className="p-3">Login, Account-Identifikation</td>
                        <td className="p-3">Bis Account-Löschung</td>
                      </tr>
                      <tr>
                        <td className="p-3">Passwort (gehasht)</td>
                        <td className="p-3">Authentifizierung</td>
                        <td className="p-3">Bis Account-Löschung</td>
                      </tr>
                      <tr>
                        <td className="p-3">Name</td>
                        <td className="p-3">Personalisierung</td>
                        <td className="p-3">Bis Account-Löschung</td>
                      </tr>
                      <tr>
                        <td className="p-3">Plan-Typ</td>
                        <td className="p-3">Feature-Zugriff</td>
                        <td className="p-3">Bis Account-Löschung</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Scan-Daten */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Website-Scan-Daten</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-zinc-300">
                    <thead className="bg-zinc-800/50 text-white">
                      <tr>
                        <th className="text-left p-3">Datentyp</th>
                        <th className="text-left p-3">Zweck</th>
                        <th className="text-left p-3">Speicherdauer</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-700">
                      <tr>
                        <td className="p-3">Gescannte URL/Domain</td>
                        <td className="p-3">Compliance-Analyse</td>
                        <td className="p-3">90 Tage</td>
                      </tr>
                      <tr>
                        <td className="p-3">Scan-Ergebnisse</td>
                        <td className="p-3">Service-Bereitstellung</td>
                        <td className="p-3">90 Tage</td>
                      </tr>
                      <tr>
                        <td className="p-3">Compliance-Score</td>
                        <td className="p-3">Übersicht & Verlauf</td>
                        <td className="p-3">90 Tage</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Cookies */}
          <section className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Cookie className="w-6 h-6 text-orange-400" />
              <h2 className="text-2xl font-bold text-white">3. Cookies & Lokale Speicherung</h2>
            </div>
            
            <div className="space-y-6">
              {/* Notwendige Cookies */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Notwendige Cookies</h3>
                <p className="text-zinc-400 text-sm mb-3">
                  Diese Cookies sind für die Funktionsfähigkeit der Plattform erforderlich.
                </p>
                <div className="space-y-3">
                  <div className="bg-zinc-800/30 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-mono text-blue-400">access_token</span>
                      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Notwendig</span>
                    </div>
                    <p className="text-sm text-zinc-400">
                      <strong>Zweck:</strong> Authentifizierung<br />
                      <strong>Speicherdauer:</strong> 24 Stunden<br />
                      <strong>Typ:</strong> HTTP-Only Cookie
                    </p>
                  </div>
                  <div className="bg-zinc-800/30 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-mono text-blue-400">refresh_token</span>
                      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Notwendig</span>
                    </div>
                    <p className="text-sm text-zinc-400">
                      <strong>Zweck:</strong> Token-Erneuerung<br />
                      <strong>Speicherdauer:</strong> 7 Tage<br />
                      <strong>Typ:</strong> HTTP-Only Cookie
                    </p>
                  </div>
                </div>
              </div>

              {/* Funktionale Cookies */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Funktionale Cookies (localStorage)</h3>
                <p className="text-zinc-400 text-sm mb-3">
                  Diese Cookies speichern Ihre Präferenzen und sind nicht essentiell.
                </p>
                <div className="space-y-3">
                  <div className="bg-zinc-800/30 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-mono text-purple-400">user_preferences</span>
                      <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">Funktional</span>
                    </div>
                    <p className="text-sm text-zinc-400">
                      <strong>Zweck:</strong> UI-Einstellungen (Theme, Sprache)<br />
                      <strong>Speicherdauer:</strong> Unbegrenzt<br />
                      <strong>Typ:</strong> localStorage
                    </p>
                  </div>
                  <div className="bg-zinc-800/30 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-mono text-purple-400">cookie_consent</span>
                      <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">Funktional</span>
                    </div>
                    <p className="text-sm text-zinc-400">
                      <strong>Zweck:</strong> Speichert Ihre Cookie-Einwilligung<br />
                      <strong>Speicherdauer:</strong> 1 Jahr<br />
                      <strong>Typ:</strong> localStorage
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Section 4: API-Aufrufe an Dritte */}
          <section className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Globe className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-bold text-white">4. Weitergabe an Dritte</h2>
            </div>
            
            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 bg-blue-500/10 rounded-r-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">eRecht24 API</h3>
                <p className="text-zinc-400 text-sm mb-2">
                  <strong>Zweck:</strong> Generierung rechtssicherer Texte (Impressum, Datenschutzerklärung)
                </p>
                <p className="text-zinc-400 text-sm mb-2">
                  <strong>Übermittelte Daten:</strong> Domain/URL, Firmendaten (nur wenn Sie diese eingeben)
                </p>
                <p className="text-zinc-400 text-sm">
                  <strong>Datenschutz:</strong> <a href="https://www.e-recht24.de/datenschutzerklaerung/" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">https://www.e-recht24.de/datenschutzerklaerung/</a>
                </p>
              </div>

              <div className="border-l-4 border-purple-500 bg-purple-500/10 rounded-r-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">Stripe Payment API</h3>
                <p className="text-zinc-400 text-sm mb-2">
                  <strong>Zweck:</strong> Zahlungsabwicklung und Abo-Management
                </p>
                <p className="text-zinc-400 text-sm mb-2">
                  <strong>Übermittelte Daten:</strong> E-Mail, Name, Zahlungsinformationen (direkt an Stripe)
                </p>
                <p className="text-zinc-400 text-sm">
                  <strong>Datenschutz:</strong> <a href="https://stripe.com/de/privacy" target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300">https://stripe.com/de/privacy</a>
                </p>
              </div>

              <div className="border-l-4 border-green-500 bg-green-500/10 rounded-r-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">OpenAI API (GPT-4)</h3>
                <p className="text-zinc-400 text-sm mb-2">
                  <strong>Zweck:</strong> AI-Fix-Generierung, Compliance-Analyse
                </p>
                <p className="text-zinc-400 text-sm mb-2">
                  <strong>Übermittelte Daten:</strong> Website-Inhalte (HTML, CSS), Issue-Beschreibungen
                </p>
                <p className="text-zinc-400 text-sm mb-2">
                  <strong>Wichtig:</strong> KEINE persönlichen Nutzerdaten werden an OpenAI übermittelt
                </p>
                <p className="text-zinc-400 text-sm">
                  <strong>Datenschutz:</strong> <a href="https://openai.com/policies/privacy-policy" target="_blank" rel="noopener noreferrer" className="text-green-400 hover:text-green-300">https://openai.com/policies/privacy-policy</a>
                </p>
              </div>
            </div>
          </section>

          {/* Section 5: Betroffenenrechte */}
          <section className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Lock className="w-6 h-6 text-yellow-400" />
              <h2 className="text-2xl font-bold text-white">5. Ihre Rechte</h2>
            </div>
            
            <p className="text-zinc-400 mb-4">
              Sie haben jederzeit folgende Rechte bezüglich Ihrer personenbezogenen Daten:
            </p>
            
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 bg-zinc-800/30 rounded-lg">
                <span className="text-blue-400 font-bold">Art. 15 DSGVO</span>
                <span className="text-zinc-300">Auskunft über gespeicherte Daten</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-zinc-800/30 rounded-lg">
                <span className="text-blue-400 font-bold">Art. 16 DSGVO</span>
                <span className="text-zinc-300">Berichtigung unrichtiger Daten</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-zinc-800/30 rounded-lg">
                <span className="text-blue-400 font-bold">Art. 17 DSGVO</span>
                <span className="text-zinc-300">Löschung gespeicherter Daten ("Recht auf Vergessenwerden")</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-zinc-800/30 rounded-lg">
                <span className="text-blue-400 font-bold">Art. 18 DSGVO</span>
                <span className="text-zinc-300">Einschränkung der Verarbeitung</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-zinc-800/30 rounded-lg">
                <span className="text-blue-400 font-bold">Art. 20 DSGVO</span>
                <span className="text-zinc-300">Datenportabilität (Export als JSON/CSV)</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-zinc-800/30 rounded-lg">
                <span className="text-blue-400 font-bold">Art. 21 DSGVO</span>
                <span className="text-zinc-300">Widerspruch gegen Datenverarbeitung</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-zinc-800/30 rounded-lg">
                <span className="text-blue-400 font-bold">Art. 77 DSGVO</span>
                <span className="text-zinc-300">Beschwerde bei Aufsichtsbehörde</span>
              </div>
            </div>
          </section>

          {/* Section 6: Datensicherheit */}
          <section className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-6 h-6 text-red-400" />
              <h2 className="text-2xl font-bold text-white">6. Datensicherheit</h2>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-zinc-800/30 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-2">🔒 Verschlüsselung</h3>
                <p className="text-zinc-400 text-sm">TLS 1.3 für alle Verbindungen</p>
              </div>
              <div className="bg-zinc-800/30 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-2">🔑 Passwort-Schutz</h3>
                <p className="text-zinc-400 text-sm">bcrypt Hashing mit Salt</p>
              </div>
              <div className="bg-zinc-800/30 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-2">🗄️ Datenbank</h3>
                <p className="text-zinc-400 text-sm">PostgreSQL mit Row-Level Security</p>
              </div>
              <div className="bg-zinc-800/30 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-2">💾 Backups</h3>
                <p className="text-zinc-400 text-sm">Tägliche verschlüsselte Backups</p>
              </div>
              <div className="bg-zinc-800/30 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-2">🌍 Server-Standort</h3>
                <p className="text-zinc-400 text-sm">EU-Rechenzentren (Deutschland)</p>
              </div>
              <div className="bg-zinc-800/30 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-2">🔐 Zugriffskontrolle</h3>
                <p className="text-zinc-400 text-sm">2FA für Admin-Zugriffe</p>
              </div>
            </div>
          </section>

          {/* Contact Section */}
          <section className="glass-card rounded-2xl p-6 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
            <div className="flex items-center gap-3 mb-4">
              <Mail className="w-6 h-6 text-blue-400" />
              <h2 className="text-2xl font-bold text-white">Kontakt</h2>
            </div>
            
            <div className="space-y-2 text-zinc-300">
              <p>
                <strong className="text-white">Allgemeine Anfragen:</strong>{' '}
                <a href="mailto:contact@complyo.tech" className="text-blue-400 hover:text-blue-300">contact@complyo.tech</a>
              </p>
              <p>
                <strong className="text-white">Datenschutz-Anfragen:</strong>{' '}
                <a href="mailto:privacy@complyo.tech" className="text-blue-400 hover:text-blue-300">privacy@complyo.tech</a>
              </p>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-zinc-700 text-center text-zinc-500 text-sm">
          <p>Diese Datenschutzerklärung wurde zuletzt am 23. November 2025 aktualisiert.</p>
          <p className="mt-2">
            <a href="/dashboard" className="text-blue-400 hover:text-blue-300">← Zurück zum Dashboard</a>
          </p>
        </div>
      </div>
    </div>
  );
}

