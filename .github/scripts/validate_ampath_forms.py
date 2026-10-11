#!/usr/bin/env python3
import csv
import hashlib
import json
import re
import sys
import uuid
import zipfile
from collections import defaultdict
from pathlib import Path


FORM_DIR = Path("configuration/ampathforms")
OCL_DIR = Path("configuration/ocl")
ENCOUNTER_TYPES_PATH = Path(
    "configuration/encountertypes/encountertypes.csv"
)
AMPATH_FORMS_NAMESPACE_UUID = "794c4598-ab82-47ca-8d18-483a8abe6f4f"
REQUIRED_TOP_LEVEL = {
    "name",
    "uuid",
    "version",
    "published",
    "retired",
    "encounter",
    "processor",
    "referencedForms",
    "pages",
}
ID_RE = re.compile(r"^[a-z][A-Za-z0-9]*$")
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
SOURCE_URL_RE = re.compile(r"/sources/([^/]+)/")
STRING_LITERAL_RE = re.compile(
    r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`"
)
IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-z0-9_$])[A-Za-z_$][A-Za-z0-9_$]*(?![A-Za-z0-9_$])"
)

# These are the renderers registered by the AMPATH/O3 form engine and intentionally
# used by this package. Additions must be reviewed together with the frontend that
# provides the renderer.
SUPPORTED_RENDERINGS = {
    "checkbox",
    "date",
    "datetime",
    "group",
    "markdown",
    "number",
    "radio",
    "repeating",
    "select",
    "select-concept-answers",
    "text",
    "textarea",
    "ui-select-extended",
    "workspace-launcher",
}
NON_VALUE_RENDERINGS = {"group", "markdown", "repeating", "workspace-launcher"}
VALUE_RENDERINGS = SUPPORTED_RENDERINGS - NON_VALUE_RENDERINGS
EXPRESSION_KEYS = {
    "alertWhenExpression",
    "calculateExpression",
    "failsWhenExpression",
    "hideWhenExpression",
}
EXPRESSION_GLOBALS = {
    "Array",
    "Date",
    "Infinity",
    "JSON",
    "Math",
    "NaN",
    "Number",
    "Object",
    "String",
    "false",
    "instanceof",
    "let",
    "myValue",
    "new",
    "null",
    "this",
    "true",
    "typeof",
    "undefined",
    "var",
}


def ampath_persisted_form_uuid(name, version):
    """Match AmpathFormsLoader and Utils.generateUuidFromObjects in Initializer 2.13.0-sihsalus.1."""
    seed = f"{AMPATH_FORMS_NAMESPACE_UUID}_{name}_{version}".encode()
    return str(uuid.UUID(bytes=hashlib.md5(seed).digest(), version=3))


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def source_from_mapping(mapping, prefix, fallback=None):
    source = mapping.get(f"{prefix}_source_name")
    if source:
        return str(source)

    source_url = mapping.get(f"{prefix}_source_url") or ""
    match = SOURCE_URL_RE.search(source_url)
    if match:
        return match.group(1)
    return fallback


def concept_summary(concept):
    return (
        f"{concept['source']}/{concept['code']} "
        f"({concept.get('display_name') or 'unnamed concept'})"
    )


def load_ocl_bundle():
    errors = []
    active_by_external_id = defaultdict(list)
    retired_by_external_id = defaultdict(list)
    q_and_a_targets = defaultdict(set)

    for zip_path in sorted(OCL_DIR.glob("*.zip")):
        try:
            with zipfile.ZipFile(zip_path) as archive:
                export = json.loads(archive.read("export.json"))
        except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
            errors.append(f"{zip_path}: cannot load export.json: {error}")
            continue

        source = export.get("source") or {}
        source_id = source.get("id") if isinstance(source, dict) else None
        source_id = source_id or export.get("short_code")
        if not source_id:
            errors.append(f"{zip_path}: OCL export has no source identifier")
            continue
        source_id = str(source_id)

        for concept in export.get("concepts", []):
            external_id = concept.get("external_id")
            concept_code = concept.get("id")
            if not external_id or concept_code is None:
                continue
            indexed_concept = {
                "source": source_id,
                "code": str(concept_code),
                "external_id": str(external_id),
                "display_name": concept.get("display_name"),
                "concept_class": concept.get("concept_class"),
                "datatype": concept.get("datatype"),
                "zip_path": zip_path,
            }
            index = retired_by_external_id if concept.get("retired") else active_by_external_id
            index[str(external_id)].append(indexed_concept)

        for mapping in export.get("mappings", []):
            if mapping.get("retired") or mapping.get("map_type") != "Q-AND-A":
                continue

            from_source = source_from_mapping(mapping, "from", source_id)
            to_source = source_from_mapping(mapping, "to")
            from_code = mapping.get("from_concept_code")
            to_code = mapping.get("to_concept_code")
            if from_source and to_source and from_code is not None and to_code is not None:
                q_and_a_targets[(from_source, str(from_code))].add(
                    (to_source, str(to_code))
                )

    if not active_by_external_id:
        errors.append(f"{OCL_DIR}: no active bundled OCL concepts found")

    return {
        "active_by_external_id": active_by_external_id,
        "retired_by_external_id": retired_by_external_id,
        "q_and_a_targets": q_and_a_targets,
    }, errors


def load_encounter_types():
    errors = []
    encounter_types = defaultdict(list)
    try:
        with ENCOUNTER_TYPES_PATH.open(encoding="utf-8-sig", newline="") as handle:
            for row_number, row in enumerate(csv.DictReader(handle), start=2):
                retired = (row.get("Void/Retire") or "").strip().lower()
                if retired in {"1", "true", "yes"}:
                    continue
                uuid = (row.get("Uuid") or "").strip()
                name = (row.get("Name") or "").strip()
                if uuid:
                    encounter_types[uuid].append((name, row_number))
    except (OSError, csv.Error) as error:
        errors.append(f"{ENCOUNTER_TYPES_PATH}: cannot load encounter types: {error}")
    return encounter_types, errors


def resolve_concept(path, node, external_id, role, bundle, errors):
    node_id = node.get("id")
    label = node.get("label")
    location = f"question {node_id!r} ({label!r})"
    if not isinstance(external_id, str) or not external_id.strip():
        errors.append(f"{path}: {location} has invalid {role} concept UUID {external_id!r}")
        return None

    matches = bundle["active_by_external_id"].get(external_id, [])
    if len(matches) == 1:
        return matches[0]
    if not matches:
        retired = bundle["retired_by_external_id"].get(external_id, [])
        if retired:
            details = ", ".join(concept_summary(concept) for concept in retired)
            errors.append(
                f"{path}: {location} uses {role} concept UUID {external_id}, but it "
                f"resolves only to retired bundled concept(s): {details}"
            )
        else:
            errors.append(
                f"{path}: {location} uses {role} concept UUID {external_id}, but it "
                "does not resolve in the bundled OCL exports"
            )
        return None

    details = ", ".join(concept_summary(concept) for concept in matches)
    errors.append(
        f"{path}: {location} uses ambiguous {role} concept UUID {external_id}; "
        f"active matches: {details}"
    )
    return None


def orderable_concept_set_references(options):
    for item in walk(options):
        if "orderableConceptSet" not in item:
            continue
        value = item.get("orderableConceptSet")
        if isinstance(value, list):
            yield from value
        else:
            yield value


def expression_references(expression):
    """Return conservatively parseable local field references from a JS expression."""
    without_strings = STRING_LITERAL_RE.sub(" ", expression)
    references = set()
    for match in IDENTIFIER_RE.finditer(without_strings):
        identifier = match.group(0)
        if identifier in EXPRESSION_GLOBALS:
            continue

        # Function identifiers are provided by the form engine (isEmpty, calcBMI,
        # today, etc.), and property names after a dot are not local question IDs.
        suffix = without_strings[match.end() :]
        if re.match(r"\s*\(", suffix):
            continue
        prefix = without_strings[: match.start()].rstrip()
        if prefix.endswith("."):
            continue
        references.add(identifier)
    return references


def validate_encounter(path, data, encounter_types, errors):
    encounter_uuid = data.get("encounterType")
    encounter_name = data.get("encounter")
    if not isinstance(encounter_uuid, str) or not encounter_uuid:
        errors.append(f"{path}: invalid encounterType UUID {encounter_uuid!r}")
        return
    matches = encounter_types.get(encounter_uuid, [])
    if not matches:
        errors.append(
            f"{path}: encounterType {encounter_uuid!r} does not resolve to an active row "
            f"in {ENCOUNTER_TYPES_PATH}"
        )
        return
    if len(matches) > 1:
        rows = ", ".join(str(row_number) for _, row_number in matches)
        errors.append(
            f"{path}: encounterType {encounter_uuid!r} is ambiguous in "
            f"{ENCOUNTER_TYPES_PATH} (rows {rows})"
        )
        return

    expected_name, row_number = matches[0]
    if encounter_name != expected_name:
        errors.append(
            f"{path}: encounter display name {encounter_name!r} does not match "
            f"{ENCOUNTER_TYPES_PATH}:{row_number} name {expected_name!r} for "
            f"encounterType {encounter_uuid}"
        )


def validate_form(path, bundle, encounter_types):
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"], None
    if not isinstance(data, dict):
        return [f"{path}: top-level JSON value must be an object"], None

    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        errors.append(f"{path}: missing top-level keys: {', '.join(missing)}")

    for field in ("name", "version"):
        value = data.get(field)
        if field in data and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{path}: {field} must be a non-empty string")

    form_uuid = data.get("uuid")
    if form_uuid is not None and (
        not isinstance(form_uuid, str) or not UUID_RE.fullmatch(form_uuid)
    ):
        errors.append(f"{path}: invalid top-level form uuid: {form_uuid!r}")

    validate_encounter(path, data, encounter_types, errors)

    ids = set()
    nodes = list(walk(data))
    for node in nodes:
        node_id = node.get("id")
        if node_id is not None:
            if not isinstance(node_id, str) or not ID_RE.fullmatch(node_id):
                errors.append(f"{path}: invalid question id: {node_id!r}")
            elif node_id in ids:
                errors.append(f"{path}: duplicate question id: {node_id}")
            else:
                ids.add(node_id)

    for node in nodes:
        node_id = node.get("id")
        node_type = node.get("type")
        options = node.get("questionOptions")

        if "editable" in node:
            errors.append(
                f"{path}: question {node_id!r} uses unsupported 'editable'; "
                "O3 form-engine fields must use 'readonly'"
            )

        for expression_key in EXPRESSION_KEYS:
            expression = node.get(expression_key)
            if not isinstance(expression, str):
                continue
            missing_references = sorted(expression_references(expression) - ids)
            if missing_references:
                errors.append(
                    f"{path}: question {node_id!r} {expression_key} references missing "
                    f"local question id(s): {', '.join(missing_references)}"
                )

        if node_type in {"obs", "obsGroup"} and (
            not isinstance(options, dict) or not options.get("concept")
        ):
            errors.append(
                f"{path}: {node_type} {node_id!r} is missing questionOptions.concept"
            )

        if not isinstance(options, dict):
            continue

        rendering = options.get("rendering")
        if rendering is not None and (
            not isinstance(rendering, str) or rendering not in SUPPORTED_RENDERINGS
        ):
            errors.append(
                f"{path}: question {node_id!r} uses unsupported rendering "
                f"{rendering!r}; supported renderings are "
                f"{', '.join(sorted(SUPPORTED_RENDERINGS))}"
            )

        question_external_id = options.get("concept")
        question_concept = None
        if question_external_id:
            question_concept = resolve_concept(
                path, node, question_external_id, "question", bundle, errors
            )

        if question_concept and node_type == "obsGroup" and (
            question_concept.get("concept_class") != "ConvSet"
            or question_concept.get("datatype") != "N/A"
        ):
            errors.append(
                f"{path}: obsGroup {node_id!r} concept {question_external_id} "
                f"({concept_summary(question_concept)}) must be ConvSet/N/A; found "
                f"{question_concept.get('concept_class')}/{question_concept.get('datatype')}"
            )

        if (
            question_concept
            and isinstance(rendering, str)
            and rendering in VALUE_RENDERINGS
            and question_concept.get("datatype") == "N/A"
        ):
            errors.append(
                f"{path}: value question {node_id!r} with rendering {rendering!r} "
                f"uses N/A concept {question_external_id} "
                f"({concept_summary(question_concept)}); use a value-bearing question concept"
            )

        answers = options.get("answers") or []
        if not isinstance(answers, list):
            errors.append(f"{path}: question {node_id!r} has non-list questionOptions.answers")
            answers = []

        seen_answer_values = set()
        seen_answer_concepts = set()
        resolved_answers = []
        for answer in answers:
            if not isinstance(answer, dict):
                errors.append(
                    f"{path}: question {node_id!r} has invalid answer entry {answer!r}"
                )
                continue
            # Native O3 dropdowns also support literal values for Text observations.
            # A value is not a concept UUID and must never be resolved through OCL.
            if "value" in answer:
                value = answer["value"]
                if (not question_concept or question_concept.get("datatype") != "Text"
                        or rendering != "select" or answer.get("concept") is not None
                        or not isinstance(value, str) or not value.strip()
                        or not isinstance(answer.get("label"), str) or not answer["label"].strip()):
                    errors.append(f"{path}: question {node_id!r} has invalid literal Text select answer")
                elif value in seen_answer_values:
                    errors.append(f"{path}: question {node_id!r} repeats literal answer {value!r}")
                else:
                    seen_answer_values.add(value)
                continue
            answer_external_id = answer.get("concept")
            answer_label = answer.get("label")
            if not answer_external_id:
                errors.append(
                    f"{path}: question {node_id!r} has answer without concept: "
                    f"{answer_label!r}"
                )
                continue
            if isinstance(answer_external_id, str):
                if answer_external_id in seen_answer_concepts:
                    errors.append(
                        f"{path}: question {node_id!r} repeats answer concept "
                        f"{answer_external_id} ({answer_label!r})"
                    )
                else:
                    seen_answer_concepts.add(answer_external_id)
            if question_external_id and answer_external_id == question_external_id:
                errors.append(
                    f"{path}: question {node_id!r} uses its own question concept "
                    f"{question_external_id} as answer {answer_label!r}"
                )

            answer_concept = resolve_concept(
                path, node, answer_external_id, f"answer {answer_label!r}", bundle, errors
            )
            if answer_concept:
                resolved_answers.append((answer, answer_concept))

        if question_concept and resolved_answers:
            question_key = (question_concept["source"], question_concept["code"])
            mapped_targets = bundle["q_and_a_targets"].get(question_key, set())
            for answer, answer_concept in resolved_answers:
                answer_key = (answer_concept["source"], answer_concept["code"])
                if answer_key not in mapped_targets:
                    errors.append(
                        f"{path}: question {node_id!r} explicit answer "
                        f"{answer.get('label')!r} ({answer_concept['external_id']}, "
                        f"{concept_summary(answer_concept)}) is not an active Q-AND-A "
                        f"target of {question_external_id} "
                        f"({concept_summary(question_concept)})"
                    )

        for orderable_external_id in orderable_concept_set_references(options):
            resolve_concept(
                path,
                node,
                orderable_external_id,
                "orderableConceptSet",
                bundle,
                errors,
            )

    return errors, data


def main():
    paths = sorted(FORM_DIR.glob("*.json"))
    errors = []
    if not paths:
        errors.append(f"{FORM_DIR}: no AMPATH form JSON files found")
    bundle, bundle_errors = load_ocl_bundle()
    encounter_types, encounter_errors = load_encounter_types()
    errors.extend(bundle_errors)
    errors.extend(encounter_errors)

    form_uuids = {}
    persisted_uuids = {}
    concept_reference_count = 0
    for path in paths:
        form_errors, data = validate_form(path, bundle, encounter_types)
        errors.extend(form_errors)
        if data is None:
            continue

        for node in walk(data):
            options = node.get("questionOptions")
            if not isinstance(options, dict):
                continue
            if options.get("concept"):
                concept_reference_count += 1
            answers = options.get("answers") or []
            if isinstance(answers, list):
                concept_reference_count += sum(
                    1
                    for answer in answers
                    if isinstance(answer, dict) and answer.get("concept")
                )
            concept_reference_count += sum(
                1 for reference in orderable_concept_set_references(options) if reference
            )

        form_uuid = data.get("uuid")
        if isinstance(form_uuid, str) and UUID_RE.fullmatch(form_uuid):
            previous = form_uuids.get(form_uuid)
            if previous is not None:
                errors.append(
                    f"{path}: duplicate top-level form uuid {form_uuid} "
                    f"also used by {previous}"
                )
            else:
                form_uuids[form_uuid] = path

        name, version = data.get("name"), data.get("version")
        if all(isinstance(value, str) and value.strip() for value in (name, version)):
            persisted_uuid = ampath_persisted_form_uuid(name, version)
            previous = persisted_uuids.setdefault(persisted_uuid, path)
            if previous != path:
                errors.append(
                    f"{path}: duplicate persisted form UUID {persisted_uuid} "
                    f"for name={name!r}, version={version!r}, also used by {previous}; "
                    "Initializer would overwrite the same Form"
                )

    if errors:
        print("AMPATH form validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(paths)} AMPATH form JSON files and "
        f"{concept_reference_count} bundled concept references."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
