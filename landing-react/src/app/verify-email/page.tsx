'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Check, X, Mail, RefreshCw } from 'lucide-react';

interface VerificationResult {
  success: boolean;
  message: string;
  email?: string;
  name?: string;
  verified_at?: string;
}

const EmailVerificationContent: React.FC = () => {
  const searchParams = useSearchParams();
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const token = searchParams.get('token');
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setError('Kein Verification-Token gefunden.');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE}/api/leads/verify/${token}`);
        const data = await response.json();
        
        if (response.ok) {
          setVerificationResult(data);
        } else {
          setError(data.detail || 'Fehler bei der Verifizierung');
        }
      } catch (err) {
        setError('Netzwerkfehler. Bitte versuchen Sie es später erneut.');
      } finally {
        setIsLoading(false);
      }
    };

    verifyEmail();
  }, [token]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <div className="text-white text-lg font-semibold">Verifiziere E-Mail...</div>
          <div className="text-gray-400 text-sm mt-2">Bitte warten Sie einen Moment</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {verificationResult?.success ? (
          // Success State
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <Check className="w-8 h-8 text-white" />
            </div>
            
            <h1 className="text-2xl font-bold text-white mb-4">
              🎉 E-Mail erfolgreich verifiziert!
            </h1>
            
            <p className="text-gray-300 mb-6">
              Vielen Dank{verificationResult.name ? `, ${verificationResult.name}` : ''}! 
              Ihre E-Mail-Adresse {verificationResult.email} wurde erfolgreich bestätigt.
            </p>
            
            <div className="bg-green-600/20 border border-green-500/30 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-2 text-green-400">
                <Mail className="w-5 h-5" />
                <span className="font-semibold">Report wird gesendet</span>
              </div>
              <p className="text-sm text-gray-300 mt-2">
                Ihr Compliance-Report wird nun automatisch an Ihre E-Mail-Adresse gesendet.
              </p>
            </div>
            
            <div className="text-xs text-gray-400 bg-gray-800/50 p-3 rounded-lg">
              🔒 <strong>Datenschutz:</strong> Ihre Daten werden gemäß DSGVO verarbeitet. 
              Sie können Ihre Einwilligung jederzeit widerrufen.
            </div>
            
            <div className="mt-6">
              <button 
                onClick={() => window.close()}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity text-white"
              >
                Fenster schließen
              </button>
            </div>
          </div>
        ) : (
          // Error State
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-orange-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <X className="w-8 h-8 text-white" />
            </div>
            
            <h1 className="text-2xl font-bold text-white mb-4">
              Verifizierung fehlgeschlagen
            </h1>
            
            <p className="text-red-400 mb-6">
              {error}
            </p>
            
            <div className="bg-yellow-600/20 border border-yellow-500/30 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-yellow-400 mb-2">Mögliche Ursachen:</h3>
              <ul className="text-sm text-gray-300 text-left space-y-1">
                <li>• Der Link ist abgelaufen (24h Gültigkeit)</li>
                <li>• Der Link wurde bereits verwendet</li>
                <li>• Der Link ist ungültig oder beschädigt</li>
              </ul>
            </div>
            
            <div className="space-y-3">
              <button 
                onClick={() => window.location.reload()}
                className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition-colors text-white"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Erneut versuchen</span>
              </button>
              
              <p className="text-xs text-gray-400">
                Bei anhaltenden Problemen kontaktieren Sie uns unter: 
                <a href="mailto:support@complyo.tech" className="text-blue-400 hover:underline">
                  support@complyo.tech
                </a>
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const EmailVerificationPage: React.FC = () => {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <div className="text-white text-lg font-semibold">Lade Verifizierungsseite...</div>
        </div>
      </div>
    }>
      <EmailVerificationContent />
    </Suspense>
  );
};

export default EmailVerificationPage;