from __future__ import annotations

import argparse
import re
import subprocess


TYPES = "build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test"
BRANCH_PATTERNS = (
    re.compile(rf"^(?:{TYPES})/(?:[0-9]+-)?[a-z0-9]+(?:-[a-z0-9]+)+$"),
    re.compile(
        rf"^(?:codex|copilot|opencode)/(?:{TYPES})-(?:[0-9]+-)?"
        r"[a-z0-9]+(?:-[a-z0-9]+)+$"
    ),
)
COMMIT_PATTERN = re.compile(
    rf"^(?:{TYPES})(?:\([a-z0-9]+(?:-[a-z0-9]+)*\))?!?: [^\s].+$"
)


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def commit_subjects(base: str | None, head: str | None, commit: str | None) -> list[str]:
    if commit:
        output = git("show", "-s", "--format=%s", commit)
    elif base and head:
        output = git("log", "--format=%s", f"{base}..{head}")
    else:
        raise ValueError("indica --commit o la pareja --base/--head")
    return [line for line in output.splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", required=True)
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--commit")
    arguments = parser.parse_args()

    failures: list[str] = []
    if arguments.branch != "main" and not any(
        pattern.fullmatch(arguments.branch) for pattern in BRANCH_PATTERNS
    ):
        failures.append(f"nombre de rama no válido: {arguments.branch}")

    try:
        subjects = commit_subjects(arguments.base, arguments.head, arguments.commit)
    except ValueError as error:
        parser.error(str(error))

    if not subjects:
        failures.append("el rango no contiene commits")
    for subject in subjects:
        if len(subject) > 100:
            failures.append(f"asunto de commit superior a 100 caracteres: {subject}")
        if not COMMIT_PATTERN.fullmatch(subject):
            failures.append(f"commit no convencional: {subject}")

    if failures:
        print("Convenciones del repositorio: ERROR")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print(
        f"Convenciones del repositorio: OK "
        f"({arguments.branch}; {len(subjects)} commits)"
    )


if __name__ == "__main__":
    main()
