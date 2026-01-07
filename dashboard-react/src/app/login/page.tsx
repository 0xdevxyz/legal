'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Shield, LogIn, Loader2, AlertCircle, Sparkles, Lock, Mail } from 'lucide-react';
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
    
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });
    
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [loadingMessage, setLoadingMessage] = useState(loadingMessages[0]);
    const [loadingProgress, setLoadingProgress] = useState(0);
    
    // Animated loading messages
    useEffect(() => {
        if (!isSubmitting) return;
        
        let messageIndex = 0;
        let progress = 0;
        
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 95) progress = 95; // Stop at 95% until actual login completes
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
    
    // Redirect if already authenticated
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
            // Kurze Pause für UI-Feedback, dann redirect
            setTimeout(() => {
                router.push('/');
            }, 500);
        } catch (error: any) {
            console.error('Login error:', error);
            setError(error.message || 'Login fehlgeschlagen. Bitte prüfen Sie Ihre Zugangsdaten.');
            setIsSubmitting(false);
            setLoadingProgress(0);
        }
    };
    
    return (
        <main role="main" aria-label="Login" className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 px-4 relative overflow-hidden">
            {/* Animated Background Blobs */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
                <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
                <div className="absolute top-40 right-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
            </div>
            
            <section className="relative bg-gray-800 bg-opacity-90 backdrop-blur-lg p-8 rounded-2xl max-w-md w-full border border-gray-700 shadow-2xl">
                {/* Logo with Animation */}
                <div className="flex items-center justify-center mb-6">
                    <Logo size="xl" />
                    <Sparkles className="w-5 h-5 text-yellow-400 animate-pulse ml-2" />
                </div>
                
                <h1 className="text-3xl font-bold mb-2 text-center">Willkommen zurück</h1>
                <p className="text-gray-400 mb-6 text-center">
                    Melden Sie sich an, um auf Ihr Dashboard zuzugreifen
                </p>
                
                {/* Error Message */}
                {error && (
                    <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-500 rounded-lg flex items-center gap-2 text-red-200 animate-shake">
                        <AlertCircle className="w-5 h-5 flex-shrink-0" />
                        <span className="text-sm">{error}</span>
                    </div>
                )}
                
                {/* Loading Progress Bar */}
                {isSubmitting && (
                    <div className="mb-4 space-y-2">
                        <div className="flex items-center gap-2 text-sm text-blue-400">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span className="animate-pulse">{loadingMessage}</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                            <div 
                                className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 bg-[length:200%_100%] animate-gradient transition-all duration-300"
                                style={{ width: `${loadingProgress}%` }}
                            />
                        </div>
                    </div>
                )}
                
                {/* Social Login Buttons */}
                <div className="mb-6">
                    <SocialLoginButtons mode="login" />
                </div>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="relative group">
                        <label htmlFor="email" className="block text-sm font-medium mb-1 text-gray-300">
                            E-Mail
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-blue-400 transition-colors" />
                            <input
                                id="email"
                                type="email"
                                placeholder="ihre@email.com"
                                value={formData.email}
                                onChange={(e) => setFormData({...formData, email: e.target.value})}
                                required
                                disabled={isSubmitting}
                                className="w-full pl-11 pr-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 focus:outline-none disabled:opacity-50 transition-all duration-200"
                            />
                        </div>
                    </div>
                    
                    <div className="relative group">
                        <label htmlFor="password" className="block text-sm font-medium mb-1 text-gray-300">
                            Passwort
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-blue-400 transition-colors" />
                            <input
                                id="password"
                                type="password"
                                placeholder="••••••••"
                                value={formData.password}
                                onChange={(e) => setFormData({...formData, password: e.target.value})}
                                required
                                disabled={isSubmitting}
                                className="w-full pl-11 pr-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 focus:outline-none disabled:opacity-50 transition-all duration-200"
                            />
                        </div>
                    </div>
                    
                    <button 
                        type="submit" 
                        disabled={isSubmitting}
                        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 py-3 rounded-lg font-bold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]"
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Anmeldung läuft...
                            </>
                        ) : (
                            <>
                                <LogIn className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                Anmelden
                            </>
                        )}
                    </button>
                </form>
                
                <div className="mt-6 text-center">
                    <a href="#" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
                        Passwort vergessen?
                    </a>
                </div>
                
                <div className="mt-4 text-center text-gray-400 text-sm">
                    Noch kein Konto?{' '}
                    <a href="/register" className="text-blue-400 hover:text-blue-300 font-semibold transition-colors">
                        Jetzt registrieren
                    </a>
                </div>
                
                {/* Security Badge */}
                <div className="mt-6 flex items-center justify-center gap-2 text-xs text-gray-500">
                    <Lock className="w-3 h-3" />
                    <span>256-bit SSL verschlüsselt</span>
                </div>
            </section>
            
            {/* CSS Animations */}
            <style jsx>{`
                @keyframes blob {
                    0%, 100% { transform: translate(0, 0) scale(1); }
                    33% { transform: translate(30px, -50px) scale(1.1); }
                    66% { transform: translate(-20px, 20px) scale(0.9); }
                }
                
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                    20%, 40%, 60%, 80% { transform: translateX(5px); }
                }
                
                @keyframes gradient {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }
                
                .animate-blob {
                    animation: blob 7s infinite;
                }
                
                .animate-shake {
                    animation: shake 0.5s;
                }
                
                .animate-gradient {
                    animation: gradient 3s ease infinite;
                }
                
                .animation-delay-2000 {
                    animation-delay: 2s;
                }
                
                .animation-delay-4000 {
                    animation-delay: 4s;
                }
            `}</style>
        </main>
    );
}
