import React from 'react';
import Register from '../components/Register';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/router';

export default function RegisterPage() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (isAuthenticated && !loading) {
      router.push('/');
    }
  }, [isAuthenticated, loading, router]);

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

  if (isAuthenticated) {
    return null; // Wird zum Dashboard weitergeleitet
  }

  return <Register />;
}
