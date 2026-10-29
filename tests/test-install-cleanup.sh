#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="$REPO_ROOT/install.sh"
# Last commit that still shipped the skills retired by the v6.1 cleanup.
RETIRED_SOURCE_REF="0de1a6718e71b32e4c4e007c491129b276747a30"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/skillz-cleanup-tests.XXXXXX")"

cleanup() {
    rm -rf "$TEST_ROOT"
}
trap cleanup EXIT

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

assert_absent() {
    [ ! -e "$1" ] && [ ! -L "$1" ] || fail "Expected path to be absent: $1"
}

assert_present() {
    [ -e "$1" ] || [ -L "$1" ] || fail "Expected path to be present: $1"
}

run_installer() {
    local home="$1"
    shift
    HOME="$home" bash "$INSTALLER" "$@" --no-wiki >"$home/install.log" 2>&1 || {
        tail -20 "$home/install.log" >&2
        fail "Installer failed: $*"
    }
}

shipped() {
    git -C "$REPO_ROOT" show "$RETIRED_SOURCE_REF:.claude/$1"
}

git -C "$REPO_ROOT" cat-file -e "$RETIRED_SOURCE_REF^{commit}" 2>/dev/null || \
    fail "Commit $RETIRED_SOURCE_REF is missing: run the suite from a full (non-shallow) clone"

new_home() {
    local home="$TEST_ROOT/$1"
    mkdir -p "$home/.codex" "$home/.local/bin"
    printf '%s\n' "$home"
}

test_global_update_cleans_every_mirror_and_retired_knowledge() {
    local home mirror
    home="$(new_home global)"
    run_installer "$home" install all

    printf 'skill:ghost-skill\n' >>"$home/.claude/.skillz-manifest"
    mkdir -p "$home/.claude/skills/ghost-skill"
    printf -- '---\nname: ghost-skill\n---\n' >"$home/.claude/skills/ghost-skill/SKILL.md"
    for mirror in .codex/skills .gemini/skills .config/opencode/skills .agents/skills; do
        ln -sfn "$home/.claude/skills/ghost-skill/" "$home/$mirror/ghost-skill"
        ln -sfn "$home/elsewhere/missing" "$home/$mirror/foreign-dead-link"
        ln -sfn "$home/.claude/skills-other/x" "$home/$mirror/sibling-prefix-link"
    done
    mkdir -p "$home/.claude/skills/multi-mind"
    printf 'my own version\n' >"$home/.claude/skills/multi-mind/SKILL.md"
    printf 'skill:multi-mind\n' >>"$home/.claude/.skillz-manifest"
    # "figma" is a strict prefix of the retired "figma-use": its checksum rule must not apply.
    mkdir -p "$home/.claude/skills/figma"
    printf 'old shipped figma\n' >"$home/.claude/skills/figma/SKILL.md"
    printf 'skill:figma\n' >>"$home/.claude/.skillz-manifest"
    mkdir -p "$home/.claude/knowledge/multi-mind"
    shipped knowledge/multi-mind/agent-personalities.md \
        >"$home/.claude/knowledge/multi-mind/agent-personalities.md"
    printf 'user notes\n' >"$home/.claude/knowledge/multi-mind/debate-templates.md"

    run_installer "$home" update all

    assert_absent "$home/.claude/skills/ghost-skill"
    for mirror in .codex/skills .gemini/skills .config/opencode/skills .agents/skills; do
        assert_absent "$home/$mirror/ghost-skill"
        assert_present "$home/$mirror/foreign-dead-link"
        assert_present "$home/$mirror/sibling-prefix-link"
    done
    assert_present "$home/.claude/skills/multi-mind/SKILL.md"
    assert_absent "$home/.claude/skills/figma"
    assert_absent "$home/.claude/knowledge/multi-mind/agent-personalities.md"
    assert_present "$home/.claude/knowledge/multi-mind/debate-templates.md"
}

test_project_update_purges_from_its_manifest() {
    local home project
    home="$(new_home project)"
    project="$TEST_ROOT/project-app"
    mkdir -p "$project"
    run_installer "$home" install "$project" --providers codex

    [ -f "$project/.claude/.skillz-manifest" ] || fail "Project install wrote no manifest"
    grep -qx 'skill:dev-workflow' "$project/.claude/.skillz-manifest" || \
        fail "Project manifest does not list installed skills"

    printf 'skill:ghost-skill\ncommand:ghost.md\nskill:../../outside\nskill:..\nskill:\ncommand:../escape.md\n' \
        >>"$project/.claude/.skillz-manifest"
    mkdir -p "$project/outside"
    printf 'keep\n' >"$project/escape.md"
    mkdir -p "$project/.claude/skills/ghost-skill" "$project/.claude/skills/user-skill"
    printf 'ghost\n' >"$project/.claude/commands/ghost.md"
    ln -sfn ../../.claude/skills/ghost-skill "$project/.codex/skills/ghost-skill"

    run_installer "$home" update "$project" --providers codex

    assert_absent "$project/.claude/skills/ghost-skill"
    assert_absent "$project/.claude/commands/ghost.md"
    assert_absent "$project/.codex/skills/ghost-skill"
    assert_present "$project/.claude/skills/user-skill"
    assert_present "$project/outside"
    assert_present "$project/escape.md"
    assert_present "$project/.claude/skills"
    if grep -qx 'skill:ghost-skill' "$project/.claude/.skillz-manifest"; then
        fail "Purged skill is still listed in the project manifest"
    fi
}

assert_global_sentinel_survives() {
    local home="$1"
    assert_present "$home/.claude/skills/sentinel/SKILL.md"
    grep -qx 'skill:sentinel' "$home/.claude/.skillz-manifest" || \
        fail "A project-mode run rewrote the global manifest"
}

test_global_claude_is_never_treated_as_a_project() {
    local home linked
    home="$(new_home home-target)"
    run_installer "$home" install all
    mkdir -p "$home/.claude/skills/sentinel"
    printf 'mine\n' >"$home/.claude/skills/sentinel/SKILL.md"
    printf 'skill:sentinel\n' >>"$home/.claude/.skillz-manifest"
    run_installer "$home" update "$home" --providers claude
    assert_global_sentinel_survives "$home"

    linked="$(new_home home-linked)"
    mkdir -p "$linked/dotfiles/.claude"
    ln -s "$linked/dotfiles/.claude" "$linked/.claude"
    run_installer "$linked" install all
    mkdir -p "$linked/.claude/skills/sentinel"
    printf 'mine\n' >"$linked/.claude/skills/sentinel/SKILL.md"
    printf 'skill:sentinel\n' >>"$linked/.claude/.skillz-manifest"
    run_installer "$linked" update "$linked/dotfiles" --providers claude
    assert_global_sentinel_survives "$linked"
}

test_project_purge_never_follows_a_linked_skills_folder() {
    local home project outside
    home="$(new_home linked)"
    project="$TEST_ROOT/linked-app"
    outside="$TEST_ROOT/linked-outside"
    mkdir -p "$project/.claude/commands" "$outside/precious"
    printf 'keep\n' >"$outside/precious/data.txt"
    ln -s "$outside" "$project/.claude/skills"
    printf 'skill:precious\n' >"$project/.claude/.skillz-manifest"

    run_installer "$home" update "$project" --providers claude

    assert_present "$outside/precious/data.txt"
    grep -q 'Purge skipped' "$home/install.log" || fail "Linked skills folder was not reported"
}

test_project_without_manifest_retires_only_unmodified_items() {
    local home project
    home="$(new_home legacy)"
    project="$TEST_ROOT/legacy-app"
    mkdir -p "$project"
    run_installer "$home" install "$project" --providers claude,codex
    rm -f "$project/.claude/.skillz-manifest"

    mkdir -p "$project/.claude/skills/multi-mind" "$project/.claude/skills/figma-use"
    shipped skills/multi-mind/SKILL.md >"$project/.claude/skills/multi-mind/SKILL.md"
    printf 'extra\n' >"$project/.claude/skills/multi-mind/notes.md"
    printf -- '---\nname: figma-use\n---\nuser copy\n' >"$project/.claude/skills/figma-use/SKILL.md"
    shipped commands/init.md >"$project/.claude/commands/init.md"
    printf 'my docs command\n' >"$project/.claude/commands/docs.md"

    run_installer "$home" update "$project" --providers claude,codex

    assert_absent "$project/.claude/skills/multi-mind"
    assert_absent "$project/.codex/skills/multi-mind"
    assert_absent "$project/.claude/commands/init.md"
    assert_present "$project/.claude/skills/figma-use/SKILL.md"
    assert_present "$project/.claude/commands/docs.md"
    grep -q 'Preserved modified target: skills/figma-use/SKILL.md' "$home/install.log" || \
        fail "Preserved retired skill was not reported"
    [ -f "$project/.claude/.skillz-manifest" ] || fail "Legacy project update wrote no manifest"
    if grep -q '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}' "$project/.claude/.skillz-manifest"; then
        fail "Project manifest carries a timestamp"
    fi
}

test_global_update_cleans_every_mirror_and_retired_knowledge
test_project_update_purges_from_its_manifest
test_global_claude_is_never_treated_as_a_project
test_project_purge_never_follows_a_linked_skills_folder
test_project_without_manifest_retires_only_unmodified_items
echo "PASS: installer cleanup suite"
