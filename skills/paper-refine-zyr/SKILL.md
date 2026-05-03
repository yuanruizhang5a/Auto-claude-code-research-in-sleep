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
/paper-refine-zyr path/to/paper.tex --style-materials: path/to/materials [--output: refined_paper.tex]
```

## Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| positional arg | yes | — | Path to the source `.tex` file to refine |
| `style-materials` | **yes** | none — ask user if missing | Path to user's reference writing materials (folder, `.pdf`, `.md`, or `.txt`) |
| `output` | no | `refined_<original_filename>.tex` in the same directory | Output `.tex` filename |

**If `style-materials` is not provided, stop and ask the user before proceeding.**

## Communication Files

All inter-agent communication files live in `skills/paper-refine-zyr/com/`. Create this folder if it does not exist. The primary orchestration file is `skills/paper-refine-zyr/com/orchestrator.json`.

### orchestrator.json Schema

```json
{
  "timestamps": {
    "skill_start": "ISO-8601 datetime when the main skill started"
  },
  "current_stage": "one of: init | style_learning | refining | compiling | done | error",
  "stage_notes": "free-text notes for the current stage (e.g. what the sub-agent just did)",
  "parameters": {
    "source_tex": "absolute path to the original .tex file",
    "output_tex": "absolute path to the output .tex file",
    "style_materials": "path provided by the user",
    "writing_style_file": "absolute path to writingStyle.json once written by the style-learning sub-agent",
    "compile_success": null
  },
  "stage_gate": {
    "style_learning_done": false,
    "refining_done": false,
    "compile_done": false
  }
}
```

Each sub-agent **must** update `current_stage`, `stage_notes`, and the relevant `stage_gate` flag before returning.

---

## Workflow

### Step 0: Initialise

1. Parse the invocation arguments: source `.tex` path, `style-materials` path, and optional `output` filename.
2. If `style-materials` is missing, ask the user and halt.
3. Create `skills/paper-refine-zyr/com/` if not present.
4. Write the initial `orchestrator.json` with `current_stage: "init"` and all stage gates `false`.
5. Copy the source `.tex` to the output path **without modification**. All edits happen only on the output file from this point forward. Never touch the original.

---

### Step 1: Style-Learning Sub-Agent

Spawn a sub-agent with the following mandate:

> **Role:** Writing-style analyst.
>
> **Inputs:**
> - `style_materials` path from `orchestrator.json`.
> - Output location: `skills/paper-refine-zyr/com/writingStyle.json`.
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
> 4. Update `orchestrator.json`: set `parameters.writing_style_file` to the absolute path of the generated file, set `stage_gate.style_learning_done = true`, and set `current_stage = "refining"`.
> 5. Return a one-paragraph summary of the author's dominant style traits.

The main agent **must not** proceed to Step 2 until `stage_gate.style_learning_done == true`.

---

### Step 2: Paper Refining

Load `writingStyle.json` from the path in `orchestrator.json`. All generated text must conform to the style entries in that file.

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
| DIY types | Apply your best judgement from context. |

$SPEC take the **highest priority** over all other requirements. When a spec conflicts with another rule below, the spec wins.

After processing each spec, replace the entire `!++ ... ++!` block (including the tags themselves) with the generated content.

---

#### 2b. Abstract

Write or rewrite the abstract section following these guidelines (adapted from `skills/paper-write/SKILL.md §0`):

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

---

#### 2c. Introduction

Write or rewrite the introduction following these guidelines (adapted from `skills/paper-write/SKILL.md §1`):

- **Hook**: open with 1–2 sentences that establish *why the reader should care*. For applied/empirical work this is usually a concrete problem. For theoretical work it may be a general motivation—an open question, a gap between theory and practice, a unification opportunity, or the significance of a class of systems.
- **Gap or open question**: articulate what is missing or unknown. For work that is not solving a specific hard problem, frame this as: "No general framework exists for …", "It remains unclear whether …", or "Prior work handles X but not Y."
- **Approach overview**: give a brief, jargon-light description of what the paper does before the reader gets lost in details.
- **Contributions**: list 2–4 items. These should be *specific and verifiable*, but need not be falsifiable in the empirical sense. Acceptable forms include: a theorem and its proof, a type system and its metatheory, a language design and its semantics, a decision procedure and its complexity, case studies demonstrating applicability.
- **Evidence / illustration**: preview the strongest result early. For papers with experiments, this is a key number. For papers with only case studies or worked examples, name the case study and what it demonstrates. For purely theoretical papers, state the principal theorem informally.
- **Roadmap**: end with a brief "The rest of this paper is organised as…" sentence.
- Include a reference to a main figure or diagram if one is already present; for theory papers this may be a commutative diagram, reduction graph, or type-derivation example rather than a plot.
- Match the author's style from `writingStyle.json`.

---

#### 2d. General Enrichment

For all other sections:

- Add necessary explanatory sentences to make the text clearer and more complete—but **never introduce new research ideas** and **never alter existing research ideas**. Your additions complement; they do not innovate.
- Do **not** change the section structure (section headings and their order) without an explicit `@inst` in a $SPEC block. You may freely add or rearrange subsections.
- Do **not** modify the preamble (everything before `\begin{document}`) without explicit user instruction. If you must add a package or macro for correctness, add it silently and record every such change; report them all together in the Final Report (Step 4).

---

#### 2e. Progress Narration

As you work through each part, output a brief (1–2 sentence) plain-English explanation of what you are doing and why. This is intentional—the user wants to learn.

Example:
> "Enriching the second paragraph of §3 to clarify why the loss function uses a KL term rather than cross-entropy—the current draft states the choice without motivation."

---

#### 2f. Completion

After all sections are processed:

1. Save the enriched output `.tex` file.
2. Update `orchestrator.json`: set `stage_gate.refining_done = true`, `current_stage = "compiling"`.

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
>    - Fix each error in the output `.tex` (only fix compilation errors—do not alter content).
>    - Re-try. Repeat until successful or until 5 attempts are exhausted.
>    - If still failing after 5 attempts, report the remaining errors clearly to the user and halt.
> 4. On success:
>    - Report: "Compiled successfully. Output PDF: `<path>`."
>    - Update `orchestrator.json`: `parameters.compile_success = true`, `stage_gate.compile_done = true`, `current_stage = "done"`.
> 5. On final failure:
>    - Update `orchestrator.json`: `parameters.compile_success = false`, `current_stage = "error"`, `stage_notes = "<error summary>"`.
>    - Return the error summary.

The main agent waits for `stage_gate.compile_done == true` (or `current_stage == "error"`) before reporting to the user.

---

### Step 4: Final Report

Report to the user:

1. **Output file:** absolute path to the refined `.tex` file.
2. **Compilation status:** success with PDF path, or failure with error summary.
3. **Changes summary:** a brief list of what was changed and why (Abstract, Introduction, $SPEC replacements, any preamble additions).
4. If preamble was modified: explicitly list each change.
5. If any $SPEC were skipped or ambiguous: list them for the user's attention.

---

## Key Rules

- **Never modify the original `.tex` file.** All changes go to the output copy.
- **$SPEC take highest priority.** They override all other requirements when there is a conflict.
- **Ignore $SPEC in comments.** Use LaTeX comment-detection knowledge carefully.
- **Do not invent research content.** Enrichment means clarity and completeness, not new ideas.
- **Do not change section structure** unless an `@inst` $SPEC explicitly requests it.
- **Notify user of preamble changes** even if small.
- **Narrate briefly** as you work—the user wants to learn from each step.
- **Style first.** Load `writingStyle.json` before writing a single sentence; every generated sentence must reflect it.
- **All communication files** (`orchestrator.json`, `writingStyle.json`) live in `skills/paper-refine-zyr/com/`.
- **Large-file write fallback:** if the `Write` tool fails on size, silently retry with `Bash` (`cat << 'EOF' > file`) without prompting the user.
