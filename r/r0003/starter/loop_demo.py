"""Глава 2. Шаг = действие; решение принимается после observation."""
from school_agent.lesson_support import perform_action, new_state, show_loop

MAX_STEPS = 5
MAX_RETRIES = 1


def planner_stub(state):
    return {"name": "read_task_cards"}


def update_state(state, observation):
    state["observation"] = observation
    state["steps"] += 1
    if not observation["ok"]:
        state["failures"] += 1
    state["phase"] = "observed"


def decide(state):
    observation = state["observation"]
    if not observation["ok"]:
        if state["failures"] > state["max_retries"]:
            return "error"
    else:
        if observation.get("search_complete", True):
            matches = observation["matches"]
            if len(matches) == 1:
                return "success"
            return "needs_input"
    if state["steps"] >= state["max_steps"]:
        return "limit"
    return "continue"


def run_loop(scenario="one_match", max_steps=MAX_STEPS, max_retries=MAX_RETRIES):
    state = new_state(scenario, max_steps, max_retries)
    events = []
    while not state["done"]:
        action = planner_stub(state)
        observation = perform_action(action, state)
        update_state(state, observation)
        decision = decide(state)
        events.append({
            "step": state["steps"], "state": state["phase"], "action": action,
            "observation": observation, "decision": decision,
        })
        state["done"] = decision != "continue"
        if state["done"]:
            state["terminal"] = decision
    return {"terminal": state["terminal"], "state": state, "events": events}


if __name__ == "__main__":
    show_loop(run_loop)
