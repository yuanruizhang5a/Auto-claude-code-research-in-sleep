---
name: paper-review-zyr
description: Draft a LaTeX response or cover letter from one or more manuscript reviews, preserve reviewer wording, write grounded point-by-point replies in the author's style, revise the paper with reversible ORI/MO annotations, process embedded $SPEC instructions, resume across calls, and compile both documents. Use when responding to peer review, preparing a revision letter, applying reviewer-requested manuscript changes, or revising an existing response letter.
---

# Paper Review ZYR

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
/paper-review-zyr path/to/paper.tex \
  --review path/to/review.tex \
  --reviews path/to/reviewer1.txt,path/to/reviewer2.pdf \
  --style-materials path/to/materials \
  [--phase normal|revise] [--instructions "..."] \
  [--include "Section A,Section B"] [--exclude "Appendix"] \
  [--no-compile] [--resume true|false] [--restart]
```

| Parameter | Required | Default | Contract |
|---|---:|---|---|
| positional `PAPER` | yes | none | Main manuscript `.tex` file to revise. Stop before mutation if missing or ambiguous. |
| `review` | no | `review.tex` in the working directory | Response-letter file. If absent, create it from `SKILL_ROOT/template.tex`. |
| `reviews` | normal phase | none | Comma-separated raw reports in `.txt`, `.md`, `.tex`, or text-readable `.pdf` form. Reuse a compatible imported ledger on resume. |
| `style-materials` | conditional | none | Writing samples in a folder or `.pdf`, `.md`, `.txt`, or `.tex`; require unless a fingerprint-matching style cache exists. |
| `phase` | no | `normal` | Use `normal` for review import/response/revision; use `revise` for explicit user-directed changes only. |
| `instructions` | revise phase | none | Required non-empty instructions for the revise phase. |
| `include` / `exclude` | no | full paper | Case-insensitive logical section/subsection selectors for manuscript and `$SPEC` edits. Exclusion wins. |
| `no-compile` | no | false | Skip all compilation and leave compilation status `skipped`/`null`. |
| `resume` | no | true | Continue the first incomplete compatible stage. |
| `restart` | no | false | Snapshot prior state into `./com/history/` and initialize a new run. Never destroy prior state. |
| `effort` | no | `balanced` | Accept `lite`, `balanced`, `max`, or `beast`; vary explanatory depth only, never issue coverage, grounding, or safety. |
| `human-checkpoint` | no | false | When true, add a checkpoint before applying manuscript edits. Complex issues always require a checkpoint. |
| `AUTO_PROCEED` | no | true | Continue through safe stages; never use it to approve a complex issue or unsupported claim. |

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
- Make every stage idempotent. Re-running a completed compatible stage must not duplicate an issue, answer, edit, annotation, template section, or compilation record.
- Keep the canonical skill portable. Describe delegation by role/input/output contract, not by a product-specific tool name.
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

## Delegate bounded roles

Use the host's native delegation mechanism when available. If delegation is unavailable or denied, perform the same role sequentially in the orchestrator and record `execution_mode` as `sequential` or `mixed`. Preserve every input/output restriction either way.

### Writing-style analyst

- Inputs: style-material paths and fingerprints from `orchestrator.json`.
- Read: only the supplied materials and required state contract.
- Write: `./com/writingStyle.json` and the corresponding style-stage fields in `orchestrator.json`.
- Analyze at least sentence length, paragraph structure, formality, voice, hedging, transitions, terminology, first-person use, equations, citations, figure references, recurring phrases, and tone.
- Reuse the file only when material paths and content fingerprints match.
- Validate the handoff with `--require writingStyle`.
- Advance only to `template_prep` in normal phase or `user_revision` in revise phase.

### Review importer and template analyst

- Inputs: resolved review-letter path, raw review paths, `SKILL_ROOT/template.tex`, and `orchestrator.json`.
- Read: each source directly in its original order.
- Write: `reviewIssues.json`, `reviewDraft.json`, and import/template fields in `orchestrator.json`.
- Do not draft substantive answers or edit the manuscript.
- Preserve ambiguous segmentation as one lossless issue and mark it for confirmation.
- Validate the handoff with `--require reviewIssues,reviewDraft`.
- Advance only after source-to-ledger coverage succeeds.

### Concern triage and response writer

- Inputs: `PAPER`, every raw issue, `writingStyle.json`, and the response rules.
- Read: concerns and paper evidence directly, not an orchestrator summary.
- Write: response/classification fields in `reviewIssues.json`, proposed rendering in `reviewDraft.json`, and stage fields in `orchestrator.json`.
- Draft only safely grounded simple responses. Mark complex items `needs_user` with concise grounded options.
- Do not edit `PAPER` or invent citations, results, or future work.
- Validate the handoff with `--require writingStyle,reviewIssues,reviewDraft`.

### Manuscript revision worker

- Inputs: `PAPER`, approved/automatic issue records, saved user decisions, section scope, and `$SPEC` rules.
- Write: linked records in `paperEdits.json`, approved annotated changes in `PAPER`, accurate response-location updates, and stage fields.
- Apply only exact targets with evidence and record original/revised text before mutation.
- Do not polish unrelated prose.
- Validate the handoff with `--require reviewIssues,paperEdits`.

### LaTeX compiler and debugger

- Inputs: the paper and response document roots plus `compileResults.json`.
- Write: compilation records, minimal compile-only repairs, and compilation fields in `orchestrator.json`.
- Never change substantive content or resolve a scientific/user decision.
- Compile the two roots independently and retain one document's success when the other fails.
- Validate the handoff with `--require compileResults`.

## Run the normal phase

### Stage 0: initialize or resume

1. Resolve absolute input paths; verify `PAPER` is the manuscript's main `.tex` file.
2. Resolve the review-letter path. Use an explicit path when supplied; otherwise use `./review.tex`.
3. If the review letter is absent, mark it for Stage 2 creation from `SKILL_ROOT/template.tex`. Stop only if the bundled template is missing or unreadable.
4. Create `./com` and missing JSON skeletons without replacing valid existing files.
5. Fingerprint `PAPER`, the resolved review letter when present, raw reviews, style materials, template, phase, and behavior-affecting parameters.
6. Compare the invocation fingerprint with saved state. Resume at the first incomplete compatible stage. If incompatible, explain the mismatch and require corrected arguments or `--restart`.
7. On `--restart`, copy the prior coordination files to `./com/history/<run_id>/`, then initialize a new run while preserving the snapshot.
8. Scan `PAPER` for annotation macros and the review letter/template for `\ranswer`.
9. Validate state and narrate the selected run ID, phase, effort, execution mode, and next stage.

Invalidate only dependent stages:

- Changed style materials: invalidate style learning and generated response prose.
- Changed raw reviews: invalidate import, triage, linked edits, `$SPEC` reconciliation, compilation, and audit.
- Changed paper content: invalidate target resolution, edits, `$SPEC`, compilation, and audit.
- Changed review template: invalidate template analysis, rendered draft, compilation, and audit.
- Changed revise instructions: invalidate user revision, compilation, and audit only.

### Stage 1: learn writing style

Run or reuse the writing-style contract. For text-readable PDFs, use an available extractor; if none can produce reliable text, request a text-readable alternative. Validate `writingStyle.json` before advancing.

### Stage 2: prepare the response letter

If the resolved review file does not exist, create it using `SKILL_ROOT/template.tex` as the structural and formatting basis. Preserve the template's document class, preamble/macros, cover-letter layout, reviewer headings, and `\ranswer{...}` structure; remove or replace example-only content. Never modify the bundled template.

If the created letter uses `letterbib.sty` and no compatible copy is available to its LaTeX root, copy `SKILL_ROOT/letterbib.sty` beside the new letter without overwriting an existing file. Record this support-file action.

For an existing user-selected letter, preserve its structure. Identify insertion points for the introduction, editor text, reviewer sections, concerns, and answers. If `\ranswer` is missing or unusable, stop and ask permission before adding a compatible definition.

### Stage 3: import reviews losslessly

Import every source and concern in source order. Keep both verbatim text and LaTeX-safe rendering in the ledger. Preserve reviewer labels and boundaries when explicit. When boundaries are ambiguous, retain the complete ambiguous span as one issue with `segmentation_status: needs_user`; do not silently split or rewrite it.

Generate stable issue IDs from reviewer identity, source fingerprint, original order, and a short content hash. Verify that every non-empty source span maps to exactly one ledger entry before advancing.

### Stage 4: triage and draft responses

Classify each issue with the taxonomy in `references/response-rules.md`. Automatically answer only language/grammar, clarity/expression, notation/naming consistency, or small technical corrections when the current paper safely supports both the reply and proposed change.

For every other issue, set `status: needs_user`; include the verbatim concern, why a decision is required, evidence consulted, and viable actions. Group all pending questions into one checkpoint by reviewer. Persist state before asking and end the invocation at that checkpoint. A later call resumes after saving the user's decisions. A deferred item remains visible and causes no manuscript change.

If `human-checkpoint` is true, also pause once with all otherwise safe proposed edits before Stage 5.

### Stage 5: revise the manuscript

For every answered and approved issue:

1. Resolve an exact in-scope target.
2. Save the original and proposed text plus rationale in `paperEdits.json`.
3. Apply the required ORI/MO annotation form.
4. Verify the annotation exists at the recorded location.
5. Update the response to describe only the change actually applied and its real location.
6. Mark the issue `revised` only after all linked edits verify.

Leave ambiguous or out-of-scope targets pending and ask the user. Avoid unrelated polishing.

### Stage 6: process `$SPEC`

Parse all in-scope `!++ ... ++!` blocks according to `references/response-rules.md`, including nesting, ignored/commented regions, type combinations, conservative `@check`, `@keep`, `@mini`, unresolved `\VE...\EVE`, and source-preserving ORI/MO output.

Apply `$SPEC` before lower-priority reviewer changes at the same location. Detect and report conflicts with reviewer requests or saved user decisions. Do not silently choose across a material conflict.

### Stage 7: compile and repair

Skip the entire stage when `no-compile` is true. Otherwise discover each document root independently and attempt, at most five times per document:

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

Do not declare completion when the final validator fails. Report absolute output paths, per-document compilation results, counts by issue status, modified locations, unresolved/deferred concerns, `$SPEC` dispositions, preamble/support-file changes, unmatched selectors, and the next resumable stage.

## Run the revise phase

Require non-empty `instructions`, then run:

```text
initialize/resume -> style learning -> user revision -> compile -> coverage audit
```

Apply instructions only to named artifacts and the resolved section scope. Do not re-import or re-answer reviews unless the instruction explicitly requests it. Preserve ORI/MO annotations for manuscript changes and update linked issue/edit records when prior responses or revisions change. Run the same compilation and final-audit rules.

## Handle failures safely

- Missing or ambiguous input: stop before mutation and request the exact path or choice.
- Invalid JSON: preserve it, emit a diagnostic path, and stop without guessing state.
- Unreadable PDF or unsupported source: identify the source and request readable text.
- Unsupported claim or citation: use `needs_user` or `\VE <reason> \EVE`; never improvise support.
- Sub-agent failure: record the error and resume the same stage later without repeating completed work.
- Partial compile failure: retain successful outputs and report each root separately.
- User interruption: atomically persist the current stage, completed artifacts, and next action before returning.
