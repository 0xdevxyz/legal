/**
 * Fest eingebaute Tracker umschreiben (Einbau per Schnipsel).
 *
 * Befund 10.11.2026 (loqal.io, 183 statische Seiten): Banner und Blocker waren
 * eingebaut, Google Analytics lud trotzdem vor der Einwilligung. Der Browser
 * holt ein fest im Quelltext stehendes <script src> ueber seinen Vorlade-Scanner,
 * bevor irgendein Skript es anfassen kann. Verhindern laesst sich das nur im
 * Markup: ohne src kein Abruf. Die Plugins fuer WordPress und Joomla schreiben
 * das Markup selbst um; wer den Schnipsel von Hand einbaut, muss es einmal tun.
 *
 * Die Attribute sind die, die public/cookie-blocker.js freigibt (unblockElements):
 * script[type="text/plain"][data-complyo-consent], iframe[data-complyo-src] und
 * link[data-complyo-href], die beiden letzten nur mit data-complyo-blocked="true".
 * Waechter: backend/tests/test_plugin_markup_neutralisierung.py.
 */

import React from 'react';
import { AlertTriangle } from 'lucide-react';

const VORHER_NACHHER = `<!-- Vorher: lädt sofort, auch ohne Einwilligung -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"></script>

<!-- Nachher: lädt erst nach der Einwilligung in Statistik -->
<script type="text/plain" data-complyo-consent="analytics"
        data-complyo-src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX" async></script>`;

const WEITERE = `<!-- Video oder Karte: src wird zu data-complyo-src -->
<iframe data-complyo-consent="marketing" data-complyo-blocked="true"
        data-complyo-src="https://www.youtube.com/embed/VIDEO-ID"></iframe>

<!-- Google Fonts: href wird zu data-complyo-href -->
<link rel="stylesheet" media="not all" data-complyo-blocked="true"
      data-complyo-href="https://fonts.googleapis.com/css2?family=Inter">`;

interface Props {
  /** Im Einrichtungsassistenten: nur Kernregel und ein Beispiel. */
  kompakt?: boolean;
}

const TrackerUmschreiben: React.FC<Props> = ({ kompakt = false }) => (
  <div className="p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg space-y-3" data-testid="tracker-umschreiben">
    <div className="flex items-start gap-2">
      <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-semibold text-gray-900 dark:text-white">
          Fest eingebaute Tracker einmal umschreiben
        </p>
        <p className="text-xs text-gray-700 dark:text-gray-300 mt-1">
          Steht ein Tracking-Skript, ein Video oder eine Karte direkt im Quelltext Ihrer Seite, lädt der Browser es,
          bevor der Blocker eingreifen kann. Schreiben Sie diese Stellen so um, dann lädt Complyo sie erst nach der
          Einwilligung. Mit dem Plugin für WordPress oder Joomla geschieht das automatisch.
        </p>
      </div>
    </div>

    <div className="bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg p-3 font-mono text-xs overflow-x-auto">
      <pre className="text-green-400 whitespace-pre-wrap">{VORHER_NACHHER}</pre>
    </div>

    {!kompakt && (
      <div className="bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg p-3 font-mono text-xs overflow-x-auto">
        <pre className="text-green-400 whitespace-pre-wrap">{WEITERE}</pre>
      </div>
    )}

    <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1 list-disc pl-5">
      <li>
        <code>analytics</code> für Statistik (Google Analytics, Tag Manager, Matomo, Hotjar),{' '}
        <code>marketing</code> für Werbung und Videos (Meta Pixel, YouTube, Vimeo),{' '}
        <code>functional</code> für Karten, Chat und Google Fonts.
      </li>
      <li>Der Cookie-Blocker steht als erstes Skript im <code>&lt;head&gt;</code>, vor allen anderen.</li>
      <li>
        Prüfen: Seite im privaten Fenster öffnen, in den Entwicklerwerkzeugen den Reiter Netzwerk wählen. Vor dem
        Klick im Banner darf keine Anfrage an Google, YouTube oder Meta erscheinen.
      </li>
    </ul>
  </div>
);

export default TrackerUmschreiben;
