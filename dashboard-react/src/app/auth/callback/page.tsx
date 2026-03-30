'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

/**
 * OAuth Callback Handler
 * Receives tokens from backend OAuth flow and stores them
 */
function AuthCallbackContent() {
  const router = useRouter();
  const { login } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const hash = window.location.hash.slice(1);
      const params = new URLSearchParams(hash);
      const accessToken = params.get('access_token');
      const refreshToken = params.get('refresh_token');

      if (accessToken && refreshToken) {
        // Store tokens
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);

        // Get user info
        try {
          const response = await fetch('https://api.complyo.de/api/auth/me', {
            headers: {
              'Authorization': `Bearer ${accessToken}`
            }
          });

          if (response.ok) {
            const user = await response.json();
            localStorage.setItem('user', JSON.stringify(user));

            // Redirect to dashboard
            router.push('/dashboard');
          } else {
            throw new Error('Failed to fetch user');
          }
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

