# Review, Response, Revision, and `$SPEC` Rules

Apply these rules to review import, response drafting, manuscript revision, and embedded specifications.

## Contents

- [Lossless review import](#lossless-review-import)
- [Default response-letter template](#default-response-letter-template)
- [Issue segmentation and stable IDs](#issue-segmentation-and-stable-ids)
- [Classification and complexity](#classification-and-complexity)
- [Grounded response drafting](#grounded-response-drafting)
- [User checkpoints](#user-checkpoints)
- [Manuscript annotations](#manuscript-annotations)
- [Section scope](#section-scope)
- [`$SPEC` parsing](#spec-parsing)
- [`$SPEC` type semantics](#spec-type-semantics)
- [`$SPEC` combinations and output](#spec-combinations-and-output)
- [Citation and factual requests](#citation-and-factual-requests)
- [Coverage audit](#coverage-audit)

## Lossless review import

Keep two forms of every concern:

1. `verbatim_text`: exact decoded source text, including wording, capitalization, punctuation, and substantive line breaks.
2. `latex_text`: a rendering safe to insert into the response letter without changing meaning.

Never paraphrase, summarize, merge, silently correct, translate, or omit reviewer wording. Preserve reviewer/source order. Keep editor text separate from reviewer text when the source distinguishes them.

For plain-text sources, escape LaTeX-reserved characters contextually:

| Source character | Safe prose rendering |
|---|---|
| `\` | `\textbackslash{}` |
| `{` / `}` | `\{` / `\}` |
| `$` | `\$` |
| `&` | `\&` |
| `%` | `\%` |
| `#` | `\#` |
| `_` | `\_` |
| `^` | `\^{}` |
| `~` | `\~{}` |

Do not blindly double-escape a `.tex` source. Preserve verified LaTeX commands and environments while escaping prose characters that would otherwise break compilation. Retain the exact source in `verbatim_text` so rendering is reversible and auditable.

For a PDF, extract text without OCR rewriting when a text layer exists. If extraction is incomplete, scrambled, or image-only, stop and request a text-readable file rather than reconstructing reviewer wording from guesses.

## Default response-letter template

When creating a response letter without a user-selected alternative template:

- Use bundled `template.tex` as the structural and formatting basis.
- Preserve its document class, packages, macros, signature/letter organization, editor/reviewer heading pattern, and `\ranswer{...}` command.
- Replace example addressee, introduction, editor content, reviewer content, answers, bibliography details, and contact details only when grounded in user/project inputs.
- Remove example-only markers and ellipses from the created review file.
- Do not mutate the bundled template.
- Copy bundled `letterbib.sty` beside the created response letter only when its LaTeX root cannot otherwise resolve that package; never overwrite an existing file.

For an existing response file, treat it as user-selected. Preserve its structure and macros. Ask permission before adding or redefining `\ranswer` when no compatible definition exists.

Insert every answer using exactly one outer `\ranswer{...}`. Do not wrap reviewer text in `\ranswer`.

## Issue segmentation and stable IDs

Prefer explicit source boundaries in this order:

1. numbered questions or comments;
2. headings such as Major/Minor Comment;
3. clearly separated bullet items;
4. paragraph boundaries that each express one concern.

Do not infer fine-grained boundaries when the source is ambiguous. Keep the whole ambiguous span as one issue, set `segmentation_status` to `needs_user`, and preserve it verbatim.

Generate IDs deterministically:

```text
R<reviewer-number>-<three-digit-original-order>-<first-8-content-hash>
```

Include the source fingerprint and reviewer identity in the hash input. Distinct concerns with similar text remain distinct because their source/order differs. Re-importing an unchanged source must reproduce the same IDs.

## Classification and complexity

Use these categories:

| Category | Automatic handling ceiling |
|---|---|
| `language_grammar` | Correct when the target and correction are unambiguous. |
| `clarity_expression` | Clarify only from content already present in the paper. |
| `notation_naming` | Make a local or consistently traceable naming correction. |
| `small_technical` | Correct only when current paper evidence directly establishes the fix. |
| `complex_scientific` | Require user decision. |
| `experiment_request` | Require user decision; never claim an unrun experiment. |
| `citation_factual_verification` | Require verification or user decision before adding support. |
| `editorial_policy` | Require user decision unless a supplied venue/editor rule answers it exactly. |
| `other` | Treat as complex until safely classified. |

Set `complexity: complex` whenever a safe answer or change requires any of:

- a new or stronger scientific claim;
- a new, rerun, or reinterpreted experiment;
- an unresolved factual judgment;
- a substantial proof or derivation;
- a new citation or unverified bibliographic fact;
- a commitment about future work, release, or policy;
- an ambiguous manuscript target;
- a choice among scientifically meaningful alternatives.

Set `complexity: undetermined` rather than guessing when evidence is incomplete. Undetermined items follow the complex checkpoint path.

## Grounded response drafting

Draft a simple response only after locating direct manuscript evidence. Record every evidence location consulted. Use the learned writing style, but prioritize accuracy and politeness over mimicry.

Prefer this response shape:

1. Acknowledge the concern specifically.
2. State the grounded answer or action.
3. Identify the exact manuscript location and change after it has actually been applied.
4. State a limitation or disagreement plainly when appropriate.

Example:

```tex
\ranswer{Thank you for identifying this ambiguity. We now define $G$ immediately
before Eq.~(4) in Section 2 and use the same notation throughout the proof.}
```

Do not write any of the following unless true and evidenced:

- “We performed an additional experiment ...”
- “The results demonstrate ...”
- “We added the requested citation ...”
- “We revised Section X ...” before that change verifies
- “We will release ...” without the user's decision

Update a draft response after manuscript editing so its location and description match the applied change. If the change could not be applied, keep the response pending and say why in state; do not leave a false completed claim in the letter.

Preserve disagreements politely. Explain the evidence and scope; do not promise a compromise that was not approved.

## User checkpoints

Group all complex/undetermined items into one checkpoint ordered by reviewer and original issue order. For each item provide:

- stable issue ID;
- verbatim concern;
- reason a decision is required;
- evidence already consulted;
- viable grounded options and their consequences;
- an explicit option to defer.

Persist `needs_user` state before asking. Never treat silence, `AUTO_PROCEED`, or a general “continue” setting as approval of a complex scientific choice. Save the user's exact decision, normalized action, rationale if supplied, and timestamp.

When the user defers or rejects a requested change, keep the concern and decision visible in the ledger and response plan. Make no corresponding manuscript change.

## Manuscript annotations

Ensure compatible definitions exist in the manuscript preamble. Reuse existing definitions; otherwise add only missing definitions and record the preamble change:

```tex
\providecommand{\A}[1]{\mbox{ \textbf{#1} }}
\providecommand{\ORI}{\A{ORI}}
\providecommand{\EORI}{\A{EORI}}
\providecommand{\MO}{\A{MO}}
\providecommand{\EMO}{\A{EMO}}
\providecommand{\VE}{\A{VE}}
\providecommand{\EVE}{\A{EVE}}
```

Use the following exact source-preserving forms:

Replacement:

```tex
\ORI <original text> \EORI\MO <revised text> \EMO
```

Pure insertion:

```tex
\MO <new text> \EMO
```

Deletion/disposition that remains visible:

```tex
\ORI <original text> \EORI
```

Never erase the original span. Do not nest a new ORI/MO pair around an already verified identical edit on resume. Record the original, revised, and rendered annotation before application, then verify the exact annotation after writing.

Put an unresolved verification placeholder inside the modified span:

```tex
\MO <conservative text> \VE <what must be verified> \EVE \EMO
```

Do not use `\VE...\EVE` to hide a decision that should be asked immediately; use it only when the paper should visibly retain an unresolved verification need.

## Section scope

Match `include` and `exclude` selectors against logical `\section`, `\subsection`, and lower-level titles case-insensitively after trimming whitespace.

- If `include` is empty, begin with the full document body.
- Otherwise, include matched sections and their descendants.
- Remove matched excluded sections and descendants; exclusion wins.
- Report every unmatched selector.
- Apply scope to review-driven manuscript changes, revise-phase manuscript changes, and `$SPEC` processing.
- Do not use section scope to suppress reviewer concerns or answers.
- Allow minimal compile-only fixes outside scope, but record them separately.

## `$SPEC` parsing

Scan the manuscript for balanced `!++ ... ++!` blocks. Support nesting to any depth by parsing delimiters with a stack; do not use a flat regular expression as the sole parser.

Ignore blocks inside:

- LaTeX line comments after an unescaped `%`;
- `\begin{comment}...\end{comment}`;
- conditional-compilation regions such as `\if... ... \fi` that are inactive or clearly used as comments;
- verbatim-like environments where the text is not manuscript prose;
- any equivalent ignored region recognized by the active document.

Record every discovered block, including out-of-scope and conflict blocks, in `paperEdits.json.specs`.

## `$SPEC` type semantics

Recognize keyword types prefixed with `@`; allow multi-word DIY types in brackets.

| Type | Required behavior |
|---|---|
| `@hint` | Use as a clue or basis. Treat it as an instruction only when context clearly makes it imperative. |
| `@keep` | Keep the original block content verbatim and append the modified output immediately below it. |
| `@mini` | Make the smallest justified edit while satisfying other active types. |
| `@inst` | Follow the explicit instruction exactly unless it conflicts with safety, evidence, or a higher-priority spec. |
| `@word` | Polish or reword only as needed. |
| `@rewrite` | Rewrite to fit local context while preserving intended meaning and research idea. |
| `@improve` | Make the text formal and paper-quality without changing the research idea. |
| `@expand` | Add only context-grounded explanation, intuition, or connective detail that materially helps. Do not pad or introduce new ideas. |
| `@check` | Check correctness, claim strength, precision, tone, and evidence fit. Keep or lightly polish supported content; correct conservatively when justified; otherwise use `\VE...\EVE`. |
| `@ref` | Resolve a citation/reference/URL from a supplied hint, paper context, labels, and verified bibliography sources. Never guess. |
| DIY type | Infer conservatively from the local block and record the interpreted behavior. Use a checkpoint if interpretation is consequential. |

## `$SPEC` combinations and output

Apply combination rules:

- `$SPEC` has highest priority over current-call instructions, reviewer changes, style, and general polishing.
- Apply `@inst` as binding, then apply `@check` to ensure the result remains supported.
- Apply `@mini` to minimize the result after satisfying other active types.
- Apply `@keep` last: preserve original block content and append the generated version.
- Use `@expand` only when justified detail exists; otherwise leave the content unchanged.
- Preserve the research idea for `@rewrite` and `@improve`.
- Do not introduce unsupported claims, results, references, or structural changes under `@check`.

When directly changing a block, replace the whole delimiters/content with a source-preserving annotated result. When a block only guides a change elsewhere, leave it intact and link it to that edit record. For `@keep`, keep the original block content and append the annotated new version immediately after it.

If a spec conflicts materially with a reviewer request or user decision, mark `scope_status: conflict`, persist the competing requirements, and ask the user unless the stated priority resolves the conflict without scientific judgment.

## Citation and factual requests

Never create a citation from memory. Search project `.bib` files first. Verify title, authors, year, venue, stable identifier, and claim support using trustworthy metadata and the paper itself before adding or citing an entry.

When verification is incomplete:

- mark the issue `needs_user` or `blocked`;
- insert `\VE <specific verification need> \EVE` only when a visible paper placeholder is useful;
- do not add plausible-looking BibTeX;
- do not claim the citation request is satisfied.

Treat requests for new experiments under the same evidence rule. Existing raw outputs may support a response only after tracing the claimed value to an actual artifact and evaluation scope.

## Coverage audit

Before completion, prove all of the following:

1. Every raw source is fingerprinted and listed once.
2. Every source's `issue_ids` point to existing unique issues in source order.
3. Every issue appears exactly once in the response-letter section plan and its verbatim concern is rendered.
4. Every drafted answer has exactly one outer `\ranswer{...}`.
5. Every claimed manuscript change links to an edit record and verified annotation.
6. Every complex/undetermined issue has a user decision or explicit pending/deferred/blocked status.
7. Every spec block has a recorded scope and disposition.
8. No response asserts an experiment, citation, result, or location that the recorded evidence does not support.

Fail the audit visibly rather than silently dropping an issue or weakening a requirement.
