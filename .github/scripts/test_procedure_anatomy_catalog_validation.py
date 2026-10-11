#!/usr/bin/env python3
import copy
import csv
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


sys.dont_write_bytecode = True
SCRIPT_PATH = Path(__file__).with_name("validate_ocl_exports.py")
SPEC = importlib.util.spec_from_file_location("validate_ocl_exports", SCRIPT_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ProcedureAnatomyCatalogValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shipped_exports = {}
        for path in VALIDATOR.OCL_DIR.glob("*.zip"):
            with zipfile.ZipFile(path) as archive:
                cls.shipped_exports[path] = json.loads(archive.read("export.json"))

    def setUp(self):
        self.exports = copy.deepcopy(self.shipped_exports)
        self.concepts = self.exports[VALIDATOR.PROCEDURE_ANATOMY_CONCEPTS_EXPORT]["concepts"]
        self.mappings = self.exports[VALIDATOR.PROCEDURE_ANATOMY_MAPPINGS_EXPORT]["mappings"]
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fhir_sources_path = Path(temporary.name) / "fhirconceptsources.csv"
        self.fhir_sources_path.write_bytes(
            Path("configuration/fhirconceptsources/fhirconceptsources.csv").read_bytes()
        )
        patcher = mock.patch.object(
            VALIDATOR, "FHIR_CONCEPT_SOURCES_PATH", self.fhir_sources_path
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def fhir_source_rows(self):
        with self.fhir_sources_path.open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    def write_fhir_source_rows(self, rows):
        with self.fhir_sources_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def errors(self):
        records = [(path, export.get("short_code"), concept)
                   for path, export in self.exports.items()
                   for concept in export.get("concepts", [])]
        errors = []
        VALIDATOR.validate_procedure_anatomy_terminology(self.exports, records, errors)
        return errors

    def assert_rejected(self, diagnostic):
        errors = self.errors()
        self.assertTrue(any(diagnostic in error for error in errors), errors)

    def test_accepts_shipped_released_catalog_and_historical_reuse(self):
        self.assertEqual([], self.errors())

    def test_rejects_replaced_membership_even_when_count_is_unchanged(self):
        members = [row for row in self.mappings if row["map_type"] == "CONCEPT-SET"]
        members[0]["to_concept_url"] = members[1]["to_concept_url"]
        self.assert_rejected("set membership must cover exactly")

    def test_rejects_member_without_external_equivalence(self):
        self.mappings.remove(next(row for row in self.mappings if row["map_type"] == "SAME-AS"))
        self.assert_rejected("every member must have exactly one HL7 SAME-AS")

    def test_rejects_missing_spanish_name(self):
        self.concepts[0]["names"] = [name for name in self.concepts[0]["names"]
                                     if name.get("locale") != "es"]
        self.assert_rejected("must have one preferred Spanish FSN")

    def test_rejects_uuid_bundled_twice(self):
        self.concepts[0]["external_id"] = self.concepts[1]["external_id"]
        self.assert_rejected("UUID must be bundled exactly once")

    def test_rejects_historical_question_as_anatomical_member(self):
        member = next(row for row in self.mappings if row["map_type"] == "CONCEPT-SET")
        member["to_concept_url"] = "/orgs/SIHSALUS/sources/sihsalus/concepts/1311/"
        main = self.exports[VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT]
        question = next(concept for concept in main["concepts"] if concept["id"] == "1311")
        member["extras"]["openmrs_uuid"] = question["external_id"]
        self.assert_rejected("invalid set membership")

    def test_rejects_missing_spanish_name_on_reused_member(self):
        main = self.exports[VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT]
        nipple = next(concept for concept in main["concepts"] if concept["id"] == "85")
        nipple["names"] = []
        self.assert_rejected("must retain a preferred Spanish name")

    def test_preserves_historical_coded_datatype(self):
        main = self.exports[VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT]
        chest = next(concept for concept in main["concepts"] if concept["id"] == "256")
        chest["datatype"] = "N/A"
        self.assert_rejected("historical 256 must preserve identity/class/datatype")

    def test_rejects_rebundled_historical_concept(self):
        main = self.exports[VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT]
        nipple = next(concept for concept in main["concepts"] if concept["id"] == "85")
        self.concepts.append(copy.deepcopy(nipple))
        self.assert_rejected("historical 85 must preserve identity/class/datatype exactly once")

    def test_rejects_external_namespace_or_version_drift(self):
        for field, bad_value in (("to_source_name", "anatomia-procedimientos"),
                                 ("to_source_name", None),
                                 ("to_source_url", "https://example.org/wrong"),
                                 ("to_source_url", None),
                                 ("to_source_version", "3.0.0")):
            with self.subTest(field=field):
                mapping = next(row for row in self.mappings if row["map_type"] == "SAME-AS")
                original = mapping[field]
                mapping[field] = bad_value
                self.assert_rejected("must reference HL7 v2-0550 version 4.0.0")
                mapping[field] = original

    def test_rejects_membership_code_disagreeing_with_external_mapping(self):
        member = next(row for row in self.mappings if row["map_type"] == "CONCEPT-SET")
        member["extras"]["upstream_code"] = "OTHER"
        self.assert_rejected("membership HL7 code does not match SAME-AS")

    def test_rejects_missing_provenance_version(self):
        mapping = next(row for row in self.mappings if row["map_type"] == "SAME-AS")
        del mapping["extras"]["upstream_version"]
        self.assert_rejected("has invalid upstream_version")

    def test_rejects_conflicting_source_provenance(self):
        for path in (VALIDATOR.PROCEDURE_ANATOMY_CONCEPTS_EXPORT,
                     VALIDATOR.PROCEDURE_ANATOMY_MAPPINGS_EXPORT):
            self.exports[path]["source"]["extras"]["upstream_version"] = "3.0.0"
        self.assert_rejected("source has invalid upstream_version")

    def test_rejects_duplicate_mapping_identity(self):
        self.mappings[0]["external_id"] = self.mappings[1]["external_id"]
        self.assert_rejected("missing or duplicate UUID")

    def test_rejects_release_content_drift_beyond_semantic_checks(self):
        self.exports[VALIDATOR.PROCEDURE_ANATOMY_CONCEPTS_EXPORT]["description"] = "Changed release"
        self.assert_rejected("canonical official release hash mismatch")

    def test_rejects_unreleased_or_wrong_version_export(self):
        export = self.exports[VALIDATOR.PROCEDURE_ANATOMY_CONCEPTS_EXPORT]
        for field, bad_value in (("released", False), ("version", "HEAD")):
            with self.subTest(field=field):
                original = export[field]
                export[field] = bad_value
                self.assert_rejected(f"export {field} must be")
                export[field] = original

    def test_rejects_split_export_metadata_disagreement(self):
        self.exports[VALIDATOR.PROCEDURE_ANATOMY_MAPPINGS_EXPORT]["description"] = "Different"
        self.assert_rejected("split exports must preserve identical release metadata")

    def test_rejects_question_answer_mapping_in_catalog(self):
        self.mappings[0]["map_type"] = "Q-AND-A"
        self.assert_rejected("unexpected mapping type")

    def test_rejects_absent_export(self):
        del self.exports[VALIDATOR.PROCEDURE_ANATOMY_MAPPINGS_EXPORT]
        self.assert_rejected("required official OCL export is missing")

    def test_rejects_missing_fhir_source_association(self):
        rows = [row for row in self.fhir_source_rows()
                if row["Url"] != VALIDATOR.PROCEDURE_ANATOMY_HL7_URL]
        self.write_fhir_source_rows(rows)
        self.assert_rejected("must declare exactly one FHIR concept source association")

    def test_rejects_incorrect_fhir_system_uri(self):
        rows = self.fhir_source_rows()
        row = next(row for row in rows if row["Url"] == VALIDATOR.PROCEDURE_ANATOMY_HL7_URL)
        row["Url"] = "https://example.org/not-hl7"
        self.write_fhir_source_rows(rows)
        self.assert_rejected("FHIR concept source Url must be")

    def test_rejects_fhir_association_with_wrong_openmrs_source(self):
        rows = self.fhir_source_rows()
        row = next(row for row in rows if row["Url"] == VALIDATOR.PROCEDURE_ANATOMY_HL7_URL)
        row["Concept source"] = "CIEL"
        self.write_fhir_source_rows(rows)
        self.assert_rejected("FHIR concept source Concept source must be")

    def test_rejects_duplicate_fhir_source_association(self):
        rows = self.fhir_source_rows()
        rows.append(dict(next(row for row in rows if row["Url"] == VALIDATOR.PROCEDURE_ANATOMY_HL7_URL)))
        self.write_fhir_source_rows(rows)
        self.assert_rejected("must declare exactly one FHIR concept source association")

    def test_preserves_fhir_source_association_identity(self):
        rows = self.fhir_source_rows()
        row = next(row for row in rows if row["Url"] == VALIDATOR.PROCEDURE_ANATOMY_HL7_URL)
        row["Uuid"] = "a-different-association"
        self.write_fhir_source_rows(rows)
        self.assert_rejected("FHIR concept source Uuid must be")


if __name__ == "__main__":
    unittest.main()
