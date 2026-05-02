# Reviewer Routing

## Default (NEVER changes without explicit user request)

All review calls use **Codex MCP** (`mcp__codex__codex`) with `reasoning_effort: xhigh`.

This is the default for ALL skills. No parameter, no config, no effort level changes this.

## Optional: GPT-5.4 Pro via Oracle

When the user explicitly passes `— reviewer: oracle-pro`, route the review through Oracle MCP instead of Codex MCP.

### Routing Logic (add to any reviewer-invoking skill)

```
Parse $ARGUMENTS for `— reviewer:` directive.

If not specified OR `— reviewer: codex`:
    → Use mcp__codex__codex with reasoning_effort: xhigh
    → This is the DEFAULT. No change from current behavior.

If `— reviewer: oracle-pro`:
    → Check if mcp__oracle__consult tool is available
    → If available:
        Use mcp__oracle__consult with:
          model: "gpt-5.4-pro"
          prompt: [same prompt you would send to Codex]
          files: [file paths for reviewer to read directly]
        Note: Oracle may use API mode (fast, needs OPENAI_API_KEY)
              or browser mode (slow ~1-2 min, needs Chrome + ChatGPT login)
    → If NOT available:
        Print: "⚠️ Oracle MCP not installed. Falling back to Codex xhigh."
        Use mcp__codex__codex as normal.
```

### Invariants

- `— reviewer: oracle-pro` ONLY takes effect when explicitly passed
- Reviewer independence protocol still applies (pass file paths, not summaries)
- `effort` and `difficulty` are orthogonal — they don't change reviewer backend
- `beast` mode may RECOMMEND oracle-pro but never requires it
- Browser mode: acceptable for one-shot reviews; NOT recommended inside multi-round loops (too slow/brittle)

### Oracle MCP Call Format

```
mcp__oracle__consult:
  prompt: |
    [role + task + output schema]
    Read all listed files directly.
  model: "gpt-5.4-pro"
  files:
    - /absolute/path/to/file1
    - /absolute/path/to/file2
```

### Skills That Support `— reviewer: oracle-pro`

| Skill | Use case for Pro |
|-------|-----------------|
| `/research-review` | Deeper critique on paper drafts |
| `/auto-review-loop` | Final stress test (last round only in browser mode) |
| `/experiment-audit` | Line-by-line eval code audit |
| `/proof-checker` | Deep mathematical reasoning |
| `/rebuttal` | Stress test before submission |
| `/idea-creator` | Idea evaluation depth |
| `/research-lit` | Literature analysis depth |

### Installation

```bash
# Install Oracle CLI + MCP
npm install -g @steipete/oracle

# Add Oracle MCP to Claude Code
claude mcp add oracle -s user -- oracle-mcp

# Restart Claude Code session to load

# API mode (fast, recommended):
export OPENAI_API_KEY="your-key"

# Browser mode (no API key, slower):
# Just log in to ChatGPT in Chrome
```

### NOT installed = ZERO impact

If Oracle is not installed, `— reviewer: oracle-pro` gracefully falls back to Codex. No error, no breakage, just a warning.

---

## Optional: Claude Sonnet 4.6 via Local `claude-review` MCP

When the user explicitly passes `— reviewer: claude`, route the review through the local `claude-review` MCP bridge instead of Codex MCP. The bridge calls `claude -p --model $CLAUDE_REVIEW_MODEL` via subprocess (default model set by the `CLAUDE_REVIEW_MODEL` env var in the MCP server config; recommended: `claude-sonnet-4-6`).

### Routing Logic (async pattern — avoids 120 s MCP timeout)

```
If `— reviewer: claude`:
    → Call mcp__claude-review__review_start(prompt=...) → returns {jobId}
    → Save jobId
    → Poll mcp__claude-review__review_status(jobId, waitSeconds=30) until done=true
    → Extract response and threadId from the completed status payload

    Round 2+ (multi-round loops):
    → Call mcp__claude-review__review_reply_start(threadId=..., prompt=...) → returns {jobId}
    → Poll review_status until done=true
```

### Invariants

- `— reviewer: claude` ONLY takes effect when explicitly passed (or read from `reviewer.txt`)
- Reviewer independence protocol still applies (pass file paths, not summaries)
- Requires: Claude Code CLI installed locally + `claude-review` MCP registered in executor client
- If `claude-review` MCP is not available, print a warning and fall back to Codex xhigh
- Model is pinned by `CLAUDE_REVIEW_MODEL` env var in the MCP server config — not at call time

### Skills That Support `— reviewer: claude`

| Skill | Where branching happens |
|-------|------------------------|
| `/paper-writing` | Phase 0 (writes `paper/.aris/reviewer.txt`); sub-skills read it |
| `/auto-review-loop` | Step 0 init (writes `review-stage/reviewer.txt`); all review phases |
| `/auto-paper-improvement-loop` | Steps 2 and 5 (reads `paper/.aris/reviewer.txt`) |
| `/paper-plan` | Step 6 cross-review (reads `paper/.aris/reviewer.txt`) |
| `/paper-write` | Step 6 cross-review (reads `paper/.aris/reviewer.txt`) |
| `/paper-figure` | Step 7 quality review (reads `paper/.aris/reviewer.txt`) |

### Installation

```bash
# Register claude-review MCP in Claude Code
claude mcp add claude-review -s user -- python3 /path/to/mcp-servers/claude-review/server.py

# Set reviewer model in MCP environment (or export in shell)
export CLAUDE_REVIEW_MODEL=claude-sonnet-4-6

# For Opencode: add to ~/.opencode/config.json (see mcp-servers/claude-review/README.md)
```

### NOT installed = ZERO impact

If `claude-review` MCP is not installed, `— reviewer: claude` falls back to Codex. No error, no breakage, just a warning.
