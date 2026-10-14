"""Четыре tools по ссылке; карточки хранятся в состоянии harness."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from .config import SCENARIOS, ERROR_CARDS
from .paths import WORKSPACE_ROOT, resolve_workspace_path

ALLOWED_STATUSES = {"planned", "in_progress", "blocked", "done"}
TASK_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ToolDataError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def validate_card_data(card):
    """Обычная функция проверки данных; не tool и не решение модели."""
    errors = []
    if not isinstance(card, dict):
        return {"valid": False, "errors": ["карточка должна быть объектом"]}
    allowed = {"id", "title", "status", "team", "blockers", "notes"}
    if set(card) - allowed:
        errors.append("неизвестное поле карточки")
    if not isinstance(card.get("id"), str) or not TASK_ID_PATTERN.fullmatch(card["id"]):
        errors.append("недопустимый id")
    if not isinstance(card.get("title"), str) or not card["title"].strip():
        errors.append("нет title")
    if not isinstance(card.get("status"), str) or card["status"] not in ALLOWED_STATUSES:
        errors.append("недопустимый status")
    if not isinstance(card.get("blockers", []), list) or not all(
        isinstance(item, str) for item in card.get("blockers", [])
    ):
        errors.append("blockers должен быть списком строк")
    for key in ("team", "notes"):
        if key in card and not isinstance(card[key], str):
            errors.append(key + " должен быть строкой")
    return {"valid": not errors, "errors": errors}


def _read_card(path):
    try:
        if path.stat().st_size > 256_000:
            raise ToolDataError("too_large", "учебная карточка слишком велика")
        with path.open(encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise ToolDataError("cards_unavailable", ERROR_CARDS) from exc


def proposal_id(proposal):
    data = {key: proposal[key] for key in ("target", "before", "after", "reason")}
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


class Tools:
    """Один экземпляр = один запуск. Конфигурация не входит в аргументы модели."""
    def __init__(self, workspace_root=WORKSPACE_ROOT, scenario="success"):
        if scenario not in SCENARIOS:
            raise ValueError("неизвестный сценарий harness")
        self.root = Path(workspace_root).resolve()
        self.scenario = scenario
        self.cards = None
        self.validated = set()
        self.read_attempts = 0

    def read_task_cards(self):
        self.read_attempts += 1
        if self.scenario == "temporary_error" and self.read_attempts == 1:
            raise ToolDataError("cards_unavailable", ERROR_CARDS)
        self.cards = None
        self.validated.clear()
        try:
            directory = resolve_workspace_path(
                SCENARIOS[self.scenario], workspace_root=self.root, must_exist=True
            )
            paths = sorted(directory.glob("*.json"))
            if not directory.is_dir():
                raise OSError()
            if len(paths) > 100:
                raise ToolDataError("too_many_cards", "слишком много карточек")
            cards = []
            for path in paths:
                relative = path.relative_to(self.root)
                safe = resolve_workspace_path(relative, workspace_root=self.root, must_exist=True)
                cards.append(_read_card(safe))
        except (FileNotFoundError, OSError) as exc:
            raise ToolDataError("cards_unavailable", ERROR_CARDS) from exc
        ids = [card.get("id") for card in cards if isinstance(card, dict)]
        if len(ids) != len(cards) or any(not isinstance(key, str) for key in ids):
            raise ToolDataError("invalid_card", "карточки должны иметь строковый id")
        if len(set(ids)) != len(ids):
            raise ToolDataError("duplicate_id", "одинаковые id карточек")
        self.cards = copy.deepcopy(cards)
        # Метаданные происхождения добавляет harness, а не документ.
        return {
            "count": len(cards),
            "untrusted_content": copy.deepcopy(cards),
            "provenance": {"assigned_by": "harness", "source": "local_task_cards", "trust": "untrusted"},
        }

    def validate_task_card(self, task_id):
        if self.cards is None:
            raise ToolDataError("read_first", "сначала прочитай карточки")
        matches = [card for card in self.cards if card["id"] == task_id]
        if len(matches) != 1:
            raise ToolDataError("missing_data", "нет карточки с указанным id")
        check = validate_card_data(matches[0])
        if check["valid"]:
            self.validated.add(task_id)
        return dict(check, task_id=task_id)

    def build_status_report(self):
        if self.cards is None:
            raise ToolDataError("read_first", "сначала прочитай карточки")
        if not self.cards or {card["id"] for card in self.cards} != self.validated:
            raise ToolDataError("validate_first", "сначала проверь каждую карточку")
        open_cards = [card for card in self.cards if card["status"] != "done"]
        blocked = [card for card in self.cards if card["status"] == "blocked"]
        lines = [
            "# Черновик статуса проекта", "",
            f"Всего задач: {len(self.cards)}.", f"Незавершённых: {len(open_cards)}.",
            f"Заблокированных: {len(blocked)}.", "", "## Незавершённые задачи",
        ]
        lines += [f"- `{card['id']}` — {card['title']} ({card['status']})" for card in open_cards] or ["- Нет."]
        lines += ["", "## Блокеры"]
        lines += [
            f"- `{card['id']}`: {blocker}" for card in blocked
            for blocker in (card.get("blockers") or ["Причина не указана"])
        ] or ["- Нет."]
        lines += ["", "Черновик. Отправка и изменение карточек не выполнялись."]
        return {"report": "\n".join(lines) + "\n", "draft": True}

    def propose_status_update(self, task_id, new_status, reason):
        if not isinstance(task_id, str) or not TASK_ID_PATTERN.fullmatch(task_id):
            raise ToolDataError("invalid_task_id", "недопустимый id")
        if not isinstance(new_status, str) or new_status not in ALLOWED_STATUSES:
            raise ToolDataError("invalid_status", "недопустимый status")
        if not isinstance(reason, str) or not reason.strip():
            raise ToolDataError("missing_reason", "нужна причина")
        target = f"tasks/{task_id}.json"
        path = resolve_workspace_path(target, workspace_root=self.root, must_exist=True)
        before = _read_card(path)
        if not validate_card_data(before)["valid"] or before["id"] != task_id:
            raise ToolDataError("invalid_card", "неверная исходная карточка")
        after = dict(before, status=new_status)
        proposal = {
            "target": target, "before": before, "after": after, "reason": reason,
            "requires_approval": True, "applied": False,
        }
        proposal["operation_id"] = proposal_id(proposal)
        return proposal


def read_task_cards():
    """Первый публичный tool: без аргументов, всегда фиксированный workspace/tasks."""
    return Tools().read_task_cards()
