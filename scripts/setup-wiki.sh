#!/usr/bin/env bash

# setup-wiki.sh — Smart bootstrap for the Obsidian LLM Wiki vault used by the
# `llm-wiki` skill and the `wiki-*` slash commands.
#
# Idempotent: safe to re-run. Will not overwrite an existing vault.
#
# Usage:
#   scripts/setup-wiki.sh                       # interactive
#   scripts/setup-wiki.sh --vault PATH          # explicit path, interactive confirm
#   scripts/setup-wiki.sh --non-interactive     # never prompt; fail if config missing
#   scripts/setup-wiki.sh --with-qmd            # also build the qmd index
#   scripts/setup-wiki.sh --no-qmd              # skip qmd entirely
#   scripts/setup-wiki.sh --verify              # only run health checks, no writes
#   scripts/setup-wiki.sh --help

set -euo pipefail

# ---------- colors ----------
if [[ -t 1 ]]; then
    GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'
    BLUE=$'\033[0;34m'; CYAN=$'\033[0;36m'; NC=$'\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; BLUE=''; CYAN=''; NC=''
fi

log()    { printf '%s[setup-wiki]%s %s\n' "$BLUE" "$NC" "$*"; }
ok()     { printf '%s✓%s %s\n' "$GREEN" "$NC" "$*"; }
warn()   { printf '%s⚠%s %s\n' "$YELLOW" "$NC" "$*" >&2; }
err()    { printf '%s✗%s %s\n' "$RED" "$NC" "$*" >&2; }
prompt() { printf '%s?%s %s ' "$CYAN" "$NC" "$*"; }

# ---------- args ----------
VAULT_ARG=""
INTERACTIVE=1
QMD_MODE="auto"          # auto | on | off
VERIFY_ONLY=0
SKIP_CLAUDE_MD=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --vault) VAULT_ARG="${2:-}"; shift 2;;
        --vault=*) VAULT_ARG="${1#*=}"; shift;;
        --non-interactive|-y) INTERACTIVE=0; shift;;
        --with-qmd) QMD_MODE="on"; shift;;
        --no-qmd) QMD_MODE="off"; shift;;
        --verify) VERIFY_ONLY=1; shift;;
        --skip-claude-md) SKIP_CLAUDE_MD=1; shift;;
        --help|-h)
            sed -n '3,16p' "$0" | sed 's/^# \{0,1\}//'
            exit 0;;
        *)
            err "Unknown argument: $1"
            exit 2;;
    esac
done

ask_yn() {
    local question="$1" default="${2:-Y}" answer
    if [[ $INTERACTIVE -eq 0 ]]; then
        [[ "$default" == "Y" ]]
        return $?
    fi
    local hint="[Y/n]"
    [[ "$default" == "N" ]] && hint="[y/N]"
    prompt "$question $hint"
    read -r answer
    answer="${answer:-$default}"
    [[ "$answer" =~ ^[Yy]$ ]]
}

# ---------- detect existing vault ----------
# CLAUDE_MD can be overridden via env (used by tests).
CLAUDE_MD="${CLAUDE_MD:-$HOME/.claude/CLAUDE.md}"
EXISTING_VAULT=""

if [[ -f "$CLAUDE_MD" ]]; then
    # Match `Vault memoire : <path>` (FR) or `Vault path: <path>` (EN), tolerating backticks.
    EXISTING_VAULT=$(awk '
        /Vault memoire/ || /Vault path/ {
            if (match($0, /`[^`]+`/)) {
                s = substr($0, RSTART+1, RLENGTH-2)
                print s
                exit
            }
        }
    ' "$CLAUDE_MD" || true)
fi

# Resolve the chosen vault path.
if [[ -n "$VAULT_ARG" ]]; then
    VAULT_PATH="$VAULT_ARG"
elif [[ -n "$EXISTING_VAULT" ]]; then
    VAULT_PATH="$EXISTING_VAULT"
    log "Detected vault from CLAUDE.md: $VAULT_PATH"
else
    GIT_USER=$(git config --global user.name 2>/dev/null | tr ' ' '-' || echo "")
    DEFAULT_VAULT="$HOME/Documents/Obsidian-${GIT_USER:-User}/Wiki"
    if [[ $INTERACTIVE -eq 0 ]]; then
        err "No vault configured and --non-interactive was set. Pass --vault PATH."
        exit 3
    fi
    prompt "Vault path [$DEFAULT_VAULT]:"
    read -r VAULT_PATH
    VAULT_PATH="${VAULT_PATH:-$DEFAULT_VAULT}"
fi

# Expand ~
VAULT_PATH="${VAULT_PATH/#\~/$HOME}"

# ---------- bootstrap vault ----------
INIT_SCRIPT="$HOME/.claude/skills/llm-wiki/scripts/init_vault.py"

bootstrap_vault() {
    if [[ -d "$VAULT_PATH/wiki" && -d "$VAULT_PATH/raw" ]]; then
        ok "Vault already initialized: $VAULT_PATH"
        return
    fi

    if ! ask_yn "Create new vault at $VAULT_PATH ?"; then
        warn "Skipping vault creation (you said no)."
        return
    fi

    local topic="personal-knowledge"
    if [[ $INTERACTIVE -eq 1 ]]; then
        prompt "Vault topic [personal-knowledge]:"
        read -r topic
        topic="${topic:-personal-knowledge}"
    fi

    mkdir -p "$VAULT_PATH"
    if [[ -f "$INIT_SCRIPT" ]]; then
        log "Running init_vault.py (topic=$topic) …"
        if python3 "$INIT_SCRIPT" --path "$VAULT_PATH" --topic "$topic" --tool all; then
            ok "Vault structure created via init_vault.py"
            return
        fi
        warn "init_vault.py failed — falling back to minimal layout."
    else
        warn "init_vault.py not found at $INIT_SCRIPT. Falling back to minimal layout."
    fi

    mkdir -p "$VAULT_PATH/raw/assets" \
             "$VAULT_PATH/wiki/entities" \
             "$VAULT_PATH/wiki/concepts" \
             "$VAULT_PATH/wiki/sources" \
             "$VAULT_PATH/wiki/synthesis"
    : > "$VAULT_PATH/wiki/index.md"
    : > "$VAULT_PATH/wiki/log.md"
    ok "Minimal vault layout created. Run /wiki-init from inside Claude to enrich it."
}

# ---------- patch ~/.claude/CLAUDE.md ----------
WIKI_BLOCK_BEGIN="<!-- BEGIN:llm-wiki-config -->"
WIKI_BLOCK_END="<!-- END:llm-wiki-config -->"

patch_claude_md() {
    [[ $SKIP_CLAUDE_MD -eq 1 ]] && { log "Skipping CLAUDE.md patch."; return; }

    local block
    block=$(cat <<EOF
$WIKI_BLOCK_BEGIN
## Obsidian LLM Wiki Memory

- Vault memoire : \`$VAULT_PATH\`
- Source de verite : skill \`llm-wiki\` + commands \`/wiki-init\`, \`/wiki-ingest\`, \`/wiki-query\`, \`/wiki-lint\`, \`/wiki-log\`, \`/wiki-capture-session\`.
- Pour interroger la memoire, lire d'abord \`wiki/index.md\`, puis les pages pertinentes ; utiliser \`qmd\` si l'index ne suffit plus.
- Quand un projet existe sous le repertoire de travail, lire son pointeur local avant tout travail non trivial : \`.claude/project-memory.md\` (Claude Code) ou \`.agents/project-memory.md\` (autres agents).
- Tableau de bord projets : \`wiki/synthesis/dev-projects-overview.md\`.
- Pour sauvegarder une session utile, utiliser \`/wiki-capture-session\` puis \`/wiki-ingest\`.
- Le codebase reste la source de verite immediate ; le vault sert aux decisions historiques, sources, concepts, syntheses et conventions durables.
- Ne jamais stocker secrets, tokens, credentials, logs complets ou transcripts bruts dans le vault.
$WIKI_BLOCK_END
EOF
)

    mkdir -p "$(dirname "$CLAUDE_MD")"
    touch "$CLAUDE_MD"

    if grep -q "$WIKI_BLOCK_BEGIN" "$CLAUDE_MD"; then
        local tmp
        tmp=$(mktemp)
        awk -v begin="$WIKI_BLOCK_BEGIN" -v end="$WIKI_BLOCK_END" '
            $0 == begin { in_block=1; next }
            in_block && $0 == end { in_block=0; next }
            !in_block { print }
        ' "$CLAUDE_MD" > "$tmp"
        printf '%s\n' "$block" >> "$tmp"
        mv "$tmp" "$CLAUDE_MD"
        ok "Updated existing wiki block in $CLAUDE_MD"
    else
        printf '\n%s\n' "$block" >> "$CLAUDE_MD"
        ok "Appended wiki block to $CLAUDE_MD"
    fi
}

# ---------- qmd integration ----------
check_qmd() {
    if command -v qmd >/dev/null 2>&1; then
        local version
        version=$(qmd --version 2>/dev/null | head -1 || echo "?")
        ok "qmd found: $version"
        return 0
    fi
    warn "qmd not on PATH. Install with:"
    printf '    brew install tobi/tap/qmd            # macOS\n'
    printf '    cargo install qmd                    # other\n'
    printf '    See https://github.com/tobi/qmd\n'
    return 1
}

build_qmd_index() {
    case "$QMD_MODE" in
        off) log "qmd index skipped (--no-qmd)."; return;;
        auto)
            ask_yn "Build qmd index of the vault now ?" "Y" || { log "qmd index deferred."; return; };;
        on) ;; # fallthrough
    esac

    if ! command -v qmd >/dev/null 2>&1; then
        warn "Cannot build qmd index — binary not installed."
        return
    fi

    log "Indexing vault with qmd …"
    if (cd "$VAULT_PATH" && qmd index . 2>&1 | tail -10); then
        ok "qmd index built."
    else
        warn "qmd index returned non-zero. Inspect output above."
    fi
}

# ---------- smoke test ----------
LINT_SCRIPT="$HOME/.claude/skills/llm-wiki/scripts/lint_wiki.py"

run_smoke_test() {
    if [[ ! -f "$LINT_SCRIPT" ]]; then
        warn "lint_wiki.py not found at $LINT_SCRIPT — skipping smoke test."
        return
    fi
    log "Running vault lint …"
    if python3 "$LINT_SCRIPT" --vault "$VAULT_PATH" 2>&1 | tail -15; then
        ok "Lint pass complete."
    else
        warn "Lint reported issues. This is normal for a fresh vault."
    fi
}

# ---------- main ----------
log "Vault path: $VAULT_PATH"

if [[ $VERIFY_ONLY -eq 1 ]]; then
    log "Running in --verify mode (no writes)."
    [[ -d "$VAULT_PATH/wiki" ]] || { err "Vault missing or incomplete: $VAULT_PATH"; exit 4; }
    check_qmd || true
    run_smoke_test
    exit 0
fi

bootstrap_vault
patch_claude_md
check_qmd || true
build_qmd_index
run_smoke_test

ok "Wiki bootstrap complete."
echo
log "Next steps:"
echo "  • Open the vault in Obsidian: open '$VAULT_PATH'"
echo "  • From Claude Code, run /wiki-query to test, /wiki-ingest to add a source."
