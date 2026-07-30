from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from src.reconciliation import ReconciliationError, stage_reconciliation


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage a private historical reconciliation")
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    try:
        result = stage_reconciliation(options.database, options.manifest, options.source_root)
    except ReconciliationError as error:
        print(f"Reconciliation failed: {error}")
        return 1
    except Exception:
        print("Reconciliation failed: Internal staging failure")
        return 1
    resumed = "yes" if result.resumed else "no"
    print(
        "Reconciliation staged: "
        f"sources={result.sources} versions={result.versions} "
        f"errors={result.errors} resumed={resumed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
