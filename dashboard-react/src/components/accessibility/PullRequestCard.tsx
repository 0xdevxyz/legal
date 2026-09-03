'use client';

/**
 * Ein-Klick-Fix: freigegebene Fixes als GitHub-Pull-Request.
 *
 * Sichtbares Ende des Ohne-LLM-Wegs: KI schlägt vor (einmal), der Nutzer gibt
 * in der Worklist frei, diese Karte macht daraus mechanisch einen PR —
 * deterministisch, ohne dass irgendeine KI den Kundencode anfasst. Gemerged
 * wird ausschließlich vom Kunden im GitHub-UI; Revert bleibt jederzeit möglich.
 *
 * Die Karte lebt bewusst IN der Worklist, nicht auf einer eigenen Seite:
 * Freigeben und Ausliefern sind ein Arbeitsgang, kein Feature-Menüpunkt.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  GitPullRequest, Github, Loader2, CheckCircle, AlertCircle, ExternalLink,
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface ConnectedRepo {
  id: string;
  provider: string;
  full_name: string;
  default_branch: string;
}

interface ApplyResult {
  success: boolean;
  pr_url?: string;
  pr_number?: number;
  branch_name?: string;
  files_changed?: string[];
  error?: string;
}

export const PullRequestCard: React.FC<{
  siteId: string;
  /** Freigegebene Fixes, die dieser Weg wirklich in Code schreiben kann. */
  approvedCount: number;
  /** Freigegebene Fixes, die über Widget/Plugin gehen statt über den PR. */
  manifestOnlyCount?: number;
}> = ({
  siteId,
  approvedCount,
  manifestOnlyCount = 0,
}) => {
  const [repos, setRepos] = useState<ConnectedRepo[]>([]);
  const [repoId, setRepoId] = useState<string>('');
  const [reposLoaded, setReposLoaded] = useState(false);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ApplyResult | null>(null);

  const loadRepos = useCallback(async () => {
    try {
      const liste = (await apiClient.get<ConnectedRepo[]>('/api/v2/git/repos')) ?? [];
      setRepos(liste);
      if (liste.length > 0) setRepoId(liste[0].id);
    } catch {
      setRepos([]);
    } finally {
      setReposLoaded(true);
    }
  }, []);

  useEffect(() => { loadRepos(); }, [loadRepos]);

  const verbinden = async () => {
    try {
      const redirect = `${window.location.origin}/accessibility/worklist`;
      const res = await apiClient.get<{ url: string }>(
        '/api/v2/git/oauth/github/url',
        { redirect_uri: redirect },
      );
      if (res?.url) window.location.href = res.url;
    } catch {
      setResult({ success: false, error: 'GitHub-Verbindung konnte nicht gestartet werden.' });
    }
  };

  const erstellePR = async () => {
    setRunning(true);
    setResult(null);
    try {
      const res = await apiClient.post<ApplyResult>('/api/v2/git/apply-approved-fixes', {
        repo_id: repoId,
        site_id: siteId,
      });
      setResult(res);
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setResult({ success: false, error: detail || 'Anfrage fehlgeschlagen.' });
    } finally {
      setRunning(false);
    }
  };

  if (!reposLoaded) return null;

  return (
    <section className="mt-8 rounded-2xl border dark:border-zinc-700/50 border-gray-200 dark:bg-zinc-800/30 bg-gray-50 p-5">
      <h2 className="flex items-center gap-2 text-sm font-semibold dark:text-zinc-200 text-gray-800">
        <GitPullRequest className="w-4 h-4 text-purple-400" />
        Als Pull Request in Ihr Repository
      </h2>
      <p className="mt-1.5 text-xs leading-relaxed dark:text-zinc-400 text-gray-600 max-w-2xl">
        Ihre freigegebenen Fixes werden mechanisch auf die Template-Dateien Ihres
        Repositories angewendet — als Vorschlag in einem eigenen Branch. Keine KI
        schreibt in Ihren Code; gemerged wird nur von Ihnen, und jeder PR lässt
        sich mit einem Klick zurücknehmen.
      </p>

      {repos.length === 0 ? (
        <button
          onClick={verbinden}
          className="mt-4 inline-flex items-center gap-2 rounded-xl dark:bg-white bg-white dark:bg-gray-900 dark:text-gray-900 text-gray-900 dark:text-white px-4 py-2.5 text-sm font-semibold hover:opacity-90 transition-opacity"
        >
          <Github className="w-4 h-4" />
          GitHub-Repository verbinden
        </button>
      ) : (
        <div className="mt-4 flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3">
          <select
            value={repoId}
            onChange={(e) => setRepoId(e.target.value)}
            aria-label="Repository wählen"
            className="rounded-xl border dark:border-zinc-600 border-gray-300 dark:bg-zinc-900/50 bg-white px-3 py-2.5 text-sm dark:text-zinc-200 text-gray-800 min-w-[14rem]"
          >
            {repos.map((r) => (
              <option key={r.id} value={r.id}>
                {r.full_name} ({r.default_branch})
              </option>
            ))}
          </select>
          <button
            onClick={erstellePR}
            disabled={running || approvedCount === 0 || !repoId}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white px-4 py-2.5 text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitPullRequest className="w-4 h-4" />}
            {running ? 'Erstelle Pull Request …' : `${approvedCount} freigegebene Fixes als PR vorschlagen`}
          </button>
        </div>
      )}

      {approvedCount === 0 && repos.length > 0 && (
        <p className="mt-2 text-xs dark:text-zinc-500 text-gray-500">
          {manifestOnlyCount > 0
            ? `Ihre ${manifestOnlyCount} freigegebenen Fixes gehen über Widget bzw. WordPress-Plugin raus — für einen Pull Request braucht es Alt-Texte oder dokumentweite Fixes.`
            : 'Noch keine freigegebenen Fixes — prüfen Sie zuerst die Vorschläge oben.'}
        </p>
      )}

      {approvedCount > 0 && manifestOnlyCount > 0 && (
        <p className="mt-2 text-xs dark:text-zinc-500 text-gray-500">
          {manifestOnlyCount} weitere freigegebene Fixes (Linktexte, CSS) liefert das
          Widget bzw. das WordPress-Plugin aus — sie sind nicht Teil dieses Pull Requests.
        </p>
      )}

      {result && result.success && (
        <div className="mt-4 flex items-start gap-2 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3">
          <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm dark:text-green-300 text-green-700">
            Pull Request #{result.pr_number} erstellt
            {result.files_changed && ` — ${result.files_changed.length} Datei(en) geändert`}.{' '}
            {result.pr_url && (
              <a
                href={result.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 font-semibold underline"
              >
                Auf GitHub ansehen <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      )}

      {result && !result.success && (
        <div className="mt-4 flex items-start gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3">
          <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm dark:text-amber-300 text-amber-700">{result.error}</p>
        </div>
      )}
    </section>
  );
};

export default PullRequestCard;
