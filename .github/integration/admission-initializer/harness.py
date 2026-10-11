#!/usr/bin/env python3
"""Real Initializer and narrow RBAC test on exclusively owned GitHub CI containers."""

import base64
import csv
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlencode

from guards import (
    BACKEND, DISTRO_SHA, IMAGE_CONTENT_SHA, IMAGE_CONTENT_VERSION, BASELINE_SHA, DATABASE_IMAGE, DATABASE,
    OWNER_LABEL, CANONICAL_ROLE, LEGACY_ROLE, CANONICAL_UUID, EMRAPI_ROLES, CHANGESET,
    INITIALIZER_VERSION, ROLES_FILE, CURRENT_ADMISSION_ADDITIONS, LIQUIBASE_FILE,
    ROLES_CHECKSUM, LIQUIBASE_CHECKSUM, UUID_PATTERN, STRICT_JAVA, HarnessFailure,
    require, checked, validate_runner, properties, extract_archive,
    single_file_archive, assemble, validate_startup, validate_assembly,
    sql_string, backend_owner, admission_privileges,
)

ROOT = Path(__file__).resolve().parents[3]
REVIEWED_FORMS = ("CRED-001-TAMIZAJE DE ANEMIA.json", "OBST-002-EMBARAZO ACTUAL.json",
                  "CE-ANAM-001-ANAMNESIS.json", "CE-EXF-001-EXAMEN FISICO.json",
                  "CE-SOAP-001-NOTA SOAP.json", "CE-001-CONSULTA EXTERNA.json",
                  "OBST-001-ANTECEDENTES.json", "OBST-006-PUERPERIO INMEDIATO.json",
                  "HOSP-010-EPICRISIS OBSTÉTRICO-POSTPARTO.json",
                  "CRED-011-SALUD MENTAL NIÑO Y CUIDADOR.json")
REVIEWED_RANGES = (
    "f0c6d3dc-a0d2-497c-921f-b7266d448fcf", "a769e98e-e91f-4d4c-b029-1c66e267f32a",
    "0502ff16-270e-423f-8fa6-95255fdc9b19", "a75289e3-427c-4e14-ad67-50fc34dcc733",
    "539619f8-19ff-4063-9f6a-03a8d9331012", "5c20e5ae-08d4-4546-b33b-50f757e09ba0",
    "9b3bf521-3b38-478f-8eba-0e329b4fd424", "a486f5a4-3ca6-440f-a8dc-60aab2ea1fd3",
    "1db1f541-ca0b-4f73-9396-f85588ed92a5", "45c9787e-8d00-417e-8d1b-c969dc4e0d9e",
    "90a78c49-0304-47e9-932a-cab13fde4055",
    "e63ce18d-b109-4097-9257-0258fbd54340",
    "ca4e4986-5945-4dd3-bba6-57cb87b267ed",
    "380b13ad-995a-4adc-83bc-454222e81c04",
    "4a7b9f10-7d7b-4cb5-ab6c-3f9fe96809ed",
    "44dcad2a-1a4d-432a-928d-a7b2f15303c4",
    "d42fd5b0-8aa6-44ec-8bab-8b415569da26",
    "7ec23591-4ea6-41ae-b97e-d06b2fe2fce1",
)
OPERATIONAL_CHANGESET = "reconcile-admission-operational-alias-20260921"
COMPLETION = "OpenMRS config loading process completed."
ABORT = "The loading of the 'liquibase' configuration file was aborted:"
FILE_ABORT = re.compile(r"The (?:pre-)?loading of the '(?P<domain>[^'\r\n]+)' configuration file was aborted:")
INITIALIZER_STOPPED = re.compile(r"Disposing of ModuleClassLoader: \{ModuleClassLoader: uid=-?\d+; initializer\}")
STATE_TABLES = {
    "role": "role", "role_privilege": "role,privilege",
    "role_role": "parent_role,child_role", "user_role": "user_id,role",
    "patientflags_tag_role": "tag_id,role", "stockmgmt_user_role_scope": "user_role_scope_id",
}
ADMISSION_SUPPLEMENT = "SIHSALUS Admision Hospitalaria"
SUPPLEMENT_CHANGESET = "retire-admission-hospital-supplement-20260921"
HOSPITAL_ROLES_FILE = "roles/roles_hospital_operations.csv"
HOSPITAL_COMPATIBILITY_FILE = "privileges/privileges_hospital_compatibility.csv"
CLINICAL_DRUG = {
    "uuid": "07c2b995-5619-4d82-8b55-e4cdf96f94d1",
    "name": "ÁCIDO URSODESOXICÓLICO 250 mg - Tableta",
    "concept": "00d9cb0c-4aef-4614-ab38-a9978e3d62e1",
    "name_es": "ÁCIDO URSODESOXICÓLICO",
    "name_en": "Ursodeoxycholic acid",
    "dosage_form": "bd1e9059-62b4-4967-a804-a63eda4f8657",
    "strength": "250 mg",
}

LOADER_DOMAINS = frozenset("""
liquibase jsonkeyvalues conceptclasses conceptsources metadatasharing visittypes
patientidentifiertypes relationshiptypes locationtags privileges encountertypes
encounterroles proceduretypes roles globalproperties attributetypes providerroles
systemtasks locations locationtagmaps addresshierarchy bahmniforms ocl concepts
conceptsets conceptreferencerange billableservices paymentmodes cashpoints
cashieritemprices flagpriorities flagtags flags programs programworkflows
programworkflowstates personattributetypes idgen autogenerationoptions drugs
orderfrequencies ordertypes appointmentspecialities appointmentservicedefinitions
appointmentservicetypes queues datafiltermappings metadatasets metadatasetmembers
metadatatermmappings cohorttypes cohortattributetypes fhirconceptsources
fhirpatientidentifiersystems ampathforms ampathformstranslations htmlforms dispositions
""".split())


def initializer_thread_stacks(output):
    """Keep bounded Java method names, never thread names, arguments or raw dumps."""
    stacks = []
    for block in output.split('\n\n'):
        frames = re.findall(
            r'^\s+at (?:[\w.@+-]+/(?:[\w.@+-]*/)?)?((?:java|jdk|sun|org\.openmrs|org\.hibernate|org\.mariadb|org\.springframework|com\.mysql)\.[\w.$]+)\([^\r\n]*\)$',
            block, re.MULTILINE)
        if any(frame.startswith('org.openmrs.module.initializer.') for frame in frames):
            stacks.append(frames[:24])
            if len(stacks) == 3:
                break
    return stacks


def loader_progress(logs):
    """Report only pinned Initializer domain names and fixed failure categories."""
    loading = re.findall(r"Loading file [^\r\n]*?/configuration/([a-z]+)/", logs)
    completed = re.findall(r"The '([a-z]+)' configuration file has finished loading:", logs)
    categories = {
        "out_of_memory": "java.lang.OutOfMemoryError",
        "connection_timeout": "java.net.SocketTimeoutException",
        "connection_refused": "java.net.ConnectException",
        "dns_failure": "java.net.UnknownHostException",
        "database_deadlock": "Deadlock found when trying to get lock",
        "database_lock_timeout": "Lock wait timeout exceeded",
        "missing_retire_reason": "general.retiredReason.empty",
    }
    return {
        "initializer_last_loading_domain": loading[-1] if loading and loading[-1] in LOADER_DOMAINS else None,
        "initializer_last_completed_domain": completed[-1] if completed and completed[-1] in LOADER_DOMAINS else None,
        "initializer_aborted_domains": sorted({match.group("domain") for match in FILE_ABORT.finditer(logs)
                                               if match.group("domain") in LOADER_DOMAINS}),
        "initializer_failure_hints": [name for name, marker in categories.items() if marker in logs],
    }


def emit(stage, status, **safe):
    print(json.dumps({"stage": stage, "status": status, **safe}), flush=True)


class Harness:
    def __init__(self, env):
        runner_temp = validate_runner(env)
        self.directory = Path(tempfile.mkdtemp(prefix="admission-initializer-", dir=runner_temp))
        self.directory.chmod(0o700)
        self.env = {"PATH": env.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"}
        self.nonce = uuid.uuid4().hex
        self.prefix = "admission-initializer-" + self.nonce[:16]
        self.docker_config = self.directory / "docker-config"
        self.docker_config.mkdir(mode=0o700)
        self.containers, self.volumes = [], []
        self.network = None
        self.deadline = time.monotonic() + 80 * 60
        self.cleanup_deadline = None
        self.candidate_sha = env["GITHUB_SHA"]
        self.password = secrets.token_urlsafe(36) + "Aa1!"
        self.admin_password = secrets.token_urlsafe(36) + "Aa1!"
        self.user_password = secrets.token_urlsafe(36) + "Aa1!"
        self.fixtures = []
        self.lifecycle_files = {}
        self.baseline_data = self.directory / "baseline-data"
        self.baseline_dump = self.directory / "baseline.sql"
        self.mysql_config = self.private("mysql.cnf", "[client]\nuser=root\npassword=" + self.password + "\n")
        self.db_env = self.private("db.env",
            f"MARIADB_DATABASE={DATABASE}\nMARIADB_USER=openmrs\n"
            f"MARIADB_PASSWORD={self.password}\nMARIADB_ROOT_PASSWORD={self.password}\n")
        self.backend_env = self.private("backend.env",
            f"OMRS_DB_HOSTNAME=db\nOMRS_DB_NAME={DATABASE}\nOMRS_DB_USERNAME=openmrs\n"
            f"OMRS_DB_PASSWORD={self.password}\nOMRS_ADMIN_USER_PASSWORD={self.admin_password}\n"
            "OMRS_AUTO_UPDATE_DATABASE=true\nOMRS_CREATE_TABLES=true\n"
            "OMRS_OCL_TOKEN=\nOMRS_MODULE_WEB_ADMIN=false\n"
            "OMRS_EXTRA_INITIALIZER_STARTUP_LOAD=fail_on_error\n"
            "OMRS_EXTRA_INITIALIZER_SKIP_CHECKSUMS=false\n"
            "OMRS_EXTRA_INITIALIZER_ROW_CHECKSUMS_ENABLED=false\n"
            "OMRS_EXTRA_INITIALIZER_LOGGING_LEVEL=INFO\n"
            "OMRS_EXTRA_INITIALIZER_LOGGING_ENABLED=true\n"
            f"OMRS_JAVA_SERVER_OPTS={STRICT_JAVA}\n"
            "OMRS_JAVA_MEMORY_OPTS=-Xms512m -Xmx3g\n")

    def private(self, name, text):
        path = self.directory / name
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
        path.chmod(0o600)
        return path

    def remaining(self, maximum=35 * 60):
        remaining = int(self.deadline - time.monotonic())
        require(remaining > 0, "global_time_budget_exhausted")
        return min(maximum, remaining)

    def docker(self, *args, data=None, timeout=60, allow_failure=False):
        if self.cleanup_deadline is not None:
            remaining = int(self.cleanup_deadline - time.monotonic())
            require(remaining > 0, "cleanup_time_budget_exhausted")
            timeout = min(timeout, 45, remaining)
        return checked(
            ["docker", "--config", str(self.docker_config), "--host",
             "unix:///var/run/docker.sock", *args],
            data=data, timeout=timeout, env=self.env, allow_failure=allow_failure,
            operation="docker_" + args[0])

    def inspect(self, kind, name):
        try:
            result = json.loads(self.docker(kind, "inspect", name).stdout)
        except ValueError:
            raise HarnessFailure("invalid_docker_inspection") from None
        require(isinstance(result, list) and len(result) == 1, "invalid_docker_inspection")
        return result[0]

    def owned(self, kind, name):
        require(name.startswith(self.prefix + "-"), "resource_name_not_owned")
        details = self.inspect(kind, name)
        labels = details.get("Labels") if kind in ("volume", "network") else details.get("Config", {}).get("Labels")
        require(labels and labels.get(OWNER_LABEL) == self.nonce, "resource_ownership_mismatch")
        return details

    def volume(self, suffix):
        name = self.prefix + "-" + suffix
        # Journal the intent first: a client timeout does not prove Docker did
        # not create it. Cleanup must inspect its label or report uncertainty.
        self.volumes.append(name)
        self.docker("volume", "create", "--label", OWNER_LABEL + "=" + self.nonce, name)
        self.owned("volume", name)
        return name

    def container(self, suffix, options, image, command=()):
        name = self.prefix + "-" + suffix
        self.containers.append(name)
        self.docker("create", "--name", name, "--label", OWNER_LABEL + "=" + self.nonce, *options, image, *command)
        self.owned("container", name)
        return name

    def remove_container(self, name):
        self.owned("container", name)
        self.docker("rm", "--force", "--volumes", name, timeout=45)
        self.containers.remove(name)

    def copy_tree(self, container, source, destination, prefix):
        self.owned("container", container)
        archive = self.docker("cp", container + ":" + source, "-", timeout=180).stdout
        extract_archive(archive, destination, prefix)

    def copy_file(self, container, source):
        self.owned("container", container)
        archive = self.docker("cp", container + ":" + source, "-").stdout
        return single_file_archive(archive, PurePosixPath(source).name)

    def git_configuration(self, sha, version, destination):
        checked(["git", "cat-file", "-e", sha + "^{commit}"], cwd=ROOT)
        pom = checked(["git", "show", sha + ":pom.xml"], cwd=ROOT).stdout
        node = ET.fromstring(pom).find("{http://maven.apache.org/POM/4.0.0}version")
        require(node is not None and isinstance(node.text, str), "missing_content_version")
        if version is None:
            require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", node.text), "candidate_release_version_required")
            require(tuple(map(int, node.text.split("."))) > (1, 25, 15), "candidate_reuses_baseline_version")
            self.candidate_version = node.text
        else:
            require(node.text == version, "unexpected_content_version")
        prefix = validate_assembly(
            checked(["git", "show", sha + ":assembly.xml"], cwd=ROOT).stdout,
            legacy=sha == BASELINE_SHA,
        )
        archive = checked(["git", "archive", sha, prefix], cwd=ROOT, timeout=180).stdout
        extract_archive(archive, destination, prefix, package=True)

    def prepare(self):
        emit("prepare", "RUNNING")
        require(sys.platform.startswith("linux"), "linux_required")
        require(Path("/var/run/docker.sock").is_socket(), "local_runner_docker_socket_required")
        require(checked(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.decode().strip() == self.candidate_sha, "checkout_sha_mismatch")
        require(not checked(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT).stdout, "clean_tracked_checkout_required")
        self.docker("pull", "--platform", "linux/amd64", BACKEND, timeout=self.remaining(600))
        self.docker("pull", "--platform", "linux/amd64", DATABASE_IMAGE, timeout=self.remaining(300))
        image = self.inspect("image", BACKEND)
        require(image.get("Os") == "linux" and image.get("Architecture") == "amd64", "unexpected_backend_platform")
        require(image.get("Config", {}).get("Labels", {}).get("org.opencontainers.image.revision") == DISTRO_SHA, "backend_revision_label_mismatch")
        require(BACKEND in image.get("RepoDigests", []), "backend_digest_mismatch")
        command = " ".join((image["Config"].get("Entrypoint") or []) + (image["Config"].get("Cmd") or []))
        require("startup.sh" in command, "unverified_image_launch_command")
        runtime_user = image["Config"].get("User", "")
        require(re.fullmatch(r"[1-9][0-9]*(?::[0-9]+)?", runtime_user), "numeric_nonroot_backend_user_required")
        probe = self.container("probe",
            ["--network", "none", "--read-only", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges", "--entrypoint", "/bin/sh"],
            BACKEND, ["-ceu", "id -u; id -g"])
        identity = self.docker("start", "--attach", probe, timeout=30).stdout
        self.backend_owner = backend_owner(runtime_user, identity)
        self.image_config = self.directory / "image-configuration"
        self.copy_tree(probe, "/openmrs/distribution/openmrs_config", self.image_config, "openmrs_config")
        startup_hash = validate_startup(self.copy_file(probe, "/openmrs/startup-init.sh"))
        startup = self.copy_file(probe, "/openmrs/startup.sh").decode()
        require("source /openmrs/startup-init.sh" in startup and "/usr/local/tomcat/bin/catalina.sh run" in startup, "unverified_image_entrypoint")
        distro = properties(self.copy_file(probe, "/openmrs/distribution/openmrs-distro.properties"))
        require(distro.get("content.sihsalus-content") == IMAGE_CONTENT_VERSION, "image_content_version_mismatch")
        self.remove_container(probe)
        original, baseline, candidate = [self.directory / name for name in ("source-image", "source-15", "source-candidate")]
        for sha, version, path in ((IMAGE_CONTENT_SHA, IMAGE_CONTENT_VERSION, original), (BASELINE_SHA, "1.25.15", baseline), (self.candidate_sha, None, candidate)):
            self.git_configuration(sha, version, path)
        self.privileges = admission_privileges(baseline)
        self.candidate_privileges = admission_privileges(candidate, CURRENT_ADMISSION_ADDITIONS)
        require(self.candidate_privileges == self.privileges | CURRENT_ADMISSION_ADDITIONS, "unreviewed_current_admission_policy")
        with (candidate / HOSPITAL_ROLES_FILE).open(encoding="utf-8-sig", newline="") as handle:
            self.hospital_roles = list(csv.DictReader(handle))
        require({row["Role name"] for row in self.hospital_roles} == {
            "SIHSALUS Laboratorio", "SIHSALUS Soporte"},
            "hospital_role_scope_changed")
        with (candidate / ROLES_FILE).open(encoding="utf-8-sig", newline="") as handle:
            laboratory = [row for row in csv.DictReader(handle) if row["Role name"] == "Laboratorio"]
        require(len(laboratory) == 1 and laboratory[0]["Uuid"] == "2049b153-6d8c-4bc1-96ab-f34f0ca43285",
                "canonical_laboratory_identity_changed")
        with (baseline / ROLES_FILE).open(encoding="utf-8-sig", newline="") as handle:
            old_laboratory = [row for row in csv.DictReader(handle) if row["Role name"] == "Laboratorio"]
        require(len(old_laboratory) == 1 and
                set(laboratory[0]["Privileges"].split(";")) ==
                set(old_laboratory[0]["Privileges"].split(";")) | {"Get Patient Programs"},
                "unreviewed_laboratory_privilege_delta")
        self.canonical_laboratory = laboratory
        with (candidate / HOSPITAL_COMPATIBILITY_FILE).open(encoding="utf-8-sig", newline="") as handle:
            self.hospital_compatibility = {row["Privilege name"] for row in csv.DictReader(handle)}
        require(len(self.hospital_compatibility) == 5 and
                all(name.startswith("app:") for name in self.hospital_compatibility),
                "hospital_compatibility_scope_changed")
        self.baseline_config, self.candidate_config = self.directory / "config-baseline", self.directory / "config-candidate"
        assemble(self.image_config, original, baseline, self.baseline_config)
        receipt = assemble(self.image_config, original, candidate, self.candidate_config)
        # Exercise the historical checksum regression independently of later
        # approved role changes, then load the exact candidate CSV separately.
        self.historical_config = self.directory / "config-historical-roles"
        shutil.copytree(self.candidate_config, self.historical_config)
        shutil.copyfile(baseline / ROLES_FILE, self.historical_config / ROLES_FILE)
        self.role_md5 = hashlib.md5((baseline / ROLES_FILE).read_bytes()).hexdigest()
        self.candidate_role_md5 = hashlib.md5((candidate / ROLES_FILE).read_bytes()).hexdigest()
        self.network = self.prefix + "-network"
        self.docker("network", "create", "--internal", "--label", OWNER_LABEL + "=" + self.nonce, self.network)
        require(self.owned("network", self.network).get("Internal") is True, "network_not_internal")
        emit("prepare", "PASSED", source_sha=self.candidate_sha, baseline_sha=BASELINE_SHA,
             candidate_version=self.candidate_version,
             backend_digest=BACKEND.split("@")[1], startup_sha256=startup_hash, **receipt)

    def start_database(self, suffix):
        volume = self.volume(suffix + "-db")
        name = self.container(suffix + "-db",
            ["--network", self.network, "--network-alias", "db", "--memory", "1g", "--cpus", "1",
             "--env-file", str(self.db_env),
             "--mount", "type=volume,src=" + volume + ",dst=/var/lib/mysql",
             "--mount", "type=bind,src=" + str(self.mysql_config) + ",dst=/run/admission-mysql.cnf,readonly"],
            DATABASE_IMAGE, ["mariadbd", "--character-set-server=utf8mb4", "--collation-server=utf8mb4_bin",
                             "--innodb-flush-log-at-trx-commit=2"])
        self.docker("start", name)
        deadline = time.monotonic() + self.remaining(180)
        while time.monotonic() < deadline:
            result = self.docker("exec", name, "mariadb", "--defaults-extra-file=/run/admission-mysql.cnf",
                "--batch", "--skip-column-names", "-e", "SELECT VERSION()", allow_failure=True)
            if result.returncode == 0:
                require(result.stdout.decode().strip().startswith("10.11.7-"), "database_version_mismatch")
                require(self.query(name, "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=" + sql_string(DATABASE)) == ["0"], "database_not_empty")
                require(self.query(name, "SELECT @@GLOBAL.innodb_flush_log_at_trx_commit") == ["2"],
                        "disposable_database_flush_mode_mismatch")
                emit("database", "PASSED", innodb_flush_log_at_trx_commit=2, power_loss_durability_tested=False)
                return name
            time.sleep(5)
        raise HarnessFailure("database_startup_timeout")

    def query(self, db, sql):
        self.owned("container", db)
        result = self.docker("exec", "-i", db, "mariadb", "--defaults-extra-file=/run/admission-mysql.cnf",
            "--default-character-set=utf8mb4", "--batch", "--skip-column-names", DATABASE,
            data=sql.encode(), timeout=120)
        return result.stdout.decode().splitlines()

    def import_baseline(self, db):
        self.owned("container", db)
        self.docker("exec", "-i", db, "mariadb", "--defaults-extra-file=/run/admission-mysql.cnf",
            DATABASE, data=self.baseline_dump.read_bytes(), timeout=self.remaining(300))

    def start_backend(self, suffix, configuration, data_volume=None, restore=False):
        require(re.fullmatch(r"[a-z][a-z-]*", suffix), "invalid_backend_phase")
        lifecycle_file = "admission-initializer-" + self.nonce + "-" + suffix + ".log"
        require(lifecycle_file not in self.lifecycle_files.values(), "reused_initializer_log")
        volume = data_volume or self.volume(suffix + "-data")
        self.owned("volume", volume)
        if restore:
            require(re.fullmatch(r"[1-9][0-9]*:[0-9]+", self.backend_owner), "backend_restore_owner_unverified")
            helper = self.container(suffix + "-restore",
                ["--network", "none", "--user", "0",
                 "--mount", "type=bind,src=" + str(self.baseline_data) + ",dst=/seed,readonly",
                 "--mount", "type=volume,src=" + volume + ",dst=/openmrs/data", "--entrypoint", "/bin/bash"],
                BACKEND, ["-ceu", "test -d /seed/configuration_checksums; cp -a /seed/. /openmrs/data/; chown -R " + self.backend_owner + " /openmrs/data"])
            self.docker("start", "--attach", helper, timeout=self.remaining(180))
            self.remove_container(helper)
        name = self.container(suffix,
            ["--network", self.network, "--memory", "4g", "--cpus", "2", "--env-file", str(self.backend_env),
             "--env", "OMRS_EXTRA_INITIALIZER_LOGGING_LOCATION=" + lifecycle_file,
             "--mount", "type=bind,src=" + str(configuration) + ",dst=/openmrs/distribution/openmrs_config,readonly",
             "--mount", "type=volume,src=" + volume + ",dst=/openmrs/data"], BACKEND)
        self.lifecycle_files[name] = lifecycle_file
        self.docker("start", name)
        return name, volume

    def request(self, backend, method, resource, body=None, restricted=False):
        self.owned("container", backend)
        require(method in ("GET", "POST", "DELETE"), "unsupported_internal_method")
        require(resource.startswith("/") and not any(char in resource for char in ('\n', '\r', '"', '\\')), "unsafe_internal_resource")
        user = self.fixtures[0]["username"] if restricted else "admin"
        password = self.user_password if restricted else self.admin_password
        auth = base64.b64encode((user + ":" + password).encode()).decode()
        config = (
            "silent\nshow-error\nnoproxy = \"*\"\nconnect-timeout = 5\nmax-time = 20\n"
            "max-redirs = 0\nretry = 0\n"
            f"url = \"http://127.0.0.1:8080/openmrs/ws/rest/v1{resource}\"\nrequest = \"{method}\"\n"
            f"header = \"Authorization: Basic {auth}\"\nheader = \"Content-Type: application/json\"\n"
            "write-out = \"\\n%{http_code}\"\n")
        if body is not None:
            config += "data = " + json.dumps(json.dumps(body, separators=(",", ":"))) + "\n"
        result = self.docker("exec", "-i", backend, "curl", "--config", "-", data=config.encode(), timeout=30, allow_failure=True)
        if result.returncode:
            return None, None
        content, separator, code = result.stdout.rpartition(b"\n")
        require(separator and re.fullmatch(rb"\d{3}", code), "invalid_internal_http_response")
        try:
            parsed = json.loads(content) if content else None
        except ValueError:
            parsed = None
        return int(code), parsed

    def module_status(self, backend):
        code, body = self.request(backend, "GET", "/module/initializer?v=full")
        # The installation filter can still redirect after Initializer finishes.
        # Do not follow it or accept it as readiness; the startup deadline applies.
        require(code not in (None, 302, 502, 503, 504), "module_state_unavailable")
        require(code == 200, "module_state_http_" + str(code))
        require(isinstance(body, dict), "module_state_malformed")
        require(body.get("uuid") == "initializer", "initializer_module_missing")
        require(body.get("version") == INITIALIZER_VERSION, "initializer_version_mismatch")
        require(isinstance(body.get("started"), bool), "initializer_started_state_missing")
        return body["started"]

    def bootstrap(self, backend):
        """Trigger the synthetic installation filter; HTTP is not a success oracle."""
        self.owned("container", backend)
        config = (
            "silent\nshow-error\nproxy = \"\"\nnoproxy = \"*\"\n"
            "connect-timeout = 2\nmax-time = 5\nmax-redirs = 0\nretry = 0\n"
            "url = \"http://127.0.0.1:8080/openmrs/initialsetup\"\nrequest = \"GET\"\n"
            "output = \"/dev/null\"\nwrite-out = \"%{http_code}\"\n")
        # --disable is curl's first option: no inherited curlrc, credentials,
        # cookies, redirects or retry settings. The response body is discarded.
        result = self.docker("exec", "-i", backend, "curl", "--disable", "--config", "-",
            data=config.encode(), timeout=10, allow_failure=True)
        if result.returncode:
            return None
        require(re.fullmatch(rb"[1-5][0-9]{2}", result.stdout), "invalid_bootstrap_http_code")
        return int(result.stdout)

    def installation_progress(self, backend):
        """Read typed flags and counters; never return installer messages or logs."""
        self.owned("container", backend)
        config = (
            "silent\nshow-error\nproxy = \"\"\nnoproxy = \"*\"\n"
            "connect-timeout = 2\nmax-time = 5\nmax-redirs = 0\nretry = 0\n"
            "url = \"http://127.0.0.1:8080/openmrs/initialsetup?page=progress.vm.ajaxRequest\"\n"
            "request = \"GET\"\nwrite-out = \"\\n%{http_code}\"\n")
        result = self.docker("exec", "-i", backend, "curl", "--disable", "--config", "-",
            data=config.encode(), timeout=10, allow_failure=True)
        if result.returncode:
            return None, None, None, None
        content, separator, code = result.stdout.rpartition(b"\n")
        if not separator or code != b"200":
            return None, None, None, None
        try:
            body = json.loads(content)
        except ValueError:
            return None, None, None, None
        if not isinstance(body, dict):
            return None, None, None, None
        has_errors, complete = body.get("hasErrors"), body.get("initializationComplete")
        counters = [body.get(key) for key in ("actionCounter", "completedPercentage")]
        # Core's per-task percentage can reset or exceed 100; it is not readiness.
        counters = [value if type(value) is int and value >= 0 else None for value in counters]
        return (has_errors if isinstance(has_errors, bool) else None,
                complete if isinstance(complete, bool) else None, *counters)

    def effective_strict(self, backend):
        values = properties(self.copy_file(backend, "/openmrs/data/openmrs-runtime.properties"))
        require(values.get("initializer.startup.load") == "fail_on_error", "strict_runtime_property_missing")
        require(values.get("initializer.skip.checksums") == "false", "checksum_tracking_not_enabled")
        require(values.get("initializer.row.checksums.enabled") == "false", "row_checksum_mode_changed")
        require(values.get("initializer.logging.enabled") == "true"
                and values.get("initializer.logging.level") == "INFO"
                and values.get("initializer.logging.location") == self.lifecycle_files[backend],
                "current_attempt_initializer_logging_not_configured")
        require(not values.get("initializer.domains"), "initializer_domain_filter_forbidden")
        require(not any(key.startswith("initializer.exclude") and value for key, value in values.items()), "initializer_exclusions_forbidden")
        actual = self.owned("container", backend)
        env = dict(item.split("=", 1) for item in actual["Config"]["Env"] if "=" in item)
        require(env.get("OMRS_JAVA_SERVER_OPTS") == STRICT_JAVA, "strict_system_flags_changed")

    def lifecycle_logs(self, backend):
        """Read this attempt's dedicated file and container output, never a restored log."""
        self.owned("container", backend)
        filename = self.lifecycle_files[backend]
        require(re.fullmatch(r"admission-initializer-[0-9a-f]{32}-[a-z-]+\.log", filename), "invalid_initializer_log_path")
        output = self.docker("logs", "--tail", "5000", backend)
        log = self.docker("exec", backend, "/bin/sh", "-c",
            'if [ ! -e "$1" ]; then exit 44; fi; test -f "$1" && test ! -L "$1" && cat "$1"',
            "--", "/openmrs/data/" + filename, allow_failure=True)
        require(log.returncode in (0, 44), "initializer_log_unreadable")
        present = log.returncode == 0
        logs = (output.stdout + output.stderr + (log.stdout if present else b"")).decode("utf-8", "replace")
        return logs, present, len(log.stdout) if present else None

    def wait_initializer(self, backend, stage, reject=False):
        started_at = time.monotonic()
        # The historical baseline can still be loading at the normal startup limit.
        startup_budget = self.remaining(45 * 60) if stage == "baseline" else self.remaining()
        deadline = started_at + startup_budget
        next_diagnostic = started_at
        observed = None
        while time.monotonic() < deadline:
            require(self.owned("container", backend)["State"].get("Running") is True, "backend_exited_before_validation")
            # The image's one-shot startup request may precede web readiness.
            # Reach the fixed filter directly, without following root redirects.
            bootstrap_code = self.bootstrap(backend)
            logs, log_present, log_bytes = self.lifecycle_logs(backend)
            abort_messages = [match.group(0) for match in FILE_ABORT.finditer(logs)]
            csv_error = "BEGINNING OF CSV FILE ERROR SUMMARY" in logs
            expected_rejection = reject and ABORT in logs and CHANGESET in logs
            unexpected_abort = csv_error or any(message != ABORT for message in abort_messages) or (
                bool(abort_messages) and not expected_rejection)
            now = time.monotonic()
            if now >= next_diagnostic or unexpected_abort:
                has_errors, installation_complete, action_counter, percentage = self.installation_progress(backend)
                emit(stage, "WAITING", backend_running=True, bootstrap_http_code=bootstrap_code,
                     completion_seen=COMPLETION in logs, abort_seen=bool(abort_messages),
                     candidate_marker_seen=CHANGESET in logs,
                     csv_error_seen=csv_error, installation_has_errors=has_errors,
                     installation_complete=installation_complete,
                     installation_action_counter=action_counter,
                     installation_completed_percentage=percentage,
                     initializer_log_present=log_present, initializer_log_bytes=log_bytes,
                     **loader_progress(logs))
                next_diagnostic = now + 60
                require(has_errors is not True, "installation_reported_errors")
            # A separate failure cannot be masked by the expected Liquibase
            # rejection. Diagnostics allow only known domains, never filenames or raw logs.
            if unexpected_abort:
                raise HarnessFailure("unexpected_initializer_abort")
            if expected_rejection:
                require(COMPLETION not in logs, "initializer_continued_after_rejection")
                observed = False
            if COMPLETION in logs:
                require(not reject, "expected_rejection_did_not_occur")
                observed = True
            if observed is not None:
                self.effective_strict(backend)
                # Core stops REST too after this startup exception. Its classloader
                # disposal follows removal from the actual started-modules map.
                if reject:
                    if INITIALIZER_STOPPED.search(logs):
                        emit(stage, "PASSED", initializer_started=False)
                        return
                    time.sleep(5)
                    continue
                try:
                    started = self.module_status(backend)
                except HarnessFailure as error:
                    if str(error) != "module_state_unavailable":
                        raise
                    # Lifecycle logs precede web availability. Keep polling;
                    # Unavailable HTTP is never interpreted as false; malformed
                    # successful responses and authentication failures are fatal.
                else:
                    if started == observed:
                        emit(stage, "PASSED", initializer_started=started)
                        return
            time.sleep(5)
        emit(stage, "FAILED", reason="initializer_lifecycle_not_proven_before_timeout",
             **self.jvm_diagnostic(backend))
        raise HarnessFailure("initializer_lifecycle_not_proven_before_timeout")

    def jvm_diagnostic(self, backend):
        self.owned("container", backend)
        try:
            result = self.docker("exec", backend, "jcmd", "0", "Thread.print", timeout=10, allow_failure=True)
        except HarnessFailure:
            result = None
        available = result is not None and result.returncode == 0
        return {"jvm_thread_dump_available": available,
                "initializer_thread_stacks": initializer_thread_stacks(result.stdout.decode("utf-8", "replace")) if available else []}

    def checksum(self, backend, relative):
        value = self.copy_file(backend, "/openmrs/data/" + relative).decode("ascii")
        require(re.fullmatch(r"[0-9a-f]{32}", value), "invalid_initializer_checksum")
        return value

    def absent_checksum(self, backend, relative):
        result = self.docker("exec", backend, "test", "-e", "/openmrs/data/" + relative, allow_failure=True)
        require(result.returncode == 1, "unexpected_checksum_file")

    def assert_checksums(self, backend, role_md5=None):
        require(self.checksum(backend, ROLES_CHECKSUM) == (role_md5 or self.role_md5), "roles_checksum_mismatch")
        # LiquibaseLoader2_5 explicitly skips checksum WRITES. Never invent one;
        # an inherited checksum could suppress loading, so that state is blocked.
        self.absent_checksum(backend, LIQUIBASE_CHECKSUM)

    def history(self, db):
        rows = self.query(db, "SELECT * FROM liquibasechangelog ORDER BY ID,AUTHOR,FILENAME")
        columns = [row.split("\t", 1)[0] for row in self.query(db, "SHOW COLUMNS FROM liquibasechangelog")]
        required = {"ID", "AUTHOR", "FILENAME", "MD5SUM", "DATEEXECUTED", "ORDEREXECUTED", "EXECTYPE", "DEPLOYMENT_ID"}
        require(required <= set(columns) and len(columns) == len(set(columns)), "history_columns_invalid")
        # The pinned audit module (13712f1) declares these four native checks
        # runAlways. Liquibase updates their execution metadata on every startup.
        # Keep their identity/checksum and every other column, including future
        # columns. Content and all other modules retain their complete rows.
        repeated = {("sihsalusaudit-20260819-" + suffix, "sihsalus", "liquibase.xml")
                    for suffix in ("07-no-update", "08-no-delete", "09-validate", "10-mariadb-validate")}
        result = []
        for row in rows:
            values = row.split("\t")
            require(len(values) == len(columns), "history_column_shape_changed")
            data = dict(zip(columns, values))
            if tuple(data[key] for key in ("ID", "AUTHOR", "FILENAME")) in repeated:
                permitted = {"EXECUTED", "RERAN"}
                if data["ID"].endswith(("07-no-update", "08-no-delete")):
                    permitted.add("MARK_RAN")
                require(data["EXECTYPE"] in permitted, "native_audit_execution_invalid")
                for column in ("DATEEXECUTED", "ORDEREXECUTED", "EXECTYPE", "DEPLOYMENT_ID"):
                    data[column] = "<native-runAlways-execution>"
            result.append("\t".join(data[column] for column in columns))
        return result

    def candidate_recorded(self, db, identifier=CHANGESET):
        records = self.query(db, "SELECT MD5SUM,EXECTYPE FROM liquibasechangelog WHERE ID=" + sql_string(identifier))
        if not records:
            return False
        require(len(records) == 1 and re.fullmatch(r"\d+:[0-9a-f]{32}\tEXECUTED", records[0]), "candidate_history_invalid")
        return True

    def assert_rejected_history(self, db, before):
        # The new preparatory changeset is a no-op outside the 55-permission
        # input. Its own committed record precedes the original guard's failure.
        after = self.history(db)
        preparatory = [row for row in after if row.split("\t", 1)[0] == OPERATIONAL_CHANGESET]
        require(len(preparatory) == 1 and self.candidate_recorded(db, OPERATIONAL_CHANGESET)
                and [row for row in after if row not in preparatory] == before,
                "rejected_migration_changed_history")

    def state(self, db):
        existing = set(self.query(db, "SHOW TABLES"))
        return {table: self.query(db, "SELECT * FROM " + table + " ORDER BY " + order)
                for table, order in STATE_TABLES.items() if table in existing}

    def assert_state(self, db, expected, reason):
        actual = self.normalized_state(self.state(db))
        expected = self.normalized_state(expected)
        for table in STATE_TABLES:
            if actual.get(table) != expected.get(table):
                before, after = Counter(expected.get(table, [])), Counter(actual.get(table, []))
                emit("rbac_snapshot", "FAILED", table=table,
                     expected_present=table in expected, actual_present=table in actual,
                     removed_rows=sum((before - after).values()), added_rows=sum((after - before).values()))
        require(actual == expected, reason)

    def expected_upgrade_state(self, db, before):
        """Explicit relational oracle; no execution or translation of candidate SQL."""
        expected = {}
        for table, rows in before.items():
            columns = [row.split("\t", 1)[0] for row in self.query(db, "SHOW COLUMNS FROM " + table)]
            transformed = []
            inserted_legacy_references = set()
            for row in rows:
                values = row.split("\t")
                require(len(values) == len(columns), "snapshot_column_shape_changed")
                data = dict(zip(columns, values))
                if table in ("role", "role_privilege", "user_role") and data.get("role") == ADMISSION_SUPPLEMENT:
                    continue
                if table == "role" and data["role"] == LEGACY_ROLE:
                    continue
                if table == "role_privilege" and data["role"] in (CANONICAL_ROLE, LEGACY_ROLE):
                    continue
                legacy_reference = table in ("user_role", "patientflags_tag_role") and data["role"] == LEGACY_ROLE
                if "role" in data and data["role"] == LEGACY_ROLE:
                    data["role"] = CANONICAL_ROLE
                if table == "role" and data["role"] == CANONICAL_ROLE:
                    data["uuid"] = CANONICAL_UUID
                rewritten = "\t".join(data[column] for column in columns)
                if legacy_reference:
                    # Only the legacy references inserted by this migration are
                    # deduplicated. Existing canonical/unrelated multiplicities
                    # must remain unchanged, including Patient Flags rows.
                    if rewritten not in rows and rewritten not in inserted_legacy_references:
                        transformed.append(rewritten)
                        inserted_legacy_references.add(rewritten)
                else:
                    transformed.append(rewritten)
            if table == "role_privilege":
                for privilege in self.privileges:
                    data = {"role": CANONICAL_ROLE, "privilege": privilege}
                    transformed.append("\t".join(data[column] for column in columns))
            # Stock IDs and every audit column remain part of each whole row.
            expected[table] = sorted(transformed)
        return self.expected_hospital_role_state(db, expected)

    def expected_hospital_role_state(self, db, before, roles=None):
        """Add the reviewed native CSV delta without discarding unrelated rows.

        Initializer preserves an existing role's UUID when it resolves by name.
        All user, Patient Flags, and stock-scope references remain exact rows.
        """
        roles = self.hospital_roles if roles is None else roles
        if not roles:
            return before
        expected = {table: list(rows) for table, rows in before.items()}
        columns = [row.split("\t", 1)[0] for row in self.query(db, "SHOW COLUMNS FROM role")]
        require(set(columns) == {"role", "description", "uuid"}, "hospital_role_schema_changed")
        grants_columns = [row.split("\t", 1)[0] for row in self.query(db, "SHOW COLUMNS FROM role_privilege")]
        require(grants_columns == ["role", "privilege"], "hospital_grants_schema_changed")
        role_index = columns.index("role")
        uuid_index = columns.index("uuid")
        for row in roles:
            name, identifier = row["Role name"], row["Uuid"]
            require(not row["Inherited roles"].strip(), "hospital_role_inheritance_unreviewed")
            existing = [value.split("\t") for value in expected["role"] if value.split("\t")[role_index] == name]
            require(len(existing) <= 1, "hospital_role_name_collision")
            require(not any(value.split("\t")[uuid_index] == identifier and value.split("\t")[role_index] != name
                            for value in expected["role"]), "hospital_role_uuid_collision")
            if existing:
                identifier = existing[0][uuid_index]
            expected["role"] = [value for value in expected["role"] if value.split("\t")[role_index] != name]
            values = {"role": name, "description": row["Description"], "uuid": identifier}
            expected["role"].append("\t".join(values[column] for column in columns))
            expected["role_privilege"] = [value for value in expected["role_privilege"] if value.split("\t")[0] != name]
            expected["role_privilege"].extend(name + "\t" + privilege for privilege in row["Privileges"].split(";") if privilege)
            # Only the child's inherited parents are replaced by RoleLineProcessor.
            expected["role_role"] = [value for value in expected["role_role"] if value.split("\t")[1] != name]
        return {table: sorted(rows) for table, rows in expected.items()}

    @staticmethod
    def normalized_state(state):
        return {table: sorted(rows) for table, rows in state.items()}

    def expected_emrapi_refresh(self, before):
        # EMRAPI contextRefreshed precedes Initializer. Its pinned implementation
        # classifies lowercase app: names as API privileges (only 'App: ' and
        # 'Task: ' are excluded), and adds these five safe compatibility names
        # to both module-owned privilege levels on the next startup.
        expected = {table: list(rows) for table, rows in before.items()}
        grants = expected["role_privilege"]
        for role in EMRAPI_ROLES:
            for privilege in self.hospital_compatibility:
                value = role + "\t" + privilege
                if value not in grants:
                    grants.append(value)
        return self.normalized_state(expected)

    def check_admission(self, db, privileges=None):
        require(self.query(db, "SELECT role,uuid FROM role WHERE role IN ('Admision','SIHSALUS Admision')") == [CANONICAL_ROLE + "\t" + CANONICAL_UUID], "final_admission_identity_mismatch")
        require(set(self.query(db, "SELECT privilege FROM role_privilege WHERE role='Admision'")) == (privileges or self.privileges), "final_admission_privileges_mismatch")
        require(self.query(db, "SELECT COUNT(*) FROM role_role WHERE parent_role IN ('Admision','SIHSALUS Admision') OR child_role IN ('Admision','SIHSALUS Admision')") == ["0"], "final_admission_inheritance_present")
        for fixture in self.fixtures:
            rows = self.query(db, "SELECT r.role FROM user_role r JOIN users u ON u.user_id=r.user_id WHERE u.uuid=" + sql_string(fixture["uuid"]))
            require(rows == [CANONICAL_ROLE], "synthetic_user_assignment_not_preserved")

    def check_emrapi_roles(self, db):
        expected = [role + "\t" + identifier for role, identifier in EMRAPI_ROLES.items()]
        require(self.query(db, "SELECT role,uuid FROM role WHERE role IN ("
                + ",".join(sql_string(role) for role in EMRAPI_ROLES) + ") ORDER BY role") == expected,
                "emrapi_role_identity_mismatch")

    def check_arrival_payment(self, db):
        rows = self.query(db, "SELECT retired,min_occurs,max_occurs,datatype "
            "FROM visit_attribute_type WHERE uuid='090eb9b3-a306-450f-8623-9fc00b8d82fa'")
        require(rows == ["0\t0\t1\torg.openmrs.customdatatype.datatype.FreeTextDatatype"],
                "arrival_payment_metadata_invalid")
        emit("arrival_payment_metadata", "PASSED", active=True, min_occurs=0, max_occurs=1)

    def form_schema_snapshot(self, db):
        names = [json.loads((self.candidate_config / "ampathforms" / name).read_text())["name"]
                 for name in REVIEWED_FORMS]
        return self.query(db,
            "SELECT f.uuid,f.form_id,f.version,f.retired,MD5(c.value) FROM form f "
            "JOIN form_resource r ON r.form_id=f.form_id AND r.name='JSON schema' "
            "JOIN clob_datatype_storage c ON c.uuid=r.value_reference WHERE f.name IN ("
            + ",".join(map(sql_string, names)) + ") ORDER BY f.uuid")

    def check_clinical_form_updates(self, db, phase, previous=None):
        """Verify Initializer writes current schemas/criteria and preserves historical forms."""
        current = self.form_schema_snapshot(db)
        active_hashes = set()
        for filename in REVIEWED_FORMS:
            data = (self.candidate_config / "ampathforms" / filename).read_bytes()
            schema = json.loads(data)
            # Core's OpenmrsObjectSaveHandler applies Java String.trim() when
            # saving ClobDatatypeStorage. Preserve every byte inside the JSON.
            stored_hash = hashlib.md5(data.strip(bytes(range(33)))).hexdigest()
            expected = "\t".join([schema["version"], "1" if schema.get("published") else "0",
                                  "1" if schema.get("retired") else "0", stored_hash])
            if not schema.get("retired"):
                active_hashes.add(stored_hash)
            rows = self.query(db,
                "SELECT f.version,f.published,f.retired,MD5(c.value) FROM form f "
                "JOIN form_resource r ON r.form_id=f.form_id AND r.name='JSON schema' "
                "JOIN clob_datatype_storage c ON c.uuid=r.value_reference WHERE f.name="
                + sql_string(schema["name"]) + " AND f.version=" + sql_string(schema["version"]))
            require(rows == [expected], "clinical_form_schema_not_loaded")
        by_uuid = {row.split("\t")[0]: row.split("\t") for row in current}
        for row in previous or []:
            old = row.split("\t")
            loaded = by_uuid.get(old[0])
            require(loaded is not None and loaded[:3] == old[:3] and loaded[4] == old[4],
                    "historical_form_identity_or_schema_changed")
            require(loaded[3] == ("0" if loaded[4] in active_hashes else "1"),
                    "historical_form_retirement_invalid")
        with (self.candidate_config / "conceptreferencerange/conceptreferencerange_laboratory.csv").open() as stream:
            ranges = {row["Uuid"]: row for row in csv.DictReader(stream)}
        for identifier in REVIEWED_RANGES:
            row = ranges[identifier]
            require(self.query(db, "SELECT MD5(criteria) FROM concept_reference_range WHERE uuid="
                    + sql_string(identifier)) == [hashlib.md5(row["Criteria"].encode()).hexdigest()],
                    "clinical_reference_range_not_updated")
        emit("clinical_form_updates", "PASSED", phase=phase, forms=len(REVIEWED_FORMS),
             ranges=len(REVIEWED_RANGES), historical_schemas_checked=len(previous or []))
        return current

    def check_clinical_drug(self, backend, db, phase, previous=None):
        """Verify the catalog entry in storage and the prescribing search response."""
        drug = CLINICAL_DRUG
        names = ",".join(sql_string(drug[key]) for key in ("name_es", "name_en"))
        concepts = self.query(db,
            "SELECT c.concept_id,c.uuid,c.retired,cc.name,dt.name FROM concept c "
            "JOIN concept_class cc ON cc.concept_class_id=c.class_id "
            "JOIN concept_datatype dt ON dt.concept_datatype_id=c.datatype_id "
            "WHERE c.uuid=" + sql_string(drug["concept"]) + " OR EXISTS (SELECT 1 FROM concept_name n "
            "WHERE n.concept_id=c.concept_id AND n.voided=0 AND n.name IN (" + names + ")) "
            "ORDER BY c.concept_id")
        require(len(concepts) == 1, "clinical_drug_concept_missing_or_duplicated")
        concept = concepts[0].split("\t")
        require(len(concept) == 5 and re.fullmatch(r"[1-9][0-9]*", concept[0])
                and concept[1:] == [drug["concept"], "0", "Drug", "N/A"],
                "clinical_drug_concept_invalid")
        require(self.query(db, "SELECT locale,name FROM concept_name WHERE concept_id=" + concept[0]
                + " AND voided=0 AND concept_name_type='FULLY_SPECIFIED' ORDER BY locale,name")
                == ["en\t" + drug["name_en"], "es\t" + drug["name_es"]],
                "clinical_drug_concept_names_invalid")
        presentations = self.query(db,
            "SELECT d.drug_id,d.uuid,d.name,d.retired,d.strength,c.uuid,f.uuid,f.retired,"
            "EXISTS (SELECT 1 FROM concept_name n WHERE n.concept_id=f.concept_id "
            "AND n.voided=0 AND n.locale='es' AND n.name='Tableta') FROM drug d "
            "JOIN concept c ON c.concept_id=d.concept_id "
            "LEFT JOIN concept f ON f.concept_id=d.dosage_form WHERE d.uuid=" + sql_string(drug["uuid"])
            + " OR c.uuid=" + sql_string(drug["concept"]) + " OR d.name=" + sql_string(drug["name"])
            + " ORDER BY d.drug_id")
        require(len(presentations) == 1, "clinical_drug_presentation_missing_or_duplicated")
        presentation = presentations[0].split("\t")
        require(len(presentation) == 9 and re.fullmatch(r"[1-9][0-9]*", presentation[0])
                and presentation[1:] == [drug["uuid"], drug["name"], "0", drug["strength"],
                    drug["concept"], drug["dosage_form"], "0", "1"], "clinical_drug_presentation_invalid")
        code, body = self.request(backend, "GET",
            "/drug?q=URSODESOX&v=custom:(uuid,display,name,strength,dosageForm:(display,uuid),concept:(display,uuid))")
        require(code == 200 and isinstance(body, dict) and isinstance(body.get("results"), list)
                and all(isinstance(item, dict) for item in body["results"]), "clinical_drug_search_invalid")
        matches = [item for item in body["results"] if item.get("uuid") == drug["uuid"]]
        require(len(matches) == 1, "clinical_drug_search_missing_or_duplicated")
        match = matches[0]
        require(match.get("name") == drug["name"] and match.get("strength") == drug["strength"]
                and isinstance(match.get("display"), str) and bool(match["display"].strip())
                and all(isinstance(match.get(key), dict) and match[key].get("uuid") == drug[target]
                    and isinstance(match[key].get("display"), str) and bool(match[key]["display"].strip())
                    for key, target in (("concept", "concept"), ("dosageForm", "dosage_form"))),
                "clinical_drug_search_entry_invalid")
        snapshot = (tuple(concepts), tuple(presentations))
        require(previous is None or snapshot == previous, "clinical_drug_changed_on_restart")
        emit("clinical_drug", "PASSED", phase=phase, concepts=1, presentations=1,
             search_http=200, restart_checked=previous is not None)
        return snapshot

    def check_ocl_refresh(self, db, phase, previous=None):
        """Verify additive OCL concepts and the independently owned neighborhood set."""
        concepts = []
        for identifier, concept_class, name in (
                ("3fb84698-488a-447d-acbc-72e8665cffdc", "Misc", "1:512"),
                ("d14f251d-82a1-4ecf-aa45-f17f57a193db", "Finding", "Cuatro cruces")):
            rows = self.query(db, "SELECT c.concept_id,c.uuid,c.retired,cc.name,dt.name,n.name FROM concept c "
                "JOIN concept_class cc ON cc.concept_class_id=c.class_id "
                "JOIN concept_datatype dt ON dt.concept_datatype_id=c.datatype_id "
                "LEFT JOIN concept_name n ON n.concept_id=c.concept_id AND n.voided=0 "
                "AND n.locale='es' AND n.concept_name_type='FULLY_SPECIFIED' WHERE c.uuid=" + sql_string(identifier))
            require(len(rows) == 1, "ocl_refresh_concept_missing_or_duplicated")
            fields = rows[0].split("\t")
            require(len(fields) == 6 and re.fullmatch(r"[1-9][0-9]*", fields[0])
                    and fields[1:] == [identifier, "0", concept_class, "N/A", name], "ocl_refresh_concept_invalid")
            concepts.append(tuple(rows))
        neighborhood_uuid = "0fd3e744-6d2c-4cb3-9b7e-1f88899635d9"
        root = self.query(db, "SELECT concept_id,uuid,retired,is_set FROM concept WHERE uuid=" + sql_string(neighborhood_uuid))
        require(len(root) == 1, "ocl_refresh_neighborhood_set_missing_or_duplicated")
        fields = root[0].split("\t")
        require(len(fields) == 4 and re.fullmatch(r"[1-9][0-9]*", fields[0])
                and fields[1:] == [neighborhood_uuid, "0", "1"], "ocl_refresh_neighborhood_set_invalid")
        members = self.query(db, "SELECT s.concept_set_id,s.uuid,m.concept_id,m.uuid,m.retired "
            "FROM concept_set s JOIN concept m ON m.concept_id=s.concept_id "
            "WHERE s.concept_set=" + fields[0] + " ORDER BY m.uuid,s.concept_set_id")
        fields = [row.split("\t") for row in members]
        require(len(fields) == 10 and all(len(row) == 5 for row in fields)
                and len({row[3] for row in fields}) == 10
                and all(re.fullmatch(r"[1-9][0-9]*", row[0]) and UUID_PATTERN.fullmatch(row[1])
                    and re.fullmatch(r"[1-9][0-9]*", row[2]) and UUID_PATTERN.fullmatch(row[3])
                    and row[4] == "0" for row in fields), "ocl_refresh_neighborhood_members_invalid")
        snapshot = (tuple(concepts), tuple(root), tuple(members))
        require(previous is None or snapshot == previous, "ocl_refresh_changed_on_restart")
        emit("ocl_refresh", "PASSED", phase=phase, concepts=2, neighborhood_sets=1,
             neighborhood_members=10, restart_checked=previous is not None)
        return snapshot

    def procedure_anatomy_contract(self):
        """Read the shipped terminology, without a second catalog in the harness."""
        exports = []
        for pattern in ("17_*anatomia-procedimientos_concepts*.zip",
                        "67_*anatomia-procedimientos_mappings*.zip",
                        "10_SIHSALUS_sihsalus_concepts*.zip"):
            paths = list((self.candidate_config / "ocl").glob(pattern))
            require(len(paths) == 1, "procedure_anatomy_export_missing_or_duplicated")
            with zipfile.ZipFile(paths[0]) as archive:
                exports.append(json.loads(archive.read("export.json")))
        concepts = {concept["url"]: concept for export in exports for concept in export["concepts"]}
        root = next(concept for concept in exports[0]["concepts"] if concept["id"] == "PROCEDURE-BODY-SITES")
        mappings = exports[1]["mappings"]
        members = [mapping for mapping in mappings if mapping["map_type"] == "CONCEPT-SET"]
        terms = [mapping for mapping in mappings if mapping["map_type"] == "SAME-AS"]
        expected = {}
        for member in members:
            concept = concepts[member["to_concept_url"]]
            spanish = [name["name"] for name in concept["names"] if name.get("locale") == "es"
                       and name.get("locale_preferred") and not name.get("retired")]
            require(len(spanish) == 1, "procedure_anatomy_spanish_name_missing")
            expected[concept["external_id"]] = (concept["concept_class"], concept["datatype"], spanish[0])
        expected_terms = {(concepts[term["from_concept_url"]]["external_id"], term["to_concept_code"],
                           term["external_id"]) for term in terms}
        require(len(members) == len(expected) == len(expected_terms) == 133,
                "procedure_anatomy_contract_invalid")
        system_url = "http://terminology.hl7.org/CodeSystem/v2-0550"
        with (self.candidate_config / "fhirconceptsources/fhirconceptsources.csv").open(newline="", encoding="utf-8") as stream:
            associations = [row for row in csv.DictReader(stream) if row["Url"] == system_url]
        require(len(associations) == 1, "procedure_anatomy_fhir_contract_invalid")
        association = associations[0]
        return root["external_id"], expected, expected_terms, (association["Uuid"], association["Concept source"], system_url)

    def check_procedure_anatomy(self, backend, db, phase, previous=None):
        """Check actual set membership, Spanish names, HL7 mappings and native searches."""
        root_uuid, expected, expected_terms, (fhir_uuid, source_uuid, system_url) = self.procedure_anatomy_contract()
        root = self.query(db, "SELECT concept_id,uuid,retired,is_set FROM concept WHERE uuid=" + sql_string(root_uuid))
        require(len(root) == 1, "procedure_anatomy_set_missing_or_duplicated")
        fields = root[0].split("\t")
        require(len(fields) == 4 and re.fullmatch(r"[1-9][0-9]*", fields[0])
                and fields[1:] == [root_uuid, "0", "1"], "procedure_anatomy_set_invalid")
        set_id = fields[0]
        rows = self.query(db, "SELECT s.concept_set_id,s.uuid,c.concept_id,c.uuid,c.retired,cc.name,dt.name,n.name "
            "FROM concept_set s JOIN concept c ON c.concept_id=s.concept_id "
            "JOIN concept_class cc ON cc.concept_class_id=c.class_id "
            "JOIN concept_datatype dt ON dt.concept_datatype_id=c.datatype_id "
            "LEFT JOIN concept_name n ON n.concept_id=c.concept_id AND n.voided=0 "
            "AND n.locale='es' AND n.locale_preferred=1 WHERE s.concept_set=" + set_id + " ORDER BY c.uuid")
        members = [row.split("\t") for row in rows]
        require(len(members) == 133 and all(len(row) == 8 for row in members)
                and {row[3] for row in members} == set(expected), "procedure_anatomy_members_invalid")
        for row in members:
            require(re.fullmatch(r"[1-9][0-9]*", row[0]) and UUID_PATTERN.fullmatch(row[1])
                    and re.fullmatch(r"[1-9][0-9]*", row[2]) and row[4] == "0"
                    and tuple(row[5:]) == expected[row[3]], "procedure_anatomy_member_metadata_invalid")
        mapping_rows = self.query(db, "SELECT c.uuid,t.code,m.uuid,m.concept_map_id,t.concept_reference_term_id "
            "FROM concept_reference_map m JOIN concept c ON c.concept_id=m.concept_id "
            "JOIN concept_reference_term t ON t.concept_reference_term_id=m.concept_reference_term_id "
            "JOIN concept_reference_source src ON src.concept_source_id=t.concept_source_id "
            "JOIN concept_map_type mt ON mt.concept_map_type_id=m.concept_map_type_id "
            "JOIN concept_set s ON s.concept_id=c.concept_id WHERE s.concept_set=" + set_id
            + " AND src.name='v2-0550' AND mt.name IN ('SAME-AS','SAME_AS') AND t.retired=0 ORDER BY c.uuid,t.code,m.uuid")
        mapped = [row.split("\t") for row in mapping_rows]
        require(len(mapped) == 133 and all(len(row) == 5 for row in mapped)
                and {tuple(row[:3]) for row in mapped} == expected_terms,
                "procedure_anatomy_hl7_mappings_invalid")
        fhir_rows = self.query(db, "SELECT f.fhir_concept_source_id,f.uuid,f.retired,src.concept_source_id,"
            "src.uuid,src.name,src.retired,f.url FROM fhir_concept_source f "
            "LEFT JOIN concept_reference_source src ON src.concept_source_id=f.concept_source_id WHERE f.uuid="
            + sql_string(fhir_uuid) + " OR src.uuid=" + sql_string(source_uuid) + " OR f.url=" + sql_string(system_url))
        require(len(fhir_rows) == 1, "procedure_anatomy_fhir_source_invalid")
        fhir_fields = fhir_rows[0].split("\t")
        require(len(fhir_fields) == 8 and re.fullmatch(r"[1-9][0-9]*", fhir_fields[0])
                and fhir_fields[1:3] == [fhir_uuid, "0"] and re.fullmatch(r"[1-9][0-9]*", fhir_fields[3])
                and fhir_fields[4:] == [source_uuid, "v2-0550", "0", system_url],
                "procedure_anatomy_fhir_source_invalid")
        by_code = {code: identifier for identifier, code, _ in expected_terms}
        for text, matches in (("abdomen", {by_code["ADB"]}), ("deltoides", {by_code["DELT"]}),
                              ("esófago", {by_code["ESO"]}), ("ceftriaxona", set())):
            query = urlencode({"q": text, "memberOf": root_uuid, "v": "custom:(uuid,display)", "limit": 50})
            status, response = self.request(backend, "GET", "/concept?" + query)
            require(status == 200 and isinstance(response, dict) and isinstance(response.get("results"), list),
                    "procedure_anatomy_search_failed")
            results = response["results"]
            require(len(results) == len(matches) and {result.get("uuid") for result in results} == matches,
                    "procedure_anatomy_search_membership_invalid")
        snapshot = (tuple(root), tuple(rows), tuple(mapping_rows), tuple(fhir_rows))
        require(previous is None or snapshot == previous, "procedure_anatomy_changed_on_restart")
        emit("procedure_anatomy", "PASSED", phase=phase, members=133, hl7_mappings=133,
             fhir_source_associations=1, native_searches=4, restart_checked=previous is not None)
        return snapshot

    def create_fixtures(self, backend):
        for index in range(2):
            code, person = self.request(backend, "POST", "/person", {
                "names": [{"givenName": "Synthetic", "familyName": "Admission CI " + self.nonce[:8]}], "gender": "M"})
            require(code == 201 and isinstance(person, dict) and UUID_PATTERN.fullmatch(person.get("uuid", "")), "synthetic_person_creation_failed")
            username = "admission-ci-" + self.nonce[:12] + "-" + str(index)
            code, user = self.request(backend, "POST", "/user", {
                "username": username, "password": self.user_password, "person": person["uuid"],
                "roles": [CANONICAL_UUID], "userProperties": {}})
            require(code == 201 and isinstance(user, dict) and UUID_PATTERN.fullmatch(user.get("uuid", "")), "synthetic_user_creation_failed")
            self.fixtures.append({"uuid": user["uuid"], "username": username, "person": person["uuid"]})
        code, session = self.request(backend, "GET", "/session?v=full", restricted=True)
        require(code == 200 and isinstance(session, dict) and session.get("authenticated") is True, "synthetic_user_not_authenticated")
        require(str(session.get("user", {}).get("userProperties", {}).get("forcePassword", "false")).lower() != "true", "synthetic_user_requires_password_change")

    def baseline(self):
        emit("baseline", "RUNNING")
        db = self.start_database("baseline")
        backend, volume = self.start_backend("baseline", self.baseline_config)
        self.wait_initializer(backend, "baseline")
        self.assert_checksums(backend)
        require(not self.candidate_recorded(db), "candidate_present_in_baseline")
        history = self.history(db)
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.remove_container(backend)
        # The historical CSV overwrote EMRAPI's roles on installation. Restart
        # that same baseline before seeding the migration, retaining all checksums.
        backend, _ = self.start_backend("baseline-restart", self.baseline_config, data_volume=volume)
        self.wait_initializer(backend, "baseline_restart")
        self.assert_checksums(backend)
        require(self.history(db) == history, "baseline_restart_changed_history")
        self.check_emrapi_roles(db)
        self.create_fixtures(backend)
        self.check_admission(db)
        self.baseline_history = self.history(db)
        require(any("normalize-admission-role-name-20260722" in row for row in self.baseline_history), "real_baseline_history_missing")
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.copy_tree(backend, "/openmrs/data", self.baseline_data, "data")
        dump = self.docker("exec", db, "mariadb-dump", "--defaults-extra-file=/run/admission-mysql.cnf",
            "--single-transaction", "--routines", "--triggers", "--skip-dump-date", DATABASE,
            timeout=self.remaining(180)).stdout
        require(dump, "empty_baseline_dump")
        self.baseline_dump.write_bytes(dump)
        self.baseline_dump.chmod(0o600)
        self.remove_container(backend)
        self.remove_container(db)
        emit("baseline_snapshot", "PASSED", synthetic_users=len(self.fixtures),
             real_history_rows=len(self.baseline_history), roles_checksum=self.role_md5)

    def fresh(self):
        emit("fresh_candidate", "RUNNING")
        db = self.start_database("fresh")
        backend, _ = self.start_backend("fresh", self.candidate_config)
        self.wait_initializer(backend, "fresh_candidate")
        self.assert_checksums(backend, self.candidate_role_md5)
        require(self.candidate_recorded(db), "fresh_candidate_history_missing")
        require(self.candidate_recorded(db, OPERATIONAL_CHANGESET), "fresh_operational_history_missing")
        self.check_arrival_payment(db)
        self.check_emrapi_roles(db)
        self.check_clinical_drug(backend, db, "fresh")
        self.check_ocl_refresh(db, "fresh")
        self.check_procedure_anatomy(backend, db, "fresh")
        self.check_clinical_form_updates(db, "fresh")
        self.create_fixtures(backend)
        self.check_admission(db, self.candidate_privileges)
        self.rbac(backend, db)
        emit("fresh_candidate", "PASSED", privileges=len(self.candidate_privileges),
             emrapi_role_identities_verified=True, roles_checksum=self.candidate_role_md5)

    def seed(self, db, bad=False):
        self.check_admission(db)
        if bad:
            require(self.query(db, "SELECT COUNT(*) FROM privilege WHERE privilege='Manage Roles'") == ["1"], "rejection_fixture_privilege_missing")
        self.query(db,
            "START TRANSACTION;\nUPDATE role SET uuid=" + sql_string(str(uuid.uuid4())) + " WHERE role='Admision';\n"
            "INSERT INTO role(role,description,uuid) VALUES ('SIHSALUS Admision','Synthetic admission fixture'," + sql_string(CANONICAL_UUID) + ");\n"
            "INSERT INTO role_privilege(role,privilege) SELECT 'SIHSALUS Admision',privilege FROM role_privilege WHERE role='Admision';\n"
            + ("INSERT INTO role_privilege(role,privilege) VALUES ('SIHSALUS Admision','Manage Roles');\n" if bad else
               "DELETE FROM role_privilege WHERE role IN ('Admision','SIHSALUS Admision') AND privilege='Delete Relationships';\n")
            + "INSERT INTO user_role(user_id,role) SELECT user_id,'SIHSALUS Admision' FROM users WHERE uuid IN ("
            + ",".join(sql_string(item["uuid"]) for item in self.fixtures) + ");\n"
            "DELETE FROM user_role WHERE role='Admision' AND user_id=(SELECT user_id FROM users WHERE uuid="
            + sql_string(self.fixtures[0]["uuid"]) + ");\nCOMMIT;")
        if not bad:
            # Existing-name/different-UUID compatibility observed in QLTY.
            # This fixture exists only in the owned disposable CI database.
            self.query(db, "INSERT INTO role(role,description,uuid) VALUES "
                       "('SIHSALUS Soporte','Synthetic pre-existing support'," + sql_string(str(uuid.uuid4())) + ");"
                       "INSERT INTO role_privilege(role,privilege) VALUES ('SIHSALUS Soporte','Get Patients');")

    def seed_operational_alias(self, db):
        """Reviewed metadata shape only; accounts and identities are synthetic."""
        self.check_admission(db)
        source = ROOT / ".github/integration/admission-role-reconciliation/src/test/resources/admission-operational-legacy-privileges.txt"
        privileges = source.read_text().splitlines()
        require(len(privileges) == 55 and len(set(privileges)) == 55, "invalid_operational_fixture")
        required = ",".join(sql_string(privilege) for privilege in privileges)
        require(set(self.query(db, "SELECT privilege FROM privilege WHERE privilege IN (" + required + ")")) == set(privileges), "operational_fixture_privilege_missing")
        self.query(db,
            "START TRANSACTION;\n"
            "INSERT INTO role(role,description,uuid) VALUES ('SIHSALUS Admision','Synthetic operational alias',"
            + sql_string(str(uuid.uuid4())) + ");\n"
            "INSERT INTO role_privilege(role,privilege) SELECT 'SIHSALUS Admision',privilege FROM privilege WHERE privilege IN ("
            + required + ");\n"
            "INSERT INTO user_role(user_id,role) SELECT user_id,'SIHSALUS Admision' FROM users WHERE uuid IN ("
            + ",".join(sql_string(item["uuid"]) for item in self.fixtures) + ");\n"
            "DELETE FROM user_role WHERE role='Admision' AND user_id=(SELECT user_id FROM users WHERE uuid="
            + sql_string(self.fixtures[0]["uuid"]) + ");\nCOMMIT;")
        require(set(self.query(db, "SELECT privilege FROM role_privilege WHERE role='SIHSALUS Admision'")) == set(privileges), "operational_fixture_policy_mismatch")

    def seed_admission_supplement(self, db):
        source = ROOT / ".github/integration/admission-role-reconciliation/src/test/resources/admission-supplement-privileges.txt"
        privileges = source.read_text().splitlines()
        require(len(privileges) == 15 and len(set(privileges)) == 15, "invalid_supplement_fixture")
        required = ",".join(sql_string(privilege) for privilege in privileges)
        require(set(self.query(db, "SELECT privilege FROM privilege WHERE privilege IN (" + required + ")")) == set(privileges),
                "supplement_fixture_privilege_missing")
        self.query(db,
            "START TRANSACTION;\n"
            "INSERT INTO role(role,description,uuid) VALUES (" + sql_string(ADMISSION_SUPPLEMENT)
            + ",'Synthetic reviewed supplement','5aaa1628-a7be-5a4f-847c-a1c593bd364e');\n"
            "INSERT INTO role_privilege(role,privilege) SELECT " + sql_string(ADMISSION_SUPPLEMENT)
            + ",privilege FROM privilege WHERE privilege IN (" + required + ");\n"
            "INSERT INTO user_role(user_id,role) SELECT user_id," + sql_string(ADMISSION_SUPPLEMENT)
            + " FROM users WHERE uuid IN (" + ",".join(sql_string(item["uuid"]) for item in self.fixtures) + ");\nCOMMIT;")

    def rbac(self, backend, db):
        code, readable = self.request(backend, "GET", "/relationshiptype?limit=1", restricted=True)
        require(code == 200 and isinstance(readable, dict) and isinstance(readable.get("results"), list), "admission_read_denied")
        suffix = secrets.token_hex(8)
        code, reltype = self.request(backend, "POST", "/relationshiptype", {
            "aIsToB": "Synthetic CI guardian " + suffix,
            "bIsToA": "Synthetic CI dependent " + suffix, "description": "Owned disposable Initializer test"})
        require(code == 201 and isinstance(reltype, dict) and UUID_PATTERN.fullmatch(reltype.get("uuid", "")), "synthetic_relationship_type_creation_failed")
        code, relationship = self.request(backend, "POST", "/relationship", {
            "personA": self.fixtures[0]["person"], "personB": self.fixtures[1]["person"], "relationshipType": reltype["uuid"]})
        require(code == 201 and isinstance(relationship, dict) and UUID_PATTERN.fullmatch(relationship.get("uuid", "")), "synthetic_relationship_creation_failed")
        identifier = relationship["uuid"]
        before = self.query(db, "SELECT * FROM relationship WHERE uuid=" + sql_string(identifier))
        require(len(before) == 1, "fresh_synthetic_relationship_missing")
        require(self.query(db, "SELECT voided FROM relationship WHERE uuid=" + sql_string(identifier)) == ["0"], "synthetic_relationship_not_active")
        code, _ = self.request(backend, "DELETE", "/relationship/" + identifier + "?purge=true", restricted=True)
        require(code == 403, "admission_purge_not_denied")
        require(self.query(db, "SELECT * FROM relationship WHERE uuid=" + sql_string(identifier)) == before, "denied_purge_changed_relationship")
        code, _ = self.request(backend, "DELETE", "/relationship/" + identifier + "?reason=synthetic-ci", restricted=True)
        require(code == 204, "admission_void_not_allowed")
        require(self.query(db, "SELECT voided FROM relationship WHERE uuid=" + sql_string(identifier)) == ["1"], "allowed_void_not_persisted")
        emit("rbac", "PASSED", authorized_read=200, denied_purge=403, authorized_void=204)

    def upgrade(self, operational=False):
        emit("operational_upgrade" if operational else "upgrade", "RUNNING")
        db = self.start_database("upgrade")
        self.import_baseline(db)
        forms_before = self.form_schema_snapshot(db)
        if operational:
            self.seed_operational_alias(db)
            self.seed_admission_supplement(db)
        else:
            self.seed(db)
        expected = self.expected_upgrade_state(db, self.state(db))
        backend, volume = self.start_backend("upgrade", self.historical_config, restore=True)
        self.wait_initializer(backend, "upgrade")
        self.assert_checksums(backend)
        require(self.candidate_recorded(db), "candidate_history_missing")
        require(self.candidate_recorded(db, OPERATIONAL_CHANGESET), "operational_history_missing")
        require(self.candidate_recorded(db, SUPPLEMENT_CHANGESET), "supplement_retirement_history_missing")
        require(self.query(db, "SELECT COUNT(*) FROM role WHERE role=" + sql_string(ADMISSION_SUPPLEMENT)) == ["0"],
                "admission_supplement_recreated")
        self.check_arrival_payment(db)
        self.check_admission(db)
        self.assert_state(db, expected, "upgrade_changed_unapproved_rbac_or_references")
        clinical_drug = self.check_clinical_drug(backend, db, "upgrade")
        ocl_refresh = self.check_ocl_refresh(db, "upgrade")
        procedure_anatomy = self.check_procedure_anatomy(backend, db, "upgrade")
        clinical_forms = self.check_clinical_form_updates(db, "upgrade", previous=forms_before)
        state, history = self.state(db), self.history(db)
        self.rbac(backend, db)
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.remove_container(backend)
        backend, _ = self.start_backend("idempotence", self.historical_config, data_volume=volume)
        self.wait_initializer(backend, "idempotence")
        self.assert_checksums(backend)
        state = self.expected_emrapi_refresh(state)
        self.assert_state(db, state, "second_start_changed_unapproved_rbac")
        require(self.history(db) == history, "second_start_changed_history")
        self.check_clinical_drug(backend, db, "idempotence", previous=clinical_drug)
        self.check_ocl_refresh(db, "idempotence", previous=ocl_refresh)
        self.check_procedure_anatomy(backend, db, "idempotence", previous=procedure_anatomy)
        require(self.check_clinical_form_updates(db, "idempotence", previous=clinical_forms) == clinical_forms,
                "second_start_changed_clinical_forms")
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.remove_container(backend)
        backend, _ = self.start_backend("current-policy", self.candidate_config, data_volume=volume)
        self.wait_initializer(backend, "current_policy")
        self.assert_checksums(backend, self.candidate_role_md5)
        self.check_admission(db, self.candidate_privileges)
        state["role_privilege"].extend(CANONICAL_ROLE + "\t" + privilege for privilege in CURRENT_ADMISSION_ADDITIONS)
        state = self.expected_hospital_role_state(db, state, self.canonical_laboratory)
        self.assert_state(db, state, "current_csv_changed_unapproved_rbac")
        require(self.history(db) == history, "current_csv_changed_migration_history")
        self.rbac(backend, db)
        emit("current_policy", "PASSED", privileges=len(self.candidate_privileges), roles_checksum=self.candidate_role_md5)
        self.remove_container(backend)
        self.remove_container(db)

    def rejection(self):
        emit("reject", "RUNNING")
        configuration = self.directory / "configuration-rejection"
        shutil.copytree(self.historical_config, configuration)
        canary_uuid, canary_role = str(uuid.uuid4()), "Synthetic Initializer canary " + self.nonce[:8]
        with (configuration / ROLES_FILE).open(encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle))
        canary = configuration / "roles/zz-admission-initializer-canary.csv"
        with canary.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerow({"Uuid": canary_uuid, "Role name": canary_role,
                "Description": "Owned disposable failure-order test", "Inherited roles": "", "Privileges": ""})
        canary.chmod(0o644)
        canary_md5 = hashlib.md5(canary.read_bytes()).hexdigest()
        require((configuration / ROLES_FILE).read_bytes() == (self.historical_config / ROLES_FILE).read_bytes(), "canary_changed_roles_csv")
        db = self.start_database("rejection")
        self.import_baseline(db)
        self.seed(db, bad=True)
        before, history = self.state(db), self.history(db)
        backend, volume = self.start_backend("rejection", configuration, restore=True)
        self.wait_initializer(backend, "reject", reject=True)
        self.assert_checksums(backend)
        self.assert_state(db, before, "rejected_migration_changed_rbac")
        self.assert_rejected_history(db, history)
        require(not self.candidate_recorded(db), "rejected_migration_was_recorded")
        require(self.query(db, "SELECT COUNT(*) FROM role WHERE uuid=" + sql_string(canary_uuid)) == ["0"], "later_roles_loader_ran_after_rejection")
        canary_checksum = "configuration_checksums/roles/zz-admission-initializer-canary.checksum"
        self.absent_checksum(backend, canary_checksum)
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.remove_container(backend)
        # Correct only the owned extra fixture. No checksum/history/XML resets.
        self.query(db, "DELETE FROM role_privilege WHERE role='SIHSALUS Admision' AND privilege='Manage Roles'")
        backend, _ = self.start_backend("retry", configuration, data_volume=volume)
        self.wait_initializer(backend, "retry")
        self.assert_checksums(backend)
        self.check_admission(db)
        require(self.candidate_recorded(db), "retry_history_missing")
        require(self.query(db, "SELECT role FROM role WHERE uuid=" + sql_string(canary_uuid)) == [canary_role], "retry_did_not_load_later_roles_canary")
        require(self.checksum(backend, canary_checksum) == canary_md5, "retry_canary_checksum_missing")
        self.remove_container(backend)
        self.remove_container(db)
        emit("reject_retry", "PASSED", later_roles_loader_blocked=True, retry_without_checksum_clear=True)

    def cleanup(self):
        self.cleanup_deadline = time.monotonic() + 180
        failures = 0
        for container in list(reversed(self.containers)):
            try:
                self.remove_container(container)
            except HarnessFailure:
                failures += 1
        for volume in list(reversed(self.volumes)):
            try:
                self.owned("volume", volume)
                self.docker("volume", "rm", volume, timeout=45)
                self.volumes.remove(volume)
            except HarnessFailure:
                failures += 1
        if self.network:
            try:
                self.owned("network", self.network)
                self.docker("network", "rm", self.network, timeout=45)
                self.network = None
            except HarnessFailure:
                failures += 1
        if not failures:
            require(self.directory.name.startswith("admission-initializer-") and self.directory.is_dir()
                    and not self.directory.is_symlink(), "cleanup_directory_not_owned")
            try:
                shutil.rmtree(self.directory)
            except OSError:
                failures += 1
        emit("cleanup", "FAILED" if failures else "PASSED", unresolved_owned_resources=failures)
        return failures == 0


def main(scenario="upgrade"):
    harness, success, cleanup_ok = None, False, True
    def interrupted(signum, frame):
        raise HarnessFailure("interrupted")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        require(scenario in ("upgrade", "fresh", "operational"), "invalid_initializer_scenario")
        harness = Harness(os.environ)
        harness.prepare()
        if scenario == "fresh":
            harness.fresh()
        else:
            harness.baseline()
            harness.upgrade(operational=True) if scenario == "operational" else harness.upgrade()
            if scenario == "upgrade":
                harness.rejection()
        success = True
    except HarnessFailure as error:
        emit("harness", "FAILED", reason=str(error))
    except Exception:
        emit("harness", "FAILED", reason="unexpected_harness_error")
    finally:
        if harness is not None:
            try:
                cleanup_ok = harness.cleanup()
            except Exception:
                emit("cleanup", "FAILED", reason="owned_cleanup_incomplete")
                cleanup_ok = False
    emit("harness", "PASSED" if success and cleanup_ok else "FAILED",
         scope="ephemeral synthetic Initializer and native relationship RBAC",
         deployed_environment_validation=False)
    return 0 if success and cleanup_ok else 1


if __name__ == "__main__":
    sys.exit(main(os.environ.get("ADMISSION_INITIALIZER_SCENARIO", "upgrade")))
