# skills-codex-claude-review

This package is a **thin override layer** for users who want:

- **Any non-Claude executor** (Codex CLI, Opencode, Cursor, Trae, Windsurf, etc.) as the main executor
- **Claude Code** (via the local `claude-review` MCP bridge) as the reviewer
- a different model family for reviewer vs executor, satisfying the ARIS cross-model independence protocol

It is designed to sit on top of the upstream Codex-native package at `skills/skills-codex/`.

## What this package contains

- Only the review-heavy skill overrides that need a different reviewer backend
- No duplicate templates or resource directories
- No replacement for the base `skills/skills-codex/` installation

Current overrides:

- `research-review`
- `novelty-check`
- `research-refine`
- `auto-review-loop`
- `paper-plan`
- `paper-figure`
- `paper-write`
- `auto-paper-improvement-loop`

## Install

### For Codex CLI users

1. Install the base Codex-native skills first:

```bash
mkdir -p ~/.codex/skills
cp -a skills/skills-codex/* ~/.codex/skills/
```

2. Install the Claude-review overrides second:

```bash
cp -a skills/skills-codex-claude-review/* ~/.codex/skills/
```

3. Register the local reviewer bridge:

```bash
mkdir -p ~/.codex/mcp-servers/claude-review
cp mcp-servers/claude-review/server.py ~/.codex/mcp-servers/claude-review/server.py
codex mcp add claude-review -- python3 ~/.codex/mcp-servers/claude-review/server.py
```

If your Claude setup depends on a shell helper such as `claude-aws`, use the wrapper instead:

```bash
cp mcp-servers/claude-review/run_with_claude_aws.sh ~/.codex/mcp-servers/claude-review/run_with_claude_aws.sh
chmod +x ~/.codex/mcp-servers/claude-review/run_with_claude_aws.sh
codex mcp add claude-review -- ~/.codex/mcp-servers/claude-review/run_with_claude_aws.sh
```

### For Opencode users

1. Install the base ARIS skills into your project via `tools/install_aris.sh`:

```bash
bash tools/install_aris.sh <your-project-path>
```

2. Copy this overlay on top (shadows the Codex-default reviewer in affected skills):

```bash
cp -a skills/skills-codex-claude-review/* <your-project-path>/.claude/skills/
```

3. Register the `claude-review` MCP bridge in Opencode — see `mcp-servers/claude-review/README.md` for the full config block. Key points:
   - The server **must** be registered under the name `claude-review` (skills reference `mcp__claude-review__*`)
   - Set `CLAUDE_REVIEW_MODEL=claude-sonnet-4-6` in the environment block to pin the reviewer model

## Why this exists

The upstream `skills/skills-codex/` path already supports Codex-native execution with a second Codex reviewer via `spawn_agent`.

This package adds a different split:

- executor: any non-Claude client (Codex CLI, Opencode, Cursor, Trae, etc.)
- reviewer: Claude Code CLI (Sonnet 4.6 or whichever model `CLAUDE_REVIEW_MODEL` specifies)
- transport: `claude-review` MCP

For long paper and review prompts, the reviewer path uses:

- `review_start`
- `review_reply_start`
- `review_status`

This avoids the observed Codex-hosted timeout issue when Claude is invoked synchronously through a local bridge.
