'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import './auth-neu.css';

// Die drei Aussagen hinter den Punkten. Jede beschreibt, was der Scan
// tatsaechlich misst, keinen Zustand der Kundenseite.
const AUSSAGEN = [
    {
        zeilen: ['Prüfen. Beheben.', 'Nachweisen.'],
        text: ['Complyo misst, was Ihre Website heute tatsächlich lädt', 'und zeigt, was sich davon beheben lässt.'],
    },
    {
        zeilen: ['Cookies im Griff.', 'Ohne Rätselraten.'],
        text: ['Der Scan öffnet Ihre Seite im Browser und zeigt,', 'welche Dienste wirklich geladen werden.'],
    },
    {
        zeilen: ['Barrierefreiheit,', 'Seite für Seite.'],
        text: ['Die Prüfung nach WCAG zeigt, an welchen Stellen', 'Besucher auf Ihrer Website scheitern.'],
    },
];

/**
 * Foto, Video, Schatten und linke Spalte der Anmelde- und Registrierungsseite.
 * Eine Quelle, damit beide Seiten nicht auseinanderlaufen (siehe
 * auth-neu.css fuer die Masse). Gehoert in ein Element mit Klasse `lg`.
 */
export function AuthHero() {
    const [aussage, setAussage] = useState(0);
    const [umgeschaltet, setUmgeschaltet] = useState(false);

    // Das Video nur dort, wo Bewegung erlaubt ist. Das Standbild steht immer.
    const [videoErlaubt, setVideoErlaubt] = useState(false);
    const [videoBereit, setVideoBereit] = useState(false);
    const videoRef = (v: HTMLVideoElement | null) => {
        // Bei zwischengespeichertem Video feuert loadeddata, bevor React den
        // Handler anhaengt, deshalb zusaetzlich der Stand beim Einhaengen.
        if (v && v.readyState >= 2) setVideoBereit(true);
    };

    useEffect(() => {
        const ruhe = window.matchMedia?.('(prefers-reduced-motion: reduce)');
        if (!ruhe?.matches) setVideoErlaubt(true);
    }, []);

    const a = AUSSAGEN[aussage];

    return (
        <>
            <div className="lg-plate" aria-hidden="true" />
            {videoErlaubt && (
                <video
                    ref={videoRef}
                    className={`lg-video${videoBereit ? ' is-ready' : ''}`}
                    src="/login/loop.mp4"
                    autoPlay
                    muted
                    loop
                    playsInline
                    preload="auto"
                    aria-hidden="true"
                    tabIndex={-1}
                    onLoadedData={() => setVideoBereit(true)}
                />
            )}
            <div className="lg-shade lg-shade-l" aria-hidden="true" />
            <div className="lg-shade lg-shade-t" aria-hidden="true" />
            <div className="lg-shade lg-shade-b" aria-hidden="true" />

            <section className="lg-hero" aria-label="Complyo">
                <div className="lg-bar">
                    <a href="https://complyo.de" className="lg-logo lg-in" style={{ ['--d' as any]: '.1s' }} aria-label="Complyo, zur Website">
                        <Image src="/logo-light-trim.png" alt="Complyo" width={852} height={287} priority />
                    </a>
                    <a href="https://complyo.de" className="lg-back lg-in" style={{ ['--d' as any]: '.18s' }}>
                        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16 10H4m0 0 5-5m-5 5 5 5" /></svg>
                        Zurück zur Website
                    </a>
                </div>

                <div className="lg-pitch">
                    <div key={aussage} className={umgeschaltet ? 'is-sw' : undefined}>
                        <h2 className="lg-title" aria-live="polite">
                            {a.zeilen.map((z, i) => (
                                <span className="lg-line" key={z}>
                                    <span style={{ ['--d' as any]: `${0.5 + i * 0.12}s` }}>{z}</span>
                                </span>
                            ))}
                        </h2>
                        <p className="lg-sub lg-in" style={{ ['--d' as any]: '.85s' }}>
                            {a.text[0]}<br />{a.text[1]}
                        </p>
                    </div>
                    <div className="lg-dots lg-in" style={{ ['--d' as any]: '1s' }} role="group" aria-label="Aussage wählen">
                        {AUSSAGEN.map((_, i) => (
                            <button
                                key={i}
                                type="button"
                                className={i === aussage ? 'is-active' : undefined}
                                aria-label={`Aussage ${i + 1} von ${AUSSAGEN.length}`}
                                aria-current={i === aussage ? 'true' : undefined}
                                onClick={() => { setAussage(i); setUmgeschaltet(true); }}
                            />
                        ))}
                    </div>
                </div>
            </section>
        </>
    );
}

/** Auge mit Strich fuer den Passwort-Umschalter (Strich = Passwort sichtbar). */
export function PasswortAuge({ sichtbar }: { sichtbar: boolean }) {
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
            <circle cx="12" cy="12" r="3" />
            <path className={`lg-slash${sichtbar ? ' is-on' : ''}`} d="M4 4l16 16" />
        </svg>
    );
}
