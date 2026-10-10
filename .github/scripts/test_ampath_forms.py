#!/usr/bin/env python3
"""Exercise form identity checks with synthetic files through the validator entry point."""

import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import validate_ampath_forms as validator


class AmpathFormIdentityTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.forms = root / "ampathforms"
        self.forms.mkdir()
        ocl = root / "ocl"
        ocl.mkdir()
        with zipfile.ZipFile(ocl / "synthetic.zip", "w") as archive:
            archive.writestr("export.json", json.dumps({
                "source": {"id": "synthetic"},
                "concepts": [{"id": "1", "external_id": "synthetic-concept", "datatype": "Text"}],
            }))
        encounters = root / "encountertypes.csv"
        encounters.write_text("Uuid,Name,Void/Retire\nsynthetic-encounter,Synthetic encounter,false\n")
        for name, value in (("FORM_DIR", self.forms), ("OCL_DIR", ocl),
                            ("ENCOUNTER_TYPES_PATH", encounters)):
            patcher = patch.object(validator, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_form(self, filename, **overrides):
        form = {
            "name": "Synthetic form", "version": "1.0",
            "uuid": "10000000-0000-4000-8000-000000000001",
            "published": True, "retired": False,
            "encounter": "Synthetic encounter", "encounterType": "synthetic-encounter",
            "processor": "EncounterFormProcessor", "referencedForms": [], "pages": [],
        }
        form.update(overrides)
        (self.forms / filename).write_text(json.dumps(form))

    def run_validator(self):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            status = validator.main()
        return status, output.getvalue() + errors.getvalue()

    def test_accepts_literal_options_for_text_observations(self):
        self.write_form("select.json", pages=[{"sections": [{"questions": [{
            "id": "onset", "type": "obs", "questionOptions": {
                "concept": "synthetic-concept", "rendering": "select",
                "answers": [{"value": "Gradual", "label": "Inicio gradual"}],
            },
        }]}]}])
        status, output = self.run_validator()
        self.assertEqual(0, status, output)

    def test_rejects_ambiguous_or_invalid_literal_options(self):
        for answers in (
            [{"value": "Gradual", "concept": "synthetic-concept", "label": "Inicio gradual"}],
            [{"value": "", "label": "Vacío"}],
            [{"value": {"unexpected": True}, "label": "Objeto"}],
            [{"value": "Gradual"}],
            [{"value": "Gradual", "label": "Uno"}, {"value": "Gradual", "label": "Dos"}],
        ):
            with self.subTest(answers=answers):
                self.write_form("select.json", pages=[{"sections": [{"questions": [{
                    "id": "onset", "type": "obs", "questionOptions": {
                        "concept": "synthetic-concept", "rendering": "select", "answers": answers,
                    },
                }]}]}])
                status, output = self.run_validator()
                self.assertEqual(1, status, output)
                self.assertIn("literal", output)

    def test_accepts_distinct_versions_without_normalizing_them(self):
        self.write_form("first.json")
        self.write_form("second.json", version="1.0.0", uuid="10000000-0000-4000-8000-000000000002")
        status, output = self.run_validator()
        self.assertEqual(0, status, output)
        self.assertIn("Validated 2 AMPATH", output)

    def test_rejects_same_persisted_identity_with_different_json_uuids(self):
        self.write_form("first.json")
        self.write_form("second.json", uuid="10000000-0000-4000-8000-000000000002")
        status, output = self.run_validator()
        self.assertEqual(1, status, output)
        self.assertIn("duplicate persisted form UUID", output)
        self.assertIn("first.json", output)
        self.assertIn("second.json", output)

    def test_rejects_collisions_from_initializers_underscore_separator(self):
        self.write_form("first.json", name="Synthetic_form", version="1")
        self.write_form("second.json", name="Synthetic", version="form_1",
                        uuid="10000000-0000-4000-8000-000000000002")
        status, output = self.run_validator()
        self.assertEqual(1, status, output)
        self.assertIn("duplicate persisted form UUID", output)

    def test_still_rejects_duplicate_json_uuids(self):
        self.write_form("first.json")
        self.write_form("second.json", version="2.0")
        status, output = self.run_validator()
        self.assertEqual(1, status, output)
        self.assertIn("duplicate top-level form uuid", output)

    def test_rejects_empty_or_missing_form_directory(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                if missing:
                    self.forms.rmdir()
                status, output = self.run_validator()
                self.assertEqual(1, status, output)
                self.assertIn("no AMPATH form JSON files found", output)

    def test_rejects_blank_or_non_string_identity_fields(self):
        for field in ("name", "version"):
            for value in (None, "", "  ", 1, True, ["value"]):
                with self.subTest(field=field, value=value):
                    self.write_form("first.json", **{field: value})
                    status, output = self.run_validator()
                    self.assertEqual(1, status, output)
                    self.assertIn(f"{field} must be a non-empty string", output)


class ObstetricHistoryCaptureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.form = json.loads(Path(
            "configuration/ampathforms/OBST-001-ANTECEDENTES.json").read_text())
        cls.fields = {q["id"]: q for q in validator.walk(cls.form)
                      if q.get("type") == "obs"}
        cls.bundle, errors = validator.load_ocl_bundle()
        if errors:
            raise AssertionError(errors)

    def test_absence_is_an_active_canonical_answer_for_both_required_histories(self):
        none = "dbb7efe1-12d9-58b0-8de2-c218f626ff48"
        concepts = self.bundle["active_by_external_id"][none]
        self.assertEqual(1, len(concepts))
        self.assertEqual(("sihsalus", "521", "N/A"),
                         tuple(concepts[0][key] for key in ("source", "code", "datatype")))
        for field_id, code in (("antecedentesFamiliares", "9"), ("antecedentesPersonales", "29")):
            with self.subTest(field=field_id):
                question = self.fields[field_id]
                self.assertIs(question["required"], True)
                options = question["questionOptions"]
                self.assertEqual("checkbox", options["rendering"])
                self.assertEqual(1, sum(a.get("concept") == none for a in options["answers"]))
                self.assertIn(("sihsalus", "521"),
                              self.bundle["q_and_a_targets"][("sihsalus", code)])
                for node in (question, options):
                    self.assertNotIn("defaultValue", node)
                    self.assertNotIn("calculate", node)

    def test_capture_change_versions_the_form_without_reinterpreting_obstetric_concepts(self):
        self.assertEqual("OBST-001-ANTECEDENTES", self.form["name"])
        self.assertEqual("af89b9db-8d2c-4151-a233-369cac81fcd6", self.form["uuid"])
        self.assertEqual("1.0.1", self.form["version"])
        self.assertNotEqual(
            validator.ampath_persisted_form_uuid(self.form["name"], "1.0.0"),
            validator.ampath_persisted_form_uuid(self.form["name"], self.form["version"]))
        for field, concept in {
            "partos": "8795c05b-f286-4d70-a1e6-69172e676f05",
            "vaginales": "985732d6-157e-49aa-9d28-556696c5c4fe",
            "cesaReas": "78b32019-9881-4f5a-9c85-c9f954e53f9f",
            "nacidosVivos": "b553ce85-94e2-4755-b106-3befef127133",
            "nacidosMuertos": "4dc3ee54-ba0c-49e7-b907-02aa727372f4",
            "rnDeMayorPesoG": "dee42f1a-657e-4ab3-8a0a-b012500edea6",
        }.items():
            with self.subTest(field=field):
                self.assertEqual(concept, self.fields[field]["questionOptions"]["concept"])
        self.assertEqual("Partos", self.fields["partos"]["label"])
        self.assertNotIn("8f2db1d3-4212-47e3-99aa-3cfa65ac1312",
                         {q["questionOptions"]["concept"] for q in self.fields.values()})


if __name__ == "__main__":
    unittest.main()
