# `skills-codex`

Codex-native mirror of the base ARIS skill set.

## Scope

This package keeps the main `skills/` workflows available for OpenAI Codex CLI.

Recent core workflow follow-up skills mirrored here include:

- `training-check`
- `result-to-claim`
- `ablation-planner`

These skills cover the experiment follow-up chain:

1. monitor training quality early
2. judge what claims the results actually support
3. design reviewer-facing ablations before paper writing

## Install

> 💡 **Recommended: use the dedicated Codex installer.** It installs or updates the Codex-native package in `~/.codex/skills/`, supports optional reviewer overlays, and can sync MCP bridge files without auto-registering them.

```bash
# 1. Clone ARIS once to a stable location
git clone https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep.git ~/aris_repo

# 2. Install or update the base Codex-native skill set
bash ~/aris_repo/tools/install_codex_skills.sh

# 3. Optional: switch the reviewer backend overlay
bash ~/aris_repo/tools/install_codex_skills.sh --reviewer claude --print-mcp-hints
bash ~/aris_repo/tools/install_codex_skills.sh --reviewer gemini --print-mcp-hints

# 4. Preview changes only
bash ~/aris_repo/tools/install_codex_skills.sh --dry-run
```

<details>
<summary><b>Alternative: legacy manual install (`~/.codex/skills/`)</b></summary>

```bash
cp -a ~/aris_repo/skills/skills-codex/* ~/.codex/skills/
```

For reviewer overlays, copy the overlay package after the base install:

```bash
cp -a ~/aris_repo/skills/skills-codex-claude-review/* ~/.codex/skills/
# or
cp -a ~/aris_repo/skills/skills-codex-gemini-review/* ~/.codex/skills/
```

Use the manual path only if you intentionally do not want the managed installer.

</details>

<details>
<summary><b>Why not use `install_aris.sh` for Codex?</b></summary>

The current `tools/install_aris.sh` is for the Claude-style `.claude/skills/` install path. For Codex, use `tools/install_codex_skills.sh` instead.

Optional companion dependency for the `deepxiv` skill:

```bash
pip install deepxiv-sdk
```

If you also use reviewer overlay packages, install this base package first, then apply the overlay on top.
