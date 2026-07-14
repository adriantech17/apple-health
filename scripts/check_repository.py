from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath


FORBIDDEN_PARTS = {
    ".gh-config",
    ".tools",
    ".venv",
    "backups",
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
    re.compile(r"^apple-health-export-.*\.zip$", re.IGNORECASE),
    re.compile(r"^export(?:ación)?\.xml$", re.IGNORECASE),
    re.compile(r"^route_.*\.gpx$", re.IGNORECASE),
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> None:
    failures: list[str] = []
    files = tracked_files()

    for filename in files:
        path = PurePosixPath(filename)
        lower = filename.lower()
        if path.name in FORBIDDEN_NAMES or FORBIDDEN_PARTS.intersection(path.parts):
            failures.append(f"archivo privado o generado versionado: {filename}")
        if lower.endswith(FORBIDDEN_SUFFIXES):
            failures.append(f"formato privado o binario versionado: {filename}")
        if any(pattern.match(path.name) for pattern in PRIVATE_EXPORT_PATTERNS):
            failures.append(f"exportación privada versionada: {filename}")

        try:
            content = Path(filename).read_bytes()
        except OSError as error:
            failures.append(f"no se pudo leer {filename}: {error}")
            continue
        for marker in SECRET_MARKERS:
            if marker.search(content):
                failures.append(f"posible secreto detectado en {filename}")

    if failures:
        print("Auditoría del repositorio: ERROR")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print(f"Auditoría del repositorio: OK ({len(files)} archivos versionados)")


if __name__ == "__main__":
    main()
