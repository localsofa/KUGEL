from actions import (
    create_todo,
    list_todos,
    create_note,
    create_project,
    create_event
)

from llm import classify_intent


def process(text):

    text_lower = text.lower().strip()
    print(f"\n[DEBUG] Input: {text}")

    # ----------------------
    # SIMPLE RULES
    # ----------------------

    if text_lower.startswith("add todo"):
        task = text[8:].strip()
        return create_todo(task)

    if text_lower in ["show todos", "list todos", "what are my tasks"]:
        return list_todos()

    if text_lower.startswith("remember"):
        content = text[len("remember"):].strip()
        return create_note(content)

    if text_lower.startswith("create project"):
        name = text[len("create project"):].strip()
        return create_project(name)

    if text_lower.startswith("event "):
        data = text[6:].split("|")

        if len(data) < 2:
            return "Format: event TITLE ; YYYY-MM-DD ; HH:MM"

        title = data[0].strip()
        event_date = data[1].strip()

        event_time = None

        if len(data) >= 3:
            event_time = data[2].strip()

        return create_event(
            title,
            event_date,
            event_time
        )

    # ----------------------
    # LLM INTENT RECOGNITION
    # ----------------------

    intent = classify_intent(text)
    print(f"[DEBUG] Intent result: {intent}")

    return execute_intent(intent, text)


def execute_intent(intent, original_text):

    print(f"[DEBUG] Executing: {intent}")

    intent_name = intent.get("intent", "chat")
    content = intent.get("content", original_text)

    if intent_name == "todo_create":
        return create_todo(content)

    elif intent_name == "todo_list":
        return list_todos()

    elif intent_name == "note_create":
        return create_note(content)

    elif intent_name == "project_create":
        return create_project(content)

    elif intent_name == "chat":
        return (
            "I'm not sure what action you want me to take yet."
        )

    else:
        return (
            f"I understood the intent '{intent_name}', "
            "but I don't know how to execute it yet."
        )