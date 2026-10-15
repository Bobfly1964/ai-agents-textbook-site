"""Проверка файловой границы учебного workspace."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = (PROJECT_ROOT / "workspace").resolve()


class WorkspaceBoundaryError(ValueError):
    """Путь выходит за разрешённую учебную папку."""


def resolve_workspace_path(
    relative_path: str | Path,
    *,
    workspace_root: str | Path = WORKSPACE_ROOT,
    must_exist: bool = False,
) -> Path:
    """Вернуть абсолютный путь, только если он находится внутри workspace.

    Символические ссылки учитываются благодаря ``resolve``. Абсолютные пути
    запрещены даже тогда, когда случайно указывают внутрь workspace: интерфейс
    курса принимает только явные относительные пути.
    """

    root = Path(workspace_root).resolve()
    raw_path = Path(relative_path)
    if raw_path.is_absolute():
        raise WorkspaceBoundaryError("ожидался относительный путь внутри workspace")

    candidate = (root / raw_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise WorkspaceBoundaryError("путь выходит за границу workspace") from exc

    if must_exist and not candidate.exists():
        raise FileNotFoundError(f"учебный путь не найден: {raw_path.as_posix()}")
    return candidate

