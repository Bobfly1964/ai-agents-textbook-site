"""Глава 1. Сначала предскажи: фраза доказывает чтение файла?"""
from school_agent.tools import read_task_cards, ToolDataError
from school_agent.config import ERROR_CARDS


def model_stub(text):
    return "Карточки проекта прочитаны. Задача task-003 заблокирована."


def run_demo(text, scenario="normal"):
    from school_agent.presentation import read_for_demo
    message = model_stub(text)
    try:
        observation = read_task_cards() if scenario == "normal" else read_for_demo(scenario)
    except ToolDataError:
        observation = {"error": ERROR_CARDS}
    return {"message": message, "observation": observation}


if __name__ == "__main__":
    from school_agent.presentation import chat_main
    chat_main(run_demo)
