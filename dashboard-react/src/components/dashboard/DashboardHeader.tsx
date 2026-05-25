'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useRouter } from 'next/navigation';
import { LogOut, Settings, CreditCard, Sun, Moon, ChevronDown, Bell } from 'lucide-react';
import { SiteSwitcher } from '@/components/dashboard/SiteSwitcher';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

interface DashboardHeaderProps {
  sidebarCollapsed?: boolean;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ sidebarCollapsed }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const router = useRouter();
  const [showDropdown, setShowDropdown] = useState(false);

  const { data: notifData } = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: () => apiClient.get('/api/legal-notifications/stats'),
    staleTime: 60_000,
    retry: false,
  });
  const unreadCount: number = ((notifData as any)?.pending ?? 0) + ((notifData as any)?.critical_pending ?? 0);

  const { data: subData } = useQuery({
    queryKey: ['subscription-status-header'],
    queryFn: () => apiClient.get('/api/stripe/subscription-status'),
    staleTime: 30_000,
    retry: false,
  });
  const activePlanType: string = (subData as any)?.plan_type ?? user?.plan_type ?? 'free';

  const handleLogout = async () => {
    setShowDropdown(false);
    await logout();
  };

  const planLabel = (plan?: string) => {
    switch (plan) {
      case 'pro': return 'Pro-Paket';
      case 'agency': return 'Agentur';
      case 'single': return 'Einzelne Säule';
      case 'expert': return 'Expertenservice';
      case 'update': return 'Updateservice';
      default: return 'Kostenlos';
    }
  };

  return (
    <header
      role="banner"
      style={{
        height: '64px',
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}
      className="dark:bg-[rgba(12,10,9,0.92)] bg-white/95 dark:border-b dark:border-white/[0.06] border-b border-gray-200/80"
    >
      {/* Left: Site Switcher */}
      <div className="flex-1 flex items-center">
        <SiteSwitcher />
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl dark:hover:bg-white/5 hover:bg-gray-100 dark:text-zinc-400 text-gray-500 hover:text-gray-800 dark:hover:text-white transition-all duration-200"
          aria-label={theme === 'dark' ? 'Zu hellem Theme wechseln' : 'Zu dunklem Theme wechseln'}
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-blue-500" />
          )}
        </button>

        {/* Notification bell */}
        <button
          className="p-2 rounded-xl dark:hover:bg-white/5 hover:bg-gray-100 dark:text-zinc-400 text-gray-500 dark:hover:text-white hover:text-gray-800 transition-all duration-200 relative"
          aria-label={`Benachrichtigungen${unreadCount > 0 ? ` (${unreadCount} ungelesen)` : ''}`}
          onClick={() => router.push('/settings?tab=notifications')}
        >
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 min-w-[16px] h-4 rounded-full bg-orange-500 text-white text-[9px] font-bold flex items-center justify-center px-0.5">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* User avatar + dropdown */}
        {user && (
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-xl dark:hover:bg-white/5 hover:bg-gray-100 transition-all duration-200"
              aria-expanded={showDropdown}
            >
              <div className="relative">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-purple-500 flex items-center justify-center font-bold text-white text-sm shadow-lg ring-2 dark:ring-white/10 ring-gray-200">
                  {user.full_name?.charAt(0).toUpperCase() || user.email?.charAt(0).toUpperCase()}
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 border-2 dark:border-zinc-900 border-white rounded-full" />
              </div>
              <div className="hidden md:flex flex-col items-start">
                <span className="text-xs font-semibold leading-tight max-w-[120px] truncate dark:text-white text-gray-900">
                  {user.full_name || user.email}
                </span>
                <span className="text-[10px] leading-tight dark:text-zinc-500 text-gray-500">{planLabel(activePlanType)}</span>
              </div>
              <ChevronDown
                className={`w-3.5 h-3.5 dark:text-zinc-500 text-gray-400 transition-transform duration-200 ${showDropdown ? 'rotate-180' : ''}`}
              />
            </button>

            {showDropdown && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowDropdown(false)} />
                <div className="absolute right-0 mt-2 w-56 rounded-2xl shadow-2xl z-20 overflow-hidden animate-slide-down border dark:bg-zinc-900 dark:border-zinc-800 bg-white border-gray-200">
                  <div className="px-4 py-3 border-b dark:border-zinc-800 border-gray-100 dark:bg-zinc-900/80 bg-gray-50">
                    <p className="text-sm font-semibold truncate dark:text-white text-gray-900">{user.full_name || user.email}</p>
                    <p className="text-xs mt-0.5 dark:text-zinc-500 text-gray-500">{user.email}</p>
                  </div>

                  <div className="py-1.5">
                    <button
                      onClick={() => { router.push('/profile'); setShowDropdown(false); }}
                      className="w-full px-4 py-2.5 text-left text-sm dark:text-zinc-300 text-gray-700 dark:hover:bg-white/5 hover:bg-gray-50 flex items-center gap-3 transition-colors"
                    >
                      <Settings className="w-4 h-4 dark:text-zinc-500 text-gray-400" />
                      Profil & Einstellungen
                    </button>
                    <button
                      onClick={() => { router.push('/subscription'); setShowDropdown(false); }}
                      className="w-full px-4 py-2.5 text-left text-sm dark:text-zinc-300 text-gray-700 dark:hover:bg-white/5 hover:bg-gray-50 flex items-center gap-3 transition-colors"
                    >
                      <CreditCard className="w-4 h-4 dark:text-zinc-500 text-gray-400" />
                      Abo & Rechnung
                    </button>
                  </div>

                  <div className="border-t dark:border-zinc-800 border-gray-100 py-1.5">
                    <button
                      onClick={() => { handleLogout(); setShowDropdown(false); }}
                      className="w-full px-4 py-2.5 text-left text-sm text-red-500 dark:hover:bg-red-500/10 hover:bg-red-50 flex items-center gap-3 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Abmelden
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
