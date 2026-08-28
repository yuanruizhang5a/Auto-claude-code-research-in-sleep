---
name: paper-refine-zyr
description: "Refine and enrich an existing LaTeX paper by following embedded !++...++! spec tags, learning the user's writing style from reference materials, and optionally compiling the result."
argument-hint: "[path/to/paper.tex] — style-materials: path/to/materials [--com-dir path] [--no-compile]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent
user-invocable: true
---

# Paper Refine (ZYR): Enrich and Polish an Existing LaTeX Paper

Refine the paper at: **$ARGUMENTS**

Invocation format:
```
/paper-refine-zyr path/to/paper.tex --style-materials: path/to/materials [--com-dir path/to/communication] [--instructions: "additional instructions"] [--include: "Abstract, Introduction"] [--exclude: "Related Work"] [--no-compile]
/paper-refine-zyr path/to/paper.tex --style-materials: path/to/materials [--output: path/to/custom_refined.tex] [--com-dir path/to/communication] [--instructions: "additional instructions"] [--include: "Abstract, Introduction"] [--exclude: "Related Work"] [--no-compile]
/paper-refine-zyr path/to/paper.tex --style-materials: path/to/materials [--overwrite] [--com-dir path/to/communication] [--instructions: "additional instructions"] [--include: "Abstract, Introduction"] [--exclude: "Related Work"] [--no-compile]
```

## Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| positional arg | yes | — | Path to the source `.tex` file to refine |
| `style-materials` | **yes** | none — ask user if missing | Path to user's reference writing materials (folder, `.pdf`, `.md`, or `.txt`) |
| `output` | no | `<base>_rN.tex` in the same directory, where `N` is the first unused positive integer and `<base>` does not end with another repeated refinement suffix | Output `.tex` filename. Each run creates a new refined file by default rather than reusing a previous default output. If the source file already ends with `_rN`, increment that suffix to `_r(N+1)` instead of appending another `_rN`. |
| `overwrite` | no | off | If present, overwrite the source `.tex` file directly. This flag wins over `output`, so the skill edits the original file in place instead of creating a new refined `.tex` file. |
| `instructions` | no | — | Free-form instructions to apply to the output file. When provided, Step 2 is **skipped** and Step 2.5 runs instead. |
| `include` | no | — | Comma-separated section/subsection titles that the skill may edit during Step 2 or Step 2.5. Matching is case-insensitive after trimming whitespace. If omitted, all sections remain eligible unless excluded. |
| `exclude` | no | — | Comma-separated section/subsection titles that the skill must skip during Step 2 or Step 2.5. Matching is case-insensitive after trimming whitespace. If omitted, no sections are skipped by default. |
| `--com-dir` | no | `./com` | Communication directory for `orchestrator.json`, `writingStyle.json`, and any future inter-agent files. Supply a non-empty path relative to the invocation's current working directory. The normalized path must remain inside that directory. |
| `no-compile` | no | off | If present, do not compile the output after modification. Skip Step 3, set `compile_success` to `null`, and report that compilation was intentionally skipped. |

**If `style-materials` is not provided, stop and ask the user before proceeding.**

**Section-scope rules for `include` / `exclude`:**

- Selectors target logical LaTeX section and subsection headings by title, not raw line ranges.
- A matched section selector includes all nested subsections unless a nested subsection is explicitly excluded.
- If both parameters are provided, the editable set is: matched `include` sections minus matched `exclude` sections.
- If neither parameter is provided, the skill behaves exactly as before and may operate on the full paper.
- If a selector matches nothing, do not guess; report the unmatched selector in the Final Report.

## Communication Files

All inter-agent communication files live in one resolved communication directory for the current run:

- With no `--com-dir`, set `COM_DIR` to the absolute normalized form of `./com` under the invocation's current working directory. This preserves the existing default.
- With `--com-dir <path>`, require a non-empty relative path, resolve it against the invocation's current working directory, normalize it, and require the result to remain inside that directory. If the path is absolute or escapes the current directory (for example via `..`), stop and ask the user for a workspace-local path.

Create `COM_DIR` if it does not exist. Set `ORCHESTRATOR_JSON=${COM_DIR}/orchestrator.json` and `WRITING_STYLE_JSON=${COM_DIR}/writingStyle.json`; use these resolved paths everywhere rather than reconstructing `./com` later.

Define `OUTPUT_TEX` separately from `COM_DIR`:

- `OUTPUT_TEX`: the source `.tex` path if `--overwrite` is present; otherwise the explicit `--output` path if provided; otherwise the default output path defined in the `output` parameter above

### orchestrator.json Schema

```json
{
  "timestamps": {
    "skill_start": "ISO-8601 datetime when the current run started",
    "last_init": "ISO-8601 datetime when Step 0 last performed initialization work",
    "last_style_learning": "ISO-8601 datetime when Step 1 last generated writingStyle.json"
  },
  "current_stage": "one of: init | style_learning | refining | compiling | done | error",
  "stage_notes": "free-text notes for the current stage (e.g. what the sub-agent just did)",
  "parameters": {
    "source_tex": "absolute path to the original .tex file",
    "output_tex": "absolute path to the output .tex file",
    "com_dir": "absolute path to the resolved communication directory",
    "overwrite": false,
    "style_materials": "path provided by the user",
    "style_materials_for_writing_style": "path last used to generate WRITING_STYLE_JSON",
    "writing_style_file": "absolute path to WRITING_STYLE_JSON once written by the style-learning sub-agent",
    "instructions": null,
    "include": null,
    "exclude": null,
    "no_compile": false,
    "compile_success": null
  },
  "stage_gate": {
    "init_done": false,
    "style_learning_done": false
  }
}
```

Each sub-agent **must** receive the absolute `ORCHESTRATOR_JSON` path and update `current_stage` and `stage_notes` there before returning. The selected `orchestrator.json` is workspace-local state for the current project and is refreshed on every invocation of the skill.

---

## Workflow

**General rule for shared state (Steps 0 and 1):** `ORCHESTRATOR_JSON` persists across runs that select the same `COM_DIR`. On every invocation, Step 0 must resolve `COM_DIR` and `OUTPUT_TEX`, ensure the selected shared state files exist, and refresh the current run's `source_tex`, `output_tex`, `com_dir`, `overwrite`, `style_materials`, `instructions`, `include`, `exclude`, and `no_compile` values before branch decisions are made. Selecting a different `--com-dir` selects an independent communication state and style cache. Step 2 or Step 2.5 always runs. Step 3 runs unless `--no-compile` is present.

### Step 0: Initialise

Step 0 runs on **every invocation**. Use shared workspace state in the selected `ORCHESTRATOR_JSON`, but always perform the initialization work needed for the current invocation parameters.

1. Parse the invocation arguments: source `.tex` path, `style-materials` path, optional `output` filename, optional `--overwrite`, optional `--com-dir`, optional `--instructions`, optional `--include`, optional `--exclude`, and optional `--no-compile`.
2. If `style-materials` is missing, ask the user and halt.
3. Capture the invocation's current working directory, then resolve `COM_DIR`, `ORCHESTRATOR_JSON`, and `WRITING_STYLE_JSON` using the Communication Files rules above. Validate `--com-dir` before reading or creating any communication file.
4. Resolve `OUTPUT_TEX` using this precedence:
   - if `--overwrite` is present, `OUTPUT_TEX = source_tex`
   - else if `--output` is present, `OUTPUT_TEX = explicit output path`
   - else resolve `OUTPUT_TEX` using the default naming rule defined above
5. Perform the initialization work required by the current invocation parameters:
   - create `COM_DIR` if it does not exist; if the resolved path exists but is not a directory, report the conflict and halt
   - if `ORCHESTRATOR_JSON` does not exist, create it with `current_stage: "init"` and all stage gates `false`
   - update `ORCHESTRATOR_JSON` with the current invocation's absolute `source_tex`, absolute `output_tex`, absolute `com_dir`, `overwrite`, `style_materials`, `instructions`, `include`, `exclude`, and `no_compile`; reset `compile_success` to `null`
   - if `--overwrite` is present, use the source `.tex` file itself as the working file for all subsequent edits
   - otherwise, ensure the resolved output `.tex` working copy exists for this run by copying the source `.tex` to `OUTPUT_TEX` only when that file does not yet exist
   - when creating a new refined `.tex` output file, insert on the first line a provenance comment of the form `%refines <source_filename>` (for example `%refines paper_r5.tex`)
   - treat the `.tex` content present at invocation start as the baseline for this refinement pass; every directly modified output span relative to that baseline must later be wrapped with `\MO ... \EMO`
6. After Step 0 is complete for the current invocation, set `stage_gate.init_done = true`, update `timestamps.last_init`, and set `current_stage = "style_learning"` in `ORCHESTRATOR_JSON`.

---

### Step 1: Style-Learning Sub-Agent

Check whether shared style state can be reused. Skip Step 1 only when all are true:

- `WRITING_STYLE_JSON` exists
- `parameters.com_dir` equals the absolute `COM_DIR`
- `parameters.writing_style_file` equals the absolute `WRITING_STYLE_JSON`
- the current `style-materials` path matches the previously recorded `parameters.style_materials_for_writing_style`

If any of those conditions fail, run the style-learning sub-agent below:

> **Role:** Writing-style analyst.
>
> **Inputs:**
> - Absolute `ORCHESTRATOR_JSON` path from Step 0.
> - `style_materials` path from that file.
> - Output location: absolute `WRITING_STYLE_JSON` from Step 0.
>
> **Task:**
> 1. Read all provided reference materials (recursively if a folder; handle `.pdf`, `.md`, `.txt`, `.tex`).
> 2. Analyse the writing style across at least the following dimensions, and any others you judge important:
>    - `sentence_length`: typical sentence length pattern (short/medium/long; varies or uniform).
>    - `paragraph_structure`: how paragraphs are opened and closed; use of topic sentences.
>    - `formality_level`: casual vs. formal academic register.
>    - `voice`: preference for active vs. passive voice.
>    - `hedging_style`: how uncertainty is expressed (e.g., "may", "it is possible that", rarely hedges).
>    - `transition_words`: favourite connectors and transition phrases.
>    - `jargon_tolerance`: tendency to define new terms vs. assume knowledge.
>    - `first_person_use`: avoids / uses "we" / uses "I".
>    - `equation_explanation_style`: how inline vs. display math is introduced and referenced.
>    - `citation_placement`: citations at end of sentence, mid-sentence, or woven naturally.
>    - `figure_reference_style`: how figures and tables are pointed to in the text.
>    - `recurring_phrases`: any characteristic phrases or idioms the author favours.
>    - `tone`: confident, cautious, enthusiastic, neutral, etc.
> 3. Write the style file to the supplied absolute `WRITING_STYLE_JSON` path with the schema:
>    ```json
>    {
>      "entry_name": {
>        "value": "concise characterisation",
>        "description": "what this entry means and how to apply it when generating text"
>      }
>    }
>    ```
> 4. Update `ORCHESTRATOR_JSON`: set `parameters.com_dir` to the absolute `COM_DIR`, set `parameters.writing_style_file` to the absolute `WRITING_STYLE_JSON`, set `parameters.style_materials_for_writing_style` to the current `style_materials` path, set `stage_gate.style_learning_done = true`, update `timestamps.last_style_learning`, and set `current_stage = "refining"`.
> 5. Return a one-paragraph summary of the author's dominant style traits.

---

**Branch decision — Step 2 vs Step 2.5:** read `parameters.instructions` from `ORCHESTRATOR_JSON`:
- If `null` or empty: execute **Step 2**. Skip Step 2.5.
- If it contains text: skip Step 2 entirely and execute **Step 2.5** instead.

After whichever step runs, continue to Step 3 unless `parameters.no_compile` is `true`. When it is `true`, skip Step 3, leave `parameters.compile_success = null`, set `current_stage = "done"`, and continue to Step 4.

**Scope resolution for Step 2 / Step 2.5:** before making any content edit, resolve the editable section set from `parameters.include` and `parameters.exclude`:
- Match selectors against section/subsection titles case-insensitively after trimming whitespace.
- If `include` is empty, start from the full document body; otherwise start from the matched include set.
- Remove all matched exclude selectors from that set.
- Apply Step 2 and Step 2.5 edits only inside the resulting editable section set.
- The preamble is never part of section scoping and still follows the existing preamble rules.
- Step 3 compile fixes are exempt from this scope restriction and may make minimal compilation-only edits anywhere if required.

---

### Step 2: Paper Refining

Shared invariants for Step 2 and Step 2.5:

- Load the style file from `parameters.writing_style_file` in `ORCHESTRATOR_JSON`; verify that it equals `WRITING_STYLE_JSON`, and make all generated text follow it.
- Resolve the editable section set from `parameters.include` / `parameters.exclude` before editing and keep unmatched selectors for Step 4.
- Compare every edit against the Step 0 baseline; every directly inserted, rewritten, or replaced span must be wrapped in `\MO ... \EMO`. Unchanged text stays unwrapped. If an edited span contains a verification placeholder, keep it inside the `\MO ... \EMO` wrapper.
- Ensure the output `.tex` preamble defines:

```tex
\newcommand{\A}[1]{\mbox{ \textbf{#1} }}
\newcommand{\MO}{\A{MO}}
\newcommand{\EMO}{\A{EMO}}
\newcommand{\VE}{\A{VE}}
\newcommand{\EVE}{\A{EVE}}
```

Reuse existing compatible definitions instead of redefining them. Treat `\A` as the shared formatter behind `\MO`, `\EMO`, `\VE`, and `\EVE`; if a literal boxed bold `A` is needed, use `\A{A}`.

#### 2a. Parse $SPEC Tags

Scan the **output `.tex` file** for `!++ ... ++!` blocks, the user's embedded specification language.

- Nested tags are allowed to any depth:
  ```
  !++
    outer spec
      !++ inner spec ++!
  ++!
  ```
- Ignore specs inside LaTeX comments or conditional-compilation blocks, including line comments (`% ...` after `%` on the same line), `\ifx ... \fi` / `\if... ... \fi`, `\begin{comment} ... \end{comment}`, and any equivalent commenting mechanism you recognise.

**$SPEC type keywords** (prefix `@`; multi-word types use `[...]`):

| Type | Meaning |
|---|---|
| `@hint` | A clue or basis to guide your work. May also imply an `@inst`—use context to decide. |
| `@keep` | Keep the current content of this spec block unchanged, and append your modified version immediately below the original content rather than replacing it. Use this when the original wording should remain visible while your revised or enriched version is added after it. |
| `@mini` | When making changes for this spec block, try to make the minimum necessary change relative to the original content. Preserve wording, structure, and local phrasing as much as possible while still satisfying the other active spec types and the paper context. |
| `@inst` | Explicit instruction—do exactly what it says. |
| `@word` | Polish / re-word / improve the content of this spec block if necessary. |
| `@grammar` | Check the content for grammar, spelling, capitalization, and punctuation problems. When no other active type authorizes broader changes, leave an error-free block completely unchanged; if problems exist, correct only the minimum necessary tokens or marks while preserving meaning, terminology, sentence structure, and phrasing. Do not paraphrase, reword, or style-polish under `@grammar` alone. |
| `@rewrite` | Rewrite the current content of this spec block according to the current paper context. Preserve the intended meaning and the underlying research idea unless the surrounding context clearly requires correction. Use the local section, neighboring claims, terminology, and paper narrative to produce a version that fits naturally into the paper. |
| `@improve` | Make the content more formal and paper-quality. Do NOT alter the underlying research idea. |
| `@expand` | Enrich, expand, or complement the explanation of the current content of this spec block according to the surrounding context and your understanding of the paper. Add clarifying detail, missing connective explanation, intuition, or brief elaboration only when it materially improves the paper. If the current content is already adequately developed, do not change this part. |
| `@check` | Check whether the current content of this spec block is stated suitably for the paper, using the surrounding paper context and your general scholarly knowledge. If the content is already suitable, keep it or make only light polish. If it is inaccurate, overstated, underspecified, awkward, or otherwise unsuitable, revise or correct it while preserving the underlying research idea. If you cannot justify a confident correction from context and knowledge, revise conservatively and insert a `\VE <reason> \EVE` placeholder instead of guessing. |
| `@ref` | Fill in reference information (e.g. a `\cite{}`, `\ref{}`, footnote, or URL). Derive the target from context—surrounding text, paper topic, nearby bibliography—or from a hint the user appends after `@ref` inside the spec block (e.g. `!++ @ref [the original LTL paper by Pnueli] ++!`). If you cannot determine a reliable reference, insert a `\VE <reason> \EVE` placeholder rather than guessing. |
| DIY types | Apply your best judgement from context. |

- `$SPEC` has highest priority over all other requirements.
- `@keep` means preserve the original block content verbatim and place your modified output directly below it. When combined with other types, apply those types to produce the appended version rather than replacing the original text.
- `@mini` means make the smallest justified edit. When combined with other types, satisfy those types while keeping the output as close as reasonably possible to the original block.
- `@grammar` alone is a grammar-and-mechanics check, not a rewriting instruction. If the content has no grammar, spelling, capitalization, or punctuation problem, leave the entire spec block unchanged. If a correction is needed, change only what is required to fix the detected problem and preserve all unaffected wording and structure.
- When another active type explicitly authorizes broader transformation, apply that type normally and then use `@grammar` to check the resulting text; `@grammar` does not restrict the companion type's authorized behavior. Apply `@mini` without reintroducing an error, then apply `@keep` last.
- `@check` judges factual correctness, claim strength, precision, tone, and fit to the paper's actual contribution/evidence. It must not introduce unsupported claims, results, references, or structural changes. If `@check` appears with other types, treat `@inst` as binding and then apply `@check`.
- `@expand` is context-grounded elaboration, not padding or new ideas. If no justified expansion is available, leave the block unchanged.
- Only process `$SPEC` blocks inside the editable section set. Leave out-of-scope blocks untouched and report them in Step 4.
- Remove a `!++ ... ++!` block only when you directly change that block's content; if it merely serves as guidance for changes elsewhere, leave it intact. When you do change it, replace the entire block with the generated content, except when `@keep` is present: in that case, preserve the original block content and append the generated version immediately below it.

Example:
`!++ @check We solve this problem perfectly in all settings. ++!`
should be kept only if the paper actually supports that statement; otherwise rewrite it to a defensible claim or add a `\VE <reason> \EVE` placeholder if the evidence is unclear. Wrap the edited replacement in `\MO ... \EMO`.

---

#### 2b. Abstract

Write or rewrite the abstract using the `../paper-write/SKILL.md §0` rubric: 4-to-5-part flow (what, why it matters, how, what is established, optional significance), self-contained, starts from the paper's specific contribution, no citations or undefined acronyms, and includes a quantitative result only when the paper actually has one. The abstract is a special front-matter exception: edit it even if it lies outside the section-title editable set.

---

#### 2c. Introduction

Write or rewrite the introduction using the `../paper-write/SKILL.md §1` rubric: hook, gap/open question, approach overview, 2–4 specific contributions, early evidence/illustration, short roadmap, and a reference to an existing main figure/diagram when appropriate. Skip this step if `Introduction` is outside the editable section set.

---

#### 2d. General Enrichment

For all other sections inside the editable section set, add clarifying/completing explanation without introducing or altering research ideas. Do not change section headings or their order unless an `@inst` explicitly asks for it; rearranging or adding subsections is allowed. Do not modify the preamble except for correctness-critical packages/macros, and record every such preamble change for Step 4.

---

#### 2e. Conclusion

Write or rewrite the conclusion to summarize the setting, approach, and main findings/contributions, emphasizing what the paper establishes or enables without adding new claims or ideas. Mention limitations/future work only if already supported. If there is no conclusion-like section, do not invent one; report that in Step 4. Skip this step if the conclusion section is outside the editable section set.

---

#### 2f. Reference Filling

After 2b–2e, scan the editable sections for unresolved reference holes: `@ref` specs, empty/placeholder `\cite{}`, empty/placeholder `\ref{}` / `\eqref{}` / `\autoref{}`, and equivalent unfilled reference forms. Resolve each hole using this source order: nearby `@ref` hint, paper context and existing `\label{}` targets, project `.bib` files, `https://github.com/yuanruizhang5a/MyLibrary.git` (`./Bibtex/reference.bib`, read-only), then web search. Do not guess: if no reliable match exists, insert `\VE <reason> \EVE`. If a `\cite{}` key is resolved, ensure the BibTeX entry exists in the project `.bib`; if a resolved `\ref{}` needs a missing `\label{}`, add it and report it in Step 4. Preserve pre-existing `\VE ... \EVE` placeholders unless you are substantively resolving or rewriting that exact segment. Only fill holes inside the editable section set, though required supporting `.bib` and `\label{}` additions are allowed.

---

#### 2g. Progress Narration

As you work, output brief 1–2 sentence plain-English explanations of what you are doing and why. Example: "Enriching the second paragraph of §3 to clarify why the loss function uses a KL term rather than cross-entropy—the current draft states the choice without motivation."

---

#### 2h. Completion

After all sections are processed:

1. Save the enriched output `.tex` file.
2. Update `ORCHESTRATOR_JSON`: if `parameters.no_compile` is `true`, leave `parameters.compile_success = null` and set `current_stage = "done"`; otherwise set `current_stage = "compiling"`.

---

### Step 2.5: User Ad-hoc Instructions (re-run only)

This step runs **only** when `--instructions` is provided in the invocation. It replaces Step 2 for this run.

Execute `--instructions` on the output `.tex` file without re-running the full §2a–2h enrichment pipeline. Keep edits inside the editable section set; allow the same abstract exception as Step 2b. If an instruction conflicts with a remaining `$SPEC`, flag that conflict before acting. Follow the shared annotation rules above and record a brief note in `stage_notes` in `ORCHESTRATOR_JSON`. If `parameters.no_compile` is `true`, leave `parameters.compile_success = null`, set `current_stage = "done"`, and skip Step 3; otherwise set `current_stage = "compiling"` and proceed to Step 3.

---

### Step 3: Compile Sub-Agent

Skip this entire step when `parameters.no_compile` is `true`.

Spawn a sub-agent with the following mandate:

> **Role:** LaTeX compiler and debugger.
>
> **Inputs:** `output_tex` and absolute `com_dir` paths from `ORCHESTRATOR_JSON`, plus the absolute `ORCHESTRATOR_JSON` path itself so status is written to the selected communication directory.
>
> **Task:**
> 1. Determine the project root (the directory containing the `.tex` file or a parent with `Makefile`/`latexmkrc`).
> 2. Attempt compilation:
>    ```bash
>    latexmk -pdf -interaction=nonstopmode -halt-on-error <output_tex>
>    ```
>    Fall back to `pdflatex` twice + `bibtex` + `pdflatex` twice if `latexmk` is not available.
> 3. If compilation fails:
>    - Read the `.log` file to identify errors.
>    - Fix each error in the output `.tex` (only fix compilation errors—do not alter content). These compile-only fixes may touch sections outside the Step 2 / Step 2.5 editable set if necessary for successful compilation.
>    - Re-try. Repeat until successful or until 5 attempts are exhausted.
>    - If still failing after 5 attempts, report the remaining errors clearly to the user and halt.
> 4. On success:
>    - Report: "Compiled successfully. Output PDF: `<path>`."
>    - Update the supplied `ORCHESTRATOR_JSON`: `parameters.compile_success = true`, `current_stage = "done"`.
> 5. On final failure:
>    - Update the supplied `ORCHESTRATOR_JSON`: `parameters.compile_success = false`, `current_stage = "error"`, `stage_notes = "<error summary>"`.
>    - Return the error summary.

The main agent reads the selected `ORCHESTRATOR_JSON` and waits for `current_stage == "done"` (or `"error"`) before reporting to the user.

---

### Step 4: Final Report

Report to the user:

1. **Output file:** absolute path to the refined `.tex` file, or the source `.tex` path if `--overwrite` was used.
2. **Compilation status:** success with PDF path, failure with error summary, or skipped because `--no-compile` was specified.
3. **Changes summary:** what changed and why (for example Abstract, Introduction, `$SPEC` replacements, preamble additions), explicitly noting `\MO ... \EMO` tagging and any newly introduced `\VE ... \EVE` placeholders.
4. **Scope summary:** which sections were included, excluded, and ultimately treated as editable for this run.
5. **Write mode:** state explicitly whether the run created a new refined file or overwrote the source `.tex` file in place.
6. If preamble was modified: explicitly list each change.
7. **Communication directory:** absolute `COM_DIR` used for this run and whether it came from the default or `--com-dir`.
8. If any `$SPEC` or sections were skipped, ambiguous, or unmatched due to scope selection: list them for the user's attention.

---

## Key Rules

- Preserve the original `.tex` unless `--overwrite` is explicitly present; `--overwrite` wins over `--output`.
- `$SPEC` has highest priority; ignore `$SPEC` in comments/ignored LaTeX regions.
- Enrichment improves clarity/completeness without inventing research content; `@check` is conservative and falls back to `\VE ... \EVE` when confidence is inadequate.
- `include` / `exclude` scope only Step 2 and Step 2.5 content edits, not minimal compile-only fixes in Step 3.
- When `--no-compile` is present, do not spawn the compile sub-agent or run any LaTeX compilation command; leave `compile_success` as `null`.
- Collect preamble changes silently for Step 4 rather than interrupting the run.
- Narrate briefly while working; every generated sentence must follow the selected `WRITING_STYLE_JSON`.
- Shared state lives in the resolved workspace-local `COM_DIR`; its default remains `./com`.
- If the `Write` tool fails on size, silently retry with `Bash` (`cat << 'EOF' > file`) without prompting.
