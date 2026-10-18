'use client';
import React, { useEffect, useRef, useState } from 'react';
import { Pause, Play, Volume2, VolumeX } from 'lucide-react';

// Wortlaut der Erzaehlung der Fassung vom 18.09.2026 (sieben Bloecke; die Bloecke
// vier bis sechs sind echte Aufnahmen aus dem angemeldeten Backoffice, Kundendomains
// verdeckt; am Ende ein Abbinder mit Logo und Adresse). Aenderungen am Video muessen hier und in der VTT-Spur nachgezogen
// werden — sonst steht neben dem Video ein Text, der nicht dazu gehoert.
//
// Diese Komponente ist aus HeroSection herausgeloest, weil das Video seit dem
// 02.09.2026 an zwei Stellen steht: auf der Early-Access-Startseite und auf der
// Produktseite unter /produkt. Zwei Kopien haetten bedeutet, dass ein neues
// Video an einer Stelle nachgezogen wird und an der anderen ein Transkript
// stehen bleibt, das nicht mehr zum Ton passt.
export const TRANSKRIPT = [
  'Bäckermeister Kern mit zwölf Angestellten hält die Website für fertig. ' +
    'Das Recht wird es nie, vier Lücken bleiben unbemerkt.',
  'Sein Cookie-Banner hat keinen Knopf zum Ablehnen, und in der ' +
    'Datenschutzerklärung fehlt das Programm, das seine Besucher zählt und auswertet.',
  'Ein Foto bleibt für Vorleseprogramme stumm, im Impressum fehlt der Vorname. ' +
    'Seine Agentur prüft dreißig Websites von Hand.',
  'complyo prüft Barrierefreiheit, Datenschutz, Cookies und Pflichttexte, ' +
    'jeder Befund mit Rechtsgrundlage.',
  'Für viele Befunde schlägt complyo Reparaturen vor und misst deren Wirkung. ' +
    'Freigeben muss ein Mensch, nicht die Maschine.',
  'Täglich prüft complyo Ihre Website neu und die Rechtsquellen. Neue Pflichten ' +
    'der Branche meldet es mit Frist und Aufgabe.',
  'Am Ende bekommt jede geprüfte Website ihr eigenes öffentliches Protokoll, ' +
    'offene Punkte eingeschlossen. Prüfen Sie Ihre Website.',
];

// Gemeinsamer Stil der beiden Bedienknoepfe auf dem Video. Der Fokusrahmen
// ist Pflicht, nicht Kuer: die Knoepfe liegen auf bewegtem Bild, ein nur
// durch Browser-Standard markierter Fokus geht dort unter (WCAG 2.4.7).
const KNOPF =
  'inline-flex items-center gap-1.5 bg-white/90 hover:bg-white text-gray-700 text-xs ' +
  'font-semibold px-3 py-2 rounded-full shadow-md border border-gray-200 transition-colors ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-akzent-700 focus-visible:ring-offset-2';

export default function Erklaervideo() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [muted, setMuted] = useState(true);
  // Spiegelt den echten Zustand des video-Elements (play/pause-Ereignisse),
  // nicht die Absicht des letzten Klicks. So stimmt die Beschriftung auch,
  // wenn der Browser das Abspielen selbst verweigert oder anhaelt.
  const [playing, setPlaying] = useState(false);

  // Kein autoPlay-Attribut: das Video startet erst hier, und nur, wenn die
  // Person keine reduzierte Bewegung eingestellt hat (WCAG 2.2.2 und 2.3.3).
  // Mit prefers-reduced-motion bleibt das Poster stehen, der Knopf startet.
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const reduziert =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduziert) return;
    v.muted = true;
    v.play().catch(() => {
      // Autoplay verweigert: Poster bleibt, die Knoepfe uebernehmen.
    });
  }, []);

  const toggleSound = () => {
    const v = videoRef.current;
    if (!v) return;
    if (muted) {
      v.currentTime = 0;
      v.muted = false;
      setMuted(false);
      v.play().catch(() => {});
    } else {
      v.muted = true;
      setMuted(true);
    }
  };

  const togglePlay = () => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) {
      v.play().catch(() => {});
    } else {
      v.pause();
    }
  };

  return (
    <div className="relative bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
      <div className="bg-gray-50 border-b border-gray-100 px-5 py-3 flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-red-400" />
        <div className="w-3 h-3 rounded-full bg-yellow-400" />
        <div className="w-3 h-3 rounded-full bg-green-400" />
        <span className="ml-3 text-xs text-gray-500">complyo – in 72 Sekunden erklärt</span>
      </div>

      <div className="relative">
        <video
          ref={videoRef}
          className="block w-full h-auto"
          muted
          loop
          playsInline
          preload="metadata"
          poster="/videos/complyo-erklaervideo-poster.jpg"
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          aria-label="Erklärvideo: Wie complyo Websites gegen Barrierefreiheit, Datenschutz, Cookie-Einwilligung und Pflichttexte prüft, Reparaturen zur Freigabe vorschlägt, täglich neue Rechtspflichten meldet und für jede geprüfte Website ein öffentliches Prüfprotokoll erstellt. Das vollständige Transkript steht unter dem Video."
        >
          <source src="/videos/complyo-erklaervideo.mp4" type="video/mp4" />
          {/* Die im Bild eingebrannten Untertitel sind weder
              abschaltbar noch maschinell lesbar. Diese Spur ist es. */}
          <track
            kind="captions"
            srcLang="de"
            label="Deutsch"
            src="/videos/complyo-erklaervideo.de.vtt"
            default
          />
        </video>
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          {/* Pause-Bedienelement fuer das selbststartende Video (WCAG 2.2.2,
              Stufe A: Bewegtbild ueber fuenf Sekunden muss anhaltbar sein). */}
          <button
            type="button"
            onClick={togglePlay}
            aria-label={playing ? 'Video anhalten' : 'Video abspielen'}
            className={KNOPF}
          >
            {playing ? <Pause className="w-4 h-4" aria-hidden="true" /> : <Play className="w-4 h-4" aria-hidden="true" />}
            {playing ? 'Pause' : 'Abspielen'}
          </button>
          <button
            type="button"
            onClick={toggleSound}
            aria-label={muted ? 'Ton einschalten und Video von vorn abspielen' : 'Ton ausschalten'}
            className={KNOPF}
          >
            {muted ? <Volume2 className="w-4 h-4" aria-hidden="true" /> : <VolumeX className="w-4 h-4" aria-hidden="true" />}
            {muted ? 'Mit Ton abspielen' : 'Stumm'}
          </button>
        </div>
      </div>

      {/* Textalternative fuer alle, die das Video nicht ansehen oder
          hoeren koennen oder wollen (WCAG 1.2.3). Zugeklappt, damit
          sie den Hero nicht auseinanderzieht. */}
      <details className="border-t border-gray-100 px-5 py-3 text-left">
        <summary className="cursor-pointer text-xs font-semibold text-gray-700 hover:text-akzent-800">
          Transkript des Videos anzeigen
        </summary>
        <div className="mt-3 space-y-2 text-xs leading-relaxed text-gray-600">
          {TRANSKRIPT.map((absatz, i) => (
            <p key={i}>{absatz}</p>
          ))}
        </div>
      </details>
    </div>
  );
}
