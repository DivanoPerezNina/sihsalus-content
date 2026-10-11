#!/usr/bin/env bash
set -euo pipefail

if (( $# > 1 )) || [[ "${1:-}" != "" && "${1:-}" != "--bundle" ]]; then
  echo "usage: test_maven_central_publication.sh [--bundle]" >&2
  exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd "${script_dir}/../.." && pwd)"
publication_gate="${script_dir}/wait_for_maven_central.sh"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

python3 - "$repository_root/pom.xml" <<'PY'
import sys
import xml.etree.ElementTree as ET

pom_path = sys.argv[1]
namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
root = ET.parse(pom_path).getroot()

release_profiles = [
    profile
    for profile in root.findall("m:profiles/m:profile", namespace)
    if profile.findtext("m:id", namespaces=namespace) == "release"
]
if len(release_profiles) != 1:
    raise SystemExit(f"Expected exactly one release profile, found {len(release_profiles)}")

plugins = release_profiles[0].findall("m:build/m:plugins/m:plugin", namespace)
central_plugins = [
    plugin
    for plugin in plugins
    if plugin.findtext("m:groupId", namespaces=namespace) == "org.sonatype.central"
    and plugin.findtext("m:artifactId", namespaces=namespace)
    == "central-publishing-maven-plugin"
]
if len(central_plugins) != 1:
    raise SystemExit(
        "Expected exactly one central-publishing-maven-plugin in the release profile, "
        f"found {len(central_plugins)}"
    )

configuration = central_plugins[0].find("m:configuration", namespace)
if configuration is None:
    raise SystemExit("Central publishing plugin has no configuration")

auto_publish = configuration.findtext("m:autoPublish", namespaces=namespace)
wait_until = configuration.findtext("m:waitUntil", namespaces=namespace)
if auto_publish != "true":
    raise SystemExit(f"Expected autoPublish=true, found {auto_publish!r}")
if wait_until != "validated":
    raise SystemExit(f"Expected waitUntil=validated, found {wait_until!r}")
PY

fake_curl="${tmp_dir}/curl"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'url="${!#}"' \
  'case "${FAKE_CURL_MODE:?}:${url}" in' \
  '  pom-only:*.pom) exit 0 ;;' \
  '  pom-only:*.zip) exit 22 ;;' \
  '  retry-once:*.pom) exit 0 ;;' \
  '  retry-once:*.zip)' \
  '    if [[ -f "${FAKE_CURL_STATE:?}" ]]; then exit 0; fi' \
  '    touch "$FAKE_CURL_STATE"' \
  '    exit 22' \
  '    ;;' \
  '  *) exit 22 ;;' \
  'esac' > "$fake_curl"
chmod +x "$fake_curl"

pom_only_log="${tmp_dir}/pom-only.log"
if CURL_BIN="$fake_curl" FAKE_CURL_MODE=pom-only \
  bash "$publication_gate" 9.9.9 1 0 >"$pom_only_log" 2>&1; then
  echo "Publication gate accepted a missing ZIP artifact" >&2
  exit 1
fi
grep -Fq "sihsalus-content-9.9.9.zip" "$pom_only_log"

retry_log="${tmp_dir}/retry.log"
CURL_BIN="$fake_curl" \
  FAKE_CURL_MODE=retry-once \
  FAKE_CURL_STATE="${tmp_dir}/zip-is-visible" \
  bash "$publication_gate" 9.9.9 2 0 >"$retry_log" 2>&1
grep -Fq "attempt 1/2" "$retry_log"
grep -Fq "sihsalus-content-9.9.9.pom and sihsalus-content-9.9.9.zip" "$retry_log"

if bash "$publication_gate" '../invalid' 1 0 >/dev/null 2>&1; then
  echo "Publication gate accepted an unsafe Maven version" >&2
  exit 1
fi

echo "Validated Maven Central release configuration, complete-artifact checks, and retry behavior."

if [[ "${1:-}" == "--bundle" ]]; then
  # Exercise the actual release extension without a publishing service or token.
  # skipPublishing in Central 0.10.0 also skips staging, so it cannot test a bundle.
  python3 - "$tmp_dir/settings.xml" <<'PY'
import pathlib
import secrets
import socket
import sys
import xml.etree.ElementTree as ET

try:
    with socket.create_connection(("127.0.0.1", 1), timeout=1):
        raise SystemExit("Bundle test requires the loopback destination to be closed")
except ConnectionRefusedError:
    pass

settings = ET.Element("settings", xmlns="http://maven.apache.org/SETTINGS/1.0.0")
server = ET.SubElement(ET.SubElement(settings, "servers"), "server")
ET.SubElement(server, "id").text = "central"
ET.SubElement(server, "username").text = "synthetic-local-only"
ET.SubElement(server, "password").text = secrets.token_hex(24)
path = pathlib.Path(sys.argv[1])
ET.ElementTree(settings).write(path, encoding="utf-8", xml_declaration=True)
path.chmod(0o600)
PY

  bundle_log="${tmp_dir}/bundle.log"
  if "$repository_root/mvnw" --batch-mode --settings "$tmp_dir/settings.xml" \
    --file "$repository_root/pom.xml" -P release -Dgpg.skip=true \
    -DcentralBaseUrl=http://127.0.0.1:1 clean deploy >"$bundle_log" 2>&1; then
    echo "Bundle test unexpectedly reached a publishing service" >&2
    exit 1
  fi
  grep -Fq "Using Central baseUrl: http://127.0.0.1:1" "$bundle_log"
  grep -Fq "Connection refused" "$bundle_log"
  if grep -Fq "Uploaded bundle successfully" "$bundle_log"; then
    echo "Bundle test unexpectedly uploaded an artifact" >&2
    exit 1
  fi

  python3 - "$repository_root" <<'PY'
import hashlib
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

root = Path(sys.argv[1])
pom = (root / "pom.xml").read_bytes()
schema = ET.fromstring(pom)
namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
group = schema.findtext("m:groupId", namespaces=namespace).replace(".", "/")
artifact = schema.findtext("m:artifactId", namespaces=namespace)
version = schema.findtext("m:version", namespaces=namespace)
prefix = f"{group}/{artifact}/{version}/{artifact}-{version}"
expected = {prefix + extension for extension in (".pom", ".zip")}
for name in tuple(expected):
    expected.update(name + "." + algorithm for algorithm in ("md5", "sha1", "sha256", "sha512"))

with zipfile.ZipFile(root / "target/central-publishing/central-bundle.zip") as bundle:
    if len(bundle.namelist()) != len(expected) or set(bundle.namelist()) != expected:
        raise SystemExit("Central bundle contains missing artifacts or local repository metadata")
    if bundle.read(prefix + ".pom") != pom:
        raise SystemExit("Central bundle POM differs from the source POM")
    if bundle.read(prefix + ".zip") != (root / f"target/{artifact}-{version}.zip").read_bytes():
        raise SystemExit("Central bundle content differs from the packaged ZIP")
    for extension in (".pom", ".zip"):
        name = prefix + extension
        for algorithm in ("md5", "sha1", "sha256", "sha512"):
            if bundle.read(name + "." + algorithm).decode().strip() != hashlib.new(
                algorithm, bundle.read(name)
            ).hexdigest():
                raise SystemExit("Central bundle checksum does not match its artifact")
print("Validated actual Central bundle: exact POM, packaged ZIP, checksums, and no repository metadata.")
PY
fi
