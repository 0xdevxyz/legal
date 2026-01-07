'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useRouter } from 'next/navigation';
import { Shield, LogOut, User, Sparkles, ChevronDown, Settings, CreditCard, Sun, Moon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Logo } from '@/components/Logo';

export const DashboardHeader: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const router = useRouter();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <header className="glass-strong sticky top-0 z-50">
      <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Logo size="lg" onClick={() => router.push('/')} />

          {/* User Info & Actions */}
          <div className="flex items-center gap-4">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="relative p-3 glass-card hover:glass-strong rounded-xl transition-all duration-300 hover:scale-105 group"
              aria-label={theme === 'dark' ? 'Zu hellem Theme wechseln' : 'Zu dunklem Theme wechseln'}
            >
              <div className="relative w-5 h-5">
                {/* Sun Icon (Light Mode) */}
                <Sun 
                  className={`absolute inset-0 w-5 h-5 text-amber-400 transition-all duration-300 ${
                    theme === 'light' 
                      ? 'opacity-100 rotate-0 scale-100' 
                      : 'opacity-0 rotate-90 scale-50'
                  }`}
                />
                {/* Moon Icon (Dark Mode) */}
                <Moon 
                  className={`absolute inset-0 w-5 h-5 text-blue-400 transition-all duration-300 ${
                    theme === 'dark' 
                      ? 'opacity-100 rotate-0 scale-100' 
                      : 'opacity-0 -rotate-90 scale-50'
                  }`}
                />
              </div>
              
              {/* Glow Effect */}
              <div className={`absolute inset-0 rounded-xl blur-md opacity-0 group-hover:opacity-30 transition-opacity duration-300 ${
                theme === 'dark' 
                  ? 'bg-blue-400' 
                  : 'bg-amber-400'
              }`}></div>
            </button>

            {/* User Dropdown */}
            {user && (
              <div className="relative">
                <button
                  onClick={() => setShowDropdown(!showDropdown)}
                  className="flex items-center gap-3 px-4 py-2.5 glass-card hover:glass-strong rounded-xl transition-all duration-300 hover:scale-105"
                >
                  <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-sky-400 to-purple-500 flex items-center justify-center font-bold text-white shadow-lg ring-2 ring-white/10 dark:ring-white/10 light:ring-gray-300/30">
                      {user.full_name?.charAt(0).toUpperCase() || user.email?.charAt(0).toUpperCase()}
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 border-2 border-zinc-900 dark:border-zinc-900 light:border-white rounded-full"></div>
                  </div>
                  <div className="hidden md:flex flex-col items-start max-w-[150px]">
                    <span className="text-sm font-semibold text-white dark:text-white light:text-gray-900 truncate" title={user.full_name || user.email}>
                      {user.full_name || user.email}
                    </span>
                    {user.plan_type && (
                      <span className="text-xs text-zinc-400 dark:text-zinc-400 light:text-gray-700 capitalize flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
                        {user.plan_type === 'ai' ? 'AI Plan' : 'Expert Plan'}
                      </span>
                    )}
                  </div>
                  <ChevronDown className={`w-4 h-4 text-zinc-400 dark:text-zinc-400 light:text-gray-700 transition-transform duration-300 ${showDropdown ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown Menu */}
                {showDropdown && (
                  <>
                    {/* Overlay zum Schließen */}
                    <div 
                      className="fixed inset-0 z-10" 
                      onClick={() => setShowDropdown(false)}
                    />
                    
                    <div className="absolute right-0 mt-3 w-64 glass-strong rounded-2xl shadow-2xl z-20 animate-slide-down overflow-hidden">
                      {/* User Info (Mobile) */}
                      <div className="md:hidden px-5 py-4 border-b border-white/10 dark:border-white/10 light:border-gray-200 bg-gradient-to-r from-sky-500/10 to-purple-500/10">
                        <p className="text-sm font-semibold text-white dark:text-white light:text-gray-900 truncate">{user.full_name || user.email}</p>
                        <p className="text-xs text-zinc-400 dark:text-zinc-400 light:text-gray-700 mt-1">{user.email}</p>
                      </div>

                      {/* Menu Items */}
                      <nav aria-label="Benutzer-Navigation" className="py-2">
                        <button
                          onClick={() => {
                            router.push('/profile');
                            setShowDropdown(false);
                          }}
                          className="w-full px-5 py-3 text-left text-sm text-zinc-200 dark:text-zinc-200 light:text-gray-900 hover:bg-white/5 dark:hover:bg-white/5 light:hover:bg-gray-100/70 flex items-center gap-3 transition-all duration-200 group"
                        >
                          <div className="p-2 rounded-lg bg-zinc-800/50 dark:bg-zinc-800/50 light:bg-gray-100 group-hover:bg-sky-500/20 transition-colors">
                            <Settings className="w-4 h-4 text-zinc-400 dark:text-zinc-400 light:text-gray-700 group-hover:text-sky-400 transition-colors" />
                          </div>
                          <div>
                            <div className="font-medium text-zinc-200 dark:text-zinc-200 light:text-gray-900">Profil & Einstellungen</div>
                            <div className="text-xs text-zinc-500 dark:text-zinc-500 light:text-gray-600">Account verwalten</div>
                          </div>
                        </button>
                        
                        <button
                          onClick={() => {
                            router.push('/subscription');
                            setShowDropdown(false);
                          }}
                          className="w-full px-5 py-3 text-left text-sm text-zinc-200 dark:text-zinc-200 light:text-gray-900 hover:bg-white/5 dark:hover:bg-white/5 light:hover:bg-gray-100/70 flex items-center gap-3 transition-all duration-200 group"
                        >
                          <div className="p-2 rounded-lg bg-zinc-800/50 dark:bg-zinc-800/50 light:bg-gray-100 group-hover:bg-purple-500/20 transition-colors">
                            <CreditCard className="w-4 h-4 text-zinc-400 dark:text-zinc-400 light:text-gray-700 group-hover:text-purple-400 transition-colors" />
                          </div>
                          <div>
                            <div className="font-medium text-zinc-200 dark:text-zinc-200 light:text-gray-900">Abo & Rechnung</div>
                            <div className="text-xs text-zinc-500 dark:text-zinc-500 light:text-gray-600">Zahlungen verwalten</div>
                          </div>
                        </button>
                      </nav>

                      {/* Logout */}
                      <div className="border-t border-white/10 dark:border-white/10 light:border-gray-200 py-2">
                        <button
                          onClick={() => {
                            handleLogout();
                            setShowDropdown(false);
                          }}
                          className="w-full px-5 py-3 text-left text-sm text-red-400 dark:text-red-400 light:text-red-600 hover:bg-red-500/10 flex items-center gap-3 transition-all duration-200 group"
                        >
                          <div className="p-2 rounded-lg bg-zinc-800/50 dark:bg-zinc-800/50 light:bg-red-100 group-hover:bg-red-500/20 transition-colors">
                            <LogOut className="w-4 h-4" />
                          </div>
                          <span className="font-medium">Abmelden</span>
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

