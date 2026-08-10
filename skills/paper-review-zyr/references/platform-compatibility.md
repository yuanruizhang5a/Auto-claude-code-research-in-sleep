# Claude Code, OpenCode, and Codex Compatibility

Use one canonical skill directory on all three hosts. These locations and invocation forms were verified against official documentation on 2026-08-10.

## Contents

- [Portable package contract](#portable-package-contract)
- [Installation locations](#installation-locations)
- [Invocation](#invocation)
- [Delegation mapping](#delegation-mapping)
- [Resource resolution](#resource-resolution)
- [Compatibility smoke tests](#compatibility-smoke-tests)
- [Official references](#official-references)

## Portable package contract

Keep the same directory contents and behavioral semantics on every host:

```text
paper-review-zyr/
|-- SKILL.md
|-- template.tex
|-- letterbib.sty
|-- agents/openai.yaml
|-- references/
`-- scripts/
```

Require only `name` and `description` in `SKILL.md` frontmatter. Those fields form the shared Agent Skills subset. Keep `agents/openai.yaml` optional: Codex/ChatGPT may use it for presentation, while Claude Code and OpenCode can ignore it.

Do not add Claude-only frontmatter such as `allowed-tools`, `context`, or argument substitutions to the canonical file. Do not add OpenCode-only metadata to the canonical file. Do not name product-specific tools in the workflow body.

## Installation locations

Inspect the destination before copying or linking. If a skill with the same name exists, stop and ask whether to update, select a different scope, or preserve both under distinct names. Never silently overwrite an unrelated installation.

### Claude Code

- Personal: `~/.claude/skills/paper-review-zyr/SKILL.md`
- Project: `<project>/.claude/skills/paper-review-zyr/SKILL.md`

Claude Code discovers supporting files beside `SKILL.md` and invokes the directory name as the command.

### OpenCode

- Global native: `~/.config/opencode/skills/paper-review-zyr/SKILL.md`
- Project native: `<project>/.opencode/skills/paper-review-zyr/SKILL.md`
- Global compatibility: `~/.claude/skills/...` or `~/.agents/skills/...`
- Project compatibility: `.claude/skills/...` or `.agents/skills/...`

OpenCode walks upward to the worktree root for project skill locations and loads supporting files relative to the directory-form `SKILL.md`.

### Codex

- User: `~/.agents/skills/paper-review-zyr/SKILL.md`
- Repository: `<working-directory-or-ancestor>/.agents/skills/paper-review-zyr/SKILL.md`
- Admin, when managed by an administrator: `/etc/codex/skills/paper-review-zyr/SKILL.md`

Codex follows symlinked skill directories. Its optional presentation metadata lives at `agents/openai.yaml`.

### One repository for all three

Keep one canonical directory in the repository and expose it at both:

```text
.claude/skills/paper-review-zyr
.agents/skills/paper-review-zyr
```

Use copies or symlinks that resolve to the same canonical content. Claude Code discovers the first path, Codex discovers the second, and OpenCode discovers either compatibility path. Do not maintain separate edited bodies.

## Invocation

Use the same argument semantics on all hosts:

- Claude Code: `/paper-review-zyr path/to/paper.tex --reviews ... --style-materials ...`
- OpenCode: `/paper-review-zyr path/to/paper.tex --reviews ... --style-materials ...`, or ask the agent to load `paper-review-zyr` when slash discovery is unavailable.
- Codex: mention `$paper-review-zyr` with the arguments, or select it through the skills interface.
- Implicit: ask for a peer-review response/revision task matching the `description`.

Do not rely on Claude's `$ARGUMENTS` preprocessing. Parse arguments from the host-provided invocation text or current user request as specified by `SKILL.md`.

## Delegation mapping

Treat every worker definition in `SKILL.md` as a role contract:

| Host | Preferred execution | Fallback |
|---|---|---|
| Claude Code | Native subagent/task delegation | Run the role sequentially in the main agent. |
| OpenCode | Native task/subagent delegation permitted by the active agent | Run the role sequentially in the main agent. |
| Codex | Native subagent collaboration | Run the role sequentially in the primary agent. |

Do not weaken inputs, outputs, JSON validation, or stage gates in fallback mode. Record `execution_mode` as `delegated`, `mixed`, or `sequential`. Reviewer independence still requires raw file paths rather than an orchestrator-written subjective summary.

## Resource resolution

Resolve `SKILL_ROOT` from the loaded `SKILL.md` location supplied or discoverable by the host. Join bundled paths to that directory:

```text
SKILL_ROOT/template.tex
SKILL_ROOT/letterbib.sty
SKILL_ROOT/references/state-schema.md
SKILL_ROOT/references/response-rules.md
SKILL_ROOT/scripts/resolve_revision_paths.py
SKILL_ROOT/scripts/validate_review_state.py
```

Do not infer `SKILL_ROOT` from the working directory. The working directory belongs to the manuscript project and contains `./com`; the installed skill directory contains read-only workflow resources.

Use Python 3 standard-library code for the validator. Detect `latexmk`, `pdflatex`, and bibliography tools before invoking them. A missing optional executable must follow the fallback or produce an actionable persisted failure.

## Compatibility smoke tests

Run these checks with the same unchanged skill directory on each available host:

1. Install or link the directory at one documented scope without overwriting an existing skill.
2. Confirm discovery shows `paper-review-zyr` and the frontmatter description.
3. Invoke it explicitly with a temporary minimal paper, a plain-text review, style material, and `--no-compile`.
4. Confirm the host resolves `template.tex`, `letterbib.sty`, both references, and the validator relative to `SKILL.md`.
5. Confirm default mode preserves `paper.tex` and `review.tex`, resolves the first unused `paper_rN.tex` and `review_rN.tex`, and creates the latter from the bundled template with `\ranswer` when its source is absent.
6. Confirm `--overwirte` resolves both outputs to their corresponding source paths; do not use this destructive-mode smoke test on valuable files.
7. Confirm `./com/orchestrator.json` contains the compatible top-level keys plus `paper_review_zyr` and the four source/output paths.
8. Confirm a complex experiment request stops at a persisted user checkpoint without creating a paper revision when no paper mutation occurred.
9. Resume the same run and confirm the saved `_rN` outputs, stable issue IDs, and no duplicate answers or edits.
10. Exercise one delegated worker when available; otherwise confirm the sequential fallback records its mode.
11. Run `python3 <skill-root>/scripts/validate_review_state.py --com-dir ./com`.

If a client is unavailable, perform a structural substitute test using its documented discovery layout and clearly report that live invocation remains unverified. Do not claim a live three-client smoke test from static file checks alone.

## Official references

- Claude Code skills: <https://code.claude.com/docs/en/skills>
- OpenCode Agent Skills: <https://opencode.ai/docs/skills>
- Codex Build Skills: <https://learn.chatgpt.com/docs/build-skills>
