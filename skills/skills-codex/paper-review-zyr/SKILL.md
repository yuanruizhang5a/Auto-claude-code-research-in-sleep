---
name: paper-review-zyr
description: Draft a LaTeX response or cover letter from one or more manuscript reviews, preserve reviewer wording, write grounded point-by-point replies in the author's style, revise the paper with reversible ORI/MO annotations, process embedded $SPEC instructions, resume across calls, and compile both documents. Use when responding to peer review, preparing a revision letter, applying reviewer-requested manuscript changes, or revising an existing response letter.
---

# Paper Review ZYR for Codex

Turn reviewer reports into a traceable response letter and a reversibly annotated manuscript revision. Treat the directory containing this `SKILL.md` as `SKILL_ROOT`; resolve every bundled reference, script, `template.tex`, and `letterbib.sty` relative to it.

## Load the contracts

Before creating or changing any project artifact:

1. Read `references/state-schema.md` completely for state, stage, fingerprint, and validation rules.
2. Read `references/response-rules.md` completely for lossless review import, issue classification, response grounding, manuscript annotations, and `$SPEC` semantics.
3. Read `references/platform-compatibility.md` only when installing, testing discovery, or adapting delegation to the current host.

Use `scripts/validate_review_state.py` after initialization and every file-based handoff. Keep the core workflow independent of optional files under `agents/`.

## Parse the invocation

Treat the text following an explicit skill invocation, or the current user request when invoked implicitly, as arguments. Accept `--key value`, `--key: value`, and `— key: value` forms.

```text
$paper-review-zyr path/to/paper.tex \
  --review path/to/review.tex \
  --reviews path/to/reviewer1.txt,path/to/reviewer2.pdf \
  --style-materials path/to/materials \
  [--phase normal|revise] [--instructions "..."] \
  [--include "Section A,Section B"] [--exclude "Appendix"] \
  [--overwrite] [--no-compile] [--resume true|false] [--restart]
```

| Parameter | Required | Default | Contract |
|---|---:|---|---|
| positional `PAPER` | yes | none | Source manuscript `.tex` file. By default preserve it and apply changes to a new `_rN` sibling. |
| `review` | no | `review.tex` in the working directory | Source response-letter path. By default preserve an existing file and write the response to a new `_rN` sibling; if absent, create that revision sibling from `SKILL_ROOT/template.tex`. |
| `reviews` | normal phase | none | Comma-separated raw reports in `.txt`, `.md`, `.tex`, or text-readable `.pdf` form. Reuse a compatible imported ledger on resume. |
| `style-materials` | conditional | none | Writing samples in a folder or `.pdf`, `.md`, `.txt`, or `.tex`; require unless a fingerprint-matching style cache exists. |
| `phase` | no | `normal` | Use `normal` for review import/response/revision; use `revise` for explicit user-directed changes only. |
| `instructions` | revise phase | none | Required non-empty instructions for the revise phase. |
| `include` / `exclude` | no | full paper | Case-insensitive logical section/subsection selectors for manuscript and `$SPEC` edits. Exclusion wins. |
| `overwrite` | no | false | Exact flag spelling. When present, modify the resolved `PAPER` and `REVIEW` paths in place instead of creating `_rN` files. Do not silently treat `--overwrite` as this destructive flag. |
| `no-compile` | no | false | Skip all compilation and leave compilation status `skipped`/`null`. |
| `resume` | no | true | Continue the first incomplete compatible stage. |
| `restart` | no | false | Snapshot prior state into `./com/history/` and initialize a new run. Never destroy prior state. |
| `effort` | no | `balanced` | Accept `lite`, `balanced`, `max`, or `beast`; vary explanatory depth only, never issue coverage, grounding, or safety. |
| `human-checkpoint` | no | false | When true, add a checkpoint before applying manuscript edits. Complex issues always require a checkpoint. |
| `AUTO_PROCEED` | no | true | Continue through safe stages; never use it to approve a complex issue or unsupported claim. |

### Resolve copy-on-write outputs

Resolve four absolute paths before any mutation: `SOURCE_PAPER`, `OUTPUT_PAPER`, `SOURCE_REVIEW`, and `OUTPUT_REVIEW`. Use the bundled deterministic resolver and save its result in `orchestrator.json.parameters`:

```text
python3 SKILL_ROOT/scripts/resolve_revision_paths.py \
  --paper SOURCE_PAPER --review SOURCE_REVIEW [--overwrite]
```

Apply these rules:

1. With `--overwrite`, set each output equal to its source. If `SOURCE_REVIEW` is absent, create it from the template; otherwise edit both existing source files in place.
2. Without `--overwrite`, preserve both source paths. For each output independently, remove any terminal sequence of `_r<number>` suffixes from the source stem, then choose the first unused positive revision number. Start at `1` for an unversioned source; when the source ends in `_rK`, start at `K+1`. Thus `paper.tex` becomes the first unused `paper_rN.tex`, `paper_r3.tex` advances to at least `paper_r4.tex`, and repeated names such as `paper_r2_r3.tex` do not become `paper_r2_r3_r1.tex`.
3. Resolve outputs once for a new run. On compatible resume, reuse the saved output paths rather than choosing a new number. On `--restart`, resolve a fresh pair after snapshotting prior state.
4. Copy an existing source to its output immediately before the first modification of that artifact. Never select or overwrite a pre-existing revision candidate on a new run; a compatible resume may continue modifying its saved output. If the source review does not exist, create `OUTPUT_REVIEW` from `SKILL_ROOT/template.tex`. Do not create `OUTPUT_PAPER` when no manuscript change is ultimately applied.
5. Read evidence from the sources, but perform all response rendering, manuscript edits, compilation repairs, and output compilation against the resolved outputs. Report both source and output paths and the write mode.

Apply precedence in this order:

1. In-scope `$SPEC` instructions.
2. Explicit instructions in the current call.
3. Saved user decisions for reviewer issues.
4. Grounded reviewer-response requirements.
5. `writingStyle.json` guidance.
6. General polishing preferences.

Report material conflicts instead of silently choosing. Report every unmatched `include` or `exclude` selector.

## Enforce invariants

- Never fabricate a result, experiment, citation, explanation, manuscript location, or commitment.
- Preserve raw reviewer wording and order. Escape or wrap it for LaTeX without paraphrasing, merging, correcting, or omitting it.
- Put every drafted answer inside the template-defined `\ranswer{...}` command.
- Require a user decision for any new scientific claim, new experiment, unresolved factual judgment, substantial derivation, new citation, policy choice, or ambiguous manuscript target.
- Never apply an unapproved complex change.
- Never remove original manuscript content from the source representation. Use the exact annotation forms in `references/response-rules.md`.
- Preserve the source `PAPER` and `REVIEW` files unless the exact `--overwrite` flag is present. In default mode, never direct any mutation or compile repair to a source path.
- Make every stage idempotent. Re-running a completed compatible stage must not duplicate an issue, answer, edit, annotation, template section, or compilation record.
- Keep behavior aligned with the canonical skill. Limit Codex-specific changes to invocation, collaboration, and presentation metadata.
- Keep all coordination in workspace-local `./com`; do not place state in the installed skill directory.
- Preserve invalid or incompatible state and stop with an actionable diagnostic; never guess or replace it wholesale.
- Pass raw artifact paths and role contracts to delegated workers. Do not bias them with the orchestrator's subjective summary.

## Coordinate state

Use these files:

```text
./com/
|-- orchestrator.json
|-- writingStyle.json
|-- reviewIssues.json
|-- reviewDraft.json
|-- paperEdits.json
`-- compileResults.json
```

Retain the inherited top-level keys and value types in `orchestrator.json`: `timestamps`, `current_stage`, `stage_notes`, `parameters`, and `stage_gate`. Store all review-specific extensions under `paper_review_zyr`. Merge updates field-by-field; do not discard unknown fields written by another compatible skill.

Write JSON atomically through a sibling temporary file followed by a same-filesystem rename. After each write, run:

```text
python3 SKILL_ROOT/scripts/validate_review_state.py --com-dir ./com
```

Use `--final` only for the Stage 8 coverage audit. If validation fails, leave the failing artifact intact, record the diagnostic, set the run to `error` or a pending checkpoint as appropriate, and stop.

## Delegate bounded roles with Codex

When active instructions permit collaboration, dispatch each role as a bounded Codex task with `spawn_agent`. Give the worker only its role contract, absolute raw-artifact paths, required reference paths, and allowed outputs; do not pass the orchestrator's subjective conclusions. Use `followup_task` to resume an idle worker and `send_message` only to communicate with a worker that is already running. Wait for the worker to finish, validate its file handoff, and advance the stage before dispatching a role that writes any of the same state files. The primary agent remains responsible for path resolution, stage gates, validation, user checkpoints, and the final audit.

If collaboration is unavailable, denied, or constrained by slot limits, execute the same role sequentially in the primary agent and record `execution_mode` as `sequential` or `mixed`. Preserve every input/output restriction either way. Never parallelize workers that can write the same coordination artifact.

### Writing-style analyst

- Inputs: style-material paths and fingerprints from `orchestrator.json`.
- Read: only the supplied materials and required state contract.
- Write: `./com/writingStyle.json` and the corresponding style-stage fields in `orchestrator.json`.
- Analyze at least sentence length, paragraph structure, formality, voice, hedging, transitions, terminology, first-person use, equations, citations, figure references, recurring phrases, and tone.
- Reuse the file only when material paths and content fingerprints match.
- Validate the handoff with `--require writingStyle`.
- Advance only to `template_prep` in normal phase or `user_revision` in revise phase.

### Review importer and template analyst

- Inputs: source/output review-letter paths, raw review paths, `SKILL_ROOT/template.tex`, and `orchestrator.json`.
- Read: each source directly in its original order.
- Write: `reviewIssues.json`, `reviewDraft.json`, and import/template fields in `orchestrator.json`.
- Do not draft substantive answers or edit the manuscript.
- Preserve ambiguous segmentation as one lossless issue and mark it for confirmation.
- Validate the handoff with `--require reviewIssues,reviewDraft`.
- Advance only after source-to-ledger coverage succeeds.

### Concern triage and response writer

- Inputs: source paper for evidence, output paper when it exists, every raw issue, `writingStyle.json`, and the response rules.
- Read: concerns and paper evidence directly, not an orchestrator summary.
- Write: response/classification fields in `reviewIssues.json`, proposed rendering in `reviewDraft.json`, and stage fields in `orchestrator.json`.
- Draft only safely grounded simple responses. Mark complex items `needs_user` with concise grounded options.
- Do not edit either paper path or invent citations, results, or future work.
- Validate the handoff with `--require writingStyle,reviewIssues,reviewDraft`.

### Manuscript revision worker

- Inputs: source/output paper paths, approved/automatic issue records, saved user decisions, section scope, and `$SPEC` rules.
- Write: linked records in `paperEdits.json`, approved annotated changes only in `OUTPUT_PAPER`, accurate response-location updates in `OUTPUT_REVIEW`, and stage fields.
- In default mode, copy `SOURCE_PAPER` to the unused `OUTPUT_PAPER` immediately before the first approved manuscript mutation. In overwrite mode, verify the two paths are equal.
- Apply only exact targets with evidence and record original/revised text before mutation.
- Do not polish unrelated prose.
- Validate the handoff with `--require reviewIssues,paperEdits`.

### LaTeX compiler and debugger

- Inputs: the resolved output paper and response document roots plus `compileResults.json`.
- Write: compilation records, minimal compile-only repairs, and compilation fields in `orchestrator.json`.
- Never change substantive content or resolve a scientific/user decision.
- Compile the two roots independently and retain one document's success when the other fails.
- Validate the handoff with `--require compileResults`.

## Run the normal phase

### Stage 0: initialize or resume

1. Resolve absolute source paths; verify `SOURCE_PAPER` is the manuscript's main `.tex` file. Resolve `SOURCE_REVIEW` from an explicit path or `./review.tex`.
2. Run the bundled revision-path resolver. Save `source_tex`, `output_tex`, `review_tex`, `output_review_tex`, and `overwrite` in parameters. On compatible resume, retain the saved output paths.
3. On a new default-mode run, verify both output candidates are unused and distinct from their sources; on compatible resume, verify they match the saved targets. In overwrite mode, verify each source/output pair is identical. If the source review is absent, mark `OUTPUT_REVIEW` for Stage 2 creation from `SKILL_ROOT/template.tex`.
4. Create `./com` and missing JSON skeletons without replacing valid existing files.
5. Fingerprint the source paper, source review when present, resolved output paths, `overwrite`, raw reviews, style materials, template, phase, and behavior-affecting parameters.
6. Compare the invocation fingerprint with saved state. Resume at the first incomplete compatible stage. If incompatible, explain the mismatch and require corrected arguments or `--restart`.
7. On `--restart`, copy the prior coordination files to `./com/history/<run_id>/`, then initialize a new run while preserving the snapshot.
8. Scan `SOURCE_PAPER` for annotation macros and `SOURCE_REVIEW` or the template for `\ranswer`.
9. Validate state and narrate the selected run ID, phase, effort, execution mode, and next stage.

Invalidate only dependent stages:

- Changed style materials: invalidate style learning and generated response prose.
- Changed raw reviews: invalidate import, triage, linked edits, `$SPEC` reconciliation, compilation, and audit.
- Changed source paper content or write mode: invalidate target resolution, edits, `$SPEC`, compilation, and audit.
- Changed review template: invalidate template analysis, rendered draft, compilation, and audit.
- Changed revise instructions: invalidate user revision, compilation, and audit only.

### Stage 1: learn writing style

Run or reuse the writing-style contract. For text-readable PDFs, use an available extractor; if none can produce reliable text, request a text-readable alternative. Validate `writingStyle.json` before advancing.

### Stage 2: prepare the response letter

Prepare only `OUTPUT_REVIEW`. In default mode, if `SOURCE_REVIEW` exists, copy it to the unused `OUTPUT_REVIEW` before changing it. If `SOURCE_REVIEW` does not exist, create `OUTPUT_REVIEW` using `SKILL_ROOT/template.tex` as the structural and formatting basis. In overwrite mode, use the existing source/output path directly, or create that path from the template when absent. Preserve the template's document class, preamble/macros, cover-letter layout, reviewer headings, and `\ranswer{...}` structure; remove or replace example-only content. Never modify the bundled template or a default-mode source review.

If the created letter uses `letterbib.sty` and no compatible copy is available to its LaTeX root, copy `SKILL_ROOT/letterbib.sty` beside the new letter without overwriting an existing file. Record this support-file action.

For a letter copied from an existing user-selected source, preserve its structure in the output. Identify insertion points for the introduction, editor text, reviewer sections, concerns, and answers. If `\ranswer` is missing or unusable, stop and ask permission before adding a compatible definition.

### Stage 3: import reviews losslessly

Import every source and concern in source order. Keep both verbatim text and LaTeX-safe rendering in the ledger. Preserve reviewer labels and boundaries when explicit. When boundaries are ambiguous, retain the complete ambiguous span as one issue with `segmentation_status: needs_user`; do not silently split or rewrite it.

Generate stable issue IDs from reviewer identity, source fingerprint, original order, and a short content hash. Verify that every non-empty source span maps to exactly one ledger entry before advancing.

### Stage 4: triage and draft responses

Classify each issue with the taxonomy in `references/response-rules.md`. Automatically answer only language/grammar, clarity/expression, notation/naming consistency, or small technical corrections when the current paper safely supports both the reply and proposed change.

Render drafted concerns and answers only into `OUTPUT_REVIEW`; never mutate `SOURCE_REVIEW` in default mode.

For every other issue, set `status: needs_user`; include the verbatim concern, why a decision is required, evidence consulted, and viable actions. Group all pending questions into one checkpoint by reviewer. Persist state before asking and end the invocation at that checkpoint. A later call resumes after saving the user's decisions. A deferred item remains visible and causes no manuscript change.

If `human-checkpoint` is true, also pause once with all otherwise safe proposed edits before Stage 5.

### Stage 5: revise the manuscript

For every answered and approved issue:

1. Resolve an exact in-scope target from `SOURCE_PAPER`. Before the first applied edit in default mode, copy it to the still-unused `OUTPUT_PAPER`; then resolve and verify the corresponding output target.
2. Save the original and proposed text plus rationale in `paperEdits.json`.
3. Apply the required ORI/MO annotation form.
4. Verify the annotation exists at the recorded location.
5. Update `OUTPUT_REVIEW` to describe only the change actually applied and its real output location.
6. Mark the issue `revised` only after all linked edits verify.

Leave ambiguous or out-of-scope targets pending and ask the user. Avoid unrelated polishing.

### Stage 6: process `$SPEC`

If `OUTPUT_PAPER` does not yet exist and an in-scope `$SPEC` will change the manuscript, copy `SOURCE_PAPER` to the still-unused output first. Parse and modify only `OUTPUT_PAPER`; use `SOURCE_PAPER` for the unchanged baseline. Parse all in-scope `!++ ... ++!` blocks according to `references/response-rules.md`, including nesting, ignored/commented regions, type combinations, standalone grammar-and-mechanics `@grammar`, conservative `@check`, `@keep`, `@mini`, unresolved `\VE...\EVE`, and source-preserving ORI/MO output.

Apply `$SPEC` before lower-priority reviewer changes at the same location. Detect and report conflicts with reviewer requests or saved user decisions. Do not silently choose across a material conflict.

### Stage 7: compile and repair

Skip the entire stage when `no-compile` is true. Otherwise discover each existing resolved output document root independently and attempt, at most five times per document. If `OUTPUT_PAPER` was intentionally not created because the manuscript was unaffected, record its compilation status as `skipped` rather than compiling or repairing `SOURCE_PAPER`:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error <root.tex>
```

If `latexmk` is unavailable, use the document's existing build command or a suitable `pdflatex`/bibliography multi-pass fallback. Read logs before every repair. Make only minimal compilation fixes and record each attempt, warning, error, fix, PDF path, and final status in `compileResults.json`.

### Stage 8: coverage audit and report

Run the validator with `--final`, then independently verify:

- every review source and concern is represented exactly once;
- every automatic response has one `\ranswer{...}` and a linked manuscript disposition;
- every complex issue has a saved decision or explicit pending/deferred status;
- every applied edit has valid ORI/MO annotations and an existing source location;
- every processed or skipped `$SPEC` has a recorded disposition;
- both affected document roots have compilation records or an intentional skip.

Do not declare completion when the final validator fails. Report absolute source and output paths, whether `_rN` copy-on-write or `--overwrite` mode was used, per-document compilation results, counts by issue status, modified locations, unresolved/deferred concerns, `$SPEC` dispositions, preamble/support-file changes, unmatched selectors, and the next resumable stage.

## Run the revise phase

Require non-empty `instructions`, then run:

```text
initialize/resume -> style learning -> user revision -> compile -> coverage audit
```

Apply instructions only to named output artifacts and the resolved section scope. Before the first requested mutation, create the corresponding `_rN` working copy unless `--overwrite` is present. Do not re-import or re-answer reviews unless the instruction explicitly requests it. Preserve ORI/MO annotations for manuscript changes and update linked issue/edit records when prior responses or revisions change. Run the same compilation and final-audit rules.

## Handle failures safely

- Missing or ambiguous input: stop before mutation and request the exact path or choice.
- Legacy state without `output_tex`, `output_review_tex`, or `overwrite`: preserve it unchanged and require `--restart`; never infer that an older in-place run authorized overwrite mode.
- Revision path collision or copy failure: leave both sources unchanged, record the attempted output, resolve no replacement silently, and stop with an actionable diagnostic.
- Invalid JSON: preserve it, emit a diagnostic path, and stop without guessing state.
- Unreadable PDF or unsupported source: identify the source and request readable text.
- Unsupported claim or citation: use `needs_user` or `\VE <reason> \EVE`; never improvise support.
- Sub-agent failure: record the error and resume the same stage later without repeating completed work.
- Partial compile failure: retain successful outputs and report each root separately.
- User interruption: atomically persist the current stage, completed artifacts, and next action before returning.
