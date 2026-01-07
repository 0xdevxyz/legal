'use client';

import { useState, Suspense } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter, useSearchParams } from 'next/navigation';
import { Shield, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import SocialLoginButtons from '@/components/SocialLoginButtons';
import { Logo } from '@/components/Logo';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

function RegisterForm() {
    const { register } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();
    const plan = searchParams?.get('plan') || 'ki';
    
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        full_name: '',
        company: '',
        plan
    });
    
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsSubmitting(true);
        
        try {
            // Register user
            await register(formData);
            
            // Nach Registration: Stripe Checkout
            const checkoutResponse = await fetch(`${API_BASE}/api/payment/create-checkout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ plan_type: plan })
            });
            
            if (!checkoutResponse.ok) {
                throw new Error('Fehler beim Erstellen der Zahlungssitzung');
            }
            
            const { checkout_url } = await checkoutResponse.json();
            window.location.href = checkout_url;  // Redirect to Stripe
        } catch (error: any) {
            console.error('Registration error:', error);
            setError(error.message || 'Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut.');
            setIsSubmitting(false);
        }
    };
    
    const planPrice = plan === 'expert' ? '2.000€ + 39€/Monat' : '39€/Monat';
    const planName = plan === 'expert' ? 'Expert Plan' : 'KI Plan';
    
    return (
        <main role="main" aria-label="Registrierung" className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
            <section className="bg-gray-800 p-8 rounded-lg max-w-md w-full border border-gray-700 shadow-xl">
                {/* Logo */}
                <div className="flex items-center justify-center mb-6">
                    <Logo size="xl" />
                </div>
                
                <h1 className="text-3xl font-bold mb-2 text-center">Jetzt registrieren</h1>
                <p className="text-gray-400 mb-6 text-center">
                    <span className={`font-semibold ${plan === 'expert' ? 'text-yellow-400' : 'text-blue-400'}`}>
                        {planName}
                    </span>
                    {' '}- {planPrice}
                </p>
                
                {error && (
                    <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-500 rounded flex items-center gap-2 text-red-200">
                        <AlertCircle className="w-5 h-5 flex-shrink-0" />
                        <span className="text-sm">{error}</span>
                    </div>
                )}
                
                {/* Social Login Buttons */}
                <div className="mb-6">
                    <SocialLoginButtons plan={plan} mode="register" />
                </div>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium mb-1 text-gray-300">
                            E-Mail *
                        </label>
                        <input
                            id="email"
                            type="email"
                            placeholder="ihre@email.com"
                            value={formData.email}
                            onChange={(e) => setFormData({...formData, email: e.target.value})}
                            required
                            disabled={isSubmitting}
                            className="w-full px-4 py-3 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                        />
                    </div>
                    
                    <div>
                        <label htmlFor="password" className="block text-sm font-medium mb-1 text-gray-300">
                            Passwort *
                        </label>
                        <input
                            id="password"
                            type="password"
                            placeholder="Mindestens 8 Zeichen"
                            value={formData.password}
                            onChange={(e) => setFormData({...formData, password: e.target.value})}
                            required
                            minLength={8}
                            disabled={isSubmitting}
                            className="w-full px-4 py-3 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                        />
                    </div>
                    
                    <div>
                        <label htmlFor="full_name" className="block text-sm font-medium mb-1 text-gray-300">
                            Vollständiger Name *
                        </label>
                        <input
                            id="full_name"
                            type="text"
                            placeholder="Max Mustermann"
                            value={formData.full_name}
                            onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                            required
                            disabled={isSubmitting}
                            className="w-full px-4 py-3 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                        />
                    </div>
                    
                    <div>
                        <label htmlFor="company" className="block text-sm font-medium mb-1 text-gray-300">
                            Firma (optional)
                        </label>
                        <input
                            id="company"
                            type="text"
                            placeholder="Ihr Unternehmen"
                            value={formData.company}
                            onChange={(e) => setFormData({...formData, company: e.target.value})}
                            disabled={isSubmitting}
                            className="w-full px-4 py-3 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                        />
                    </div>
                    
                    <button 
                        type="submit" 
                        disabled={isSubmitting}
                        className="w-full bg-blue-600 py-3 rounded font-bold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Wird verarbeitet...
                            </>
                        ) : (
                            <>
                                Weiter zur Zahlung
                                <CheckCircle className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </form>
                
                <div className="mt-6 text-center text-sm text-gray-400">
                    <p>Bereits registriert?{' '}
                        <a href="/login" className="text-blue-400 hover:text-blue-300 font-semibold">
                            Jetzt anmelden
                        </a>
                    </p>
                </div>
                
                <div className="mt-6 text-xs text-gray-500 text-center">
                    Mit der Registrierung stimmen Sie unseren{' '}
                    <a href="/agb" className="text-blue-400 hover:underline">AGB</a> und der{' '}
                    <a href="/datenschutz" className="text-blue-400 hover:underline">Datenschutzerklärung</a> zu.
                </div>
            </section>
        </main>
    );
}

export default function RegisterPage() {
    return (
        <Suspense fallback={
            <main role="main" aria-label="Registrierung wird geladen" className="min-h-screen flex items-center justify-center bg-gray-900">
                <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
            </main>
        }>
            <RegisterForm />
        </Suspense>
    );
}

