---
name: paper-refine-zyr
description: "Refine and enrich an existing LaTeX paper by following embedded !++...++! spec tags, learning the user's writing style from reference materials, and compiling the result."
argument-hint: "[path/to/paper.tex] — style-materials: path/to/materials"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent
user-invocable: true
---

# Paper Refine (ZYR): Enrich and Polish an Existing LaTeX Paper

Refine the paper at: **$ARGUMENTS**

Invocation format:
```
/paper-refine-zyr path/to/paper.tex --style-materials: path/to/materials [--instructions: "additional instructions"] [--include: "Abstract, Introduction"] [--exclude: "Related Work"]
/paper-refine-zyr path/to/paper.tex --style-materials: path/to/materials [--output: path/to/custom_refined.tex] [--instructions: "additional instructions"] [--include: "Abstract, Introduction"] [--exclude: "Related Work"]
/paper-refine-zyr path/to/paper.tex --style-materials: path/to/materials [--overwrite] [--instructions: "additional instructions"] [--include: "Abstract, Introduction"] [--exclude: "Related Work"]
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

**If `style-materials` is not provided, stop and ask the user before proceeding.**

**Section-scope rules for `include` / `exclude`:**

- Selectors target logical LaTeX section and subsection headings by title, not raw line ranges.
- A matched section selector includes all nested subsections unless a nested subsection is explicitly excluded.
- If both parameters are provided, the editable set is: matched `include` sections minus matched `exclude` sections.
- If neither parameter is provided, the skill behaves exactly as before and may operate on the full paper.
- If a selector matches nothing, do not guess; report the unmatched selector in the Final Report.

## Communication Files

All inter-agent communication files live in one shared workspace-local communication directory for this skill:

- `COM_DIR=./com`

If `./com` does not exist, create it. The primary orchestration file is `./com/orchestrator.json`.

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
    "overwrite": false,
    "style_materials": "path provided by the user",
    "style_materials_for_writing_style": "path last used to generate ./com/writingStyle.json",
    "writing_style_file": "absolute path to ./com/writingStyle.json once written by the style-learning sub-agent",
    "instructions": null,
    "include": null,
    "exclude": null,
    "compile_success": null
  },
  "stage_gate": {
    "init_done": false,
    "style_learning_done": false
  }
}
```

Each sub-agent **must** update `current_stage` and `stage_notes` before returning. The shared `orchestrator.json` is workspace-local state for the current project and is refreshed on every invocation of the skill.

---

## Workflow

**General rule for shared state (Steps 0 and 1):** `./com/orchestrator.json` persists across runs in the same workspace. On every invocation, Step 0 must resolve `OUTPUT_TEX`, ensure shared state files exist, and refresh the current run's `source_tex`, `output_tex`, `overwrite`, `style_materials`, `instructions`, `include`, and `exclude` values before branch decisions are made. Steps 2, 2.5, and 3 always run.

### Step 0: Initialise

Step 0 runs on **every invocation**. Use shared workspace state in `./com/orchestrator.json`, but always perform the initialization work needed for the current invocation parameters.

1. Parse the invocation arguments: source `.tex` path, `style-materials` path, optional `output` filename, optional `--overwrite`, optional `--instructions`, optional `--include`, and optional `--exclude`.
2. If `style-materials` is missing, ask the user and halt.
3. Resolve `OUTPUT_TEX` using this precedence:
   - if `--overwrite` is present, `OUTPUT_TEX = source_tex`
   - else if `--output` is present, `OUTPUT_TEX = explicit output path`
   - else resolve `OUTPUT_TEX` using the default naming rule defined above
4. Perform the initialization work required by the current invocation parameters:
   - create `./com` if it does not exist
   - if `./com/orchestrator.json` does not exist, create it with `current_stage: "init"` and all stage gates `false`
   - update `./com/orchestrator.json` with the current invocation's `source_tex`, `output_tex`, `overwrite`, `style_materials`, `instructions`, `include`, and `exclude`
   - if `--overwrite` is present, use the source `.tex` file itself as the working file for all subsequent edits
   - otherwise, ensure the resolved output `.tex` working copy exists for this run by copying the source `.tex` to `OUTPUT_TEX` only when that file does not yet exist
   - when creating a new refined `.tex` output file, insert on the first line a provenance comment of the form `%refines <source_filename>` (for example `%refines paper_r5.tex`)
5. After Step 0 is complete for the current invocation, set `stage_gate.init_done = true`, update `timestamps.last_init`, and set `current_stage = "style_learning"`.

---

### Step 1: Style-Learning Sub-Agent

Check whether shared style state can be reused. Skip Step 1 only when all are true:

- `./com/writingStyle.json` exists
- `parameters.writing_style_file` points to `./com/writingStyle.json`
- the current `style-materials` path matches the previously recorded `parameters.style_materials_for_writing_style`

If any of those conditions fail, run the style-learning sub-agent below:

> **Role:** Writing-style analyst.
>
> **Inputs:**
> - `style_materials` path from `orchestrator.json`.
> - Output location: `./com/writingStyle.json`.
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
> 3. Write `writingStyle.json` with the schema:
>    ```json
>    {
>      "entry_name": {
>        "value": "concise characterisation",
>        "description": "what this entry means and how to apply it when generating text"
>      }
>    }
>    ```
> 4. Update `orchestrator.json`: set `parameters.writing_style_file` to the absolute path of `./com/writingStyle.json`, set `parameters.style_materials_for_writing_style` to the current `style_materials` path, set `stage_gate.style_learning_done = true`, update `timestamps.last_style_learning`, and set `current_stage = "refining"`.
> 5. Return a one-paragraph summary of the author's dominant style traits.

---

**Branch decision — Step 2 vs Step 2.5:** read `parameters.instructions` from `orchestrator.json`:
- If `null` or empty: execute **Step 2**. Skip Step 2.5.
- If it contains text: skip Step 2 entirely and execute **Step 2.5** instead.

After whichever step runs, continue directly to Step 3.

**Scope resolution for Step 2 / Step 2.5:** before making any content edit, resolve the editable section set from `parameters.include` and `parameters.exclude`:
- Match selectors against section/subsection titles case-insensitively after trimming whitespace.
- If `include` is empty, start from the full document body; otherwise start from the matched include set.
- Remove all matched exclude selectors from that set.
- Apply Step 2 and Step 2.5 edits only inside the resulting editable section set.
- The preamble is never part of section scoping and still follows the existing preamble rules.
- Step 3 compile fixes are exempt from this scope restriction and may make minimal compilation-only edits anywhere if required.

---

### Step 2: Paper Refining

Load `writingStyle.json` from the path in `orchestrator.json`. All generated text must conform to the style entries in that file.
Before any rewrite, resolve the editable section set from `parameters.include` / `parameters.exclude` and keep a list of unmatched selectors for Step 4.

#### 2a. Parse $SPEC Tags

Scan the **output `.tex` file** for all `!++ ... ++!` blocks. This is the user's embedded specification language.

**Parsing rules:**

- Tags can be nested to any depth:
  ```
  !++
    outer spec
      !++ inner spec ++!
  ++!
  ```
- **Ignore** any `!++ ... ++!` that appears inside a LaTeX comment or conditional-compilation block. Specifically, ignore specs inside:
  - Line comments: `% ... !++ ... ++! ...` (anything after `%` on the same line)
  - `\ifx ... \fi` / `\if... ... \fi` blocks
  - `\begin{comment} ... \end{comment}` blocks
  - Any other LaTeX commenting mechanism you recognise

**$SPEC type keywords** (prefix `@`; multi-word types use `[...]`):

| Type | Meaning |
|---|---|
| `@hint` | A clue or basis to guide your work. May also imply an `@inst`—use context to decide. |
| `@inst` | Explicit instruction—do exactly what it says. |
| `@word` | Polish / re-word the content of this spec block. |
| `@enrich` | Make the content more formal and paper-quality. Do NOT alter the underlying research idea. |
| `@check` | Check whether the current content of this spec block is stated suitably for the paper, using the surrounding paper context and your general scholarly knowledge. If the content is already suitable, keep it or make only light polish. If it is inaccurate, overstated, underspecified, awkward, or otherwise unsuitable, revise or correct it while preserving the underlying research idea. If you cannot justify a confident correction from context and knowledge, revise conservatively and insert a `!<< VERIFY: <reason> >>!` placeholder instead of guessing. |
| `@ref` | Fill in reference information (e.g. a `\cite{}`, `\ref{}`, footnote, or URL). Derive the target from context—surrounding text, paper topic, nearby bibliography—or from a hint the user appends after `@ref` inside the spec block (e.g. `!++ @ref [the original LTL paper by Pnueli] ++!`). If you cannot determine a reliable reference, insert a `!<< VERIFY: <reason> >>!` placeholder rather than guessing. |
| DIY types | Apply your best judgement from context. |

$SPEC take the **highest priority** over all other requirements. When a spec conflicts with another rule below, the spec wins.

For `@check`, judge suitability broadly: factual correctness, claim strength, precision, academic tone, and whether the wording fits the paper's apparent contribution and evidence. `@check` is a quality-control pass, not permission to introduce new claims, new results, new references, or structural changes that are unsupported by the paper. If `@check` appears together with other types, treat `@inst` as binding and apply `@check` to improve the resulting content within that instruction.

Only process a `$SPEC` block if it is located inside the editable section set. Leave `$SPEC` blocks outside the editable set untouched, and report those skipped blocks in the Final Report.

After processing each spec, replace the entire `!++ ... ++!` block (including the tags themselves) with the generated content.

Example:
`!++ @check We solve this problem perfectly in all settings. ++!`
should be kept only if the paper actually supports that statement; otherwise rewrite it to a defensible claim or add a `VERIFY` placeholder if the evidence is unclear.

---

#### 2b. Abstract

Write or rewrite the abstract section following these guidelines (adapted from `../paper-write/SKILL.md §0`):

- Use a **4-to-5-part flow**, adapted to the nature of the work:
  1. **What**: the subject, question, or phenomenon the paper addresses.
  2. **Why it matters** (not necessarily "why it is hard"): for theoretical work, this is often the *importance* or *generality* of the question—e.g., it unifies scattered results, reveals a fundamental limit, or enables reasoning about a broad class of systems. Hardness is one reason to care, but not the only one.
  3. **How**: the paper's approach, framework, or key construction.
  4. **What is established**: the main results—theorems, decision procedures, type systems, program logics, language designs, etc. For empirical work, include the strongest quantitative result. For theoretical work, state the principal theorem or contribution precisely but concisely.
  5. **Significance / take-away** (optional but encouraged): one sentence on what the result enables or changes.
- Must be self-contained (understandable without reading the paper).
- Start with the paper's specific contribution, not generic field-level background.
- **Quantitative results**: include one if the paper has experiments or benchmarks; omit if the paper is purely theoretical or presents only case studies—do not fabricate numbers.
- No citations, no undefined acronyms.
- Match the author's style from `writingStyle.json`.
- Create or rewrite the paper's abstract according to the paper's LaTeX format even if the abstract is outside the editable section set. Treat the abstract as a special front-matter element, not as a section-title-scoped edit.

---

#### 2c. Introduction

Write or rewrite the introduction following these guidelines (adapted from `../paper-write/SKILL.md §1`):

- **Hook**: open with 1–2 sentences that establish *why the reader should care*. For applied/empirical work this is usually a concrete problem. For theoretical work it may be a general motivation—an open question, a gap between theory and practice, a unification opportunity, or the significance of a class of systems.
- **Gap or open question**: articulate what is missing or unknown. For work that is not solving a specific hard problem, frame this as: "No general framework exists for …", "It remains unclear whether …", or "Prior work handles X but not Y."
- **Approach overview**: give a brief, jargon-light description of what the paper does before the reader gets lost in details.
- **Contributions**: list 2–4 items. These should be *specific and verifiable*, but need not be falsifiable in the empirical sense. Acceptable forms include: a theorem and its proof, a type system and its metatheory, a language design and its semantics, a decision procedure and its complexity, case studies demonstrating applicability.
- **Evidence / illustration**: preview the strongest result early. For papers with experiments, this is a key number. For papers with only case studies or worked examples, name the case study and what it demonstrates. For purely theoretical papers, state the principal theorem informally.
- **Roadmap**: end with a brief "The rest of this paper is organised as…" sentence.
- Include a reference to a main figure or diagram if one is already present; for theory papers this may be a commutative diagram, reduction graph, or type-derivation example rather than a plot.
- Match the author's style from `writingStyle.json`.
- Skip this step if `Introduction` is outside the editable section set.

---

#### 2d. General Enrichment

For all other sections:

- Add necessary explanatory sentences to make the text clearer and more complete—but **never introduce new research ideas** and **never alter existing research ideas**. Your additions complement; they do not innovate.
- Do **not** change the section structure (section headings and their order) without an explicit `@inst` in a $SPEC block. You may freely add or rearrange subsections.
- Do **not** modify the preamble (everything before `\begin{document}`) without explicit user instruction. If you must add a package or macro for correctness, add it silently and record every such change; report them all together in the Final Report (Step 4).
- Apply this step only to sections inside the editable section set.

---

#### 2e. Conclusion

Write or rewrite the conclusion section so it clearly summarizes the paper's content and takeaways.

- Synthesize the problem setting, the paper's approach, and the main findings or contributions.
- Emphasize what the paper establishes or enables without introducing new claims or new research ideas.
- Optionally mention limitations or future work only if the draft already supports them.
- Match the author's style from `writingStyle.json`.
- If the paper has no explicit conclusion-like section, do not invent a new section; record that fact in the Final Report.
- Skip this step if the conclusion section is outside the editable section set.

---

#### 2f. Reference Filling

After content enrichment (2b–2e), scan the **editable sections of the output `.tex` file** for every unresolved reference hole and attempt to fill it with the correct information.

**What counts as a reference hole:**
- Any `@ref` $SPEC block (e.g. `!++ @ref [the original LTL paper by Pnueli] ++!`)
- Empty or placeholder `\cite{}` commands (empty key, or keys like `?`, `TODO`, `FIXME`, `XX`)
- Empty or placeholder `\ref{}` / `\eqref{}` / `\autoref{}` commands
- Other similar LaTeX reference forms you recognise as unfilled

**How to fill each hole — consult sources in this order:**

1. **Nearby $SPEC hint**: if the hole is inside or immediately adjacent to a `@ref` $SPEC block, use that hint as the primary guide.
2. **Paper context**: infer from the surrounding prose, section content, and already-defined `\label{}` targets in the file.
3. **Project `.bib` files**: search all `.bib` files found in the working project directory (and its subdirectories) for a matching entry.
4. **Personal library**: clone or fetch `https://github.com/yuanruizhang5a/MyLibrary.git` (read-only, do not modify) and search `./Bibtex/reference.bib` within it.
5. **Web search**: only if all above sources fail to yield a confident match.

**Rules:**
- Do **not** guess. If no source provides a reliable match, insert a `!<< VERIFY: <reason> >>!` placeholder in place of the hole and move on.
- When a `\cite{}` key is resolved, ensure the corresponding BibTeX entry exists in the project's `.bib` file; copy it from the library `.bib` if needed.
- When a `\ref{}` target is resolved to a `\label{}` that does not yet exist in the file, add the `\label{}` at the appropriate location and record the addition in the Final Report.
- Do not remove or alter any `!<< VERIFY: ... >>!` placeholders left by earlier steps.
- Only fill holes located inside the editable section set. Adding a supporting `.bib` entry or a missing `\label{}` is allowed when required to complete an in-scope fix.

---

#### 2g. Progress Narration

As you work through each part, output a brief (1–2 sentence) plain-English explanation of what you are doing and why. This is intentional—the user wants to learn.

Example:
> "Enriching the second paragraph of §3 to clarify why the loss function uses a KL term rather than cross-entropy—the current draft states the choice without motivation."

---

#### 2h. Completion

After all sections are processed:

1. Save the enriched output `.tex` file.
2. Update `orchestrator.json`: set `current_stage = "compiling"`.

---

### Step 2.5: User Ad-hoc Instructions (re-run only)

This step runs **only** when `--instructions` is provided in the invocation. It replaces Step 2 for this run.

Execute the instructions passed via `--instructions` on the output `.tex` file. Instructions are free-form: edits, rewrites, additions, removals, or any other modification the user specifies.

Rules:
- Do **not** re-run the full §2a–2h enrichment pipeline; only act on what the instructions say.
- Constrain all edits to the editable section set resolved from `--include` / `--exclude`.
- If the instructions target the abstract, allow abstract edits even when the abstract lies outside the section-title editable set. Treat the abstract as the same special front-matter exception used in Step 2b.
- If an instruction conflicts with a $SPEC tag remaining in the file, flag the conflict to the user before acting.
- Record a brief note of what was done in `stage_notes` of `orchestrator.json`.
- After completing, set `current_stage = "compiling"` and proceed to Step 3.

---

### Step 3: Compile Sub-Agent

Spawn a sub-agent with the following mandate:

> **Role:** LaTeX compiler and debugger.
>
> **Inputs:** `output_tex` path from `orchestrator.json`.
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
>    - Update `orchestrator.json`: `parameters.compile_success = true`, `current_stage = "done"`.
> 5. On final failure:
>    - Update `orchestrator.json`: `parameters.compile_success = false`, `current_stage = "error"`, `stage_notes = "<error summary>"`.
>    - Return the error summary.

The main agent waits for `current_stage == "done"` (or `"error"`) before reporting to the user.

---

### Step 4: Final Report

Report to the user:

1. **Output file:** absolute path to the refined `.tex` file, or the source `.tex` path if `--overwrite` was used.
2. **Compilation status:** success with PDF path, or failure with error summary.
3. **Changes summary:** a brief list of what was changed and why (Abstract, Introduction, $SPEC replacements, any preamble additions).
4. **Scope summary:** which sections were included, excluded, and ultimately treated as editable for this run.
5. **Write mode:** state explicitly whether the run created a new refined file or overwrote the source `.tex` file in place.
6. If preamble was modified: explicitly list each change.
7. If any `$SPEC` or sections were skipped, ambiguous, or unmatched due to scope selection: list them for the user's attention.

---

## Key Rules

- **Default mode preserves the original `.tex` file.** All changes go to the output copy unless `--overwrite` is explicitly present.
- **$SPEC take highest priority.** They override all other requirements when there is a conflict.
- **Ignore $SPEC in comments.** Use LaTeX comment-detection knowledge carefully.
- **`@check` is conservative.** Correct or soften unsuitable content when justified by the paper and general knowledge; when confidence is inadequate, use `!<< VERIFY: ... >>!` instead of asserting a strong correction.
- **Do not invent research content.** Enrichment means clarity and completeness, not new ideas.
- **Do not change section structure** unless an `@inst` $SPEC explicitly requests it.
- **`include` / `exclude` only scope Step 2 and Step 2.5 content edits.** They do not restrict minimal compile-only fixes in Step 3.
- **Preamble changes go to the Final Report**, not as immediate interruptions—collect them silently and list them all in Step 4.
- **Narrate briefly** as you work—the user wants to learn from each step.
- **Style first.** Load `writingStyle.json` before writing a single sentence; every generated sentence must reflect it.
- **All communication files** (`orchestrator.json`, `writingStyle.json`) live in the shared workspace-local `./com` directory.
- **`--overwrite` wins over `--output`.** If both are present, write directly to the source `.tex` file.
- **Large-file write fallback:** if the `Write` tool fails on size, silently retry with `Bash` (`cat << 'EOF' > file`) without prompting the user.
