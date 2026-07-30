from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.check_repository import (
    EXPECTED_CAPABILITIES,
    EXPECTED_REQUIREMENT_COUNT,
    EXPECTED_SCENARIO_COUNT,
    EXPECTED_SPEC_PATHS,
    MAX_SCANNED_FILE_BYTES,
    PROTECTED_NARRATIVE_COMMIT,
    PROTECTED_NARRATIVE_PATHS,
    PRIVATE_ARTIFACT_PARTS,
    SOURCE_COMMIT,
    GovernanceError,
    audit_file,
    discover_change_root,
    is_documentation_evidence,
    main,
    requirement_slug,
    validate_requirement_matrix,
    validate_relocation_manifest,
)


RECOVERY_CHANGE = "recover-dashboard-documentation"
RECLASSIFY_CHANGE = "reclassify-dashboard-future-specs"


def identity(content: bytes) -> dict[str, object]:
    return {
        "source_blob_sha1": hashlib.sha1(
            f"blob {len(content)}\0".encode() + content
        ).hexdigest(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_count": len(content),
    }


class GovernanceFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.recovery_root = root / "openspec/changes" / RECOVERY_CHANGE
        self.reclassify_root = root / "openspec/changes" / RECLASSIFY_CHANGE
        self.evidence_root = (
            self.reclassify_root / "evidence/recover-dashboard-future-specs"
        )
        self.spec_baselines: dict[str, dict[str, object]] = {}
        self.narrative_baselines: dict[str, dict[str, object]] = {}
        self.tracked_paths: list[str] = []

    def create(self) -> None:
        for index, source_path in enumerate(EXPECTED_SPEC_PATHS, start=1):
            capability = Path(source_path).parent.name
            destination = self.evidence_root / capability / "spec.md"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                content = destination.read_bytes()
            else:
                content = f"# Synthetic spec {index}\n".encode()
                destination.write_bytes(content)
            destination_path = destination.relative_to(self.root).as_posix()
            self.spec_baselines[source_path] = identity(content)
            self.tracked_paths.append(destination_path)

        for index, source_path in enumerate(PROTECTED_NARRATIVE_PATHS, start=1):
            current = self.recovery_root / Path(source_path).name
            content = f"# Protected narrative {index}\n".encode()
            current.parent.mkdir(parents=True, exist_ok=True)
            current.write_bytes(content)
            self.narrative_baselines[source_path] = identity(content)
            self.tracked_paths.append(current.relative_to(self.root).as_posix())

        self.write_manifest()

    def manifest_data(self) -> dict[str, object]:
        entries = []
        for source_path in EXPECTED_SPEC_PATHS:
            capability = Path(source_path).parent.name
            destination_path = (
                f"openspec/changes/{RECLASSIFY_CHANGE}/evidence/"
                f"recover-dashboard-future-specs/{capability}/spec.md"
            )
            entries.append(
                {
                    "source_path": source_path,
                    "destination_path": destination_path,
                    **self.spec_baselines[source_path],
                }
            )
        narratives = [
            {"path": path, **self.narrative_baselines[path]}
            for path in PROTECTED_NARRATIVE_PATHS
        ]
        return {
            "entries": entries,
            "protected_narrative_commit": PROTECTED_NARRATIVE_COMMIT,
            "protected_narratives": narratives,
            "schema_version": 1,
            "source_commit": SOURCE_COMMIT,
        }

    def write_manifest(self, data: dict[str, object] | None = None) -> None:
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        payload = self.manifest_data() if data is None else data
        (self.evidence_root / "relocation-manifest.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def validate(self) -> list[tuple[str, str]]:
        return validate_relocation_manifest(
            self.root,
            self.recovery_root,
            self.reclassify_root,
            self.tracked_paths,
            spec_baselines=self.spec_baselines,
            narrative_baselines=self.narrative_baselines,
        )


SCENARIO_COUNTS = {
    "accessible-descriptive-dashboard": (5, 2, 2),
    "dashboard-operational-data": (4, 4, 3, 5, 3),
    "dashboard-release-baseline": (2, 4, 2, 3, 2, 3, 1, 2),
    "private-dashboard-access": (2, 2, 4, 5, 2, 2),
}
OWNERS = {
    "accessible-descriptive-dashboard": "frontend-presentation",
    "dashboard-operational-data": "dashboard-read-contract",
    "dashboard-release-baseline": "deployment-release",
    "private-dashboard-access": "browser-authentication-session",
}


class MatrixFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.change_root = root / "openspec/changes" / RECLASSIFY_CHANGE
        self.evidence_root = self.change_root / "evidence/recover-dashboard-future-specs"
        self.rows: list[list[str]] = []

    def create(self) -> None:
        for capability in EXPECTED_CAPABILITIES:
            spec = self.evidence_root / capability / "spec.md"
            spec.parent.mkdir(parents=True, exist_ok=True)
            lines = [f"# {capability}\n", "## Requirements\n"]
            for requirement_index, scenario_count in enumerate(
                SCENARIO_COUNTS[capability], start=1
            ):
                requirement = f"Requirement {capability} {requirement_index}"
                scenarios = [
                    f"Scenario {capability} {requirement_index}.{index}"
                    for index in range(1, scenario_count + 1)
                ]
                lines.append(f"### Requirement: {requirement}\n")
                lines.extend(f"#### Scenario: {scenario}\n" for scenario in scenarios)
                dependency = "None"
                if capability == "dashboard-operational-data":
                    dependency = (
                        "SQLite phases 4–10; SQLite phases 11–17"
                        if requirement_index == 1
                        else "SQLite phases 4–10"
                    )
                anchor = (
                    f"evidence/recover-dashboard-future-specs/{capability}/spec.md"
                    f"#requirement-{requirement_slug(requirement)}"
                )
                self.rows.append(
                    [
                        anchor,
                        requirement,
                        str(scenario_count),
                        "<br>".join(scenarios),
                        OWNERS[capability],
                        dependency,
                    ]
                )
            spec.write_text("\n".join(lines), encoding="utf-8")
        self.write_matrix()

    def matrix_text(self, rows: list[list[str]] | None = None) -> str:
        rows = self.rows if rows is None else rows
        lines = [
            "# Requirement Ownership Matrix",
            "",
            "Requirements: 22",
            "Scenarios: 64",
            "",
            "| Source anchor | Requirement | Scenario count | Scenarios | Future owner | Dependencies |",
            "|---|---|---:|---|---|---|",
        ]
        lines.extend("| " + " | ".join(row) + " |" for row in rows)
        return "\n".join(lines) + "\n"

    def write_matrix(self, text: str | None = None) -> None:
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        (self.evidence_root / "requirement-matrix.md").write_text(
            self.matrix_text() if text is None else text,
            encoding="utf-8",
        )

    def validate(self) -> None:
        validate_requirement_matrix(self.change_root)


class AuditFileTests(unittest.TestCase):
    def test_rejects_tracked_private_reconciliation_directories(self) -> None:
        for part in PRIVATE_ARTIFACT_PARTS:
            with self.subTest(part=part):
                path = f"{part}/synthetic.txt"
                self.assertEqual(
                    audit_file(path),
                    [f"archivo privado o generado versionado: {path}"],
                )

    def test_rejects_symbolic_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "target.txt").write_text("contenido", encoding="utf-8")
            (root / "link.txt").symlink_to(root / "target.txt")

            self.assertEqual(
                audit_file("link.txt", root),
                ["enlace simbólico no permitido: link.txt"],
            )

    def test_rejects_files_above_scan_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / "large.txt").open("wb") as file:
                file.truncate(MAX_SCANNED_FILE_BYTES + 1)

            failures = audit_file("large.txt", root)

            self.assertEqual(len(failures), 1)
            self.assertIn("archivo demasiado grande para auditar", failures[0])

    def test_skips_content_checks_for_already_forbidden_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "private.zip").symlink_to(root / "missing-target")

            self.assertEqual(
                audit_file("private.zip", root),
                ["formato privado o binario versionado: private.zip"],
            )


class PlanningEvidenceDiscoveryTests(unittest.TestCase):
    def test_contract_constants_are_pinned(self) -> None:
        self.assertEqual(SOURCE_COMMIT, "12cf7d316887f206fcdd0041435b8622445de042")
        self.assertEqual(
            PROTECTED_NARRATIVE_COMMIT,
            "14dd29f03fe08d35a89b6ec23bbd07fbbb02eb36",
        )
        self.assertEqual(len(EXPECTED_SPEC_PATHS), 4)
        self.assertEqual(len(PROTECTED_NARRATIVE_PATHS), 5)
        self.assertEqual((EXPECTED_REQUIREMENT_COUNT, EXPECTED_SCENARIO_COUNT), (22, 64))

    def test_discovers_one_active_or_archived_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = root / "openspec/changes" / RECLASSIFY_CHANGE
            active.mkdir(parents=True)
            self.assertEqual(discover_change_root(root, RECLASSIFY_CHANGE), active)
            active.rmdir()
            archived = (
                root
                / "openspec/changes/archive"
                / f"2026-07-26-{RECLASSIFY_CHANGE}"
            )
            archived.mkdir(parents=True)
            self.assertEqual(discover_change_root(root, RECLASSIFY_CHANGE), archived)

    def test_rejects_missing_duplicate_conflicting_and_malformed_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            changes = root / "openspec/changes"
            changes.mkdir(parents=True)
            with self.assertRaisesRegex(GovernanceError, "exactly one"):
                discover_change_root(root, RECLASSIFY_CHANGE)

            active = changes / RECLASSIFY_CHANGE
            archive = changes / "archive" / f"2026-07-26-{RECLASSIFY_CHANGE}"
            active.mkdir()
            archive.mkdir(parents=True)
            with self.assertRaisesRegex(GovernanceError, "exactly one"):
                discover_change_root(root, RECLASSIFY_CHANGE)

            active.rmdir()
            malformed = changes / "archive" / f"July-26-{RECLASSIFY_CHANGE}"
            malformed.mkdir()
            with self.assertRaisesRegex(GovernanceError, "malformed"):
                discover_change_root(root, RECLASSIFY_CHANGE)

    def test_accepts_only_non_executable_contracted_evidence(self) -> None:
        accepted = [
            "openspec/changes/example/evidence/item/spec.md",
            "openspec/changes/example/evidence/item/manifest.json",
        ]
        rejected = [
            "openspec/changes/example/evidence/requirements.txt",
            "openspec/changes/example/evidence/CMakeLists.txt",
            "openspec/changes/example/evidence/README.sh",
            "openspec/changes/example/evidence/page.mdx",
        ]
        self.assertTrue(all(is_documentation_evidence(path) for path in accepted))
        self.assertTrue(all(not is_documentation_evidence(path) for path in rejected))
        self.assertFalse(
            is_documentation_evidence(accepted[0], mode=os.stat_result((0o100755,) + (0,) * 9).st_mode)
        )


class RelocationManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = GovernanceFixture(Path(self.temporary.name))
        self.fixture.create()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_accepts_canonical_complete_manifest(self) -> None:
        plan = self.fixture.validate()
        self.assertEqual(len(plan), 4)
        self.assertEqual(plan[0][0], EXPECTED_SPEC_PATHS[0])

    def test_rejects_malformed_or_noncanonical_json(self) -> None:
        manifest = self.fixture.evidence_root / "relocation-manifest.json"
        manifest.write_text("{not-json}\n", encoding="utf-8")
        with self.assertRaisesRegex(GovernanceError, "JSON"):
            self.fixture.validate()

        self.fixture.write_manifest()
        manifest.write_text(manifest.read_text(encoding="utf-8").rstrip(), encoding="utf-8")
        with self.assertRaisesRegex(GovernanceError, "canonical"):
            self.fixture.validate()

    def test_rejects_wrong_shape_commits_paths_and_order(self) -> None:
        mutations = [
            lambda data: data.update(source_commit="0" * 40),
            lambda data: data.update(protected_narrative_commit="0" * 40),
            lambda data: data["entries"].pop(),
            lambda data: data["protected_narratives"].pop(),
            lambda data: data["entries"].reverse(),
            lambda data: data["entries"][0].update(source_path="../unsafe/spec.md"),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                data = self.fixture.manifest_data()
                mutate(data)
                self.fixture.write_manifest(data)
                with self.assertRaises(GovernanceError):
                    self.fixture.validate()

    def test_rejects_missing_or_altered_destination_identity(self) -> None:
        destination = self.fixture.evidence_root / "accessible-descriptive-dashboard/spec.md"
        destination.unlink()
        with self.assertRaisesRegex(GovernanceError, "destination"):
            self.fixture.validate()

        destination.write_bytes(b"altered\n")
        with self.assertRaisesRegex(GovernanceError, "identity"):
            self.fixture.validate()

    def test_rejects_blob_sha_count_and_narrative_drift(self) -> None:
        for field, value in (
            ("source_blob_sha1", "0" * 40),
            ("sha256", "0" * 64),
            ("byte_count", 999),
        ):
            with self.subTest(field=field):
                data = self.fixture.manifest_data()
                data["entries"][0][field] = value
                self.fixture.write_manifest(data)
                with self.assertRaisesRegex(GovernanceError, "identity"):
                    self.fixture.validate()

        self.fixture.write_manifest()
        (self.fixture.recovery_root / "proposal.md").write_text("drift\n", encoding="utf-8")
        with self.assertRaisesRegex(GovernanceError, "narrative"):
            self.fixture.validate()

    def test_rejects_mergeable_or_conflicting_paths_and_premature_archive(self) -> None:
        source_path = EXPECTED_SPEC_PATHS[0]
        self.fixture.tracked_paths.append(source_path)
        with self.assertRaisesRegex(GovernanceError, "mergeable"):
            self.fixture.validate()

        self.fixture.tracked_paths.pop()
        archived_recovery = (
            self.fixture.root
            / "openspec/changes/archive"
            / f"2026-07-26-{RECOVERY_CHANGE}"
        )
        archived_recovery.parent.mkdir(parents=True, exist_ok=True)
        self.fixture.recovery_root.rename(archived_recovery)
        self.fixture.recovery_root = archived_recovery
        with self.assertRaisesRegex(GovernanceError, "reclassification"):
            self.fixture.validate()

    def test_archived_reclassification_requires_canonical_pass_verification(self) -> None:
        archived = (
            self.fixture.root
            / "openspec/changes/archive"
            / f"2026-07-26-{RECLASSIFY_CHANGE}"
        )
        archived.parent.mkdir(parents=True, exist_ok=True)
        self.fixture.reclassify_root.rename(archived)
        self.fixture.reclassify_root = archived
        self.fixture.evidence_root = archived / "evidence/recover-dashboard-future-specs"
        test_hash = "sha256:" + "b" * 64
        build_hash = "sha256:" + "c" * 64
        evidence = json.dumps(
            {
                "blockers": 0,
                "checks": [
                    {
                        "command": ".venv/bin/python -m pytest",
                        "exit_code": 0,
                        "output_hash": test_hash,
                    },
                    {
                        "command": ".venv/bin/python scripts/check_repository.py",
                        "exit_code": 0,
                        "output_hash": build_hash,
                    },
                ],
                "critical_findings": 0,
                "requirements": "8/8",
                "scenarios": "16/16",
                "schema": "gentle-ai.sdd-verification-evidence/v1",
                "verdict": "pass",
            },
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        evidence_revision = "sha256:" + hashlib.sha256(evidence.encode()).hexdigest()
        report = f"""```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: {evidence_revision}
verdict: pass
blockers: 0
critical_findings: 0
requirements: 8/8
scenarios: 16/16
test_command: .venv/bin/python -m pytest
test_exit_code: 0
test_output_hash: {test_hash}
build_command: .venv/bin/python scripts/check_repository.py
build_exit_code: 0
build_output_hash: {build_hash}
```
### Canonical Verification Evidence

```json
{evidence}```
"""
        verification = archived / "verify-report.md"
        verification.write_text(report, encoding="utf-8")
        self.assertEqual(len(self.fixture.validate()), 4)

        invalid_reports = {
            "bare": "status: pass\n",
            "incomplete": "```yaml\nschema: gentle-ai.verify-result/v1\nverdict: pass\n```\n",
            "duplicate": report.replace("verdict: pass\n", "verdict: pass\nverdict: pass\n"),
            "malformed": report.replace("requirements: 8/8", "requirements: eight/eight"),
            "wrong-schema": report.replace("gentle-ai.verify-result/v1", "verify-result/v1"),
            "contradictory": report.replace("blockers: 0", "blockers: 1"),
            "critical": report.replace("critical_findings: 0", "critical_findings: 1"),
            "partial": report.replace("scenarios: 16/16", "scenarios: 15/16"),
            "wrong-total": report.replace("requirements: 8/8", "requirements: 1/1"),
            "test-failure": report.replace("test_exit_code: 0", "test_exit_code: 1"),
            "build-failure": report.replace("build_exit_code: 0", "build_exit_code: 1"),
            "unbound-evidence": report.replace(evidence_revision, "sha256:" + "a" * 64),
            "missing-hash": report.replace(
                f"evidence_revision: {evidence_revision}\n", ""
            ),
        }
        for case, invalid_report in invalid_reports.items():
            with self.subTest(case=case):
                verification.write_text(invalid_report, encoding="utf-8")
                with self.assertRaises(GovernanceError):
                    self.fixture.validate()


class PlanningEvidenceRollbackTests(unittest.TestCase):
    def test_returns_deterministic_four_file_restoration_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = GovernanceFixture(Path(directory))
            fixture.create()
            plan = fixture.validate()
            self.assertEqual([source for source, _ in plan], list(EXPECTED_SPEC_PATHS))
            self.assertEqual(len({destination for _, destination in plan}), 4)

    def test_rejects_ambiguous_restoration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = GovernanceFixture(Path(directory))
            fixture.create()
            data = fixture.manifest_data()
            data["entries"][1]["destination_path"] = data["entries"][0][
                "destination_path"
            ]
            fixture.write_manifest(data)
            with self.assertRaisesRegex(GovernanceError, "destination"):
                fixture.validate()


class RequirementMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = MatrixFixture(Path(self.temporary.name))
        self.fixture.create()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_accepts_exact_22_requirement_64_scenario_matrix(self) -> None:
        self.assertIsNone(self.fixture.validate())
        self.assertEqual(len(self.fixture.rows), 22)
        self.assertEqual(sum(int(row[2]) for row in self.fixture.rows), 64)

    def test_rejects_columns_and_declared_or_parsed_count_drift(self) -> None:
        text = self.fixture.matrix_text().replace(" | Dependencies |", " |")
        self.fixture.write_matrix(text)
        with self.assertRaisesRegex(GovernanceError, "columns"):
            self.fixture.validate()

        self.fixture.write_matrix(self.fixture.matrix_text().replace("Requirements: 22", "Requirements: 21"))
        with self.assertRaisesRegex(GovernanceError, "22"):
            self.fixture.validate()

        spec = self.fixture.evidence_root / EXPECTED_CAPABILITIES[0] / "spec.md"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("#### Scenario:", "#### Removed:", 1),
            encoding="utf-8",
        )
        self.fixture.write_matrix()
        with self.assertRaisesRegex(GovernanceError, "64"):
            self.fixture.validate()

    def test_rejects_name_anchor_and_scenario_drift(self) -> None:
        for column, replacement in (
            (0, "evidence/wrong.md#requirement-wrong"),
            (1, "Altered requirement"),
            (3, "Altered scenario"),
        ):
            with self.subTest(column=column):
                rows = [row.copy() for row in self.fixture.rows]
                rows[0][column] = replacement
                self.fixture.write_matrix(self.fixture.matrix_text(rows))
                with self.assertRaises(GovernanceError):
                    self.fixture.validate()

        rows = [row.copy() for row in self.fixture.rows]
        rows[1][0] = rows[0][0]
        self.fixture.write_matrix(self.fixture.matrix_text(rows))
        with self.assertRaisesRegex(GovernanceError, "anchor"):
            self.fixture.validate()

    def test_rejects_owner_cardinality_allowlist_and_lost_dependencies(self) -> None:
        for owner in ("unknown-owner", "frontend-presentation, deployment-release"):
            rows = [row.copy() for row in self.fixture.rows]
            rows[0][4] = owner
            self.fixture.write_matrix(self.fixture.matrix_text(rows))
            with self.assertRaisesRegex(GovernanceError, "owner"):
                self.fixture.validate()

        rows = [row.copy() for row in self.fixture.rows]
        operational = next(
            row for row in rows if "dashboard-operational-data" in row[0]
        )
        operational[5] = "None"
        self.fixture.write_matrix(self.fixture.matrix_text(rows))
        with self.assertRaisesRegex(GovernanceError, "SQLite"):
            self.fixture.validate()


class RepositoryGovernanceCliTests(unittest.TestCase):
    def build_fixture(self, root: Path) -> tuple[GovernanceFixture, MatrixFixture]:
        matrix = MatrixFixture(root)
        matrix.create()
        governance = GovernanceFixture(root)
        governance.create()
        return governance, matrix

    def run_cli(self, governance: GovernanceFixture) -> None:
        main(
            governance.root,
            governance.tracked_paths,
            spec_baselines=governance.spec_baselines,
            narrative_baselines=governance.narrative_baselines,
        )

    def test_cli_accepts_complete_active_governance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            governance, _ = self.build_fixture(Path(directory))
            self.run_cli(governance)

    def test_cli_fails_closed_for_incomplete_or_conflicting_state(self) -> None:
        def missing_manifest(governance: GovernanceFixture, _: MatrixFixture) -> None:
            (governance.evidence_root / "relocation-manifest.json").unlink()

        def mergeable(governance: GovernanceFixture, _: MatrixFixture) -> None:
            governance.tracked_paths.append(EXPECTED_SPEC_PATHS[0])

        def matrix_drift(_: GovernanceFixture, matrix: MatrixFixture) -> None:
            matrix.write_matrix(matrix.matrix_text().replace("Scenarios: 64", "Scenarios: 63"))

        def rollback_conflict(governance: GovernanceFixture, _: MatrixFixture) -> None:
            data = governance.manifest_data()
            data["entries"][1]["destination_path"] = data["entries"][0]["destination_path"]
            governance.write_manifest(data)

        def premature_archive(governance: GovernanceFixture, _: MatrixFixture) -> None:
            archive = governance.root / "openspec/changes/archive/2026-07-26-recover-dashboard-documentation"
            archive.parent.mkdir(parents=True)
            governance.recovery_root.rename(archive)

        for mutate in (missing_manifest, mergeable, matrix_drift, rollback_conflict, premature_archive):
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as directory:
                governance, matrix = self.build_fixture(Path(directory))
                mutate(governance, matrix)
                with self.assertRaises(SystemExit):
                    self.run_cli(governance)


if __name__ == "__main__":
    unittest.main()
