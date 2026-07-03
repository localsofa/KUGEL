from pathlib import Path
from memory import get_todos
from brain import decide
from actions import add_todo, add_event
from memory import get_todos, save_note, get_notes
from llm import ask_ollama


def build_context_prompt(user_text: str) -> str:
    system_prompt = Path("prompts/system.txt").read_text(encoding="utf-8").strip()
    notes = get_notes()
    todos = get_todos()

    return f"""{system_prompt}

Use the following saved information when it is relevant.

Todos / reminders:
{todos}

Notes:
{notes}

User request: {user_text}
"""


def process(user_text):

    decision = decide(user_text)

    if isinstance(decision, str):
        return decision

    if not isinstance(decision, dict):
        return "KUGEL error: invalid brain output"

    intent = decision.get("intent", "general_chat")
    content = decision.get("content", user_text)
    
    # --- ACTIONS ---

    if intent == "todo_add":
        add_todo(content)
        return "Added to your todo list."

    if intent == "note_add":
        save_note(content)
        return "Saved note."

    if intent == "calendar_add":
        add_event(content)
        return "Added to calendar."

    # --- MEMORY QUERY ---

    if intent == "note_query":
        return get_notes()

    if intent == "todo_query":
        return get_todos()

    # --- CHAT ---

    return ask_ollama(build_context_prompt(user_text))