# ARIS Skills Guide

Complete guide to every skill: when to use it, how to invoke it, and what prerequisites it requires.

---

## Full Pipelines

### `/research-pipeline`
**When:** You want to go from a raw research direction all the way to a submitted paper in one shot.
**Prerequisites:** Internet access (web search), Codex MCP configured.
**Invoke:**
```
/research-pipeline "direction" — effort: balanced
```

### `/research-refine-pipeline`
**When:** You have a vague idea and want a focused proposal + detailed experiment roadmap in one step.
**Prerequisites:** Codex MCP.
**Invoke:**
```
/research-refine-pipeline "vague direction"
```

### `/patent-pipeline`
**When:** You have an invention and want complete filing documents (CN/US/EP).
**Prerequisites:** Codex MCP, internet access.
**Invoke:**
```
/patent-pipeline "invention description" — jurisdiction: CN
```

---

## Stage W1 — Literature & Idea Discovery

### `/research-lit`
**When:** You need to find related papers, write a literature review, or understand a research landscape.
**Prerequisites:** Internet access. Optional: Zotero MCP, Obsidian MCP for local library.
**Invoke:**
```
/research-lit "transformer-based anomaly detection"
```

### `/comm-lit-review`
**When:** Specifically for communications, wireless, 5G/6G, NTN, networking topics.
**Prerequisites:** Internet access.
**Invoke:**
```
/comm-lit-review "OFDM channel estimation with deep learning"
```

### `/arxiv`
**When:** You want to search or download papers from arXiv by keyword or ID.
**Prerequisites:** Internet access.
**Invoke:**
```
/arxiv "diffusion models survey"
/arxiv 2310.12345
```

### `/alphaxiv`
**When:** You have a single arXiv paper and want a quick LLM-optimized summary.
**Prerequisites:** Internet access.
**Invoke:**
```
/alphaxiv 2310.12345
/alphaxiv "https://arxiv.org/abs/2310.12345"
```

### `/deepxiv`
**When:** You want to read a paper section-by-section or access trending papers via DeepXiv.
**Prerequisites:** Internet access.
**Invoke:**
```
/deepxiv "attention mechanism"
```

### `/semantic-scholar`
**When:** You need published venue papers (IEEE, ACM, Springer) with citation counts — complements `/arxiv`.
**Prerequisites:** Internet access.
**Invoke:**
```
/semantic-scholar "federated learning personalization"
```

### `/exa-search`
**When:** You need broad web search beyond academic databases.
**Prerequisites:** Internet access.
**Invoke:**
```
/exa-search "state space models 2024 benchmarks"
```

### `/research-wiki`
**When:** You want a persistent knowledge base that accumulates papers, ideas, and claims across multiple sessions.
**Prerequisites:** Run `init` first; `python3 tools/research_wiki.py ingest_paper` available.
**Invoke:**
```
/research-wiki init
/research-wiki "ingest" — path: papers/
/research-wiki "query: what do we know about KV cache compression?"
```

### `/idea-discovery`
**When:** Starting a project from scratch — takes a direction and returns validated, pilot-tested research ideas.
**Prerequisites:** Internet access, Codex MCP. Outputs `idea-stage/IDEA_REPORT.md`.
**Invoke:**
```
/idea-discovery "efficient inference for LLMs"
```

### `/idea-discovery-robot`
**When:** Same as `/idea-discovery` but specialized for robotics and embodied AI.
**Prerequisites:** Internet access, Codex MCP.
**Invoke:**
```
/idea-discovery-robot "sim-to-real transfer for manipulation"
```

### `/idea-creator`
**When:** You already have a literature survey and just want to brainstorm and rank ideas — lighter than the full discovery pipeline.
**Prerequisites:** Internet access, Codex MCP.
**Invoke:**
```
/idea-creator "self-supervised learning for graphs"
```

### `/novelty-check`
**When:** You have a specific idea and want to verify no one has done it before publishing.
**Prerequisites:** Internet access, Codex MCP.
**Invoke:**
```
/novelty-check "using reversible networks for continual learning to avoid forgetting"
```

### `/research-refine`
**When:** You have a rough idea and want iterative GPT-5.4 review to sharpen it into a concrete method plan.
**Prerequisites:** Codex MCP.
**Invoke:**
```
/research-refine "my draft method: ..."
```

---

## Stage W1.5 — Experiment Planning & Execution

### `/experiment-plan`
**When:** After `/research-refine`, to convert a method plan into a claim-driven experiment roadmap with ablation matrix and compute budget.
**Prerequisites:** A refined proposal (from `/research-refine` or manually written).
**Invoke:**
```
/experiment-plan
```

### `/experiment-bridge`
**When:** You have `EXPERIMENT_PLAN.md` and want code implemented, deployed to GPU, and initial results collected automatically.
**Prerequisites:** `refine-logs/EXPERIMENT_PLAN.md` exists; GPU access configured.
**Invoke:**
```
/experiment-bridge
/experiment-bridge "EXPERIMENT_PLAN.md"
```

### `/run-experiment`
**When:** You need to launch a training job to local, remote SSH, Vast.ai, or Modal.
**Prerequisites:** GPU access (local, SSH key, Vast.ai API key, or Modal token).
**Invoke:**
```
/run-experiment "train ResNet on CIFAR-10 using configs/resnet.yaml"
```

### `/experiment-queue`
**When:** You have a multi-seed or grid-search sweep and want it managed as a job queue with OOM-aware retry.
**Prerequisites:** SSH access to compute; `run-experiment` and `monitor-experiment` skills installed.
**Invoke:**
```
/experiment-queue "grid: lr=[1e-3,1e-4], seeds=[0,1,2]"
```

### `/monitor-experiment`
**When:** An experiment is already running (via screen/tmux) and you want to check progress or collect results.
**Prerequisites:** SSH access configured.
**Invoke:**
```
/monitor-experiment "gpu-server-1"
/monitor-experiment "train_screen"
```

### `/training-check`
**When:** Training is running and you want WandB metrics polled to catch divergence or NaN early.
**Prerequisites:** WandB run active, Codex MCP.
**Invoke:**
```
/training-check "entity/project/run-id"
```

### `/dse-loop`
**When:** You're doing computer architecture / EDA and need automated design space exploration (parameter sweeps with objective convergence).
**Prerequisites:** The target program and parameter space defined.
**Invoke:**
```
/dse-loop "optimize cache size and associativity for gem5; minimize CPI; timeout 2h"
```

### `/serverless-modal`
**When:** You need a GPU instantly with zero setup — no SSH, no Docker.
**Prerequisites:** Modal CLI installed and authenticated (`modal token new`).
**Invoke:**
```
/serverless-modal "fine-tune LLaMA-3 on my dataset"
```

### `/vast-gpu`
**When:** You want to rent a cheap GPU from Vast.ai.
**Prerequisites:** Vast.ai account and API key set.
**Invoke:**
```
/vast-gpu "rent RTX 4090, 1x, run training for 6h"
```

### `/qzcli`
**When:** You're using the Qizhi (启智) platform (Chinese HPC).
**Prerequisites:** `qzcli` installed, platform credentials.
**Invoke:**
```
/qzcli "create job train.yaml"
/qzcli "list"
```

### `/system-profile`
**When:** You suspect a bottleneck (slow training, GPU underutilization, memory leak) and need a performance report.
**Prerequisites:** The target process running or a script to profile.
**Invoke:**
```
/system-profile "train.py"
/system-profile "gpu"
/system-profile "pid 1234"
```

---

## Stage W2 — Results Analysis & Review

### `/analyze-results`
**When:** Experiments finished and you need statistics, comparison tables, and insights from raw output files.
**Prerequisites:** Result files in `results/` or similar.
**Invoke:**
```
/analyze-results "results/run_*.json"
```

### `/result-to-claim`
**When:** After experiments, to judge what claims the results actually support vs. what's missing.
**Prerequisites:** Experiment results exist; Codex MCP.
**Invoke:**
```
/result-to-claim "we ran ablations on layer count, results in results/ablation.csv"
```

### `/ablation-planner`
**When:** Main results passed `result-to-claim` and you need to design ablations before paper submission.
**Prerequisites:** `result-to-claim` completed with `claim_supported=yes/partial`; Codex MCP.
**Invoke:**
```
/ablation-planner "our method uses attention + gating; need ablations for ICLR"
```

### `/experiment-audit`
**When:** You want to verify experiment integrity before claiming results (catches fake ground truth, score inflation, phantom numbers).
**Prerequisites:** Experiment directory with code and results; Codex MCP.
**Invoke:**
```
/experiment-audit "experiments/run_final/"
```

### `/research-review`
**When:** You want a deep external critical review of your research from GPT.
**Prerequisites:** Codex MCP; research artifacts (paper draft, results) present.
**Invoke:**
```
/research-review "our method and results"
```

### `/auto-review-loop`
**When:** You want autonomous iterative review-fix cycles until the research passes or hits max rounds.
**Prerequisites:** Codex MCP; research artifacts present.
**Invoke:**
```
/auto-review-loop "our method for efficient attention" — difficulty: hard
/auto-review-loop "our method for efficient attention" — difficulty: hard, reviewer: claude
```

### `/auto-review-loop-llm`
**When:** Same as `/auto-review-loop` but using any OpenAI-compatible LLM instead of Codex.
**Prerequisites:** `llm-chat` MCP server configured or env vars set.
**Invoke:**
```
/auto-review-loop-llm "our compression method"
```

### `/auto-review-loop-minimax`
**When:** Same as `/auto-review-loop` but using MiniMax API as reviewer.
**Prerequisites:** MiniMax API key configured.
**Invoke:**
```
/auto-review-loop-minimax "our method"
```

---

## Stage W3 — Paper Writing

### `/paper-plan`
**When:** You have results and want a structured outline (section plan, figure plan, citation scaffolding) before writing.
**Prerequisites:** `NARRATIVE_REPORT.md` or experiment results; Codex MCP.
**Invoke:**
```
/paper-plan "NARRATIVE_REPORT.md"
```

### `/paper-figure`
**When:** You have `PAPER_PLAN.md` and need matplotlib/seaborn plots and LaTeX tables generated from your data.
**Prerequisites:** `PAPER_PLAN.md` exists; result data files (JSON/CSV) in `results/`.
**Invoke:**
```
/paper-figure "PAPER_PLAN.md"
```

### `/figure-spec`
**When:** You need a deterministic architecture/workflow/pipeline diagram as editable SVG (no external API needed).
**Prerequisites:** None (fully local).
**Invoke:**
```
/figure-spec "three-stage pipeline: encoder → cross-attention → decoder"
```

### `/paper-illustration`
**When:** You want an AI-generated qualitative illustration (method concept, natural-style diagram) using Gemini.
**Prerequisites:** `GEMINI_API_KEY` env var set; Codex MCP.
**Invoke:**
```
/paper-illustration "contrastive learning with augmented views"
```

### `/paper-illustration-image2`
**When:** Same as above but uses Codex native image generation instead of Gemini (experimental).
**Prerequisites:** Codex app-server running and signed in; `codex-image2` MCP bridge registered (`claude mcp add`). Run `python3 tools/paper_illustration_image2.py preflight --workspace .` to verify.
**Invoke:**
```
/paper-illustration-image2 "contrastive learning with augmented views"
```

### `/mermaid-diagram`
**When:** You need a quick flowchart, sequence diagram, state machine, or ER diagram — free, no API key.
**Prerequisites:** None.
**Invoke:**
```
/mermaid-diagram "training loop: load data → forward → loss → backward → update"
```

### `/paper-write`
**When:** You have `PAPER_PLAN.md` and want LaTeX sections drafted one by one.
**Prerequisites:** `PAPER_PLAN.md`; Codex MCP; figures ready in `figures/`.
**Invoke:**
```
/paper-write "PAPER_PLAN.md"
```

### `/paper-compile`
**When:** LaTeX source is ready and you want to build the PDF with auto-error-fixing.
**Prerequisites:** LaTeX distribution installed (`latexmk`, `pdflatex`/`xelatex`).
**Invoke:**
```
/paper-compile "paper/"
```

### `/auto-paper-improvement-loop`
**When:** Paper compiled successfully and you want 2 rounds of GPT-5.4 review + automatic fixes.
**Prerequisites:** `paper/main.pdf` compiled; Codex MCP.
**Invoke:**
```
/auto-paper-improvement-loop "paper/"
```

### `/paper-writing`
**When:** You want all of the above (plan → figures → write → compile → improve) in one automated pipeline.
**Prerequisites:** `NARRATIVE_REPORT.md`; LaTeX installed; Codex MCP; optionally `GEMINI_API_KEY` for illustration mode.
**Invoke:**
```
/paper-writing "NARRATIVE_REPORT.md" — venue: ICLR
/paper-writing "NARRATIVE_REPORT.md" — venue: NeurIPS, illustration: gemini, effort: max
/paper-writing "NARRATIVE_REPORT.md" — venue: ICLR, reviewer: claude
```

### `/writing-systems-papers`
**When:** Writing a systems paper (OSDI, SOSP, ASPLOS, NSDI, EuroSys) — provides a venue-specific structural blueprint.
**Prerequisites:** Codex MCP; research results ready.
**Invoke:**
```
/writing-systems-papers "OSDI"
```

### `/claims-drafting`
**When:** You need to write patent claims from an invention disclosure.
**Prerequisites:** Invention disclosure document; Codex MCP.
**Invoke:**
```
/claims-drafting "invention_disclosure.md"
```

### `/formula-derivation`
**When:** You need to derive or organize mathematical formulas into a coherent theory line.
**Prerequisites:** Relevant equations or notes.
**Invoke:**
```
/formula-derivation "derive regret bound for our bandit algorithm"
```

### `/proof-writer`
**When:** You need to write a rigorous mathematical proof for a theorem, lemma, or proposition.
**Prerequisites:** Theorem statement and assumptions.
**Invoke:**
```
/proof-writer "prove convergence of our SGD variant under L-smoothness"
```

### `/overleaf-sync`
**When:** You want to sync your local `paper/` directory with an Overleaf project.
**Prerequisites:** Overleaf Premium account (Git bridge access); Git installed.
**Invoke:**
```
/overleaf-sync "setup abc123def456"   # first time
/overleaf-sync "push"
/overleaf-sync "pull"
```

---

## Audit & Submission Gate (W3 Gating)

### `/proof-checker`
**When:** Your paper contains theorems/lemmas/proofs and you need rigorous gap detection before submission.
**Prerequisites:** `paper/` with LaTeX proof environments; Codex MCP.
**Invoke:**
```
/proof-checker "paper/"
```

### `/paper-claim-audit`
**When:** Before submission, verify every number/comparison in the paper matches raw result files (catches cherry-picking and rounding inflation).
**Prerequisites:** `paper/` with LaTeX; raw result files in `results/` or `outputs/`; Codex MCP.
**Invoke:**
```
/paper-claim-audit "paper/"
```

### `/citation-audit`
**When:** Before submission, verify every `\cite{}` entry is real, correctly attributed, and used in the right context.
**Prerequisites:** `paper/references.bib`; internet access; Codex MCP.
**Invoke:**
```
/citation-audit "paper/"
```

---

## Stage W3 Post-Paper — Presentation

### `/paper-slides`
**When:** Paper is compiled and you need conference presentation slides (Beamer PDF + PPTX + speaker notes).
**Prerequisites:** `paper/main.pdf` compiled; Codex MCP.
**Invoke:**
```
/paper-slides "paper/" — talk-length: 15min
```

### `/paper-poster`
**When:** Paper is compiled and you need an A0/A1 conference poster (LaTeX + PPTX + SVG).
**Prerequisites:** `paper/main.pdf` compiled; Codex MCP.
**Invoke:**
```
/paper-poster "paper/" — venue: NeurIPS
```

---

## Stage W4 — Rebuttal

### `/rebuttal`
**When:** You received peer reviews and need to draft a structured rebuttal under venue word limits.
**Prerequisites:** Paper files + reviewer comments (text or PDF); Codex MCP.
**Invoke:**
```
/rebuttal "paper/ + reviews/R1.txt R2.txt R3.txt"
```

---

## Patent Track

### `/prior-art-search`
**When:** Before filing, search patent databases and academic literature for prior art.
**Prerequisites:** Internet access.
**Invoke:**
```
/prior-art-search "adaptive beamforming using neural networks"
```

### `/patent-novelty-check`
**When:** Assess whether an invention is novel and non-obvious for patentability.
**Prerequisites:** Internet access; Codex MCP.
**Invoke:**
```
/patent-novelty-check "invention_brief.md"
```

### `/invention-structuring`
**When:** You have a rough idea and need it formalized into a structured invention disclosure.
**Prerequisites:** Codex MCP.
**Invoke:**
```
/invention-structuring "rough idea description"
```

### `/specification-writing`
**When:** Claims are drafted and you need the full patent specification written.
**Prerequisites:** `claims.md` exists; Codex MCP.
**Invoke:**
```
/specification-writing "claims.md"
```

### `/embodiment-description`
**When:** Specification is drafted and you need detailed embodiment/implementation descriptions.
**Prerequisites:** Claims and specification files.
**Invoke:**
```
/embodiment-description "claims.md"
```

### `/figure-description`
**When:** You have patent figures and need formal drawing descriptions with reference numerals.
**Prerequisites:** Figure files in a directory.
**Invoke:**
```
/figure-description "figures/"
```

### `/jurisdiction-format`
**When:** Patent application is complete and you need it formatted for a specific jurisdiction's filing requirements.
**Prerequisites:** Complete patent documents; target jurisdiction (CN/US/EP).
**Invoke:**
```
/jurisdiction-format "patent/" — jurisdiction: US
```

### `/patent-review`
**When:** You want an external patent examiner perspective on your application before filing.
**Prerequisites:** Complete patent documents; Codex MCP.
**Invoke:**
```
/patent-review "patent/"
```

---

## Utility Skills

### `/grant-proposal`
**When:** Writing a funding application (KAKENHI, NSF, NSFC, ERC, DFG, etc.).
**Prerequisites:** Internet access; Codex MCP; research direction and literature ready.
**Invoke:**
```
/grant-proposal "efficient video understanding — NSFC"
```

### `/feishu-notify`
**When:** Sending a notification to Feishu/Lark (usually called automatically by other skills).
**Prerequisites:** Feishu webhook URL configured.
**Invoke:**
```
/feishu-notify "experiments finished, results in results/"
```

### `/meta-optimize`
**When:** You want to analyze ARIS usage logs and improve skill prompts/defaults based on past runs.
**Prerequisites:** `.aris/meta/events.jsonl` exists (requires meta-logging hook enabled).
**Invoke:**
```
/meta-optimize "all"
/meta-optimize "paper-writing"
```

### `/pixel-art`
**When:** You need a simple SVG pixel-art illustration for a README, doc, or slide.
**Prerequisites:** None.
**Invoke:**
```
/pixel-art "a robot reading a paper"
```

### `/system-profile`
**When:** Performance profiling of a script, GPU, or running process.
**Prerequisites:** Target script or process exists.
**Invoke:**
```
/system-profile "train.py"
/system-profile "gpu"
/system-profile "pid 1234"
```

---

## Quick Decision Tree

```
Starting research from scratch?
  → /idea-discovery or /research-pipeline (full end-to-end)

Have an idea, need a method plan?
  → /research-refine → /experiment-plan

Have a plan, need to run experiments?
  → /experiment-bridge (automated) or /run-experiment (manual)

Experiments done, need to write a paper?
  → /paper-writing "NARRATIVE_REPORT.md" (full pipeline)
     or individually: /paper-plan → /paper-figure → /paper-write → /paper-compile

Paper done, need to submit?
  → /proof-checker, /paper-claim-audit, /citation-audit (audit gates)
  → /paper-slides or /paper-poster for presentation

Got reviews back?
  → /rebuttal

Have an invention?
  → /patent-pipeline or individual patent skills
```
