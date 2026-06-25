'use client';

import React, { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useComploaiGuard } from '@/hooks/useComploaiGuard';
import { SiteSwitcher } from '@/components/dashboard/SiteSwitcher';
import {
  LayoutDashboard,
  Cookie,
  Eye,
  Sparkles,
  FileText,
  Building2,
  Settings,
  CreditCard,
  Shield,
  Sun,
  Moon,
  Bell,
  LogOut,
  Menu,
  X,
  Lock,
  Route,
  ScanLine,
  Globe,
  ListChecks,
  Package,
  BookOpen,
} from 'lucide-react';

interface NavItem {
  label: string;
  icon: React.ElementType;
  href: string;
  // Gated behind the comploai_guard add-on; shown with a lock and routed to the
  // upsell until the add-on is active.
  requiresComploaiGuard?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/' },
  { label: 'Journey', icon: Route, href: '/journey' },
  { label: 'Cookies', icon: Cookie, href: '/cookie-compliance' },
  { label: 'Deep Scan', icon: ScanLine, href: '/deep-cookie-scanner' },
  { label: 'Barrierefreiheit', icon: Eye, href: '/accessibility/statement' },
  { label: 'AI-Compliance', icon: Sparkles, href: '/ai-compliance', requiresComploaiGuard: true },
  { label: 'Dokumente', icon: FileText, href: '/docs/cms' },
  { label: 'Agentur', icon: Building2, href: '/agency' },
];

// Secondary destinations — surfaced in the avatar popover and the mobile drawer.
const ACCOUNT_ITEMS: NavItem[] = [
  { label: 'Rechts-Wissen', icon: BookOpen, href: '/knowledge' },
  { label: 'Alt-Text Review', icon: ListChecks, href: '/accessibility/review' },
  { label: 'EU-Vergleich', icon: Globe, href: '/compliance/countries' },
  { label: 'Add-ons', icon: Package, href: '/dashboard/addons' },
  { label: 'Einstellungen', icon: Settings, href: '/settings' },
  { label: 'Abo & Rechnung', icon: CreditCard, href: '/subscription' },
];

export const Sidebar: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { hasComploaiGuard } = useComploaiGuard();
  const [showAccount, setShowAccount] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const navTarget = (item: NavItem) =>
    item.requiresComploaiGuard && !hasComploaiGuard ? '/ai-compliance/upgrade' : item.href;
  const isLocked = (item: NavItem) => !!item.requiresComploaiGuard && !hasComploaiGuard;

  const { data: notifData } = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: () => apiClient.get('/api/legal-notifications/stats'),
    staleTime: 60_000,
    retry: false,
  });
  const unreadCount: number =
    ((notifData as any)?.pending ?? 0) + ((notifData as any)?.critical_pending ?? 0);

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
  const activePlanType: string = user?.plan_type ?? 'free';

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  const handleLogout = async () => {
    setShowAccount(false);
    await logout();
  };

  const go = (href: string) => {
    router.push(href);
    setShowMobileMenu(false);
  };

  return (
    <>
      {/* Mobile top strip — only the hamburger + logo (lg: hidden) */}
      <div className="rail-mobilebar lg:hidden">
        <button
          onClick={() => go('/')}
          className="flex items-center gap-2"
          aria-label="Zum Dashboard"
        >
          <Shield className="w-6 h-6" style={{ color: 'var(--lime)' }} />
          <span className="font-black text-base tracking-tight dark:text-white text-gray-900">
            Complyo
          </span>
        </button>
        <button
          onClick={() => setShowMobileMenu(true)}
          className="p-2 rounded-xl dark:hover:bg-white/5 hover:bg-gray-100 dark:text-zinc-300 text-gray-600"
          aria-label="Menü öffnen"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* Desktop icon rail (lg+) */}
      <nav className="rail hidden lg:flex" role="navigation" aria-label="Hauptnavigation">
        {/* Logo */}
        <button
          onClick={() => go('/')}
          className="rail-logo"
          aria-label="Zum Dashboard"
        >
          <Shield className="w-6 h-6" style={{ color: 'var(--lime)' }} />
        </button>

        {/* Primary nav */}
        <div className="rail-group">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            const locked = isLocked(item);
            return (
              <button
                key={item.href}
                onClick={() => go(navTarget(item))}
                className={`rail-item${active ? ' active' : ''}`}
                aria-label={item.label}
                aria-current={active ? 'page' : undefined}
              >
                <Icon className="rail-icon" />
                {locked && <Lock className="rail-lock" aria-hidden />}
                <span className="rail-tooltip">{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Bottom cluster */}
        <div className="rail-group rail-bottom">
          {/* Agency-only site switcher (renders null for non-agency users) */}
          <div className="rail-siteswitcher">
            <SiteSwitcher />
          </div>

          {/* Notifications */}
          <button
            onClick={() => router.push('/settings?tab=notifications')}
            className="rail-item"
            aria-label={`Benachrichtigungen${unreadCount > 0 ? ` (${unreadCount} ungelesen)` : ''}`}
          >
            <Bell className="rail-icon" />
            {unreadCount > 0 && (
              <span
                className="rail-badge"
                style={{ background: 'var(--lime)' }}
              >
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
            <span className="rail-tooltip">Benachrichtigungen</span>
          </button>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="rail-item"
            aria-label={theme === 'dark' ? 'Helles Theme' : 'Dunkles Theme'}
          >
            {theme === 'dark' ? (
              <Sun className="rail-icon text-amber-400" />
            ) : (
              <Moon className="rail-icon text-zinc-600" />
            )}
            <span className="rail-tooltip">{theme === 'dark' ? 'Helles Theme' : 'Dunkles Theme'}</span>
          </button>

          {/* Avatar + account popover */}
          {user && (
            <div className="relative">
              <button
                onClick={() => setShowAccount(!showAccount)}
                className="rail-avatar-btn"
                aria-label="Konto-Menü"
                aria-expanded={showAccount}
              >
                <div className="relative">
                  <div
                    className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm text-zinc-950 ring-2 dark:ring-white/10 ring-gray-200"
                    style={{ background: 'var(--lime)' }}
                  >
                    {user.full_name?.charAt(0).toUpperCase() ||
                      user.email?.charAt(0).toUpperCase()}
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 border-2 dark:border-zinc-900 border-white rounded-full" />
                </div>
              </button>

              {showAccount && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowAccount(false)} />
                  <div className="absolute bottom-0 left-full ml-3 w-56 rounded-2xl shadow-2xl z-20 overflow-hidden border dark:bg-zinc-900 dark:border-zinc-800 bg-white border-gray-200">
                    <div className="px-4 py-3 border-b dark:border-zinc-800 border-gray-100 dark:bg-zinc-900/80 bg-gray-50">
                      <p className="text-sm font-semibold truncate dark:text-white text-gray-900">
                        {user.full_name || user.email}
                      </p>
                      <p className="text-xs mt-0.5 dark:text-zinc-500 text-gray-500">
                        {planLabel(activePlanType)}
                      </p>
                    </div>
                    <div className="py-1.5">
                      {ACCOUNT_ITEMS.map((item) => {
                        const Icon = item.icon;
                        return (
                          <button
                            key={item.href}
                            onClick={() => { router.push(item.href); setShowAccount(false); }}
                            className="w-full px-4 py-2.5 text-left text-sm dark:text-zinc-300 text-gray-700 dark:hover:bg-white/5 hover:bg-gray-50 flex items-center gap-3 transition-colors"
                          >
                            <Icon className="w-4 h-4 dark:text-zinc-500 text-gray-400" />
                            {item.label}
                          </button>
                        );
                      })}
                    </div>
                    <div className="border-t dark:border-zinc-800 border-gray-100 py-1.5">
                      <button
                        onClick={handleLogout}
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
      </nav>

      {/* Mobile drawer */}
      {showMobileMenu && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/60" onClick={() => setShowMobileMenu(false)} />
          <div className="absolute top-0 left-0 h-full w-72 max-w-[85vw] dark:bg-zinc-950 bg-white border-r dark:border-white/10 border-gray-200 p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <span className="font-black text-lg dark:text-white text-gray-900">Menü</span>
              <button
                onClick={() => setShowMobileMenu(false)}
                className="p-2 rounded-xl dark:hover:bg-white/5 hover:bg-gray-100 dark:text-zinc-400 text-gray-500"
                aria-label="Menü schließen"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="mb-4">
              <SiteSwitcher />
            </div>
            <div className="space-y-1">
              {[...NAV_ITEMS, ...ACCOUNT_ITEMS].map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                const locked = isLocked(item);
                return (
                  <button
                    key={item.href}
                    onClick={() => go(navTarget(item))}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                      active
                        ? 'text-zinc-950'
                        : 'dark:text-zinc-300 text-gray-700 dark:hover:bg-white/5 hover:bg-gray-100'
                    }`}
                    style={active ? { background: 'var(--lime)' } : undefined}
                    aria-current={active ? 'page' : undefined}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                    {locked && <Lock className="w-3.5 h-3.5 ml-auto opacity-60" aria-label="Add-on erforderlich" />}
                  </button>
                );
              })}
            </div>
            <div className="border-t dark:border-zinc-800 border-gray-100 mt-4 pt-3">
              <button
                onClick={async () => { setShowMobileMenu(false); await logout(); }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-red-500 dark:hover:bg-red-500/10 hover:bg-red-50 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Abmelden
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
