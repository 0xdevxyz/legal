'use client';

import StatementGenerator from '@/components/accessibility/StatementGenerator';

export default function AccessibilityStatementPage() {
  return (
    <main className="px-4 sm:px-6 py-6">
      {/* Querverweis: wer hier landet, sucht meist die Fix-Funktionen */}
      <div className="max-w-3xl mx-auto mb-6 rounded-xl border dark:border-teal-500/30 border-teal-200 dark:bg-teal-500/5 bg-teal-50 px-4 py-3 text-sm dark:text-teal-300 text-teal-800">
        Ihre KI-Fix-Vorschläge (Alt-Texte, Dokument-Fixes) prüfen und freigeben Sie unter{' '}
        <a href="/accessibility/worklist" className="font-semibold underline">Fixes &amp; Freigaben</a>
        {' '}— dort verbinden Sie auch Ihr GitHub-Repository für den Ein-Klick-Pull-Request.
      </div>
      <StatementGenerator />
    </main>
  );
}
