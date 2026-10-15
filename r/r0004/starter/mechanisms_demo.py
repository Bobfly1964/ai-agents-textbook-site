"""Глава 4. Пять механизмов рядом: инструкция, форма, операция, подключение, процедура.

Локальная учебная демонстрация: сеть не используется, scripts не запускаются,
карточки проекта не изменяются. Слои Agent Skill читает существующий загрузчик
``school_agent.skill_loader`` из главы 9 — второго загрузчика в starter нет,
и каждый режим ``skill --layer`` обращается ровно к одному его слою.
"""

import argparse

from school_agent.mechanism_support import (
    CH04_ROOT,
    REFERENCE_PATH,
    SKILL_NAME,
    ChoicesFormatError,
    check_mechanism_choices,
    format_choice_review,
    format_fragment_list,
    format_mcp_map,
    list_mcp_resources,
    list_mechanism_fragments,
    report_fields,
    skill_steps,
)
from school_agent.paths import WorkspaceBoundaryError
from school_agent.skill_loader import (
    discover_skills,
    load_skill,
    read_skill_resource,
)


SKILLS_ROOT = CH04_ROOT / "skills"


def _print_catalog():
    """Слой 1: только короткие metadata каталога."""

    catalog = discover_skills(SKILLS_ROOT)
    entry = next(item for item in catalog if item["name"] == SKILL_NAME)
    print("progressive disclosure: catalog")
    print("Agent Skill: " + entry["name"])
    print("description: " + entry["description"])
    print("next: SKILL.md")


def _print_instructions():
    """Слой 2: порядок работы; reference назван, но ещё не прочитан."""

    skill = load_skill(SKILLS_ROOT, SKILL_NAME)
    print("progressive disclosure: SKILL.md")
    for step in skill_steps(skill["instructions"]):
        print("step: " + step)
    references = [
        item["path"] for item in skill["available_files"] if item["kind"] == "references"
    ]
    print("next: " + (references[0] if references else "none"))


def _print_reference():
    """Слой 3: только запрошенный справочный материал."""

    resource = read_skill_resource(SKILLS_ROOT, SKILL_NAME, REFERENCE_PATH)
    print("progressive disclosure: " + resource["path"])
    for field in report_fields(resource["content"]):
        print("field: " + field)
    print("next: none")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Пять механизмов главы 4 на локальных учебных данных.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fragments", help="пять нейтральных фрагментов A–E")
    check = commands.add_parser("check", help="сверить ответы классификации")
    check.add_argument("choices", help="путь к файлу ответов внутри workspace/")
    commands.add_parser("mcp", help="локальная mock-карта MCP без сети")
    skill = commands.add_parser("skill", help="один слой Agent Skill")
    skill.add_argument(
        "--layer",
        choices=["catalog", "instructions", "reference"],
        required=True,
    )
    args = parser.parse_args(argv)

    if args.command == "fragments":
        print(format_fragment_list(list_mechanism_fragments()), end="")
    elif args.command == "check":
        try:
            review = check_mechanism_choices(args.choices)
        except (WorkspaceBoundaryError, ChoicesFormatError, OSError) as exc:
            parser.error(str(exc))
        print(format_choice_review(review), end="")
    elif args.command == "mcp":
        print(format_mcp_map(list_mcp_resources()), end="")
    elif args.layer == "catalog":
        _print_catalog()
    elif args.layer == "instructions":
        _print_instructions()
    else:
        _print_reference()
    return 0


if __name__ == "__main__":
    main()
