"""Глава 3. Harness выделен вокруг знакомого цикла без live-модели."""

import argparse
import json

from loop_demo import (
    MAX_RETRIES,
    MAX_STEPS,
    decide,
    planner_stub,
    update_state,
)
from school_agent.lesson_support import format_loop, new_state, perform_action


HARNESS_PARTS = (
    ("интерфейс", "show_loop, main"),
    ("выбор", "planner_stub"),
    ("оркестрация", "run_harness"),
    ("runtime", "perform_action"),
    ("состояние", "new_state, update_state"),
    ("активный_контекст", "state -> planner_stub"),
    (
        "permissions",
        "access_demo.check_workspace_access (отдельное демо главы 3)",
    ),
)


def format_harness_parts():
    lines = []
    for name, implementation in HARNESS_PARTS:
        lines.append(name + ": " + implementation)
        if name == "оркестрация":
            lines.append("  решение_после_observation: decide")
    return "\n".join(lines) + "\n"


def run_harness(
    scenario="one_match",
    max_steps=MAX_STEPS,
    max_retries=MAX_RETRIES,
):
    state = new_state(scenario, max_steps, max_retries)
    events = []
    while not state["done"]:
        action = planner_stub(state)
        observation = perform_action(action, state)
        update_state(state, observation)
        decision = decide(state)
        events.append({
            "step": state["steps"],
            "state": state["phase"],
            "action": action,
            "observation": observation,
            "decision": decision,
        })
        state["done"] = decision != "continue"
        if state["done"]:
            state["terminal"] = decision
    return {"terminal": state["terminal"], "state": state, "events": events}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="one_match")
    parser.add_argument("--show-parts", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.show_parts:
        if args.json:
            parser.error("--json не используется вместе с --show-parts")
        print(format_harness_parts(), end="")
        return

    try:
        result = run_harness(args.scenario)
    except ValueError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_loop(result), end="")


if __name__ == "__main__":
    main()
