'use client';
import React, { useState, useEffect, useRef } from 'react';
import { CheckCircle2, AlertCircle, Loader2, Lock } from 'lucide-react';
import { leadsApi } from '@/lib/api';
import type { WaitlistJoinRequest } from '@/types/api';

type FormState = 'idle' | 'loading' | 'success' | 'already_registered' | 'error';

const TURNSTILE_SITEKEY = process.env.NEXT_PUBLIC_TURNSTILE_SITEKEY || '';

// Der Server verwirft alles, was schneller als vier Sekunden ausgefuellt wurde
// (lead_routes._MIN_FILL_SECONDS). Autofill unterschreitet das muehelos, und
// der Eintrag waere weg, ohne dass es jemand merkt. Statt die Serverabwehr zu
// lockern, wartet das Formular die Differenz ab. Echte Bots posten ohne
// form_ts direkt auf den Endpunkt und fallen weiterhin heraus.
const MIN_ABSENDEZEIT_MS = 4600;

declare global {
  interface Window {
    turnstile?: {
      render: (el: HTMLElement, opts: Record<string, unknown>) => string;
      reset: (id?: string) => void;
    };
  }
}

/** Liest die Kampagnenparameter aus der Adresszeile. */
function herkunftAuslesen(kampagne: string): Partial<WaitlistJoinRequest> {
  if (typeof window === 'undefined') return { campaign: kampagne };
  const p = new URLSearchParams(window.location.search);
  return {
    campaign: kampagne,
    utm_source: p.get('utm_source') || undefined,
    utm_medium: p.get('utm_medium') || undefined,
    utm_campaign: p.get('utm_campaign') || undefined,
    utm_content: p.get('utm_content') || undefined,
    utm_term: p.get('utm_term') || undefined,
    landing_path: window.location.pathname,
  };
}

export default function WartelistenFormular({
  kampagne,
  knopfText = 'Platz sichern',
  id,
}: {
  kampagne: string;
  knopfText?: string;
  id?: string;
}) {
  const [email, setEmail] = useState('');
  const [consent, setConsent] = useState(false);
  const [honeypot, setHoneypot] = useState('');
  const [formState, setFormState] = useState<FormState>('idle');
  const [consentError, setConsentError] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState('');
  const [turnstileError, setTurnstileError] = useState(false);

  const openedAt = useRef<number>(0);
  const turnstileBox = useRef<HTMLDivElement | null>(null);
  const turnstileRendered = useRef(false);

  useEffect(() => {
    openedAt.current = Date.now();
  }, []);

  useEffect(() => {
    if (!TURNSTILE_SITEKEY || formState === 'success' || formState === 'already_registered') return;

    const scriptId = 'cf-turnstile-script';
    if (!document.getElementById(scriptId)) {
      const s = document.createElement('script');
      s.id = scriptId;
      s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
      s.async = true;
      s.defer = true;
      document.head.appendChild(s);
    }

    let cancelled = false;
    const tryRender = () => {
      if (cancelled || turnstileRendered.current) return;
      if (!window.turnstile || !turnstileBox.current) {
        window.setTimeout(tryRender, 100);
        return;
      }
      turnstileRendered.current = true;
      window.turnstile.render(turnstileBox.current, {
        sitekey: TURNSTILE_SITEKEY,
        callback: (token: string) => { setTurnstileToken(token); setTurnstileError(false); },
        'expired-callback': () => setTurnstileToken(''),
        'error-callback': () => setTurnstileToken(''),
      });
    };
    tryRender();

    return () => { cancelled = true; };
  }, [formState]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consent) {
      setConsentError(true);
      return;
    }
    setConsentError(false);

    if (TURNSTILE_SITEKEY && !turnstileToken) {
      setTurnstileError(true);
      return;
    }

    setFormState('loading');

    const offen = Date.now() - (openedAt.current || Date.now());
    if (offen < MIN_ABSENDEZEIT_MS) {
      await new Promise((r) => setTimeout(r, MIN_ABSENDEZEIT_MS - offen));
    }

    try {
      const result = await leadsApi.joinWaitlist({
        email,
        consent,
        website: honeypot || undefined,
        source: 'landing',
        form_ts: openedAt.current || undefined,
        turnstile_token: turnstileToken || undefined,
        ...herkunftAuslesen(kampagne),
      });

      // Der Endpunkt antwortet bei ausgeloester Bot-Abwehr mit 204 und leerem
      // Rumpf. Ohne diese Pruefung liefe das als Erfolg durch: der Besucher
      // sieht eine Bestaetigung und wartet auf eine Mail, die nie kommt,
      // waehrend der Klick bereits bezahlt ist. Lieber eine ehrliche
      // Fehlermeldung und ein zweiter Versuch.
      if (!result || !result.status) {
        setFormState('error');
        return;
      }

      setFormState(result.status === 'already_registered' ? 'already_registered' : 'success');
    } catch {
      setFormState('error');
    }
  };

  if (formState === 'success' || formState === 'already_registered') {
    const schonDrin = formState === 'already_registered';
    return (
      <div
        id={id}
        className="bg-green-50 border border-green-200 rounded-2xl p-6 flex items-start gap-3"
        role="status"
      >
        <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <p className="font-semibold text-green-900">
            {schonDrin ? 'Diese Adresse steht schon auf der Liste.' : 'Fast geschafft – bitte E-Mail bestätigen.'}
          </p>
          <p className="text-sm text-green-800 mt-1 leading-relaxed">
            {schonDrin
              ? 'Wir melden uns unter dieser Adresse, sobald es losgeht. Du musst nichts weiter tun.'
              : 'Wir haben dir eine Mail geschickt. Der Platz ist erst mit dem Klick darin reserviert – ohne Bestätigung dürfen wir dich nicht anschreiben.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <form id={id} onSubmit={handleSubmit} className="space-y-3" noValidate>
      {/* Honeypot: fuer Menschen unsichtbar, fuer Formularausfueller verlockend. */}
      <div className="absolute left-[-9999px]" aria-hidden="true">
        <label htmlFor={`website-${kampagne}`}>Website</label>
        <input
          id={`website-${kampagne}`}
          type="text"
          tabIndex={-1}
          autoComplete="off"
          value={honeypot}
          onChange={(e) => setHoneypot(e.target.value)}
        />
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <label htmlFor={`email-${kampagne}`} className="sr-only">
            E-Mail-Adresse
          </label>
          <input
            id={`email-${kampagne}`}
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="deine@firma.de"
            className="w-full px-4 py-3.5 rounded-xl border border-gray-300 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </div>
        <button
          type="submit"
          disabled={formState === 'loading'}
          className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed text-white font-semibold px-6 py-3.5 rounded-xl transition-colors whitespace-nowrap"
        >
          {formState === 'loading' ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
              Wird gesendet…
            </>
          ) : (
            knopfText
          )}
        </button>
      </div>

      {TURNSTILE_SITEKEY && <div ref={turnstileBox} className="pt-1" />}
      {turnstileError && (
        <p className="text-sm text-red-600 flex items-center gap-1.5">
          <AlertCircle className="w-4 h-4" aria-hidden="true" />
          Bitte bestätige kurz, dass du kein Bot bist.
        </p>
      )}

      <label className="flex items-start gap-2.5 text-sm text-gray-600 cursor-pointer">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => { setConsent(e.target.checked); setConsentError(false); }}
          className="mt-0.5 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600"
        />
        <span>
          Ich möchte zum Start benachrichtigt werden und bin damit einverstanden, dass complyo
          meine E-Mail-Adresse dafür speichert. Widerruf jederzeit über den Abmeldelink in jeder
          Mail. Näheres in der{' '}
          <a href="/datenschutz" className="text-blue-600 underline hover:text-blue-700">
            Datenschutzerklärung
          </a>
          .
        </span>
      </label>
      {consentError && (
        <p className="text-sm text-red-600 flex items-center gap-1.5" role="alert">
          <AlertCircle className="w-4 h-4" aria-hidden="true" />
          Ohne diese Einwilligung dürfen wir dir nicht schreiben.
        </p>
      )}

      {formState === 'error' && (
        <p className="text-sm text-red-600 flex items-center gap-1.5" role="alert">
          <AlertCircle className="w-4 h-4" aria-hidden="true" />
          Das hat nicht geklappt – deine Adresse wurde nicht gespeichert. Bitte versuch es noch einmal.
        </p>
      )}

      <p className="text-xs text-gray-500 flex items-center gap-1.5">
        <Lock className="w-3.5 h-3.5" aria-hidden="true" />
        Kein Newsletter, keine Weitergabe an Dritte. Nur die Nachricht zum Start.
      </p>
    </form>
  );
}
