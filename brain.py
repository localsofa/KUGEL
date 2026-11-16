import re

from actions import (
    create_todo,
    list_todos,
    create_note,
    create_project,
    create_event,
    find_project,
    save_project_note,
    save_project_link,
    create_project_todo
)

from llm import assist_with_project, classify_intent


def process(text, project_id=None):

    text_lower = text.lower().strip()
    print(f"\n[DEBUG] Input: {text}")

    project_capture = re.match(
        r"^add (?:idea|note) to project\s+(.+?)\s*:\s*(.+)$",
        text.strip(),
        re.IGNORECASE | re.DOTALL
    )
    if project_capture:
        project = find_project(project_capture.group(1))
        if project is None:
            return f"I couldn't find a project named '{project_capture.group(1)}'."
        save_project_note(project[0], project_capture.group(2))
        return f"Saved that idea to the '{project[1]}' project."

    project_link = re.match(
        r"^add link to project\s+(.+?)\s*:\s*(.+)$",
        text.strip(),
        re.IGNORECASE | re.DOTALL
    )
    if project_link:
        project = find_project(project_link.group(1))
        if project is None:
            return f"I couldn't find a project named '{project_link.group(1)}'."
        link_details = project_link.group(2).strip().split("|", 1)
        if len(link_details) == 2:
            title, url = link_details
        else:
            url = link_details[0]
            title = url
        save_project_link(project[0], title, url)
        return f"Saved the link to the '{project[1]}' project."

    project_task = re.match(
        r"^add (?:project )?task to project\s+(.+?)\s*:\s*(.+)$",
        text.strip(),
        re.IGNORECASE | re.DOTALL
    )
    if project_task:
        project = find_project(project_task.group(1))
        if project is None:
            return f"I couldn't find a project named '{project_task.group(1)}'."
        return create_project_todo(project[0], project_task.group(2))

    project_assistance = re.match(
        r"^(summarize|summary of) project\s+(.+)$",
        text.strip(),
        re.IGNORECASE
    )
    if project_assistance:
        return get_project_assistance(project_assistance.group(2), "summary")

    project_assistance = re.match(
        r"^suggest next steps for project\s+(.+)$",
        text.strip(),
        re.IGNORECASE
    )
    if project_assistance:
        return get_project_assistance(project_assistance.group(1), "next_steps")

    # ----------------------
    # SIMPLE RULES
    # ----------------------

    if text_lower.startswith("add todo"):
        task = text[8:].strip()
        if project_id is not None:
            return create_project_todo(project_id, task)
        return create_todo(task)

    if text_lower in ["show todos", "list todos", "what are my tasks"]:
        return list_todos()

    if text_lower.startswith("remember"):
        content = text[len("remember"):].strip()
        if project_id is not None:
            save_project_note(project_id, content)
            return "I've saved that to this project."
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

    return execute_intent(intent, text, project_id)


def get_project_assistance(project_name, mode):
    project = find_project(project_name.strip())
    if project is None:
        return f"I couldn't find a project named '{project_name.strip()}'."
    return assist_with_project(project[0], mode)


def execute_intent(intent, original_text, project_id=None):

    print(f"[DEBUG] Executing: {intent}")

    intent_name = intent.get("intent", "chat")
    content = intent.get("content", original_text)

    if intent_name == "todo_create":
        if project_id is not None:
            return create_project_todo(project_id, content)
        return create_todo(content)

    elif intent_name == "todo_list":
        return list_todos()

    elif intent_name == "note_create":
        if project_id is not None:
            save_project_note(project_id, content)
            return "I've saved that to this project."
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