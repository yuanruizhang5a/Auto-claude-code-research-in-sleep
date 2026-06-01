# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

**ARIS** (Auto-claude-code-research-in-sleep) is a zero-build, plain-Markdown research automation harness. It orchestrates a full ML research lifecycle—literature survey, idea generation, experiment execution, cross-model adversarial review, and paper writing—through composable "skill" files. No build step, no package.json, no compiled artifacts.

## Running Tests

```bash
python3 -m unittest discover tests/   # stdlib only, no config file needed
python3 tests/test_<name>.py          # single test file
```

Tests use `unittest.mock` to patch subprocess and filesystem calls. No live API keys required.

## Installing Skills Into a Research Project

```bash
bash tools/install_aris.sh [project_path]
```

Creates one symlink per skill at `.claude/skills/<skill-name>` and writes a versioned manifest to `.aris/installed-skills.txt`. Re-runnable to reconcile added/removed skills.

Managed global Claude install:

```bash
bash tools/install_aris_global.sh
```

Creates one symlink per skill at `~/.claude/skills/<skill-name>` and writes a versioned manifest to `~/.claude/aris-global/installed-skills.txt`. Prefer the project-local installer when you want to avoid collisions with other global skill packs.

## MCP Server Dependencies

Install per-server as needed — servers are in `mcp-servers/`:

| Server | Pip dependency |
|---|---|
| `feishu-bridge` | `lark-oapi` |
| `llm-chat`, `minimax-chat`, `codex-image2` | `httpx` |
| `gemini-review`, `claude-review` | stdlib only (calls `gemini`/`claude` CLI via subprocess) |

## Architecture

### Skills

Each skill is a single `skills/<name>/SKILL.md` file:

```markdown
---
name: skill-name
description: "Used for slash-command discovery"
allowed-tools: Bash(*), Read, Write, Edit, ...
---
```

Invoked as slash commands: `/skill-name "arguments" — key: value`. The `SKILL.md` file is the authoritative spec for that skill's behavior. `AGENT_GUIDE.md` is a routing index only.

### Cross-Model Protocol (most critical convention)

- **Executor** (Claude Code / Codex): writes code, runs experiments, drafts text
- **Reviewer** (GPT/Gemini/GLM via MCP): critiques, scores, demands revisions
- Executor and reviewer must be **different model families**
- Default reviewer: `mcp__codex__codex` with `reasoning_effort: xhigh`; override with `— reviewer: claude` (local Claude Code CLI via `claude-review` MCP, model pinned by `CLAUDE_REVIEW_MODEL`) or `— reviewer: oracle-pro` (GPT-5.4 Pro via Oracle MCP)
- **Reviewer independence** (`skills/shared-references/reviewer-independence.md`): pass only file paths + role + task to reviewer — never executor summaries, fix descriptions, or leading context. Use a fresh Codex thread per review round (`mcp__codex__codex`, not `mcp__codex__codex-reply`)

### Major Workflows

| Skill | Entry point | Pipeline stage |
|---|---|---|
| Full pipeline | `/research-pipeline` | W1 → W1.5 → W2 → W3 end-to-end |
| Idea Discovery | `/idea-discovery` | W1: lit survey → ideation → novelty check → review |
| Experiment Bridge | `/experiment-bridge` | W1.5: implements + runs from `EXPERIMENT_PLAN.md` |
| Auto Review Loop | `/auto-review-loop` | W2: GPT review → Claude fixes → repeat |
| Paper Writing | `/paper-writing` | W3: plan → figures → LaTeX → compile → improve |
| Rebuttal | `/rebuttal` | W4: parse reviews → strategy → draft → stress test |

### Output File Protocol

Every overwritten output file is first timestamped as `FILENAME_YYYYMMDD_HHmmss.md`, then copied to the fixed name. Downstream skills always read the fixed name. Never delete timestamped files.

Stage-scoped directories:
```
project/
├── idea-stage/IDEA_REPORT.md        # W1 output
├── refine-logs/EXPERIMENT_PLAN.md   # W1.5 input
├── review-stage/AUTO_REVIEW.md      # W2 output
├── paper/main.tex                   # W3 output
└── .aris/
    ├── meta/events.jsonl            # meta-optimize hook log
    └── traces/                      # full review prompt/response pairs
```

Skills fall back to root-level files (`./IDEA_REPORT.md`) for backward compatibility with pre-layout projects.

### Effort and Assurance Levels

Every skill accepts `— effort: lite | balanced | max | beast` (default: `balanced`):
- `lite` (~0.4×): fewer papers, ideas, rounds
- `max` (~2.5×) and `beast` (~5–8×) both imply `assurance: submission`

`assurance: submission` requires all audit skills (`/proof-checker`, `/paper-claim-audit`, `/citation-audit`) to emit a JSON verdict; `tools/verify_paper_audits.sh` blocks Final Report on failure.

### MCP Servers

All servers are stateless Python stdio servers implementing JSON-RPC 2.0. Async servers (`codex-image2`, `gemini-review`) use a `generate_start` / `generate_status` pattern to avoid the ~120 s MCP tool timeout.

## Key Shared References

All in `skills/shared-references/` — read these before modifying skill behavior:

- `reviewer-independence.md` — what can/cannot be passed to a reviewer
- `effort-contract.md` — per-skill effort tables
- `assurance-contract.md` — 6-state verdict schema for submission gate
- `output-versioning.md` — timestamped file protocol
- `experiment-integrity.md` — prohibited patterns for experiment code
- `citation-discipline.md` — DBLP/CrossRef validation rules

## Non-obvious Conventions

- `patent/` is gitignored to protect confidential invention details; the skill framework files in `skills/` are tracked.
- Research Wiki (`research-wiki/`) is optional. If present, paper-reading skills auto-ingest via `python3 tools/research_wiki.py ingest_paper`. Absence is graceful.
- Meta-optimize event capture: copy `templates/claude-hooks/meta_logging.json` into the project's `.claude/settings.json` to enable. Logs go to `.aris/meta/events.jsonl`.
- `AUTO_PROCEED: true` in pipeline skills auto-selects the top idea after a 10-second pause; always false at expensive decision gates unless overridden.
- Large-file write fallback: if the `Write` tool fails on size, skills silently retry with `Bash` (`cat << 'EOF' > file`) without prompting the user.
<!-- ARIS:BEGIN -->
## ARIS Skill Scope
ARIS skills installed in this project: 70 entries.
Manifest: `.aris/installed-skills.txt` (lists every skill ARIS installed and its upstream target).
For ARIS workflows, prefer the project-local skills under `.claude/skills/` over global skills.
Do not modify or delete files inside any skill that is a symlink (symlinks point into `/home/zyr/myCode/Auto-claude-code-research-in-sleep`).
Update with: `bash /home/zyr/myCode/Auto-claude-code-research-in-sleep/tools/install_aris.sh`  (re-runnable; reconciles new/removed skills).
<!-- ARIS:END -->
