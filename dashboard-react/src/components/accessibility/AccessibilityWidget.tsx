'use client';

import { useEffect } from 'react';
import { useDashboardStore } from '@/stores/dashboard';
import { generateSiteId } from '@/lib/siteIdUtils';

/**
 * Complyo Accessibility Widget Loader
 * 
 * Lädt das Barrierefreiheits-Widget dynamisch basierend auf der
 * aktuell analysierten Website-Domain.
 */
export const AccessibilityWidget: React.FC = () => {
  const { currentWebsite } = useDashboardStore();

  useEffect(() => {
    // Nur laden wenn eine Website analysiert wurde
    if (!currentWebsite?.url) {
      return;
    }

    // ✅ Generiere Site-ID aus URL (z.B. "complyo.tech" -> "complyo-tech")
    const siteId = generateSiteId(currentWebsite.url);

    // Prüfe ob Script bereits existiert
    const existingScript = document.querySelector('script[data-complyo-widget]');
    if (existingScript) {
      existingScript.remove();
    }

    // Erstelle neues Script-Tag
    const script = document.createElement('script');
    script.src = 'https://api.complyo.tech/api/widgets/accessibility.js';
    script.setAttribute('data-site-id', siteId);
    script.setAttribute('data-auto-fix', 'true');
    script.setAttribute('data-show-toolbar', 'true');
    script.setAttribute('data-complyo-widget', 'true'); // Marker für Cleanup
    script.async = true;

    // Füge Script zum Body hinzu
    document.body.appendChild(script);

    console.log('🚀 Complyo Widget geladen für:', {
      website: currentWebsite.url,
      siteId: siteId
    });

    // Cleanup beim Unmount oder wenn Website wechselt
    return () => {
      const scriptToRemove = document.querySelector('script[data-complyo-widget]');
      if (scriptToRemove) {
        scriptToRemove.remove();
      }
    };
  }, [currentWebsite?.url]);

  return null; // Kein visuelles Element, nur Script-Loader
};

