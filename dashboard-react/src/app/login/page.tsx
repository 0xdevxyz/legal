'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { LogIn, Loader2, AlertCircle, Lock, Mail, Eye, EyeOff, ArrowRight, CheckCircle2 } from 'lucide-react';
import SocialLoginButtons from '@/components/SocialLoginButtons';
import { Logo } from '@/components/Logo';

const loadingMessages = [
    "Sicherheitsprotokolle werden geladen...",
    "Compliance-Daten werden abgerufen...",
    "Ihre Identität wird verifiziert...",
    "Dashboard wird vorbereitet...",
    "Fast geschafft..."
];

export default function LoginPage() {
    const { login, isAuthenticated } = useAuth();
    const router = useRouter();

    const [formData, setFormData] = useState({ email: '', password: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState(loadingMessages[0]);
    const [loadingProgress, setLoadingProgress] = useState(0);
    const [emailFocused, setEmailFocused] = useState(false);
    const [passwordFocused, setPasswordFocused] = useState(false);
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const particles: { x: number; y: number; vx: number; vy: number; size: number; opacity: number }[] = [];
        for (let i = 0; i < 60; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                size: Math.random() * 1.5 + 0.5,
                opacity: Math.random() * 0.4 + 0.1,
            });
        }

        let animId: number;
        const draw = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {
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
            particles.forEach((p, i) => {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[j].x - p.x;
                    const dy = particles[j].y - p.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 100) {
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(99, 179, 237, ${0.08 * (1 - dist / 100)})`;
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            });
            animId = requestAnimationFrame(draw);
        };
        draw();

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        window.addEventListener('resize', handleResize);
        return () => {
            cancelAnimationFrame(animId);
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    useEffect(() => {
        if (!isSubmitting) return;
        let messageIndex = 0;
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 95) progress = 95;
            setLoadingProgress(progress);
        }, 200);
        const messageInterval = setInterval(() => {
            messageIndex = (messageIndex + 1) % loadingMessages.length;
            setLoadingMessage(loadingMessages[messageIndex]);
        }, 1500);
        return () => {
            clearInterval(progressInterval);
            clearInterval(messageInterval);
        };
    }, [isSubmitting]);

    useEffect(() => {
        if (isAuthenticated && !isSubmitting) {
            router.push('/');
        }
    }, [isAuthenticated, isSubmitting, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsSubmitting(true);
        setLoadingProgress(0);
        try {
            await login(formData.email, formData.password);
            setLoadingProgress(100);
            setTimeout(() => router.push('/'), 500);
        } catch (error: any) {
            setError(error.message || 'Login fehlgeschlagen. Bitte prüfen Sie Ihre Zugangsdaten.');
            setIsSubmitting(false);
            setLoadingProgress(0);
        }
    };

    const emailHasValue = formData.email.length > 0;
    const passwordHasValue = formData.password.length > 0;

    return (
        <main
            role="main"
            aria-label="Login"
            className="min-h-screen flex items-center justify-center relative overflow-hidden"
            style={{ background: 'linear-gradient(135deg, #050812 0%, #0a0f1e 40%, #0d1428 70%, #050812 100%)' }}
        >
            <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none" />

            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full pointer-events-none" style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%)' }} />
                <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full pointer-events-none" style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)' }} />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full pointer-events-none" style={{ background: 'radial-gradient(circle, rgba(16,24,64,0.4) 0%, transparent 60%)' }} />
            </div>

            <div className="relative w-full max-w-md mx-4 z-10">
                <div className="mb-8 text-center">
                    <div className="flex justify-center mb-4">
                        <Logo size="lg" />
                    </div>
                    <p className="text-sm" style={{ color: 'rgba(148,163,184,0.7)' }}>
                        Legal Compliance Platform
                    </p>
                </div>

                <section
                    className="relative rounded-2xl p-8 overflow-hidden"
                    style={{
                        background: 'rgba(15, 23, 42, 0.7)',
                        backdropFilter: 'blur(24px)',
                        WebkitBackdropFilter: 'blur(24px)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        boxShadow: '0 0 0 1px rgba(255,255,255,0.03), 0 32px 64px rgba(0,0,0,0.5), 0 0 80px rgba(59,130,246,0.05)',
                    }}
                >
                    <div className="absolute top-0 left-0 right-0 h-px" style={{ background: 'linear-gradient(90deg, transparent, rgba(99,179,237,0.3), transparent)' }} />

                    <div className="mb-7">
                        <h1 className="text-2xl font-semibold text-white mb-1.5 tracking-tight">Willkommen zurück</h1>
                        <p className="text-sm" style={{ color: 'rgba(148,163,184,0.6)' }}>
                            Melden Sie sich an, um auf Ihr Dashboard zuzugreifen
                        </p>
                    </div>

                    {error && (
                        <div
                            className="mb-5 p-3.5 rounded-xl flex items-start gap-3 text-sm animate-errorfade"
                            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
                        >
                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#f87171' }} />
                            <span style={{ color: '#fca5a5' }}>{error}</span>
                        </div>
                    )}

                    {isSubmitting && (
                        <div className="mb-5 space-y-2.5">
                            <div className="flex items-center gap-2.5">
                                <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: '#60a5fa' }} />
                                <span className="text-xs" style={{ color: '#60a5fa' }}>{loadingMessage}</span>
                            </div>
                            <div className="h-0.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                                <div
                                    className="h-full rounded-full transition-all duration-300"
                                    style={{
                                        width: `${loadingProgress}%`,
                                        background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                                        boxShadow: '0 0 8px rgba(59,130,246,0.5)',
                                    }}
                                />
                            </div>
                        </div>
                    )}

                    <div className="mb-5">
                        <SocialLoginButtons mode="login" />
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="relative">
                            <label
                                htmlFor="email"
                                className="block text-xs font-medium mb-2 transition-colors duration-200"
                                style={{ color: emailFocused ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}
                            >
                                E-Mail-Adresse
                            </label>
                            <div className="relative">
                                <Mail
                                    className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200"
                                    style={{ color: emailFocused ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                                />
                                <input
                                    id="email"
                                    type="email"
                                    placeholder="ihre@email.com"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    onFocus={() => setEmailFocused(true)}
                                    onBlur={() => setEmailFocused(false)}
                                    required
                                    disabled={isSubmitting}
                                    className="w-full pl-10 pr-10 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all duration-200 disabled:opacity-40"
                                    style={{
                                        background: emailFocused ? 'rgba(59,130,246,0.04)' : 'rgba(255,255,255,0.03)',
                                        border: emailFocused ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.07)',
                                        boxShadow: emailFocused ? '0 0 0 3px rgba(59,130,246,0.08)' : 'none',
                                    }}
                                />
                                {emailHasValue && !isSubmitting && (
                                    <CheckCircle2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#34d399' }} />
                                )}
                            </div>
                        </div>

                        <div className="relative">
                            <div className="flex items-center justify-between mb-2">
                                <label
                                    htmlFor="password"
                                    className="block text-xs font-medium transition-colors duration-200"
                                    style={{ color: passwordFocused ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}
                                >
                                    Passwort
                                </label>
                                <a
                                    href="mailto:support@complyo.tech"
                                    className="text-xs transition-colors duration-200 hover:opacity-80"
                                    style={{ color: 'rgba(96,165,250,0.6)' }}
                                >
                                    Passwort vergessen?
                                </a>
                            </div>
                            <div className="relative">
                                <Lock
                                    className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200"
                                    style={{ color: passwordFocused ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                                />
                                <input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="••••••••••••"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    onFocus={() => setPasswordFocused(true)}
                                    onBlur={() => setPasswordFocused(false)}
                                    required
                                    disabled={isSubmitting}
                                    className="w-full pl-10 pr-10 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all duration-200 disabled:opacity-40"
                                    style={{
                                        background: passwordFocused ? 'rgba(59,130,246,0.04)' : 'rgba(255,255,255,0.03)',
                                        border: passwordFocused ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.07)',
                                        boxShadow: passwordFocused ? '0 0 0 3px rgba(59,130,246,0.08)' : 'none',
                                    }}
                                />
                                {passwordHasValue && (
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3.5 top-1/2 -translate-y-1/2 transition-colors duration-200 hover:opacity-80"
                                        style={{ color: 'rgba(100,116,139,0.7)' }}
                                        tabIndex={-1}
                                    >
                                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                )}
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full py-3 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2.5 transition-all duration-300 mt-2 group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
                            style={{
                                background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)',
                                boxShadow: isSubmitting ? 'none' : '0 4px 20px rgba(37,99,235,0.3)',
                            }}
                        >
                            <div
                                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                                style={{ background: 'linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%)' }}
                            />
                            <span className="relative flex items-center gap-2.5">
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Anmeldung läuft...
                                    </>
                                ) : (
                                    <>
                                        <LogIn className="w-4 h-4" />
                                        Anmelden
                                        <ArrowRight className="w-3.5 h-3.5 opacity-0 -ml-1 group-hover:opacity-100 group-hover:ml-0 transition-all duration-200" />
                                    </>
                                )}
                            </span>
                        </button>
                    </form>

                    <div className="mt-6 pt-5" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                        <p className="text-center text-xs" style={{ color: 'rgba(100,116,139,0.6)' }}>
                            Noch kein Konto?{' '}
                            <a
                                href="/register"
                                className="font-medium transition-colors duration-200 hover:opacity-80"
                                style={{ color: '#60a5fa' }}
                            >
                                Jetzt registrieren
                            </a>
                        </p>
                    </div>
                </section>

                <div className="mt-5 flex items-center justify-center gap-4">
                    <div className="flex items-center gap-1.5">
                        <Lock className="w-3 h-3" style={{ color: 'rgba(100,116,139,0.4)' }} />
                        <span className="text-xs" style={{ color: 'rgba(100,116,139,0.4)' }}>256-bit SSL</span>
                    </div>
                    <div className="w-px h-3" style={{ background: 'rgba(100,116,139,0.2)' }} />
                    <span className="text-xs" style={{ color: 'rgba(100,116,139,0.4)' }}>DSGVO-konform</span>
                    <div className="w-px h-3" style={{ background: 'rgba(100,116,139,0.2)' }} />
                    <span className="text-xs" style={{ color: 'rgba(100,116,139,0.4)' }}>ISO 27001</span>
                </div>
            </div>

            <style jsx>{`
                @keyframes errorfade {
                    from { opacity: 0; transform: translateY(-4px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-errorfade {
                    animation: errorfade 0.2s ease-out forwards;
                }
            `}</style>
        </main>
    );
}
