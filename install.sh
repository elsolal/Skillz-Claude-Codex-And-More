#!/bin/bash

# ============================================================
# D-EPCT+R Workflow v5.1 Installer
# Install Claude Code skills + RALPH Mode + 54 Knowledge Files + Templates
# 21 skills, 20 commands, 18 templates, 4 agent compatibility layers
#
# Usage:
#   # Fresh install in a project
#   curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- .
#   ./install.sh /path/to/project
#
#   # Update existing project installation (preserves CLAUDE.md, settings.json, mcp.json)
#   curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- . --update
#   ./install.sh /path/to/project --update
#
#   # Global install into ~/.claude/ (available in ALL projects)
#   curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- --global
#   ./install.sh --global
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

# Parse arguments
UPDATE_MODE=false
GLOBAL_MODE=false
TARGET_DIR=""

for arg in "$@"; do
    case $arg in
        --update)
            UPDATE_MODE=true
            ;;
        --global)
            GLOBAL_MODE=true
            UPDATE_MODE=true
            ;;
        *)
            if [ -z "$TARGET_DIR" ]; then
                TARGET_DIR="$arg"
            fi
            ;;
    esac
done

# Global mode: install into ~/.claude/ (user-level, all projects)
if [ "$GLOBAL_MODE" = true ]; then
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║             D-EPCT+R Workflow v5.1 — Global Install                 ║"
    echo "║                                                                       ║"
    echo "║   Target: ~/.claude/ (available in ALL your projects)                 ║"
    echo "║   Preserves: CLAUDE.md, settings.json, mcp.json                      ║"
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

    # rsync contents, preserving user config files
    echo -e "${CYAN}🔄 Syncing to ~/.claude/...${NC}"
    rsync -a \
        --exclude='CLAUDE.md' \
        --exclude='settings.json' \
        --exclude='mcp.json' \
        "$SOURCE_DIR/" ~/.claude/

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
    echo ""
    echo -e "${GREEN}Preserved (your config):${NC}"
    echo -e "   ${GREEN}✅ ~/.claude/CLAUDE.md${NC}"
    echo -e "   ${GREEN}✅ ~/.claude/settings.json${NC}"
    echo -e "   ${GREEN}✅ ~/.claude/mcp.json${NC}"
    echo ""
    echo -e "${CYAN}These skills & commands are now available in ALL your projects.${NC}"
    echo -e "${CYAN}To update later: run the same command again.${NC}"
    echo ""
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
echo "║   SKILLS:       21 (Planning, Design, Dev, Security, Figma)            ║"
echo "║   COMMANDS:     20 (Manuel + RALPH + Ship/QA/Retro)                   ║"
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
echo -e "${GREEN}📁 Installing skills (21)...${NC}"
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
echo -e "${GREEN}📁 Installing commands (20)...${NC}"
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
echo -e "${GREEN}📁 Installing multi-agent compatibility (.agents, .codex, .gemini, .opencode)...${NC}"
for agent_dir in .agents .codex .gemini .opencode; do
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

        # Create symlinks to .claude/skills and .claude/knowledge
        if [ ! -L "$TARGET_AGENT/skills" ]; then
            ln -sf ../.claude/skills "$TARGET_AGENT/skills"
        fi
        if [ ! -L "$TARGET_AGENT/knowledge" ]; then
            ln -sf ../.claude/knowledge "$TARGET_AGENT/knowledge"
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
echo -e "   ${CYAN}🔄 Skills (21)${NC}"
echo -e "   ${CYAN}🔄 Commands (20)${NC}"
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
echo "    figma/              3 files (Code Connect, MCP tools, tokens mapping)"
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
echo -e "${BLUE}  🤖 Multi-Agent Compatibility:${NC}"
echo "    .agents/         Generic fallback (AGENTS.md)"
echo "    .codex/          OpenAI Codex CLI"
echo "    .gemini/         Google Gemini CLI"
echo "    .opencode/       OpenCode"
echo "    → All symlinked to .claude/skills and .claude/knowledge"
echo ""
echo -e "${BLUE}  Skills (21):${NC}"
echo "    Planning:  idea-brainstorm, pm-prd, architect, pm-stories,"
echo "               api-designer, database-designer"
echo "    Design:    ux-designer, ui-designer (auto-triggered)"
echo "    Figma:     figma-setup, figma-to-code, figma-designer,"
echo "               figma-design-system, figma-design-code-sync"
echo "    Dev:       github-issue-reader, code-implementer,"
echo "               test-runner, code-reviewer"
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
echo "  curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- . --update"
echo ""
