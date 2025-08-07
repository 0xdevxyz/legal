import React, { useState } from 'react';
import { createCheckoutSession } from '../services/payment';

export default function SubscriptionUpgrade() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleBasicSubscription = async () => {
    await handleSubscription('basic');
  };
  
  const handleExpertSubscription = async () => {
    await handleSubscription('expert');
  };
  
  const handleExpertSetup = async () => {
    await handleSubscription('expert', 'onetime');
  };
  
  const handleSubscription = async (tier, paymentType = 'subscription') => {
    setLoading(true);
    setError(null);
    
    try {
      const session = await createCheckoutSession(tier, paymentType);
      // Zum Stripe Checkout weiterleiten
      window.location.href = session.checkout_url;
    } catch (err) {
      setError('Fehler beim Erstellen der Zahlungssession: ' + (err.message || 'Unbekannter Fehler'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Abonnement upgraden</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-900 text-red-200 rounded-md">
          {error}
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-750 rounded-lg p-6 border border-indigo-800">
          <h3 className="text-lg font-bold mb-2 text-indigo-400">KI-Automatisierung</h3>
          <p className="text-gray-300 mb-4">Vollautomatische Compliance-Lösungen für Ihre Website</p>
          
          <ul className="space-y-2 mb-6">
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>Unbegrenzte Compliance-Scans</span>
            </li>
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>KI-generierte Rechtstexte</span>
            </li>
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>Cookie-Banner-Implementation</span>
            </li>
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>Monatliche Re-Scans</span>
            </li>
          </ul>
          
          <div className="mb-4">
            <span className="text-2xl font-bold">39€</span>
            <span className="text-gray-400">/Monat</span>
          </div>
          
          <button
            onClick={handleBasicSubscription}
            disabled={loading}
            className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {loading ? 'Wird bearbeitet...' : 'Jetzt upgraden'}
          </button>
        </div>
        
        <div className="bg-gray-750 rounded-lg p-6 border border-purple-800">
          <h3 className="text-lg font-bold mb-2 text-purple-400">Experten-Service</h3>
          <p className="text-gray-300 mb-4">Persönliche Betreuung durch Compliance-Experten</p>
          
          <ul className="space-y-2 mb-6">
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>Alle Features der KI-Automatisierung</span>
            </li>
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>Persönliche Experten-Betreuung</span>
            </li>
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>Deep-Dive Compliance-Audit</span>
            </li>
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>Branchenspezifische Compliance</span>
            </li>
          </ul>
          
          <div className="mb-4">
            <span className="text-2xl font-bold">2.000€</span>
            <span className="text-gray-400"> Einrichtung + </span>
            <span className="text-xl font-bold">39€</span>
            <span className="text-gray-400">/Monat</span>
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleExpertSetup}
              disabled={loading}
              className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              Setup zahlen
            </button>
            <button
              onClick={handleExpertSubscription}
              disabled={loading}
              className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              Nur Abo
            </button>
          </div>
        </div>
      </div>
      
      <p className="text-sm text-gray-400 text-center">
        Sicher bezahlen mit Stripe. Jederzeit kündbar.
      </p>
    </div>
  );
}
