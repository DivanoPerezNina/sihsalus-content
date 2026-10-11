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

echo "Validated Maven Central complete-artifact checks and retry behavior."

if [[ "${1:-}" == "--bundle" ]]; then
  # Use native remote file staging and the publisher's dry run, with a throwaway
  # signing key. No publishing credentials, user keyring, or upload is required.
  export GNUPGHOME="${tmp_dir}/gnupg"
  mkdir -m 700 "$GNUPGHOME"
  trap 'gpgconf --homedir "$GNUPGHOME" --kill gpg-agent >/dev/null 2>&1 || true; rm -rf "$tmp_dir"' EXIT
  gpg --batch --pinentry-mode loopback --passphrase '' \
    --quick-generate-key 'SIHSALUS publication regression <publication-test@example.invalid>' \
    rsa2048 sign 1d >"${tmp_dir}/key.log" 2>&1
  printf '%s\n' '<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"/>' >"${tmp_dir}/settings.xml"
  printf '%s\n' 'environment: {}' >"${tmp_dir}/jreleaser-settings.yml"
  export JRELEASER_MAVENCENTRAL_CENTRAL_USERNAME=synthetic-local-only
  JRELEASER_MAVENCENTRAL_CENTRAL_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
  export JRELEASER_MAVENCENTRAL_CENTRAL_PASSWORD

  bundle_log="${tmp_dir}/bundle.log"
  if ! "$repository_root/mvnw" --batch-mode --no-transfer-progress \
    --settings "$tmp_dir/settings.xml" --file "$repository_root/pom.xml" \
    -P release -Djreleaser.dry.run=true \
    -Djreleaser.settings.file="$tmp_dir/jreleaser-settings.yml" \
    clean deploy >"$bundle_log" 2>&1; then
    cat "$bundle_log" >&2
    exit 1
  fi

  python3 - "$repository_root" "$tmp_dir" <<'PYBUNDLE'
import hashlib
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

root, temporary = map(Path, sys.argv[1:])
pom = (root / "pom.xml").read_bytes()
schema = ET.fromstring(pom)
namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
group = schema.findtext("m:groupId", namespaces=namespace).replace(".", "/")
artifact = schema.findtext("m:artifactId", namespaces=namespace)
version = schema.findtext("m:version", namespaces=namespace)
prefix = f"{group}/{artifact}/{version}/{artifact}-{version}"
expected = {prefix + extension for extension in (".pom", ".zip", ".pom.asc", ".zip.asc")}
for name in (prefix + ".pom", prefix + ".zip"):
    expected.update(name + "." + algorithm for algorithm in ("md5", "sha1", "sha256", "sha512"))

bundles = list((root / "target/jreleaser/deploy/mavenCentral/central").glob("*-bundle.zip"))
if len(bundles) != 1:
    raise SystemExit("Expected exactly one native JReleaser publication bundle")
with zipfile.ZipFile(bundles[0]) as bundle:
    if len(bundle.namelist()) != len(expected) or set(bundle.namelist()) != expected:
        raise SystemExit("Central bundle contains missing artifacts or repository metadata")
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
        payload = temporary / ("artifact" + extension)
        signature = temporary / ("artifact" + extension + ".asc")
        payload.write_bytes(bundle.read(name))
        signature.write_bytes(bundle.read(name + ".asc"))
        subprocess.run(["gpg", "--batch", "--no-auto-key-retrieve", "--verify", str(signature), str(payload)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Validated native Central bundle: exact POM, packaged ZIP, four checksums, valid signatures, no repository metadata.")

# A native validation error must still stop publishing when repository warnings
# are permitted. Mutate only the generated staging POM, never the source POM.
staged_pom = root / "target/staging-deploy" / (prefix + ".pom")
(temporary / "valid-staged.pom").write_bytes(staged_pom.read_bytes())
(temporary / "staged-pom-path").write_text(str(staged_pom))
schema.remove(schema.find("m:name", namespace))
ET.register_namespace("", namespace["m"])
staged_pom.write_bytes(ET.tostring(schema, encoding="utf-8", xml_declaration=True))
PYBUNDLE

  invalid_pom_log="${tmp_dir}/invalid-pom.log"
  invalid_pom_status=0
  "$repository_root/mvnw" --batch-mode --no-transfer-progress \
    --settings "$tmp_dir/settings.xml" --file "$repository_root/pom.xml" \
    -P release -Djreleaser.dry.run=true \
    -Djreleaser.settings.file="$tmp_dir/jreleaser-settings.yml" \
    jreleaser:deploy >"$invalid_pom_log" 2>&1 || invalid_pom_status=$?
  cp "$tmp_dir/valid-staged.pom" "$(cat "$tmp_dir/staged-pom-path")"
  if (( invalid_pom_status == 0 )); then
    echo "Publisher accepted a staged POM without the mandatory name" >&2
    exit 1
  fi
  grep -Fq 'PomChecker detected errors' "$invalid_pom_log"
  grep -Fq '<name>' "$invalid_pom_log"
  echo "Validated native rejection of an invalid staged POM."
fi
