'use client';

import React from 'react';

/**
 * Shared ORION-layout primitives.
 *
 * The app shell (top-nav) is provided globally by SidebarLayout. Pages should
 * render their content inside <PageContainer> so every route shares the same
 * max-width, padding and vertical rhythm as the main dashboard, and inherits
 * the global theme-aware background instead of hardcoding bg-gray-900 etc.
 */

interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
  /** aria-label for the <main> landmark */
  label?: string;
  /** widen/narrow the content column (default: 1600px like the dashboard) */
  width?: '1600' | '1280' | '960' | '720';
}

const WIDTHS: Record<NonNullable<PageContainerProps['width']>, string> = {
  '1600': 'max-w-[1600px]',
  '1280': 'max-w-[1280px]',
  '960': 'max-w-[960px]',
  '720': 'max-w-[720px]',
};

export const PageContainer: React.FC<PageContainerProps> = ({
  children,
  className = '',
  label,
  width = '1600',
}) => (
  <main
    role="main"
    aria-label={label}
    className={`px-4 sm:px-6 py-6 space-y-6 ${WIDTHS[width]} mx-auto w-full ${className}`}
  >
    {children}
  </main>
);

interface PageHeaderProps {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  /** lucide icon component */
  icon?: React.ElementType;
  /** right-aligned actions (buttons etc.) */
  actions?: React.ReactNode;
  /** optional eyebrow / breadcrumb label above the title */
  eyebrow?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  icon: Icon,
  actions,
  eyebrow,
  className = '',
}) => (
  <header
    className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 ${className}`}
  >
    <div className="flex items-center gap-4 min-w-0">
      {Icon && (
        <div
          className="flex-shrink-0 w-12 h-12 rounded-2xl flex items-center justify-center"
          style={{ background: 'var(--lime-dim)', color: 'var(--lime)' }}
        >
          <Icon className="w-6 h-6" />
        </div>
      )}
      <div className="min-w-0">
        {eyebrow && (
          <p className="text-[11px] font-semibold uppercase tracking-wider mb-1 dark:text-zinc-500 text-gray-500">
            {eyebrow}
          </p>
        )}
        <h1 className="text-2xl sm:text-3xl font-black tracking-tight truncate dark:text-white text-gray-900">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm mt-1 dark:text-zinc-400 text-gray-600">{subtitle}</p>
        )}
      </div>
    </div>
    {actions && <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>}
  </header>
);

/** Themed card matching the dashboard's glass-card surface. */
export const PageCard: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`glass-card rounded-2xl p-5 sm:p-6 ${className}`}>{children}</div>
);
