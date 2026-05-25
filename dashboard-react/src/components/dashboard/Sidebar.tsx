'use client';

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Cookie,
  Eye,
  Sparkles,
  FileText,
  Building2,
  Settings,
  CreditCard,
  ChevronLeft,
  ChevronRight,
  Shield,
} from 'lucide-react';

interface SidebarItem {
  label: string;
  icon: React.ElementType;
  href: string;
}

const NAV_ITEMS: SidebarItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/' },
  { label: 'Cookie-Compliance', icon: Cookie, href: '/cookie-compliance' },
  { label: 'Barrierefreiheit', icon: Eye, href: '/accessibility/statement' },
  { label: 'AI-Compliance', icon: Sparkles, href: '/ai-compliance' },
  { label: 'Dokumente', icon: FileText, href: '/docs/cms' },
  { label: 'Agentur', icon: Building2, href: '/agency' },
];

const BOTTOM_ITEMS: SidebarItem[] = [
  { label: 'Einstellungen', icon: Settings, href: '/settings' },
  { label: 'Abo & Rechnung', icon: CreditCard, href: '/subscription' },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const router = useRouter();
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <nav
      className={`sidebar-nav${collapsed ? ' collapsed' : ''}`}
      aria-label="Hauptnavigation"
    >
      {/* Logo area */}
      <div
        className="flex items-center justify-between px-4 py-4 border-b border-white/[0.06]"
        style={{ height: 'var(--topbar-height)' }}
      >
        {!collapsed && (
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => router.push('/')}>
            <Shield className="w-6 h-6 text-orange-500 flex-shrink-0" />
            <span className="font-bold text-white text-base tracking-tight">Complyo</span>
          </div>
        )}
        {collapsed && (
          <div className="mx-auto cursor-pointer" onClick={() => router.push('/')}>
            <Shield className="w-6 h-6 text-orange-500" />
          </div>
        )}
        {!collapsed && (
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg hover:bg-white/5 text-zinc-400 hover:text-white transition-colors"
            aria-label="Sidebar einklappen"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Collapsed toggle */}
      {collapsed && (
        <button
          onClick={onToggle}
          className="mx-auto mt-3 p-1.5 rounded-lg hover:bg-white/5 text-zinc-400 hover:text-white transition-colors flex"
          aria-label="Sidebar ausklappen"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      )}

      {/* Main nav */}
      <div className="flex-1 py-4 overflow-y-auto overflow-x-hidden">
        {!collapsed && (
          <div className="px-4 mb-2">
            <span className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600">Menü</span>
          </div>
        )}
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <button
              key={item.href}
              onClick={() => router.push(item.href)}
              className={`sidebar-item w-full text-left${active ? ' active' : ''}`}
              title={collapsed ? item.label : undefined}
              aria-current={active ? 'page' : undefined}
            >
              <Icon className={`sidebar-item-icon flex-shrink-0 ${active ? 'text-orange-500' : ''}`} />
              <span className="sidebar-item-label">{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Bottom items */}
      <div className="border-t border-white/[0.06] py-3">
        {!collapsed && (
          <div className="px-4 mb-2">
            <span className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600">Account</span>
          </div>
        )}
        {BOTTOM_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <button
              key={item.href}
              onClick={() => router.push(item.href)}
              className={`sidebar-item w-full text-left${active ? ' active' : ''}`}
              title={collapsed ? item.label : undefined}
              aria-current={active ? 'page' : undefined}
            >
              <Icon className={`sidebar-item-icon flex-shrink-0 ${active ? 'text-orange-500' : ''}`} />
              <span className="sidebar-item-label">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
