import hashlib
import json
import os
import sqlite3
import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

import scripts.reconcile_history as reconciliation_cli
from src.reconciliation import ReconciliationError, discard_staging, stage_reconciliation
from src.operational_store import OperationalStore
from src.storage_schema import connect_operational, create_operational_database


USER_ID = "primary-user"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def private_file(path: Path, content: bytes) -> None:
    path.write_bytes(content)
    path.chmod(0o600)


def source_payload(*rows: tuple[str, str, int]) -> bytes:
    groups: dict[str, list[dict[str, object]]] = {}
    units = {"step_count": "count", "vo2_max": "mL/kg/min"}
    for metric, local_date, value in rows:
        groups.setdefault(metric, []).append({"date": local_date, "qty": value})
    return canonical(
        {
            "data": {
                "metrics": [
                    {"data": data, "name": metric, "units": units[metric]}
                    for metric, data in sorted(groups.items())
                ]
            }
        }
    )


def create_fixture(
    tmp_path: Path,
    *,
    rows: tuple[tuple[str, str, int], ...] = (("step_count", "2026-01-02", 10),),
    identities: list[dict[str, str]] | None = None,
    metrics: list[str] | None = None,
) -> tuple[Path, Path, Path, dict[str, object]]:
    candidate = tmp_path / "candidate"
    sources = tmp_path / "sources"
    candidate.mkdir(mode=0o700)
    sources.mkdir(mode=0o700)
    database = create_operational_database(candidate, user_id=USER_ID)
    payload = source_payload(*rows)
    private_file(sources / "synthetic-annual.json", payload)
    identities = identities or [
        {"local_date": local_date, "metric": metric, "state": "value"}
        for metric, local_date, _ in rows
    ]
    metrics = metrics or sorted({item["metric"] for item in identities})
    manifest: dict[str, object] = {
        "batch_id": "synthetic-baseline",
        "expected_counts": {"identities": len(identities), "sources": 1},
        "generation_context": {"generator": "synthetic-test"},
        "identities": identities,
        "importer_version": "1",
        "kind": "reconciliation",
        "owner": USER_ID,
        "required_evidence": ["semantic_comparison"],
        "schema_version": 1,
        "scope": {
            "end_date": "2026-12-31",
            "metrics": metrics,
            "start_date": "2026-01-01",
        },
        "sources": [
            {
                "name": "synthetic-annual.json",
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        ],
        "timezone": "Europe/Madrid",
    }
    manifest_path = tmp_path / "manifest.json"
    private_file(manifest_path, canonical(manifest))
    return database, manifest_path, sources, manifest


def table_count(database: Path, table: str) -> int:
    with connect_operational(database) as db:
        return db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_stages_canonical_manifest_sources_and_pending_versions_invisibly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    database, manifest, sources, _ = create_fixture(tmp_path)

    result = stage_reconciliation(database, manifest, sources)

    assert (result.resumed, result.sources, result.versions, result.errors) == (False, 1, 1, 0)
    assert capsys.readouterr().out == ""
    with connect_operational(database) as db:
        assert db.execute(
            "SELECT kind,status FROM reconciliation_batches"
        ).fetchall() == [("reconciliation", "pending")]
        assert db.execute(
            "SELECT result,kind FROM import_receipts"
        ).fetchall() == [("pending", "reconciliation")]
        assert db.execute(
            "SELECT metric,local_date,validation_status,live_authority_sequence,batch_authority_sequence FROM metric_versions"
        ).fetchall() == [("step_count", "2026-01-02", "pending", None, None)]
        assert db.execute("SELECT COUNT(*) FROM metric_current").fetchone() == (0,)
        assert db.execute("SELECT COUNT(*) FROM authority_events").fetchone() == (0,)
        assert db.execute("SELECT COUNT(*) FROM live_freshness").fetchone() == (0,)
    artifact = next((database.parent / "batch-sources" / "sha256").glob("*/*.json"))
    retained_manifest = next((database.parent / "manifests").glob("*.json"))
    assert artifact.read_bytes() == (sources / "synthetic-annual.json").read_bytes()
    assert retained_manifest.read_bytes() == manifest.read_bytes()
    assert stat.S_IMODE(artifact.stat().st_mode) == 0o600


def test_equal_identity_occurrences_retain_each_producing_receipt(tmp_path: Path):
    database, manifest_path, sources, manifest = create_fixture(tmp_path)
    duplicate_payload = b" " + (sources / "synthetic-annual.json").read_bytes()
    private_file(sources / "synthetic-copy.json", duplicate_payload)
    manifest["sources"].append(
        {
            "name": "synthetic-copy.json",
            "sha256": hashlib.sha256(duplicate_payload).hexdigest(),
        }
    )
    manifest["expected_counts"]["sources"] = 2
    private_file(manifest_path, canonical(manifest))

    result = stage_reconciliation(database, manifest_path, sources)

    assert (result.sources, result.versions, result.errors) == (2, 2, 0)
    with connect_operational(database) as db:
        versions = db.execute(
            """SELECT receipt_id,canonical_value,context_fingerprint,validation_status
               FROM metric_versions ORDER BY receipt_id"""
        ).fetchall()
        assert len({version[0] for version in versions}) == 2
        assert [version[1] for version in versions] == ["10", "10"]
        assert len({version[2] for version in versions}) == 1
        assert [version[3] for version in versions] == ["pending", "pending"]
        assert db.execute(
            "SELECT COUNT(*) FROM receipt_errors WHERE code='unresolved_conflict'"
        ).fetchone() == (0,)


@pytest.mark.parametrize(
    ("identity_state", "additional_value", "expected_errors"),
    [
        ("value", 11, ["missing_identity", "unresolved_conflict"]),
        ("absence", None, ["unresolved_conflict"]),
    ],
    ids=["differing-values", "value-absence"],
)
def test_only_differing_or_value_absence_occurrences_conflict(
    tmp_path: Path,
    identity_state: str,
    additional_value: int | None,
    expected_errors: list[str],
):
    identity = {"local_date": "2026-01-02", "metric": "step_count", "state": identity_state}
    database, manifest_path, sources, manifest = create_fixture(tmp_path, identities=[identity])
    if additional_value is not None:
        conflicting_payload = source_payload(("step_count", "2026-01-02", additional_value))
        private_file(sources / "synthetic-conflict.json", conflicting_payload)
        manifest["sources"].append(
            {
                "name": "synthetic-conflict.json",
                "sha256": hashlib.sha256(conflicting_payload).hexdigest(),
            }
        )
        manifest["expected_counts"]["sources"] = 2
        private_file(manifest_path, canonical(manifest))

    result = stage_reconciliation(database, manifest_path, sources)

    assert result.versions == 0
    with connect_operational(database) as db:
        assert db.execute("SELECT code FROM receipt_errors ORDER BY code").fetchall() == [
            (code,) for code in expected_errors
        ]


def test_same_payload_in_distinct_same_kind_batches_has_distinct_context(tmp_path: Path):
    database, manifest_path, sources, manifest = create_fixture(tmp_path)
    first = stage_reconciliation(database, manifest_path, sources)
    manifest["batch_id"] = "synthetic-baseline-next"
    private_file(manifest_path, canonical(manifest))

    second = stage_reconciliation(database, manifest_path, sources)

    assert (first.versions, second.versions) == (1, 1)
    with connect_operational(database) as db:
        versions = db.execute(
            """SELECT batch_id,context_fingerprint FROM metric_versions
               ORDER BY batch_id"""
        ).fetchall()
        assert [version[0] for version in versions] == [
            "synthetic-baseline",
            "synthetic-baseline-next",
        ]
        assert len({version[1] for version in versions}) == 2
        assert db.execute("SELECT COUNT(*) FROM imports").fetchone() == (1,)
        assert db.execute("SELECT COUNT(*) FROM import_receipts").fetchone() == (2,)


def test_source_publication_handles_partial_os_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    database, manifest, sources, _ = create_fixture(tmp_path)
    original_write = os.write
    shortened = False

    def partial_write(descriptor: int, content: bytes) -> int:
        nonlocal shortened
        if not shortened and len(content) > 1:
            shortened = True
            return original_write(descriptor, content[: len(content) // 2])
        return original_write(descriptor, content)

    monkeypatch.setattr(os, "write", partial_write)
    result = stage_reconciliation(database, manifest, sources)

    artifact = next((database.parent / "batch-sources" / "sha256").glob("*/*.json"))
    retained_manifest = next((database.parent / "manifests").glob("*.json"))
    assert result.sources == 1
    assert shortened is True
    assert retained_manifest.read_bytes() == manifest.read_bytes()
    assert artifact.read_bytes() == (sources / "synthetic-annual.json").read_bytes()


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (lambda value: value.update(owner="another-owner"), "Manifest identity invalid"),
        (lambda value: value.update(timezone="UTC"), "Manifest identity invalid"),
        (
            lambda value: value["expected_counts"].update(sources=2),
            "Manifest shape invalid",
        ),
        (
            lambda value: value["identities"][0].update(local_date="2027-01-01"),
            "Manifest scope invalid",
        ),
        (lambda value: value["sources"].append(dict(value["sources"][0])), "Manifest sources invalid"),
    ],
)
def test_rejects_identity_scope_and_duplicate_source_before_staging(
    tmp_path: Path, mutation, expected: str
):
    database, manifest_path, sources, manifest = create_fixture(tmp_path)
    mutation(manifest)
    private_file(manifest_path, canonical(manifest))

    with pytest.raises(ReconciliationError, match=f"^{expected}$"):
        stage_reconciliation(database, manifest_path, sources)

    assert table_count(database, "reconciliation_batches") == 0


@pytest.mark.parametrize("failure", ["noncanonical", "source_hash"])
def test_hash_or_canonical_mismatch_is_private_and_changes_no_state(
    tmp_path: Path, failure: str
):
    database, manifest_path, sources, manifest = create_fixture(tmp_path)
    private_token = "private-synthetic-token"
    if failure == "noncanonical":
        private_file(manifest_path, json.dumps(manifest, indent=2).encode())
    else:
        private_file(sources / "synthetic-annual.json", private_token.encode())

    with pytest.raises(ReconciliationError) as captured:
        stage_reconciliation(database, manifest_path, sources)

    message = str(captured.value)
    assert message in {"Manifest is not canonical", "Source verification failed"}
    assert private_token not in message
    assert str(sources) not in message
    assert manifest["sources"][0]["sha256"] not in message
    assert table_count(database, "reconciliation_batches") == 0


def test_sparse_scope_uses_only_explicit_values_and_absence(tmp_path: Path):
    identities = [
        {"local_date": "2026-02-01", "metric": "vo2_max", "state": "value"},
        {"local_date": "2026-10-01", "metric": "vo2_max", "state": "value"},
        {"local_date": "2026-06-01", "metric": "vo2_max", "state": "absence"},
    ]
    database, manifest, sources, _ = create_fixture(
        tmp_path,
        rows=(("vo2_max", "2026-02-01", 40), ("vo2_max", "2026-10-01", 42)),
        identities=identities,
        metrics=["vo2_max"],
    )

    result = stage_reconciliation(database, manifest, sources)

    assert (result.versions, result.errors) == (3, 0)
    with connect_operational(database) as db:
        assert db.execute(
            "SELECT local_date,version_kind FROM metric_versions ORDER BY local_date"
        ).fetchall() == [
            ("2026-02-01", "value"),
            ("2026-06-01", "absence"),
            ("2026-10-01", "value"),
        ]


def test_undeclared_and_missing_identities_are_pending_blocking_errors(tmp_path: Path):
    identities = [
        {"local_date": "2026-01-03", "metric": "step_count", "state": "value"}
    ]
    database, manifest, sources, _ = create_fixture(tmp_path, identities=identities)

    result = stage_reconciliation(database, manifest, sources)

    assert (result.versions, result.errors) == (0, 2)
    with connect_operational(database) as db:
        assert db.execute(
            "SELECT code,metric,local_date FROM receipt_errors ORDER BY code"
        ).fetchall() == [
            ("missing_identity", "step_count", "2026-01-03"),
            ("undeclared_identity", "step_count", "2026-01-02"),
        ]
        assert db.execute("SELECT COUNT(*) FROM metric_current").fetchone() == (0,)


def test_exact_manifest_resume_is_idempotent_but_drift_is_refused(tmp_path: Path):
    database, manifest_path, sources, manifest = create_fixture(tmp_path)
    first = stage_reconciliation(database, manifest_path, sources)

    resumed = stage_reconciliation(database, manifest_path, sources)
    manifest["generation_context"] = {"generator": "changed"}
    private_file(manifest_path, canonical(manifest))

    assert first.resumed is False
    assert resumed.resumed is True
    assert (table_count(database, "reconciliation_batches"), table_count(database, "import_receipts")) == (1, 1)
    with pytest.raises(ReconciliationError, match="^Batch manifest mismatch$"):
        stage_reconciliation(database, manifest_path, sources)
    assert table_count(database, "reconciliation_batches") == 1


def test_staging_rebinds_same_hash_live_artifact_to_batch_source(tmp_path: Path):
    database, manifest, sources, _ = create_fixture(tmp_path)
    payload = (sources / "synthetic-annual.json").read_bytes()
    live = OperationalStore(database, user_id=USER_ID).record_receipt(
        payload,
        receipt_id="existing-live-receipt",
        kind="live",
        parser_version="1",
        contract_version="1",
        source_metadata={},
        result="accepted",
        received_at=datetime(2026, 1, 3, tzinfo=UTC),
        contract_valid=True,
    )
    digest = hashlib.sha256(payload).hexdigest()
    with connect_operational(database) as db:
        live_path = db.execute("SELECT relative_path FROM artifacts WHERE artifact_sha256=?", (digest,)).fetchone()[0]

    stage_reconciliation(database, manifest, sources)

    with connect_operational(database) as db:
        assert db.execute("SELECT COUNT(*) FROM imports").fetchone() == (1,)
        assert db.execute("SELECT DISTINCT import_id FROM import_receipts").fetchall() == [(live.import_id,)]
        assert db.execute(
            "SELECT kind,relative_path FROM artifacts WHERE artifact_sha256=?", (digest,)
        ).fetchone() == ("batch_source", f"batch-sources/sha256/{digest[:2]}/{digest}.json")
        assert db.execute("SELECT purpose FROM receipt_artifacts ORDER BY purpose").fetchall() == [("batch_source",), ("raw_payload",)]
    assert (database.parent / live_path).exists()


def test_output_inside_git_worktree_and_unsafe_cleanup_are_refused(tmp_path: Path):
    database, manifest, sources, _ = create_fixture(tmp_path)
    (database.parent / ".git").mkdir()

    with pytest.raises(ReconciliationError, match="^Private output cannot be inside a Git worktree$"):
        stage_reconciliation(database, manifest, sources)

    staging_root = tmp_path / "cleanup" / "batch-sources"
    staging_root.mkdir(parents=True)
    staging = staging_root / ".synthetic.staging"
    durable = staging_root / "durable.json"
    outside = tmp_path / "outside.staging"
    escaped = tmp_path / "cleanup" / ".escaped.staging"
    for path in (staging, durable, outside, escaped):
        path.write_text("synthetic", encoding="utf-8")
    discard_staging(tmp_path / "cleanup", staging)
    assert not staging.exists()
    for candidate in (durable, outside, staging_root / ".." / ".escaped.staging"):
        with pytest.raises(ReconciliationError, match="^Cleanup target is not disposable staging$"):
            discard_staging(tmp_path / "cleanup", candidate)
    assert durable.exists()
    assert outside.exists()
    assert escaped.exists()


def test_cli_reports_only_sanitized_counts_and_failures(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    database, manifest, sources, _ = create_fixture(tmp_path)

    assert reconciliation_cli.main(["--database", str(database), "--manifest", str(manifest), "--source-root", str(sources)]) == 0
    assert capsys.readouterr().out == "Reconciliation staged: sources=1 versions=1 errors=0 resumed=no\n"
    private_file(sources / "synthetic-annual.json", b"private-synthetic-value")
    assert reconciliation_cli.main(["--database", str(database), "--manifest", str(manifest), "--source-root", str(sources)]) == 1
    output = capsys.readouterr().out
    assert output == "Reconciliation failed: Source verification failed\n"
    assert str(sources) not in output
    assert "private-synthetic-value" not in output


@pytest.mark.parametrize(
    "failure", [sqlite3.OperationalError, RuntimeError, OSError],
    ids=["sqlite", "writer-lock", "directory-sync"],
)
def test_cli_sanitizes_lower_level_failures(tmp_path, capsys, monkeypatch, failure):
    private = f"{tmp_path}/{'a' * 64}"
    monkeypatch.setattr(reconciliation_cli, "stage_reconciliation", lambda *_: (_ for _ in ()).throw(failure(private)))
    assert reconciliation_cli.main(["--database", private, "--manifest", private, "--source-root", private]) == 1
    assert capsys.readouterr().out == "Reconciliation failed: Internal staging failure\n"
