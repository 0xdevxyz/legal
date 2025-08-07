import React from 'react';
import dynamic from 'next/dynamic';
import { useAuth } from '../contexts/AuthContext';
import Login from '../components/Login';

// Dynamischer Import, um localStorage-Fehler zu vermeiden
const Dashboard = dynamic(() => import('../components/Dashboard'), {
  ssr: false
});

export default function Home() {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="mt-4 text-gray-300">Laden...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return <Dashboard />;
}
