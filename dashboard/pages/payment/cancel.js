import React from 'react';
import { useRouter } from 'next/router';

export default function PaymentCancel() {
  const router = useRouter();
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg max-w-md w-full text-center">
        <svg className="h-16 w-16 text-yellow-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
        </svg>
        
        <h2 className="text-xl font-bold mb-2 text-white">Zahlung abgebrochen</h2>
        <p className="text-gray-300 mb-6">
          Ihre Zahlungstransaktion wurde abgebrochen. Es wurde keine Zahlung ausgeführt.
        </p>
        
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
