/**
 * Grundsystem (CMS) der Kundenwebsite und der passende Einrichtungsweg.
 *
 * Der Cookie-Scan (POST /api/cookie-compliance/scan) und die Abfrage
 * GET /api/cookie-compliance/grundsystem liefern beide dieselben Felder;
 * die Quelle ist backend/compliance_engine/grundsystem.py.
 */

export interface Grundsystem {
  /** Anzeigename, z.B. "WordPress", oder null wenn nichts erkannt */
  detected_cms: string | null;
  /** Kleinschreibung, "html" wenn nichts erkannt */
  cms_key: string;
  /** "plugin": fertiges Paket zum Hochladen, "snippet": Schnipsel in den <head> */
  einrichtung: 'plugin' | 'snippet';
  /** Pfad unter der API, nur bei "plugin" */
  plugin_download_pfad: string | null;
  /** Ein Satz, wo Paket bzw. Schnipsel hingehoert */
  anleitung: string;
}

export const API_BASE = 'https://api.complyo.de';

export function istGrundsystem(x: any): x is Grundsystem {
  return !!x && typeof x === 'object' && typeof x.cms_key === 'string' && typeof x.einrichtung === 'string';
}

export function pluginDownloadUrl(g: Grundsystem | null | undefined): string | null {
  if (!g || g.einrichtung !== 'plugin' || !g.plugin_download_pfad) return null;
  return `${API_BASE}${g.plugin_download_pfad}`;
}

/** Welcher Tab im Integrations-Guide zum Grundsystem gehoert. */
export function integrationsTab(g: Grundsystem | null | undefined): 'wordpress' | 'joomla' | 'shopify' | 'html' {
  const key = g?.cms_key || 'html';
  if (key === 'wordpress' || key === 'joomla' || key === 'shopify') return key;
  return 'html';
}

/** Schritte fuer den Plugin-Weg, je Grundsystem. */
export function pluginSchritte(g: Grundsystem | null | undefined, siteId: string): string[] {
  const id = siteId || 'Ihre Site-ID (siehe Dashboard)';
  if (g?.cms_key === 'joomla') {
    return [
      'Paket herunterladen (plg_system_complyo.zip).',
      'Joomla-Backend: System, Installieren, Erweiterungen. Zip hochladen.',
      'Unter Plugins das System-Plugin „Complyo" aktivieren.',
      `In den Plugin-Einstellungen die Site-ID eintragen: ${id}.`,
    ];
  }
  return [
    'Paket herunterladen (complyo-compliance.zip).',
    'WordPress-Backend: Plugins, Installieren, Plugin hochladen. Zip auswählen und installieren.',
    'Plugin aktivieren.',
    `Unter Einstellungen, Complyo die Site-ID prüfen: ${id}. Das Plugin leitet sie aus der Domain ab.`,
  ];
}
