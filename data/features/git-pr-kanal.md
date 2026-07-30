# GitHub-PR-Kanal (Fix-Auslieferung ohne Direktschreiben)

**Stand:** 2026-07-30 · **Status:** 🟢 Backend live, UI live — Praxistest wartet auf GitHub-OAuth-App (Launchtag)

## Ziel
Der strategische Auslieferungsweg für Fixes (Betreiber-Entscheidung 29.07.2026):
complyo schlägt Änderungen als Pull Request vor, der Kunde prüft und merged.
Die KI schreibt nie selbst in die Kundenseite; Rollback = Revert-PR.

## Architektur
- **Service:** `backend/git_service/git_service.py` — GitHubClient + GitLabClient,
  OAuth-Code-Tausch, Branch anlegen, Dateien schreiben, `create_accessibility_pr`
  (unified_diff-Patches), `revert_pull_request` (offen → schließen; gemerged →
  Gegen-PR auf den Stand des ersten Merge-Commit-Parents; added-Dateien werden
  entfernt; bricht ab statt halbe Reverts zu bauen).
- **Routes:** `backend/git_routes.py`, Prefix `/api/v2/git`, alle mit
  `get_current_user`: `oauth/{provider}/url`, `oauth/{provider}/callback`
  (State in Redis, TTL 10 min), `repos/connect`, `repos`, `apply-patches`,
  `status`, `prs`, `prs/{id}/revert`.
- **Token-Sicherheit:** `backend/git_token_crypto.py` — Fernet, Schlüssel
  `GIT_TOKEN_ENC_KEY`. Fail-closed: ohne Schlüssel wird nicht gespeichert (503)
  und nicht gelesen (wie „nicht verbunden"); Ciphertext wird nie als Klartext
  zurückgegeben.
- **Schema:** Revision `0010_git_integration` — `git_credentials`
  (UNIQUE user+provider, Tokens verschlüsselt), `git_connected_repos`,
  `git_pull_requests` (Status-CHECK OPEN/MERGED/CLOSED/DRAFT).
- **UI:** `dashboard-react/src/components/settings/GitHubIntegration.tsx`
  (Tab „Integrationen": OAuth-Verbindung, Repo-Auswahl, PR-Liste mit
  „Zurücknehmen"). Nur GitHub im UI; GitLab-Client bleibt im Code.
- **MCP:** apply-patches, prs, revert sind Teil der kuratierten Allowlist
  ([[mcp-server]]) — ein Agent kann PRs vorschlagen und zurücknehmen,
  gemerged wird immer vom Menschen.

## Entfernte Duplikate (2026-07-30)
- `POST /api/v2/fixes/propose-pr` (Kunden-Token im Request-Body, naive Patches)
- `compliance_engine/github_integration.py` (unimportierte Drittvariante)

## Tests
`tests/test_git_integration_auth.py`: jede Route verlangt Login; INSERT sieht
nur verschlüsselte Werte; fail-closed ohne Schlüssel; Duplikate bleiben entfernt.

## Offen
- **Launchtag:** GitHub-OAuth-App anlegen (`GITHUB_CLIENT_ID`/`SECRET` in `.env`,
  vorbereitet und leer), PR- und Revert-Flow gegen ein Test-Repo durchspielen.
- Patch-Erzeugung aus der A11y-Worklist an `apply-patches` anschließen
  (Format `unified_diff`+`file_path` passt; `accessibility_patch_generator.py`
  braucht dafür echte Seiten-Patches statt Beispiel-HTML).
- PR-Status-Sync (OPEN → MERGED) läuft nur bei Revert-Aufrufen, kein Webhook.
