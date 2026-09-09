import type { Config } from 'dompurify';

const ALLOWED_CONFIG: Config = {
  ALLOWED_TAGS: [
    'p', 'br', 'b', 'i', 'em', 'strong', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'span', 'div', 'code', 'pre', 'blockquote', 'hr',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
  ],
  ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'id'],
  FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
};

export function sanitizeHtml(dirty: string): string {
  // Auf dem Server gibt es kein DOM und damit kein DOMPurify. Bis zum
  // 10.09.2026 wurde der Text dort UNGEPRUEFT zurueckgegeben — beim
  // Server-Rendern hiesse das: er steht roh im ausgelieferten HTML, und
  // dort laeuft ein <script> tatsaechlich (anders als bei innerHTML im
  // Browser). In der Praxis kommen diese Inhalte erst nach dem Laden per
  // API herein, der Zweig lief also leer. Ein Sicherheitsnetz, das im
  // Zweifel durchlaesst, ist trotzdem keins.
  if (typeof window === 'undefined') return '';
  /* eslint-disable-next-line */
  const DOMPurify = require('dompurify');
  return DOMPurify.sanitize(dirty, ALLOWED_CONFIG) as string;
}
