'use client';

import React, { useEffect, useState } from 'react';
import { Lock, Unlock, RefreshCw, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface DomainLock {
  domain_name: string;
  fixes_used: number;
  fixes_limit: number;
  is_unlocked: boolean;
  created_at: string;
  unlocked_at?: string;
}

interface DomainLockStatusProps {
  refreshTrigger?: number; // Prop zum Triggern eines Refreshs
}

export const DomainLockStatus: React.FC<DomainLockStatusProps> = ({ refreshTrigger }) => {
  const [locks, setLocks] = useState<DomainLock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDomainLocks();
  }, [refreshTrigger]);

  const fetchDomainLocks = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Nicht angemeldet');
        return;
      }

      const response = await axios.get('/api/user/domain-locks', {
        baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.success) {
        setLocks(response.data.domain_locks || []);
      }
    } catch (err: any) {
      console.error('Failed to fetch domain locks:', err);
      setError(err.response?.data?.detail || 'Fehler beim Laden der Domain-Status');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  if (loading && locks.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600 dark:text-gray-400">Lade Domain-Status...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white flex items-center gap-2">
          <Lock className="w-5 h-5 text-blue-600" />
          Ihre Domains
        </h3>
        <button
          onClick={fetchDomainLocks}
          disabled={loading}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          title="Aktualisieren"
        >
          <RefreshCw className={`w-4 h-4 text-gray-600 dark:text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-red-800 dark:text-red-300">Fehler</div>
              <div className="text-sm text-red-700 dark:text-red-400">{error}</div>
            </div>
          </div>
        )}

        {locks.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-5xl mb-4">🌐</div>
            <p className="text-gray-500 dark:text-gray-400 mb-2">Noch keine Domains analysiert</p>
            <p className="text-sm text-gray-400 dark:text-gray-500">
              Starten Sie eine Website-Analyse, um Ihre erste Domain hinzuzufügen
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {locks.map((lock, index) => (
              <div
                key={`${lock.domain_name}-${index}`}
                className={`border rounded-lg p-4 transition-all hover:shadow-md ${
                  lock.is_unlocked
                    ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
                    : 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-700/50'
                }`}
              >
                {/* Domain Name & Status Badge */}
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
                    <span className="text-lg">🌐</span>
                    {lock.domain_name}
                  </span>
                  {lock.is_unlocked ? (
                    <span className="px-3 py-1 bg-green-100 dark:bg-green-900/40 border border-green-300 dark:border-green-700 text-green-800 dark:text-green-300 text-xs font-semibold rounded-full flex items-center gap-1.5">
                      <Unlock className="w-3.5 h-3.5" />
                      Unlocked
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-xs font-semibold rounded-full flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5" />
                      Free
                    </span>
                  )}
                </div>

                {/* Fixes Status */}
                <div className="space-y-2">
                  {lock.is_unlocked ? (
                    <div className="text-sm text-green-700 dark:text-green-300 flex items-center gap-2">
                      <span className="text-lg">✨</span>
                      <span className="font-medium">Unbegrenzte Fixes verfügbar</span>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center justify-between mb-1">
                        <span>Fixes verwendet:</span>
                        <span className={`font-semibold ${
                          lock.fixes_used >= lock.fixes_limit
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-gray-800 dark:text-white'
                        }`}>
                          {lock.fixes_used} / {lock.fixes_limit}
                        </span>
                      </div>
                      {/* Progress Bar */}
                      <div className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all ${
                            lock.fixes_used >= lock.fixes_limit
                              ? 'bg-red-500'
                              : 'bg-blue-500'
                          }`}
                          style={{
                            width: `${Math.min((lock.fixes_used / lock.fixes_limit) * 100, 100)}%`
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Dates */}
                  <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 pt-2">
                    <span>Erstellt: {formatDate(lock.created_at)}</span>
                    {lock.unlocked_at && (
                      <span>Freigeschaltet: {formatDate(lock.unlocked_at)}</span>
                    )}
                  </div>
                </div>

                {/* Upgrade Button for Locked Domains */}
                {!lock.is_unlocked && lock.fixes_used >= lock.fixes_limit && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                    <button
                      onClick={() => {
                        // Trigger Paywall Modal
                        // You can emit an event or use a callback

                      }}
                      className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-2 px-4 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2"
                    >
                      <Unlock className="w-4 h-4" />
                      Jetzt upgraden - Unbegrenzte Fixes
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Info Box */}
        {locks.length > 0 && (
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-300">
                <strong>Hinweis:</strong> Jede Domain beginnt mit 1 kostenlosen Fix. 
                Für unbegrenzte Fixes upgraden Sie für 39€/Monat pro Domain.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DomainLockStatus;

