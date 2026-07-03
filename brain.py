from llm import ask_ollama
from memory import save_note, get_notes
from actions import add_todo, add_event
import json

def decide(user_text: str):
    text = user_text.strip().lower()
    original_text = user_text.strip()

    # --- RULES  ---

    if "todo" in text or "add task" in text:
        return {"intent": "todo_add", "content": original_text}

    if text.startswith("remember"):
        return {"intent": "note_add", "content": original_text}

    if any(phrase in text for phrase in [
        "what do i remember",
        "what i remember",
        "what's in my notes",
        "what is in my notes",
        "show my notes",
        "list my notes",
        "read my notes",
        "my notes",
    ]):
        return {"intent": "note_query", "content": original_text}

    if "note" in text or "notes" in text:
        return {"intent": "note_add", "content": original_text}

    if "calendar" in text or "event" in text:
        return {"intent": "calendar_add", "content": original_text}

    # --- FALLBACK TO LLM ---
    # if request is not contained within the rules

    structured = ask_ollama(f"""
You are KUGEL's intent parser.

Return JSON ONLY.

Possible intents:
- todo_add
- todo_list
- note_add
- note_query
- calendar_add
- general_chat

User input:
{text}

Output format:
{{"intent": "...", "content": "..."}}
""")

    try:
        return json.loads(structured)
    except:
        return {
            "intent": "general_chat",
            "content": structured
        }