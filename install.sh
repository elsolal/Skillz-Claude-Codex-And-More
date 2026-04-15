#!/bin/bash

# ============================================================
# D-EPCT+R Workflow Installer
# Install Skillz-Claude skills + RALPH Mode + Knowledge Files + Templates
# into Claude Code, Codex CLI, Gemini CLI, OpenCode, and generic agents.
#
# USAGE (v5.6.0+ subcommand syntax — recommended):
#
#   ./install.sh install  claude|codex|gemini|opencode|agents|all|<path>   — fresh install
#   ./install.sh update   claude|codex|gemini|opencode|agents|all|<path>   — update existing install
#   ./install.sh uninstall claude|codex|gemini|opencode|agents|all         — remove Skillz-managed items
#   ./install.sh help                                — show full help
#
# Examples:
#   ./install.sh install all           # All supported providers globally
#   ./install.sh install claude        # Claude global only
#   ./install.sh install codex         # Codex global only (Claude must exist)
#   ./install.sh install gemini        # Gemini global only (Claude must exist)
#   ./install.sh install opencode      # OpenCode global only (Claude must exist)
#   ./install.sh install .             # Per-project install in current directory
#   ./install.sh install . --providers codex,gemini
#   ./install.sh update claude         # Refresh Claude from latest repo
#   ./install.sh uninstall codex       # Remove Codex mirror, keep Claude
#
#   # Via curl (no clone)
#   curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- install all
#   curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- install .
#
# LEGACY FLAGS (deprecated, still work with a warning):
#   --global              → equivalent to "install all"
#   --global --no-codex   → equivalent to "install claude"
#   --update              → equivalent to "update <path>"
#   <path>                → equivalent to "install <path>"
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

REPO_URL="https://github.com/elsolal/Skillz-Claude.git"
REPO_NAME="Skillz-Claude"

# ============================================================
# Subcommand helpers (v5.6.0+)
# ============================================================

show_usage() {
    cat <<EOF
Skillz-Claude Installer

USAGE:
  ./install.sh <action> <target>

ACTIONS:
  install       Fresh install (prompts if already installed)
  update        Idempotent update (no prompt, preserves your config)
  uninstall     Remove Skillz-managed skills/commands (preserves user-added ones)
  help          Show this help

TARGETS:
  claude        ~/.claude/ globally (for Claude Code)
  codex         ~/.codex/ globally (for Codex CLI, requires Claude installed first)
  gemini        ~/.gemini/ globally (for Gemini CLI, requires Claude installed first)
  opencode      ~/.config/opencode/ globally (for OpenCode, requires Claude installed first)
  agents        ~/.agents/ globally (generic agents, requires Claude installed first)
  all           Claude + Codex + Gemini + OpenCode + generic agents
  <path>        Per-project install in the given directory

EXAMPLES:
  ./install.sh install all            # All supported providers globally
  ./install.sh install claude         # Claude global only
  ./install.sh install codex          # Codex mirror only (Claude must exist)
  ./install.sh install gemini         # Gemini mirror only (Claude must exist)
  ./install.sh install opencode       # OpenCode mirror only (Claude must exist)
  ./install.sh install .              # Per-project install in current dir
  ./install.sh install . --providers codex,gemini
  ./install.sh update claude          # Refresh Claude from latest repo
  ./install.sh uninstall codex        # Remove Codex mirror, keep Claude
  ./install.sh uninstall all          # Remove everything Skillz installed globally

PROJECT OPTIONS:
  --providers LIST                    # all | claude,codex,gemini,opencode,agents

LEGACY FLAGS (deprecated, still work with a warning):
  --global              → install all
  --global --no-codex   → install claude
  --update              → update <current dir>

For full docs: https://github.com/elsolal/Skillz-Claude
EOF
}

deprecation_warning() {
    local old="$1"
    local new="$2"
    echo -e "${YELLOW}⚠️  '$old' is deprecated. Use '$new' instead.${NC}" >&2
    echo -e "${YELLOW}   Continuing with legacy behavior for backwards compatibility.${NC}" >&2
    echo "" >&2
}

is_valid_provider() {
    case "$1" in
        claude|codex|gemini|opencode|agents|all) return 0 ;;
        *) return 1 ;;
    esac
}

validate_provider_list() {
    local list="$1"
    [ -n "$list" ] || return 1
    local normalized="${list//,/ }"
    local provider
    for provider in $normalized; do
        is_valid_provider "$provider" || return 1
    done
    return 0
}

provider_list_contains() {
    local list="$1"
    local provider="$2"
    [ "$list" = "all" ] && return 0
    case ",$list," in
        *",$provider,"*) return 0 ;;
        *) return 1 ;;
    esac
}

global_target_enabled() {
    provider_list_contains "$GLOBAL_TARGETS" "$1"
}

project_provider_enabled() {
    provider_list_contains "$PROJECT_PROVIDERS" "$1"
}

# Uninstall Claude globally — reads ~/.claude/.skillz-manifest and removes
# ONLY the skills/commands listed there. User-added items are preserved.
# Never touches CLAUDE.md, settings.json, mcp.json, knowledge/, templates/.
uninstall_claude_global() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║             Uninstall Claude (Skillz-managed items)                   ║"
    echo "║                                                                       ║"
    echo "║   Removes: skills/* and commands/* that Skillz installed              ║"
    echo "║   Preserves: CLAUDE.md, settings.json, mcp.json, user-added skills    ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    local manifest="$HOME/.claude/.skillz-manifest"
    if [ ! -f "$manifest" ]; then
        echo -e "${YELLOW}ℹ️  No manifest found at $manifest — nothing Skillz-managed to remove.${NC}"
        echo -e "${YELLOW}   (Skills/commands added without Skillz will not be touched.)${NC}"
        return 0
    fi

    local removed_skills=0
    local removed_commands=0
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        case "$line" in \#*) continue ;; esac
        local type="${line%%:*}"
        local name="${line#*:}"
        case "$type" in
            skill)
                if [ -d "$HOME/.claude/skills/$name" ] || [ -L "$HOME/.claude/skills/$name" ]; then
                    rm -rf "$HOME/.claude/skills/$name"
                    echo -e "   ${YELLOW}🗑️  skill: $name${NC}"
                    removed_skills=$((removed_skills + 1))
                fi
                ;;
            command)
                if [ -f "$HOME/.claude/commands/$name" ] || [ -L "$HOME/.claude/commands/$name" ]; then
                    rm -f "$HOME/.claude/commands/$name"
                    echo -e "   ${YELLOW}🗑️  command: $name${NC}"
                    removed_commands=$((removed_commands + 1))
                fi
                ;;
        esac
    done < "$manifest"

    rm -f "$manifest"
    echo ""
    echo -e "${GREEN}✅ Removed $removed_skills skill(s) and $removed_commands command(s)${NC}"
    echo -e "${GREEN}✅ Manifest deleted${NC}"
    echo -e "${CYAN}ℹ️  Your CLAUDE.md, settings.json, mcp.json, and user-added skills are untouched.${NC}"
}

# Uninstall Codex globally — removes symlinks in ~/.codex/skills/ that point to
# ~/.claude/skills/ (Skillz-managed), removes the 5 Codex-native prompts, and
# preserves .system/, config.toml, AGENTS.md, and third-party prompts (BMad).
uninstall_codex_global() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║             Uninstall Codex (Skillz-managed items)                    ║"
    echo "║                                                                       ║"
    echo "║   Removes: skill symlinks pointing to ~/.claude/, Codex-native prompts║"
    echo "║   Preserves: .system/, config.toml, AGENTS.md, third-party prompts    ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    if [ ! -d ~/.codex ]; then
        echo -e "${YELLOW}ℹ️  ~/.codex/ not found — nothing to uninstall.${NC}"
        return 0
    fi

    # 1. Remove skill symlinks pointing to ~/.claude/skills/
    local removed_links=0
    if [ -d ~/.codex/skills ]; then
        for link in ~/.codex/skills/*; do
            [ -L "$link" ] || continue
            local name
            name=$(basename "$link")
            case "$name" in .system|.*) continue ;; esac
            local target
            target=$(readlink "$link")
            # Only remove if it points to ~/.claude/ (Skillz-managed)
            case "$target" in
                "$HOME/.claude/skills/"*|"$HOME/.claude/skills/"*/)
                    rm -f "$link"
                    echo -e "   ${YELLOW}🗑️  skill symlink: $name${NC}"
                    removed_links=$((removed_links + 1))
                    ;;
            esac
        done
    fi

    # 2. Remove Codex-native prompts managed by Skillz (dev, discovery, ship, quick-fix, status)
    local removed_prompts=0
    for prompt in dev discovery ship quick-fix status; do
        local f="$HOME/.codex/prompts/$prompt.md"
        if [ -f "$f" ] && [ ! -L "$f" ]; then
            rm -f "$f"
            echo -e "   ${YELLOW}🗑️  prompt: $prompt.md${NC}"
            removed_prompts=$((removed_prompts + 1))
        fi
    done

    echo ""
    echo -e "${GREEN}✅ Removed $removed_links skill symlink(s) and $removed_prompts Codex prompt(s)${NC}"
    echo -e "${CYAN}ℹ️  ~/.codex/skills/.system/, config.toml, AGENTS.md, and third-party prompts (BMad) are untouched.${NC}"
}

uninstall_provider_symlinks() {
    local skills_dir="$1"
    local label="$2"
    local removed=0
    UNINSTALL_PROVIDER_LINKS_REMOVED=0

    if [ -L "$skills_dir" ]; then
        local target
        target=$(readlink "$skills_dir")
        case "$target" in
            "$HOME/.claude/skills"|"$HOME/.claude/skills/"*|../.claude/skills)
                rm -f "$skills_dir"
                echo -e "   ${YELLOW}🗑️  $label skills symlink${NC}"
                UNINSTALL_PROVIDER_LINKS_REMOVED=1
                return 0
                ;;
        esac
    fi

    if [ -d "$skills_dir" ]; then
        for link in "$skills_dir"/*; do
            [ -L "$link" ] || continue
            local target
            target=$(readlink "$link")
            case "$target" in
                "$HOME/.claude/skills/"*|"$HOME/.claude/skills/"*/|../.claude/skills/*)
                    rm -f "$link"
                    echo -e "   ${YELLOW}🗑️  skill symlink: $(basename "$link")${NC}"
                    removed=$((removed + 1))
                    ;;
            esac
        done
    fi

    UNINSTALL_PROVIDER_LINKS_REMOVED=$removed
}

uninstall_gemini_global() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║             Uninstall Gemini (Skillz-managed items)                   ║"
    echo "║                                                                       ║"
    echo "║   Removes: Skillz command files and skill symlinks                    ║"
    echo "║   Preserves: GEMINI.md and user-added commands/skills                 ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    if [ ! -d ~/.gemini ]; then
        echo -e "${YELLOW}ℹ️  ~/.gemini/ not found — nothing to uninstall.${NC}"
        return 0
    fi

    uninstall_provider_symlinks "$HOME/.gemini/skills" "Gemini"
    local removed_links="$UNINSTALL_PROVIDER_LINKS_REMOVED"

    local removed_commands=0
    for command in dev discovery ship quick-fix status; do
        local f="$HOME/.gemini/commands/$command.toml"
        if [ -f "$f" ] && [ ! -L "$f" ]; then
            rm -f "$f"
            echo -e "   ${YELLOW}🗑️  command: $command.toml${NC}"
            removed_commands=$((removed_commands + 1))
        fi
    done

    echo ""
    echo -e "${GREEN}✅ Removed $removed_links skill symlink(s) and $removed_commands Gemini command(s)${NC}"
    echo -e "${CYAN}ℹ️  ~/.gemini/GEMINI.md and user-added items are untouched.${NC}"
}

uninstall_opencode_global() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║             Uninstall OpenCode (Skillz-managed items)                 ║"
    echo "║                                                                       ║"
    echo "║   Removes: Skillz command files and skill symlinks                    ║"
    echo "║   Preserves: config, AGENTS.md, and user-added commands/skills        ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    local base="$HOME/.config/opencode"
    if [ ! -d "$base" ]; then
        echo -e "${YELLOW}ℹ️  ~/.config/opencode/ not found — nothing to uninstall.${NC}"
        return 0
    fi

    uninstall_provider_symlinks "$base/skills" "OpenCode"
    local removed_links="$UNINSTALL_PROVIDER_LINKS_REMOVED"

    local removed_commands=0
    for command in dev discovery ship quick-fix status; do
        local f="$base/commands/$command.md"
        if [ -f "$f" ] && [ ! -L "$f" ]; then
            rm -f "$f"
            echo -e "   ${YELLOW}🗑️  command: $command.md${NC}"
            removed_commands=$((removed_commands + 1))
        fi
    done

    echo ""
    echo -e "${GREEN}✅ Removed $removed_links skill symlink(s) and $removed_commands OpenCode command(s)${NC}"
    echo -e "${CYAN}ℹ️  ~/.config/opencode/AGENTS.md and user-added items are untouched.${NC}"
}

uninstall_agents_global() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║             Uninstall generic agents (Skillz-managed items)           ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    if [ ! -d ~/.agents ]; then
        echo -e "${YELLOW}ℹ️  ~/.agents/ not found — nothing to uninstall.${NC}"
        return 0
    fi

    uninstall_provider_symlinks "$HOME/.agents/skills" "Agents"
    local removed_links="$UNINSTALL_PROVIDER_LINKS_REMOVED"

    echo ""
    echo -e "${GREEN}✅ Removed $removed_links skill symlink(s)${NC}"
    echo -e "${CYAN}ℹ️  ~/.agents/AGENTS.md and user-added items are untouched.${NC}"
}

# ============================================================
# Argument parsing — subcommand dispatcher first, then legacy fallback
# ============================================================

UPDATE_MODE=false
GLOBAL_MODE=false
NO_CODEX=false
GLOBAL_TARGETS=""
PROJECT_PROVIDERS="all"
TARGET_DIR=""

# No arguments at all → show help. This prevents accidental install
# into the current directory when user just runs `./install.sh`.
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

# Try to parse as subcommand first (install/update/uninstall/help as $1)
SUBCOMMAND_CONSUMED=false
if [ $# -gt 0 ]; then
    case "$1" in
        install|update|uninstall|help)
            SUBCOMMAND_CONSUMED=true
            ACTION="$1"
            TARGET="${2:-}"

            case "$ACTION" in
                help)
                    show_usage
                    exit 0
                    ;;
                uninstall)
                    case "$TARGET" in
                        claude)
                            uninstall_claude_global
                            exit 0
                            ;;
                        codex)
                            uninstall_codex_global
                            exit 0
                            ;;
                        gemini)
                            uninstall_gemini_global
                            exit 0
                            ;;
                        opencode)
                            uninstall_opencode_global
                            exit 0
                            ;;
                        agents)
                            uninstall_agents_global
                            exit 0
                            ;;
                        all)
                            uninstall_codex_global
                            echo ""
                            uninstall_gemini_global
                            echo ""
                            uninstall_opencode_global
                            echo ""
                            uninstall_agents_global
                            echo ""
                            uninstall_claude_global
                            exit 0
                            ;;
                        "")
                            echo -e "${RED}❌ Error: 'uninstall' requires a target: claude | codex | gemini | opencode | agents | all${NC}"
                            echo ""
                            show_usage
                            exit 1
                            ;;
                        *)
                            echo -e "${RED}❌ Error: invalid uninstall target '$TARGET'. Valid: claude | codex | gemini | opencode | agents | all${NC}"
                            exit 1
                            ;;
                    esac
                    ;;
                install|update)
                    # Both install and update translate to legacy flags.
                    # The existing code is already idempotent, so update == re-install.
                    [ "$ACTION" = "update" ] && UPDATE_MODE=true

                    case "$TARGET" in
                        claude)
                            GLOBAL_MODE=true
                            UPDATE_MODE=true
                            NO_CODEX=true
                            GLOBAL_TARGETS="claude"
                            ;;
                        codex)
                            # Standalone Codex install: requires ~/.claude/ to exist already
                            if [ ! -d ~/.claude/skills ]; then
                                echo -e "${RED}❌ Error: ~/.claude/skills/ not found.${NC}"
                                echo -e "${YELLOW}   Codex mirror requires Claude to be installed first.${NC}"
                                echo -e "${YELLOW}   Run: ./install.sh install claude${NC}"
                                exit 1
                            fi
                            GLOBAL_MODE=true
                            UPDATE_MODE=true
                            NO_CODEX=false
                            GLOBAL_TARGETS="codex"
                            ;;
                        gemini|opencode|agents)
                            if [ ! -d ~/.claude/skills ]; then
                                echo -e "${RED}❌ Error: ~/.claude/skills/ not found.${NC}"
                                echo -e "${YELLOW}   $TARGET mirror requires Claude to be installed first.${NC}"
                                echo -e "${YELLOW}   Run: ./install.sh install claude${NC}"
                                exit 1
                            fi
                            GLOBAL_MODE=true
                            UPDATE_MODE=true
                            NO_CODEX=false
                            GLOBAL_TARGETS="$TARGET"
                            ;;
                        all)
                            GLOBAL_MODE=true
                            UPDATE_MODE=true
                            NO_CODEX=false
                            GLOBAL_TARGETS="all"
                            ;;
                        "")
                            echo -e "${RED}❌ Error: '$ACTION' requires a target: claude | codex | gemini | opencode | agents | all | <path>${NC}"
                            echo ""
                            show_usage
                            exit 1
                            ;;
                        *)
                            # Assume it's a path (absolute or relative)
                            TARGET_DIR="$TARGET"
                            ;;
                    esac

                    EXTRA_ARGS=("${@:3}")
                    extra_index=0
                    while [ $extra_index -lt ${#EXTRA_ARGS[@]} ]; do
                        extra_arg="${EXTRA_ARGS[$extra_index]}"
                        case "$extra_arg" in
                            --providers)
                                extra_index=$((extra_index + 1))
                                PROJECT_PROVIDERS="${EXTRA_ARGS[$extra_index]:-}"
                                if ! validate_provider_list "$PROJECT_PROVIDERS"; then
                                    echo -e "${RED}❌ Error: invalid --providers value '$PROJECT_PROVIDERS'.${NC}"
                                    echo -e "${YELLOW}   Valid: all | claude,codex,gemini,opencode,agents${NC}"
                                    exit 1
                                fi
                                ;;
                            --help|-h)
                                show_usage
                                exit 0
                                ;;
                            "")
                                ;;
                            *)
                                echo -e "${RED}❌ Error: unknown option '$extra_arg'${NC}"
                                echo ""
                                show_usage
                                exit 1
                                ;;
                        esac
                        extra_index=$((extra_index + 1))
                    done
                    ;;
            esac
            ;;
    esac
fi

# Legacy flag parsing (runs only if no subcommand was consumed)
if [ "$SUBCOMMAND_CONSUMED" = false ]; then
    LEGACY_FLAG_USED=""
    for arg in "$@"; do
        case $arg in
            --update)
                UPDATE_MODE=true
                LEGACY_FLAG_USED="--update"
                ;;
            --global)
                GLOBAL_MODE=true
                UPDATE_MODE=true
                LEGACY_FLAG_USED="--global"
                ;;
            --no-codex)
                NO_CODEX=true
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$TARGET_DIR" ]; then
                    TARGET_DIR="$arg"
                fi
                ;;
        esac
    done

    # Print deprecation warnings for legacy flags
    if [ -n "$LEGACY_FLAG_USED" ]; then
        if [ "$GLOBAL_MODE" = true ] && [ "$NO_CODEX" = true ]; then
            deprecation_warning "--global --no-codex" "install claude"
        elif [ "$GLOBAL_MODE" = true ]; then
            deprecation_warning "--global" "install all"
        elif [ "$UPDATE_MODE" = true ] && [ -n "$TARGET_DIR" ]; then
            deprecation_warning "--update" "update $TARGET_DIR"
        fi
    fi
fi

if [ "$GLOBAL_MODE" = true ] && [ -z "$GLOBAL_TARGETS" ]; then
    if [ "$NO_CODEX" = true ]; then
        GLOBAL_TARGETS="claude"
    else
        GLOBAL_TARGETS="all"
    fi
fi

# Global mode: install into ~/.claude/ (user-level, all projects)
if [ "$GLOBAL_MODE" = true ]; then
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║             D-EPCT+R Workflow v5.1 — Global Install                 ║"
    echo "║                                                                       ║"
    echo "║   Target: ~/.claude/ (available in ALL your projects)                 ║"
    echo "║   CLAUDE.md: merges workflow section, keeps your content              ║"
    echo "║   Preserves: settings.json, mcp.json                                 ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Determine source
    SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
    SCRIPT_DIR=""
    if [ -n "$SCRIPT_SOURCE" ] && [ "$SCRIPT_SOURCE" != "/dev/stdin" ] && [ -f "$SCRIPT_SOURCE" ]; then
        SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
    fi

    IS_REPO=false
    if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/install.sh" ] && [ -d "$SCRIPT_DIR/.claude/skills" ]; then
        IS_REPO=true
        SOURCE_DIR="$SCRIPT_DIR/.claude"
    fi

    if [ "$IS_REPO" = false ]; then
        echo -e "${BLUE}📥 Downloading from GitHub...${NC}"
        TEMP_DIR=$(mktemp -d)
        trap "rm -rf $TEMP_DIR" EXIT
        git clone --depth 1 --quiet "$REPO_URL" "$TEMP_DIR/$REPO_NAME"
        SOURCE_DIR="$TEMP_DIR/$REPO_NAME/.claude"
        echo -e "${GREEN}✅ Downloaded${NC}"
    fi

    # Ensure ~/.claude/ exists
    mkdir -p ~/.claude

    # Provider-only installs reuse ~/.claude as the single source of truth.
    if ! global_target_enabled claude; then
        if [ ! -d ~/.claude/skills ]; then
            echo -e "${RED}❌ Error: ~/.claude/skills/ not found.${NC}"
            echo -e "${YELLOW}   Provider mirrors require Claude to be installed first.${NC}"
            echo -e "${YELLOW}   Run: ./install.sh install claude${NC}"
            exit 1
        fi
        echo -e "${CYAN}ℹ️  Provider-only mode — skipping Claude sync, reusing existing ~/.claude/${NC}"
        echo ""
    else

    # ------------------------------------------------------------
    # Manifest-based orphan purge (Claude side)
    # Skills & commands that were installed by Skillz in a previous
    # run but are no longer in the source are removed. User-added
    # items (never listed in the manifest) are left untouched.
    # ------------------------------------------------------------
    MANIFEST_FILE="$HOME/.claude/.skillz-manifest"
    # Build set of currently-managed items from the source
    NEW_SKILLS=$(find "$SOURCE_DIR/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null \
        | xargs -n1 basename 2>/dev/null | sort)
    NEW_COMMANDS=$(find "$SOURCE_DIR/commands" -mindepth 1 -maxdepth 1 -name '*.md' 2>/dev/null \
        | xargs -n1 basename 2>/dev/null | sort)

    if [ -f "$MANIFEST_FILE" ]; then
        echo -e "${CYAN}🧹 Checking for orphaned skills/commands (drift cleanup)...${NC}"
        purged_skills=0
        purged_commands=0
        while IFS= read -r line; do
            [ -z "$line" ] && continue
            case "$line" in \#*) continue ;; esac
            type="${line%%:*}"
            name="${line#*:}"
            case "$type" in
                skill)
                    if ! echo "$NEW_SKILLS" | grep -qx "$name"; then
                        if [ -d "$HOME/.claude/skills/$name" ] || [ -L "$HOME/.claude/skills/$name" ]; then
                            rm -rf "$HOME/.claude/skills/$name"
                            echo -e "   ${YELLOW}🗑️  skill: $name (removed, no longer in source)${NC}"
                            purged_skills=$((purged_skills + 1))
                        fi
                    fi
                    ;;
                command)
                    if ! echo "$NEW_COMMANDS" | grep -qx "$name"; then
                        if [ -f "$HOME/.claude/commands/$name" ] || [ -L "$HOME/.claude/commands/$name" ]; then
                            rm -f "$HOME/.claude/commands/$name"
                            echo -e "   ${YELLOW}🗑️  command: $name (removed, no longer in source)${NC}"
                            purged_commands=$((purged_commands + 1))
                        fi
                    fi
                    ;;
            esac
        done < "$MANIFEST_FILE"
        total_purged=$((purged_skills + purged_commands))
        if [ "$total_purged" -gt 0 ]; then
            echo -e "   ${GREEN}✅ $purged_skills skill(s), $purged_commands command(s) purged${NC}"
        else
            echo -e "   ${GREEN}✅ No drift detected${NC}"
        fi
    else
        echo -e "${CYAN}ℹ️  First run with manifest — creating baseline (no purge this time)${NC}"
    fi

    # rsync contents, preserving settings.json and mcp.json (CLAUDE.md handled separately)
    echo -e "${CYAN}🔄 Syncing skills, commands, knowledge, templates...${NC}"
    rsync -a \
        --exclude='CLAUDE.md' \
        --exclude='settings.json' \
        --exclude='mcp.json' \
        --exclude='.skillz-manifest' \
        "$SOURCE_DIR/" ~/.claude/

    # Write fresh manifest — always after successful rsync
    {
        echo "# skillz-manifest v1"
        echo "# Auto-generated by install.sh --global on $(date '+%Y-%m-%d %H:%M:%S')"
        echo "# Lists skills/commands installed by Skillz (for drift detection on next run)"
        echo "# DO NOT EDIT MANUALLY"
        for s in $NEW_SKILLS; do echo "skill:$s"; done
        for c in $NEW_COMMANDS; do echo "command:$c"; done
    } > "$MANIFEST_FILE"

    # Merge CLAUDE.md: preserve user content, update D-EPCT+R section
    echo -e "${CYAN}🔄 Merging CLAUDE.md...${NC}"
    if [ -f ~/.claude/CLAUDE.md ] && [ -f "$SOURCE_DIR/CLAUDE.md" ]; then
        # Extract the D-EPCT section from the new source
        NEW_DEPCT=$(sed -n '/<!-- D-EPCT-START -->/,/<!-- D-EPCT-END -->/p' "$SOURCE_DIR/CLAUDE.md")

        if grep -q "<!-- D-EPCT-START -->" ~/.claude/CLAUDE.md 2>/dev/null; then
            # User already has D-EPCT markers → replace that section
            TEMP_MERGE=$(mktemp)
            awk '
                /<!-- D-EPCT-START -->/ { skip=1; next }
                /<!-- D-EPCT-END -->/ { skip=0; next }
                !skip { print }
            ' ~/.claude/CLAUDE.md > "$TEMP_MERGE"
            # Append the new D-EPCT section
            echo "" >> "$TEMP_MERGE"
            echo "$NEW_DEPCT" >> "$TEMP_MERGE"
            mv "$TEMP_MERGE" ~/.claude/CLAUDE.md
            echo -e "   ${CYAN}🔄 D-EPCT+R section updated (your content preserved)${NC}"
        else
            # No D-EPCT markers → append at the end
            echo "" >> ~/.claude/CLAUDE.md
            echo "$NEW_DEPCT" >> ~/.claude/CLAUDE.md
            echo -e "   ${GREEN}✅ D-EPCT+R section added to your CLAUDE.md${NC}"
        fi
    elif [ -f "$SOURCE_DIR/CLAUDE.md" ]; then
        # No existing CLAUDE.md → copy as-is
        cp "$SOURCE_DIR/CLAUDE.md" ~/.claude/CLAUDE.md
        echo -e "   ${GREEN}✅ CLAUDE.md created${NC}"
    fi

    # Count what was installed
    skills_count=$(ls -1d ~/.claude/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' ')
    commands_count=$(ls -1 ~/.claude/commands/*.md 2>/dev/null | wc -l | tr -d ' ')
    knowledge_count=$(find ~/.claude/knowledge -type f 2>/dev/null | wc -l | tr -d ' ')

    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗"
    echo -e "║                       ✅ Global Install Complete!                    ║"
    echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "   ${GREEN}✅ Skills:    $skills_count${NC}"
    echo -e "   ${GREEN}✅ Commands:  $commands_count${NC}"
    echo -e "   ${GREEN}✅ Knowledge: $knowledge_count files${NC}"
    echo -e "   ${GREEN}✅ Templates, hooks, examples${NC}"
    echo -e "   ${GREEN}✅ CLAUDE.md: D-EPCT+R section merged${NC}"
    echo ""
    echo -e "${GREEN}Preserved (your config):${NC}"
    echo -e "   ${GREEN}✅ ~/.claude/CLAUDE.md (your content kept, workflow updated)${NC}"
    echo -e "   ${GREEN}✅ ~/.claude/settings.json${NC}"
    echo -e "   ${GREEN}✅ ~/.claude/mcp.json${NC}"
    echo ""
    echo -e "${CYAN}These skills & commands are now available in ALL your projects.${NC}"
    echo -e "${CYAN}To update later: run the same command again.${NC}"
    echo ""

    fi  # end of Claude sync guard

    # ====================================================================
    # Codex CLI install (symlinks ~/.claude/* into ~/.codex/*)
    # ====================================================================
    if global_target_enabled codex; then
        if [ ! -d ~/.codex ]; then
            echo -e "${YELLOW}ℹ️  ~/.codex/ not found — Codex CLI doesn't seem installed.${NC}"
            echo -e "${YELLOW}    Skipping Codex install.${NC}"
            echo ""
        else
            echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════╗"
            echo -e "║         Mirroring into ~/.codex/ (Codex CLI compatibility)            ║"
            echo -e "║   Skills & prompts symlinked → single source of truth in ~/.claude    ║"
            echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
            echo ""

            mkdir -p ~/.codex/skills
            mkdir -p ~/.codex/prompts

    # 0. Sweep dead symlinks left over from previous runs (e.g. skills removed from
    #    ~/.claude/skills/). Only symlinks are touched — real dirs/files are left alone.
    echo -e "${CYAN}🧹 Sweeping dead symlinks in ~/.codex/skills & prompts...${NC}"
    dead_skill_links=0
    for link in "$HOME/.codex/skills"/*; do
        [ -L "$link" ] || continue
        name=$(basename "$link")
        case "$name" in .system|.*) continue ;; esac
        if [ ! -e "$link" ]; then
            rm -f "$link"
            echo -e "   ${YELLOW}🗑️  skill: $name (dead link removed)${NC}"
            dead_skill_links=$((dead_skill_links + 1))
        fi
    done
    dead_prompt_links=0
    for link in "$HOME/.codex/prompts"/*; do
        [ -L "$link" ] || continue
        if [ ! -e "$link" ]; then
            name=$(basename "$link")
            rm -f "$link"
            echo -e "   ${YELLOW}🗑️  prompt: $name (dead link removed)${NC}"
            dead_prompt_links=$((dead_prompt_links + 1))
        fi
    done
    total_dead=$((dead_skill_links + dead_prompt_links))
    if [ "$total_dead" -gt 0 ]; then
        echo -e "   ${GREEN}✅ $dead_skill_links dead skill link(s), $dead_prompt_links dead prompt link(s) removed${NC}"
    else
        echo -e "   ${GREEN}✅ No dead links${NC}"
    fi

    # 1. Symlink each skill (preserving native .system/ folder & hidden files)
    echo -e "${CYAN}🔗 Symlinking skills → ~/.codex/skills/...${NC}"
    skill_link_count=0
    skill_skip_count=0
    for skill_dir in ~/.claude/skills/*/; do
        [ -d "$skill_dir" ] || continue
        name=$(basename "$skill_dir")
        # Never override Codex system skills (.system/) or hidden entries
        case "$name" in
            .system|.*) continue ;;
        esac
        target="$HOME/.codex/skills/$name"
        # Skip if a non-symlink directory already exists at target — don't clobber user data
        if [ -e "$target" ] && [ ! -L "$target" ]; then
            echo -e "   ${YELLOW}⚠️  $name (skipped — exists as real dir, not symlink)${NC}"
            skill_skip_count=$((skill_skip_count + 1))
            continue
        fi
        ln -sfn "$skill_dir" "$target"
        skill_link_count=$((skill_link_count + 1))
    done
    echo -e "   ${GREEN}✅ $skill_link_count skills linked${NC}"
    if [ "$skill_skip_count" -gt 0 ]; then
        echo -e "   ${YELLOW}⚠️  $skill_skip_count skipped (real dirs — delete manually if you want them mirrored)${NC}"
    fi

    # 2. Copy Codex-native prompts from source .codex/prompts/ → ~/.codex/prompts/
    #
    # IMPORTANT: we do NOT symlink ~/.claude/commands → ~/.codex/prompts anymore.
    # Claude commands use $ARGUMENTS and Claude-specific tools (SendMessage,
    # TaskCreate, parallel subagents) that don't work in Codex. Instead, we ship
    # a separate set of Codex-native prompts in .codex/prompts/ in the repo that
    # are short BMad-style triggers loading shared workflow skills.
    SOURCE_CODEX_PROMPTS="$(dirname "$SOURCE_DIR")/.codex/prompts"
    if [ -d "$SOURCE_CODEX_PROMPTS" ]; then
        echo -e "${CYAN}📋 Copying Codex-native prompts → ~/.codex/prompts/...${NC}"
        prompt_copy_count=0
        prompt_skip_count=0
        for prompt_file in "$SOURCE_CODEX_PROMPTS"/*.md; do
            [ -f "$prompt_file" ] || continue
            name=$(basename "$prompt_file")
            target="$HOME/.codex/prompts/$name"
            # If a real file exists at target AND it's NOT one of our managed prompts,
            # skip it to preserve user-added or third-party prompts (BMad, etc.).
            # We detect "ours" by comparing content — if it exists and differs from
            # source but isn't a symlink, assume it's user-managed and skip.
            if [ -e "$target" ] && [ ! -L "$target" ]; then
                # Safe to overwrite if content matches (already copied from us) OR
                # if the existing file looks like a dead symlink that got replaced.
                if ! cmp -s "$prompt_file" "$target"; then
                    echo -e "   ${YELLOW}⚠️  $name (skipped — real file with different content)${NC}"
                    prompt_skip_count=$((prompt_skip_count + 1))
                    continue
                fi
            fi
            # Remove any existing symlink (including dead ones from previous runs)
            [ -L "$target" ] && rm -f "$target"
            cp "$prompt_file" "$target"
            prompt_copy_count=$((prompt_copy_count + 1))
        done
        echo -e "   ${GREEN}✅ $prompt_copy_count Codex prompts copied${NC}"
        if [ "$prompt_skip_count" -gt 0 ]; then
            echo -e "   ${YELLOW}⚠️  $prompt_skip_count skipped (existing files with different content)${NC}"
        fi
    else
        echo -e "${YELLOW}ℹ️  No .codex/prompts/ in source — skipping Codex prompts${NC}"
    fi

    # 3. Generate ~/.codex/AGENTS.md from ~/.claude/CLAUDE.md (replace H1, add header)
    if [ -f ~/.claude/CLAUDE.md ]; then
        echo -e "${CYAN}📝 Generating ~/.codex/AGENTS.md from ~/.claude/CLAUDE.md...${NC}"
        TEMP_AGENTS=$(mktemp)
        {
            echo "# Agent Instructions"
            echo ""
            echo "<!-- Auto-generated from ~/.claude/CLAUDE.md by Skillz-Claude installer. -->"
            echo "<!-- Edit ~/.claude/CLAUDE.md and re-run \`./install.sh update codex\` to update. -->"
            echo ""
            tail -n +2 ~/.claude/CLAUDE.md
        } > "$TEMP_AGENTS"
        mv "$TEMP_AGENTS" ~/.codex/AGENTS.md
        echo -e "   ${GREEN}✅ ~/.codex/AGENTS.md${NC}"
    fi

    # Codex install summary
    codex_skills=$(find ~/.codex/skills -mindepth 1 -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')
    # Count only the Codex-native prompts we manage (those present in source)
    codex_prompts=0
    if [ -d "$SOURCE_CODEX_PROMPTS" ]; then
        for prompt_file in "$SOURCE_CODEX_PROMPTS"/*.md; do
            [ -f "$prompt_file" ] || continue
            name=$(basename "$prompt_file")
            [ -f "$HOME/.codex/prompts/$name" ] && codex_prompts=$((codex_prompts + 1))
        done
    fi

    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗"
    echo -e "║                  ✅ Codex Mirror Complete!                          ║"
    echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "   ${GREEN}✅ Skills (symlinks):       $codex_skills${NC}"
    echo -e "   ${GREEN}✅ Codex-native prompts:    $codex_prompts${NC}"
    echo -e "   ${GREEN}✅ AGENTS.md generated${NC}"
    echo -e "   ${GREEN}✅ Native ~/.codex/skills/.system/ preserved${NC}"
    echo -e "   ${GREEN}✅ Third-party prompts (BMad, etc.) preserved${NC}"
    echo ""
    echo -e "${YELLOW}ℹ️  MCP servers in ~/.codex/config.toml are untouched.${NC}"
    echo -e "${YELLOW}    To mirror Claude MCPs, edit config.toml manually under [mcp_servers.X].${NC}"
    echo ""
    echo -e "${CYAN}Codex will now see your skills & slash commands the same as Claude.${NC}"
    echo ""
        fi
    fi

    # ====================================================================
    # Gemini CLI install
    # ====================================================================
    if global_target_enabled gemini; then
        echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════╗"
        echo -e "║         Mirroring into ~/.gemini/ (Gemini CLI compatibility)          ║"
        echo -e "║   Skills, commands, and GEMINI.md generated from ~/.claude            ║"
        echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        mkdir -p ~/.gemini
        if [ -L "$HOME/.gemini/skills" ]; then
            rm -f "$HOME/.gemini/skills"
        fi
        if [ -L "$HOME/.gemini/knowledge" ]; then
            rm -f "$HOME/.gemini/knowledge"
        fi
        mkdir -p ~/.gemini/skills ~/.gemini/knowledge ~/.gemini/commands

        gemini_skill_count=0
        gemini_skill_skip_count=0
        for skill_dir in ~/.claude/skills/*/; do
            [ -d "$skill_dir" ] || continue
            name=$(basename "$skill_dir")
            target="$HOME/.gemini/skills/$name"
            if [ -e "$target" ] && [ ! -L "$target" ]; then
                echo -e "   ${YELLOW}⚠️  $name (skipped — exists as real dir, not symlink)${NC}"
                gemini_skill_skip_count=$((gemini_skill_skip_count + 1))
                continue
            fi
            ln -sfn "$skill_dir" "$target"
            gemini_skill_count=$((gemini_skill_count + 1))
        done

        if [ -d ~/.claude/knowledge ]; then
            ln -sfn "$HOME/.claude/knowledge" "$HOME/.gemini/knowledge/skillz"
        fi

        SOURCE_GEMINI_COMMANDS="$(dirname "$SOURCE_DIR")/.gemini/commands"
        gemini_command_count=0
        if [ -d "$SOURCE_GEMINI_COMMANDS" ]; then
            for command_file in "$SOURCE_GEMINI_COMMANDS"/*.toml; do
                [ -f "$command_file" ] || continue
                cp "$command_file" "$HOME/.gemini/commands/"
                gemini_command_count=$((gemini_command_count + 1))
            done
        fi

        if [ -f ~/.claude/CLAUDE.md ]; then
            TEMP_GEMINI=$(mktemp)
            {
                echo "# Gemini Instructions"
                echo ""
                echo "<!-- Auto-generated from ~/.claude/CLAUDE.md by Skillz-Claude installer. -->"
                echo "<!-- Edit ~/.claude/CLAUDE.md and re-run \`./install.sh update gemini\` to update. -->"
                echo ""
                tail -n +2 ~/.claude/CLAUDE.md
            } > "$TEMP_GEMINI"
            mv "$TEMP_GEMINI" ~/.gemini/GEMINI.md
        fi

        echo -e "   ${GREEN}✅ Skills linked:       $gemini_skill_count${NC}"
        echo -e "   ${GREEN}✅ Gemini commands:     $gemini_command_count${NC}"
        echo -e "   ${GREEN}✅ GEMINI.md generated${NC}"
        if [ "$gemini_skill_skip_count" -gt 0 ]; then
            echo -e "   ${YELLOW}⚠️  $gemini_skill_skip_count skipped (real dirs — delete manually if you want them mirrored)${NC}"
        fi
        echo ""
    fi

    # ====================================================================
    # OpenCode install
    # ====================================================================
    if global_target_enabled opencode; then
        OPENCODE_HOME="$HOME/.config/opencode"
        echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════╗"
        echo -e "║       Mirroring into ~/.config/opencode/ (OpenCode compatibility)     ║"
        echo -e "║   Skills, commands, and AGENTS.md generated from ~/.claude            ║"
        echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        mkdir -p "$OPENCODE_HOME"
        if [ -L "$OPENCODE_HOME/skills" ]; then
            rm -f "$OPENCODE_HOME/skills"
        fi
        if [ -L "$OPENCODE_HOME/knowledge" ]; then
            rm -f "$OPENCODE_HOME/knowledge"
        fi
        mkdir -p "$OPENCODE_HOME/skills" "$OPENCODE_HOME/knowledge" "$OPENCODE_HOME/commands"

        opencode_skill_count=0
        opencode_skill_skip_count=0
        for skill_dir in ~/.claude/skills/*/; do
            [ -d "$skill_dir" ] || continue
            name=$(basename "$skill_dir")
            target="$OPENCODE_HOME/skills/$name"
            if [ -e "$target" ] && [ ! -L "$target" ]; then
                echo -e "   ${YELLOW}⚠️  $name (skipped — exists as real dir, not symlink)${NC}"
                opencode_skill_skip_count=$((opencode_skill_skip_count + 1))
                continue
            fi
            ln -sfn "$skill_dir" "$target"
            opencode_skill_count=$((opencode_skill_count + 1))
        done

        if [ -d ~/.claude/knowledge ]; then
            ln -sfn "$HOME/.claude/knowledge" "$OPENCODE_HOME/knowledge/skillz"
        fi

        SOURCE_OPENCODE_COMMANDS="$(dirname "$SOURCE_DIR")/.opencode/commands"
        opencode_command_count=0
        if [ -d "$SOURCE_OPENCODE_COMMANDS" ]; then
            for command_file in "$SOURCE_OPENCODE_COMMANDS"/*.md; do
                [ -f "$command_file" ] || continue
                cp "$command_file" "$OPENCODE_HOME/commands/"
                opencode_command_count=$((opencode_command_count + 1))
            done
        fi

        if [ -f ~/.claude/CLAUDE.md ]; then
            TEMP_OPENCODE=$(mktemp)
            {
                echo "# Agent Instructions"
                echo ""
                echo "<!-- Auto-generated from ~/.claude/CLAUDE.md by Skillz-Claude installer. -->"
                echo "<!-- Edit ~/.claude/CLAUDE.md and re-run \`./install.sh update opencode\` to update. -->"
                echo ""
                tail -n +2 ~/.claude/CLAUDE.md
            } > "$TEMP_OPENCODE"
            mv "$TEMP_OPENCODE" "$OPENCODE_HOME/AGENTS.md"
        fi

        echo -e "   ${GREEN}✅ Skills linked:       $opencode_skill_count${NC}"
        echo -e "   ${GREEN}✅ OpenCode commands:   $opencode_command_count${NC}"
        echo -e "   ${GREEN}✅ AGENTS.md generated${NC}"
        if [ "$opencode_skill_skip_count" -gt 0 ]; then
            echo -e "   ${YELLOW}⚠️  $opencode_skill_skip_count skipped (real dirs — delete manually if you want them mirrored)${NC}"
        fi
        echo ""
    fi

    # ====================================================================
    # Generic ~/.agents install
    # ====================================================================
    if global_target_enabled agents; then
        echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════╗"
        echo -e "║          Mirroring into ~/.agents/ (generic agent compatibility)      ║"
        echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        mkdir -p ~/.agents
        if [ -L "$HOME/.agents/skills" ]; then
            rm -f "$HOME/.agents/skills"
        fi
        mkdir -p ~/.agents/skills ~/.agents/knowledge

        agents_skill_count=0
        agents_skill_skip_count=0
        for skill_dir in ~/.claude/skills/*/; do
            [ -d "$skill_dir" ] || continue
            name=$(basename "$skill_dir")
            target="$HOME/.agents/skills/$name"
            if [ -e "$target" ] && [ ! -L "$target" ]; then
                echo -e "   ${YELLOW}⚠️  $name (skipped — exists as real dir, not symlink)${NC}"
                agents_skill_skip_count=$((agents_skill_skip_count + 1))
                continue
            fi
            ln -sfn "$skill_dir" "$target"
            agents_skill_count=$((agents_skill_count + 1))
        done

        if [ -d ~/.claude/knowledge ]; then
            ln -sfn "$HOME/.claude/knowledge" "$HOME/.agents/knowledge/skillz"
        fi

        if [ -f ~/.claude/CLAUDE.md ]; then
            TEMP_AGENTS_GLOBAL=$(mktemp)
            {
                echo "# Agent Instructions"
                echo ""
                echo "<!-- Auto-generated from ~/.claude/CLAUDE.md by Skillz-Claude installer. -->"
                echo "<!-- Edit ~/.claude/CLAUDE.md and re-run \`./install.sh update agents\` to update. -->"
                echo ""
                tail -n +2 ~/.claude/CLAUDE.md
            } > "$TEMP_AGENTS_GLOBAL"
            mv "$TEMP_AGENTS_GLOBAL" ~/.agents/AGENTS.md
        fi

        echo -e "   ${GREEN}✅ Skills linked:       $agents_skill_count${NC}"
        echo -e "   ${GREEN}✅ AGENTS.md generated${NC}"
        if [ "$agents_skill_skip_count" -gt 0 ]; then
            echo -e "   ${YELLOW}⚠️  $agents_skill_skip_count skipped (real dirs — delete manually if you want them mirrored)${NC}"
        fi
        echo ""
    fi

    exit 0
fi

# Default target is current directory
TARGET_DIR="${TARGET_DIR:-.}"
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)" || TARGET_DIR="$(pwd)/${TARGET_DIR}"
TARGET_CLAUDE="$TARGET_DIR/.claude"
TARGET_DOCS="$TARGET_DIR/docs"

# Display header
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
if [ "$UPDATE_MODE" = true ]; then
echo "║             D-EPCT+R Workflow v5.1 Updater                            ║"
else
echo "║             D-EPCT+R Workflow v5.1 Installer                          ║"
fi
echo "║                                                                       ║"
echo "║   SKILLS:       33 (Planning, Design, Dev, Security, Figma, Audio/Video)║"
echo "║   COMMANDS:     21 (Manuel + RALPH + Ship/QA/Retro)                   ║"
echo "║   TEMPLATES:    18 (CI/CD, Git Hooks, DevContainer, GitHub)           ║"
echo "║   KNOWLEDGE:    54 fichiers (testing, workflows, security, figma)     ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Update mode info
if [ "$UPDATE_MODE" = true ]; then
    echo -e "${CYAN}🔄 Mode UPDATE activé${NC}"
    echo -e "   → Skills, commands, hooks, examples, knowledge, templates seront mis à jour"
    echo -e "   → CLAUDE.md, settings.json, mcp.json seront préservés"
    echo ""
fi

# Determine source directory
# If run via curl pipe, we need to clone the repo first
SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
SCRIPT_DIR=""

# Only set SCRIPT_DIR if we have a real file path (not stdin/pipe)
if [ -n "$SCRIPT_SOURCE" ] && [ "$SCRIPT_SOURCE" != "/dev/stdin" ] && [ -f "$SCRIPT_SOURCE" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
fi

# Check if running from the actual Skillz-Claude repo (has install.sh AND .claude/skills/)
IS_REPO=false
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/install.sh" ] && [ -d "$SCRIPT_DIR/.claude/skills" ]; then
    IS_REPO=true
fi

if [ "$IS_REPO" = false ]; then
    # Running via curl pipe or not from repo - need to clone
    echo -e "${BLUE}📥 Downloading D-EPCT+R workflow from GitHub...${NC}"

    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    if command -v git &> /dev/null; then
        git clone --depth 1 --quiet "$REPO_URL" "$TEMP_DIR/$REPO_NAME"
    else
        echo -e "${RED}❌ Error: git is required but not installed${NC}"
        exit 1
    fi

    SOURCE_CLAUDE="$TEMP_DIR/$REPO_NAME/.claude"
    echo -e "${GREEN}✅ Downloaded successfully${NC}"
    echo ""
else
    # Running from cloned Skillz-Claude repo
    SOURCE_CLAUDE="$SCRIPT_DIR/.claude"
fi

# Check source exists
if [ ! -d "$SOURCE_CLAUDE" ]; then
    echo -e "${RED}❌ Error: .claude directory not found${NC}"
    exit 1
fi

# Check if target already has .claude (for non-update mode)
MERGE_MODE=false
if [ -d "$TARGET_CLAUDE" ]; then
    if [ "$UPDATE_MODE" = true ]; then
        # Update mode - no confirmation needed
        echo -e "${BLUE}📦 Updating D-EPCT+R workflow in $TARGET_DIR...${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: .claude directory already exists in $TARGET_DIR${NC}"
        echo ""
        echo -e "   Pour mettre à jour, utilisez: ${CYAN}--update${NC}"
        echo ""
        read -p "Do you want to merge (skip existing files)? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ Installation cancelled${NC}"
            exit 1
        fi
        MERGE_MODE=true
    fi
else
    if [ "$UPDATE_MODE" = true ]; then
        echo -e "${YELLOW}⚠️  No existing installation found. Running fresh install...${NC}"
        UPDATE_MODE=false
    fi
fi

if [ "$UPDATE_MODE" != true ] && [ "$MERGE_MODE" != true ]; then
    echo -e "${BLUE}📦 Installing D-EPCT+R workflow v5.1 to $TARGET_DIR...${NC}"
fi
echo ""

# Create directories if needed
mkdir -p "$TARGET_CLAUDE/skills"
mkdir -p "$TARGET_CLAUDE/commands"
mkdir -p "$TARGET_CLAUDE/hooks"
mkdir -p "$TARGET_CLAUDE/knowledge/testing"
mkdir -p "$TARGET_CLAUDE/knowledge/workflows"
mkdir -p "$TARGET_CLAUDE/knowledge/brainstorming"
mkdir -p "$TARGET_CLAUDE/knowledge/multi-mind"
mkdir -p "$TARGET_CLAUDE/knowledge/supabase-security"
mkdir -p "$TARGET_CLAUDE/knowledge/figma"
mkdir -p "$TARGET_CLAUDE/templates/github-actions"
mkdir -p "$TARGET_CLAUDE/templates/github/ISSUE_TEMPLATE"
mkdir -p "$TARGET_CLAUDE/templates/git-hooks"
mkdir -p "$TARGET_CLAUDE/templates/devcontainer"

# Create docs structure
echo -e "${GREEN}📁 Creating docs structure...${NC}"
mkdir -p "$TARGET_DOCS/planning/brainstorms"
mkdir -p "$TARGET_DOCS/planning/ux"
mkdir -p "$TARGET_DOCS/planning/prd"
mkdir -p "$TARGET_DOCS/planning/ui"
mkdir -p "$TARGET_DOCS/planning/architecture"
mkdir -p "$TARGET_DOCS/stories"
mkdir -p "$TARGET_DOCS/ralph-logs"
mkdir -p "$TARGET_DOCS/debates"
mkdir -p "$TARGET_DOCS/security"
echo -e "   ${GREEN}✅ docs/planning/brainstorms/${NC}"
echo -e "   ${GREEN}✅ docs/planning/ux/${NC}"
echo -e "   ${GREEN}✅ docs/planning/prd/${NC}"
echo -e "   ${GREEN}✅ docs/planning/ui/${NC}"
echo -e "   ${GREEN}✅ docs/planning/architecture/${NC}"
echo -e "   ${GREEN}✅ docs/stories/${NC}"
echo -e "   ${GREEN}✅ docs/ralph-logs/${NC}"
echo -e "   ${GREEN}✅ docs/debates/${NC}"
echo -e "   ${GREEN}✅ docs/security/${NC}"

# Copy knowledge base (always update in UPDATE_MODE)
echo -e "${GREEN}📚 Installing Knowledge Base (54 files)...${NC}"
if [ -d "$SOURCE_CLAUDE/knowledge" ]; then
    # Copy testing knowledge (32 files)
    if [ -d "$SOURCE_CLAUDE/knowledge/testing" ]; then
        cp -r "$SOURCE_CLAUDE/knowledge/testing/"* "$TARGET_CLAUDE/knowledge/testing/" 2>/dev/null || true
        testing_count=$(ls -1 "$SOURCE_CLAUDE/knowledge/testing/"*.md 2>/dev/null | wc -l | tr -d ' ')
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${CYAN}🔄 testing/ ($testing_count files)${NC}"
        else
            echo -e "   ${GREEN}✅ testing/ ($testing_count files)${NC}"
        fi
    fi
    # Copy workflows knowledge
    if [ -d "$SOURCE_CLAUDE/knowledge/workflows" ]; then
        cp -r "$SOURCE_CLAUDE/knowledge/workflows/"* "$TARGET_CLAUDE/knowledge/workflows/" 2>/dev/null || true
        workflows_count=$(ls -1 "$SOURCE_CLAUDE/knowledge/workflows/"* 2>/dev/null | wc -l | tr -d ' ')
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${CYAN}🔄 workflows/ ($workflows_count files)${NC}"
        else
            echo -e "   ${GREEN}✅ workflows/ ($workflows_count files)${NC}"
        fi
    fi
    # Copy brainstorming knowledge (NEW v3.6)
    if [ -d "$SOURCE_CLAUDE/knowledge/brainstorming" ]; then
        cp -r "$SOURCE_CLAUDE/knowledge/brainstorming/"* "$TARGET_CLAUDE/knowledge/brainstorming/" 2>/dev/null || true
        brain_count=$(ls -1 "$SOURCE_CLAUDE/knowledge/brainstorming/"* 2>/dev/null | wc -l | tr -d ' ')
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${CYAN}🔄 brainstorming/ ($brain_count files)${NC}"
        else
            echo -e "   ${GREEN}✅ brainstorming/ ($brain_count files)${NC}"
        fi
    fi
    # Copy multi-mind knowledge (NEW v3.5)
    if [ -d "$SOURCE_CLAUDE/knowledge/multi-mind" ]; then
        cp -r "$SOURCE_CLAUDE/knowledge/multi-mind/"* "$TARGET_CLAUDE/knowledge/multi-mind/" 2>/dev/null || true
        mm_count=$(ls -1 "$SOURCE_CLAUDE/knowledge/multi-mind/"* 2>/dev/null | wc -l | tr -d ' ')
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${CYAN}🔄 multi-mind/ ($mm_count files)${NC}"
        else
            echo -e "   ${GREEN}✅ multi-mind/ ($mm_count files)${NC}"
        fi
    fi
    # Copy supabase-security knowledge (NEW v3.7)
    if [ -d "$SOURCE_CLAUDE/knowledge/supabase-security" ]; then
        cp -r "$SOURCE_CLAUDE/knowledge/supabase-security/"* "$TARGET_CLAUDE/knowledge/supabase-security/" 2>/dev/null || true
        supa_count=$(ls -1 "$SOURCE_CLAUDE/knowledge/supabase-security/"* 2>/dev/null | wc -l | tr -d ' ')
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${CYAN}🔄 supabase-security/ ($supa_count files)${NC}"
        else
            echo -e "   ${GREEN}✅ supabase-security/ ($supa_count files)${NC}"
        fi
    fi
    # Copy figma knowledge (NEW v3.8)
    if [ -d "$SOURCE_CLAUDE/knowledge/figma" ]; then
        cp -r "$SOURCE_CLAUDE/knowledge/figma/"* "$TARGET_CLAUDE/knowledge/figma/" 2>/dev/null || true
        figma_count=$(ls -1 "$SOURCE_CLAUDE/knowledge/figma/"* 2>/dev/null | wc -l | tr -d ' ')
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${CYAN}🔄 figma/ ($figma_count files)${NC}"
        else
            echo -e "   ${GREEN}✅ figma/ ($figma_count files)${NC}"
        fi
    fi
    # Copy index (only if source != destination)
    if [ -f "$SOURCE_CLAUDE/knowledge/tea-index.csv" ]; then
        SOURCE_INDEX="$(cd "$(dirname "$SOURCE_CLAUDE/knowledge/tea-index.csv")" && pwd)/tea-index.csv"
        TARGET_INDEX="$TARGET_CLAUDE/knowledge/tea-index.csv"
        if [ "$SOURCE_INDEX" != "$TARGET_INDEX" ]; then
            cp "$SOURCE_CLAUDE/knowledge/tea-index.csv" "$TARGET_CLAUDE/knowledge/"
            if [ "$UPDATE_MODE" = true ]; then
                echo -e "   ${CYAN}🔄 tea-index.csv${NC}"
            else
                echo -e "   ${GREEN}✅ tea-index.csv${NC}"
            fi
        else
            echo -e "   ${GREEN}✅ tea-index.csv (already in place)${NC}"
        fi
    fi
fi

# Copy skills
echo -e "${GREEN}📁 Installing skills (33)...${NC}"
for skill_dir in "$SOURCE_CLAUDE/skills"/*; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        target_skill="$TARGET_CLAUDE/skills/$skill_name"

        # Skip if source and target are the same location
        SOURCE_REAL="$(cd "$skill_dir" && pwd)"
        TARGET_REAL="$TARGET_CLAUDE/skills/$skill_name"
        if [ -d "$TARGET_REAL" ]; then
            TARGET_REAL="$(cd "$TARGET_REAL" && pwd)"
        fi

        if [ "$SOURCE_REAL" = "$TARGET_REAL" ]; then
            echo -e "   ${GREEN}✅ $skill_name (already in place)${NC}"
            continue
        fi

        if [ "$UPDATE_MODE" = true ]; then
            # Update mode: always overwrite skills
            rm -rf "$target_skill"
            cp -R "$skill_dir" "$TARGET_CLAUDE/skills/"
            echo -e "   ${CYAN}🔄 $skill_name${NC}"
        elif [ -d "$target_skill" ] && [ "$MERGE_MODE" = true ]; then
            echo -e "   ${YELLOW}⚠️  Skipping $skill_name (already exists)${NC}"
        else
            cp -R "$skill_dir" "$TARGET_CLAUDE/skills/"
            echo -e "   ${GREEN}✅ $skill_name${NC}"
        fi
    fi
done

# Copy commands
echo -e "${GREEN}📁 Installing commands (21)...${NC}"
for cmd_file in "$SOURCE_CLAUDE/commands"/*.md; do
    if [ -f "$cmd_file" ]; then
        cmd_name=$(basename "$cmd_file")
        target_cmd="$TARGET_CLAUDE/commands/$cmd_name"

        if [ "$UPDATE_MODE" = true ]; then
            # Update mode: always overwrite commands
            cp "$cmd_file" "$TARGET_CLAUDE/commands/"
            echo -e "   ${CYAN}🔄 $cmd_name${NC}"
        elif [ -f "$target_cmd" ] && [ "$MERGE_MODE" = true ]; then
            echo -e "   ${YELLOW}⚠️  Skipping $cmd_name (already exists)${NC}"
        else
            cp "$cmd_file" "$TARGET_CLAUDE/commands/"
            echo -e "   ${GREEN}✅ $cmd_name${NC}"
        fi
    fi
done

# Copy hooks
echo -e "${GREEN}📁 Installing RALPH hooks...${NC}"
if [ -d "$SOURCE_CLAUDE/hooks" ]; then
    for hook_file in "$SOURCE_CLAUDE/hooks"/*; do
        if [ -f "$hook_file" ]; then
            hook_name=$(basename "$hook_file")
            target_hook="$TARGET_CLAUDE/hooks/$hook_name"

            if [ "$UPDATE_MODE" = true ]; then
                # Update mode: always overwrite hooks
                cp "$hook_file" "$TARGET_CLAUDE/hooks/"
                chmod +x "$TARGET_CLAUDE/hooks/$hook_name"
                echo -e "   ${CYAN}🔄 $hook_name${NC}"
            elif [ -f "$target_hook" ] && [ "$MERGE_MODE" = true ]; then
                echo -e "   ${YELLOW}⚠️  Skipping $hook_name (already exists)${NC}"
            else
                cp "$hook_file" "$TARGET_CLAUDE/hooks/"
                chmod +x "$TARGET_CLAUDE/hooks/$hook_name"
                echo -e "   ${GREEN}✅ $hook_name${NC}"
            fi
        fi
    done
fi

# Copy examples
echo -e "${GREEN}📁 Installing examples (3 projects)...${NC}"
mkdir -p "$TARGET_CLAUDE/examples"
if [ -d "$SOURCE_CLAUDE/examples" ]; then
    for example_dir in "$SOURCE_CLAUDE/examples"/*; do
        if [ -d "$example_dir" ]; then
            example_name=$(basename "$example_dir")
            target_example="$TARGET_CLAUDE/examples/$example_name"

            # Skip if source and target are the same location
            SOURCE_REAL="$(cd "$example_dir" && pwd)"
            TARGET_REAL="$TARGET_CLAUDE/examples/$example_name"
            if [ -d "$TARGET_REAL" ]; then
                TARGET_REAL="$(cd "$TARGET_REAL" && pwd)"
            fi

            if [ "$SOURCE_REAL" = "$TARGET_REAL" ]; then
                echo -e "   ${GREEN}✅ $example_name (already in place)${NC}"
                continue
            fi

            if [ "$UPDATE_MODE" = true ]; then
                # Update mode: always overwrite examples
                rm -rf "$target_example"
                cp -R "$example_dir" "$TARGET_CLAUDE/examples/"
                echo -e "   ${CYAN}🔄 $example_name${NC}"
            elif [ -d "$target_example" ] && [ "$MERGE_MODE" = true ]; then
                echo -e "   ${YELLOW}⚠️  Skipping $example_name (already exists)${NC}"
            else
                cp -R "$example_dir" "$TARGET_CLAUDE/examples/"
                echo -e "   ${GREEN}✅ $example_name${NC}"
            fi
        fi
    done
fi

# Copy templates (NEW v3.0+)
echo -e "${GREEN}📁 Installing templates (18 files)...${NC}"
if [ -d "$SOURCE_CLAUDE/templates" ]; then
    # GitHub Actions templates
    if [ -d "$SOURCE_CLAUDE/templates/github-actions" ]; then
        for file in "$SOURCE_CLAUDE/templates/github-actions"/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                if [ "$UPDATE_MODE" = true ]; then
                    cp "$file" "$TARGET_CLAUDE/templates/github-actions/"
                    echo -e "   ${CYAN}🔄 github-actions/$filename${NC}"
                else
                    cp "$file" "$TARGET_CLAUDE/templates/github-actions/"
                    echo -e "   ${GREEN}✅ github-actions/$filename${NC}"
                fi
            fi
        done
    fi

    # GitHub templates (PR, Issues)
    if [ -d "$SOURCE_CLAUDE/templates/github" ]; then
        # Copy PR template
        if [ -f "$SOURCE_CLAUDE/templates/github/PULL_REQUEST_TEMPLATE.md" ]; then
            cp "$SOURCE_CLAUDE/templates/github/PULL_REQUEST_TEMPLATE.md" "$TARGET_CLAUDE/templates/github/"
            if [ "$UPDATE_MODE" = true ]; then
                echo -e "   ${CYAN}🔄 github/PULL_REQUEST_TEMPLATE.md${NC}"
            else
                echo -e "   ${GREEN}✅ github/PULL_REQUEST_TEMPLATE.md${NC}"
            fi
        fi
        # Copy README
        if [ -f "$SOURCE_CLAUDE/templates/github/README.md" ]; then
            cp "$SOURCE_CLAUDE/templates/github/README.md" "$TARGET_CLAUDE/templates/github/"
        fi
        # Copy Issue templates
        if [ -d "$SOURCE_CLAUDE/templates/github/ISSUE_TEMPLATE" ]; then
            for file in "$SOURCE_CLAUDE/templates/github/ISSUE_TEMPLATE"/*; do
                if [ -f "$file" ]; then
                    filename=$(basename "$file")
                    cp "$file" "$TARGET_CLAUDE/templates/github/ISSUE_TEMPLATE/"
                    if [ "$UPDATE_MODE" = true ]; then
                        echo -e "   ${CYAN}🔄 github/ISSUE_TEMPLATE/$filename${NC}"
                    else
                        echo -e "   ${GREEN}✅ github/ISSUE_TEMPLATE/$filename${NC}"
                    fi
                fi
            done
        fi
    fi

    # Git Hooks templates (NEW v3.1)
    if [ -d "$SOURCE_CLAUDE/templates/git-hooks" ]; then
        for file in "$SOURCE_CLAUDE/templates/git-hooks"/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                cp "$file" "$TARGET_CLAUDE/templates/git-hooks/"
                if [ "$UPDATE_MODE" = true ]; then
                    echo -e "   ${CYAN}🔄 git-hooks/$filename${NC}"
                else
                    echo -e "   ${GREEN}✅ git-hooks/$filename${NC}"
                fi
            fi
        done
    fi

    # DevContainer templates (NEW v3.1)
    if [ -d "$SOURCE_CLAUDE/templates/devcontainer" ]; then
        for file in "$SOURCE_CLAUDE/templates/devcontainer"/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                cp "$file" "$TARGET_CLAUDE/templates/devcontainer/"
                if [ "$UPDATE_MODE" = true ]; then
                    echo -e "   ${CYAN}🔄 devcontainer/$filename${NC}"
                else
                    echo -e "   ${GREEN}✅ devcontainer/$filename${NC}"
                fi
            fi
        done
    fi
fi

# Create multi-agent compatibility layer (NEW v3.7)
AGENT_DIRS=""
project_provider_enabled agents && AGENT_DIRS="$AGENT_DIRS .agents"
project_provider_enabled codex && AGENT_DIRS="$AGENT_DIRS .codex"
project_provider_enabled gemini && AGENT_DIRS="$AGENT_DIRS .gemini"
project_provider_enabled opencode && AGENT_DIRS="$AGENT_DIRS .opencode"

if [ -n "$AGENT_DIRS" ]; then
    echo -e "${GREEN}📁 Installing provider compatibility ($AGENT_DIRS )...${NC}"
else
    echo -e "${YELLOW}⏭️  Provider compatibility skipped (--providers claude)${NC}"
fi

for agent_dir in $AGENT_DIRS; do
    SOURCE_AGENT="$SOURCE_CLAUDE/../$agent_dir"
    TARGET_AGENT="$TARGET_DIR/$agent_dir"

    if [ -d "$SOURCE_AGENT" ]; then
        mkdir -p "$TARGET_AGENT"

        # Copy instruction files (AGENTS.md, GEMINI.md, README.md)
        for file in "$SOURCE_AGENT"/*.md; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                cp "$file" "$TARGET_AGENT/"
            fi
        done

        # Copy native provider command/prompt folders when present.
        for subdir in prompts commands; do
            if [ -d "$SOURCE_AGENT/$subdir" ]; then
                if [ "$UPDATE_MODE" = true ]; then
                    rm -rf "$TARGET_AGENT/$subdir"
                fi
                mkdir -p "$TARGET_AGENT/$subdir"
                cp -R "$SOURCE_AGENT/$subdir/." "$TARGET_AGENT/$subdir/" 2>/dev/null || true
            fi
        done

        # Create symlinks to .claude/skills and .claude/knowledge
        if [ -L "$TARGET_AGENT/skills" ] || [ ! -e "$TARGET_AGENT/skills" ]; then
            ln -sfn ../.claude/skills "$TARGET_AGENT/skills"
        else
            echo -e "   ${YELLOW}⚠️  $agent_dir/skills exists as a real file/dir — symlink skipped${NC}"
        fi
        if [ -L "$TARGET_AGENT/knowledge" ] || [ ! -e "$TARGET_AGENT/knowledge" ]; then
            ln -sfn ../.claude/knowledge "$TARGET_AGENT/knowledge"
        else
            echo -e "   ${YELLOW}⚠️  $agent_dir/knowledge exists as a real file/dir — symlink skipped${NC}"
        fi

        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${CYAN}🔄 $agent_dir/${NC}"
        else
            echo -e "   ${GREEN}✅ $agent_dir/${NC}"
        fi
    fi
done

# Copy mcp.json (PRESERVE in update mode)
echo -e "${GREEN}📄 Installing mcp.json...${NC}"
if [ -f "$SOURCE_CLAUDE/mcp.json" ]; then
    if [ -f "$TARGET_CLAUDE/mcp.json" ]; then
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${GREEN}✅ mcp.json (preserved - your config)${NC}"
        else
            echo -e "   ${YELLOW}⚠️  mcp.json exists - creating mcp.d-epct.json${NC}"
            cp "$SOURCE_CLAUDE/mcp.json" "$TARGET_CLAUDE/mcp.d-epct.json"
            echo -e "   ${YELLOW}📝 NOTE: Merge mcp.d-epct.json into your existing mcp.json${NC}"
        fi
    else
        cp "$SOURCE_CLAUDE/mcp.json" "$TARGET_CLAUDE/"
        echo -e "   ${GREEN}✅ mcp.json${NC}"
    fi
fi

# Copy settings.json (PRESERVE in update mode)
echo -e "${GREEN}📄 Installing settings.json...${NC}"
if [ -f "$SOURCE_CLAUDE/settings.json" ]; then
    if [ -f "$TARGET_CLAUDE/settings.json" ]; then
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${GREEN}✅ settings.json (preserved - your config)${NC}"
        else
            echo -e "   ${YELLOW}⚠️  settings.json exists - creating settings.ralph.json${NC}"
            cp "$SOURCE_CLAUDE/settings.json" "$TARGET_CLAUDE/settings.ralph.json"
            echo -e "   ${YELLOW}📝 NOTE: Merge settings.ralph.json into your existing settings.json${NC}"
        fi
    else
        cp "$SOURCE_CLAUDE/settings.json" "$TARGET_CLAUDE/"
        echo -e "   ${GREEN}✅ settings.json${NC}"
    fi
fi

# Handle CLAUDE.md (MERGE in update mode - preserve user's PROJECT-RULES section)
echo -e "${GREEN}📄 Installing CLAUDE.md...${NC}"
if [ -f "$TARGET_CLAUDE/CLAUDE.md" ]; then
    if [ "$UPDATE_MODE" = true ]; then
        # Extract user's PROJECT-RULES section if it exists
        USER_RULES=""
        if grep -q "PROJECT-RULES-START" "$TARGET_CLAUDE/CLAUDE.md" 2>/dev/null; then
            USER_RULES=$(sed -n '/<!-- PROJECT-RULES-START -->/,/<!-- PROJECT-RULES-END -->/p' "$TARGET_CLAUDE/CLAUDE.md")
        fi

        # Copy new CLAUDE.md
        cp "$SOURCE_CLAUDE/CLAUDE.md" "$TARGET_CLAUDE/"

        # Restore user's PROJECT-RULES section if they had customizations
        if [ -n "$USER_RULES" ]; then
            # Check if user actually customized (not just the default template)
            if echo "$USER_RULES" | grep -qv "Exemple de règles à ajouter"; then
                # Replace the default PROJECT-RULES section with user's version
                # Create a temp file with user's rules
                TEMP_FILE=$(mktemp)
                echo "$USER_RULES" > "$TEMP_FILE"

                # Use awk to replace the section
                awk '
                    /<!-- PROJECT-RULES-START -->/ {
                        skip=1
                        while ((getline line < "'"$TEMP_FILE"'") > 0) print line
                        next
                    }
                    /<!-- PROJECT-RULES-END -->/ { skip=0; next }
                    !skip { print }
                ' "$TARGET_CLAUDE/CLAUDE.md" > "$TARGET_CLAUDE/CLAUDE.md.tmp"
                mv "$TARGET_CLAUDE/CLAUDE.md.tmp" "$TARGET_CLAUDE/CLAUDE.md"
                rm -f "$TEMP_FILE"

                echo -e "   ${CYAN}🔄 CLAUDE.md (workflow updated, your rules preserved)${NC}"
            else
                echo -e "   ${CYAN}🔄 CLAUDE.md (updated)${NC}"
            fi
        else
            echo -e "   ${CYAN}🔄 CLAUDE.md (updated)${NC}"
        fi
    else
        echo -e "   ${YELLOW}⚠️  CLAUDE.md exists - creating CLAUDE.d-epct.md instead${NC}"
        cp "$SOURCE_CLAUDE/CLAUDE.md" "$TARGET_CLAUDE/CLAUDE.d-epct.md"
        echo ""
        echo -e "${YELLOW}📝 NOTE: Merge the content of CLAUDE.d-epct.md into your existing CLAUDE.md${NC}"
    fi
else
    cp "$SOURCE_CLAUDE/CLAUDE.md" "$TARGET_CLAUDE/"
    echo -e "   ${GREEN}✅ CLAUDE.md${NC}"
fi

# Copy CHANGELOG.md to project root
if [ -f "$SOURCE_CLAUDE/../CHANGELOG.md" ]; then
    if [ "$UPDATE_MODE" = true ] || [ ! -f "$TARGET_DIR/CHANGELOG.md" ]; then
        cp "$SOURCE_CLAUDE/../CHANGELOG.md" "$TARGET_DIR/"
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "   ${CYAN}🔄 CHANGELOG.md${NC}"
        else
            echo -e "   ${GREEN}✅ CHANGELOG.md${NC}"
        fi
    fi
fi

# Create .gitkeep files to preserve empty directories
touch "$TARGET_DOCS/planning/brainstorms/.gitkeep"
touch "$TARGET_DOCS/planning/ux/.gitkeep"
touch "$TARGET_DOCS/planning/prd/.gitkeep"
touch "$TARGET_DOCS/planning/ui/.gitkeep"
touch "$TARGET_DOCS/planning/architecture/.gitkeep"
touch "$TARGET_DOCS/stories/.gitkeep"
touch "$TARGET_DOCS/ralph-logs/.gitkeep"
touch "$TARGET_DOCS/debates/.gitkeep"
touch "$TARGET_DOCS/security/.gitkeep"

echo ""
if [ "$UPDATE_MODE" = true ]; then
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗"
echo -e "║                       ✅ Update Complete!                            ║"
echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Updated components:${NC}"
echo -e "   ${CYAN}🔄 Skills (33)${NC}"
echo -e "   ${CYAN}🔄 Commands (21)${NC}"
echo -e "   ${CYAN}🔄 Hooks${NC}"
echo -e "   ${CYAN}🔄 Knowledge Base (54 files)${NC}"
echo -e "   ${CYAN}🔄 Templates (18 files)${NC}"
echo -e "   ${CYAN}🔄 Examples (3 projects)${NC}"
echo -e "   ${CYAN}🔄 Multi-agent compatibility (4 layers)${NC}"
echo ""
echo -e "${GREEN}Preserved (your customizations):${NC}"
echo -e "   ${GREEN}✅ CLAUDE.md PROJECT-RULES section${NC}"
echo -e "   ${GREEN}✅ settings.json${NC}"
echo -e "   ${GREEN}✅ mcp.json${NC}"
else
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗"
echo -e "║                     ✅ Installation Complete!                         ║"
echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Installed components:${NC}"
echo ""
echo -e "${BLUE}  📚 Knowledge Base (54 files):${NC}"
echo "    testing/           32 files (test levels, priorities, factories, fixtures...)"
echo "    workflows/         10 files (PRD, architecture, stories, UX, UI templates...)"
echo "    brainstorming/      1 file  (61 techniques en 10 catégories)"
echo "    multi-mind/         2 files (agent personalities, debate templates)"
echo "    supabase-security/  7 files (RLS patterns, remediation, auth config...)"
echo "    figma/              3 files (Code Connect, MCP tools, tokens mapping) [legacy]"
echo ""
echo -e "${BLUE}  📂 Templates (18 files):${NC}"
echo "    github-actions/  CI/CD workflows (ci, release, security, deploy)"
echo "    github/          PR template, Issue templates"
echo "    git-hooks/       pre-commit, commit-msg (Conventional Commits)"
echo "    devcontainer/    Docker dev environment (Node.js, PostgreSQL, Redis)"
echo ""
echo -e "${BLUE}  📂 Examples (3 projects):${NC}"
echo "    simple-api/      API REST simple (mode LIGHT)"
echo "    blog-nextjs/     Blog Next.js (mode FULL)"
echo "    saas-dashboard/  Dashboard SaaS (mode RALPH)"
echo ""
echo -e "${BLUE}  🤖 Provider Compatibility:${NC}"
echo "    Requested:        $PROJECT_PROVIDERS"
echo "    .agents/         Generic fallback (AGENTS.md)"
echo "    .codex/          OpenAI Codex CLI"
echo "    .gemini/         Google Gemini CLI"
echo "    .opencode/       OpenCode"
echo "    → Selected provider dirs symlink to .claude/skills and .claude/knowledge"
echo ""
echo -e "${BLUE}  Skills (33):${NC}"
echo "    Planning:  idea-brainstorm, pm-prd, architect, pm-stories,"
echo "               api-designer, database-designer"
echo "    Design:    ux-designer, ui-designer (auto-triggered)"
echo "    Figma:     figma-use, figma-code-connect, figma-generate-design,"
echo "               figma-generate-library, figma-implement-design,"
echo "               figma-create-design-system-rules, figma-create-new-file,"
echo "               figma-design-code-sync"
echo "    Dev:       github-issue-reader, code-implementer,"
echo "               test-runner, code-reviewer"
echo "    Audio/Video: elevenlabs (TTS, music, SFX), remotion (React video)"
echo "    Audit:     security-auditor, performance-auditor, supabase-security"
echo "    Multi-IA:  multi-mind (6 IA debate system)"
echo ""
echo -e "${BLUE}  Commands - Mode Manuel:${NC}"
echo "    /discovery           Planning avec validation"
echo "    /dev #123            Dev avec validation"
echo "    /ship                Ship: merge → tests → review → PR"
echo ""
echo -e "${MAGENTA}  Commands - Mode RALPH (autonome):${NC}"
echo "    /auto-loop \"prompt\"  Boucle générique"
echo "    /auto-discovery      Planning autonome"
echo "    /auto-dev #123       Dev autonome"
echo "    /cancel-ralph        Arrêter la boucle"
echo "    /resume-ralph        Reprendre session"
echo ""
echo -e "${BLUE}  Commands - Ship & QA:${NC}"
echo "    /ship                Ship workflow automatisé"
echo "    /qa                  QA testing + health score"
echo "    /plan-review         Review CEO/Founder"
echo "    /retro               Rétrospective engineering"
echo ""
echo -e "${BLUE}  Commands - Utilitaires:${NC}"
echo "    /status              État du projet"
echo "    /pr-review #123      Review PR (3 passes)"
echo "    /quick-fix           Fix rapide"
echo "    /refactor            Refactoring ciblé"
echo "    /docs                Génère documentation"
echo "    /changelog           Génère CHANGELOG"
echo "    /metrics             Dashboard métriques"
echo "    /init                Scaffolding projet"
echo "    /supabase-security   Audit sécurité Supabase"
fi
echo ""
echo -e "${CYAN}Usage:${NC}"
echo ""
echo "  cd $TARGET_DIR"
echo "  claude"
echo ""
echo -e "  ${BLUE}# Mode Manuel (validation humaine)${NC}"
echo "  /discovery"
echo "  /dev #123"
echo ""
echo -e "  ${MAGENTA}# Mode RALPH (autonome)${NC}"
echo "  /auto-discovery \"Je veux créer une app de todo\""
echo "  /auto-dev #123 --max 50"
echo ""
if [ "$UPDATE_MODE" != true ]; then
echo -e "${CYAN}Workflow:${NC}"
echo ""
echo "  Planning:  🧠 Brainstorm → 📋 PRD → 🏗️ Architecture → 📝 Stories (orchestrateur garde le contexte)"
echo "  Dev:       🔍 Explore → 📝 Plan (orchestrateur) → 💻 Code+Tests (subagents //) → 🔄 Review ×3 (subagents //) → 🚀 Ship"
echo ""
echo -e "${CYAN}Documentation:${NC}"
echo ""
echo "  Les skills chargent automatiquement le knowledge pertinent."
echo "  Voir .claude/knowledge/tea-index.csv pour l'index complet."
echo "  Voir .claude/examples/ pour des projets exemples complets."
echo ""
fi
echo -e "${CYAN}Update:${NC}"
echo ""
echo "  # Pour mettre à jour vers la dernière version:"
echo "  curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- update . --providers $PROJECT_PROVIDERS"
echo ""
