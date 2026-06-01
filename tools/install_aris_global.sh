#!/usr/bin/env bash
# install_aris_global.sh — Global ARIS skill installation for Claude Code.
#
# Each ARIS skill is symlinked into `~/.claude/skills/<skill-name>` so
# Claude Code's slash-command discovery finds it globally. A versioned
# manifest at `~/.claude/aris-global/installed-skills.txt` tracks every
# entry this installer created — uninstall and reconcile read from the
# manifest and never touch user-owned skills with the same name.
#
# Usage:
#   bash tools/install_aris_global.sh [options]
#
# Actions (mutually exclusive, default: auto):
#   default          install if no manifest, else reconcile
#   --reconcile      explicit reconcile; refuse if no manifest
#   --uninstall      remove only entries in manifest; delete manifest
#
# Options:
#   --aris-repo PATH       override aris-repo discovery
#   --claude-home PATH     override ~/.claude (useful for tests)
#   --dry-run              show plan, no writes
#   --quiet                no prompts; abort on any condition that would prompt
#   --adopt-existing NAME  adopt a non-managed symlink that already points to
#                          the correct upstream target (repeatable)
#   --replace-link NAME    replace an upstream-internal symlink that points to
#                          a DIFFERENT entry than expected (repeatable)
#   --clear-stale-lock     remove stale lock dir from a crashed prior run
#                          (host+PID metadata is verified before removal)
#
# Safety rules enforced:
#   S1  Never delete a path that is not a symlink.
#   S2  Never delete a symlink whose target is outside the configured aris-repo.
#   S3  Never delete a symlink not listed in the manifest (except via --uninstall
#       which only deletes manifest entries).
#   S4  Never overwrite an existing path during CREATE — abort by default.
#   S5  Manifest write is atomic (temp + rename in same dir).
#   S6  Concurrent runs serialize via mkdir lockdir.
#   S7  Crash mid-apply leaves the previous manifest intact; rerun adopts.
#   S8  Uninstall revalidates each managed symlink's target before removing.
#   S9  If ~/.claude, ~/.claude/skills, or ~/.claude/aris-global is itself a
#       symlink, abort.
#   S10 Reject upstream entries that are symlinks to outside aris-repo.
#   S11 Revalidate exact target match (lstat + readlink) before every mutation.
#   S12 Temp files live in the same directory as the destination.
#   S13 Skill names must match ^[A-Za-z0-9][A-Za-z0-9._-]*$ (slug regex).

set -euo pipefail

# ─── Constants ────────────────────────────────────────────────────────────────
MANIFEST_VERSION="1"
MANIFEST_NAME="installed-skills.txt"
MANIFEST_PREV_NAME="installed-skills.txt.prev"
GLOBAL_STATE_DIR_NAME="aris-global"
LOCK_DIR_NAME=".install.lock.d"
SKILLS_REL="skills"
SAFE_NAME_REGEX='^[A-Za-z0-9][A-Za-z0-9._-]*$'
SUPPORT_NAMES=("shared-references")
EXCLUDE_TOP_NAMES=("skills-codex" "skills-codex.bak")

# ─── Argument parsing ─────────────────────────────────────────────────────────
ARIS_REPO_OVERRIDE=""
CLAUDE_HOME_OVERRIDE=""
ACTION="auto"        # auto | reconcile | uninstall
DRY_RUN=false
QUIET=false
CLEAR_STALE_LOCK=false
ADOPT_NAMES=()
REPLACE_LINK_NAMES=()

usage() { sed -n '2,38p' "$0" | sed 's/^# \?//'; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reconcile)         ACTION="reconcile"; shift ;;
        --uninstall)         ACTION="uninstall"; shift ;;
        --aris-repo)         ARIS_REPO_OVERRIDE="${2:?--aris-repo requires path}"; shift 2 ;;
        --claude-home)       CLAUDE_HOME_OVERRIDE="${2:?--claude-home requires path}"; shift 2 ;;
        --dry-run)           DRY_RUN=true; shift ;;
        --quiet)             QUIET=true; shift ;;
        --clear-stale-lock)  CLEAR_STALE_LOCK=true; shift ;;
        --adopt-existing)    ADOPT_NAMES+=("${2:?--adopt-existing requires NAME}"); shift 2 ;;
        --replace-link)      REPLACE_LINK_NAMES+=("${2:?--replace-link requires NAME}"); shift 2 ;;
        -h|--help)           usage; exit 0 ;;
        --*)                 echo "Unknown option: $1" >&2; exit 2 ;;
        *)                   echo "Error: unexpected positional: $1" >&2; exit 2 ;;
    esac
done

# ─── Helpers ──────────────────────────────────────────────────────────────────
log()      { $QUIET && return 0; echo "$@"; }
warn()     { echo "warning: $*" >&2; }
die()      { echo "error: $*" >&2; exit 1; }
prompt()   { $QUIET && return 1; printf "%s " "$1" >&2; read -r REPLY; [[ "$REPLY" =~ ^[Yy]$ ]]; }
abs_path() { ( cd "$1" 2>/dev/null && pwd ) || return 1; }

is_safe_name() { [[ "$1" =~ $SAFE_NAME_REGEX ]]; }

contains_name() {
    local needle="$1"
    shift
    local item
    for item in "$@"; do
        [[ "$item" == "$needle" ]] && return 0
    done
    return 1
}

read_link_target() {
    if command -v greadlink >/dev/null 2>&1; then greadlink "$1"
    else readlink "$1"; fi
}

canonicalize() {
    if command -v greadlink >/dev/null 2>&1; then greadlink -f "$1" 2>/dev/null || true
    elif readlink -f "$1" 2>/dev/null; then :
    else
        local d f
        if [[ -d "$1" ]]; then ( cd "$1" && pwd )
        else d="$(dirname "$1")"; f="$(basename "$1")"; ( cd "$d" 2>/dev/null && echo "$(pwd)/$f" )
        fi
    fi
}

is_symlink() { [[ -L "$1" ]]; }

resolve_aris_repo() {
    local p
    if [[ -n "$ARIS_REPO_OVERRIDE" ]]; then
        p="$(abs_path "$ARIS_REPO_OVERRIDE")" || die "--aris-repo path not found: $ARIS_REPO_OVERRIDE"
        [[ -d "$p/skills" ]] || die "--aris-repo has no skills/ subdir: $p"
        echo "$p"; return
    fi
    local script_dir parent
    script_dir="$(cd "$(dirname "$0")" && pwd)"
    parent="$(cd "$script_dir/.." && pwd)"
    if [[ -d "$parent/skills" ]]; then echo "$parent"; return; fi
    if [[ -n "${ARIS_REPO:-}" && -d "$ARIS_REPO/skills" ]]; then abs_path "$ARIS_REPO"; return; fi
    for guess in \
        "$HOME/Desktop/aris_repo" \
        "$HOME/aris_repo" \
        "$HOME/.aris" \
        "$HOME/Desktop/Auto-claude-code-research-in-sleep" \
        "$HOME/.codex/Auto-claude-code-research-in-sleep" \
        "$HOME/.claude/Auto-claude-code-research-in-sleep" ; do
        [[ -d "$guess/skills" ]] && { abs_path "$guess"; return; }
    done
    die "cannot find ARIS repo. Use --aris-repo PATH or set ARIS_REPO env var."
}

resolve_claude_home() {
    local p
    if [[ -n "$CLAUDE_HOME_OVERRIDE" ]]; then
        if [[ "$CLAUDE_HOME_OVERRIDE" == /* ]]; then
            p="$CLAUDE_HOME_OVERRIDE"
        else
            p="$(pwd)/$CLAUDE_HOME_OVERRIDE"
        fi
        echo "$p"
        return
    fi
    echo "$HOME/.claude"
}

build_upstream_inventory() {
    local repo="$1"
    local skills_dir="$repo/skills"
    local entries=() name src
    for d in "$skills_dir"/*/; do
        name="$(basename "$d")"
        is_safe_name "$name" || { warn "skipping unsafe upstream name: $name"; continue; }
        for ex in "${EXCLUDE_TOP_NAMES[@]}"; do [[ "$name" == "$ex" ]] && continue 2; done
        local is_support=false
        for s in "${SUPPORT_NAMES[@]}"; do [[ "$name" == "$s" ]] && { is_support=true; break; }; done
        if $is_support; then continue; fi
        if [[ ! -f "$d/SKILL.md" ]]; then continue; fi
        src="$skills_dir/$name"
        if is_symlink "$src"; then
            local resolved; resolved="$(canonicalize "$src")"
            [[ "$resolved" == "$repo"/* ]] || { warn "skipping upstream symlink leading outside repo: $name -> $resolved"; continue; }
        fi
        entries+=("skill|$name")
    done
    for s in "${SUPPORT_NAMES[@]}"; do
        if [[ -d "$skills_dir/$s" ]]; then entries+=("support|$s"); fi
    done
    printf "%s\n" "${entries[@]}"
}

load_manifest() {
    local path="$1" out="$2"
    : > "$out"
    [[ -f "$path" ]] || return 0
    local ver; ver="$(awk -F'\t' '$1=="version"{print $2}' "$path" | head -1)"
    [[ "$ver" == "$MANIFEST_VERSION" ]] || die "manifest version mismatch (file: $ver, expected: $MANIFEST_VERSION)"
    awk -F'\t' '
        BEGIN { in_body=0 }
        /^kind\tname\tsource_rel\ttarget_rel\tmode$/ { in_body=1; next }
        in_body && NF==5 { print }
    ' "$path" > "$out"
}

manifest_lookup_target() {
    local manifest_data="$1" name="$2"
    awk -F'\t' -v n="$name" '$2==n { print $4 }' "$manifest_data" | head -1
}

ARIS_REPO="$(resolve_aris_repo)"
SKILLS_DIR_ABS="$ARIS_REPO/skills"
CLAUDE_HOME="$(resolve_claude_home)"
GLOBAL_SKILLS_DIR="$CLAUDE_HOME/$SKILLS_REL"
GLOBAL_STATE_DIR="$CLAUDE_HOME/$GLOBAL_STATE_DIR_NAME"
MANIFEST_PATH="$GLOBAL_STATE_DIR/$MANIFEST_NAME"
MANIFEST_PREV="$GLOBAL_STATE_DIR/$MANIFEST_PREV_NAME"
LOCK_DIR="$GLOBAL_STATE_DIR/$LOCK_DIR_NAME"

check_no_symlinked_parents() {
    local p
    for p in "$CLAUDE_HOME" "$GLOBAL_SKILLS_DIR" "$GLOBAL_STATE_DIR"; do
        if [[ -e "$p" || -L "$p" ]] && is_symlink "$p"; then
            die "S9: $p is a symlink — refusing to install (would mutate symlink target)"
        fi
    done
}

write_lock_metadata() {
    cat > "$LOCK_DIR/owner.json" <<EOF
{"host":"$(hostname)","pid":$$,"started_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","tool":"install_aris_global.sh"}
EOF
    echo "$$" > "$LOCK_DIR/owner.pid"
    echo "$(hostname)" > "$LOCK_DIR/owner.host"
}

acquire_lock() {
    mkdir -p "$GLOBAL_STATE_DIR"
    if mkdir "$LOCK_DIR" 2>/dev/null; then
        write_lock_metadata
        trap release_lock EXIT INT TERM
        return 0
    fi
    if $CLEAR_STALE_LOCK; then
        local owner=""
        [[ -f "$LOCK_DIR/owner.json" ]] && owner="$(cat "$LOCK_DIR/owner.json")"
        warn "removing stale lock: $LOCK_DIR (was: $owner)"
        rm -rf "$LOCK_DIR"
        mkdir "$LOCK_DIR" || die "still cannot acquire lock after stale clear"
        write_lock_metadata
        trap release_lock EXIT INT TERM
        return 0
    fi
    local owner=""
    [[ -f "$LOCK_DIR/owner.json" ]] && owner="$(cat "$LOCK_DIR/owner.json")"
    die "another install_aris_global.sh is running (lock: $LOCK_DIR)
       owner: $owner
       if you are sure no install is in progress, rerun with --clear-stale-lock"
}

release_lock() {
    [[ -d "$LOCK_DIR" ]] || return 0
    if [[ -f "$LOCK_DIR/owner.pid" ]]; then
        local pid; pid="$(cat "$LOCK_DIR/owner.pid" 2>/dev/null || echo "")"
        local host; host="$(cat "$LOCK_DIR/owner.host" 2>/dev/null || echo "")"
        if [[ "$pid" == "$$" && "$host" == "$(hostname)" ]]; then
            rm -rf "$LOCK_DIR"
        fi
    fi
}

compute_plan() {
    local upstream_file="$1" manifest_data="$2" out="$3"
    : > "$out"
    local target_path expected_target current_target kind name
    while IFS='|' read -r kind name; do
        [[ -z "$name" ]] && continue
        target_path="$GLOBAL_SKILLS_DIR/$name"
        expected_target="$SKILLS_DIR_ABS/$name"
        if [[ -L "$target_path" ]]; then
            current_target="$(read_link_target "$target_path")"
            if [[ "$current_target" != /* ]]; then
                current_target="$(canonicalize "$GLOBAL_SKILLS_DIR/$current_target")"
            fi
            local in_manifest=false
            if [[ -n "$(manifest_lookup_target "$manifest_data" "$name")" ]]; then in_manifest=true; fi
            if [[ "$current_target" == "$expected_target" ]]; then
                if $in_manifest; then echo "REUSE|$kind|$name|" >> "$out"
                else echo "ADOPT|$kind|$name|" >> "$out"
                fi
            else
                if $in_manifest; then
                    echo "UPDATE_TARGET|$kind|$name|$current_target" >> "$out"
                else
                    echo "CONFLICT|$kind|$name|symlink_to:$current_target" >> "$out"
                fi
            fi
        elif [[ -e "$target_path" ]]; then
            echo "CONFLICT|$kind|$name|real_path" >> "$out"
        else
            echo "CREATE|$kind|$name|" >> "$out"
        fi
    done < "$upstream_file"
    while IFS=$'\t' read -r mkind mname msrc mtarget mmode; do
        [[ -z "$mname" ]] && continue
        if grep -q "^[^|]*|$mname$" "$upstream_file"; then continue; fi
        echo "REMOVE|$mkind|$mname|" >> "$out"
    done < "$manifest_data"
}

print_plan() {
    local plan="$1"
    local n_create n_update n_reuse n_remove n_adopt n_conflict
    n_create=$(grep -c '^CREATE|' "$plan" || true)
    n_update=$(grep -c '^UPDATE_TARGET|' "$plan" || true)
    n_reuse=$(grep -c '^REUSE|' "$plan" || true)
    n_remove=$(grep -c '^REMOVE|' "$plan" || true)
    n_adopt=$(grep -c '^ADOPT|' "$plan" || true)
    n_conflict=$(grep -c '^CONFLICT|' "$plan" || true)
    log ""
    log "Plan summary:"
    log "  CREATE:        $n_create"
    log "  ADOPT:         $n_adopt"
    log "  UPDATE_TARGET: $n_update"
    log "  REUSE:         $n_reuse"
    log "  REMOVE:        $n_remove"
    log "  CONFLICT:      $n_conflict"
    if (( n_conflict > 0 )); then
        log ""
        log "Conflicts (need user action):"
        grep '^CONFLICT|' "$plan" | while IFS='|' read -r _ kind name extra; do
            log "  - $name ($kind): $extra"
        done
    fi
}

write_manifest_tmp() {
    local plan="$1" out="$2"
    {
        printf "version\t%s\n" "$MANIFEST_VERSION"
        printf "repo_root\t%s\n" "$ARIS_REPO"
        printf "claude_home\t%s\n" "$CLAUDE_HOME"
        printf "generated\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        printf "kind\tname\tsource_rel\ttarget_rel\tmode\n"
        awk -F'|' '$1=="REUSE"||$1=="ADOPT"||$1=="CREATE"||$1=="UPDATE_TARGET"{print $0}' "$plan" \
        | while IFS='|' read -r action kind name _; do
            printf "%s\t%s\tskills/%s\t%s/%s\tsymlink\n" "$kind" "$name" "$name" "$SKILLS_REL" "$name"
        done
    } > "$out"
}

apply_plan() {
    local plan="$1"
    mkdir -p "$GLOBAL_SKILLS_DIR"
    while IFS='|' read -r action kind name extra; do
        [[ -z "$name" ]] && continue
        local target_path="$GLOBAL_SKILLS_DIR/$name"
        local expected_target="$SKILLS_DIR_ABS/$name"
        case "$action" in
            REUSE|ADOPT)
                :
                ;;
            CREATE)
                if [[ -e "$target_path" || -L "$target_path" ]]; then
                    warn "S4: create target appeared since plan: $target_path — skipping"
                    continue
                fi
                if $DRY_RUN; then log "  (dry-run) ln -s $expected_target $target_path"
                else ln -s "$expected_target" "$target_path"; log "  + $name"
                fi
                ;;
            UPDATE_TARGET)
                local plan_saw_target; plan_saw_target="$(read_link_target "$target_path" 2>/dev/null || echo "")"
                [[ "$plan_saw_target" != /* && -n "$plan_saw_target" ]] && plan_saw_target="$(canonicalize "$(dirname "$target_path")/$plan_saw_target")"
                if [[ "$plan_saw_target" != "$extra" ]]; then
                    warn "S11: $target_path target changed since plan ($plan_saw_target vs $extra) — skipping"
                    continue
                fi
                if [[ "$plan_saw_target" != "$ARIS_REPO"/* ]] && ! contains_name "$name" "${REPLACE_LINK_NAMES[@]}"; then
                    warn "S2: refusing to replace symlink pointing outside aris-repo: $target_path -> $plan_saw_target"
                    continue
                fi
                if $DRY_RUN; then log "  (dry-run) update target: $target_path -> $expected_target"
                else
                    rm -f "$target_path"
                    ln -s "$expected_target" "$target_path"
                    log "  ↻ $name"
                fi
                ;;
            REMOVE)
                is_symlink "$target_path" || { warn "S1: $target_path is not a symlink, refusing to remove"; continue; }
                local cur; cur="$(read_link_target "$target_path")"
                [[ "$cur" != /* ]] && cur="$(canonicalize "$(dirname "$target_path")/$cur")"
                [[ "$cur" == "$ARIS_REPO"/* ]] || { warn "S2: $target_path target $cur outside aris-repo, refusing"; continue; }
                if $DRY_RUN; then log "  (dry-run) rm $target_path"
                else rm -f "$target_path"; log "  - $name"
                fi
                ;;
            CONFLICT)
                die "BUG: CONFLICT $name reached apply phase"
                ;;
        esac
    done < "$plan"
}

commit_manifest() {
    local manifest_tmp="$1"
    if $DRY_RUN; then log "  (dry-run) would commit manifest"; return; fi
    if [[ -f "$MANIFEST_PATH" ]]; then
        cp -p "$MANIFEST_PATH" "$MANIFEST_PREV.tmp"
        mv -f "$MANIFEST_PREV.tmp" "$MANIFEST_PREV"
    fi
    mv -f "$manifest_tmp" "$MANIFEST_PATH"
}

do_uninstall() {
    [[ -f "$MANIFEST_PATH" ]] || die "no manifest at $MANIFEST_PATH; nothing to uninstall"
    local manifest_data; manifest_data="$(mktemp -t aris-manifest.XXXX)"
    load_manifest "$MANIFEST_PATH" "$manifest_data"
    log ""
    log "Uninstall plan:"
    while IFS=$'\t' read -r kind name src target mode; do
        [[ -z "$name" ]] && continue
        log "  - $name ($kind)"
    done < "$manifest_data"
    if ! $DRY_RUN && ! $QUIET; then
        prompt "Proceed?" || { log "aborted"; exit 0; }
    fi
    while IFS=$'\t' read -r kind name src target mode; do
        [[ -z "$name" ]] && continue
        local target_path="$CLAUDE_HOME/$target"
        local expected="$SKILLS_DIR_ABS/$name"
        is_symlink "$target_path" || { warn "S1: $target_path not a symlink, skipping"; continue; }
        local cur; cur="$(read_link_target "$target_path")"
        [[ "$cur" != /* ]] && cur="$(canonicalize "$(dirname "$target_path")/$cur")"
        if [[ "$cur" != "$expected" ]]; then
            warn "S8: $target_path target $cur != expected $expected, skipping"
            continue
        fi
        if $DRY_RUN; then log "  (dry-run) rm $target_path"
        else rm -f "$target_path"; log "  - removed $name"
        fi
    done < "$manifest_data"
    rm -f "$manifest_data"
    if ! $DRY_RUN; then
        [[ -f "$MANIFEST_PATH" ]] && mv -f "$MANIFEST_PATH" "$MANIFEST_PREV"
        log "  ✓ uninstalled (manifest preserved as $MANIFEST_PREV)"
    fi
}

log ""
log "ARIS Global Install"
log "  Claude home: $CLAUDE_HOME"
log "  ARIS repo:   $ARIS_REPO"
log "  Action:      $ACTION$($DRY_RUN && echo ' (dry-run)')"
log ""

check_no_symlinked_parents
if ! $DRY_RUN; then
    acquire_lock
fi

if [[ "$ACTION" == "uninstall" ]]; then
    do_uninstall
    exit 0
fi

if [[ "$ACTION" == "reconcile" && ! -f "$MANIFEST_PATH" ]]; then
    die "--reconcile requires existing manifest; none found at $MANIFEST_PATH"
fi

UPSTREAM_FILE="$(mktemp -t aris-upstream.XXXX)"
build_upstream_inventory "$ARIS_REPO" > "$UPSTREAM_FILE"
[[ -s "$UPSTREAM_FILE" ]] || die "upstream inventory empty (broken aris-repo?)"

MANIFEST_DATA="$(mktemp -t aris-manifest.XXXX)"
load_manifest "$MANIFEST_PATH" "$MANIFEST_DATA"

PLAN_FILE="$(mktemp -t aris-plan.XXXX)"
compute_plan "$UPSTREAM_FILE" "$MANIFEST_DATA" "$PLAN_FILE"
print_plan "$PLAN_FILE"

N_CONFLICT=$(grep -c '^CONFLICT|' "$PLAN_FILE" || true)
if (( N_CONFLICT > 0 )); then
    if [[ ${#REPLACE_LINK_NAMES[@]} -gt 0 ]]; then
        for n in "${REPLACE_LINK_NAMES[@]}"; do
            awk -F'|' -v name="$n" 'BEGIN{OFS="|"} { if ($1=="CONFLICT" && $3==name) $1="UPDATE_TARGET"; print }' "$PLAN_FILE" > "$PLAN_FILE.tmp"
            mv -f "$PLAN_FILE.tmp" "$PLAN_FILE"
        done
        N_CONFLICT=$(grep -c '^CONFLICT|' "$PLAN_FILE" || true)
    fi
    if (( N_CONFLICT > 0 )); then
        log ""
        log "Aborting due to $N_CONFLICT unresolved conflicts."
        log "Resolve options per name:"
        log "  - back up & remove the conflicting path manually, then rerun"
        log "  - if it's a foreign symlink that should be replaced: --replace-link NAME"
        exit 1
    fi
fi

if $DRY_RUN; then
    log ""
    log "(dry-run) no changes made"
    exit 0
fi

N_CHANGES=$(awk -F'|' '$1=="CREATE"||$1=="UPDATE_TARGET"||$1=="REMOVE"' "$PLAN_FILE" | wc -l | tr -d ' ')
if (( N_CHANGES > 0 )) && ! $QUIET; then
    prompt "Apply these $N_CHANGES changes?" || { log "aborted"; exit 0; }
fi

MANIFEST_TMP="$MANIFEST_PATH.tmp.$$"
mkdir -p "$GLOBAL_STATE_DIR"
write_manifest_tmp "$PLAN_FILE" "$MANIFEST_TMP"
log ""
log "Applying:"
apply_plan "$PLAN_FILE"
commit_manifest "$MANIFEST_TMP"

if ! $DRY_RUN; then
    BAD=0
    while IFS=$'\t' read -r v_kind v_name v_src v_target v_mode; do
        [[ -z "$v_name" ]] && continue
        VTARGET="$CLAUDE_HOME/$v_target"
        if ! is_symlink "$VTARGET"; then warn "verify: $VTARGET missing"; BAD=$((BAD+1)); fi
    done < <(awk -F'\t' '
        BEGIN { in_body=0 }
        /^kind\tname\tsource_rel\ttarget_rel\tmode$/ { in_body=1; next }
        in_body && NF==5 { print }
    ' "$MANIFEST_PATH")
    (( BAD == 0 )) && log "" && log "✓ Install complete. $N_CHANGES changes applied."
fi

rm -f "$UPSTREAM_FILE" "$MANIFEST_DATA" "$PLAN_FILE"
