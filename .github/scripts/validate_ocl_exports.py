#!/usr/bin/env python3
import csv
import hashlib
import json
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


OCL_DIR = Path("configuration/ocl")
FORM_DIR = Path("configuration/ampathforms")
GLOBAL_PROPERTIES_PATH = Path(
    "configuration/globalproperties/globalproperties-sihsalus.xml"
)
ADDRESS_CONFIGURATION_PATH = Path(
    "configuration/addresshierarchy/addressConfiguration.xml"
)
PERSON_ATTRIBUTE_TYPES_PATH = Path(
    "configuration/personattributetypes/personattributetypes.csv"
)
FHIR_CONCEPT_SOURCES_PATH = Path("configuration/fhirconceptsources/fhirconceptsources.csv")
EXPECTED_SIHSALUS_SUBSCRIPTION_URL = (
    "https://api.openconceptlab.org/orgs/SIHSALUS/sources/sihsalus/2026-07-16-02"
)
EXPECTED_SIHSALUS_CONCEPTS_EXPORT = (
    OCL_DIR / "10_SIHSALUS_sihsalus_concepts_2026-09-09-1.zip"
)
EXPECTED_SIHSALUS_MAPPINGS_EXPORT = (
    OCL_DIR / "60_SIHSALUS_sihsalus_mappings_2026-09-09-1.zip"
)
EXPECTED_SIHSALUS_CANONICAL_SHA256 = (
    "cae14cffdce3d5ed882e97cc3ca6030d798788526b3baded304f472f7779e195"
)
OCCUPATIONS_SOURCE = "ocupaciones"
OCCUPATIONS_ROOT_URL = "/orgs/SIHSALUS/sources/ocupaciones/concepts/1/"
OCCUPATIONS_CONCEPT_URL_PREFIX = "/orgs/SIHSALUS/sources/ocupaciones/concepts/"
EXPECTED_OCCUPATION_UNIT_GROUPS = 436
SIHSALUS_SOURCE = "sihsalus"
NEIGHBORHOOD_SOURCE = "barrios-santa-clotilde"
NEIGHBORHOOD_VERSION = "2026-08-22-01"
EXPECTED_NEIGHBORHOOD_CANONICAL_SHA256 = (
    "fbcb4f0ed111ceb4c686ac343eee09c2435037f8dceb9b679cee0a226e1c9177"
)
NEIGHBORHOOD_ATTRIBUTE_TYPE_UUID = "4a182c6e-9a19-4db8-8042-4bbf3b4308c2"
NEIGHBORHOOD_SET_UUID = "0fd3e744-6d2c-4cb3-9b7e-1f88899635d9"
NEIGHBORHOOD_CONCEPTS_EXPORT = OCL_DIR / (
    f"15_SIHSALUS_{NEIGHBORHOOD_SOURCE}_concepts_{NEIGHBORHOOD_VERSION}.zip"
)
NEIGHBORHOOD_MAPPINGS_EXPORT = OCL_DIR / (
    f"65_SIHSALUS_{NEIGHBORHOOD_SOURCE}_mappings_{NEIGHBORHOOD_VERSION}.zip"
)
NEIGHBORHOODS = [
    ("SCL-01", "1975805f-a096-4583-aacc-ab439c79e1cd", "Barrio Santa Rosa"),
    ("SCL-02", "6db9db1a-b772-4cc7-b261-41ea0957e0f7", "Barrio San Juan Bautista"),
    ("SCL-03", "d31430ca-4892-43b9-aba5-0f0c51aea497", "Barrio Fray Martín"),
    ("SCL-04", "4f0c3fd5-100f-4d2e-9478-100169d952da", "Barrio Jorge Chávez"),
    ("SCL-05", "30a01fac-2c8e-4313-b675-3c389a255db5", "Barrio San Antonio"),
    ("SCL-06", "4bc7352e-f2b1-4e4b-a625-ca1d043e10a9", "Barrio Señor de los Milagros"),
    ("SCL-07", "a65d66bd-b0a6-4ada-9270-e55ba200e4ca", "Barrio Jaime Carranza"),
    ("SCL-08", "b77b4e56-64c7-427f-9d6b-87ce54291653", "Barrio Santa Elisa"),
    ("SCL-09", "81fc260c-9a5f-4182-b7ac-d50f0960370b", "Barrio 28 de Julio"),
    ("SCL-10", "ef33a561-cdea-4218-a360-723d16ccdd08", "Barrio Nueva Primavera"),
]
NEIGHBORHOOD_SET = ("SCL-BARRIOS", NEIGHBORHOOD_SET_UUID, "Barrios de Santa Clotilde")
NEIGHBORHOOD_FACILITY = "Hospital II-1 Santa Clotilde"
NEIGHBORHOOD_PRESENTATION_METADATA = {
    "SCL-01": {"ui_color": "#B94A36", "ui_tag_type": "red"},
    "SCL-02": {"ui_color": "#4F6128", "ui_tag_type": "green"},
    "SCL-03": {"ui_color": "#304238", "ui_tag_type": "teal"},
    "SCL-04": {"ui_color": "#4E8C24", "ui_tag_type": "green"},
    "SCL-05": {"ui_color": "#B47A16", "ui_tag_type": "warm-gray"},
    "SCL-06": {"ui_color": "#642C35", "ui_tag_type": "magenta"},
    "SCL-07": {"ui_color": "#D45A1F", "ui_tag_type": "red"},
    "SCL-08": {"ui_color": "#A5B51D", "ui_tag_type": "green"},
    "SCL-09": {"ui_color": "#B98A16", "ui_tag_type": "warm-gray"},
    "SCL-10": {"ui_color": "#D94B3D", "ui_tag_type": "red"},
}
REFERRAL_SOURCE = "referencia-institucional"
REFERRAL_VERSION = "2026-08-25-01"
PROCEDURE_ANATOMY_SOURCE = "anatomia-procedimientos"
PROCEDURE_ANATOMY_VERSION = "2026-10-11-02"
PROCEDURE_ANATOMY_SET_CODE = "PROCEDURE-BODY-SITES"
PROCEDURE_ANATOMY_SET_UUID = "25b4e8e6-0781-5c04-bc76-888402f3f505"
PROCEDURE_ANATOMY_HL7_URL = "http://terminology.hl7.org/CodeSystem/v2-0550"
PROCEDURE_ANATOMY_CONCEPT_SOURCE_UUID = "30c3cf28-091d-5ec9-ace5-5edfc9e1543b"
PROCEDURE_ANATOMY_FHIR_SOURCE_UUID = "ab151b90-06d7-5734-928d-5907c65226b5"
PROCEDURE_ANATOMY_CONCEPTS_EXPORT = OCL_DIR / (
    f"17_SIHSALUS_{PROCEDURE_ANATOMY_SOURCE}_concepts_{PROCEDURE_ANATOMY_VERSION}.zip"
)
PROCEDURE_ANATOMY_MAPPINGS_EXPORT = OCL_DIR / (
    f"67_SIHSALUS_{PROCEDURE_ANATOMY_SOURCE}_mappings_{PROCEDURE_ANATOMY_VERSION}.zip"
)
EXPECTED_PROCEDURE_ANATOMY_CANONICAL_SHA256 = (
    "26dd43fb00dc098741742a7cbfe86f247b42aa229390d5ed4f7a687b74d928a7"
)
# Historical identities are assertions, not a second operational catalog.
PROCEDURE_ANATOMY_HISTORICAL = {
    "85": ("NIPPL", "99a163e0-0352-4d46-a994-3b75a25cf4be", "Anatomy", "N/A"),
    "256": ("CHES", "08579338-2599-438e-b3be-6cd3e7d955bd", "Anatomy", "Coded"),
    "325": ("LIP", "8a914b99-9e1f-4d69-ae15-8f1699b28dc5", "Anatomy", "N/A"),
    "327": ("PLATH", "aadfe8f3-3417-4075-83f0-b06692c2806e", "Anatomy", "N/A"),
    "329": ("PLATS", "ac2051b4-a46f-47f3-a7d6-74d832900e44", "Anatomy", "N/A"),
    "344": ("LARYN", "18a4c1f6-dde3-44f7-bdd7-c99f56525609", "Anatomy", "N/A"),
    "348": ("FBMAX", "ae834c80-902d-4f5b-89c0-a669ae584687", "Anatomy", "N/A"),
    "349": ("ORO", "5524065b-2ee1-4d4e-8ad8-28c61d407c2a", "Anatomy", "N/A"),
    "2790": ("OVARY", "24dd6942-b693-485d-9924-28b86b323d27", "Misc", "N/A"),
    "2787": ("ENDM", "48403d33-d806-4455-94b4-dd69c82a6318", "Misc", "N/A"),
    "1351": ("PLC", "ee00490c-9481-4e4a-a098-d8dc481bc94b", "Finding", "N/A"),
    "1294": ("ESO", "e066680d-d825-45fe-a0ad-f3734dea6cb2", "Misc", "N/A"),
    "1239": ("TONG", "a25eefd5-80cd-496f-9578-dd2b0152a11e", "Misc", "N/A"),
}
REFERRAL_TRANSPORT_CSV = Path(
    "configuration/concepts/referral_transport_concepts.csv"
)
REFERRAL_CONCEPTS_EXPORT = OCL_DIR / (
    f"16_SIHSALUS_{REFERRAL_SOURCE}_concepts_{REFERRAL_VERSION}.zip"
)
EXPECTED_REFERRAL_CANONICAL_SHA256 = (
    "9a85ebac1f3710be861ddb092fb9806eee0e5d60557e494bcdb742be510aedff"
)
REFERRAL_TRANSPORT_CONCEPTS = [
    (
        "REF-TR-01",
        "844be877-6d20-45e2-876f-dc5de42edd67",
        "Transporte terrestre para referencia",
        "Terrestre",
        "Land transport for referral",
        "Land",
        "Modo de transporte terrestre usado durante una referencia institucional.",
    ),
    (
        "REF-TR-02",
        "2a228c88-7daf-4f60-9e55-c884c9302bd8",
        "Transporte aéreo para referencia",
        "Aéreo",
        "Air transport for referral",
        "Air",
        "Modo de transporte aéreo usado durante una referencia institucional.",
    ),
    (
        "REF-TR-03",
        "d5e04df9-d1dc-431e-bd71-c934ec3e18e2",
        "Transporte fluvial para referencia",
        "Fluvial",
        "River transport for referral",
        "River",
        "Modo de transporte fluvial usado durante una referencia institucional.",
    ),
]
TPED_ROOT_ID = "3798"
TPED_LINES = {
    "90": ("A", ["91", "92", "93", "94", "95"]),
    "96": ("B", ["97", "98", "99"]),
    "100": ("C", ["101", "103", "105", "106", "107", "108"]),
    "109": ("D", [str(concept_id) for concept_id in range(130, 141)]),
    "141": ("E", ["142", "143", "144"]),
    "145": ("F", ["146", "147", "148"]),
    "149": ("G", [str(concept_id) for concept_id in range(150, 159)]),
    "159": ("H", [str(concept_id) for concept_id in range(160, 168)]),
    "168": ("I", [str(concept_id) for concept_id in range(169, 180)]),
    "180": ("J", [str(concept_id) for concept_id in range(181, 190)]),
    "190": ("K", [str(concept_id) for concept_id in range(191, 201)]),
    "201": ("L", [str(concept_id) for concept_id in range(202, 213)]),
}
INSTRUMENT_SETS = {
    TPED_ROOT_ID: {
        *TPED_LINES,
        "3791",
        "1036",
    },
    "1070": {
        "3774",
        "1028",
        "1030",
        "1029",
        "1035",
        "1031",
        "1032",
        "1033",
        "1034",
        "1036",
        "1037",
        "1042",
        "1038",
        "1043",
        "1039",
        "1044",
        "1040",
        "1045",
        "1041",
        "1046",
        "1047",
        "1048",
        "1049",
        "1050",
        "1051",
        "1052",
        "1053",
        "1054",
        "1055",
    },
    "1071": {
        "1069",
        "1056",
        "1031",
        "1032",
        "1033",
        "1034",
        "1057",
        "1058",
        "1059",
        "1060",
        "1061",
        "1062",
        "1063",
        "1064",
        "1065",
        "1066",
        "1067",
        "1068",
        "1050",
        "1053",
        "1054",
        "1055",
    },
    "4167": {"4443", "4143", "4144"},
    "4168": {"4148", "4447", "4149", "4144"},
}
INSTRUMENT_NAMES = {
    "3798": "Test Peruano de Evaluación del Desarrollo del Niño (TPED)",
    "1070": "Test de Vigilancia del Neurodesarrollo (Huanca Test)",
    "1071": "Lista de Habilidades y Conductas Esperadas por Edad",
    "4167": "Prueba de Evaluación del Desarrollo Infantil (EDI)",
    "4168": "M-CHAT-R/F versión peruana",
}
CODED_RESULT_SETS = {
    "4443": ["4444", "4445", "4446"],
    "4447": ["4448", "4449", "4450"],
}
PROCEDURE_STATUS_ID = "4451"
PROCEDURE_STATUS_EXTERNAL_ID = "f0d47b45-8303-4cdc-a9f2-c37135a3700f"
PROCEDURE_STATUS_ANSWERS = [
    ("4452", "167153AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Preparación"),
    ("4453", "163723AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "En progreso"),
    ("4454", "1118AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "No realizado"),
    ("4455", "167154AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "En espera"),
    ("4456", "167155AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Discontinuado"),
    ("4457", "1267AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Completado"),
    ("4458", "162983AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Registrado por error"),
    ("4459", "1067AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Desconocido (procedimiento)"),
]
DURATION_UNITS_ID = "612"
DURATION_UNITS_EXTERNAL_ID = "1732AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
DURATION_UNIT_MEMBERS = [
    ("615", "162583AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Segundos"),
    ("609", "1733AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Minuto"),
    ("603", "1822AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Horas"),
    ("610", "1072AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Días"),
    ("611", "1073AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Semanas"),
    ("613", "1074AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Meses"),
    ("608", "1734AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Años"),
    ("614", "162582AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Cantidad de veces"),
]


def main():
    errors = []
    checked = 0
    occupation_unit_ids = set()
    occupation_mapping_targets = []
    concepts_by_source = defaultdict(dict)
    mappings_by_source = defaultdict(list)
    concepts_by_url = {}
    concept_records = []
    mapping_records = []
    exports_by_path = {}

    for zip_path in sorted(OCL_DIR.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as archive:
            try:
                export = json.loads(archive.read("export.json"))
            except KeyError:
                errors.append(f"{zip_path}: missing export.json")
                continue

        source = export.get("source") or {}
        source_id = source.get("id") if isinstance(source, dict) else export.get("short_code")
        exports_by_path[zip_path] = export

        for concept in export.get("concepts", []):
            concept_id = concept.get("id")
            if source_id and concept_id:
                concepts_by_source[source_id][concept_id] = concept
            concept_records.append((zip_path, source_id, concept))

            concept_url = normalize_ocl_url(concept.get("url"))
            if concept_url:
                existing = concepts_by_url.get(concept_url)
                if existing and existing[2].get("external_id") != concept.get("external_id"):
                    errors.append(
                        f"{zip_path}: concept URL {concept_url} is duplicated by "
                        f"{existing[0]} and {concept.get('external_id') or concept_id}"
                    )
                else:
                    concepts_by_url[concept_url] = (zip_path, source_id, concept)

        if source_id:
            mappings_by_source[source_id].extend(export.get("mappings", []))
            mapping_records.extend(
                (zip_path, source_id, mapping) for mapping in export.get("mappings", [])
            )

        for concept in export.get("concepts", []):
            checked += 1
            names_by_external_id = defaultdict(list)

            for name in concept.get("names", []):
                if name.get("retired"):
                    continue

                external_id = (name.get("external_id") or "").strip()
                if external_id:
                    names_by_external_id[external_id].append(name)

            for external_id, names in names_by_external_id.items():
                if len(names) < 2:
                    continue

                concept_identifier = concept.get("external_id") or concept.get("id") or concept.get("uuid")
                rendered_names = ", ".join(
                    f"{name.get('locale')}:{name.get('name')} ({name.get('name_type')})" for name in names
                )
                errors.append(
                    f"{zip_path}: concept {concept_identifier} has duplicated active concept-name "
                    f"external_id {external_id}: {rendered_names}"
                )

            if source_id != OCCUPATIONS_SOURCE or concept.get("retired"):
                continue
            if (concept.get("extras") or {}).get("level") != "unit_group":
                continue

            concept_id = concept.get("id") or ""
            if not re.fullmatch(r"\d{4}", concept_id):
                errors.append(f"{zip_path}: occupation unit group has invalid id {concept_id!r}")
                continue

            occupation_unit_ids.add(concept_id)
            active_names = [name for name in concept.get("names", []) if not name.get("retired")]
            preferred_es = [
                name for name in active_names if name.get("locale") == "es" and name.get("locale_preferred")
            ]
            preferred_en = [
                name for name in active_names if name.get("locale") == "en" and name.get("locale_preferred")
            ]
            short_es = [
                name
                for name in active_names
                if name.get("locale") == "es"
                and name.get("name_type") == "Short"
                and name.get("name") == concept_id
            ]

            if len(preferred_es) != 1:
                errors.append(
                    f"{zip_path}: occupation {concept_id} must have exactly one preferred Spanish name"
                )
            if len(preferred_en) != 1:
                errors.append(
                    f"{zip_path}: occupation {concept_id} must have exactly one preferred English name"
                )
            if len(short_es) != 1:
                errors.append(f"{zip_path}: occupation {concept_id} must have its code as a Spanish Short name")

            if preferred_es:
                spanish_name = preferred_es[0].get("name") or ""
                if spanish_name.startswith(f"CIUO-08 {concept_id} -"):
                    errors.append(
                        f"{zip_path}: occupation {concept_id} still has the generated untranslated Spanish label"
                    )
                if preferred_en and concept_id != "3434" and spanish_name == preferred_en[0].get("name"):
                    errors.append(
                        f"{zip_path}: occupation {concept_id} has the same preferred name in Spanish and English"
                    )

            extras = concept.get("extras") or {}
            for field in ("major_label_es", "sub_major_label_es", "minor_label_es"):
                if not extras.get(field):
                    errors.append(f"{zip_path}: occupation {concept_id} is missing {field}")

        if source_id == OCCUPATIONS_SOURCE:
            for mapping in export.get("mappings", []):
                if mapping.get("retired") or mapping.get("map_type") != "CONCEPT-SET":
                    continue
                if mapping.get("from_concept_url") != OCCUPATIONS_ROOT_URL:
                    continue
                target_url = mapping.get("to_concept_url") or ""
                if not target_url.startswith(OCCUPATIONS_CONCEPT_URL_PREFIX):
                    continue
                target_id = target_url.removeprefix(OCCUPATIONS_CONCEPT_URL_PREFIX).rstrip("/")
                if re.fullmatch(r"\d{4}", target_id):
                    occupation_mapping_targets.append(target_id)

    if len(occupation_unit_ids) != EXPECTED_OCCUPATION_UNIT_GROUPS:
        errors.append(
            "occupation terminology must contain "
            f"{EXPECTED_OCCUPATION_UNIT_GROUPS} active CIUO-08 unit groups; found {len(occupation_unit_ids)}"
        )

    if len(occupation_mapping_targets) != EXPECTED_OCCUPATION_UNIT_GROUPS:
        errors.append(
            "occupation root must have exactly "
            f"{EXPECTED_OCCUPATION_UNIT_GROUPS} active unit-group mappings; "
            f"found {len(occupation_mapping_targets)}"
        )
    elif set(occupation_mapping_targets) != occupation_unit_ids:
        missing = sorted(occupation_unit_ids - set(occupation_mapping_targets))
        unexpected = sorted(set(occupation_mapping_targets) - occupation_unit_ids)
        errors.append(f"occupation mapping coverage mismatch: missing={missing}, unexpected={unexpected}")

    validate_mapping_integrity(concepts_by_url, mapping_records, errors)
    validate_default_name_collision_safety(concept_records, errors)
    validate_laboratory_capture(concept_records, errors)
    validate_sihsalus_export(exports_by_path, errors)

    validate_development_instruments(
        concepts_by_source[SIHSALUS_SOURCE], mappings_by_source[SIHSALUS_SOURCE], errors
    )
    validate_procedure_terminology(
        concepts_by_source[SIHSALUS_SOURCE], mappings_by_source[SIHSALUS_SOURCE], errors
    )
    validate_neighborhood_terminology(
        exports_by_path,
        concepts_by_source[SIHSALUS_SOURCE],
        errors,
    )
    validate_neighborhood_backend_configuration(errors)
    validate_referral_transport_terminology(exports_by_path, concept_records, errors)
    validate_procedure_anatomy_terminology(exports_by_path, concept_records, errors)
    validate_ocl_global_properties(errors)

    if errors:
        print("OCL export validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {checked} OCL concepts and {len(mapping_records)} mapping endpoints.")
    return 0


def validate_laboratory_capture(concept_records, errors):
    expected = {
        "5282": ("6576cf12-ca50-4234-be46-ac74a4e7814d", "Coded"),
        "5286": ("a0d91c80-4e2f-4f12-8007-3a5c40931bf8", "Coded"),
        "2470": ("267b3f53-10ff-498f-a37e-f33b945bd1ce", "Numeric"),
        "5400": ("bc79bdb5-5bbe-4864-a2ed-81c7ad77ff88", "Numeric"),
    }
    for code, (uuid, datatype) in expected.items():
        matches = [
            (source, concept) for _, source, concept in concept_records
            if (source == "laboratorio" and str(concept.get("id")) == code)
            or concept.get("external_id") == uuid
        ]
        if len(matches) != 1:
            errors.append(f"laboratorio:{code}: expected exactly one concept {uuid}; found {len(matches)}")
            continue
        source, concept = matches[0]
        if (source != "laboratorio" or str(concept.get("id")) != code
                or concept.get("external_id") != uuid or concept.get("retired") is not False
                or concept.get("datatype") != datatype):
            errors.append(f"laboratorio:{code}: must preserve active UUID {uuid} with datatype {datatype}")
        if code == "5400":
            extras = concept.get("extras") or {}
            # Accept the legacy spelling only for declared magnitude; Units does not
            # demonstrate that OpenMRS persisted units. Conflicting spellings fail.
            units = [extras[key] for key in ("units", "Units") if key in extras] if isinstance(extras, dict) else []
            if not units or any(unit != "mg/24h" for unit in units):
                errors.append(f"laboratorio:{code}: {uuid} must declare mg/24h consistently in units/Units")


def validate_sihsalus_export(exports_by_path, errors):
    concepts = exports_by_path.get(EXPECTED_SIHSALUS_CONCEPTS_EXPORT)
    mappings = exports_by_path.get(EXPECTED_SIHSALUS_MAPPINGS_EXPORT)
    if concepts is None or mappings is None:
        errors.append("missing pinned sihsalus concepts/mappings exports")
        return
    if concepts.get("mappings") != [] or mappings.get("concepts") != []:
        errors.append("sihsalus exports must separate concepts from mappings")
    if {
        key: value for key, value in concepts.items() if key not in {"concepts", "mappings"}
    } != {
        key: value for key, value in mappings.items() if key not in {"concepts", "mappings"}
    }:
        errors.append("sihsalus concepts/mappings release metadata differs")
    combined = dict(concepts)
    combined["mappings"] = mappings.get("mappings")
    canonical = json.dumps(
        combined, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != EXPECTED_SIHSALUS_CANONICAL_SHA256:
        errors.append("sihsalus exports differ from the reviewed release with explicit neighborhood exclusions")


def normalize_ocl_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    return url.strip().rstrip("/") + "/"


def validate_mapping_integrity(concepts_by_url, mapping_records, errors):
    internal_map_types = {"Q-AND-A", "CONCEPT-SET"}

    for zip_path, source_id, mapping in mapping_records:
        mapping_identifier = mapping.get("url") or mapping.get("external_id") or mapping.get("id")
        prefix = f"{zip_path}: mapping {mapping_identifier}"

        from_url = normalize_ocl_url(mapping.get("from_concept_url"))
        if not from_url:
            errors.append(f"{prefix} has no from_concept_url")
        elif from_url not in concepts_by_url:
            errors.append(f"{prefix} references unbundled origin concept {from_url}")

        if mapping.get("map_type") in internal_map_types:
            to_url = normalize_ocl_url(mapping.get("to_concept_url"))
            if not to_url:
                errors.append(
                    f"{prefix} ({mapping.get('map_type')}) has no to_concept_url"
                )
            elif to_url not in concepts_by_url:
                errors.append(f"{prefix} references unbundled target concept {to_url}")
            continue

        target_source_name = mapping.get("to_source_name") or mapping.get(
            "to_source_name_resolved"
        )
        if not target_source_name:
            errors.append(f"{prefix} has no target source name")
        if not normalize_ocl_url(mapping.get("to_source_url")):
            errors.append(f"{prefix} has no to_source_url")
        if not str(mapping.get("to_concept_code") or "").strip():
            errors.append(f"{prefix} has no to_concept_code")


def normalize_name_type(name_type):
    return re.sub(r"[-_]+", " ", str(name_type or "").strip().casefold())


def normalize_concept_name(name):
    return " ".join(str(name or "").strip().casefold().split())


def validate_default_name_collision_safety(concept_records, errors, required_spanish_uuids=None):
    default_names = defaultdict(list)

    def name_key(name):
        text = normalize_concept_name(name)
        if required_spanish_uuids is not None:
            text = unicodedata.normalize("NFD", text)
            text = "".join(char for char in text if not unicodedata.combining(char))
        return text

    for zip_path, source_id, concept in concept_records:
        if concept.get("retired"):
            continue

        active_names = [name for name in concept.get("names", []) if not name.get("retired")]
        for name in active_names:
            if required_spanish_uuids is not None and name.get("locale") != "es":
                continue
            if normalize_name_type(name.get("name_type")) == "index term":
                continue
            if not (
                name.get("locale_preferred")
                or normalize_name_type(name.get("name_type")) == "fully specified"
            ):
                continue

            key = (name.get("locale"), name_key(name.get("name")))
            default_names[key].append(
                (zip_path, source_id, concept, active_names, name)
            )

    for key, matches in default_names.items():
        concept_uuids = {
            concept.get("external_id") or f"{source_id}:{concept.get('id')}"
            for _, source_id, concept, _, _ in matches
        }
        if len(concept_uuids) < 2:
            continue

        for zip_path, source_id, concept, active_names, name in matches:
            # OCL demotes colliding default names to index terms. For this
            # Spanish selector, another-language fallback cannot make that safe.
            if required_spanish_uuids is not None:
                if concept.get("external_id") in required_spanish_uuids:
                    errors.append(
                        f"{zip_path}: concept {source_id}:{concept.get('id')} "
                        f"preferred Spanish name collides: {name.get('name')!r}"
                    )
                continue
            alternatives = [
                candidate
                for candidate in active_names
                if normalize_name_type(candidate.get("name_type")) != "index term"
                and (
                    candidate.get("locale"),
                    name_key(candidate.get("name")),
                )
                != key
            ]
            if alternatives:
                continue

            rendered_matches = ", ".join(
                f"{other_source}:{other_concept.get('id')} "
                f"({other_name.get('name')!r})"
                for _, other_source, other_concept, _, other_name in matches
            )
            errors.append(
                f"{zip_path}: active concept {source_id}:{concept.get('id')} has no safe "
                f"fully-specified-name fallback for case-insensitive default-name collision "
                f"{name.get('name')!r}; matches: {rendered_matches}"
            )


def validate_development_instruments(concepts, mappings, errors):
    active_mappings = [mapping for mapping in mappings if not mapping.get("retired")]

    def targets(from_id, map_type):
        matching = [
            mapping
            for mapping in active_mappings
            if mapping.get("from_concept_code") == from_id and mapping.get("map_type") == map_type
        ]
        if matching and all(mapping.get("sort_weight") is not None for mapping in matching):
            matching.sort(key=lambda mapping: float(mapping["sort_weight"]))
        return [mapping.get("to_concept_code") for mapping in matching]

    for concept_id, expected_name in INSTRUMENT_NAMES.items():
        concept = concepts.get(concept_id)
        if not concept:
            errors.append(f"sihsalus: missing development instrument concept {concept_id}")
            continue
        if concept.get("concept_class") != "ConvSet" or concept.get("datatype") != "N/A":
            errors.append(
                f"sihsalus: instrument {concept_id} must be ConvSet/N/A; "
                f"found {concept.get('concept_class')}/{concept.get('datatype')}"
            )
        if concept.get("display_name") != expected_name:
            errors.append(
                f"sihsalus: instrument {concept_id} must display as {expected_name!r}; "
                f"found {concept.get('display_name')!r}"
            )

    tped_answer_ids = set()
    for line_id, (line_code, expected_targets) in TPED_LINES.items():
        line = concepts.get(line_id)
        if not line:
            errors.append(f"sihsalus: missing TPED line {line_code} ({line_id})")
            continue
        if line.get("concept_class") != "Question" or line.get("datatype") != "Coded":
            errors.append(
                f"sihsalus: TPED line {line_code} ({line_id}) must be Question/Coded"
            )
        if (line.get("extras") or {}).get("tped_line") != line_code:
            errors.append(f"sihsalus: TPED line {line_code} ({line_id}) has invalid metadata")

        actual_targets = targets(line_id, "Q-AND-A")
        if actual_targets != expected_targets:
            errors.append(
                f"sihsalus: TPED line {line_code} mappings mismatch: "
                f"expected={expected_targets}, actual={actual_targets}"
            )

        for order, target_id in enumerate(expected_targets, start=1):
            tped_answer_ids.add(target_id)
            target = concepts.get(target_id)
            extras = (target or {}).get("extras") or {}
            if not target or target.get("concept_class") != "Misc" or target.get("datatype") != "N/A":
                errors.append(f"sihsalus: TPED milestone {target_id} must be Misc/N/A")
            if extras.get("tped_line") != line_code or extras.get("tped_order") != order:
                errors.append(
                    f"sihsalus: TPED milestone {target_id} must have line={line_code}, order={order}"
                )

    if len(tped_answer_ids) != 89:
        errors.append(f"sihsalus: TPED must have 89 unique milestones; found {len(tped_answer_ids)}")

    for instrument_id, expected_targets in INSTRUMENT_SETS.items():
        actual_targets = set(targets(instrument_id, "CONCEPT-SET"))
        if actual_targets != expected_targets:
            errors.append(
                f"sihsalus: instrument set {instrument_id} mismatch: "
                f"missing={sorted(expected_targets - actual_targets)}, "
                f"unexpected={sorted(actual_targets - expected_targets)}"
            )

    for question_id, expected_targets in CODED_RESULT_SETS.items():
        question = concepts.get(question_id)
        if not question or question.get("concept_class") != "Question" or question.get("datatype") != "Coded":
            errors.append(f"sihsalus: result concept {question_id} must be Question/Coded")
        actual_targets = targets(question_id, "Q-AND-A")
        if actual_targets != expected_targets:
            errors.append(
                f"sihsalus: result answers for {question_id} mismatch: "
                f"expected={expected_targets}, actual={actual_targets}"
            )

    validate_development_forms(concepts, active_mappings, errors)


def validate_procedure_terminology(concepts, mappings, errors):
    active_mappings = [mapping for mapping in mappings if not mapping.get("retired")]

    def preferred_spanish_names(concept):
        return [
            name.get("name")
            for name in (concept or {}).get("names", [])
            if not name.get("retired")
            and name.get("locale") == "es"
            and name.get("locale_preferred")
        ]

    def ordered_targets(from_id, map_type):
        matching = [
            mapping
            for mapping in active_mappings
            if mapping.get("from_concept_code") == from_id and mapping.get("map_type") == map_type
        ]
        matching.sort(
            key=lambda mapping: (
                float(mapping["sort_weight"])
                if mapping.get("sort_weight") is not None
                else float("inf")
            )
        )
        return [mapping.get("to_concept_code") for mapping in matching]

    procedure_status = concepts.get(PROCEDURE_STATUS_ID)
    if not procedure_status:
        errors.append(f"sihsalus: missing procedure status concept {PROCEDURE_STATUS_ID}")
    else:
        if procedure_status.get("external_id") != PROCEDURE_STATUS_EXTERNAL_ID:
            errors.append(
                f"sihsalus: procedure status must use OpenMRS UUID {PROCEDURE_STATUS_EXTERNAL_ID}; "
                f"found {procedure_status.get('external_id')}"
            )
        if (
            procedure_status.get("concept_class") != "Question"
            or procedure_status.get("datatype") != "Coded"
        ):
            errors.append("sihsalus: procedure status must be Question/Coded")
        if preferred_spanish_names(procedure_status) != ["Estado del procedimiento"]:
            errors.append("sihsalus: procedure status must prefer 'Estado del procedimiento' in Spanish")

    expected_answer_ids = [concept_id for concept_id, _, _ in PROCEDURE_STATUS_ANSWERS]
    actual_answer_ids = ordered_targets(PROCEDURE_STATUS_ID, "Q-AND-A")
    if actual_answer_ids != expected_answer_ids:
        errors.append(
            f"sihsalus: procedure status answers mismatch: "
            f"expected={expected_answer_ids}, actual={actual_answer_ids}"
        )

    for concept_id, external_id, spanish_name in PROCEDURE_STATUS_ANSWERS:
        concept = concepts.get(concept_id)
        if not concept:
            errors.append(f"sihsalus: missing procedure status answer {concept_id}")
            continue
        if concept.get("external_id") != external_id:
            errors.append(
                f"sihsalus: procedure status answer {concept_id} must use UUID {external_id}; "
                f"found {concept.get('external_id')}"
            )
        if concept.get("concept_class") != "Misc" or concept.get("datatype") != "N/A":
            errors.append(f"sihsalus: procedure status answer {concept_id} must be Misc/N/A")
        if preferred_spanish_names(concept) != [spanish_name]:
            errors.append(
                f"sihsalus: procedure status answer {concept_id} must prefer {spanish_name!r} in Spanish"
            )

    unknown = concepts.get("4459")
    unknown_spanish_names = {
        name.get("name")
        for name in (unknown or {}).get("names", [])
        if not name.get("retired") and name.get("locale") == "es"
    }
    if "Desconocido" not in unknown_spanish_names:
        errors.append("sihsalus: procedure status Unknown answer must retain Spanish alias 'Desconocido'")

    medication_dispense_uuid = "167157AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    if any(
        (concepts.get(concept_id) or {}).get("external_id") == medication_dispense_uuid
        for concept_id in actual_answer_ids
    ):
        errors.append("sihsalus: medication dispense status must not be used as a procedure status answer")

    snomed_mappings = [
        mapping
        for mapping in active_mappings
        if mapping.get("from_concept_code") == PROCEDURE_STATUS_ID
        and mapping.get("map_type") == "NARROWER-THAN"
        and mapping.get("to_source_url") == "/orgs/IHTSDO/sources/SNOMED-CT/"
        and mapping.get("to_concept_code") == "416342005"
    ]
    if len(snomed_mappings) != 1:
        errors.append(
            "sihsalus: procedure status must have exactly one NARROWER-THAN mapping to SNOMED 416342005"
        )

    duration_units = concepts.get(DURATION_UNITS_ID)
    if not duration_units:
        errors.append(f"sihsalus: missing duration units concept {DURATION_UNITS_ID}")
    else:
        if duration_units.get("external_id") != DURATION_UNITS_EXTERNAL_ID:
            errors.append(
                f"sihsalus: duration units must use OpenMRS UUID {DURATION_UNITS_EXTERNAL_ID}; "
                f"found {duration_units.get('external_id')}"
            )
        if duration_units.get("concept_class") != "ConvSet" or duration_units.get("datatype") != "N/A":
            errors.append("sihsalus: duration units must be ConvSet/N/A")
        if preferred_spanish_names(duration_units) != ["Unidades de duración"]:
            errors.append("sihsalus: duration units must prefer 'Unidades de duración' in Spanish")

    expected_duration_ids = [concept_id for concept_id, _, _ in DURATION_UNIT_MEMBERS]
    actual_duration_ids = ordered_targets(DURATION_UNITS_ID, "CONCEPT-SET")
    if actual_duration_ids != expected_duration_ids:
        errors.append(
            f"sihsalus: duration units members mismatch: "
            f"expected={expected_duration_ids}, actual={actual_duration_ids}"
        )

    for concept_id, external_id, spanish_name in DURATION_UNIT_MEMBERS:
        concept = concepts.get(concept_id)
        if not concept:
            errors.append(f"sihsalus: missing duration unit {concept_id}")
            continue
        if concept.get("external_id") != external_id:
            errors.append(
                f"sihsalus: duration unit {concept_id} must use UUID {external_id}; "
                f"found {concept.get('external_id')}"
            )
        if preferred_spanish_names(concept) != [spanish_name]:
            errors.append(f"sihsalus: duration unit {concept_id} must prefer {spanish_name!r} in Spanish")


def validate_procedure_anatomy_terminology(exports_by_path, concept_records, errors):
    prefix = "procedure anatomy"
    provenance = {
        "upstream_system": PROCEDURE_ANATOMY_HL7_URL,
        "upstream_version": "4.0.0", "translation_owner": "SIHSALUS",
    }
    paths = {PROCEDURE_ANATOMY_CONCEPTS_EXPORT, PROCEDURE_ANATOMY_MAPPINGS_EXPORT}
    if set(OCL_DIR.glob(f"*_SIHSALUS_{PROCEDURE_ANATOMY_SOURCE}_*.zip")) != paths:
        errors.append(f"{prefix}: must bundle only the pinned concepts/mappings pair")
    exports = [exports_by_path.get(path) for path in (
        PROCEDURE_ANATOMY_CONCEPTS_EXPORT, PROCEDURE_ANATOMY_MAPPINGS_EXPORT
    )]
    if not all(isinstance(export, dict) and export for export in exports):
        errors.append(f"{prefix}: required official OCL export is missing")
        return
    for export, counts in zip(exports, ((121, 0), (0, 266))):
        for field, expected in {
            "type": "Source Version", "id": PROCEDURE_ANATOMY_VERSION,
            "version": PROCEDURE_ANATOMY_VERSION, "short_code": PROCEDURE_ANATOMY_SOURCE,
            "owner": "SIHSALUS", "owner_type": "Organization", "released": True,
        }.items():
            if export.get(field) != expected:
                errors.append(f"{prefix}: export {field} must be {expected!r}")
        for key, count in zip(("concepts", "mappings"), counts):
            if not isinstance(export.get(key), list) or len(export[key]) != count:
                errors.append(f"{prefix}: export must contain exactly {count} {key}")
    if not all(isinstance(export.get(key), list) for export in exports
               for key in ("concepts", "mappings")):
        return
    metadata = [{key: value for key, value in export.items()
                 if key not in {"concepts", "mappings"}} for export in exports]
    if metadata[0] != metadata[1]:
        errors.append(f"{prefix}: split exports must preserve identical release metadata")
    combined = dict(exports[0], mappings=exports[1]["mappings"])
    digest = hashlib.sha256(json.dumps(
        combined, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()
    if digest != EXPECTED_PROCEDURE_ANATOMY_CANONICAL_SHA256:
        errors.append(f"{prefix}: canonical official release hash mismatch: actual={digest}")

    source_url = f"/orgs/SIHSALUS/sources/{PROCEDURE_ANATOMY_SOURCE}/"
    set_url = f"{source_url}concepts/{PROCEDURE_ANATOMY_SET_CODE}/"
    source = exports[0].get("source") or {}
    if not isinstance(source, dict):
        errors.append(f"{prefix}: source metadata must be an object")
        return
    for field, expected in {
        "id": PROCEDURE_ANATOMY_SOURCE, "owner": "SIHSALUS", "owner_type": "Organization",
        "custom_validation_schema": "OpenMRS", "default_locale": "es",
    }.items():
        if source.get(field) != expected:
            errors.append(f"{prefix}: source {field} must be {expected!r}")
    if normalize_ocl_url(source.get("url")) != source_url:
        errors.append(f"{prefix}: source URL mismatch")
    if set(source.get("supported_locales") or []) != {"es", "en"}:
        errors.append(f"{prefix}: source must support Spanish and English")
    for field, expected in provenance.items():
        if (source.get("extras") or {}).get(field) != expected:
            errors.append(f"{prefix}: source has invalid {field}")

    by_url = {normalize_ocl_url(concept.get("url")): concept
              for _, _, concept in concept_records}
    by_uuid = defaultdict(list)
    for _, _, concept in concept_records:
        by_uuid[concept.get("external_id")].append(concept)
    concepts = exports[0]["concepts"]
    new_urls = {normalize_ocl_url(concept.get("url")) for concept in concepts}
    for concept in concepts:
        code = concept.get("id")
        is_set = code == PROCEDURE_ANATOMY_SET_CODE
        if concept.get("retired") or concept.get("concept_class") != (
            "ConvSet" if is_set else "Anatomy"
        ) or concept.get("datatype") != "N/A":
            errors.append(f"{prefix}: new concept {code} has invalid class/datatype or is retired")
        if normalize_ocl_url(concept.get("url")) != f"{source_url}concepts/{code}/":
            errors.append(f"{prefix}: new concept {code} must belong to the catalog source")
        if not concept.get("external_id") or len(by_uuid[concept.get("external_id")]) != 1:
            errors.append(f"{prefix}: concept {code} UUID must be bundled exactly once")
        if is_set and concept.get("external_id") != PROCEDURE_ANATOMY_SET_UUID:
            errors.append(f"{prefix}: concept set UUID mismatch")
        spanish = [name for name in concept.get("names", []) if not name.get("retired")
                   and name.get("locale") == "es" and name.get("locale_preferred")
                   and str(name.get("name") or "").strip()]
        if len(spanish) != 1 or normalize_name_type(spanish[0].get("name_type")) != "fully specified":
            errors.append(f"{prefix}: concept {code} must have one preferred Spanish FSN")

    historical = {}
    for code, (hl7, uuid, concept_class, datatype) in PROCEDURE_ANATOMY_HISTORICAL.items():
        url = f"/orgs/SIHSALUS/sources/sihsalus/concepts/{code}/"
        historical[url] = hl7
        concept = by_url.get(url) or {}
        if (concept.get("external_id"), concept.get("concept_class"), concept.get("datatype")) != (
            uuid, concept_class, datatype
        ) or concept.get("retired") or len(by_uuid[uuid]) != 1:
            errors.append(f"{prefix}: historical {code} must preserve identity/class/datatype exactly once")
    expected_members = (new_urls - {set_url}) | set(historical)
    validate_default_name_collision_safety(
        concept_records, errors,
        required_spanish_uuids={(by_url.get(url) or {}).get("external_id") for url in expected_members},
    )
    memberships = defaultdict(list)
    equivalents = defaultdict(list)
    mapping_uuids = set()
    for mapping in exports[1]["mappings"]:
        identifier = mapping.get("id")
        uuid = mapping.get("external_id")
        if not uuid or uuid in mapping_uuids or uuid in by_uuid:
            errors.append(f"{prefix}: mapping {identifier} has missing or duplicate UUID")
        mapping_uuids.add(uuid)
        if mapping.get("retired") or not (
            normalize_ocl_url(mapping.get("url")) or ""
        ).startswith(f"{source_url}mappings/"):
            errors.append(f"{prefix}: mapping {identifier} must be active and owned by the catalog")
        origin = normalize_ocl_url(mapping.get("from_concept_url"))
        target = normalize_ocl_url(mapping.get("to_concept_url"))
        extras = mapping.get("extras") or {}
        if mapping.get("map_type") == "CONCEPT-SET":
            memberships[target].append(mapping)
            concept = by_url.get(target) or {}
            if origin != set_url or target not in expected_members:
                errors.append(f"{prefix}: invalid set membership {identifier}")
            if extras.get("openmrs_uuid") != concept.get("external_id"):
                errors.append(f"{prefix}: membership {identifier} UUID does not match target")
        elif mapping.get("map_type") == "SAME-AS":
            equivalents[origin].append(mapping)
            # OCL 2.3.209 bulk authoring omits the optional native version field.
            # Require provenance version below and reject conflicting native versions.
            if (mapping.get("to_source_url"), mapping.get("to_source_name")) != (
                PROCEDURE_ANATOMY_HL7_URL, "v2-0550"
            ) or mapping.get("to_source_version") not in (None, "4.0.0"):
                errors.append(f"{prefix}: mapping {identifier} must reference HL7 v2-0550 version 4.0.0")
            for field, expected in provenance.items():
                if extras.get(field) != expected:
                    errors.append(f"{prefix}: mapping {identifier} has invalid {field}")
            if not extras.get("display_es") or not extras.get("upstream_display_en"):
                errors.append(f"{prefix}: mapping {identifier} must retain Spanish and original English labels")
        else:
            errors.append(f"{prefix}: unexpected mapping type {mapping.get('map_type')!r}")
    if (set(memberships) != expected_members or len(expected_members) != 133
            or any(len(rows) != 1 for rows in memberships.values())):
        errors.append(f"{prefix}: set membership must cover exactly the 133 unique approved sites")
    if set(equivalents) != expected_members or any(len(rows) != 1 for rows in equivalents.values()):
        errors.append(f"{prefix}: every member must have exactly one HL7 SAME-AS mapping")
    hl7_codes = []
    for url in expected_members:
        rows = equivalents.get(url, [])
        if len(rows) != 1:
            continue
        code = rows[0].get("to_concept_code")
        hl7_codes.append(code)
        concept = by_url.get(url) or {}
        expected_code = historical.get(url) or concept.get("id")
        if not code or code != expected_code:
            errors.append(f"{prefix}: site {url} has incorrect HL7 code")
        if url not in historical and concept.get("extras") != rows[0].get("extras"):
            errors.append(f"{prefix}: site {url} provenance must match its HL7 mapping")
        if not any(name.get("locale") == "es" and name.get("locale_preferred")
                   and not name.get("retired") and str(name.get("name") or "").strip()
                   for name in concept.get("names", [])):
            errors.append(f"{prefix}: member {url} must retain a preferred Spanish name")
        for membership in memberships.get(url, []):
            if (membership.get("extras") or {}).get("upstream_code") != code:
                errors.append(f"{prefix}: membership HL7 code does not match SAME-AS mapping")
    if len(set(hl7_codes)) != len(hl7_codes):
        errors.append(f"{prefix}: HL7 codes must identify unique anatomical sites")

    if not FHIR_CONCEPT_SOURCES_PATH.is_file():
        errors.append(f"{prefix}: required FHIR concept sources CSV is missing")
        return
    with FHIR_CONCEPT_SOURCES_PATH.open(newline="", encoding="utf-8") as stream:
        associations = [row for row in csv.DictReader(stream) if (
            row.get("Uuid") == PROCEDURE_ANATOMY_FHIR_SOURCE_UUID
            or row.get("Concept source") in (PROCEDURE_ANATOMY_CONCEPT_SOURCE_UUID, "v2-0550")
            or row.get("Url") == PROCEDURE_ANATOMY_HL7_URL
        )]
    if len(associations) != 1:
        errors.append(f"{prefix}: must declare exactly one FHIR concept source association")
        return
    for field, expected in {
        "Uuid": PROCEDURE_ANATOMY_FHIR_SOURCE_UUID,
        "Void/Retire": "", "Concept source": PROCEDURE_ANATOMY_CONCEPT_SOURCE_UUID,
        "Url": PROCEDURE_ANATOMY_HL7_URL,
    }.items():
        if associations[0].get(field) != expected:
            errors.append(f"{prefix}: FHIR concept source {field} must be {expected!r}")


def validate_neighborhood_export_identity(path, export, concept_count, mapping_count, errors):
    prefix = str(path)
    if not export:
        errors.append(f"{prefix}: required official OCL export is missing")
        return False

    expected_fields = {
        "type": "Source Version",
        "id": NEIGHBORHOOD_VERSION,
        "version": NEIGHBORHOOD_VERSION,
        "short_code": NEIGHBORHOOD_SOURCE,
        "owner": "SIHSALUS",
        "owner_type": "Organization",
        "released": True,
    }
    for field, expected in expected_fields.items():
        if export.get(field) != expected:
            errors.append(
                f"{prefix}: export {field} must be {expected!r}; found {export.get(field)!r}"
            )

    source = export.get("source") or {}
    if not isinstance(source, dict):
        errors.append(f"{prefix}: export source metadata must be an object")
    else:
        if source.get("id") != NEIGHBORHOOD_SOURCE:
            errors.append(
                f"{prefix}: source id must be {NEIGHBORHOOD_SOURCE!r}; found {source.get('id')!r}"
            )
        if source.get("owner") != "SIHSALUS" or source.get("owner_type") != "Organization":
            errors.append(f"{prefix}: source owner must be the SIHSALUS organization")
        expected_source_url = f"/orgs/SIHSALUS/sources/{NEIGHBORHOOD_SOURCE}/"
        if normalize_ocl_url(source.get("url")) != expected_source_url:
            errors.append(
                f"{prefix}: source URL must be {expected_source_url}; found {source.get('url')!r}"
            )

    concepts = export.get("concepts")
    mappings = export.get("mappings")
    if not isinstance(concepts, list) or len(concepts) != concept_count:
        errors.append(
            f"{prefix}: export must contain exactly {concept_count} concepts; "
            f"found {len(concepts) if isinstance(concepts, list) else 'invalid'}"
        )
    if not isinstance(mappings, list) or len(mappings) != mapping_count:
        errors.append(
            f"{prefix}: export must contain exactly {mapping_count} mappings; "
            f"found {len(mappings) if isinstance(mappings, list) else 'invalid'}"
        )
    return isinstance(concepts, list) and isinstance(mappings, list)


def validate_neighborhood_terminology(exports_by_path, sihsalus_concepts, errors):
    expected_catalog_exports = {
        NEIGHBORHOOD_CONCEPTS_EXPORT,
        NEIGHBORHOOD_MAPPINGS_EXPORT,
    }
    actual_catalog_exports = set(
        OCL_DIR.glob(f"*_SIHSALUS_{NEIGHBORHOOD_SOURCE}_*.zip")
    )
    for path in sorted(actual_catalog_exports - expected_catalog_exports):
        errors.append(
            f"{path}: unexpected neighborhood export; replace it with the exact "
            f"{NEIGHBORHOOD_VERSION} concepts/mappings pair"
        )

    expected_main_exports = {
        EXPECTED_SIHSALUS_CONCEPTS_EXPORT,
        EXPECTED_SIHSALUS_MAPPINGS_EXPORT,
    }
    actual_main_exports = set(OCL_DIR.glob("*_SIHSALUS_sihsalus_*.zip"))
    if actual_main_exports != expected_main_exports:
        missing = sorted(str(path) for path in expected_main_exports - actual_main_exports)
        unexpected = sorted(str(path) for path in actual_main_exports - expected_main_exports)
        errors.append(
            "the main sihsalus source must use the pinned concepts/mappings pair: "
            f"missing={missing}, unexpected={unexpected}"
        )

    concepts_export = exports_by_path.get(NEIGHBORHOOD_CONCEPTS_EXPORT)
    mappings_export = exports_by_path.get(NEIGHBORHOOD_MAPPINGS_EXPORT)
    concepts_export_valid = validate_neighborhood_export_identity(
        NEIGHBORHOOD_CONCEPTS_EXPORT, concepts_export, 11, 0, errors
    )
    mappings_export_valid = validate_neighborhood_export_identity(
        NEIGHBORHOOD_MAPPINGS_EXPORT, mappings_export, 0, 10, errors
    )
    if not concepts_export_valid or not mappings_export_valid:
        return

    concepts_metadata = {
        key: value
        for key, value in concepts_export.items()
        if key not in {"concepts", "mappings"}
    }
    mappings_metadata = {
        key: value
        for key, value in mappings_export.items()
        if key not in {"concepts", "mappings"}
    }
    if concepts_metadata != mappings_metadata:
        errors.append(
            "neighborhood concepts/mappings exports must preserve identical official release metadata"
        )

    reconstructed_export = dict(concepts_export)
    reconstructed_export["mappings"] = mappings_export["mappings"]
    canonical_export = json.dumps(
        reconstructed_export,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    canonical_sha256 = hashlib.sha256(canonical_export).hexdigest()
    if canonical_sha256 != EXPECTED_NEIGHBORHOOD_CANONICAL_SHA256:
        errors.append(
            "recombined neighborhood exports do not match the canonical official released export: "
            f"expected={EXPECTED_NEIGHBORHOOD_CANONICAL_SHA256}, actual={canonical_sha256}"
        )

    concepts = concepts_export["concepts"]
    expected_concepts = [*NEIGHBORHOODS, NEIGHBORHOOD_SET]
    expected_external_ids = {external_id for _, external_id, _ in expected_concepts}
    concepts_by_external_id = defaultdict(list)
    for concept in concepts:
        concepts_by_external_id[concept.get("external_id")].append(concept)

    actual_external_ids = set(concepts_by_external_id)
    if actual_external_ids != expected_external_ids:
        errors.append(
            f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: neighborhood UUID inventory mismatch: "
            f"missing={sorted(expected_external_ids - actual_external_ids)}, "
            f"unexpected={sorted(actual_external_ids - expected_external_ids, key=str)}"
        )

    expected_source_prefix = f"/orgs/SIHSALUS/sources/{NEIGHBORHOOD_SOURCE}/concepts/"
    for concept_id, external_id, spanish_label in expected_concepts:
        matches = concepts_by_external_id.get(external_id, [])
        if len(matches) != 1:
            errors.append(
                f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: UUID {external_id} must occur exactly once; "
                f"found {len(matches)}"
            )
            continue

        concept = matches[0]
        is_set = external_id == NEIGHBORHOOD_SET_UUID
        expected_class = "ConvSet" if is_set else "Misc"
        if concept.get("id") != concept_id:
            errors.append(
                f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: UUID {external_id} must use OCL ID "
                f"{concept_id}; found {concept.get('id')!r}"
            )
        if concept.get("retired"):
            errors.append(f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: {concept_id} must be active")
        if concept.get("concept_class") != expected_class or concept.get("datatype") != "N/A":
            errors.append(
                f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: {concept_id} must be "
                f"{expected_class}/N/A; found {concept.get('concept_class')}/{concept.get('datatype')}"
            )

        expected_extras = {
            "facility": NEIGHBORHOOD_FACILITY,
            "local_code": concept_id,
        }
        if is_set:
            expected_extras["catalog_size"] = len(NEIGHBORHOODS)
        else:
            expected_extras.update(NEIGHBORHOOD_PRESENTATION_METADATA[concept_id])
        if concept.get("extras") != expected_extras:
            errors.append(
                f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: {concept_id} metadata mismatch: "
                f"expected={expected_extras}, actual={concept.get('extras')}"
            )

        expected_url = f"{expected_source_prefix}{concept_id}/"
        if normalize_ocl_url(concept.get("url")) != expected_url:
            errors.append(
                f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: {concept_id} URL must be {expected_url}; "
                f"found {concept.get('url')!r}"
            )

        active_spanish_names = [
            name
            for name in concept.get("names", [])
            if not name.get("retired") and name.get("locale") == "es"
        ]
        preferred_spanish_names = [
            name.get("name") for name in active_spanish_names if name.get("locale_preferred")
        ]
        expected_fsn = spanish_label
        spanish_fsns = [
            name.get("name")
            for name in active_spanish_names
            if normalize_name_type(name.get("name_type")) == "fully specified"
        ]
        if spanish_fsns != [expected_fsn]:
            errors.append(
                f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: {concept_id} must have exactly the Spanish FSN "
                f"{expected_fsn!r}; found {spanish_fsns}"
            )
        if preferred_spanish_names != [expected_fsn]:
            errors.append(
                f"{NEIGHBORHOOD_CONCEPTS_EXPORT}: {concept_id} must prefer its Spanish FSN "
                f"{expected_fsn!r}; found {preferred_spanish_names}"
            )

    main_external_ids = {
        concept.get("external_id") for concept in sihsalus_concepts.values() if concept.get("external_id")
    }
    duplicated_in_main = sorted(expected_external_ids & main_external_ids)
    if duplicated_in_main:
        errors.append(
            "the main sihsalus export must not bundle neighborhood UUIDs, including retired history, "
            "until OCL purges them or the export excludes them explicitly; "
            f"found={duplicated_in_main}"
        )

    mappings = mappings_export["mappings"]
    expected_mapping_targets = [concept_id for concept_id, _, _ in NEIGHBORHOODS]
    mapping_prefix = f"/orgs/SIHSALUS/sources/{NEIGHBORHOOD_SOURCE}/mappings/"
    expected_set_url = f"{expected_source_prefix}{NEIGHBORHOOD_SET[0]}/"
    for mapping in mappings:
        mapping_identifier = mapping.get("id") or mapping.get("external_id") or mapping.get("url")
        prefix = f"{NEIGHBORHOOD_MAPPINGS_EXPORT}: mapping {mapping_identifier}"
        target_id = mapping.get("to_concept_code")
        if mapping.get("retired"):
            errors.append(f"{prefix} must be active")
        if mapping.get("map_type") != "CONCEPT-SET":
            errors.append(f"{prefix} must use CONCEPT-SET")
        if mapping.get("from_concept_code") != NEIGHBORHOOD_SET[0]:
            errors.append(f"{prefix} must originate from {NEIGHBORHOOD_SET[0]}")
        if normalize_ocl_url(mapping.get("from_concept_url")) != expected_set_url:
            errors.append(f"{prefix} has an invalid source-specific from_concept_url")
        expected_target_url = f"{expected_source_prefix}{target_id}/"
        if normalize_ocl_url(mapping.get("to_concept_url")) != expected_target_url:
            errors.append(f"{prefix} has an invalid source-specific to_concept_url")
        mapping_url = normalize_ocl_url(mapping.get("url"))
        if not mapping_url or not mapping_url.startswith(mapping_prefix):
            errors.append(f"{prefix} must belong to the {NEIGHBORHOOD_SOURCE} source")

    def mapping_sort_weight(mapping):
        try:
            return float(mapping.get("sort_weight"))
        except (TypeError, ValueError):
            return float("inf")

    ordered_mappings = sorted(mappings, key=mapping_sort_weight)
    actual_mapping_targets = [mapping.get("to_concept_code") for mapping in ordered_mappings]
    if actual_mapping_targets != expected_mapping_targets:
        errors.append(
            f"{NEIGHBORHOOD_MAPPINGS_EXPORT}: ordered set membership mismatch: "
            f"expected={expected_mapping_targets}, actual={actual_mapping_targets}"
        )
    for position, mapping in enumerate(ordered_mappings, start=1):
        sort_weight = mapping_sort_weight(mapping)
        if sort_weight != position * 10:
            errors.append(
                f"{NEIGHBORHOOD_MAPPINGS_EXPORT}: mapping to "
                f"{mapping.get('to_concept_code')} must have sort_weight {position * 10}; "
                f"found {mapping.get('sort_weight')!r}"
            )


def validate_neighborhood_backend_configuration(errors):
    try:
        with PERSON_ATTRIBUTE_TYPES_PATH.open(newline="") as stream:
            attribute_rows = list(csv.DictReader(stream))
    except OSError as error:
        errors.append(f"{PERSON_ATTRIBUTE_TYPES_PATH}: cannot read person attribute types: {error}")
        attribute_rows = []
    neighborhood_attribute_rows = [
        row for row in attribute_rows if row.get("Uuid") == NEIGHBORHOOD_ATTRIBUTE_TYPE_UUID
    ]
    if len(neighborhood_attribute_rows) != 1:
        errors.append(
            f"{PERSON_ATTRIBUTE_TYPES_PATH}: neighborhood attribute type must occur exactly once"
        )
    else:
        row = neighborhood_attribute_rows[0]
        if (
            row.get("Name") != "Barrio"
            or row.get("Format") != "org.openmrs.Concept"
            or row.get("Foreign UUID") != NEIGHBORHOOD_SET_UUID
            or row.get("Searchable") != "true"
        ):
            errors.append(
                f"{PERSON_ATTRIBUTE_TYPES_PATH}: neighborhood attribute must be a searchable coded "
                "attribute bound to the neighborhood concept set"
            )

    try:
        address_root = ET.parse(ADDRESS_CONFIGURATION_PATH).getroot()
    except (OSError, ET.ParseError) as error:
        errors.append(f"{ADDRESS_CONFIGURATION_PATH}: cannot parse address configuration: {error}")
        return
    legacy_components = [
        component
        for component in address_root.findall("./addressComponents/addressComponent")
        if component.findtext("field") == "ADDRESS_3"
    ]
    if legacy_components:
        errors.append(
            f"{ADDRESS_CONFIGURATION_PATH}: ADDRESS_3/Barrio must be absent after the "
            "confirmed no-data cutover"
        )
    address_lines = [line.text for line in address_root.findall("./lineByLineFormat/string")]
    if "address3" in address_lines:
        errors.append(
            f"{ADDRESS_CONFIGURATION_PATH}: address3 must be absent from the formatted address "
            "after the confirmed no-data cutover"
        )


def validate_referral_transport_terminology(exports_by_path, concept_records, errors):
    expected_exports = {REFERRAL_CONCEPTS_EXPORT}
    actual_exports = set(OCL_DIR.glob(f"*_SIHSALUS_{REFERRAL_SOURCE}_*.zip"))
    if actual_exports != expected_exports:
        missing = sorted(str(path) for path in expected_exports - actual_exports)
        unexpected = sorted(str(path) for path in actual_exports - expected_exports)
        errors.append(
            "the institutional referral terminology must bundle only its approved concepts export: "
            f"missing={missing}, unexpected={unexpected}"
        )

    export = exports_by_path.get(REFERRAL_CONCEPTS_EXPORT)
    if not export:
        errors.append(f"{REFERRAL_CONCEPTS_EXPORT}: required official OCL export is missing")
        return

    expected_fields = {
        "type": "Source Version",
        "id": REFERRAL_VERSION,
        "version": REFERRAL_VERSION,
        "short_code": REFERRAL_SOURCE,
        "owner": "SIHSALUS",
        "owner_type": "Organization",
        "released": True,
    }
    for field, expected in expected_fields.items():
        if export.get(field) != expected:
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: export {field} must be {expected!r}; "
                f"found {export.get(field)!r}"
            )

    source = export.get("source") or {}
    expected_source_url = f"/orgs/SIHSALUS/sources/{REFERRAL_SOURCE}/"
    if not isinstance(source, dict):
        errors.append(f"{REFERRAL_CONCEPTS_EXPORT}: source metadata must be an object")
    else:
        source_expectations = {
            "id": REFERRAL_SOURCE,
            "owner": "SIHSALUS",
            "owner_type": "Organization",
            "custom_validation_schema": "OpenMRS",
            "default_locale": "es",
        }
        for field, expected in source_expectations.items():
            if source.get(field) != expected:
                errors.append(
                    f"{REFERRAL_CONCEPTS_EXPORT}: source {field} must be {expected!r}; "
                    f"found {source.get(field)!r}"
                )
        if set(source.get("supported_locales") or []) != {"es", "en"}:
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: source must support exactly Spanish and English"
            )
        if normalize_ocl_url(source.get("url")) != expected_source_url:
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: source URL must be {expected_source_url}; "
                f"found {source.get('url')!r}"
            )
        if (source.get("extras") or {}).get("catalog_domain") != "institutional-referral":
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: source must identify the institutional-referral domain"
            )

    concepts = export.get("concepts")
    mappings = export.get("mappings")
    if not isinstance(concepts, list) or len(concepts) != len(REFERRAL_TRANSPORT_CONCEPTS):
        errors.append(
            f"{REFERRAL_CONCEPTS_EXPORT}: export must contain exactly "
            f"{len(REFERRAL_TRANSPORT_CONCEPTS)} concepts; "
            f"found {len(concepts) if isinstance(concepts, list) else 'invalid'}"
        )
        return
    if not isinstance(mappings, list) or mappings:
        errors.append(
            f"{REFERRAL_CONCEPTS_EXPORT}: export must contain no mappings; "
            f"found {len(mappings) if isinstance(mappings, list) else 'invalid'}"
        )

    canonical_export = json.dumps(
        export,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    canonical_sha256 = hashlib.sha256(canonical_export).hexdigest()
    if canonical_sha256 != EXPECTED_REFERRAL_CANONICAL_SHA256:
        errors.append(
            "the institutional referral export does not match the canonical official release: "
            f"expected={EXPECTED_REFERRAL_CANONICAL_SHA256}, actual={canonical_sha256}"
        )

    concepts_by_external_id = defaultdict(list)
    for concept in concepts:
        concepts_by_external_id[concept.get("external_id")].append(concept)
    expected_external_ids = {
        external_id for _, external_id, *_ in REFERRAL_TRANSPORT_CONCEPTS
    }
    actual_external_ids = set(concepts_by_external_id)
    if actual_external_ids != expected_external_ids:
        errors.append(
            f"{REFERRAL_CONCEPTS_EXPORT}: referral transport UUID inventory mismatch: "
            f"missing={sorted(expected_external_ids - actual_external_ids)}, "
            f"unexpected={sorted(actual_external_ids - expected_external_ids, key=str)}"
        )

    source_prefix = f"{expected_source_url}concepts/"
    for (
        concept_id,
        external_id,
        spanish_fsn,
        spanish_short,
        english_fsn,
        english_short,
        spanish_description,
    ) in REFERRAL_TRANSPORT_CONCEPTS:
        matches = concepts_by_external_id.get(external_id, [])
        if len(matches) != 1:
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: UUID {external_id} must occur exactly once; "
                f"found {len(matches)}"
            )
            continue

        concept = matches[0]
        if concept.get("id") != concept_id:
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: UUID {external_id} must use OCL ID "
                f"{concept_id}; found {concept.get('id')!r}"
            )
        if concept.get("retired"):
            errors.append(f"{REFERRAL_CONCEPTS_EXPORT}: {concept_id} must be active")
        if concept.get("concept_class") != "Misc" or concept.get("datatype") != "N/A":
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: {concept_id} must be Misc/N/A; "
                f"found {concept.get('concept_class')}/{concept.get('datatype')}"
            )
        expected_url = f"{source_prefix}{concept_id}/"
        if normalize_ocl_url(concept.get("url")) != expected_url:
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: {concept_id} URL must be {expected_url}; "
                f"found {concept.get('url')!r}"
            )

        active_names = [name for name in concept.get("names", []) if not name.get("retired")]
        actual_names = {
            (
                name.get("name"),
                name.get("locale"),
                bool(name.get("locale_preferred")),
                normalize_name_type(name.get("name_type")),
            )
            for name in active_names
        }
        expected_names = {
            (spanish_fsn, "es", True, "fully specified"),
            (spanish_short, "es", False, "short"),
            (english_fsn, "en", True, "fully specified"),
            (english_short, "en", False, "short"),
        }
        if len(active_names) != len(expected_names) or actual_names != expected_names:
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: {concept_id} names mismatch: "
                f"expected={sorted(expected_names)}, actual={sorted(actual_names)}"
            )

        active_descriptions = [
            description
            for description in concept.get("descriptions", [])
            if not description.get("retired")
        ]
        actual_descriptions = {
            (
                description.get("description"),
                description.get("locale"),
                bool(description.get("locale_preferred")),
            )
            for description in active_descriptions
        }
        expected_descriptions = {(spanish_description, "es", True)}
        if (
            len(active_descriptions) != len(expected_descriptions)
            or actual_descriptions != expected_descriptions
        ):
            errors.append(
                f"{REFERRAL_CONCEPTS_EXPORT}: {concept_id} descriptions mismatch: "
                f"expected={sorted(expected_descriptions)}, actual={sorted(actual_descriptions)}"
            )

    bundled_matches = defaultdict(list)
    for zip_path, source_id, concept in concept_records:
        external_id = concept.get("external_id")
        if external_id in expected_external_ids:
            bundled_matches[external_id].append((zip_path, source_id, concept.get("id")))
    for external_id in sorted(expected_external_ids):
        matches = bundled_matches[external_id]
        if len(matches) != 1 or matches[0][0] != REFERRAL_CONCEPTS_EXPORT:
            errors.append(
                f"referral transport UUID {external_id} must be bundled exactly once from "
                f"{REFERRAL_CONCEPTS_EXPORT}; found={matches}"
            )

    if REFERRAL_TRANSPORT_CSV.exists():
        errors.append(
            f"{REFERRAL_TRANSPORT_CSV}: remove the Initializer CSV after bundling the OCL release"
        )


def validate_ocl_global_properties(errors):
    try:
        root = ET.parse(GLOBAL_PROPERTIES_PATH).getroot()
    except (OSError, ET.ParseError) as error:
        errors.append(f"{GLOBAL_PROPERTIES_PATH}: cannot parse global properties: {error}")
        return

    properties = {}
    for global_property in root.findall(".//globalProperty"):
        key = global_property.findtext("property")
        value = global_property.findtext("value")
        if key:
            properties[key.strip()] = (value or "").strip()

    if properties.get("openconceptlab.subscriptionUrl") != EXPECTED_SIHSALUS_SUBSCRIPTION_URL:
        errors.append(
            "openconceptlab.subscriptionUrl must preserve the validated import namespace "
            "until a supported host transition: "
            f"{EXPECTED_SIHSALUS_SUBSCRIPTION_URL}"
        )
    if properties.get("order.durationUnitsConceptUuid") != DURATION_UNITS_EXTERNAL_ID:
        errors.append(
            f"order.durationUnitsConceptUuid must be {DURATION_UNITS_EXTERNAL_ID}; "
            f"found {properties.get('order.durationUnitsConceptUuid')!r}"
        )


def validate_development_forms(concepts, mappings, errors):
    concept_id_by_external_id = {
        concept.get("external_id"): concept.get("id")
        for concept in concepts.values()
        if concept.get("external_id")
    }

    def load_form(filename):
        path = FORM_DIR / filename
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: cannot load form: {error}")
            return None

    def form_questions(form):
        for page in form.get("pages", []):
            for section in page.get("sections", []):
                yield from section.get("questions", [])

    mapping_targets = defaultdict(list)
    for mapping in mappings:
        if mapping.get("map_type") == "Q-AND-A":
            mapping_targets[mapping.get("from_concept_code")].append(mapping.get("to_concept_code"))

    for filename in (
        "CRED-009-EDI.json",
        "CRED-010-TAMIZAJE TEA.json",
        "CRED-011-SALUD MENTAL NIÑO Y CUIDADOR.json",
        "CRED-026-HUANCA TEST VIGILANCIA NEURODESARROLLO.json",
        "CRED-027-LISTA HABILIDADES Y CONDUCTAS ESPERADAS.json",
        "CRED-028-TPED.json",
    ):
        form = load_form(filename)
        if not form:
            continue
        for question in form_questions(form):
            options = question.get("questionOptions") or {}
            question_external_id = options.get("concept")
            if not question_external_id:
                continue
            question_id = concept_id_by_external_id.get(question_external_id)
            if not question_id:
                errors.append(f"{filename}: unresolved question concept {question_external_id}")
                continue
            expected_answers = [
                concept_id_by_external_id.get(answer.get("concept")) for answer in options.get("answers", [])
            ]
            unresolved_answers = [
                answer.get("concept")
                for answer in options.get("answers", [])
                if answer.get("concept") not in concept_id_by_external_id
            ]
            if unresolved_answers:
                errors.append(f"{filename}: unresolved answer concepts {unresolved_answers}")
            if expected_answers and not set(expected_answers).issubset(mapping_targets[question_id]):
                errors.append(
                    f"{filename}: Q-AND-A mismatch for {question_id}: "
                    f"form={expected_answers}, mappings={mapping_targets[question_id]}"
                )

    def questions_by_id(filename):
        form = load_form(filename)
        if not form:
            return None, {}
        return form, {question.get("id"): question for question in form_questions(form)}

    anemia_form, anemia = questions_by_id("CRED-001-TAMIZAJE DE ANEMIA.json")
    if anemia_form:
        if "NTS 213" not in anemia_form.get("description", "") or "NTS 137" in anemia_form.get(
            "description", ""
        ):
            errors.append("CRED-001: description must cite NTS 213 and must not cite NTS 137")
        for question_id in ("edadMeses", "hemoglobina", "altitud", "clasificacionAnemia"):
            if not anemia.get(question_id, {}).get("required"):
                errors.append(f"CRED-001: {question_id} must be required")
        anemia_labels = {
            answer.get("label")
            for answer in (anemia.get("clasificacionAnemia", {}).get("questionOptions") or {}).get(
                "answers", []
            )
        }
        if anemia_labels != {"Sin anemia", "Anemia leve", "Anemia moderada", "Anemia severa"}:
            errors.append("CRED-001: anemia answer labels must not embed a fixed hemoglobin cutoff")
        altitude_alert = anemia.get("altitud", {}).get("alert") or {}
        if altitude_alert.get("alertWhenExpression") != "altitud >= 500":
            errors.append("CRED-001: altitude correction alert must start at 500 m.s.n.m.")

    edi_form, edi = questions_by_id("CRED-009-EDI.json")
    if edi_form:
        for question_id in ("edadCronologicaDias", "resultadoGlobal", "observaciones"):
            if not edi.get(question_id, {}).get("required"):
                errors.append(f"CRED-009: {question_id} must be required")
        if "cinco ejes" not in (edi.get("observaciones", {}).get("questionInfo") or ""):
            errors.append("CRED-009: the summary must explicitly cover the five EDI axes")
        if "No reemplaza" not in edi_form.get("description", ""):
            errors.append("CRED-009: description must state that the summary does not replace the official form")

    mchat_form, mchat = questions_by_id("CRED-010-TAMIZAJE TEA.json")
    if mchat_form:
        for question_id in ("edadMeses", "puntaje", "resultadoGlobal", "senalesAlerta"):
            if not mchat.get(question_id, {}).get("required"):
                errors.append(f"CRED-010: {question_id} must be required")
        if "20 ítems" not in (mchat.get("senalesAlerta", {}).get("questionInfo") or ""):
            errors.append("CRED-010: risk-item traceability must refer to the official 20 items")

    mental_form, mental = questions_by_id("CRED-011-SALUD MENTAL NIÑO Y CUIDADOR.json")
    if mental_form:
        expected_concepts = {
            "instrumentoTamizaje": "f1000000-0000-4000-8000-000000000028",
            "puntajeTamizaje": "f1000000-0000-4000-8000-000000000029",
            "resultadoTamizaje": "f1000000-0000-4000-8000-000000000030",
        }
        for question_id, expected_concept in expected_concepts.items():
            actual = (mental.get(question_id, {}).get("questionOptions") or {}).get("concept")
            if actual != expected_concept:
                errors.append(
                    f"CRED-011: {question_id} must use {expected_concept}; found {actual}"
                )
        if "resultadoSaludMental" in mental:
            errors.append("CRED-011: generic normal/risk/abnormal result must not replace instrument identity")
        if mental.get("observaciones", {}).get("required") is not True:
            errors.append("CRED-011: additional instruments and their results must be documented")
        if "instrumento adicional" not in (mental.get("observaciones", {}).get("questionInfo") or ""):
            errors.append("CRED-011: observations must request every additional instrument")

    growth_form, growth = questions_by_id("CRED-015-CRECIMIENTO Y ESTADO NUTRICIONAL.json")
    if growth_form:
        ambiguous_ids = {
            "clasificacionPesoEdad",
            "clasificacionTallaEdad",
            "clasificacionPesoTalla",
        }
        if ambiguous_ids.intersection(growth):
            errors.append("CRED-015: nutritional indicators must not reuse one generic classification concept")
        for question_id in ("edadMeses", "imc", "perimetroAbdominalCm", "diagnosticoNutricional"):
            if question_id not in growth:
                errors.append(f"CRED-015: missing {question_id}")
        imc_expression = (
            (growth.get("imc", {}).get("questionOptions") or {}).get("calculate") or {}
        ).get("calculateExpression", "")
        if "Math." in imc_expression or "pesoKg" not in imc_expression or "tallaCm" not in imc_expression:
            errors.append("CRED-015: BMI must use a portable calculation from weight and height")

    huanca_form, huanca = questions_by_id("CRED-026-HUANCA TEST VIGILANCIA NEURODESARROLLO.json")
    if huanca_form:
        if "pautaEdad" in huanca:
            errors.append("CRED-026: the obsolete mixed EDI/Huanca age selector must not be exposed")
        for area in ("MotorGrueso", "MotorFino", "Social", "Cognitivo", "Habla"):
            count = huanca.get(f"noLogrados{area}", {})
            detail = huanca.get(f"detalle{area}", {})
            if count.get("required") is not True:
                errors.append(f"CRED-026: noLogrados{area} must be required")
            if not isinstance(detail.get("required"), str):
                errors.append(f"CRED-026: detalle{area} must be conditionally required")

    skills_form, skills = questions_by_id("CRED-027-LISTA HABILIDADES Y CONDUCTAS ESPERADAS.json")
    if skills_form:
        if skills.get("edadMeses", {}).get("required") is not True:
            errors.append("CRED-027: age in months must be required for EDI/referral decisions")
        if skills.get("factorRiesgo", {}).get("required") is not True:
            errors.append("CRED-027: development risk factor must be required for the normative decision")
        if skills.get("accionInmediata", {}).get("readonly") is not True:
            errors.append("CRED-027: immediate action must be calculated and readonly")
        action_expression = (
            (skills.get("accionInmediata", {}).get("questionOptions") or {}).get("calculate") or {}
        ).get("calculateExpression", "")
        if "factorRiesgo" not in action_expression or "edadMeses <= 60" not in action_expression:
            errors.append("CRED-027: EDI/referral calculation must require absence plus a risk factor and age")
        for question_id in ("requiereEdi", "requiereInterconsulta"):
            if "factorRiesgo" not in str(skills.get(question_id, {}).get("required", "")):
                errors.append(f"CRED-027: {question_id} must require a development risk factor")
        if "No sustituye" not in skills_form.get("description", ""):
            errors.append("CRED-027: description must state that the summary does not replace the official list")

    tped_form = load_form("CRED-028-TPED.json")
    if tped_form:
        line_questions = [
            question
            for question in form_questions(tped_form)
            if (question.get("id") or "").startswith("tpedLinea")
        ]
        answer_count = sum(
            len((question.get("questionOptions") or {}).get("answers", []))
            for question in line_questions
        )
        if len(line_questions) != 12 or answer_count != 89:
            errors.append(
                f"CRED-028-TPED.json: expected 12 line questions and 89 answers; "
                f"found {len(line_questions)} and {answer_count}"
            )


if __name__ == "__main__":
    raise SystemExit(main())
