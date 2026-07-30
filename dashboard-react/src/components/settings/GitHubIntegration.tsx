'use client';

/**
 * GitHub-Integration — der PR-Auslieferungskanal.
 *
 * Grundsatz (Betreiber-Entscheidung 29.07.2026): complyo schreibt nie selbst
 * in die Kundenseite. Freigegebene Fixes werden als Pull Request in das
 * verbundene Repository vorgeschlagen; gemerged wird vom Kunden.
 *
 * Gegenstellen: backend/git_routes.py (/api/v2/git/*). Der OAuth-Redirect
 * kommt mit ?code=&state= auf diese Seite zurück (redirect_uri).
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  Github, Loader2, CheckCircle, AlertCircle, GitPullRequest, Plus, ExternalLink,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { getApiClient } from '@/lib/api-client';

const api = getApiClient();

interface ProviderStatus {
  provider: string;
  git_username: string | null;
  connected_at: string | null;
}

interface ConnectedRepo {
  id: string;
  provider: string;
  full_name: string;
  default_branch: string;
  connected_at: string;
}

interface PullRequestItem {
  id: number;
  pr_number: number | null;
  pr_url: string | null;
  branch_name: string | null;
  status: 'OPEN' | 'MERGED' | 'CLOSED' | 'DRAFT';
  created_at: string | null;
  repo_full_name: string;
}

const PR_STATUS_STYLE: Record<string, string> = {
  OPEN: 'bg-emerald-500/15 text-emerald-500',
  MERGED: 'bg-purple-500/15 text-purple-500',
  CLOSED: 'bg-zinc-500/15 text-zinc-500',
  DRAFT: 'bg-amber-500/15 text-amber-500',
};

function fehlertext(e: unknown, fallback: string): string {
  const err = e as { response?: { data?: { detail?: string } }; message?: string };
  return err?.response?.data?.detail || err?.message || fallback;
}

export default function GitHubIntegration() {
  const [status, setStatus] = useState<ProviderStatus[] | null>(null);
  const [repos, setRepos] = useState<ConnectedRepo[]>([]);
  const [prs, setPrs] = useState<PullRequestItem[]>([]);
  const [laden, setLaden] = useState(true);
  const [aktion, setAktion] = useState(false);
  const [meldung, setMeldung] = useState<{ typ: 'ok' | 'fehler'; text: string } | null>(null);

  const [owner, setOwner] = useState('');
  const [repoName, setRepoName] = useState('');
  const [branch, setBranch] = useState('main');

  const verbunden = (status ?? []).some((p) => p.provider === 'github');

  const ladeAlles = useCallback(async () => {
    setLaden(true);
    try {
      const [st, rp, pr] = await Promise.all([
        api.get('/api/v2/git/status'),
        api.get<ConnectedRepo[]>('/api/v2/git/repos'),
        api.get('/api/v2/git/prs'),
      ]);
      setStatus(st.data?.providers ?? []);
      setRepos(rp.data ?? []);
      setPrs(pr.data?.prs ?? []);
    } catch (e: unknown) {
      setMeldung({ typ: 'fehler', text: fehlertext(e, 'Status konnte nicht geladen werden.') });
    } finally {
      setLaden(false);
    }
  }, []);

  useEffect(() => { ladeAlles(); }, [ladeAlles]);

  // OAuth-Rueckkehr: GitHub haengt code+state an die redirect_uri.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    if (!code || !state) return;
    // Query sofort bereinigen, damit ein Reload den Code nicht erneut einloest.
    window.history.replaceState({}, '', window.location.pathname + '?tab=integrationen');
    (async () => {
      setAktion(true);
      try {
        const res = await api.post('/api/v2/git/oauth/github/callback', { code, state });
        if (res.data?.success) {
          setMeldung({ typ: 'ok', text: `GitHub verbunden als ${res.data.user_name ?? 'unbekannt'}.` });
          await ladeAlles();
        } else {
          setMeldung({ typ: 'fehler', text: res.data?.error ?? 'GitHub-Verbindung fehlgeschlagen.' });
        }
      } catch (e: unknown) {
        setMeldung({ typ: 'fehler', text: fehlertext(e, 'GitHub-Verbindung fehlgeschlagen.') });
      } finally {
        setAktion(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const starteOAuth = async () => {
    setAktion(true);
    setMeldung(null);
    try {
      const redirect = `${window.location.origin}/settings?tab=integrationen`;
      const res = await api.get('/api/v2/git/oauth/github/url', {
        params: { redirect_uri: redirect },
      });
      window.location.href = res.data.url;
    } catch (e: unknown) {
      setMeldung({ typ: 'fehler', text: fehlertext(e, 'OAuth konnte nicht gestartet werden. Ist die GitHub-App konfiguriert?') });
      setAktion(false);
    }
  };

  const verbindeRepo = async () => {
    if (!owner.trim() || !repoName.trim()) {
      setMeldung({ typ: 'fehler', text: 'Owner und Repository angeben.' });
      return;
    }
    setAktion(true);
    setMeldung(null);
    try {
      const res = await api.post('/api/v2/git/repos/connect', {
        provider: 'github',
        owner: owner.trim(),
        repo: repoName.trim(),
        default_branch: branch.trim() || 'main',
      });
      if (res.data?.success) {
        setMeldung({ typ: 'ok', text: `${res.data.full_name} verbunden.` });
        setOwner(''); setRepoName('');
        await ladeAlles();
      } else {
        setMeldung({ typ: 'fehler', text: res.data?.error ?? 'Repository konnte nicht verbunden werden.' });
      }
    } catch (e: unknown) {
      setMeldung({ typ: 'fehler', text: fehlertext(e, 'Repository konnte nicht verbunden werden.') });
    } finally {
      setAktion(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold dark:text-white text-gray-900 flex items-center gap-2">
          <Github className="w-5 h-5" />
          GitHub-Integration
        </h3>
        <p className="text-sm dark:text-zinc-400 text-gray-600 mt-1">
          complyo schreibt nie direkt in Ihre Website. Freigegebene Fixes werden als
          Pull Request vorgeschlagen — Sie prüfen und mergen selbst. Jeder PR lässt
          sich per Revert rückstandslos zurücknehmen.
        </p>
      </div>

      {meldung && (
        <div className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${
          meldung.typ === 'ok'
            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500'
            : 'border-red-500/30 bg-red-500/10 text-red-500'
        }`}>
          {meldung.typ === 'ok'
            ? <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            : <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />}
          <span>{meldung.text}</span>
        </div>
      )}

      {laden ? (
        <div className="flex items-center gap-2 text-sm dark:text-zinc-400 text-gray-600">
          <Loader2 className="w-4 h-4 animate-spin" /> Wird geladen …
        </div>
      ) : (
        <>
          <Card className="dark:bg-zinc-900/50 bg-white/70">
            <CardContent className="p-5 flex flex-wrap items-center justify-between gap-3">
              {verbunden ? (
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  <span className="dark:text-white text-gray-900">
                    Verbunden als{' '}
                    <strong>
                      {(status ?? []).find((p) => p.provider === 'github')?.git_username ?? 'GitHub-Konto'}
                    </strong>
                  </span>
                </div>
              ) : (
                <p className="text-sm dark:text-zinc-400 text-gray-600">
                  Noch nicht verbunden. Die Verbindung nutzt GitHub-OAuth — complyo
                  sieht Ihr Passwort nie, Tokens werden verschlüsselt gespeichert.
                </p>
              )}
              <Button onClick={starteOAuth} disabled={aktion} className="gap-2">
                {aktion ? <Loader2 className="w-4 h-4 animate-spin" /> : <Github className="w-4 h-4" />}
                {verbunden ? 'Erneut verbinden' : 'Mit GitHub verbinden'}
              </Button>
            </CardContent>
          </Card>

          {verbunden && (
            <Card className="dark:bg-zinc-900/50 bg-white/70">
              <CardContent className="p-5 space-y-4">
                <p className="font-medium dark:text-white text-gray-900">Verbundene Repositories</p>
                {repos.length === 0 ? (
                  <p className="text-sm dark:text-zinc-500 text-gray-500">Noch kein Repository verbunden.</p>
                ) : (
                  <ul className="space-y-2">
                    {repos.map((r) => (
                      <li key={r.id} className="flex items-center justify-between text-sm rounded border dark:border-zinc-800 border-gray-200 px-3 py-2">
                        <span className="dark:text-white text-gray-900 font-mono">{r.full_name}</span>
                        <span className="dark:text-zinc-500 text-gray-500">Branch: {r.default_branch}</span>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="grid gap-3 sm:grid-cols-4 items-end">
                  <div className="space-y-1">
                    <Label htmlFor="gh-owner">Owner</Label>
                    <Input id="gh-owner" value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="mein-account" />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="gh-repo">Repository</Label>
                    <Input id="gh-repo" value={repoName} onChange={(e) => setRepoName(e.target.value)} placeholder="meine-website" />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="gh-branch">Branch</Label>
                    <Input id="gh-branch" value={branch} onChange={(e) => setBranch(e.target.value)} />
                  </div>
                  <Button onClick={verbindeRepo} disabled={aktion} variant="outline" className="gap-2">
                    <Plus className="w-4 h-4" /> Verbinden
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {prs.length > 0 && (
            <Card className="dark:bg-zinc-900/50 bg-white/70">
              <CardContent className="p-5 space-y-3">
                <p className="font-medium dark:text-white text-gray-900 flex items-center gap-2">
                  <GitPullRequest className="w-4 h-4" /> Über complyo erstellte Pull Requests
                </p>
                <ul className="space-y-2">
                  {prs.map((pr) => (
                    <li key={pr.id} className="flex flex-wrap items-center justify-between gap-2 text-sm rounded border dark:border-zinc-800 border-gray-200 px-3 py-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`px-2 py-0.5 rounded text-xs ${PR_STATUS_STYLE[pr.status] ?? ''}`}>{pr.status}</span>
                        <span className="dark:text-white text-gray-900 font-mono truncate">
                          {pr.repo_full_name}#{pr.pr_number ?? '—'}
                        </span>
                        <span className="dark:text-zinc-500 text-gray-500 truncate">{pr.branch_name}</span>
                      </div>
                      {pr.pr_url && (
                        <a href={pr.pr_url} target="_blank" rel="noopener noreferrer"
                           className="inline-flex items-center gap-1 text-teal-500 hover:text-teal-400">
                          Ansehen <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
