'use client';

import { useState, Suspense, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter, useSearchParams } from 'next/navigation';
import { Shield, CheckCircle, Loader2, AlertCircle, Eye, FileText, BarChart3, Crown } from 'lucide-react';
import SocialLoginButtons from '@/components/SocialLoginButtons';
import { Logo } from '@/components/Logo';

const getApiBase = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8002';
    }
    if (hostname.includes('complyo.tech')) {
      return 'https://api.complyo.tech';
    }
  }
  return 'http://localhost:8002';
};

const API_BASE = getApiBase();

const MODULES = [
    { id: 'cookie', name: 'Cookie & DSGVO', icon: Shield, description: 'Cookie-Banner, Consent-Management' },
    { id: 'accessibility', name: 'Barrierefreiheit', icon: Eye, description: 'WCAG 2.1 AA Scanner & Fixes' },
    { id: 'legal_texts', name: 'Rechtliche Texte', icon: FileText, description: 'Impressum, Datenschutz, AGB' },
    { id: 'monitoring', name: 'Monitoring', icon: BarChart3, description: 'Automatische Scans & Alerts' },
];

function RegisterForm() {
    const { register } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();
    const initialPlan = searchParams?.get('plan') || 'complete';
    const initialModule = searchParams?.get('module') || '';
    
    const [plan, setPlan] = useState(initialPlan);
    const [selectedModules, setSelectedModules] = useState<string[]>(
        initialModule ? [initialModule] : (initialPlan === 'single' ? [] : ['cookie', 'accessibility', 'legal_texts', 'monitoring'])
    );
    
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        full_name: '',
        company: '',
    });
    
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    
    useEffect(() => {
        if (plan === 'complete') {
            setSelectedModules(['cookie', 'accessibility', 'legal_texts', 'monitoring']);
        } else if (plan === 'expert') {
            setSelectedModules(['cookie', 'accessibility', 'legal_texts', 'monitoring']);
        }
    }, [plan]);
    
    const toggleModule = (moduleId: string) => {
        if (plan !== 'single') return;
        setSelectedModules(prev => 
            prev.includes(moduleId) 
                ? prev.filter(m => m !== moduleId)
                : [...prev, moduleId]
        );
    };
    
    const calculatePrice = () => {
        if (plan === 'expert') return { monthly: 39, setup: 2990 };
        if (plan === 'complete') return { monthly: 49, setup: 0 };
        return { monthly: selectedModules.length * 19, setup: 0 };
    };
    
    const price = calculatePrice();
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        
        if (plan === 'single' && selectedModules.length === 0) {
            setError('Bitte wählen Sie mindestens ein Modul aus.');
            return;
        }
        
        setIsSubmitting(true);
        
        try {
            await register({ ...formData, plan, modules: selectedModules });
            
            const checkoutResponse = await fetch(`${API_BASE}/api/payment/create-checkout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    plan_type: plan,
                    modules: selectedModules
                })
            });
            
            if (!checkoutResponse.ok) {
                throw new Error('Fehler beim Erstellen der Zahlungssitzung');
            }
            
            const { checkout_url } = await checkoutResponse.json();
            window.location.href = checkout_url;
        } catch (error: any) {
            console.error('Registration error:', error);
            setError(error.message || 'Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut.');
            setIsSubmitting(false);
        }
    };
    
    const getPlanName = () => {
        if (plan === 'expert') return 'Expertenservice';
        if (plan === 'complete') return 'Komplett-Paket';
        return `Einzelmodul${selectedModules.length > 1 ? 'e' : ''}`;
    };
    
    const getPriceDisplay = () => {
        if (price.setup > 0) {
            return `${price.setup.toLocaleString('de-DE')}€ + ${price.monthly}€/Monat`;
        }
        return `${price.monthly}€/Monat`;
    };
    
    return (
        <main role="main" aria-label="Registrierung" className="min-h-screen flex items-center justify-center bg-gray-900 px-4 py-8">
            <section className="bg-gray-800 p-8 rounded-lg max-w-lg w-full border border-gray-700 shadow-xl">
                <div className="flex items-center justify-center mb-6">
                    <Logo size="xl" />
                </div>
                
                <h1 className="text-3xl font-bold mb-2 text-center">Jetzt registrieren</h1>
                
                <div className="mb-6">
                    <label className="block text-sm font-medium mb-3 text-gray-300">Plan auswählen</label>
                    <div className="grid grid-cols-3 gap-2">
                        <button
                            type="button"
                            onClick={() => setPlan('single')}
                            className={`p-3 rounded-lg border text-center transition-all ${
                                plan === 'single' 
                                    ? 'border-blue-500 bg-blue-500/20 text-blue-400' 
                                    : 'border-gray-600 hover:border-gray-500 text-gray-400'
                            }`}
                        >
                            <div className="text-sm font-semibold">Einzelmodul</div>
                            <div className="text-xs mt-1">19€/Säule</div>
                        </button>
                        <button
                            type="button"
                            onClick={() => setPlan('complete')}
                            className={`p-3 rounded-lg border text-center transition-all relative ${
                                plan === 'complete' 
                                    ? 'border-purple-500 bg-purple-500/20 text-purple-400' 
                                    : 'border-gray-600 hover:border-gray-500 text-gray-400'
                            }`}
                        >
                            <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-[10px] px-2 py-0.5 rounded-full">Beliebt</div>
                            <div className="text-sm font-semibold">Komplett</div>
                            <div className="text-xs mt-1">49€/Monat</div>
                        </button>
                        <button
                            type="button"
                            onClick={() => setPlan('expert')}
                            className={`p-3 rounded-lg border text-center transition-all ${
                                plan === 'expert' 
                                    ? 'border-yellow-500 bg-yellow-500/20 text-yellow-400' 
                                    : 'border-gray-600 hover:border-gray-500 text-gray-400'
                            }`}
                        >
                            <Crown className="w-4 h-4 mx-auto mb-1" />
                            <div className="text-sm font-semibold">Expert</div>
                            <div className="text-xs mt-1">2.990€+</div>
                        </button>
                    </div>
                </div>
                
                {plan === 'single' && (
                    <div className="mb-6">
                        <label className="block text-sm font-medium mb-3 text-gray-300">
                            Module auswählen <span className="text-gray-500">(19€ pro Modul/Monat)</span>
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            {MODULES.map((module) => {
                                const Icon = module.icon;
                                const isSelected = selectedModules.includes(module.id);
                                return (
                                    <button
                                        key={module.id}
                                        type="button"
                                        onClick={() => toggleModule(module.id)}
                                        className={`p-3 rounded-lg border text-left transition-all ${
                                            isSelected 
                                                ? 'border-blue-500 bg-blue-500/10' 
                                                : 'border-gray-600 hover:border-gray-500'
                                        }`}
                                    >
                                        <div className="flex items-center gap-2 mb-1">
                                            <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                                                isSelected ? 'bg-blue-500 border-blue-500' : 'border-gray-500'
                                            }`}>
                                                {isSelected && <CheckCircle className="w-3 h-3 text-white" />}
                                            </div>
                                            <Icon className={`w-4 h-4 ${isSelected ? 'text-blue-400' : 'text-gray-500'}`} />
                                        </div>
                                        <div className={`text-sm font-medium ${isSelected ? 'text-white' : 'text-gray-400'}`}>
                                            {module.name}
                                        </div>
                                        <div className="text-xs text-gray-500">{module.description}</div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                )}
                
                <div className="bg-gray-700/50 rounded-lg p-4 mb-6">
                    <div className="flex justify-between items-center">
                        <div>
                            <div className="text-sm text-gray-400">Ihr Plan</div>
                            <div className="text-lg font-semibold text-white">{getPlanName()}</div>
                            {plan === 'single' && selectedModules.length > 0 && (
                                <div className="text-xs text-gray-500 mt-1">
                                    {selectedModules.map(m => MODULES.find(mod => mod.id === m)?.name).join(', ')}
                                </div>
                            )}
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-bold text-blue-400">{getPriceDisplay()}</div>
                            <div className="text-xs text-gray-500">zzgl. MwSt.</div>
                        </div>
                    </div>
                </div>
                
                {error && (
                    <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-500 rounded flex items-center gap-2 text-red-200">
                        <AlertCircle className="w-5 h-5 flex-shrink-0" />
                        <span className="text-sm">{error}</span>
                    </div>
                )}
                
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
                        disabled={isSubmitting || (plan === 'single' && selectedModules.length === 0)}
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
