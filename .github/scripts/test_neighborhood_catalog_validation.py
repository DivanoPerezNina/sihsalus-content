#!/usr/bin/env python3
import importlib.util
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("validate_ocl_exports.py")
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("validate_ocl_exports", SCRIPT_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
SPLITTER_PATH = Path(__file__).with_name("split_ocl_export.py")
SPLITTER_SPEC = importlib.util.spec_from_file_location("split_ocl_export", SPLITTER_PATH)
SPLITTER = importlib.util.module_from_spec(SPLITTER_SPEC)
SPLITTER_SPEC.loader.exec_module(SPLITTER)


class NeighborhoodCatalogValidationTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.ocl_directory = Path(self.temporary_directory.name)
        self.concepts_path = self.ocl_directory / (
            "15_SIHSALUS_barrios-santa-clotilde_concepts_2026-08-22-01.zip"
        )
        self.mappings_path = self.ocl_directory / (
            "65_SIHSALUS_barrios-santa-clotilde_mappings_2026-08-22-01.zip"
        )
        self.main_concepts_path = self.ocl_directory / (
            "10_SIHSALUS_sihsalus_concepts_2026-07-16-02.zip"
        )
        self.main_mappings_path = self.ocl_directory / (
            "60_SIHSALUS_sihsalus_mappings_2026-07-16-02.zip"
        )
        for path in (
            self.concepts_path,
            self.mappings_path,
            self.main_concepts_path,
            self.main_mappings_path,
        ):
            path.touch()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def validate_subscription(self, subscription_url):
        document = ET.parse(VALIDATOR.GLOBAL_PROPERTIES_PATH)
        for global_property in document.findall(".//globalProperty"):
            if global_property.findtext("property") == "openconceptlab.subscriptionUrl":
                global_property.find("value").text = subscription_url
        path = self.ocl_directory / "globalproperties.xml"
        document.write(path, encoding="utf-8")
        errors = []
        with mock.patch.object(VALIDATOR, "GLOBAL_PROPERTIES_PATH", path):
            VALIDATOR.validate_ocl_global_properties(errors)
        return errors

    def test_accepts_existing_zip_import_namespace(self):
        self.assertEqual(
            self.validate_subscription(
                "https://api.openconceptlab.org/orgs/SIHSALUS/sources/sihsalus/2026-07-16-02"
            ),
            [],
        )

    def test_rejects_premature_institutional_host_transition(self):
        errors = self.validate_subscription(
            "https://api.gidis-terminology.duckdns.org/orgs/SIHSALUS/sources/sihsalus/2026-09-09-1"
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("openconceptlab.subscriptionUrl", errors[0])

    def source_version(self, concepts, mappings):
        return {
            "type": "Source Version",
            "id": VALIDATOR.NEIGHBORHOOD_VERSION,
            "version": VALIDATOR.NEIGHBORHOOD_VERSION,
            "short_code": VALIDATOR.NEIGHBORHOOD_SOURCE,
            "owner": "SIHSALUS",
            "owner_type": "Organization",
            "released": True,
            "source": {
                "id": VALIDATOR.NEIGHBORHOOD_SOURCE,
                "owner": "SIHSALUS",
                "owner_type": "Organization",
                "url": f"/orgs/SIHSALUS/sources/{VALIDATOR.NEIGHBORHOOD_SOURCE}/",
            },
            "concepts": concepts,
            "mappings": mappings,
        }

    def concept(self, concept_id, external_id, spanish_label, is_set=False):
        fsn = spanish_label
        names = [
            {
                "name": fsn,
                "locale": "es",
                "locale_preferred": True,
                "name_type": "Fully-Specified",
                "retired": False,
            }
        ]
        extras = {
            "facility": VALIDATOR.NEIGHBORHOOD_FACILITY,
            "local_code": concept_id,
        }
        if is_set:
            extras["catalog_size"] = len(VALIDATOR.NEIGHBORHOODS)
        else:
            extras.update(
                VALIDATOR.NEIGHBORHOOD_PRESENTATION_METADATA.get(
                    concept_id, {"ui_color": "#000000", "ui_tag_type": "gray"}
                )
            )
        return {
            "id": concept_id,
            "external_id": external_id,
            "concept_class": "ConvSet" if is_set else "Misc",
            "datatype": "N/A",
            "retired": False,
            "url": (
                f"/orgs/SIHSALUS/sources/{VALIDATOR.NEIGHBORHOOD_SOURCE}/"
                f"concepts/{concept_id}/"
            ),
            "names": names,
            "extras": extras,
        }

    def valid_exports(self):
        concepts = [
            self.concept(concept_id, external_id, spanish_label)
            for concept_id, external_id, spanish_label in VALIDATOR.NEIGHBORHOODS
        ]
        concepts.append(self.concept(*VALIDATOR.NEIGHBORHOOD_SET, is_set=True))
        mappings = [
            {
                "id": str(position),
                "external_id": f"mapping-{position}",
                "from_concept_code": VALIDATOR.NEIGHBORHOOD_SET[0],
                "from_concept_url": (
                    f"/orgs/SIHSALUS/sources/{VALIDATOR.NEIGHBORHOOD_SOURCE}/"
                    f"concepts/{VALIDATOR.NEIGHBORHOOD_SET[0]}/"
                ),
                "to_concept_code": concept_id,
                "to_concept_url": (
                    f"/orgs/SIHSALUS/sources/{VALIDATOR.NEIGHBORHOOD_SOURCE}/"
                    f"concepts/{concept_id}/"
                ),
                "map_type": "CONCEPT-SET",
                "sort_weight": position * 10,
                "retired": False,
                "url": (
                    f"/orgs/SIHSALUS/sources/{VALIDATOR.NEIGHBORHOOD_SOURCE}/"
                    f"mappings/{position}/"
                ),
            }
            for position, (concept_id, _, _) in enumerate(VALIDATOR.NEIGHBORHOODS, start=1)
        ]
        return {
            self.concepts_path: self.source_version(concepts, []),
            self.mappings_path: self.source_version([], list(reversed(mappings))),
        }

    def canonical_digest(self, exports):
        reconstructed = dict(exports[self.concepts_path])
        reconstructed["mappings"] = exports[self.mappings_path]["mappings"]
        canonical = VALIDATOR.json.dumps(
            reconstructed,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return VALIDATOR.hashlib.sha256(canonical).hexdigest()

    def validator_globals(self, exports):
        return mock.patch.multiple(
            VALIDATOR,
            OCL_DIR=self.ocl_directory,
            NEIGHBORHOOD_CONCEPTS_EXPORT=self.concepts_path,
            NEIGHBORHOOD_MAPPINGS_EXPORT=self.mappings_path,
            EXPECTED_SIHSALUS_CONCEPTS_EXPORT=self.main_concepts_path,
            EXPECTED_SIHSALUS_MAPPINGS_EXPORT=self.main_mappings_path,
            EXPECTED_NEIGHBORHOOD_CANONICAL_SHA256=self.canonical_digest(exports),
        )

    def test_accepts_exact_source_specific_exports(self):
        exports = self.valid_exports()
        errors = []
        with self.validator_globals(exports):
            VALIDATOR.validate_neighborhood_terminology(exports, {}, errors)
        self.assertEqual([], errors)

    def test_rejects_unexpected_concept(self):
        exports = self.valid_exports()
        exports[self.concepts_path]["concepts"].append(
            self.concept("UNEXPECTED", "3fb84698-488a-447d-acbc-72e8665cffdc", "1:512")
        )
        errors = []
        with self.validator_globals(exports):
            VALIDATOR.validate_neighborhood_terminology(exports, {}, errors)
        self.assertTrue(any("exactly 11 concepts" in error for error in errors))
        self.assertTrue(any("unexpected=" in error for error in errors))

    def test_rejects_main_source_duplication(self):
        duplicated_uuid = VALIDATOR.NEIGHBORHOODS[0][1]
        exports = self.valid_exports()
        errors = []
        with self.validator_globals(exports):
            VALIDATOR.validate_neighborhood_terminology(
                exports,
                {"legacy": {"external_id": duplicated_uuid}},
                errors,
            )
        self.assertTrue(any("must not bundle neighborhood UUIDs" in error for error in errors))

    def test_splitter_is_reproducible_and_lossless(self):
        exports = self.valid_exports()
        combined = dict(exports[self.concepts_path])
        combined["mappings"] = exports[self.mappings_path]["mappings"]
        official_path = self.ocl_directory / "official.zip"
        SPLITTER.write_export(official_path, combined)

        first_concepts = self.ocl_directory / "first-concepts.zip"
        first_mappings = self.ocl_directory / "first-mappings.zip"
        second_concepts = self.ocl_directory / "second-concepts.zip"
        second_mappings = self.ocl_directory / "second-mappings.zip"
        SPLITTER.split_export(official_path, first_concepts, first_mappings)
        SPLITTER.split_export(official_path, second_concepts, second_mappings)

        self.assertEqual(first_concepts.read_bytes(), second_concepts.read_bytes())
        self.assertEqual(first_mappings.read_bytes(), second_mappings.read_bytes())
        reconstructed = SPLITTER.read_export(first_concepts)
        reconstructed["mappings"] = SPLITTER.read_export(first_mappings)["mappings"]
        self.assertEqual(combined, reconstructed)


if __name__ == "__main__":
    unittest.main()
