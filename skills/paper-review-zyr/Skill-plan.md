# Implementation Plan: `paper-review-zyr`

## 1. Goal

Create a resumable skill that turns one or more manuscript reviews into a LaTeX response/cover letter, drafts grounded responses in the user's writing style, applies the corresponding revisions to the manuscript, processes embedded `$SPEC` instructions, and compiles the affected LaTeX documents. Package one canonical implementation that can be installed and used on Claude Code, OpenCode, and Codex without maintaining divergent platform-specific skill bodies.

The implementation must follow `Skill-draft.md` and inherit the applicable behavior of `../paper-refine-zyr/SKILL.md`, especially:

- writing-style learning through a sub-agent;
- workspace-local JSON coordination in `./com`;
- persistent, multi-call execution state;
- `$SPEC` parsing and priority rules;
- annotated, reversible manuscript edits;
- a separate compilation/debugging sub-agent;
- parameter parsing, section scoping, progress updates, and final reporting.

## 2. Clarifications to Encode

Resolve the draft's underspecified points in `SKILL.md` as follows:

1. Resolve `$REVIEW` to an explicit `--review` path when supplied; otherwise default to `review.tex` in the working directory. If the resolved file does not exist, create it using the colocated `template.tex` as the default structural and formatting template. Unless the user explicitly requests another template or format, every review file created by the skill must follow `template.tex`, preserving its document class, preamble/macros, cover-letter layout, reviewer sections, and `\ranswer{...}` response structure while replacing its example content. Stop and ask the user only when `template.tex` is missing or unreadable.
2. Treat `$PAPER` as the manuscript's main `.tex` file. Require it before any manuscript edit.
3. Treat raw reviewer material separately from `$REVIEW`. Accept one or more review sources through a `reviews` parameter; allow `.txt`, `.md`, `.tex`, and text-readable `.pdf` inputs.
4. Preserve reviewer wording semantically. Only perform LaTeX escaping and structural wrapping needed to place it in `$REVIEW`; do not paraphrase, summarize, merge, or silently correct it.
5. Classify a concern as complex whenever a safe response or manuscript change requires a new scientific claim, new experiment, unresolved factual judgment, substantial derivation, new citation, or a user policy decision. Queue it for a user checkpoint rather than guessing.
6. Compile both affected document roots when `$PAPER` and `$REVIEW` are separate compilable documents. Record their results independently.
7. Interpret "share the same JSON format" as backward-compatible extension: retain the `paper-refine-zyr` top-level keys and value types, add review-specific state under a namespaced object, and never discard fields written by either skill.
8. Keep the skill portable across Claude Code, OpenCode, and Codex. Use only the common `SKILL.md` frontmatter contract (`name` and `description`), express workflow instructions without hard-coded platform tool names, and treat platform-specific metadata as optional additive files that other platforms may ignore.

## 3. Planned Skill Layout

```text
paper-review-zyr/
|-- SKILL.md
|-- template.tex
|-- agents/
|   `-- openai.yaml
|-- references/
|   |-- state-schema.md
|   |-- response-rules.md
|   `-- platform-compatibility.md
`-- scripts/
    `-- validate_review_state.py
```

Keep `SKILL.md` focused on routing, invariants, workflow stages, portable sub-agent contracts, and failure behavior. Put the complete JSON schemas and detailed concern taxonomy in `references/`. Put verified installation locations, invocation forms, capability mappings, and platform smoke-test instructions in `references/platform-compatibility.md`. Add the validation script only if schema checks cannot be expressed reliably with existing repository utilities.

Do not package `Skill-draft.md` or `Skill-plan.md` as runtime resources; they are development artifacts.

## 4. Invocation and Parameters

Design an invocation similar to:

```text
/paper-review-zyr path/to/paper.tex \
  --review path/to/review.tex \
  --reviews path/to/reviewer1.txt,path/to/reviewer2.pdf \
  --style-materials path/to/materials \
  [--phase normal|revise] \
  [--instructions "..."] \
  [--include "Section A,Section B"] \
  [--exclude "Appendix"] \
  [--no-compile]
```

Planned parameters:

| Parameter | Required | Default | Purpose |
|---|---:|---|---|
| positional `$PAPER` | yes | none | Main manuscript `.tex` file to revise |
| `review` (`$REVIEW`) | no | existing `review.tex`, otherwise create `review.tex` from `template.tex` | LaTeX response/cover-letter file to fill; newly created files follow `template.tex` by default |
| `reviews` | normal phase | none | One or more raw reviewer reports |
| `style-materials` | yes unless reusable state matches | none | Writing samples used to create `writingStyle.json` |
| `phase` | no | `normal` | Select the normal or revise workflow |
| `instructions` | revise phase | none | User-directed edits performed by Func 8 |
| `include` / `exclude` | no | full paper | Restrict content edits by logical section title |
| `no-compile` | no | false | Skip compilation while preserving a resumable state |
| `resume` | no | true | Continue compatible incomplete state from `./com` |
| `restart` | no | false | Start a new run while preserving prior state as history |

Reuse `paper-refine-zyr` parameter names and semantics wherever they apply. Define deterministic precedence for conflicting flags and report unmatched scope selectors.

The slash-command example is illustrative. Accept the same arguments when the host exposes skills through a natural-language skill invocation or another native command form.

### 4.1 Cross-Platform Compatibility

Implement and validate one skill directory for Claude Code, OpenCode, and Codex:

1. Keep `SKILL.md`, `template.tex`, references, scripts, state files, parameters, and behavioral semantics identical across platforms.
2. Make the directory directly copyable or linkable into each platform's documented user-level or project-level skill location. Record the verified locations and invocation syntax in `references/platform-compatibility.md`; do not guess undocumented paths.
3. Keep `agents/openai.yaml` as optional Codex-facing UI metadata. Do not require it, or any Claude Code/OpenCode-specific metadata, to execute the core skill.
4. Describe sub-agent work as role, input, output, and completion contracts. At runtime, map those contracts to Claude Code's, OpenCode's, or Codex's native delegation mechanism instead of embedding platform-specific tool identifiers in the canonical workflow.
5. When a host cannot delegate a required role, run that role sequentially in the orchestrator while preserving the same file-based handoff, validation, stage-gate, and reviewer-independence rules. Record the fallback in `orchestrator.json`.
6. Resolve the skill root from the loaded `SKILL.md` location so bundled references, scripts, and `template.tex` work regardless of the platform's installation directory. Never depend on repository-specific or user-specific absolute paths.
7. Use portable Python and shell commands for deterministic helpers. Detect optional executables such as `latexmk` before use and retain the documented fallback behavior.

## 5. Shared State and Communication Files

Use one workspace-local communication directory:

```text
./com/
|-- orchestrator.json
|-- writingStyle.json
|-- reviewIssues.json
|-- reviewDraft.json
|-- paperEdits.json
`-- compileResults.json
```

### 5.1 `orchestrator.json`

Preserve the compatible top-level shape used by `paper-refine-zyr`:

- `timestamps`
- `current_stage`
- `stage_notes`
- `parameters`
- `stage_gate`

Add a `paper_review_zyr` namespace containing:

- `schema_version`;
- `run_id` and invocation fingerprint;
- `phase` (`normal` or `revise`);
- ordered stage list and current review-specific stage;
- stage completion timestamps;
- raw review source fingerprints;
- paths to all communication files;
- pending user decisions;
- per-document compilation status;
- warnings, unmatched selectors, and unresolved items.

On every call, merge state rather than replacing the entire JSON document. Resume only when `$PAPER`, `$REVIEW`, phase, review inputs, and relevant parameters are compatible with the saved run. Otherwise explain the mismatch and require `--restart` or corrected arguments.

### 5.2 `reviewIssues.json`

Maintain a lossless reviewer-by-reviewer issue ledger. Each issue should contain:

- stable `issue_id`, reviewer identifier, and original order;
- verbatim source text and source location;
- LaTeX-safe rendering of the same text;
- category and complexity classification;
- evidence paths/locations consulted in the paper;
- proposed `\ranswer{...}` content;
- user decision when required;
- linked manuscript edit IDs;
- status such as `untriaged`, `simple`, `needs_user`, `approved`, `answered`, `revised`, `deferred`, or `blocked`.

This ledger is the coverage source of truth. Every imported reviewer concern must appear exactly once and must reach a terminal or explicitly pending status.

### 5.3 `paperEdits.json`

For every proposed or applied manuscript change, record:

- stable edit ID and linked issue/spec IDs;
- file and structural location;
- original text;
- revised text;
- rationale and grounding evidence;
- annotation status;
- application and compilation status.

Sub-agents write structured proposals; the main agent verifies and applies/coordinates them.

## 6. Global Invariants

Encode these rules near the top of `SKILL.md`:

1. Never fabricate results, experiments, citations, explanations, or commitments.
2. Never change the substance of reviewer text while converting it to LaTeX.
3. Answer every drafted response with the template-defined `\ranswer{...}` command.
4. Never remove original manuscript content during review-driven revision.
5. Represent a replacement as `\ORI <original> \EORI\MO <revision> \EMO`.
6. Represent a pure insertion as `\MO <new text> \EMO`; preserve deletions visibly inside `\ORI ... \EORI` and explain the disposition in the response.
7. Reuse compatible macro definitions; otherwise add the required `\ORI`, `\EORI`, `\MO`, and `\EMO` definitions minimally and report the preamble change.
8. Give `$SPEC` instructions highest priority, followed by explicit current-call user instructions, approved reviewer responses, style guidance, and general polishing rules.
9. Do not apply an unapproved complex change.
10. Make stages idempotent: resuming a completed stage must not duplicate reviews, responses, annotations, or edits.
11. Keep sub-agent communication file-based. Pass raw artifact paths and task contracts, not the main agent's subjective summaries.

## 7. Sub-Agent Roles

The main agent is the orchestrator and remains responsible for validation, stage transitions, user interaction, conflict resolution, and final reporting. Define the following bounded sub-agents:

1. **Writing-style analyst**
   - Inherit the full `paper-refine-zyr` style-learning contract.
   - Read the supplied materials and write `./com/writingStyle.json`.
   - Reuse cached output only when material paths/fingerprints match.

2. **Review importer and template analyst**
   - Inspect `$REVIEW` to identify its reviewer/question/answer structure and `\ranswer` definition.
   - Convert raw reviews to LaTeX-safe form without changing content.
   - Populate `reviewIssues.json` and `reviewDraft.json`.

3. **Concern triage and response writer**
   - Read each raw concern directly, the paper, and `writingStyle.json`.
   - Classify concern type/complexity and draft only grounded simple responses.
   - Mark complex concerns `needs_user` with a concise decision question and viable options; do not invent a response.

4. **Manuscript revision agent**
   - Apply only approved/automatic grounded edits linked to response IDs.
   - Preserve original text with `\ORI...\EORI` and tag revisions with `\MO...\EMO`.
   - Process in-scope `$SPEC` blocks using the inherited semantics.

5. **LaTeX compiler/debugger**
   - Compile `$PAPER` and `$REVIEW` document roots independently.
   - Make only minimal compilation fixes, never substantive content changes.
   - Retry up to five times and write structured results.

For every role, specify exact input files, allowed outputs, required JSON updates, and the next permitted stage. Require atomic writes or validate JSON after every handoff.

## 8. Normal-Phase Workflow

Implement the draft's order as explicit resumable stages.

### Stage 0: Initialize and Resume

1. Parse and validate parameters and paths.
2. Resolve `$REVIEW` using the default rule.
3. Create/merge `./com/orchestrator.json` and communication files.
4. Fingerprint relevant inputs and decide whether the saved state is reusable.
5. Scan the paper preamble for annotation macros and the review template for `\ranswer`.
6. Set the next incomplete stage without rerunning completed compatible stages.

### Stage 1: Learn Writing Style (Func 1)

Run or reuse the style-learning sub-agent from `paper-refine-zyr`. Validate the output schema before advancing.

### Stage 2: Prepare the Response Template (Func 2)

If `$REVIEW` does not exist, create it from the colocated `template.tex` according to the default-format rule. Inspect `$REVIEW`, preserve its document structure/macros, and identify safe insertion points for the cover-letter introduction, reviewer sections, concern text, and answers. If `\ranswer` is absent or unusable, stop and ask the user whether the skill may add a compatible definition.

### Stage 3: Import Reviews (Func 3)

Import every review in original order. Preserve reviewer labels and item boundaries when present. If boundaries are ambiguous, retain the complete text and mark the segmentation for user confirmation rather than altering content.

Verify lossless coverage between source reviews and the issue ledger before advancing.

### Stage 4: Triage and Draft Responses (Funcs 4 and 4.5)

Classify issues into at least:

- language/grammar;
- clarity/expression;
- notation/naming consistency;
- small technical correction grounded in the current paper;
- complex scientific/technical request;
- experiment request;
- citation/factual verification request;
- editorial or policy decision.

Automatically draft responses for the first four categories only when the answer and change are safely supported by the paper. Wrap each response in `\ranswer{...}` and match `writingStyle.json`.

Collect all `needs_user` items into one concise checkpoint grouped by reviewer. For each item, show the verbatim concern, why it needs a decision, and the available grounded actions. Persist the user's decision before continuing. If the user defers an issue, retain it visibly as unresolved and make no corresponding manuscript change.

### Stage 5: Revise the Manuscript (Func 5)

For each answered issue:

1. Resolve the exact manuscript target and confirm it is in scope.
2. Create a linked edit record.
3. Preserve the original content with `\ORI...\EORI`.
4. Add revised/new content with `\MO...\EMO`.
5. Update the response so it accurately describes the applied change and location.
6. Mark the issue `revised` only after verifying the edit exists in the paper.

Avoid unrelated polishing during this stage.

### Stage 6: Process `$SPEC` (Func 6)

Inherit the `$SPEC` parser and type semantics from `paper-refine-zyr`, including nested tags, ignored comment regions, scope handling, conservative `@check`, unresolved `\VE...\EVE` placeholders, and priority rules. Adapt output annotations so changed source is preserved with both ORI and MO wrappers.

Detect conflicts between a `$SPEC`, reviewer request, and user decision. Do not silently choose; use the stated priority order and report any material conflict.

### Stage 7: Compile and Repair (Func 7)

Unless `--no-compile` is set:

1. Discover the document root for `$PAPER` and `$REVIEW`.
2. Compile with `latexmk`; use the established `pdflatex`/bibliography fallback if unavailable.
3. Diagnose logs and make minimal compile-only fixes.
4. Retry up to five times per document.
5. Record PDF paths, attempts, warnings, and final status in `compileResults.json`.

Do not treat unresolved scientific/user decisions as compilation errors.

### Stage 8: Coverage Audit and Final Report

Before declaring completion, verify:

- every reviewer/source and concern was imported;
- every simple concern has one `\ranswer` and linked manuscript disposition;
- every complex concern has a recorded user decision or explicit pending/deferred state;
- every applied paper edit has correct ORI/MO annotations;
- all processed `$SPEC` blocks have a recorded disposition;
- compilation results reflect every affected document.

Report output paths, per-document compilation status, issue counts by status, modified locations, unresolved/user-deferred concerns, `$SPEC` results, preamble changes, and the next resumable stage if incomplete.

## 9. Revise-Phase Workflow

Implement the draft's alternate path as:

```text
initialize/resume -> style learning -> user instructions (Func 8) -> compile -> report
```

In revise phase:

- require non-empty `--instructions`;
- do not re-import or re-answer reviews unless the instruction explicitly asks to update an existing response;
- apply instructions only to the named artifacts and section scope;
- keep all ORI/MO preservation rules for manuscript changes;
- update linked issue/edit records when prior responses or revisions change;
- run the same compilation and final-audit logic.

## 10. Multi-Call Behavior

Make every invocation:

1. initialize and validate state;
2. resume at the first incomplete compatible stage;
3. run until completion, a required user checkpoint, or an unrecoverable error;
4. persist state before returning.

Use stable IDs and content fingerprints to prevent duplicate import or response generation. When inputs change between calls, invalidate only dependent stages. For example:

- changed style materials invalidate style learning and generated response prose, but not raw review import;
- changed raw reviews invalidate import, triage, linked edits, and later stages;
- changed paper content invalidates target resolution, paper edits, `$SPEC` processing, and compilation;
- changed `--instructions` in revise phase invalidates Func 8 and compilation only.

## 11. Safety and Failure Handling

- Missing/ambiguous required files: stop before mutation and request the exact path.
- Invalid JSON: preserve the file, write a diagnostic, and do not guess state.
- Missing LaTeX macros: request permission before changing the response template when its contract is unclear; add manuscript annotation macros only when compatible.
- Unsupported review format or unreadable PDF: report the source and request a text-readable version.
- Ambiguous paper edit target: keep the response in draft/pending state and ask the user.
- Unsupported technical claim: mark `needs_user` or insert the inherited verification placeholder; never fabricate support.
- Partial compilation failure: retain successful outputs and report each failed root separately.
- Sub-agent failure: record the error and resume that stage on the next call without repeating completed work.

## 12. Implementation Sequence

1. Write the final `SKILL.md` frontmatter, trigger description, parameters, invariants, and phase router.
2. Define backward-compatible schemas in `references/state-schema.md`.
3. Define concern classification, response grounding, LaTeX conversion, and preservation rules in `references/response-rules.md`.
4. Implement stage initialization, fingerprints, gates, invalidation, and resume behavior.
5. Add the style, import, response, revision, and compile sub-agent contracts.
6. Add normal- and revise-phase workflows plus user checkpoint behavior.
7. Add optional deterministic state validation tooling.
8. Write and verify the three-platform installation, invocation, capability-mapping, and fallback contract in `references/platform-compatibility.md`.
9. Generate optional `agents/openai.yaml` from the completed skill metadata without making core execution depend on it.
10. Validate the same skill directory and forward-test representative scenarios on Claude Code, OpenCode, and Codex, using an explicitly documented substitute only when a client is unavailable in the test environment.

## 13. Validation and Tests

### Static validation

- Run the skill creator's `quick_validate.py` on the completed skill.
- Validate YAML frontmatter, lowercase directory/name consistency, reference links, and `agents/openai.yaml` when that optional metadata file is present.
- Validate every sample communication JSON against the documented schema.
- Reject hard-coded repository paths, home-directory paths, and platform-specific tool identifiers in the canonical workflow.
- Verify that optional platform metadata can be absent or ignored without changing core behavior.

### Platform compatibility smoke tests

For Claude Code, OpenCode, and Codex, verify that the same skill directory can:

1. be discovered from a documented user-level or project-level skill installation;
2. trigger from the platform's native invocation form and parse the same parameters;
3. resolve `template.tex`, references, and scripts relative to the skill root;
4. create or resume the same `./com` state and preserve schema compatibility;
5. delegate each role through the platform's native mechanism or execute the documented sequential fallback;
6. create a default review file from `template.tex` and reach the expected user checkpoint or final report.

### Workflow fixtures

Create temporary fixtures covering:

1. one reviewer with grammar and notation issues;
2. multiple reviewers with preserved ordering and duplicate-looking but distinct concerns;
3. a complex experiment request that pauses for user input;
4. a review template with an existing `\ranswer` macro;
5. missing `review.tex` creation from `template.tex` and missing `\ranswer` behavior;
6. nested/commented `$SPEC` tags;
7. normal-to-resume execution across multiple calls;
8. revise phase with scoped user instructions;
9. style-cache reuse and invalidation;
10. separate paper/review compilation success and partial failure.

### Required assertions

- Raw reviewer text survives import without semantic change.
- Every concern has exactly one stable ledger entry.
- Every automatic response is enclosed in `\ranswer{...}`.
- Every review file created without a user-selected alternative template follows the structure and formatting of `template.tex`.
- No complex item is answered or applied without a saved decision.
- Replacements contain the original and modified spans in ORI/MO form.
- A resumed stage produces no duplicated response or edit.
- `$SPEC` precedence and scope match `paper-refine-zyr`.
- Compilation fixes do not introduce substantive content changes.
- `orchestrator.json` remains readable by preserving the inherited top-level format.

## 14. Definition of Done

The skill is ready when:

- both phases execute according to the draft;
- all required sub-agent handoffs use validated JSON artifacts;
- multi-call resume is deterministic and idempotent;
- simple issues are answered and applied with full traceability;
- complex issues reliably pause for the user;
- reviewer text and original manuscript text are preserved as required;
- `$SPEC` behavior is inherited and adapted correctly;
- paper and response documents compile or return actionable, persisted failures;
- the final coverage audit prevents silent omission of any reviewer concern;
- the same canonical skill directory installs and runs on Claude Code, OpenCode, and Codex without behavior forks;
- platform-specific metadata remains optional and core execution contains no hard-coded platform tool names or installation paths;
- static validation, platform smoke tests, and all representative workflow fixtures pass.
