'use client';
import React, { useRef, useState } from 'react';
import { Volume2, VolumeX } from 'lucide-react';

// Wortlaut der Erzaehlung, abgelesen aus den eingebrannten Untertiteln der
// Videodatei. Aenderungen am Video muessen hier und in der VTT-Spur nachgezogen
// werden — sonst steht neben dem Video ein Text, der nicht dazu gehoert.
//
// Diese Komponente ist aus HeroSection herausgeloest, weil das Video seit dem
// 02.09.2026 an zwei Stellen steht: auf der Early-Access-Startseite und auf der
// Produktseite unter /produkt. Zwei Kopien haetten bedeutet, dass ein neues
// Video an einer Stelle nachgezogen wird und an der anderen ein Transkript
// stehen bleibt, das nicht mehr zum Ton passt.
export const TRANSKRIPT = [
  'Datenschutz, Cookie-Banner, Barrierefreiheit – wer blickt da noch durch? ' +
    'Jede Woche neue Pflichten, und auf der eigenen Website sammeln sich still ' +
    'die Warnzeichen, während der Laden laufen soll.',
  'Hinter dem Chaos stecken genau vier Säulen: Barrierefreiheit für alle ' +
    'Besucher, Datenschutz, saubere Cookie-Einwilligung und rechtssichere Texte ' +
    'vom Impressum bis zum Widerruf.',
  'Wer eine Säule ignoriert, riskiert Abmahnung oder Bußgeld, und seit dem ' +
    'Barrierefreiheitsstärkungsgesetz trifft das auch kleine Shops. Die Pflichten ' +
    'wachsen schneller als der Umsatz.',
  'Genau hier setzt complyo an: Ein Scan prüft die Website in unter sechzig ' +
    'Sekunden gegen alle vier Säulen und zeigt jede Baustelle auf einem Bildschirm.',
  'Im Dashboard repariert die künstliche Intelligenz direkt mit: Alt-Texte, ' +
    'Kontraste, Cookie-Banner und Rechtstexte bekommen nacheinander ihren Haken, ' +
    'und jede Reparatur wird im Browser nachgemessen.',
  'Aus vier Baustellen wird eine Übersicht voller Haken, der Prüfnachweis liegt ' +
    'dabei. Also: Durchblicken statt Ärgern – testen Sie Ihre Website heute, eine ' +
    'Minute genügt.',
];

export default function Erklaervideo() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [muted, setMuted] = useState(true);

  const toggleSound = () => {
    const v = videoRef.current;
    if (!v) return;
    if (muted) {
      v.currentTime = 0;
      v.muted = false;
      setMuted(false);
      v.play();
    } else {
      v.muted = true;
      setMuted(true);
    }
  };

  return (
    <div className="relative bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
      <div className="bg-gray-50 border-b border-gray-100 px-5 py-3 flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-red-400" />
        <div className="w-3 h-3 rounded-full bg-yellow-400" />
        <div className="w-3 h-3 rounded-full bg-green-400" />
        <span className="ml-3 text-xs text-gray-500">Complyo – in 60 Sekunden erklärt</span>
      </div>

      <div className="relative">
        <video
          ref={videoRef}
          className="block w-full h-auto"
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          poster="/videos/complyo-erklaervideo-poster.jpg"
          aria-label="Erklärvideo: Wie Complyo die vier Compliance-Säulen Barrierefreiheit, Datenschutz, Cookie-Einwilligung und Rechtstexte löst. Das vollständige Transkript steht unter dem Video."
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
        <button
          type="button"
          onClick={toggleSound}
          aria-label={muted ? 'Ton einschalten und Video von vorn abspielen' : 'Ton ausschalten'}
          className="absolute bottom-3 right-3 inline-flex items-center gap-1.5 bg-white/90 hover:bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-full shadow-md border border-gray-200 transition-colors"
        >
          {muted ? <Volume2 className="w-4 h-4" aria-hidden="true" /> : <VolumeX className="w-4 h-4" aria-hidden="true" />}
          {muted ? 'Mit Ton abspielen' : 'Stumm'}
        </button>
      </div>

      {/* Textalternative fuer alle, die das Video nicht ansehen oder
          hoeren koennen oder wollen (WCAG 1.2.3). Zugeklappt, damit
          sie den Hero nicht auseinanderzieht. */}
      <details className="border-t border-gray-100 px-5 py-3 text-left">
        <summary className="cursor-pointer text-xs font-semibold text-gray-700 hover:text-blue-700">
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
