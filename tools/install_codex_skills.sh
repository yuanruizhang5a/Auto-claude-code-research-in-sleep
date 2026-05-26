#!/usr/bin/env bash
# install_codex_skills.sh — install/update ARIS Codex skills into ~/.codex/skills
#
# Examples:
#   bash tools/install_codex_skills.sh
#   bash tools/install_codex_skills.sh --reviewer claude
#   bash tools/install_codex_skills.sh --reviewer gemini --print-mcp-hints
#   bash tools/install_codex_skills.sh --reviewer gemini --no-sync-mcp-files
#   bash tools/install_codex_skills.sh --dry-run
#
# What it does:
#   - installs base skills from skills/skills-codex/
#   - optionally overlays claude/gemini reviewer variants
#   - optionally syncs MCP bridge files to ~/.codex/mcp-servers/
#   - updates managed installs safely when re-run
#
# What it does not do:
#   - does not register MCP servers with codex automatically
#   - does not manage project-local .agents/skills installs
#
# Usage:
#   bash tools/install_codex_skills.sh [options]
#
# Options:
#   --reviewer none|claude|gemini  Select reviewer overlay (default: none)
#   --sync-mcp-files               Sync MCP bridge files for selected overlay
#   --no-sync-mcp-files            Skip MCP bridge file sync
#   --aris-repo PATH               Override ARIS repo discovery
#   --dry-run                      Show plan without writing files
#   --quiet                        Reduce output
#   --print-mcp-hints              Print manual codex mcp add commands
#   -h, --help                     Show this help text

set -euo pipefail

MANIFEST_VERSION="1"
CODEX_HOME_DEFAULT="$HOME/.codex"
ARIS_REPO_OVERRIDE=""
REVIEWER="none"
SYNC_MCP_FILES="auto"
DRY_RUN=false
QUIET=false
PRINT_MCP_HINTS=false

usage() { sed -n '2,31p' "$0" | sed 's/^# \{0,1\}//'; }

log() { $QUIET && return 0; echo "$@"; }
die() { echo "error: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reviewer)
            REVIEWER="${2:?--reviewer requires none|claude|gemini}"
            shift 2
            ;;
        --sync-mcp-files)
            SYNC_MCP_FILES=true
            shift
            ;;
        --no-sync-mcp-files)
            SYNC_MCP_FILES=false
            shift
            ;;
        --aris-repo)
            ARIS_REPO_OVERRIDE="${2:?--aris-repo requires a path}"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        --print-mcp-hints)
            PRINT_MCP_HINTS=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unknown argument: $1"
            ;;
    esac
done

case "$REVIEWER" in
    none|claude|gemini) ;;
    *) die "--reviewer must be one of: none, claude, gemini (got: $REVIEWER)" ;;
esac

if [[ "$SYNC_MCP_FILES" == "auto" ]]; then
    if [[ "$REVIEWER" == "none" ]]; then
        SYNC_MCP_FILES=false
    else
        SYNC_MCP_FILES=true
    fi
fi

abs_path() { ( cd "$1" 2>/dev/null && pwd ) || return 1; }

resolve_aris_repo() {
    local p script_dir parent
    if [[ -n "$ARIS_REPO_OVERRIDE" ]]; then
        p="$(abs_path "$ARIS_REPO_OVERRIDE")" || die "--aris-repo path not found: $ARIS_REPO_OVERRIDE"
        [[ -d "$p/skills/skills-codex" ]] || die "--aris-repo path missing skills/skills-codex: $p"
        echo "$p"
        return
    fi
    script_dir="$(cd "$(dirname "$0")" && pwd)"
    parent="$(cd "$script_dir/.." && pwd)"
    [[ -d "$parent/skills/skills-codex" ]] && { echo "$parent"; return; }
    [[ -n "${ARIS_REPO:-}" && -d "$ARIS_REPO/skills/skills-codex" ]] && { abs_path "$ARIS_REPO"; return; }
    for p in \
        "$HOME/aris_repo" \
        "$HOME/.aris" \
        "$HOME/.codex/Auto-claude-code-research-in-sleep" \
        "$HOME/Desktop/Auto-claude-code-research-in-sleep"; do
        [[ -d "$p/skills/skills-codex" ]] && { abs_path "$p"; return; }
    done
    die "cannot find ARIS repo. Use --aris-repo PATH."
}

assert_managed_path() {
    local path="$1"
    case "$path" in
        "$HOME/.codex"/*) ;;
        *) die "refusing to modify unmanaged path: $path" ;;
    esac
}

replace_path() {
    local src="$1" dest="$2"
    local parent name staging
    assert_managed_path "$dest"
    if $DRY_RUN; then
        log "[dry-run] install $dest"
        return
    fi
    parent="$(dirname "$dest")"
    name="$(basename "$dest")"
    mkdir -p "$parent"
    staging="$(mktemp -d "$parent/.${name}.tmp.XXXXXX")"
    cp -a "$src" "$staging/"
    rm -rf "$dest"
    mv "$staging/$name" "$dest"
    rmdir "$staging" 2>/dev/null || true
    log "installed $dest"
}

list_top_level_entries() {
    local src_dir="$1"
    find "$src_dir" -mindepth 1 -maxdepth 1 -printf '%f\n' | LC_ALL=C sort
}

print_mcp_hints() {
    case "$REVIEWER" in
        claude)
            cat <<EOF
Manual MCP registration hints:
  mkdir -p ~/.codex/mcp-servers/claude-review
  codex mcp add claude-review -- python3 ~/.codex/mcp-servers/claude-review/server.py

If you use the Claude shell wrapper instead:
  chmod +x ~/.codex/mcp-servers/claude-review/run_with_claude_aws.sh
  codex mcp add claude-review -- ~/.codex/mcp-servers/claude-review/run_with_claude_aws.sh
EOF
            ;;
        gemini)
            cat <<EOF
Manual MCP registration hints:
  mkdir -p ~/.codex/mcp-servers/gemini-review
  codex mcp add gemini-review --env GEMINI_REVIEW_BACKEND=api -- python3 ~/.codex/mcp-servers/gemini-review/server.py
EOF
            ;;
    esac
}

ARIS_REPO="$(resolve_aris_repo)"
CODEX_HOME="${CODEX_HOME_DEFAULT}"
SKILLS_DEST="$CODEX_HOME/skills"
MCP_DEST="$CODEX_HOME/mcp-servers"
MANIFEST_DIR="$CODEX_HOME/aris"
MANIFEST_PATH="$MANIFEST_DIR/install-codex-skills.txt"

BASE_SRC="$ARIS_REPO/skills/skills-codex"
[[ -d "$BASE_SRC" ]] || die "missing base skill package: $BASE_SRC"

OVERLAY_SRC=""
MCP_SRC=""
MCP_NAME=""
case "$REVIEWER" in
    claude)
        OVERLAY_SRC="$ARIS_REPO/skills/skills-codex-claude-review"
        MCP_SRC="$ARIS_REPO/mcp-servers/claude-review"
        MCP_NAME="claude-review"
        ;;
    gemini)
        OVERLAY_SRC="$ARIS_REPO/skills/skills-codex-gemini-review"
        MCP_SRC="$ARIS_REPO/mcp-servers/gemini-review"
        MCP_NAME="gemini-review"
        ;;
esac

if [[ -n "$OVERLAY_SRC" && ! -d "$OVERLAY_SRC" ]]; then
    die "missing overlay package: $OVERLAY_SRC"
fi
if [[ "$SYNC_MCP_FILES" == true && -n "$MCP_SRC" && ! -d "$MCP_SRC" ]]; then
    die "missing MCP bridge source: $MCP_SRC"
fi

BASE_ENTRIES="$(list_top_level_entries "$BASE_SRC")"
OVERLAY_ENTRIES=""
if [[ -n "$OVERLAY_SRC" ]]; then
    OVERLAY_ENTRIES="$(list_top_level_entries "$OVERLAY_SRC")"
fi

log ""
log "ARIS Codex Install Plan"
log "  ARIS repo:        $ARIS_REPO"
log "  Codex skills:     $SKILLS_DEST"
log "  Reviewer overlay: $REVIEWER"
log "  Sync MCP files:   $SYNC_MCP_FILES"
if [[ -n "$MCP_NAME" ]]; then
    log "  MCP target:       $MCP_DEST/$MCP_NAME"
fi
if $DRY_RUN; then
    log "  Mode:             DRY-RUN"
else
    log "  Mode:             APPLY"
fi
log ""

while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue
    replace_path "$BASE_SRC/$entry" "$SKILLS_DEST/$entry"
done <<< "$BASE_ENTRIES"

if [[ -n "$OVERLAY_SRC" ]]; then
    while IFS= read -r entry; do
        [[ -z "$entry" ]] && continue
        replace_path "$OVERLAY_SRC/$entry" "$SKILLS_DEST/$entry"
    done <<< "$OVERLAY_ENTRIES"
fi

PREV_MCP_NAME=""
if [[ -f "$MANIFEST_PATH" ]]; then
    PREV_MCP_NAME="$(awk -F'=' '$1=="mcp_name"{print $2; exit}' "$MANIFEST_PATH" 2>/dev/null || true)"
fi

if [[ -n "$PREV_MCP_NAME" && "$PREV_MCP_NAME" != "$MCP_NAME" ]]; then
    assert_managed_path "$MCP_DEST/$PREV_MCP_NAME"
    if $DRY_RUN; then
        log "[dry-run] remove stale MCP dir $MCP_DEST/$PREV_MCP_NAME"
    else
        rm -rf "$MCP_DEST/$PREV_MCP_NAME"
        log "removed stale MCP dir $MCP_DEST/$PREV_MCP_NAME"
    fi
fi

if [[ "$SYNC_MCP_FILES" == true && -n "$MCP_SRC" ]]; then
    replace_path "$MCP_SRC" "$MCP_DEST/$MCP_NAME"
fi

ARIS_COMMIT="$(git -C "$ARIS_REPO" rev-parse HEAD 2>/dev/null || true)"
[[ -n "$ARIS_COMMIT" ]] || ARIS_COMMIT="unknown"
INSTALLED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

if ! $DRY_RUN; then
    mkdir -p "$MANIFEST_DIR"
    {
        echo "version=$MANIFEST_VERSION"
        echo "aris_repo=$ARIS_REPO"
        echo "aris_commit=$ARIS_COMMIT"
        echo "reviewer=$REVIEWER"
        echo "sync_mcp_files=$SYNC_MCP_FILES"
        echo "mcp_name=$MCP_NAME"
        echo "installed_at=$INSTALLED_AT"
        echo "skills_dest=$SKILLS_DEST"
        echo "mcp_dest=$MCP_DEST"
        echo "base_entries=$(echo "$BASE_ENTRIES" | tr '\n' ',' | sed 's/,$//')"
        echo "overlay_entries=$(echo "$OVERLAY_ENTRIES" | tr '\n' ',' | sed 's/,$//')"
    } > "$MANIFEST_PATH"
    log "wrote manifest $MANIFEST_PATH"
else
    log "[dry-run] would write manifest $MANIFEST_PATH"
fi

if $PRINT_MCP_HINTS && [[ "$REVIEWER" != "none" ]]; then
    echo ""
    print_mcp_hints
fi
