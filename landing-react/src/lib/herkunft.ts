'use client';
import { useEffect, useState } from 'react';

/**
 * Herkunft eines Besuchers: die utm-Parameter aus der Adresszeile.
 *
 * Die Kanal-Kurzlinks (/li, /tt, /scan, siehe nginx) haengen utm_source,
 * utm_medium, utm_campaign und optional utm_content an. Die Warteliste
 * speichert diese Werte seit September. Der Kaufweg tat das bis zum
 * 28.09.2026 nicht: der Knopf "Pro buchen" fuehrte nach app.complyo.de ohne
 * jede Herkunft, und ein Kauf liess sich hinterher keinem Kanal zuordnen.
 * Die Entscheidungsregel nach Woche 45 ("Kaeufe je Kanal") war damit nicht
 * messbar.
 *
 * Deshalb reisen die Parameter mit auf die Registrierungsseite. Nur eine
 * feste Liste, nur harmlose Zeichen: was hier steht, landet spaeter in
 * Stripe-Metadaten und in der Datenbank.
 */
const SCHLUESSEL = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'] as const;
const MUSTER = /^[A-Za-z0-9_.:-]{1,120}$/;

export function herkunftAusSuche(search: string): URLSearchParams {
  const eingang = new URLSearchParams(search);
  const ausgang = new URLSearchParams();
  for (const k of SCHLUESSEL) {
    const v = eingang.get(k);
    if (v && MUSTER.test(v)) ausgang.set(k, v);
  }
  // Kurzform ?c=P01 wie bei den Kurzlinks: wird zu utm_content, wenn das
  // nicht schon gesetzt ist.
  const c = eingang.get('c');
  if (c && !ausgang.has('utm_content') && MUSTER.test(c)) ausgang.set('utm_content', c);
  return ausgang;
}

export function mitHerkunft(href: string, herkunft: URLSearchParams): string {
  const s = herkunft.toString();
  if (!s) return href;
  return href + (href.includes('?') ? '&' : '?') + s;
}

/** Liest die Herkunft nach dem ersten Rendern; auf dem Server ist sie leer. */
export function useHerkunft(): URLSearchParams {
  const [herkunft, setHerkunft] = useState(() => new URLSearchParams());
  useEffect(() => {
    setHerkunft(herkunftAusSuche(window.location.search));
  }, []);
  return herkunft;
}
