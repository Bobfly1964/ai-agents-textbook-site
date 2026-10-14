"""Глава 3. Проверяемая файловая граница; это не доказательство OS-sandbox."""

import argparse
import json
from pathlib import Path

from school_agent.paths import (
    WORKSPACE_ROOT as DEFAULT_WORKSPACE_ROOT,
    WorkspaceBoundaryError,
    resolve_workspace_path,
)


WORKSPACE_ROOT = DEFAULT_WORKSPACE_ROOT
KNOWN_OPERATIONS = frozenset({"read", "write"})
ALLOWED_OPERATIONS = frozenset({"read"})
WRITABLE_PREFIX = "drafts/"
WRITE_PROOF_TEXT = "chapter 3 write gate proof\n"

HUMAN_BOUNDARIES = {
    "inside_workspace": "внутри workspace",
    "outside_workspace": "вне workspace",
}

HUMAN_REASONS = {
    "existing_file": "файл существует",
    "operation_not_allowed": "операция запрещена политикой демо",
    "path_not_writable": "путь не входит в область записи workspace/drafts/",
    "not_found": "файл не найден",
    "path_outside_workspace": "путь выходит за workspace",
    "unknown_operation": "неизвестная операция",
    "read_failed": "чтение не выполнено",
    "write_failed": "запись не выполнена",
    "write_completed": "служебный черновик записан",
}


def _observation(operation, relative_path, status, boundary, reason):
    return {
        "operation": operation,
        "path": Path(relative_path).as_posix(),
        "status": status,
        "boundary": boundary,
        "reason": reason,
        "os_sandbox_proven": False,
    }


def _is_writable_path(target):
    relative_target = target.relative_to(Path(WORKSPACE_ROOT).resolve()).as_posix()
    return relative_target.startswith(WRITABLE_PREFIX)


def check_workspace_access(relative_path, operation="read"):
    if operation not in KNOWN_OPERATIONS:
        return _observation(
            operation,
            relative_path,
            "error",
            "inside_workspace",
            "unknown_operation",
        )

    try:
        target = resolve_workspace_path(
            relative_path,
            workspace_root=WORKSPACE_ROOT,
        )
    except WorkspaceBoundaryError:
        return _observation(
            operation,
            relative_path,
            "denied",
            "outside_workspace",
            "path_outside_workspace",
        )

    if operation not in ALLOWED_OPERATIONS:
        return _observation(
            operation,
            relative_path,
            "denied",
            "inside_workspace",
            "operation_not_allowed",
        )

    if operation == "write" and not _is_writable_path(target):
        return _observation(
            operation,
            relative_path,
            "denied",
            "inside_workspace",
            "path_not_writable",
        )

    if operation == "read":
        try:
            target.read_text(encoding="utf-8")
        except FileNotFoundError:
            return _observation(
                operation,
                relative_path,
                "error",
                "inside_workspace",
                "not_found",
            )
        except OSError:
            return _observation(
                operation,
                relative_path,
                "error",
                "inside_workspace",
                "read_failed",
            )
        return _observation(
            operation,
            relative_path,
            "allowed",
            "inside_workspace",
            "existing_file",
        )

    try:
        target.write_text(WRITE_PROOF_TEXT, encoding="utf-8")
    except OSError:
        return _observation(
            operation,
            relative_path,
            "error",
            "inside_workspace",
            "write_failed",
        )
    return _observation(
        operation,
        relative_path,
        "allowed",
        "inside_workspace",
        "write_completed",
    )


def format_access_observation(observation):
    return "\n".join([
        "операция: " + observation["operation"],
        "путь: " + observation["path"],
        "результат: " + observation["status"],
        "граница: " + HUMAN_BOUNDARIES[observation["boundary"]],
        "причина: " + HUMAN_REASONS[observation["reason"]],
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--access", dest="operation", choices=("read", "write"), required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check_workspace_access(args.path, args.operation)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(format_access_observation(result), end="")


if __name__ == "__main__":
    main()
