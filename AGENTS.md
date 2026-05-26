# Repository Guidelines

## Project Structure & Module Organization

ARIS is organized around Markdown skills plus lightweight Python tooling. Core skills live in `skills/`, with shared policy docs in `skills/shared-references/`. Codex-specific variants live under `skills/skills-codex*/`. Python utilities and automation scripts are in `tools/`, including `tools/experiment_queue/`. MCP bridge servers live in `mcp-servers/<server-name>/`. Tests are centralized in `tests/`. Reusable templates belong in `templates/`, and longer-form user or operator documentation belongs in `docs/`.

## Build, Test, and Development Commands

There is no single build step for the repo; most work is editing Markdown skills or Python scripts directly.

- `python -m unittest discover -s tests`: run the main unit-test suite.
- `pytest tests`: run the full test suite, including the `pytest`-based cases.
- `bash tools/smart_update.sh`: preview safe skill updates from upstream.
- `bash tools/smart_update.sh --apply`: apply safe updates after review.
- `cp -r skills/<skill-name> ~/.claude/skills/`: install one skill locally for manual validation.

Install server-specific Python dependencies from each local manifest, for example `pip install -r mcp-servers/llm-chat/requirements.txt`.

## Coding Style & Naming Conventions

Python uses 4-space indentation, `snake_case` for functions and variables, and concise module/function docstrings. Prefer small, dependency-light scripts that can run standalone with `python3`. Keep Markdown skills declarative: one `SKILL.md` per skill directory, with clear frontmatter and imperative instructions. Name new tests `test_<feature>.py`. Use ASCII unless the surrounding file already depends on Unicode.

## Testing Guidelines

Add or update tests in `tests/` whenever changing Python behavior in `tools/` or `mcp-servers/`. Favor isolated unit tests with `unittest.mock`; reserve live API coverage for opt-in paths guarded by environment variables, as in `tests/test_minimax_integration.py`. Run `python -m unittest discover -s tests` before opening a PR, and run `pytest tests` when touching `pytest`-based helpers.

## Commit & Pull Request Guidelines

Prefer the conventional style already used in shared history: `feat(scope): concise summary`, `docs(scope): concise summary`, or a clear imperative sentence. Avoid personal snapshot-style messages such as date-only checkpoints in reviewable branches. Keep PRs focused, describe behavior changes, list test coverage, and link related issues. Include screenshots only when changing visual assets or docs that depend on rendered output.

## Agent-Specific Notes

For AI-agent-facing routing and workflow contracts, read `AGENT_GUIDE.md` and the relevant `skills/<name>/SKILL.md` before changing a workflow. Treat those files as the behavioral source of truth.
