from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from src.reconciliation import ReconciliationError, seal_reconciliation, stage_reconciliation


def now_utc() -> datetime:
    return datetime.now(UTC)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a private historical reconciliation")
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--seal-batch")
    parser.add_argument("--approval-manifest-sha256")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    staging = options.manifest is not None or options.source_root is not None
    sealing = options.seal_batch is not None or options.approval_manifest_sha256 is not None
    if staging == sealing or (staging and None in (options.manifest, options.source_root)) or (
        sealing and None in (options.seal_batch, options.approval_manifest_sha256)
    ):
        print("Reconciliation failed: Select one complete staging or sealing operation")
        return 1
    try:
        if sealing:
            result = seal_reconciliation(
                options.database,
                options.seal_batch,
                options.approval_manifest_sha256,
                sealed_at=now_utc(),
            )
        else:
            result = stage_reconciliation(options.database, options.manifest, options.source_root)
    except ReconciliationError as error:
        print(f"Reconciliation failed: {error}")
        return 1
    except Exception:
        print("Reconciliation failed: Internal staging failure")
        return 1
    resumed = "yes" if result.resumed else "no"
    if sealing:
        print(
            "Reconciliation sealed: "
            f"identities={result.identities} versions={result.versions} "
            f"authority={result.authority_sequence} resumed={resumed}"
        )
    else:
        print(
            "Reconciliation staged: "
            f"sources={result.sources} versions={result.versions} "
            f"errors={result.errors} resumed={resumed}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
