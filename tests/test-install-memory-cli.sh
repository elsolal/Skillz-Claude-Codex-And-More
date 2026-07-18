#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="$REPO_ROOT/install.sh"
BASE_PATH="$PATH"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/skillz-memory-tests.XXXXXX")"

cleanup() {
    rm -rf "$TEST_ROOT"
}
trap cleanup EXIT

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

assert_contains() {
    local file="$1"
    local expected="$2"
    grep -Fq "$expected" "$file" || fail "Expected '$expected' in $file"
}

assert_managed_link() {
    local link="$1"
    local expected_target="$2"
    [ -L "$link" ] || fail "Expected managed symlink: $link"
    [ "$(readlink "$link")" = "$expected_target" ] || \
        fail "Unexpected target for $link: $(readlink "$link")"
}

assert_absent() {
    local path="$1"
    [ ! -e "$path" ] && [ ! -L "$path" ] || fail "Expected path to be absent: $path"
}

new_home() {
    local name="$1"
    local home="$TEST_ROOT/$name"
    mkdir -p "$home/.codex" "$home/.local/bin"
    printf '%s\n' "$home"
}

run_installer() {
    local home="$1"
    local path_value="$2"
    local log="$3"
    shift 3
    HOME="$home" PATH="$path_value" bash "$INSTALLER" "$@" --no-wiki >"$log" 2>&1
}

run_installer_expect_failure() {
    local home="$1"
    local path_value="$2"
    local log="$3"
    shift 3
    if HOME="$home" PATH="$path_value" bash "$INSTALLER" "$@" --no-wiki >"$log" 2>&1; then
        fail "Installer unexpectedly succeeded: $*"
    fi
}

write_third_party_binary() {
    local path="$1"
    printf '#!/usr/bin/env bash\necho third-party-memory\n' >"$path"
    chmod +x "$path"
}

test_install_update_and_uninstall() {
    local home log expected_target skillz_output alias_output deny_bin command test_path
    home="$(new_home happy-path)"
    log="$home/install.log"
    expected_target="$home/.claude/skills/llm-wiki/bin/memory"
    deny_bin="$home/deny-downloads"
    mkdir -p "$deny_bin"
    for command in qmd npm bun curl; do
        printf '#!/usr/bin/env bash\necho "%s invoked" >>"$HOME/unexpected-download-command"\nexit 97\n' "$command" \
            >"$deny_bin/$command"
        chmod +x "$deny_bin/$command"
    done
    test_path="$home/.local/bin:$deny_bin:$BASE_PATH"

    run_installer "$home" "$test_path" "$log" install all

    assert_managed_link "$home/.local/bin/skillz-memory" "$expected_target"
    assert_managed_link "$home/.local/bin/memory" "$expected_target"
    [ -L "$home/.codex/skills/llm-wiki" ] || fail "Codex provider mirror was not installed"
    [ -L "$home/.gemini/skills/llm-wiki" ] || fail "Gemini provider mirror was not installed"
    [ -L "$home/.config/opencode/skills/llm-wiki" ] || fail "OpenCode provider mirror was not installed"
    [ -L "$home/.agents/skills/llm-wiki" ] || fail "Generic agents provider mirror was not installed"
    assert_absent "$home/unexpected-download-command"
    skillz_output="$(HOME="$home" PATH="$test_path" skillz-memory --version)"
    alias_output="$(HOME="$home" PATH="$test_path" memory --version)"
    [ -n "$skillz_output" ] || fail "skillz-memory --version returned no output"
    [ "$skillz_output" = "$alias_output" ] || fail "CLI aliases returned different versions"

    run_installer "$home" "$test_path" "$log" update all
    run_installer "$home" "$test_path" "$log" update all
    assert_managed_link "$home/.local/bin/skillz-memory" "$expected_target"
    assert_managed_link "$home/.local/bin/memory" "$expected_target"
    [ "$(grep -c '^binary:skillz-memory$' "$home/.claude/.skillz-manifest")" -eq 1 ] || \
        fail "skillz-memory manifest entry is not idempotent"
    [ "$(grep -c '^binary:memory$' "$home/.claude/.skillz-manifest")" -eq 1 ] || \
        fail "memory manifest entry is not idempotent"

    run_installer "$home" "$test_path" "$log" uninstall all
    assert_absent "$home/.local/bin/skillz-memory"
    assert_absent "$home/.local/bin/memory"
}

test_memory_collision_is_preserved() {
    local home log third_party before after expected_target
    home="$(new_home memory-collision)"
    log="$home/install.log"
    third_party="$home/.local/bin/memory"
    expected_target="$home/.claude/skills/llm-wiki/bin/memory"
    write_third_party_binary "$third_party"
    before="$(cksum "$third_party")"

    run_installer "$home" "$home/.local/bin:$BASE_PATH" "$log" install all

    after="$(cksum "$third_party")"
    [ "$before" = "$after" ] || fail "Third-party memory binary was modified"
    [ ! -L "$third_party" ] || fail "Third-party memory binary became a symlink"
    assert_managed_link "$home/.local/bin/skillz-memory" "$expected_target"
    assert_contains "$log" "skillz-memory"
    ! grep -q '^binary:memory$' "$home/.claude/.skillz-manifest" || \
        fail "Unmanaged memory binary was recorded as managed"

    run_installer "$home" "$home/.local/bin:$BASE_PATH" "$log" uninstall all
    [ -x "$third_party" ] || fail "Third-party memory binary was removed by uninstall"
    [ "$($third_party)" = "third-party-memory" ] || fail "Third-party memory binary changed after uninstall"
}

test_replaced_alias_is_not_reclaimed() {
    local home log alias before expected_target
    home="$(new_home replaced-alias)"
    log="$home/install.log"
    alias="$home/.local/bin/memory"
    expected_target="$home/.claude/skills/llm-wiki/bin/memory"

    run_installer "$home" "$home/.local/bin:$BASE_PATH" "$log" install claude
    assert_managed_link "$alias" "$expected_target"
    rm -f "$alias"
    write_third_party_binary "$alias"
    before="$(cksum "$alias")"

    run_installer "$home" "$home/.local/bin:$BASE_PATH" "$log" update claude
    [ "$before" = "$(cksum "$alias")" ] || fail "Replaced alias was reclaimed during update"
    [ ! -L "$alias" ] || fail "Replaced alias became managed again"
    assert_contains "$log" "skillz-memory"
    ! grep -q '^binary:memory$' "$home/.claude/.skillz-manifest" || \
        fail "Replaced alias remained recorded as managed"

    run_installer "$home" "$home/.local/bin:$BASE_PATH" "$log" uninstall claude
    [ -x "$alias" ] || fail "Replacement binary was removed by uninstall"
}

test_reserved_name_collision_fails_safely() {
    local home log binary before
    home="$(new_home reserved-collision)"
    log="$home/install.log"
    binary="$home/.local/bin/skillz-memory"
    write_third_party_binary "$binary"
    before="$(cksum "$binary")"

    run_installer_expect_failure "$home" "$home/.local/bin:$BASE_PATH" "$log" install claude
    [ "$before" = "$(cksum "$binary")" ] || fail "Reserved third-party binary was modified"
    assert_contains "$log" "skillz-memory"
}

test_path_diagnostic_keeps_install_usable() {
    local home log expected_target
    home="$(new_home path-diagnostic)"
    log="$home/install.log"
    expected_target="$home/.claude/skills/llm-wiki/bin/memory"

    run_installer "$home" "$BASE_PATH" "$log" install claude
    assert_managed_link "$home/.local/bin/skillz-memory" "$expected_target"
    assert_contains "$log" "PATH"
    HOME="$home" PATH="$BASE_PATH" "$home/.local/bin/skillz-memory" --version >/dev/null
}

test_python_version_is_enforced() {
    local home log fake_bin
    home="$(new_home old-python)"
    log="$home/install.log"
    fake_bin="$home/fake-bin"
    mkdir -p "$fake_bin"
    printf '#!/usr/bin/env bash\necho "Python 3.9.0" >&2\nexit 1\n' >"$fake_bin/python3"
    chmod +x "$fake_bin/python3"

    run_installer_expect_failure "$home" "$fake_bin:$BASE_PATH" "$log" install claude
    assert_contains "$log" "Python 3.10"
    [ ! -e "$home/.local/bin/skillz-memory" ] || fail "CLI installed with unsupported Python"
}

test_install_update_and_uninstall
test_memory_collision_is_preserved
test_replaced_alias_is_not_reclaimed
test_reserved_name_collision_fails_safely
test_path_diagnostic_keeps_install_usable
test_python_version_is_enforced

echo "PASS: memory CLI installer acceptance suite"
