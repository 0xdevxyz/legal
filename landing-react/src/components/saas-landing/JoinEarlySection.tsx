'use client';
import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertCircle, Loader2, Lock, Mail, User, Phone } from 'lucide-react';
import { leadsApi } from '@/lib/api';

type FormState = 'idle' | 'loading' | 'success' | 'already_registered' | 'error';

export default function JoinEarlySection() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [consent, setConsent] = useState(false);
  const [honeypot, setHoneypot] = useState('');
  const [formState, setFormState] = useState<FormState>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [consentError, setConsentError] = useState(false);
  const [confirmedBanner, setConfirmedBanner] = useState<boolean | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const confirmed = params.get('confirmed');
      if (confirmed === '1') setConfirmedBanner(true);
      if (confirmed === '0') setConfirmedBanner(false);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consent) {
      setConsentError(true);
      return;
    }
    setConsentError(false);
    setFormState('loading');
    setErrorMsg('');

    const source =
      typeof window !== 'undefined'
        ? window.location.hostname
        : 'early-access';

    try {
      const result = await leadsApi.joinWaitlist({
        email,
        name: name || undefined,
        phone: phone || undefined,
        consent,
        website: honeypot || undefined,
        source,
      });

      if (result.status === 'already_registered') {
        setFormState('already_registered');
      } else {
        setFormState('success');
      }
    } catch {
      setFormState('error');
      setErrorMsg('Ein Fehler ist aufgetreten. Bitte versuche es erneut.');
    }
  };

  return (
    <section id="waitlist" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {confirmedBanner === true && (
          <div className="max-w-lg mx-auto mb-10 bg-green-50 border border-green-200 rounded-2xl p-5 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-green-800">E-Mail bestätigt – willkommen an Bord!</p>
              <p className="text-sm text-green-700 mt-0.5">Du stehst jetzt auf der Early-Access-Liste. Wir melden uns, sobald Complyo startet.</p>
            </div>
          </div>
        )}

        {confirmedBanner === false && (
          <div className="max-w-lg mx-auto mb-10 bg-red-50 border border-red-200 rounded-2xl p-5 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-800">Bestätigungs-Link ungültig oder abgelaufen.</p>
              <p className="text-sm text-red-700 mt-0.5">Bitte melde dich erneut an, um einen neuen Link zu erhalten.</p>
            </div>
          </div>
        )}

        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-full px-4 py-1.5 mb-5">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Early Access</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-gray-900 mb-4">
            Sei einer der <span className="text-blue-600">Ersten</span>
          </h2>
          <p className="text-lg text-gray-500 max-w-xl mx-auto">
            Trage dich ein und erhalte als Erster Zugang zu Complyo – der KI-Compliance-Plattform für Websites.
          </p>
        </div>

        <div className="max-w-lg mx-auto">
          {formState === 'success' && (
            <div className="bg-green-50 border border-green-200 rounded-2xl p-8 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-green-900 mb-2">Danke!</h3>
              <p className="text-green-700">Wir haben dir eine Bestätigungsmail geschickt. Bitte bestätige deine E-Mail-Adresse, um deinen Platz zu sichern.</p>
            </div>
          )}

          {formState === 'already_registered' && (
            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-8 text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mail className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-blue-900 mb-2">Bereits angemeldet</h3>
              <p className="text-blue-700">Diese E-Mail steht bereits auf der Warteliste. Bitte prüfe dein Postfach für die Bestätigungsmail.</p>
            </div>
          )}

          {(formState === 'idle' || formState === 'loading' || formState === 'error') && (
            <form onSubmit={handleSubmit} className="bg-gray-50 border border-gray-200 rounded-2xl p-8 space-y-5" noValidate>
              <div>
                <label htmlFor="waitlist-email" className="block text-sm font-medium text-gray-700 mb-1.5">
                  E-Mail-Adresse <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    id="waitlist-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="deine@email.de"
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none text-sm transition-colors"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="waitlist-name" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Name <span className="text-gray-400 text-xs font-normal">(optional)</span>
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    id="waitlist-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Dein Name"
                    maxLength={120}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none text-sm transition-colors"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="waitlist-phone" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Telefon <span className="text-gray-400 text-xs font-normal">(optional)</span>
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    id="waitlist-phone"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+49 123 456789"
                    maxLength={40}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none text-sm transition-colors"
                  />
                </div>
              </div>

              <input
                type="text"
                name="website"
                value={honeypot}
                onChange={(e) => setHoneypot(e.target.value)}
                tabIndex={-1}
                aria-hidden="true"
                autoComplete="off"
                style={{ position: 'absolute', left: '-9999px', width: '1px', height: '1px', opacity: 0 }}
              />

              <div>
                <label className={`flex items-start gap-3 cursor-pointer group ${consentError ? 'text-red-600' : 'text-gray-600'}`}>
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={(e) => {
                      setConsent(e.target.checked);
                      if (e.target.checked) setConsentError(false);
                    }}
                    required
                    className="mt-0.5 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 flex-shrink-0"
                  />
                  <span className="text-sm leading-relaxed">
                    Ich willige ein, dass meine Daten zur Kontaktaufnahme und Information über Complyo verarbeitet werden. Mehr dazu in der{' '}
                    <a href="/datenschutz" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                      Datenschutzerklärung
                    </a>. <span className="text-red-500">*</span>
                  </span>
                </label>
                {consentError && (
                  <p className="text-xs text-red-600 mt-1.5 ml-7">Bitte stimme der Datenschutzerklärung zu.</p>
                )}
              </div>

              {formState === 'error' && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-3 flex items-center gap-2 text-sm text-red-700">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {errorMsg}
                </div>
              )}

              <button
                type="submit"
                disabled={formState === 'loading'}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-md shadow-blue-100"
              >
                {formState === 'loading' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Wird eingetragen…
                  </>
                ) : (
                  'Auf Warteliste setzen'
                )}
              </button>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2 text-xs text-gray-400">
                <span className="flex items-center gap-1"><Lock className="w-3 h-3" /> DSGVO-konform</span>
                <span className="hidden sm:block">·</span>
                <span>Kein Spam – nur Produkt-Updates</span>
                <span className="hidden sm:block">·</span>
                <span>Jederzeit abmeldbar</span>
              </div>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}
