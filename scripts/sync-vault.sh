#!/usr/bin/env bash
# Schreibt den aktuellen Complyo-Stand als Note in den Hermes-Vault.
# Aufruf: automatisch via .git/hooks/post-commit, oder manuell.
#
# Die Note ist generiert — NICHT von Hand bearbeiten, Änderungen werden
# überschrieben. Inhaltliche Notizen gehören in complyo.md im Vault.
set -uo pipefail

REPO="/home/clawd/saas/legal"
VAULT="/opt/hermes/brain"
NOTE="$VAULT/complyo-tech-stand.md"
VAULT_USER="hermes"

[ -d "$VAULT/.git" ] || { echo "sync-vault: Vault $VAULT nicht gefunden — übersprungen." >&2; exit 0; }

cd "$REPO" || exit 0

BRANCH=$(git branch --show-current)
STAMP=$(date +%Y-%m-%d)

# --- Feature-Stand: Tabellenzeilen aus der Registry übernehmen ---------------
features=$(awk -F'|' '
  /^\| *\[?[A-ZÄÖÜ]/ && !/^\| *Feature *\|/ && !/^\|---/ {
    name=$2; doc=$3; status=$4; stand=$5
    gsub(/^ +| +$/, "", name); gsub(/^ +| +$/, "", status); gsub(/^ +| +$/, "", stand)
    if (match(doc, /\(([^)]+)\)/)) { f=substr(doc, RSTART+1, RLENGTH-2) } else { f="" }
    printf "| %s | %s | %s | `data/features/%s` |\n", name, status, stand, f
  }' data/features/00_FEATURES_INDEX.md)

# --- Offene Punkte: Checkboxen aus den Planungsdokumenten --------------------
open_points=""
for plan in planning/*.md; do
  [ -e "$plan" ] || continue
  open=$(grep -c '^\s*- \[ \]' "$plan" || true)
  done_n=$(grep -c '^\s*- \[x\]' "$plan" || true)
  total=$((open + done_n))
  [ "$total" -eq 0 ] && continue
  open_points+="| \`$plan\` | $done_n / $total erledigt | **$open offen** |"$'\n'
done

# Offene Phasen des Launch-Plans einzeln auflisten (Blocker-Sicht)
launch_phases=""
LP="planning/STRUKTUR_FIXES_LAUNCH_PLAN.md"
if [ -f "$LP" ]; then
  launch_phases=$(awk '
    /^## / { if (phase != "" && open > 0) printf "- **%s** — %d offen\n", phase, open
             phase=substr($0,4); open=0; next }
    /^\s*- \[ \]/ { open++ }
    END { if (phase != "" && open > 0) printf "- **%s** — %d offen\n", phase, open }
  ' "$LP")
fi

# --- Deploy-Stand: laufende Complyo-Container -------------------------------
containers=$(docker ps --filter "name=complyo-" --format '| `{{.Names}}` | {{.Status}} |' 2>/dev/null | sort)
[ -z "$containers" ] && containers="| _keine complyo-Container gefunden_ | — |"

commits=$(git log --oneline -8 --format='- `%h` %s _(%ar)_')

# --- Note schreiben ---------------------------------------------------------
cat > "$NOTE" <<EOF
---
title: complyo – Technischer Stand (auto)
gewicht: 9
tags: [complyo, technik, stand, auto-sync, features, deploy]
quelle: repo-sync
aktualisiert: $STAMP
---

# complyo – Technischer Stand (auto)

> ⚙️ **Automatisch generiert** aus \`$REPO\` bei jedem Commit
> (\`scripts/sync-vault.sh\`, ausgelöst per \`post-commit\`-Hook).
> **Nicht von Hand bearbeiten** — Änderungen werden überschrieben.
> Strategie/Produkt gehört nach [[complyo]], Wettbewerb nach [[complyo-wettbewerb]].

Kanonische Domain: **complyo.de** (\`complyo.tech\` ist eliminiert, siehe [[complyo-domains-infrastruktur]]).

## Gebaute Features

| Feature | Status | Stand | Doku |
|---|---|---|---|
$features

Pflege-Pflicht: jedes Feature in \`data/features/\` dokumentieren, Registry-Zeile aktuell halten.

## Offene Punkte (aus den Planungsdokumenten)

| Plan | Fortschritt | |
|---|---|---|
$open_points

### Launch-Plan: offene Phasen
$launch_phases

## Deploy-Stand

Branch: \`$BRANCH\`

| Container | Status |
|---|---|
$containers

### Letzte Commits
$commits

---
_Erzeugt am $STAMP von \`scripts/sync-vault.sh\`._
EOF

chown "$VAULT_USER:$VAULT_USER" "$NOTE" 2>/dev/null || true

# --- Committen (nur wenn sich etwas geändert hat) ---------------------------
cd "$VAULT" || exit 0
if [ -z "$(git status --porcelain -- "$(basename "$NOTE")")" ]; then
  echo "sync-vault: keine Änderung am Vault-Stand."
  exit 0
fi

SHA=$(git -C "$REPO" rev-parse --short HEAD)
run_git() { if [ "$(id -un)" = "$VAULT_USER" ]; then git "$@"; else sudo -u "$VAULT_USER" git "$@"; fi; }
run_git add -- "$(basename "$NOTE")"
run_git -c user.name="complyo-sync" -c user.email="sync@complyo.de" \
  commit -q -m "sync via repo: complyo Tech-Stand ($SHA)" && \
  echo "sync-vault: Vault aktualisiert ($SHA). Hermes-Indexer zieht binnen 10 Min."
