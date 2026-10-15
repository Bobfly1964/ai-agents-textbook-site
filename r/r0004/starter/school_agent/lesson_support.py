"""Заготовленные наблюдения и служебный CLI вынесены из ученического листинга."""
from .config import ERROR_CARDS


def new_state(scenario, max_steps, max_retries):
    if scenario not in ("one_match", "two_matches", "temporary_error", "permanent_error", "limit", "missing_file", "no_matches"):
        raise ValueError("неизвестный сценарий")
    if type(max_steps) is not int or not 1 <= max_steps <= 5:
        raise ValueError("max_steps должен быть от 1 до 5")
    if type(max_retries) is not int or not 0 <= max_retries <= 1:
        raise ValueError("max_retries должен быть 0 или 1")
    return {"phase": "start", "scenario": scenario, "steps": 0, "failures": 0,
            "done": False, "terminal": None, "max_steps": max_steps, "max_retries": max_retries}


def perform_action(action, state):
    if action != {"name": "read_task_cards"}:
        return {"ok": False, "error": "неизвестное действие"}
    scenario = state["scenario"]
    if scenario in ("permanent_error", "missing_file") or (
        scenario == "temporary_error" and state["steps"] == 0
    ):
        return {"ok": False, "error": ERROR_CARDS}
    if scenario == "two_matches":
        return {"ok": True, "matches": ["task-003", "task-003-copy"]}
    if scenario == "limit":
        number = state["steps"] + 1
        return {
            "ok": True,
            "matches": ["candidate-" + str(number).zfill(3)],
            "search_complete": False,
            "next_page": number + 1,
        }
    if scenario == "no_matches":
        return {"ok": True, "matches": []}
    return {"ok": True, "matches": ["task-003"]}


def format_loop(result):
    import json
    lines = []
    for event in result["events"]:
        lines += [
            "step: " + str(event["step"]), "state: " + event["state"],
            "action: " + event["action"]["name"],
            "observation: " + json.dumps(event["observation"], ensure_ascii=False),
            "decision: " + event["decision"],
        ]
    return "\n".join(lines) + "\n"


def show_loop(run_loop):
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="one_match")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = run_loop(args.scenario)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else format_loop(result), end="\n" if args.json else "")
