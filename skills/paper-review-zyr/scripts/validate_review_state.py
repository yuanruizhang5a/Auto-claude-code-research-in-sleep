#!/usr/bin/env python3
"""Validate paper-review-zyr coordination files without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
JSON_FILES = {
    "orchestrator": "orchestrator.json",
    "writingStyle": "writingStyle.json",
    "reviewIssues": "reviewIssues.json",
    "reviewDraft": "reviewDraft.json",
    "paperEdits": "paperEdits.json",
    "compileResults": "compileResults.json",
}
STAGES = {
    "init",
    "style_learning",
    "template_prep",
    "review_import",
    "response_drafting",
    "user_checkpoint",
    "manuscript_revision",
    "spec_processing",
    "user_revision",
    "compiling",
    "auditing",
    "done",
    "error",
}
ISSUE_CATEGORIES = {
    "language_grammar",
    "clarity_expression",
    "notation_naming",
    "small_technical",
    "complex_scientific",
    "experiment_request",
    "citation_factual_verification",
    "editorial_policy",
    "other",
}
ISSUE_STATUSES = {
    "untriaged",
    "simple",
    "needs_user",
    "approved",
    "answered",
    "revised",
    "deferred",
    "blocked",
}
FINAL_ISSUE_STATUSES = {"answered", "revised", "deferred", "blocked"}
STYLE_KEYS = {
    "sentence_length",
    "paragraph_structure",
    "formality_level",
    "voice",
    "hedging_style",
    "transition_words",
    "jargon_tolerance",
    "first_person_use",
    "equation_explanation_style",
    "citation_placement",
    "figure_reference_style",
    "recurring_phrases",
    "tone",
}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class Validator:
    """Accumulate schema and cross-file validation diagnostics."""

    def __init__(self, com_dir: Path, required: set[str], final: bool) -> None:
        self.com_dir = com_dir
        self.required = required
        self.final = final
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []
        self.data: dict[str, dict[str, Any]] = {}

    def error(self, path: str, message: str) -> None:
        self.errors.append({"path": path, "message": message})

    def warn(self, path: str, message: str) -> None:
        self.warnings.append({"path": path, "message": message})

    def expect(self, condition: bool, path: str, message: str) -> bool:
        if not condition:
            self.error(path, message)
            return False
        return True

    def load_files(self) -> None:
        for logical_name, filename in JSON_FILES.items():
            path = self.com_dir / filename
            must_exist = (
                logical_name == "orchestrator"
                or logical_name in self.required
                or self.final
            )
            if not path.is_file():
                if must_exist:
                    self.error(filename, "required file is missing")
                else:
                    self.warn(filename, "file is not present yet")
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                self.error(filename, f"cannot parse UTF-8 JSON: {exc}")
                continue
            if not isinstance(value, dict):
                self.error(filename, "root must be a JSON object")
                continue
            self.data[logical_name] = value

    def validate(self) -> None:
        self.load_files()
        if "orchestrator" in self.data:
            self.validate_orchestrator(self.data["orchestrator"])
        if "writingStyle" in self.data:
            self.validate_writing_style(self.data["writingStyle"])
        if "reviewIssues" in self.data:
            self.validate_review_issues(self.data["reviewIssues"])
        if "reviewDraft" in self.data:
            self.validate_review_draft(self.data["reviewDraft"])
        if "paperEdits" in self.data:
            self.validate_paper_edits(self.data["paperEdits"])
        if "compileResults" in self.data:
            self.validate_compile_results(self.data["compileResults"])
        self.validate_cross_file_contracts()

    def validate_orchestrator(self, obj: dict[str, Any]) -> None:
        for key, expected_type in (
            ("timestamps", dict),
            ("current_stage", str),
            ("stage_notes", str),
            ("parameters", dict),
            ("stage_gate", dict),
            ("paper_review_zyr", dict),
        ):
            self.expect(
                isinstance(obj.get(key), expected_type),
                f"orchestrator.json.{key}",
                f"must be {expected_type.__name__}",
            )

        current_stage = obj.get("current_stage")
        if isinstance(current_stage, str):
            self.expect(
                current_stage in STAGES,
                "orchestrator.json.current_stage",
                f"unsupported stage {current_stage!r}",
            )

        timestamps = obj.get("timestamps")
        if isinstance(timestamps, dict):
            for key, value in timestamps.items():
                self.expect(
                    value is None or isinstance(value, str),
                    f"orchestrator.json.timestamps.{key}",
                    "must be a string or null",
                )

        gates = obj.get("stage_gate")
        if isinstance(gates, dict):
            for key, value in gates.items():
                self.expect(
                    isinstance(value, bool),
                    f"orchestrator.json.stage_gate.{key}",
                    "must be boolean",
                )

        parameters = obj.get("parameters")
        if isinstance(parameters, dict):
            self.validate_parameters(parameters)

        namespace = obj.get("paper_review_zyr")
        if isinstance(namespace, dict):
            self.validate_namespace(namespace, current_stage)

    def validate_parameters(self, params: dict[str, Any]) -> None:
        required_types = {
            "source_tex": str,
            "output_tex": str,
            "review_tex": str,
            "output_review_tex": str,
            "overwirte": bool,
            "raw_reviews": list,
            "writing_style_file": str,
            "phase": str,
            "include": list,
            "exclude": list,
            "no_compile": bool,
            "resume": bool,
            "restart": bool,
            "effort": str,
            "human_checkpoint": bool,
            "AUTO_PROCEED": bool,
        }
        for key, expected_type in required_types.items():
            self.expect(
                isinstance(params.get(key), expected_type),
                f"orchestrator.json.parameters.{key}",
                f"must be {expected_type.__name__}",
            )

        for key in ("style_materials", "style_materials_for_writing_style", "instructions"):
            self.expect(
                params.get(key) is None or isinstance(params.get(key), str),
                f"orchestrator.json.parameters.{key}",
                "must be a string or null",
            )

        self.expect(
            params.get("compile_success") is None
            or isinstance(params.get("compile_success"), bool),
            "orchestrator.json.parameters.compile_success",
            "must be boolean or null",
        )
        self.expect(
            params.get("phase") in {"normal", "revise"},
            "orchestrator.json.parameters.phase",
            "must be 'normal' or 'revise'",
        )
        self.expect(
            params.get("effort") in {"lite", "balanced", "max", "beast"},
            "orchestrator.json.parameters.effort",
            "must be lite, balanced, max, or beast",
        )
        for key in ("raw_reviews", "include", "exclude"):
            value = params.get(key)
            if isinstance(value, list):
                self.expect(
                    all(isinstance(item, str) for item in value),
                    f"orchestrator.json.parameters.{key}",
                    "must contain only strings",
                )
        source_output_pairs = (
            ("source_tex", "output_tex"),
            ("review_tex", "output_review_tex"),
        )
        for source_key, output_key in source_output_pairs:
            source = params.get(source_key)
            output = params.get(output_key)
            if not isinstance(source, str) or not isinstance(output, str):
                continue
            source_path = Path(source)
            output_path = Path(output)
            self.expect(
                source_path.suffix.lower() == ".tex",
                f"orchestrator.json.parameters.{source_key}",
                "must be a .tex path",
            )
            self.expect(
                output_path.suffix.lower() == ".tex",
                f"orchestrator.json.parameters.{output_key}",
                "must be a .tex path",
            )
            if params.get("overwirte") is True:
                self.expect(
                    source_path == output_path,
                    f"orchestrator.json.parameters.{output_key}",
                    f"must equal {source_key} when overwirte is true",
                )
            elif params.get("overwirte") is False:
                self.expect(
                    source_path != output_path,
                    f"orchestrator.json.parameters.{output_key}",
                    f"must differ from {source_key} when overwirte is false",
                )
                self.expect(
                    source_path.parent == output_path.parent,
                    f"orchestrator.json.parameters.{output_key}",
                    "must be a sibling of its source",
                )
                self.expect(
                    re.search(r"(?:_r[1-9][0-9]*)+\.tex$", output_path.name) is not None,
                    f"orchestrator.json.parameters.{output_key}",
                    "must end in a positive `_rN.tex` revision suffix",
                )
        if params.get("phase") == "revise":
            self.expect(
                isinstance(params.get("instructions"), str)
                and bool(params["instructions"].strip()),
                "orchestrator.json.parameters.instructions",
                "must be non-empty in revise phase",
            )

    def validate_namespace(
        self, namespace: dict[str, Any], top_level_stage: Any
    ) -> None:
        self.expect(
            namespace.get("schema_version") == SCHEMA_VERSION,
            "orchestrator.json.paper_review_zyr.schema_version",
            f"must equal {SCHEMA_VERSION}",
        )
        for key in ("run_id", "invocation_fingerprint", "phase", "execution_mode", "current_stage"):
            self.expect(
                isinstance(namespace.get(key), str) and bool(namespace[key]),
                f"orchestrator.json.paper_review_zyr.{key}",
                "must be a non-empty string",
            )
        self.expect(
            namespace.get("phase") in {"normal", "revise"},
            "orchestrator.json.paper_review_zyr.phase",
            "must be 'normal' or 'revise'",
        )
        self.expect(
            namespace.get("execution_mode") in {"delegated", "sequential", "mixed"},
            "orchestrator.json.paper_review_zyr.execution_mode",
            "must be delegated, sequential, or mixed",
        )
        ns_stage = namespace.get("current_stage")
        self.expect(
            ns_stage in STAGES,
            "orchestrator.json.paper_review_zyr.current_stage",
            f"unsupported stage {ns_stage!r}",
        )
        self.expect(
            top_level_stage == ns_stage,
            "orchestrator.json.current_stage",
            "must match paper_review_zyr.current_stage",
        )

        for key in ("ordered_stages", "pending_user_decisions", "warnings", "unmatched_selectors", "unresolved_items", "history"):
            self.expect(
                isinstance(namespace.get(key), list),
                f"orchestrator.json.paper_review_zyr.{key}",
                "must be a list",
            )
        for key in ("completed_at", "input_fingerprints", "files", "compilation"):
            self.expect(
                isinstance(namespace.get(key), dict),
                f"orchestrator.json.paper_review_zyr.{key}",
                "must be an object",
            )

        ordered = namespace.get("ordered_stages")
        if isinstance(ordered, list):
            self.expect(
                all(isinstance(item, str) and item in STAGES for item in ordered),
                "orchestrator.json.paper_review_zyr.ordered_stages",
                "contains an unsupported stage",
            )
            self.expect(
                len(ordered) == len(set(ordered)),
                "orchestrator.json.paper_review_zyr.ordered_stages",
                "must not contain duplicates",
            )

        fingerprint = namespace.get("invocation_fingerprint")
        if isinstance(fingerprint, str):
            self.expect(
                bool(SHA256_RE.fullmatch(fingerprint)),
                "orchestrator.json.paper_review_zyr.invocation_fingerprint",
                "must be a 64-character SHA-256 hex digest",
            )
        fingerprints = namespace.get("input_fingerprints")
        if isinstance(fingerprints, dict):
            for key, value in fingerprints.items():
                self.expect(
                    value is None
                    or (isinstance(value, str) and bool(SHA256_RE.fullmatch(value))),
                    f"orchestrator.json.paper_review_zyr.input_fingerprints.{key}",
                    "must be a SHA-256 hex digest or null",
                )

        if self.final:
            self.expect(
                ns_stage in {"auditing", "done"},
                "orchestrator.json.paper_review_zyr.current_stage",
                "final validation is allowed only in auditing or done stage",
            )
            self.expect(
                namespace.get("pending_user_decisions") == [],
                "orchestrator.json.paper_review_zyr.pending_user_decisions",
                "must be empty for final validation",
            )

    def validate_writing_style(self, obj: dict[str, Any]) -> None:
        must_be_complete = self.final or "writingStyle" in self.required
        if not obj:
            if must_be_complete:
                self.error("writingStyle.json", "must be non-empty")
            else:
                self.warn("writingStyle.json", "style analysis is not populated yet")
            return
        for key, value in obj.items():
            if not isinstance(value, dict):
                self.error(f"writingStyle.json.{key}", "must be an object")
                continue
            for field in ("value", "description"):
                self.expect(
                    isinstance(value.get(field), str) and bool(value[field].strip()),
                    f"writingStyle.json.{key}.{field}",
                    "must be a non-empty string",
                )
        missing = sorted(STYLE_KEYS - set(obj))
        if missing:
            message = f"missing required style entries: {', '.join(missing)}"
            if must_be_complete:
                self.error("writingStyle.json", message)
            else:
                self.warn("writingStyle.json", message)

    def validate_review_issues(self, obj: dict[str, Any]) -> None:
        self._schema_and_lists(obj, "reviewIssues.json", ("sources", "issues"))
        sources = obj.get("sources")
        issues = obj.get("issues")
        if not isinstance(sources, list) or not isinstance(issues, list):
            return

        source_ids: set[str] = set()
        source_issue_ids: list[str] = []
        for index, source in enumerate(sources):
            prefix = f"reviewIssues.json.sources[{index}]"
            if not isinstance(source, dict):
                self.error(prefix, "must be an object")
                continue
            for field in ("source_id", "path", "sha256", "reviewer_id"):
                self.expect(
                    isinstance(source.get(field), str) and bool(source[field]),
                    f"{prefix}.{field}",
                    "must be a non-empty string",
                )
            self.expect(
                isinstance(source.get("order"), int) and source["order"] >= 1,
                f"{prefix}.order",
                "must be a positive integer",
            )
            issue_ids = source.get("issue_ids")
            self.expect(
                isinstance(issue_ids, list)
                and all(isinstance(item, str) and item for item in issue_ids),
                f"{prefix}.issue_ids",
                "must be a list of non-empty strings",
            )
            if isinstance(issue_ids, list):
                source_issue_ids.extend(item for item in issue_ids if isinstance(item, str))
            source_id = source.get("source_id")
            if isinstance(source_id, str):
                self.expect(source_id not in source_ids, f"{prefix}.source_id", "duplicate source ID")
                source_ids.add(source_id)
            sha256 = source.get("sha256")
            if isinstance(sha256, str):
                self.expect(bool(SHA256_RE.fullmatch(sha256)), f"{prefix}.sha256", "must be a SHA-256 hex digest")

        issue_ids: set[str] = set()
        issue_source_ids: dict[str, str] = {}
        for index, issue in enumerate(issues):
            prefix = f"reviewIssues.json.issues[{index}]"
            if not isinstance(issue, dict):
                self.error(prefix, "must be an object")
                continue
            for field in ("issue_id", "reviewer_id", "source_id", "verbatim_text", "source_location", "latex_text", "category", "complexity", "segmentation_status", "status", "disposition"):
                self.expect(
                    isinstance(issue.get(field), str) and bool(issue[field]),
                    f"{prefix}.{field}",
                    "must be a non-empty string",
                )
            self.expect(
                isinstance(issue.get("original_order"), int) and issue["original_order"] >= 1,
                f"{prefix}.original_order",
                "must be a positive integer",
            )
            for field in ("evidence_locations", "linked_edit_ids"):
                value = issue.get(field)
                self.expect(
                    isinstance(value, list) and all(isinstance(item, str) for item in value),
                    f"{prefix}.{field}",
                    "must be a list of strings",
                )
            self.expect(
                issue.get("category") in ISSUE_CATEGORIES,
                f"{prefix}.category",
                "unsupported category",
            )
            self.expect(
                issue.get("complexity") in {"simple", "complex", "undetermined"},
                f"{prefix}.complexity",
                "must be simple, complex, or undetermined",
            )
            self.expect(
                issue.get("segmentation_status") in {"confirmed", "needs_user"},
                f"{prefix}.segmentation_status",
                "must be confirmed or needs_user",
            )
            self.expect(
                issue.get("status") in ISSUE_STATUSES,
                f"{prefix}.status",
                "unsupported issue status",
            )
            proposed_answer = issue.get("proposed_answer")
            self.expect(
                proposed_answer is None or isinstance(proposed_answer, str),
                f"{prefix}.proposed_answer",
                "must be a string or null",
            )
            self.expect(
                issue.get("user_decision") is None or isinstance(issue.get("user_decision"), dict),
                f"{prefix}.user_decision",
                "must be an object or null",
            )

            issue_id = issue.get("issue_id")
            if isinstance(issue_id, str):
                self.expect(issue_id not in issue_ids, f"{prefix}.issue_id", "duplicate issue ID")
                issue_ids.add(issue_id)
                if isinstance(issue.get("source_id"), str):
                    issue_source_ids[issue_id] = issue["source_id"]
            self.expect(
                issue.get("source_id") in source_ids,
                f"{prefix}.source_id",
                "does not reference a known source",
            )

            status = issue.get("status")
            if status in {"answered", "revised"}:
                self.expect(
                    isinstance(proposed_answer, str)
                    and proposed_answer.count("\\ranswer{") == 1,
                    f"{prefix}.proposed_answer",
                    "answered/revised issue must contain exactly one outer \\ranswer{",
                )
            if issue.get("complexity") in {"complex", "undetermined"} and status in {"approved", "answered", "revised", "deferred"}:
                self.expect(
                    isinstance(issue.get("user_decision"), dict),
                    f"{prefix}.user_decision",
                    "complex/undetermined disposition requires a saved user decision",
                )
            if self.final:
                self.expect(
                    status in FINAL_ISSUE_STATUSES,
                    f"{prefix}.status",
                    "must be terminal for final validation",
                )

        self.expect(
            len(source_issue_ids) == len(set(source_issue_ids)),
            "reviewIssues.json.sources[*].issue_ids",
            "an issue is assigned more than once across sources",
        )
        self.expect(
            set(source_issue_ids) == issue_ids,
            "reviewIssues.json",
            "source issue_ids must cover all and only ledger issues",
        )

    def validate_review_draft(self, obj: dict[str, Any]) -> None:
        self._schema_and_lists(obj, "reviewDraft.json", ("support_files", "sections", "rendered_issue_ids"))
        for key in ("review_path", "template_path", "template_sha256", "status", "introduction"):
            self.expect(
                isinstance(obj.get(key), str),
                f"reviewDraft.json.{key}",
                "must be a string",
            )
        self.expect(
            isinstance(obj.get("created_from_default_template"), bool),
            "reviewDraft.json.created_from_default_template",
            "must be boolean",
        )
        self.expect(
            obj.get("status") in {"pending", "prepared", "rendered", "blocked"},
            "reviewDraft.json.status",
            "unsupported status",
        )
        sha256 = obj.get("template_sha256")
        if isinstance(sha256, str) and sha256:
            self.expect(bool(SHA256_RE.fullmatch(sha256)), "reviewDraft.json.template_sha256", "must be a SHA-256 hex digest")

        section_issue_ids: list[str] = []
        sections = obj.get("sections")
        if isinstance(sections, list):
            for index, section in enumerate(sections):
                prefix = f"reviewDraft.json.sections[{index}]"
                if not isinstance(section, dict):
                    self.error(prefix, "must be an object")
                    continue
                self.expect(
                    isinstance(section.get("reviewer_id"), str) and bool(section["reviewer_id"]),
                    f"{prefix}.reviewer_id",
                    "must be a non-empty string",
                )
                ids = section.get("issue_ids")
                self.expect(
                    isinstance(ids, list) and all(isinstance(item, str) for item in ids),
                    f"{prefix}.issue_ids",
                    "must be a list of strings",
                )
                if isinstance(ids, list):
                    section_issue_ids.extend(item for item in ids if isinstance(item, str))
        self.expect(
            len(section_issue_ids) == len(set(section_issue_ids)),
            "reviewDraft.json.sections[*].issue_ids",
            "an issue appears in more than one response section",
        )

    def validate_paper_edits(self, obj: dict[str, Any]) -> None:
        self._schema_and_lists(obj, "paperEdits.json", ("edits", "specs"))
        edits = obj.get("edits")
        specs = obj.get("specs")
        if not isinstance(edits, list) or not isinstance(specs, list):
            return
        edit_ids: set[str] = set()
        for index, edit in enumerate(edits):
            prefix = f"paperEdits.json.edits[{index}]"
            if not isinstance(edit, dict):
                self.error(prefix, "must be an object")
                continue
            for field in ("edit_id", "file", "structural_location", "original_text", "revised_text", "rendered_annotation", "rationale", "annotation_status", "application_status", "compilation_status"):
                self.expect(isinstance(edit.get(field), str), f"{prefix}.{field}", "must be a string")
            for field in ("linked_issue_ids", "linked_spec_ids", "evidence_locations"):
                value = edit.get(field)
                self.expect(
                    isinstance(value, list) and all(isinstance(item, str) for item in value),
                    f"{prefix}.{field}",
                    "must be a list of strings",
                )
            self.expect(edit.get("annotation_status") in {"pending", "applied", "verified", "not_applicable"}, f"{prefix}.annotation_status", "unsupported annotation status")
            self.expect(edit.get("application_status") in {"pending", "applied", "skipped", "blocked"}, f"{prefix}.application_status", "unsupported application status")
            self.expect(edit.get("compilation_status") in {"pending", "success", "failed", "skipped"}, f"{prefix}.compilation_status", "unsupported compilation status")
            edit_id = edit.get("edit_id")
            if isinstance(edit_id, str):
                self.expect(edit_id not in edit_ids, f"{prefix}.edit_id", "duplicate edit ID")
                edit_ids.add(edit_id)
            if edit.get("application_status") == "applied":
                rendered = edit.get("rendered_annotation", "")
                original = edit.get("original_text", "")
                revised = edit.get("revised_text", "")
                if original:
                    self.expect("\\ORI" in rendered and "\\EORI" in rendered, f"{prefix}.rendered_annotation", "original text requires ORI/EORI markers")
                if revised:
                    self.expect("\\MO" in rendered and "\\EMO" in rendered, f"{prefix}.rendered_annotation", "revised/inserted text requires MO/EMO markers")

        spec_ids: set[str] = set()
        for index, spec in enumerate(specs):
            prefix = f"paperEdits.json.specs[{index}]"
            if not isinstance(spec, dict):
                self.error(prefix, "must be an object")
                continue
            for field in ("spec_id", "file", "structural_location", "raw_text", "scope_status", "disposition"):
                self.expect(isinstance(spec.get(field), str) and bool(spec[field]), f"{prefix}.{field}", "must be a non-empty string")
            for field in ("types", "linked_edit_ids"):
                value = spec.get(field)
                self.expect(isinstance(value, list) and all(isinstance(item, str) for item in value), f"{prefix}.{field}", "must be a list of strings")
            self.expect(spec.get("scope_status") in {"in_scope", "out_of_scope", "conflict"}, f"{prefix}.scope_status", "unsupported scope status")
            self.expect(spec.get("disposition") in {"pending", "unchanged", "revised", "deferred", "blocked", "out_of_scope"}, f"{prefix}.disposition", "unsupported disposition")
            spec_id = spec.get("spec_id")
            if isinstance(spec_id, str):
                self.expect(spec_id not in spec_ids, f"{prefix}.spec_id", "duplicate spec ID")
                spec_ids.add(spec_id)
            for edit_id in spec.get("linked_edit_ids", []) if isinstance(spec.get("linked_edit_ids"), list) else []:
                self.expect(edit_id in edit_ids, f"{prefix}.linked_edit_ids", f"unknown edit ID {edit_id!r}")
            if self.final:
                self.expect(spec.get("disposition") != "pending", f"{prefix}.disposition", "must not be pending for final validation")

    def validate_compile_results(self, obj: dict[str, Any]) -> None:
        self._schema_and_lists(obj, "compileResults.json", ("documents",))
        documents = obj.get("documents")
        if not isinstance(documents, list):
            return
        kinds: set[str] = set()
        for index, document in enumerate(documents):
            prefix = f"compileResults.json.documents[{index}]"
            if not isinstance(document, dict):
                self.error(prefix, "must be an object")
                continue
            for field in ("kind", "source_tex", "document_root", "status"):
                self.expect(isinstance(document.get(field), str) and bool(document[field]), f"{prefix}.{field}", "must be a non-empty string")
            self.expect(document.get("pdf_path") is None or isinstance(document.get("pdf_path"), str), f"{prefix}.pdf_path", "must be a string or null")
            self.expect(isinstance(document.get("attempts"), int) and 0 <= document["attempts"] <= 5, f"{prefix}.attempts", "must be an integer from 0 to 5")
            for field in ("warnings", "errors", "fixes"):
                self.expect(isinstance(document.get(field), list), f"{prefix}.{field}", "must be a list")
            self.expect(document.get("kind") in {"paper", "review"}, f"{prefix}.kind", "must be paper or review")
            self.expect(document.get("status") in {"pending", "skipped", "success", "failed"}, f"{prefix}.status", "unsupported status")
            kind = document.get("kind")
            if isinstance(kind, str):
                self.expect(kind not in kinds, f"{prefix}.kind", "duplicate document kind")
                kinds.add(kind)
            if document.get("status") == "success":
                self.expect(isinstance(document.get("pdf_path"), str) and bool(document["pdf_path"]), f"{prefix}.pdf_path", "successful compilation requires a PDF path")
        if self.final:
            self.expect(kinds == {"paper", "review"}, "compileResults.json.documents", "must contain paper and review records")
            for index, document in enumerate(documents):
                if isinstance(document, dict):
                    self.expect(document.get("status") != "pending", f"compileResults.json.documents[{index}].status", "must not be pending for final validation")

    def validate_cross_file_contracts(self) -> None:
        issues_obj = self.data.get("reviewIssues", {})
        draft_obj = self.data.get("reviewDraft", {})
        edits_obj = self.data.get("paperEdits", {})
        orchestrator = self.data.get("orchestrator", {})
        compile_obj = self.data.get("compileResults", {})

        issues = issues_obj.get("issues") if isinstance(issues_obj, dict) else None
        issue_ids = {
            issue.get("issue_id")
            for issue in issues
            if isinstance(issues, list) and isinstance(issue, dict) and isinstance(issue.get("issue_id"), str)
        } if isinstance(issues, list) else set()

        edits = edits_obj.get("edits") if isinstance(edits_obj, dict) else None
        edit_ids = {
            edit.get("edit_id")
            for edit in edits
            if isinstance(edits, list) and isinstance(edit, dict) and isinstance(edit.get("edit_id"), str)
        } if isinstance(edits, list) else set()

        if isinstance(issues, list):
            for index, issue in enumerate(issues):
                if not isinstance(issue, dict):
                    continue
                for edit_id in issue.get("linked_edit_ids", []) if isinstance(issue.get("linked_edit_ids"), list) else []:
                    self.expect(edit_id in edit_ids, f"reviewIssues.json.issues[{index}].linked_edit_ids", f"unknown edit ID {edit_id!r}")

        if isinstance(edits, list):
            for index, edit in enumerate(edits):
                if not isinstance(edit, dict):
                    continue
                for issue_id in edit.get("linked_issue_ids", []) if isinstance(edit.get("linked_issue_ids"), list) else []:
                    self.expect(issue_id in issue_ids, f"paperEdits.json.edits[{index}].linked_issue_ids", f"unknown issue ID {issue_id!r}")

        sections = draft_obj.get("sections") if isinstance(draft_obj, dict) else None
        section_ids: list[str] = []
        if isinstance(sections, list):
            for section in sections:
                if isinstance(section, dict) and isinstance(section.get("issue_ids"), list):
                    section_ids.extend(item for item in section["issue_ids"] if isinstance(item, str))
        rendered_ids = draft_obj.get("rendered_issue_ids") if isinstance(draft_obj, dict) else None
        if self.final:
            self.expect(set(section_ids) == issue_ids, "reviewDraft.json.sections", "must cover all and only ledger issues")
            self.expect(isinstance(rendered_ids, list) and set(rendered_ids) == issue_ids, "reviewDraft.json.rendered_issue_ids", "must cover all and only ledger issues")
            self.expect(draft_obj.get("status") == "rendered", "reviewDraft.json.status", "must be rendered for final validation")

        params = orchestrator.get("parameters") if isinstance(orchestrator, dict) else None
        documents = compile_obj.get("documents") if isinstance(compile_obj, dict) else None
        if isinstance(params, dict):
            output_tex = params.get("output_tex")
            output_review_tex = params.get("output_review_tex")
            if isinstance(draft_obj, dict) and draft_obj:
                self.expect(
                    draft_obj.get("review_path") == output_review_tex,
                    "reviewDraft.json.review_path",
                    "must equal orchestrator output_review_tex",
                )
            if isinstance(edits, list):
                for index, edit in enumerate(edits):
                    if isinstance(edit, dict):
                        self.expect(
                            edit.get("file") == output_tex,
                            f"paperEdits.json.edits[{index}].file",
                            "must equal orchestrator output_tex",
                        )
            specs = edits_obj.get("specs") if isinstance(edits_obj, dict) else None
            if isinstance(specs, list):
                for index, spec in enumerate(specs):
                    if isinstance(spec, dict):
                        self.expect(
                            spec.get("file") == output_tex,
                            f"paperEdits.json.specs[{index}].file",
                            "must equal orchestrator output_tex",
                        )
            if isinstance(documents, list):
                expected_outputs = {
                    "paper": output_tex,
                    "review": output_review_tex,
                }
                for index, document in enumerate(documents):
                    if not isinstance(document, dict):
                        continue
                    kind = document.get("kind")
                    if kind in expected_outputs:
                        self.expect(
                            document.get("source_tex") == expected_outputs[kind],
                            f"compileResults.json.documents[{index}].source_tex",
                            f"must equal the resolved {kind} output path",
                        )
        if isinstance(params, dict) and isinstance(documents, list):
            statuses = [doc.get("status") for doc in documents if isinstance(doc, dict)]
            if params.get("no_compile") is True:
                self.expect(all(status == "skipped" for status in statuses), "compileResults.json.documents", "all documents must be skipped when no_compile is true")
                self.expect(params.get("compile_success") is None, "orchestrator.json.parameters.compile_success", "must remain null when compilation is skipped")
            elif self.final and statuses:
                expected = all(status == "success" for status in statuses)
                self.expect(params.get("compile_success") is expected, "orchestrator.json.parameters.compile_success", "must summarize independent document statuses")

    def _schema_and_lists(
        self, obj: dict[str, Any], filename: str, list_fields: tuple[str, ...]
    ) -> None:
        self.expect(obj.get("schema_version") == SCHEMA_VERSION, f"{filename}.schema_version", f"must equal {SCHEMA_VERSION}")
        for field in list_fields:
            self.expect(isinstance(obj.get(field), list), f"{filename}.{field}", "must be a list")


def parse_required(raw: str) -> set[str]:
    """Parse and normalize logical communication-file names."""
    if not raw.strip():
        return set()
    aliases = {name.lower(): name for name in JSON_FILES}
    aliases.update({filename.lower(): name for name, filename in JSON_FILES.items()})
    result: set[str] = set()
    for item in raw.split(","):
        key = item.strip().lower()
        if not key:
            continue
        if key not in aliases:
            choices = ", ".join(JSON_FILES)
            raise argparse.ArgumentTypeError(f"unknown required file {item!r}; choose from {choices}")
        result.add(aliases[key])
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--com-dir", type=Path, default=Path("./com"), help="coordination directory (default: ./com)")
    parser.add_argument("--require", default="", help="comma-separated logical files required for this handoff")
    parser.add_argument("--final", action="store_true", help="enforce terminal coverage and compilation checks")
    parser.add_argument("--json", action="store_true", dest="json_output", help="emit machine-readable diagnostics")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        required = parse_required(args.require)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    validator = Validator(args.com_dir.resolve(), required, args.final)
    validator.validate()
    valid = not validator.errors
    result = {
        "valid": valid,
        "com_dir": str(validator.com_dir),
        "final": args.final,
        "errors": validator.errors,
        "warnings": validator.warnings,
    }
    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        label = "VALID" if valid else "INVALID"
        print(f"{label}: {validator.com_dir}")
        for item in validator.errors:
            print(f"ERROR {item['path']}: {item['message']}")
        for item in validator.warnings:
            print(f"WARN  {item['path']}: {item['message']}")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
