'use client';

import { useEffect, useRef } from 'react';

/**
 * Der Hintergrund der Anmelde- und Registrierungsseite.
 *
 * Warum als eigenes Bauteil: Anmeldung und Registrierung sollen gleich
 * aussehen, und der einzige verlaessliche Weg dorthin ist eine gemeinsame
 * Quelle. Kopiert man den Verlauf samt Partikelfeld in beide Dateien, sieht
 * es heute gleich aus und in drei Monaten nicht mehr — dieses Projekt hat
 * genau diese Sorte Drift schon mehrfach bezahlt.
 *
 * Neu gegenueber der bisherigen Fassung auf der Anmeldeseite:
 * `prefers-reduced-motion` wird beachtet. Wer in seinem System angegeben hat,
 * dass Bewegung ihm Beschwerden bereitet, bekommt den ruhigen Verlauf ohne
 * Partikel. Fuer einen Anbieter, der Barrierefreiheit verkauft, ist eine
 * Dauer­animation auf der ersten Seite, die ein Kunde sieht, keine Kleinigkeit
 * (WCAG 2.3.3 bzw. 2.2.2).
 */
export function AuthBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        // Bewegung nur, wenn sie nicht ausdruecklich abbestellt wurde.
        const ruhe = window.matchMedia?.('(prefers-reduced-motion: reduce)');
        if (ruhe?.matches) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const groesseSetzen = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        groesseSetzen();

        const partikel: { x: number; y: number; vx: number; vy: number; size: number; opacity: number }[] = [];
        for (let i = 0; i < 60; i++) {
            partikel.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                size: Math.random() * 1.5 + 0.5,
                opacity: Math.random() * 0.4 + 0.1,
            });
        }

        let animId: number;
        const zeichnen = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            partikel.forEach((p) => {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(99, 179, 237, ${p.opacity})`;
                ctx.fill();
            });
            partikel.forEach((p, i) => {
                for (let j = i + 1; j < partikel.length; j++) {
                    const dx = partikel[j].x - p.x;
                    const dy = partikel[j].y - p.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 100) {
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(99, 179, 237, ${0.08 * (1 - dist / 100)})`;
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(partikel[j].x, partikel[j].y);
                        ctx.stroke();
                    }
                }
            });
            animId = requestAnimationFrame(zeichnen);
        };
        zeichnen();

        window.addEventListener('resize', groesseSetzen);
        return () => {
            cancelAnimationFrame(animId);
            window.removeEventListener('resize', groesseSetzen);
        };
    }, []);

    return (
        <>
            {/* aria-hidden: reine Dekoration, fuer Screenreader nichts zu holen. */}
            <canvas ref={canvasRef} aria-hidden="true" className="absolute inset-0 pointer-events-none" />
            <div aria-hidden="true" className="absolute inset-0 pointer-events-none">
                <div
                    className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full pointer-events-none"
                    style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%)' }}
                />
                <div
                    className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full pointer-events-none"
                    style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)' }}
                />
                <div
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full pointer-events-none"
                    style={{ background: 'radial-gradient(circle, rgba(16,24,64,0.4) 0%, transparent 60%)' }}
                />
            </div>
        </>
    );
}

/** Der Seitenverlauf — identisch auf Anmeldung und Registrierung. */
export const AUTH_VERLAUF =
    'linear-gradient(135deg, #050812 0%, #0a0f1e 40%, #0d1428 70%, #050812 100%)';

/** Die Glaskarte, in der beide Formulare stehen. */
export const AUTH_KARTE: React.CSSProperties = {
    background: 'rgba(15, 23, 42, 0.7)',
    backdropFilter: 'blur(24px)',
    WebkitBackdropFilter: 'blur(24px)',
    border: '1px solid rgba(255,255,255,0.06)',
    boxShadow:
        '0 0 0 1px rgba(255,255,255,0.03), 0 32px 64px rgba(0,0,0,0.5), 0 0 80px rgba(59,130,246,0.05)',
};

/** Eingabefeld: Ruhe- und Fokuszustand, damit beide Seiten gleich reagieren. */
export function feldStil(fokussiert: boolean): React.CSSProperties {
    return {
        background: fokussiert ? 'rgba(59,130,246,0.04)' : 'rgba(255,255,255,0.03)',
        border: fokussiert ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.07)',
        boxShadow: fokussiert ? '0 0 0 3px rgba(59,130,246,0.08)' : 'none',
    };
}

/** Die Vertrauenszeile unter der Karte. */
export function AuthVertrauen() {
    return (
        <div className="mt-5 flex items-center justify-center gap-4">
            <span className="text-xs" style={{ color: 'rgba(100,116,139,0.4)' }}>256-bit SSL</span>
            <div className="w-px h-3" style={{ background: 'rgba(100,116,139,0.2)' }} />
            <span className="text-xs" style={{ color: 'rgba(100,116,139,0.4)' }}>DSGVO-konform</span>
            <div className="w-px h-3" style={{ background: 'rgba(100,116,139,0.2)' }} />
            {/* Hier stand "ISO 27001". Eine Zertifizierung, die complyo nicht
                haelt, und ohne Beleglink — genau der Befund, den der eigene
                Scanner als Irrefuehrung nach §5 UWG meldet. Ersetzt durch eine
                Aussage, die belegbar ist (01.09.2026). */}
            <span className="text-xs" style={{ color: 'rgba(100,116,139,0.4)' }}>Server in Deutschland</span>
        </div>
    );
}
