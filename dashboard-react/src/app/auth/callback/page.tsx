'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { setAccessToken } from '@/lib/auth-refresh';
import { apiClient } from '@/lib/api-client';

function AuthCallbackContent() {
  const router = useRouter();

  useEffect(() => {
    const handleCallback = async () => {
      const hash = window.location.hash.slice(1);
      const params = new URLSearchParams(hash);
      const accessToken = params.get('access_token');

      if (accessToken) {
        setAccessToken(accessToken);

        try {
          const user = await apiClient.get('/api/auth/me');
          try { localStorage.setItem('user', JSON.stringify(user)); } catch {}
          router.push('/dashboard');
        } catch (error) {
          console.error('OAuth callback error:', error);
          router.push('/login?error=oauth_failed');
        }
      } else {
        router.push('/login?error=no_tokens');
      }
    };

    handleCallback();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-white">Login wird verarbeitet...</p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <AuthCallbackContent />
  );
}
