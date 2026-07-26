from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath


FORBIDDEN_PARTS = {
    ".gh-config",
    ".tools",
    ".venv",
    "backups",
    "build",
    "credentials",
    "data",
    "dist",
    "imports",
    "native_exports",
    "node_modules",
    "secrets",
}
FORBIDDEN_NAMES = {
    ".env",
    "dashboard_password",
    "dashboard_session_secret",
    "health_api_token",
    "id_ed25519",
    "id_rsa",
}
FORBIDDEN_SUFFIXES = (
    ".db",
    ".parquet",
    ".sqlite",
    ".sqlite3",
    ".json.gz",
    ".gpg",
    ".zip",
    ".tar",
    ".tar.gz",
)
SECRET_MARKERS = (
    re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"gh[opusr]_[A-Za-z0-9_]{30,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{40,}"),
)
PRIVATE_EXPORT_PATTERNS = (
    re.compile(r"^HealthAutoExport-.*\.json$", re.IGNORECASE),
    re.compile(r"^export.*\.xml$", re.IGNORECASE),
    re.compile(r"^route_.*\.gpx$", re.IGNORECASE),
)
MAX_SCANNED_FILE_BYTES = 5 * 1024 * 1024

SOURCE_COMMIT = "12cf7d316887f206fcdd0041435b8622445de042"
PROTECTED_NARRATIVE_COMMIT = "14dd29f03fe08d35a89b6ec23bbd07fbbb02eb36"
RECOVERY_CHANGE = "recover-dashboard-documentation"
RECLASSIFY_CHANGE = "reclassify-dashboard-future-specs"
EXPECTED_REQUIREMENT_COUNT = 22
EXPECTED_SCENARIO_COUNT = 64
EXPECTED_CAPABILITIES = (
    "accessible-descriptive-dashboard",
    "dashboard-operational-data",
    "dashboard-release-baseline",
    "private-dashboard-access",
)
EXPECTED_SPEC_PATHS = tuple(
    sorted(
        f"openspec/changes/{RECOVERY_CHANGE}/specs/{capability}/spec.md"
        for capability in EXPECTED_CAPABILITIES
    )
)
PROTECTED_NARRATIVE_PATHS = tuple(
    sorted(
        f"openspec/changes/{RECOVERY_CHANGE}/{filename}"
        for filename in (
            "exploration.md",
            "proposal.md",
            "design.md",
            "tasks.md",
            "verify-report.md",
        )
    )
)
SPEC_BASELINES = {
    EXPECTED_SPEC_PATHS[0]: {
        "byte_count": 6470,
        "sha256": "75aff88eeb257bb223041ce1db5ca35d6e7204649a1d3f1a55143e5ccfdb4781",
        "source_blob_sha1": "d569fd37b7e598a1007d1b422cfdcba4aa46057a",
    },
    EXPECTED_SPEC_PATHS[1]: {
        "byte_count": 12657,
        "sha256": "b3f34054ddb652e6e7ffcd376f92820b9e01080dd80eb3d71dae513f6b10911d",
        "source_blob_sha1": "10b6a7bb86dab865c203b1d609417f67b0fac6ff",
    },
    EXPECTED_SPEC_PATHS[2]: {
        "byte_count": 13530,
        "sha256": "459b47514d9f35e8dc3061d10757f2169c9380b311cc511dfc9bbfe40449c53f",
        "source_blob_sha1": "79810d9ed6f51f366c578df4ed13cd25eeee7d29",
    },
    EXPECTED_SPEC_PATHS[3]: {
        "byte_count": 10601,
        "sha256": "aab8cbd6faf14e66d3d74e646853f16199f0878aba43a413704845fe59020cab",
        "source_blob_sha1": "0978d17ade5072216cea15bdab11707a89e95ab6",
    },
}
NARRATIVE_BASELINES = {
    f"openspec/changes/{RECOVERY_CHANGE}/design.md": {
        "byte_count": 26567,
        "sha256": "03a8c3a24176b090ab8e511eb39fb785d9fcc55ce2543e61335ddde5db6d966f",
        "source_blob_sha1": "cff19ffae2a69ca8d63195aa23bfd8fa120646a9",
    },
    f"openspec/changes/{RECOVERY_CHANGE}/exploration.md": {
        "byte_count": 7578,
        "sha256": "28135872bb4b654f299f9b83f52ec84a054a2df12d800edbc825d106514bae53",
        "source_blob_sha1": "6429ecb63d87b27ede26e518456b74308fe25fd7",
    },
    f"openspec/changes/{RECOVERY_CHANGE}/proposal.md": {
        "byte_count": 14538,
        "sha256": "9a2d937521984565c8d80bc8138954f28a9ed329e01446b676b27d126ea0d1eb",
        "source_blob_sha1": "ab8732903105c55a9b7ba36571c735af05203016",
    },
    f"openspec/changes/{RECOVERY_CHANGE}/tasks.md": {
        "byte_count": 5518,
        "sha256": "b8b8d803e2d3b9a3e32a0e5e6fed04f80a44aa3eeaeb47caac7df3f54a9e0864",
        "source_blob_sha1": "13be9802762c1490d77aa39370555a8070af7c1f",
    },
    f"openspec/changes/{RECOVERY_CHANGE}/verify-report.md": {
        "byte_count": 7164,
        "sha256": "b70d361de715a2a202c4a37abbb7dd8ea87d28c763219d57886897edb24113c1",
        "source_blob_sha1": "f7ee8fe55a89d45d022de3e49213d615ac73592a",
    },
}
MANIFEST_KEYS = {
    "entries",
    "protected_narrative_commit",
    "protected_narratives",
    "schema_version",
    "source_commit",
}
IDENTITY_KEYS = {"byte_count", "sha256", "source_blob_sha1"}
MATRIX_COLUMNS = (
    "Source anchor",
    "Requirement",
    "Scenario count",
    "Scenarios",
    "Future owner",
    "Dependencies",
)
FUTURE_OWNERS = {
    "dashboard-read-contract",
    "browser-authentication-session",
    "frontend-presentation",
    "deployment-release",
}
VERIFY_RESULT_FIELDS = {
    "blockers",
    "build_command",
    "build_exit_code",
    "build_output_hash",
    "critical_findings",
    "evidence_revision",
    "requirements",
    "scenarios",
    "schema",
    "test_command",
    "test_exit_code",
    "test_output_hash",
    "verdict",
}


class GovernanceError(ValueError):
    pass


def _identity(content: bytes) -> dict[str, object]:
    return {
        "byte_count": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "source_blob_sha1": hashlib.sha1(
            f"blob {len(content)}\0".encode() + content
        ).hexdigest(),
    }


def _safe_repository_path(value: object) -> str:
    if not isinstance(value, str) or "\\" in value:
        raise GovernanceError("manifest path is not normalized")
    path = PurePosixPath(value)
    if path.is_absolute() or not value or value != path.as_posix():
        raise GovernanceError("manifest path is not normalized")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise GovernanceError("manifest path is unsafe")
    return value


def discover_change_root(root: Path, change_name: str) -> Path:
    changes = root / "openspec/changes"
    active = changes / change_name
    candidates = [active] if active.is_dir() else []
    archive = changes / "archive"
    malformed: list[Path] = []
    if archive.is_dir():
        for candidate in archive.iterdir():
            if not candidate.is_dir() or not candidate.name.endswith(f"-{change_name}"):
                continue
            if re.fullmatch(rf"\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(change_name)}", candidate.name):
                candidates.append(candidate)
            else:
                malformed.append(candidate)
    if malformed:
        raise GovernanceError(f"malformed archived change root: {malformed[0]}")
    if len(candidates) != 1:
        raise GovernanceError(
            f"expected exactly one active or archived root for {change_name}; "
            f"found {len(candidates)}"
        )
    return candidates[0]


def _is_archived_change_root(path: Path) -> bool:
    return path.parent.name == "archive"


def is_documentation_evidence(filename: str, mode: int = stat.S_IFREG | 0o644) -> bool:
    try:
        path = PurePosixPath(_safe_repository_path(filename))
    except GovernanceError:
        return False
    return (
        "evidence" in path.parts
        and path.suffix in {".md", ".json"}
        and not mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    )


def _manifest_destination(source_path: str) -> str:
    capability = PurePosixPath(source_path).parent.name
    return (
        f"openspec/changes/{RECLASSIFY_CHANGE}/evidence/"
        f"recover-dashboard-future-specs/{capability}/spec.md"
    )


def _resolve_recorded_path(recorded: str, change: str, current_root: Path) -> Path:
    prefix = PurePosixPath(f"openspec/changes/{change}")
    path = PurePosixPath(recorded)
    try:
        suffix = path.relative_to(prefix)
    except ValueError as error:
        raise GovernanceError(f"path does not belong to {change}: {recorded}") from error
    return current_root.joinpath(*suffix.parts)


def _read_manifest(path: Path) -> dict[str, object]:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GovernanceError(f"manifest JSON cannot be read: {error}") from error
    if not isinstance(data, dict):
        raise GovernanceError("manifest JSON must be an object")
    canonical = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if raw != canonical:
        raise GovernanceError("manifest JSON is not canonical")
    return data


def _validate_identity_record(
    record: object,
    path_key: str,
    expected_path: str,
    baseline: dict[str, object],
    current_path: Path,
    label: str,
) -> None:
    if not isinstance(record, dict) or set(record) != IDENTITY_KEYS | {path_key}:
        raise GovernanceError(f"{label} identity record has an invalid shape")
    if _safe_repository_path(record[path_key]) != expected_path:
        raise GovernanceError(f"{label} path does not match the contract")
    recorded_identity = {key: record[key] for key in IDENTITY_KEYS}
    if recorded_identity != baseline:
        raise GovernanceError(f"{label} identity does not match the reviewed baseline")
    try:
        content = current_path.read_bytes()
        mode = current_path.lstat().st_mode
    except OSError as error:
        raise GovernanceError(f"{label} destination cannot be read: {error}") from error
    if label == "spec" and not is_documentation_evidence(expected_path, mode):
        raise GovernanceError(f"spec destination is not non-executable documentation")
    if _identity(content) != baseline:
        raise GovernanceError(f"{label} identity drift detected")


def _has_mergeable_recovered_spec(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return any(
        len(parts) >= 3
        and parts[index] == "specs"
        and parts[index + 1] in EXPECTED_CAPABILITIES
        and parts[index + 2] == "spec.md"
        for index in range(len(parts) - 2)
    )


def _validate_pass_verification(report: str) -> None:
    lines = report.splitlines()
    if not lines or lines[0] != "```yaml":
        raise GovernanceError("verification envelope is missing or malformed")
    try:
        end = lines.index("```", 1)
    except ValueError as error:
        raise GovernanceError("verification envelope is missing or malformed") from error

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.fullmatch(r"([a-z][a-z0-9_]*): (.+)", line)
        if match is None:
            raise GovernanceError("verification envelope contains malformed YAML")
        key, value = match.groups()
        if key in fields or value != value.strip():
            raise GovernanceError("verification envelope contains duplicate or malformed fields")
        fields[key] = value
    if set(fields) != VERIFY_RESULT_FIELDS:
        raise GovernanceError("verification envelope fields are missing or unknown")
    if fields["schema"] != "gentle-ai.verify-result/v1":
        raise GovernanceError("verification schema is invalid")
    if fields["verdict"] != "pass":
        raise GovernanceError("verification verdict is not PASS")
    if fields["blockers"] != "0" or fields["critical_findings"] != "0":
        raise GovernanceError("PASS verification contains blocking findings")
    for field, expected in (("requirements", "8/8"), ("scenarios", "16/16")):
        if fields[field] != expected:
            raise GovernanceError(f"verification {field} are not fully compliant")
    if fields["test_exit_code"] != "0" or fields["build_exit_code"] != "0":
        raise GovernanceError("PASS verification contains a failed command")
    for field in ("evidence_revision", "test_output_hash", "build_output_hash"):
        if re.fullmatch(r"sha256:[0-9a-f]{64}", fields[field]) is None:
            raise GovernanceError(f"verification {field} is missing or malformed")

    marker = "```json\n"
    if report.count(marker) != 1:
        raise GovernanceError("canonical verification evidence is missing or ambiguous")
    evidence_start = report.index(marker) + len(marker)
    evidence_end = report.find("```", evidence_start)
    if evidence_end < 0:
        raise GovernanceError("canonical verification evidence is malformed")
    evidence_bytes = report[evidence_start:evidence_end].encode()
    try:
        evidence = json.loads(evidence_bytes)
    except json.JSONDecodeError as error:
        raise GovernanceError("canonical verification evidence is malformed") from error
    canonical = (json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if evidence_bytes != canonical:
        raise GovernanceError("verification evidence JSON is not canonical")
    revision = "sha256:" + hashlib.sha256(canonical).hexdigest()
    if fields["evidence_revision"] != revision:
        raise GovernanceError("verification evidence revision does not match canonical evidence")

    expected_summary = {
        "schema": "gentle-ai.sdd-verification-evidence/v1",
        "verdict": "pass",
        "blockers": 0,
        "critical_findings": 0,
        "requirements": fields["requirements"],
        "scenarios": fields["scenarios"],
    }
    if not isinstance(evidence, dict) or any(
        evidence.get(key) != value for key, value in expected_summary.items()
    ):
        raise GovernanceError("verification evidence contradicts the PASS envelope")
    checks = evidence.get("checks")
    if not isinstance(checks, list) or any(
        not isinstance(check, dict)
        or set(check) != {"command", "exit_code", "output_hash"}
        or check["exit_code"] != 0
        or not isinstance(check["output_hash"], str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", check["output_hash"]) is None
        for check in checks
    ):
        raise GovernanceError("verification evidence checks are malformed or failed")
    for prefix in ("test", "build"):
        expected_check = {
            "command": fields[f"{prefix}_command"],
            "exit_code": 0,
            "output_hash": fields[f"{prefix}_output_hash"],
        }
        if checks.count(expected_check) != 1:
            raise GovernanceError(f"verification {prefix} output is not bound to evidence")


def _validate_archive_preconditions(
    recovery_root: Path,
    reclassify_root: Path,
    tracked_paths: list[str],
) -> None:
    if any(_has_mergeable_recovered_spec(path) for path in tracked_paths):
        raise GovernanceError("recovered evidence remains in a mergeable specs path")
    if _is_archived_change_root(recovery_root) and not _is_archived_change_root(
        reclassify_root
    ):
        raise GovernanceError("recovery archive requires archived reclassification")
    if _is_archived_change_root(reclassify_root):
        verification = reclassify_root / "verify-report.md"
        try:
            report = verification.read_text(encoding="utf-8")
        except OSError as error:
            raise GovernanceError("archived reclassification lacks verification") from error
        _validate_pass_verification(report)


def validate_relocation_manifest(
    root: Path,
    recovery_root: Path,
    reclassify_root: Path,
    tracked_paths: list[str],
    *,
    spec_baselines: dict[str, dict[str, object]] | None = None,
    narrative_baselines: dict[str, dict[str, object]] | None = None,
) -> list[tuple[str, str]]:
    spec_baselines = SPEC_BASELINES if spec_baselines is None else spec_baselines
    narrative_baselines = (
        NARRATIVE_BASELINES if narrative_baselines is None else narrative_baselines
    )
    manifest_path = (
        reclassify_root
        / "evidence/recover-dashboard-future-specs/relocation-manifest.json"
    )
    data = _read_manifest(manifest_path)
    if set(data) != MANIFEST_KEYS or data["schema_version"] != 1:
        raise GovernanceError("manifest schema v1 shape is invalid")
    if data["source_commit"] != SOURCE_COMMIT:
        raise GovernanceError("manifest source commit is invalid")
    if data["protected_narrative_commit"] != PROTECTED_NARRATIVE_COMMIT:
        raise GovernanceError("manifest protected narrative commit is invalid")

    entries = data["entries"]
    if not isinstance(entries, list) or len(entries) != 4:
        raise GovernanceError("manifest must contain exactly four entries")
    entry_paths = [entry.get("source_path") for entry in entries if isinstance(entry, dict)]
    if entry_paths != list(EXPECTED_SPEC_PATHS):
        raise GovernanceError("manifest entries are unsafe, missing, or out of order")

    destinations: set[str] = set()
    restoration: list[tuple[str, str]] = []
    for entry, source_path in zip(entries, EXPECTED_SPEC_PATHS, strict=True):
        if not isinstance(entry, dict) or set(entry) != IDENTITY_KEYS | {
            "source_path",
            "destination_path",
        }:
            raise GovernanceError("spec identity record has an invalid shape")
        destination = _safe_repository_path(entry["destination_path"])
        if destination != _manifest_destination(source_path) or destination in destinations:
            raise GovernanceError("manifest destination is conflicting or invalid")
        destinations.add(destination)
        current = _resolve_recorded_path(destination, RECLASSIFY_CHANGE, reclassify_root)
        _validate_identity_record(
            {key: entry[key] for key in IDENTITY_KEYS | {"destination_path"}},
            "destination_path",
            destination,
            spec_baselines[source_path],
            current,
            "spec",
        )
        restoration.append((source_path, destination))

    narratives = data["protected_narratives"]
    if not isinstance(narratives, list) or len(narratives) != 5:
        raise GovernanceError("manifest must contain exactly five protected narratives")
    narrative_paths = [item.get("path") for item in narratives if isinstance(item, dict)]
    if narrative_paths != list(PROTECTED_NARRATIVE_PATHS):
        raise GovernanceError("protected narratives are missing or out of order")
    for record, source_path in zip(narratives, PROTECTED_NARRATIVE_PATHS, strict=True):
        current = _resolve_recorded_path(source_path, RECOVERY_CHANGE, recovery_root)
        _validate_identity_record(
            record,
            "path",
            source_path,
            narrative_baselines[source_path],
            current,
            "narrative",
        )

    _validate_archive_preconditions(recovery_root, reclassify_root, tracked_paths)
    return restoration


def requirement_slug(requirement: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", requirement.lower()).strip("-")


def _parse_spec_contract(path: Path) -> list[tuple[str, list[str]]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise GovernanceError(f"cannot parse evidence spec {path}: {error}") from error
    requirements: list[tuple[str, list[str]]] = []
    current_scenarios: list[str] | None = None
    for line in lines:
        if line.startswith("### Requirement: "):
            name = line.removeprefix("### Requirement: ").strip()
            if not name:
                raise GovernanceError(f"empty requirement heading in {path}")
            current_scenarios = []
            requirements.append((name, current_scenarios))
        elif line.startswith("#### Scenario: "):
            name = line.removeprefix("#### Scenario: ").strip()
            if current_scenarios is None or not name:
                raise GovernanceError(f"orphan or empty scenario heading in {path}")
            current_scenarios.append(name)
    return requirements


def _parse_matrix(path: Path) -> tuple[int, int, list[list[str]]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise GovernanceError(f"cannot parse requirement matrix: {error}") from error
    requirement_match = next(
        (re.fullmatch(r"Requirements: (\d+)", line) for line in lines if line.startswith("Requirements:")),
        None,
    )
    scenario_match = next(
        (re.fullmatch(r"Scenarios: (\d+)", line) for line in lines if line.startswith("Scenarios:")),
        None,
    )
    if requirement_match is None or scenario_match is None:
        raise GovernanceError("matrix count declarations are missing or malformed")
    header = "| " + " | ".join(MATRIX_COLUMNS) + " |"
    try:
        header_index = lines.index(header)
    except ValueError as error:
        raise GovernanceError("matrix columns do not match the contract") from error
    if header_index + 1 >= len(lines) or not re.fullmatch(
        r"\|---\|---\|---:?\|---\|---\|---\|", lines[header_index + 1]
    ):
        raise GovernanceError("matrix columns separator is malformed")
    rows: list[list[str]] = []
    for line in lines[header_index + 2 :]:
        if not line.strip():
            continue
        if not line.startswith("|") or not line.endswith("|"):
            raise GovernanceError("matrix row is malformed")
        cells = [cell.strip() for cell in line[1:-1].split("|")]
        if len(cells) != len(MATRIX_COLUMNS) or any(not cell for cell in cells):
            raise GovernanceError("matrix row columns are malformed")
        rows.append(cells)
    return int(requirement_match.group(1)), int(scenario_match.group(1)), rows


def validate_requirement_matrix(reclassify_root: Path) -> None:
    evidence_root = reclassify_root / "evidence/recover-dashboard-future-specs"
    expected: list[tuple[str, str, list[str], str]] = []
    for capability in EXPECTED_CAPABILITIES:
        spec_path = evidence_root / capability / "spec.md"
        for index, (requirement, scenarios) in enumerate(
            _parse_spec_contract(spec_path), start=1
        ):
            anchor = (
                f"evidence/recover-dashboard-future-specs/{capability}/spec.md"
                f"#requirement-{requirement_slug(requirement)}"
            )
            dependency = "None"
            if capability == "dashboard-operational-data":
                dependency = (
                    "SQLite phases 4–10; SQLite phases 11–17"
                    if index == 1
                    else "SQLite phases 4–10"
                )
            expected.append((anchor, requirement, scenarios, dependency))

    parsed_scenarios = sum(len(item[2]) for item in expected)
    if len(expected) != EXPECTED_REQUIREMENT_COUNT:
        raise GovernanceError(
            f"evidence specs must parse to exactly {EXPECTED_REQUIREMENT_COUNT} requirements"
        )
    if parsed_scenarios != EXPECTED_SCENARIO_COUNT:
        raise GovernanceError(
            f"evidence specs must parse to exactly {EXPECTED_SCENARIO_COUNT} scenarios"
        )

    declared_requirements, declared_scenarios, rows = _parse_matrix(
        evidence_root / "requirement-matrix.md"
    )
    if declared_requirements != EXPECTED_REQUIREMENT_COUNT or len(rows) != EXPECTED_REQUIREMENT_COUNT:
        raise GovernanceError("matrix must declare and contain exactly 22 requirements")
    if declared_scenarios != EXPECTED_SCENARIO_COUNT:
        raise GovernanceError("matrix must declare exactly 64 scenarios")

    anchors = [row[0] for row in rows]
    expected_anchors = [item[0] for item in expected]
    if anchors != expected_anchors or len(set(anchors)) != len(anchors):
        raise GovernanceError("matrix anchors are missing, duplicated, or out of order")
    seen_scenarios: set[str] = set()
    for row, (anchor, requirement, scenarios, dependency) in zip(rows, expected, strict=True):
        row_anchor, row_requirement, count, scenario_cell, owner, row_dependency = row
        row_scenarios = scenario_cell.split("<br>")
        if row_anchor != anchor or row_requirement != requirement:
            raise GovernanceError("matrix requirement name or anchor drift detected")
        if not count.isdigit() or int(count) != len(scenarios):
            raise GovernanceError("matrix scenario count drift detected")
        if row_scenarios != scenarios or seen_scenarios.intersection(row_scenarios):
            raise GovernanceError("matrix scenarios are missing, duplicated, or altered")
        seen_scenarios.update(row_scenarios)
        if owner not in FUTURE_OWNERS:
            raise GovernanceError("matrix owner must be exactly one allowlisted owner")
        if dependency != "None" and row_dependency != dependency:
            raise GovernanceError("matrix lost required SQLite phase dependencies")
    if len(seen_scenarios) != EXPECTED_SCENARIO_COUNT:
        raise GovernanceError("matrix must account for exactly 64 unique scenarios")


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def audit_file(filename: str, root: Path = Path(".")) -> list[str]:
    failures: list[str] = []
    path = PurePosixPath(filename)
    lower = filename.lower()
    if path.name in FORBIDDEN_NAMES or FORBIDDEN_PARTS.intersection(path.parts):
        failures.append(f"archivo privado o generado versionado: {filename}")
    if lower.endswith(FORBIDDEN_SUFFIXES):
        failures.append(f"formato privado o binario versionado: {filename}")
    if any(pattern.match(path.name) for pattern in PRIVATE_EXPORT_PATTERNS):
        failures.append(f"exportación privada versionada: {filename}")

    if failures:
        return failures

    file_path = root / filename
    try:
        file_status = file_path.lstat()
    except OSError as error:
        return [f"no se pudo inspeccionar {filename}: {error}"]

    if stat.S_ISLNK(file_status.st_mode):
        return [f"enlace simbólico no permitido: {filename}"]
    if not stat.S_ISREG(file_status.st_mode):
        return [f"archivo no regular no permitido: {filename}"]
    if file_status.st_size > MAX_SCANNED_FILE_BYTES:
        return [
            f"archivo demasiado grande para auditar: {filename} "
            f"({file_status.st_size} bytes; límite {MAX_SCANNED_FILE_BYTES})"
        ]

    try:
        content = file_path.read_bytes()
    except OSError as error:
        return [f"no se pudo leer {filename}: {error}"]

    for marker in SECRET_MARKERS:
        if marker.search(content):
            failures.append(f"posible secreto detectado en {filename}")

    return failures


def main(
    root: Path = Path("."),
    files: list[str] | None = None,
    *,
    spec_baselines: dict[str, dict[str, object]] | None = None,
    narrative_baselines: dict[str, dict[str, object]] | None = None,
) -> None:
    files = tracked_files() if files is None else files
    failures = [
        failure for filename in files for failure in audit_file(filename, root)
    ]
    try:
        recovery_root = discover_change_root(root, RECOVERY_CHANGE)
        reclassify_root = discover_change_root(root, RECLASSIFY_CHANGE)
        validate_relocation_manifest(
            root,
            recovery_root,
            reclassify_root,
            files,
            spec_baselines=spec_baselines,
            narrative_baselines=narrative_baselines,
        )
        validate_requirement_matrix(reclassify_root)
    except GovernanceError as error:
        failures.append(f"gobernanza de evidencia inválida: {error}")

    if failures:
        print("Auditoría del repositorio: ERROR")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print(f"Auditoría del repositorio: OK ({len(files)} archivos versionados)")


if __name__ == "__main__":
    main()
