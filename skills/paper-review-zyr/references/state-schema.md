# State and Resume Contract

Use this contract for every file under workspace-local `./com`. Preserve unknown fields so `paper-refine-zyr` or a later schema version can extend the same state safely.

## Contents

- [General rules](#general-rules)
- [orchestrator.json](#orchestratorjson)
- [writingStyle.json](#writingstylejson)
- [reviewIssues.json](#reviewissuesjson)
- [reviewDraft.json](#reviewdraftjson)
- [paperEdits.json](#papereditsjson)
- [compileResults.json](#compileresultsjson)
- [Stage transitions](#stage-transitions)
- [Fingerprint and invalidation rules](#fingerprint-and-invalidation-rules)
- [Validation commands](#validation-commands)

## General rules

1. Store JSON as UTF-8 with an object at the root.
2. Write atomically: serialize to a sibling temporary file, parse and validate it, then rename it over the destination.
3. Merge known fields rather than replacing the root object. Never discard an unknown key.
4. Use absolute paths for user/project artifacts and communication files. Use paths relative to the skill root only when naming bundled read-only resources.
5. Use ISO-8601 timestamps with timezone information.
6. Use SHA-256 for content fingerprints. For directories, hash a sorted list of relative paths plus each file's content hash.
7. Keep stable IDs unchanged across compatible resumes. Derive issue/edit/spec IDs deterministically and reject duplicates.
8. Represent unavailable values with JSON `null`; do not use strings such as `"none"` or `"unknown"` when the schema permits `null`.
9. Preserve invalid JSON unchanged. Write a separate diagnostic and stop.
10. Snapshot all coordination files to `./com/history/<run_id>/` before `--restart`; never delete earlier snapshots.

## orchestrator.json

Retain these backward-compatible top-level keys and types:

```json
{
  "timestamps": {},
  "current_stage": "init",
  "stage_notes": "",
  "parameters": {},
  "stage_gate": {},
  "paper_review_zyr": {}
}
```

Require the following parameter fields for an initialized run:

```json
{
  "source_tex": "/absolute/path/paper.tex",
  "review_tex": "/absolute/path/review.tex",
  "raw_reviews": ["/absolute/path/reviewer1.txt"],
  "style_materials": "/absolute/path/style-materials",
  "style_materials_for_writing_style": null,
  "writing_style_file": "/absolute/workspace/com/writingStyle.json",
  "phase": "normal",
  "instructions": null,
  "include": [],
  "exclude": [],
  "no_compile": false,
  "resume": true,
  "restart": false,
  "effort": "balanced",
  "human_checkpoint": false,
  "AUTO_PROCEED": true,
  "compile_success": null
}
```

Keep `compile_success` as `null`, `true`, or `false` for compatibility. Store independent paper/review details in `compileResults.json` and the namespaced compilation object.

Require Boolean stage gates for every stage relevant to the current phase. Additional gates are allowed.

Use this review-specific namespace:

```json
{
  "paper_review_zyr": {
    "schema_version": 1,
    "run_id": "prz-20260810T120000Z-a1b2c3d4",
    "invocation_fingerprint": "sha256 hex",
    "phase": "normal",
    "execution_mode": "delegated",
    "ordered_stages": [
      "init",
      "style_learning",
      "template_prep",
      "review_import",
      "response_drafting",
      "manuscript_revision",
      "spec_processing",
      "compiling",
      "auditing",
      "done"
    ],
    "current_stage": "style_learning",
    "completed_at": {},
    "input_fingerprints": {
      "paper": "sha256 hex",
      "review": null,
      "raw_reviews": "sha256 hex",
      "style_materials": "sha256 hex",
      "template": "sha256 hex",
      "parameters": "sha256 hex"
    },
    "files": {
      "orchestrator": "/absolute/workspace/com/orchestrator.json",
      "writing_style": "/absolute/workspace/com/writingStyle.json",
      "review_issues": "/absolute/workspace/com/reviewIssues.json",
      "review_draft": "/absolute/workspace/com/reviewDraft.json",
      "paper_edits": "/absolute/workspace/com/paperEdits.json",
      "compile_results": "/absolute/workspace/com/compileResults.json"
    },
    "pending_user_decisions": [],
    "compilation": {
      "paper": "pending",
      "review": "pending"
    },
    "warnings": [],
    "unmatched_selectors": [],
    "unresolved_items": [],
    "history": []
  }
}
```

Allow `execution_mode` values `delegated`, `sequential`, or `mixed`. Keep top-level `current_stage` equal to `paper_review_zyr.current_stage` for stages used by this skill.

Use these stage values:

- Shared: `init`, `style_learning`, `compiling`, `auditing`, `user_checkpoint`, `done`, `error`.
- Normal phase: `template_prep`, `review_import`, `response_drafting`, `manuscript_revision`, `spec_processing`.
- Revise phase: `user_revision`.

## writingStyle.json

Use the inherited entry map:

```json
{
  "sentence_length": {
    "value": "Mostly medium-length sentences with occasional short emphasis.",
    "description": "Keep most sentences compact and reserve short sentences for conclusions."
  }
}
```

Require a non-empty object after style learning. Require every entry to contain non-empty string `value` and `description`. Include at least:

- `sentence_length`
- `paragraph_structure`
- `formality_level`
- `voice`
- `hedging_style`
- `transition_words`
- `jargon_tolerance`
- `first_person_use`
- `equation_explanation_style`
- `citation_placement`
- `figure_reference_style`
- `recurring_phrases`
- `tone`

## reviewIssues.json

Use the lossless source ledger as the coverage source of truth:

```json
{
  "schema_version": 1,
  "sources": [
    {
      "source_id": "source-1-a1b2c3d4",
      "path": "/absolute/path/reviewer1.txt",
      "sha256": "sha256 hex",
      "order": 1,
      "reviewer_id": "reviewer-1",
      "issue_ids": ["R1-001-a1b2c3d4"]
    }
  ],
  "issues": [
    {
      "issue_id": "R1-001-a1b2c3d4",
      "reviewer_id": "reviewer-1",
      "source_id": "source-1-a1b2c3d4",
      "original_order": 1,
      "verbatim_text": "Original reviewer wording.",
      "source_location": "reviewer1.txt:paragraph 1",
      "latex_text": "Original reviewer wording.",
      "category": "clarity_expression",
      "complexity": "simple",
      "segmentation_status": "confirmed",
      "evidence_locations": ["paper.tex:Introduction"],
      "proposed_answer": "\\ranswer{Thank you. We clarified ...}",
      "user_decision": null,
      "linked_edit_ids": ["E-R1-001-a1b2c3d4-01"],
      "status": "revised",
      "disposition": "answered_and_revised"
    }
  ]
}
```

Allow categories:

- `language_grammar`
- `clarity_expression`
- `notation_naming`
- `small_technical`
- `complex_scientific`
- `experiment_request`
- `citation_factual_verification`
- `editorial_policy`
- `other`

Allow complexity values `simple`, `complex`, or `undetermined`; segmentation values `confirmed` or `needs_user`; and statuses `untriaged`, `simple`, `needs_user`, `approved`, `answered`, `revised`, `deferred`, or `blocked`.

Keep a deferred or blocked issue visible. Never erase it to make coverage pass. Use a user-decision object containing `decision`, `rationale`, and `timestamp` whenever the user approves, rejects, or defers a complex issue.

## reviewDraft.json

Store the response-letter rendering plan separately from the issue ledger:

```json
{
  "schema_version": 1,
  "review_path": "/absolute/path/review.tex",
  "template_path": "/absolute/skill/path/template.tex",
  "template_sha256": "sha256 hex",
  "created_from_default_template": true,
  "support_files": ["/absolute/path/letterbib.sty"],
  "status": "rendered",
  "introduction": "Grounded cover-letter introduction.",
  "sections": [
    {
      "reviewer_id": "reviewer-1",
      "issue_ids": ["R1-001-a1b2c3d4"]
    }
  ],
  "rendered_issue_ids": ["R1-001-a1b2c3d4"]
}
```

Allow status values `pending`, `prepared`, `rendered`, or `blocked`. Ensure every imported issue appears exactly once in `sections`; add it to `rendered_issue_ids` only after its verbatim concern is present in the response letter.

## paperEdits.json

Record edits before applying them:

```json
{
  "schema_version": 1,
  "edits": [
    {
      "edit_id": "E-R1-001-a1b2c3d4-01",
      "linked_issue_ids": ["R1-001-a1b2c3d4"],
      "linked_spec_ids": [],
      "file": "/absolute/path/paper.tex",
      "structural_location": "Introduction, paragraph 2",
      "original_text": "Old text.",
      "revised_text": "New text.",
      "rendered_annotation": "\\ORI Old text. \\EORI\\MO New text. \\EMO",
      "rationale": "Clarify the definition requested by Reviewer 1.",
      "evidence_locations": ["paper.tex:Definition 1"],
      "annotation_status": "verified",
      "application_status": "applied",
      "compilation_status": "success"
    }
  ],
  "specs": [
    {
      "spec_id": "S-001-a1b2c3d4",
      "file": "/absolute/path/paper.tex",
      "structural_location": "Section 3",
      "raw_text": "!++ @check ... ++!",
      "types": ["check"],
      "scope_status": "in_scope",
      "disposition": "revised",
      "linked_edit_ids": ["E-S-001-a1b2c3d4-01"]
    }
  ]
}
```

Allow annotation statuses `pending`, `applied`, `verified`, or `not_applicable`; application statuses `pending`, `applied`, `skipped`, or `blocked`; compilation statuses `pending`, `success`, `failed`, or `skipped`; scope statuses `in_scope`, `out_of_scope`, or `conflict`; and spec dispositions `pending`, `unchanged`, `revised`, `deferred`, `blocked`, or `out_of_scope`.

## compileResults.json

Track the two roots independently:

```json
{
  "schema_version": 1,
  "documents": [
    {
      "kind": "paper",
      "source_tex": "/absolute/path/paper.tex",
      "document_root": "/absolute/path/paper.tex",
      "pdf_path": "/absolute/path/paper.pdf",
      "attempts": 1,
      "status": "success",
      "warnings": [],
      "errors": [],
      "fixes": []
    },
    {
      "kind": "review",
      "source_tex": "/absolute/path/review.tex",
      "document_root": "/absolute/path/review.tex",
      "pdf_path": "/absolute/path/review.pdf",
      "attempts": 1,
      "status": "success",
      "warnings": [],
      "errors": [],
      "fixes": []
    }
  ]
}
```

Allow kinds `paper` and `review`, and statuses `pending`, `skipped`, `success`, or `failed`. Cap attempts at five. Require one record per affected kind at final audit, including intentional skips.

## Stage transitions

Advance only after validating the current stage's output:

```text
normal:
init -> style_learning -> template_prep -> review_import
     -> response_drafting -> [user_checkpoint]
     -> manuscript_revision -> spec_processing
     -> [compiling] -> auditing -> done

revise:
init -> style_learning -> user_revision
     -> [compiling] -> auditing -> done
```

Use `error` for an unrecoverable current-call failure. Use `user_checkpoint` for required input that has already been represented in state. Resume from the saved next incomplete stage after the user responds.

## Fingerprint and invalidation rules

Build the invocation fingerprint from normalized absolute paths, content fingerprints, phase, scope, compilation flag, and behavior-affecting parameters. Do not include timestamps.

Invalidate only dependent outputs:

| Changed input | Invalidate |
|---|---|
| style materials | style analysis, generated response prose, later stages |
| raw reviews | import ledger, responses, linked edits, spec reconciliation, compilation, audit |
| paper | target resolution, edits, spec processing, compilation, audit |
| review template/letter structure | template analysis, rendered response draft, review compilation, audit |
| revise instructions | user revision, compilation, audit |
| include/exclude scope | target resolution, edits, spec processing, compilation, audit |

If the saved run is incompatible and `--restart` is absent, stop and explain which fingerprint components differ. Never silently repurpose old state.

## Validation commands

Validate an in-progress state:

```text
python3 <skill-root>/scripts/validate_review_state.py --com-dir ./com
```

Require named handoff files when needed:

```text
python3 <skill-root>/scripts/validate_review_state.py \
  --com-dir ./com --require writingStyle,reviewIssues
```

Run strict coverage checks before completion:

```text
python3 <skill-root>/scripts/validate_review_state.py --com-dir ./com --final
```

Treat exit code `0` as valid and exit code `1` as a validation failure. Use `--json` for machine-readable diagnostics.
