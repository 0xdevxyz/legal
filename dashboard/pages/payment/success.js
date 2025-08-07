import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { verifyPayment } from '../../services/payment';
import { useAuth } from '../../contexts/AuthContext';

export default function PaymentSuccess() {
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('Zahlung wird überprüft...');
  const router = useRouter();
  const { session_id } = router.query;
  const { user, logout } = useAuth();
  
  useEffect(() => {
    if (!session_id) return;
    
    const checkPayment = async () => {
      try {
        const result = await verifyPayment(session_id);
        setStatus(result.status);
        setMessage(result.message);
        
        // Bei erfolgreicher Zahlung den Benutzer kurz ausloggen und neu einloggen,
        // damit die neuen Abonnementdaten geladen werden
        if (result.status === 'success') {
          setTimeout(() => {
            logout();
            // Nach kurzer Verzögerung zur Hauptseite umleiten, wo der Benutzer sich neu anmelden muss
            setTimeout(() => {
              router.push('/');
            }, 1000);
          }, 3000);
        }
      } catch (error) {
        setStatus('error');
        setMessage('Fehler beim Überprüfen der Zahlung: ' + (error.message || 'Unbekannter Fehler'));
        console.error(error);
      }
    };
    
    checkPayment();
  }, [session_id, router, logout]);
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg max-w-md w-full text-center">
        {status === 'loading' && (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500 mx-auto mb-4"></div>
            <h2 className="text-xl font-bold mb-2 text-white">Zahlung wird verarbeitet</h2>
          </>
        )}
        
        {status === 'success' && (
          <>
            <svg className="h-16 w-16 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <h2 className="text-xl font-bold mb-2 text-white">Zahlung erfolgreich</h2>
          </>
        )}
        
        {status === 'error' && (
          <>
            <svg className="h-16 w-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            <h2 className="text-xl font-bold mb-2 text-white">Fehler</h2>
          </>
        )}
        
        {status === 'pending' && (
          <>
            <svg className="h-16 w-16 text-yellow-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <h2 className="text-xl font-bold mb-2 text-white">Zahlung ausstehend</h2>
          </>
        )}
        
        <p className="text-gray-300 mb-6">{message}</p>
        
        <button 
          onClick={() => router.push('/')}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Zurück zum Dashboard
        </button>
      </div>
    </div>
  );
}
